#if UNITY_EDITOR
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using UnityEditor;
using UnityEngine;

namespace ForgeArtisan
{
    /// <summary>
    /// ForgeArtisanBridge: Local HTTP RPC server running inside the Unity Editor.
    /// Exposes endpoints for procedural mesh generation, compound mechanical assembly,
    /// PBR material assignment, and viewport snapshot capture for SAM 3.1 visual critique.
    /// </summary>
    [InitializeOnLoad]
    public static class ForgeArtisanBridge
    {
        private const int DefaultPort = 8080;
        private static HttpListener _listener;
        private static Thread _listenerThread;
        private static bool _isRunning = false;
        private static readonly ConcurrentQueue<Action> _mainThreadQueue = new ConcurrentQueue<Action>();
        private static volatile string _cachedActiveScene = "SampleScene";
        private static volatile int _cachedObjectCount = 0;

        static ForgeArtisanBridge()
        {
            Application.runInBackground = true;
            EditorApplication.update += UpdateMainThreadQueue;
            EditorApplication.delayCall += DelayedStart;
            AssemblyReloadEvents.beforeAssemblyReload += StopServer;
            EditorApplication.quitting += StopServer;
        }

        private static void DelayedStart()
        {
            StartServer(DefaultPort);
        }

        [MenuItem("ForgeArtisan/Restart Bridge Server")]
        public static void RestartServerMenu()
        {
            StopServer();
            StartServer(DefaultPort);
        }

        [MenuItem("ForgeArtisan/Server Status")]
        public static void ShowStatusMenu()
        {
            EditorUtility.DisplayDialog(
                "ForgeArtisan Bridge",
                _isRunning 
                    ? $"Server is active on http://127.0.0.1:{DefaultPort}/\nReady to receive agent commands."
                    : "Server is stopped.",
                "OK"
            );
        }

        [MenuItem("ForgeArtisan/Spawn Playable Character")]
        public static void SpawnPlayerMenu()
        {
            SpawnPlayerCharacter();
        }

        [MenuItem("ForgeArtisan/Toggle Play Mode (Explore) _F5")]
        public static void TogglePlayModeMenu()
        {
            if (EditorApplication.isPlaying)
            {
                EditorApplication.isPlaying = false;
            }
            else
            {
                SpawnPlayerCharacter();
                EditorApplication.isPlaying = true;
            }
        }

        private static int _activePort = DefaultPort;

        public static void StartServer(int port = DefaultPort)
        {
            if (_isRunning) return;

            int[] candidatePorts = new int[] { port, 8081, 8082, 8083 };
            bool started = false;

            foreach (var p in candidatePorts)
            {
                try
                {
                    if (_listener != null)
                    {
                        try { _listener.Stop(); _listener.Close(); } catch { }
                        _listener = null;
                    }

                    _listener = new HttpListener();
                    _listener.Prefixes.Add($"http://127.0.0.1:{p}/");
                    _listener.Start();
                    _isRunning = true;
                    _activePort = p;

                    _listenerThread = new Thread(ListenLoop)
                    {
                        IsBackground = true,
                        Name = "ForgeArtisan_HttpListener"
                    };
                    _listenerThread.Start();

                    Debug.Log($"[ForgeArtisan] Unity Bridge Server started on http://127.0.0.1:{p}/");

                    // Save port for web client auto-discovery
                    try
                    {
                        string repoPortFile = @"C:\Soham\Repositories\Hackathon-meta\forge-artisan\workspace\unity_bridge_port.txt";
                        string dir = Path.GetDirectoryName(repoPortFile);
                        if (Directory.Exists(dir))
                        {
                            File.WriteAllText(repoPortFile, p.ToString());
                        }
                    }
                    catch { }

                    started = true;
                    break;
                }
                catch
                {
                    try { _listener?.Close(); } catch { }
                    _listener = null;
                }
            }

            if (!started)
            {
                Debug.LogWarning("[ForgeArtisan] Could not bind bridge server to candidate ports (8080-8083). Use menu 'ForgeArtisan -> Restart Bridge Server' once sockets release.");
                _isRunning = false;
            }
        }

        public static void StopServer()
        {
            _isRunning = false;
            try
            {
                _listener?.Stop();
                _listener?.Abort();
                _listener?.Close();
            }
            catch { }

            _listenerThread = null;
            _listener = null;
            Debug.Log("[ForgeArtisan] Unity Bridge Server stopped.");
        }

        private class PartBuildTask
        {
            public GameObject rootGo;
            public ComponentPartSpec part;
            public int index;
            public int total;
        }

        private static readonly Queue<PartBuildTask> _partBuildQueue = new Queue<PartBuildTask>();
        private static double _lastPartSpawnTime = 0.0;
        private const double PartSpawnInterval = 0.045; // 45ms per block for smooth, visible progressive assembly

        private static void UpdateMainThreadQueue()
        {
            try
            {
                var scn = UnityEditor.SceneManagement.EditorSceneManager.GetActiveScene();
                if (scn.IsValid()) _cachedActiveScene = scn.name;
                var root = GameObject.Find("ForgeArtisan_Workspace");
                _cachedObjectCount = root != null ? root.transform.childCount : 0;
            }
            catch { }

            while (_mainThreadQueue.TryDequeue(out var action))
            {
                try
                {
                    action?.Invoke();
                }
                catch (Exception ex)
                {
                    Debug.LogError($"[ForgeArtisan] Error executing action on main thread: {ex}");
                }
            }

            // Progressive block-by-block mesh construction
            if (_partBuildQueue.Count > 0 && EditorApplication.timeSinceStartup - _lastPartSpawnTime >= PartSpawnInterval)
            {
                _lastPartSpawnTime = EditorApplication.timeSinceStartup;
                var task = _partBuildQueue.Dequeue();
                if (task.rootGo != null && task.part != null)
                {
                    try
                    {
                        SpawnSinglePart(task.rootGo, task.part, task.index);
                        SceneView.RepaintAll();
                    }
                    catch (Exception ex)
                    {
                        Debug.LogError($"[ForgeArtisan] Error assembling part {task.part?.name}: {ex}");
                    }
                }

                // When progressive assembly completes, automatically spawn playable explorer character
                if (_partBuildQueue.Count == 0)
                {
                    SpawnPlayerCharacter();
                    Debug.Log("[ForgeArtisan] Assembly complete! Playable character spawned at entrance. Press F5 or Play to explore.");
                }
            }
        }

        private static void EnqueueMainThread(Action action)
        {
            _mainThreadQueue.Enqueue(action);
        }

        private static Task<T> EnqueueMainThreadAsync<T>(Func<T> func)
        {
            var tcs = new TaskCompletionSource<T>();
            _mainThreadQueue.Enqueue(() =>
            {
                try
                {
                    var result = func();
                    tcs.SetResult(result);
                }
                catch (Exception ex)
                {
                    tcs.SetException(ex);
                }
            });
            return tcs.Task;
        }

        private static void ListenLoop()
        {
            while (_isRunning && _listener != null && _listener.IsListening)
            {
                try
                {
                    var context = _listener.GetContext();
                    ThreadPool.QueueUserWorkItem(async _ =>
                    {
                        try
                        {
                            await HandleRequestAsync(context);
                        }
                        catch (Exception ex)
                        {
                            Debug.LogWarning($"[ForgeArtisan] Request handling error: {ex.Message}");
                        }
                    });
                }
                catch (HttpListenerException)
                {
                    break;
                }
                catch (Exception ex)
                {
                    if (_isRunning) Debug.LogWarning($"[ForgeArtisan] Listener error: {ex.Message}");
                }
            }
        }

        private static async Task HandleRequestAsync(HttpListenerContext context)
        {
            var req = context.Request;
            var res = context.Response;

            res.Headers.Add("Access-Control-Allow-Origin", "*");
            res.Headers.Add("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
            res.Headers.Add("Access-Control-Allow-Headers", "Content-Type");

            if (req.HttpMethod == "OPTIONS")
            {
                res.StatusCode = 200;
                res.Close();
                return;
            }

            string path = req.Url.AbsolutePath.TrimEnd('/').ToLowerInvariant();
            string responseString = "";
            int statusCode = 200;

            try
            {
                string body = "";
                if (req.HasEntityBody)
                {
                    using var reader = new StreamReader(req.InputStream, req.ContentEncoding);
                    body = await reader.ReadToEndAsync();
                }

                switch (path)
                {
                    case "/status":
                    case "":
                        responseString = JsonSuccess(new Dictionary<string, object>
                        {
                            ["status"] = "connected",
                            ["engine"] = "Unity",
                            ["unity_version"] = Application.unityVersion,
                            ["active_scene"] = _cachedActiveScene,
                            ["workspace_objects"] = _cachedObjectCount,
                            ["camera_available"] = true
                        });
                        break;

                    case "/clear":
                        responseString = await EnqueueMainThreadAsync(() => ClearWorkspace());
                        break;

                    case "/spawn_primitive":
                        responseString = await EnqueueMainThreadAsync(() => SpawnPrimitive(body));
                        break;

                    case "/build_procedural_mesh":
                        responseString = await EnqueueMainThreadAsync(() => BuildProceduralMesh(body));
                        break;

                    case "/build_compound_model":
                        responseString = await EnqueueMainThreadAsync(() => BuildCompoundModel(body));
                        break;

                    case "/set_material":
                        responseString = await EnqueueMainThreadAsync(() => SetMaterial(body));
                        break;

                    case "/capture_viewport":
                        responseString = await EnqueueMainThreadAsync(() => CaptureViewport(body));
                        break;

                    case "/spawn_player":
                        responseString = await EnqueueMainThreadAsync(() => SpawnPlayerJson());
                        break;

                    case "/enter_play_mode":
                        responseString = await EnqueueMainThreadAsync(() => EnterPlayModeJson());
                        break;

                    case "/exit_play_mode":
                        responseString = await EnqueueMainThreadAsync(() => ExitPlayModeJson());
                        break;

                    default:
                        statusCode = 404;
                        responseString = JsonError($"Endpoint not found: {path}");
                        break;
                }
            }
            catch (Exception ex)
            {
                statusCode = 500;
                responseString = JsonError($"Server internal error: {ex.Message}");
                Debug.LogError($"[ForgeArtisan] Error handling {path}: {ex}");
            }

            try
            {
                byte[] buffer = Encoding.UTF8.GetBytes(responseString);
                res.ContentType = "application/json";
                res.StatusCode = statusCode;
                res.ContentLength64 = buffer.Length;
                await res.OutputStream.WriteAsync(buffer, 0, buffer.Length);
                res.Close();
            }
            catch { }
        }

        #region Main Thread API Handlers

        private static string GetStatusJson()
        {
            var activeScene = UnityEditor.SceneManagement.EditorSceneManager.GetActiveScene();
            var cam = Camera.main ?? SceneView.lastActiveSceneView?.camera;
            
            var root = GameObject.Find("ForgeArtisan_Workspace");
            int objectCount = root != null ? root.transform.childCount : 0;

            return JsonSuccess(new Dictionary<string, object>
            {
                ["status"] = "connected",
                ["engine"] = "Unity",
                ["unity_version"] = Application.unityVersion,
                ["active_scene"] = activeScene.name,
                ["workspace_objects"] = objectCount,
                ["camera_available"] = (cam != null)
            });
        }

        private static string ClearWorkspace()
        {
            _partBuildQueue.Clear();
            var root = GameObject.Find("ForgeArtisan_Workspace");
            if (root != null)
            {
                Undo.DestroyObjectImmediate(root);
            }
            return JsonSuccess(new Dictionary<string, object>
            {
                ["message"] = "Workspace cleared."
            });
        }

        private static GameObject GetOrCreateWorkspace()
        {
            var root = GameObject.Find("ForgeArtisan_Workspace");
            if (root == null)
            {
                root = new GameObject("ForgeArtisan_Workspace");
                Undo.RegisterCreatedObjectUndo(root, "Create ForgeArtisan Workspace");
            }
            return root;
        }

        [Serializable]
        public class PrimitiveRequest
        {
            public string type = "cube"; // cube, cylinder, sphere, capsule, plane
            public string name = "Primitive";
            public float[] position = new float[] { 0, 0, 0 };
            public float[] rotation = new float[] { 0, 0, 0 };
            public float[] scale = new float[] { 1, 1, 1 };
            public float[] color = new float[] { 0.8f, 0.8f, 0.8f, 1f };
            public float metallic = 0.1f;
            public float smoothness = 0.5f;
            public string parent_name = null;
        }

        private static string SpawnPrimitive(string json)
        {
            var req = JsonUtility.FromJson<PrimitiveRequest>(json) ?? new PrimitiveRequest();
            PrimitiveType pType = PrimitiveType.Cube;
            switch (req.type?.ToLowerInvariant())
            {
                case "cylinder": pType = PrimitiveType.Cylinder; break;
                case "sphere": pType = PrimitiveType.Sphere; break;
                case "capsule": pType = PrimitiveType.Capsule; break;
                case "plane": pType = PrimitiveType.Plane; break;
                default: pType = PrimitiveType.Cube; break;
            }

            var go = GameObject.CreatePrimitive(pType);
            go.name = req.name ?? "Primitive";

            var workspace = GetOrCreateWorkspace();
            if (!string.IsNullOrEmpty(req.parent_name))
            {
                var parentGo = GameObject.Find(req.parent_name);
                go.transform.SetParent(parentGo != null ? parentGo.transform : workspace.transform, false);
            }
            else
            {
                go.transform.SetParent(workspace.transform, false);
            }

            if (req.position != null && req.position.Length >= 3)
                go.transform.localPosition = new Vector3(req.position[0], req.position[1], req.position[2]);

            if (req.rotation != null && req.rotation.Length >= 3)
                go.transform.localEulerAngles = new Vector3(req.rotation[0], req.rotation[1], req.rotation[2]);

            if (req.scale != null && req.scale.Length >= 3)
            {
                float sy = req.scale[1];
                if (req.type?.ToLowerInvariant() == "cylinder") sy *= 0.5f;
                go.transform.localScale = new Vector3(req.scale[0], sy, req.scale[2]);
            }

            ApplyPBRMaterial(go, req.color, req.metallic, req.smoothness);

            Undo.RegisterCreatedObjectUndo(go, $"Spawn {go.name}");
            Selection.activeGameObject = go;

            return JsonSuccess(new Dictionary<string, object>
            {
                ["created"] = go.name,
                ["id"] = go.GetHashCode()
            });
        }

        [Serializable]
        public class ProceduralMeshRequest
        {
            public string name = "ProceduralMesh";
            public string type = null;
            public float[] vertices; // flat array [x0, y0, z0, x1, y1, z1, ...]
            public int[] triangles;   // index array [t0, t1, t2, ...]
            public float[] uvs;       // flat array [u0, v0, u1, v1, ...]
            public float[] normals;   // optional flat array
            public float[] position = new float[] { 0, 0, 0 };
            public float[] rotation = new float[] { 0, 0, 0 };
            public float[] scale = new float[] { 1, 1, 1 };
            public float[] color = new float[] { 0.7f, 0.7f, 0.7f, 1f };
            public float metallic = 0.2f;
            public float smoothness = 0.6f;
            public bool recalculate_normals = true;
            public string parent_name = null;
        }

        private static string BuildProceduralMesh(string json)
        {
            var req = JsonUtility.FromJson<ProceduralMeshRequest>(json);
            if (req == null || req.vertices == null || req.triangles == null || req.vertices.Length < 9)
            {
                return JsonError("Invalid mesh parameters: vertices and triangles required.");
            }

            var go = new GameObject(req.name ?? "ProceduralMesh");
            var workspace = GetOrCreateWorkspace();

            if (!string.IsNullOrEmpty(req.parent_name))
            {
                var parentGo = GameObject.Find(req.parent_name);
                go.transform.SetParent(parentGo != null ? parentGo.transform : workspace.transform, false);
            }
            else
            {
                go.transform.SetParent(workspace.transform, false);
            }

            if (req.position != null && req.position.Length >= 3)
                go.transform.localPosition = new Vector3(req.position[0], req.position[1], req.position[2]);
            if (req.rotation != null && req.rotation.Length >= 3)
                go.transform.localEulerAngles = new Vector3(req.rotation[0], req.rotation[1], req.rotation[2]);
            if (req.scale != null && req.scale.Length >= 3)
            {
                go.transform.localScale = new Vector3(req.scale[0], req.scale[1], req.scale[2]);
            }

            var mf = go.AddComponent<MeshFilter>();
            var mr = go.AddComponent<MeshRenderer>();
            var mesh = new Mesh { name = $"{go.name}_Mesh" };

            int vertCount = req.vertices.Length / 3;
            var vertList = new Vector3[vertCount];
            for (int i = 0; i < vertCount; i++)
            {
                vertList[i] = new Vector3(req.vertices[i * 3], req.vertices[i * 3 + 1], req.vertices[i * 3 + 2]);
            }
            mesh.vertices = vertList;
            mesh.triangles = req.triangles;

            if (req.uvs != null && req.uvs.Length == vertCount * 2)
            {
                var uvList = new Vector2[vertCount];
                for (int i = 0; i < vertCount; i++)
                {
                    uvList[i] = new Vector2(req.uvs[i * 2], req.uvs[i * 2 + 1]);
                }
                mesh.uv = uvList;
            }

            if (req.normals != null && req.normals.Length == req.vertices.Length)
            {
                var normList = new Vector3[vertCount];
                for (int i = 0; i < vertCount; i++)
                {
                    normList[i] = new Vector3(req.normals[i * 3], req.normals[i * 3 + 1], req.normals[i * 3 + 2]);
                }
                mesh.normals = normList;
            }
            else if (req.recalculate_normals)
            {
                mesh.RecalculateNormals();
            }

            mesh.RecalculateBounds();
            mf.sharedMesh = mesh;

            ApplyPBRMaterial(go, req.color, req.metallic, req.smoothness);
            Undo.RegisterCreatedObjectUndo(go, $"Build {go.name}");

            return JsonSuccess(new Dictionary<string, object>
            {
                ["created"] = go.name,
                ["vertex_count"] = vertCount,
                ["triangle_count"] = req.triangles.Length / 3
            });
        }

        [Serializable]
        public class ComponentPartSpec
        {
            public string name;
            public string primitive_type; // cylinder, cube, sphere, beveled_box, wedge
            public float[] position = new float[] { 0, 0, 0 };
            public float[] rotation = new float[] { 0, 0, 0 };
            public float[] scale = new float[] { 1, 1, 1 };
            public float[] color = new float[] { 0.5f, 0.5f, 0.5f, 1f };
            public float metallic = 0.5f;
            public float smoothness = 0.5f;
            public float bevel_radius = 0.05f; // For beveled geometry
            public int bevel_segments = 3;
            public float[] emission_color = null;
        }

        [Serializable]
        public class CompoundModelRequest
        {
            public string root_name = "CompoundModel";
            public float[] root_position = new float[] { 0, 0, 0 };
            public float[] root_rotation = new float[] { 0, 0, 0 };
            public float[] root_scale = new float[] { 1, 1, 1 };
            public List<ComponentPartSpec> parts = new List<ComponentPartSpec>();
            public bool progressive = true;
        }

        private static GameObject SpawnSinglePart(GameObject rootGo, ComponentPartSpec part, int partIndex)
        {
            string partName = string.IsNullOrEmpty(part.name) ? $"Part_{partIndex}" : part.name;
            GameObject partGo;

            string pType = part.primitive_type?.ToLowerInvariant() ?? "cube";
            if (pType == "beveled_box")
            {
                partGo = CreateBeveledBox(partName, part.scale, part.bevel_radius, part.bevel_segments);
            }
            else if (pType == "barrel_lid" || pType == "vault" || pType == "arched_vault")
            {
                partGo = CreateBarrelLidMesh(partName, part.scale);
            }
            else if (pType == "torus" || pType == "ring")
            {
                partGo = CreateTorusMesh(partName, part.scale);
            }
            else if (pType == "wedge")
            {
                partGo = CreateWedgeMesh(partName, part.scale);
            }
            else if (pType == "cowcatcher")
            {
                partGo = CreateCowcatcherMesh(partName, part.scale);
            }
            else
            {
                PrimitiveType primType = PrimitiveType.Cube;
                if (pType == "cylinder") primType = PrimitiveType.Cylinder;
                else if (pType == "sphere") primType = PrimitiveType.Sphere;
                else if (pType == "capsule") primType = PrimitiveType.Capsule;

                partGo = GameObject.CreatePrimitive(primType);
                partGo.name = partName;
                if (part.scale != null && part.scale.Length >= 3)
                {
                    float sy = part.scale[1];
                    if (pType == "cylinder") sy *= 0.5f; // Unity cylinder default height is 2.0; scaling Y by 0.5 matches requested length
                    partGo.transform.localScale = new Vector3(part.scale[0], sy, part.scale[2]);
                }
            }

            partGo.transform.SetParent(rootGo.transform, false);

            if (part.position != null && part.position.Length >= 3)
                partGo.transform.localPosition = new Vector3(part.position[0], part.position[1], part.position[2]);
            if (part.rotation != null && part.rotation.Length >= 3)
                partGo.transform.localEulerAngles = new Vector3(part.rotation[0], part.rotation[1], part.rotation[2]);

            ApplyPBRMaterial(partGo, part.color, part.metallic, part.smoothness, part.emission_color);
            Undo.RegisterCreatedObjectUndo(partGo, $"Spawn {partGo.name}");
            return partGo;
        }

        private static string BuildCompoundModel(string json)
        {
            var req = JsonUtility.FromJson<CompoundModelRequest>(json);
            if (req == null || req.parts == null)
            {
                return JsonError("Invalid compound model request.");
            }

            var workspace = GetOrCreateWorkspace();
            var rootGo = new GameObject(req.root_name ?? "CompoundModel");
            rootGo.transform.SetParent(workspace.transform, false);

            if (req.root_position != null && req.root_position.Length >= 3)
                rootGo.transform.localPosition = new Vector3(req.root_position[0], req.root_position[1], req.root_position[2]);
            if (req.root_rotation != null && req.root_rotation.Length >= 3)
                rootGo.transform.localEulerAngles = new Vector3(req.root_rotation[0], req.root_rotation[1], req.root_rotation[2]);
            if (req.root_scale != null && req.root_scale.Length >= 3)
                rootGo.transform.localScale = new Vector3(req.root_scale[0], req.root_scale[1], req.root_scale[2]);

            Undo.RegisterCreatedObjectUndo(rootGo, $"Build Compound {rootGo.name}");
            Selection.activeGameObject = rootGo;

            if (req.progressive)
            {
                _partBuildQueue.Clear();
                int total = req.parts.Count;
                for (int i = 0; i < total; i++)
                {
                    _partBuildQueue.Enqueue(new PartBuildTask
                    {
                        rootGo = rootGo,
                        part = req.parts[i],
                        index = i + 1,
                        total = total
                    });
                }

                // Immediately place the first part so visual assembly starts with zero latency
                if (_partBuildQueue.Count > 0)
                {
                    var firstTask = _partBuildQueue.Dequeue();
                    SpawnSinglePart(firstTask.rootGo, firstTask.part, firstTask.index);
                    _lastPartSpawnTime = EditorApplication.timeSinceStartup;
                    SceneView.RepaintAll();
                }

                Debug.Log($"[ForgeArtisan] Starting progressive block-by-block build of {rootGo.name} ({total} components queued)...");

                return JsonSuccess(new Dictionary<string, object>
                {
                    ["created"] = rootGo.name,
                    ["parts_count"] = req.parts.Count,
                    ["mode"] = "progressive"
                });
            }
            else
            {
                int partIndex = 0;
                foreach (var part in req.parts)
                {
                    partIndex++;
                    SpawnSinglePart(rootGo, part, partIndex);
                }

                return JsonSuccess(new Dictionary<string, object>
                {
                    ["created"] = rootGo.name,
                    ["parts_count"] = req.parts.Count,
                    ["mode"] = "instant"
                });
            }
        }

        private static GameObject CreateBeveledBox(string name, float[] scale, float bevelRadius, int segments)
        {
            var go = new GameObject(name);
            var mf = go.AddComponent<MeshFilter>();
            go.AddComponent<MeshRenderer>();

            // Generate clean beveled rounded box geometry
            float sx = (scale != null && scale.Length >= 1) ? scale[0] : 1f;
            float sy = (scale != null && scale.Length >= 2) ? scale[1] : 1f;
            float sz = (scale != null && scale.Length >= 3) ? scale[2] : 1f;

            Mesh mesh = ProceduralMeshGenerators.CreateChamferedBox(sx, sy, sz, Mathf.Min(bevelRadius, 0.2f * Mathf.Min(sx, Mathf.Min(sy, sz))));
            mesh.name = $"{name}_Mesh";
            mf.sharedMesh = mesh;

            var mc = go.AddComponent<MeshCollider>();
            mc.sharedMesh = mesh;
            return go;
        }

        private static GameObject CreateWedgeMesh(string name, float[] scale)
        {
            var go = new GameObject(name);
            var mf = go.AddComponent<MeshFilter>();
            go.AddComponent<MeshRenderer>();

            float sx = (scale != null && scale.Length >= 1) ? scale[0] : 1f;
            float sy = (scale != null && scale.Length >= 2) ? scale[1] : 1f;
            float sz = (scale != null && scale.Length >= 3) ? scale[2] : 1f;

            Mesh mesh = ProceduralMeshGenerators.CreateWedge(sx, sy, sz);
            mesh.name = $"{name}_WedgeMesh";
            mf.sharedMesh = mesh;

            var mc = go.AddComponent<MeshCollider>();
            mc.sharedMesh = mesh;
            return go;
        }

        private static GameObject CreateCowcatcherMesh(string name, float[] scale)
        {
            var go = new GameObject(name);
            var mf = go.AddComponent<MeshFilter>();
            go.AddComponent<MeshRenderer>();

            float sx = (scale != null && scale.Length >= 1) ? scale[0] : 1f;
            float sy = (scale != null && scale.Length >= 2) ? scale[1] : 1f;
            float sz = (scale != null && scale.Length >= 3) ? scale[2] : 1f;

            Mesh mesh = ProceduralMeshGenerators.CreateCowcatcher(sx, sy, sz);
            mesh.name = $"{name}_CowcatcherMesh";
            mf.sharedMesh = mesh;

            var mc = go.AddComponent<MeshCollider>();
            mc.sharedMesh = mesh;
            return go;
        }

        private static GameObject CreateBarrelLidMesh(string name, float[] scale)
        {
            var go = new GameObject(name);
            var mf = go.AddComponent<MeshFilter>();
            go.AddComponent<MeshRenderer>();

            float sx = (scale != null && scale.Length >= 1) ? scale[0] : 1f;
            float sy = (scale != null && scale.Length >= 2) ? scale[1] : 0.4f;
            float sz = (scale != null && scale.Length >= 3) ? scale[2] : 1f;

            Mesh mesh = ProceduralMeshGenerators.CreateBarrelLid(sx, sy, sz);
            mesh.name = $"{name}_BarrelLidMesh";
            mf.sharedMesh = mesh;

            var mc = go.AddComponent<MeshCollider>();
            mc.sharedMesh = mesh;
            return go;
        }

        private static GameObject CreateTorusMesh(string name, float[] scale)
        {
            var go = new GameObject(name);
            var mf = go.AddComponent<MeshFilter>();
            go.AddComponent<MeshRenderer>();

            float sx = (scale != null && scale.Length >= 1) ? scale[0] : 0.3f;
            float sy = (scale != null && scale.Length >= 2) ? scale[1] : 0.08f;
            float sz = (scale != null && scale.Length >= 3) ? scale[2] : 0.3f;

            float mainRadius = Mathf.Max(0.04f, (sx * 0.5f) - (sy * 0.5f));
            float tubeRadius = Mathf.Max(0.01f, sy * 0.5f);

            Mesh mesh = ProceduralMeshGenerators.CreateTorus(mainRadius, tubeRadius);
            mesh.name = $"{name}_TorusMesh";
            mf.sharedMesh = mesh;

            var mc = go.AddComponent<MeshCollider>();
            mc.sharedMesh = mesh;
            return go;
        }

        public static GameObject SpawnPlayerCharacter()
        {
            var workspace = GetOrCreateWorkspace();

            var existingPlayer = GameObject.Find("ForgeArtisan_Player");
            if (existingPlayer != null)
            {
                Undo.DestroyObjectImmediate(existingPlayer);
            }

            Vector3 spawnPos = new Vector3(0f, 0.9f, 6.5f);
            Vector3 lookTarget = Vector3.zero;

            if (workspace.transform.childCount > 0)
            {
                Transform targetModel = workspace.transform.GetChild(0);
                Renderer[] renderers = targetModel.GetComponentsInChildren<Renderer>();
                if (renderers.Length > 0)
                {
                    Bounds b = renderers[0].bounds;
                    for (int i = 1; i < renderers.Length; i++)
                    {
                        b.Encapsulate(renderers[i].bounds);
                    }
                    spawnPos = new Vector3(b.center.x, Mathf.Max(0.5f, b.min.y + 0.2f), b.max.z + 2.8f);
                    lookTarget = new Vector3(b.center.x, b.center.y * 0.5f, b.center.z);
                }
            }

            var playerGo = new GameObject("ForgeArtisan_Player");
            playerGo.tag = "Player";
            playerGo.transform.position = spawnPos;

            Vector3 toTarget = lookTarget - spawnPos;
            toTarget.y = 0f;
            if (toTarget.sqrMagnitude > 0.01f)
            {
                playerGo.transform.rotation = Quaternion.LookRotation(toTarget);
            }

            var cc = playerGo.AddComponent<CharacterController>();
            cc.height = 1.8f;
            cc.radius = 0.35f;
            cc.center = new Vector3(0f, 0.9f, 0f);
            cc.stepOffset = 0.45f;
            cc.slopeLimit = 50f;
            cc.skinWidth = 0.05f;

            var camGo = new GameObject("PlayerCamera");
            camGo.transform.SetParent(playerGo.transform, false);
            camGo.transform.localPosition = new Vector3(0f, 1.65f, 0f);
            camGo.tag = "MainCamera";

            var cam = camGo.AddComponent<Camera>();
            cam.nearClipPlane = 0.05f;
            cam.fieldOfView = 65f;
            camGo.AddComponent<AudioListener>();

            foreach (var c in Camera.allCameras)
            {
                if (c != cam && c.CompareTag("MainCamera"))
                {
                    c.enabled = false;
                }
            }

            var bodyVis = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            bodyVis.name = "AvatarVisual";
            bodyVis.transform.SetParent(playerGo.transform, false);
            bodyVis.transform.localPosition = new Vector3(0f, 0.9f, 0f);
            bodyVis.transform.localScale = new Vector3(0.6f, 0.9f, 0.6f);
            var col = bodyVis.GetComponent<Collider>();
            if (col != null) UnityEngine.Object.DestroyImmediate(col);

            System.Type controllerType = System.Type.GetType("ForgeArtisan.ForgeArtisanPlayerController, Assembly-CSharp");
            if (controllerType != null)
            {
                var ctrl = playerGo.AddComponent(controllerType);
                var camField = controllerType.GetField("playerCamera");
                if (camField != null) camField.SetValue(ctrl, cam);
            }

            Undo.RegisterCreatedObjectUndo(playerGo, "Spawn ForgeArtisan Player");
            Selection.activeGameObject = playerGo;
            return playerGo;
        }

        private static string SpawnPlayerJson()
        {
            var go = SpawnPlayerCharacter();
            return JsonSuccess(new Dictionary<string, object>
            {
                ["spawned"] = go != null ? go.name : "null",
                ["position"] = go != null ? new float[] { go.transform.position.x, go.transform.position.y, go.transform.position.z } : null
            });
        }

        private static string EnterPlayModeJson()
        {
            SpawnPlayerCharacter();
            EditorApplication.isPlaying = true;
            return JsonSuccess(new Dictionary<string, object>
            {
                ["play_mode"] = true,
                ["message"] = "Unity entered Play Mode with playable character."
            });
        }

        private static string ExitPlayModeJson()
        {
            EditorApplication.isPlaying = false;
            return JsonSuccess(new Dictionary<string, object>
            {
                ["play_mode"] = false,
                ["message"] = "Unity exited Play Mode."
            });
        }

        [Serializable]
        public class MaterialRequest
        {
            public string target_name;
            public float[] color;
            public float metallic = 0.5f;
            public float smoothness = 0.5f;
            public float[] emission_color;
        }

        private static string SetMaterial(string json)
        {
            var req = JsonUtility.FromJson<MaterialRequest>(json);
            if (req == null || string.IsNullOrEmpty(req.target_name))
                return JsonError("target_name required");

            var go = GameObject.Find(req.target_name);
            if (go == null)
            {
                var workspace = GameObject.Find("ForgeArtisan_Workspace");
                if (workspace != null)
                {
                    foreach (var t in workspace.GetComponentsInChildren<Transform>(true))
                    {
                        if (string.Equals(t.name, req.target_name, StringComparison.OrdinalIgnoreCase) ||
                            t.name.IndexOf(req.target_name, StringComparison.OrdinalIgnoreCase) >= 0)
                        {
                            go = t.gameObject;
                            break;
                        }
                    }
                }
            }
            if (go == null) return JsonError($"Object not found: {req.target_name}");

            ApplyPBRMaterial(go, req.color, req.metallic, req.smoothness, req.emission_color);
            return JsonSuccess(new Dictionary<string, object>
            {
                ["updated"] = go.name
            });
        }

        private static void ApplyPBRMaterial(GameObject go, float[] col, float metallic, float smoothness, float[] emission = null)
        {
            var mr = go.GetComponent<MeshRenderer>();
            if (mr == null) return;

            Shader shader = Shader.Find("Universal Render Pipeline/Lit") 
                         ?? Shader.Find("Standard") 
                         ?? Shader.Find("Diffuse");

            var mat = new Material(shader) { name = $"{go.name}_Material" };
            Color c = (col != null && col.Length >= 3)
                ? new Color(col[0], col[1], col[2], col.Length >= 4 ? col[3] : 1f)
                : new Color(0.8f, 0.8f, 0.8f, 1f);

            if (mat.HasProperty("_BaseColor")) mat.SetColor("_BaseColor", c);
            else if (mat.HasProperty("_Color")) mat.SetColor("_Color", c);

            if (mat.HasProperty("_Metallic")) mat.SetFloat("_Metallic", Mathf.Clamp01(metallic));
            if (mat.HasProperty("_Smoothness")) mat.SetFloat("_Smoothness", Mathf.Clamp01(smoothness));
            else if (mat.HasProperty("_Glossiness")) mat.SetFloat("_Glossiness", Mathf.Clamp01(smoothness));

            if (emission != null && emission.Length >= 3 && (emission[0] > 0.02f || emission[1] > 0.02f || emission[2] > 0.02f))
            {
                // Soft, balanced HDR emission (0.22f scale) that preserves rich color saturation
                // and stays comfortably within URP Post-Processing volume bloom threshold
                float emissionScale = 0.22f;
                Color emColor = new Color(emission[0] * emissionScale, emission[1] * emissionScale, emission[2] * emissionScale);
                if (mat.HasProperty("_EmissionColor"))
                {
                    mat.EnableKeyword("_EMISSION");
                    mat.SetColor("_EmissionColor", emColor);
                }

                // If the requested base albedo was near-white (or defaulted to white), tint it down
                // so the 2.0x directional sun doesn't multiply with white diffuse into blinding white bloom flares
                if (c.r > 0.75f && c.g > 0.75f && c.b > 0.75f)
                {
                    Color tintedAlbedo = new Color(
                        Mathf.Max(0.12f, emission[0] * 0.45f),
                        Mathf.Max(0.12f, emission[1] * 0.45f),
                        Mathf.Max(0.12f, emission[2] * 0.45f),
                        1f
                    );
                    if (mat.HasProperty("_BaseColor")) mat.SetColor("_BaseColor", tintedAlbedo);
                    else if (mat.HasProperty("_Color")) mat.SetColor("_Color", tintedAlbedo);
                }
            }

            mr.sharedMaterial = mat;
        }

        [Serializable]
        public class CaptureRequest
        {
            public int width = 1024;
            public int height = 1024;
            public float[] camera_position = null;
            public float[] camera_target = null;
            public string save_path = null;
        }

        private static string CaptureViewport(string json)
        {
            var req = JsonUtility.FromJson<CaptureRequest>(json) ?? new CaptureRequest();
            int width = Mathf.Clamp(req.width, 256, 4096);
            int height = Mathf.Clamp(req.height, 256, 4096);

            // Focus camera on ForgeArtisan_Workspace
            var workspace = GameObject.Find("ForgeArtisan_Workspace");
            Camera cam = Camera.main;

            GameObject tempCamGo = null;
            if (cam == null)
            {
                tempCamGo = new GameObject("ForgeArtisan_CaptureCam");
                cam = tempCamGo.AddComponent<Camera>();
                cam.clearFlags = CameraClearFlags.SolidColor;
                cam.backgroundColor = new Color(0.12f, 0.12f, 0.14f);
            }

            if (req.camera_position != null && req.camera_position.Length >= 3)
            {
                cam.transform.position = new Vector3(req.camera_position[0], req.camera_position[1], req.camera_position[2]);
                if (req.camera_target != null && req.camera_target.Length >= 3)
                {
                    cam.transform.LookAt(new Vector3(req.camera_target[0], req.camera_target[1], req.camera_target[2]));
                }
            }
            else if (workspace != null)
            {
                Bounds bounds = GetRenderBounds(workspace);
                Vector3 center = bounds.center;
                float radius = Mathf.Max(bounds.size.x, Mathf.Max(bounds.size.y, bounds.size.z));
                if (radius < 0.1f) radius = 5f;

                cam.transform.position = center + new Vector3(radius * 1.5f, radius * 1.2f, -radius * 1.8f);
                cam.transform.LookAt(center);
            }

            var rt = new RenderTexture(width, height, 24);
            cam.targetTexture = rt;
            cam.Render();

            RenderTexture.active = rt;
            var tex = new Texture2D(width, height, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, width, height), 0, 0);
            tex.Apply();

            cam.targetTexture = null;
            RenderTexture.active = null;
            RenderTexture.DestroyImmediate(rt);

            if (tempCamGo != null)
            {
                UnityEngine.Object.DestroyImmediate(tempCamGo);
            }

            byte[] bytes = tex.EncodeToPNG();
            UnityEngine.Object.DestroyImmediate(tex);

            string base64 = Convert.ToBase64String(bytes);

            string savedFile = null;
            if (!string.IsNullOrEmpty(req.save_path))
            {
                try
                {
                    File.WriteAllBytes(req.save_path, bytes);
                    savedFile = req.save_path;
                }
                catch { }
            }

            return JsonSuccess(new Dictionary<string, object>
            {
                ["width"] = width,
                ["height"] = height,
                ["saved_path"] = savedFile,
                ["image_base64"] = base64
            });
        }

        private static Bounds GetRenderBounds(GameObject go)
        {
            var renderers = go.GetComponentsInChildren<Renderer>();
            if (renderers.Length == 0) return new Bounds(go.transform.position, Vector3.one * 2f);

            Bounds b = renderers[0].bounds;
            for (int i = 1; i < renderers.Length; i++)
            {
                b.Encapsulate(renderers[i].bounds);
            }
            return b;
        }

        #endregion

        #region Helper Json Serializer

        private static string JsonSuccess(Dictionary<string, object> data)
        {
            var sb = new StringBuilder();
            sb.Append("{\"success\":true");
            foreach (var kvp in data)
            {
                sb.Append($",\"{kvp.Key}\":{ToJsonValue(kvp.Value)}");
            }
            sb.Append("}");
            return sb.ToString();
        }

        private static string JsonError(string message)
        {
            return $"{{\"success\":false,\"error\":\"{EscapeJson(message)}\"}}";
        }

        private static string ToJsonValue(object val)
        {
            if (val == null) return "null";
            if (val is bool b) return b ? "true" : "false";
            if (val is int || val is long || val is float || val is double) return val.ToString();
            if (val is string s) return $"\"{EscapeJson(s)}\"";
            return $"\"{EscapeJson(val.ToString())}\"";
        }

        private static string EscapeJson(string s)
        {
            if (string.IsNullOrEmpty(s)) return "";
            return s.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", "\\n").Replace("\r", "\\r");
        }

        #endregion
    }

    /// <summary>
    /// Algorithmic procedural geometry generators for chamfers, bevels, wedges, and curved surfaces.
    /// </summary>
    public static class ProceduralMeshGenerators
    {
        public static Mesh CreateChamferedBox(float width, float height, float depth, float chamfer)
        {
            float hx = width * 0.5f;
            float hy = height * 0.5f;
            float hz = depth * 0.5f;
            float c = Mathf.Min(chamfer, Mathf.Min(hx, Mathf.Min(hy, hz)) * 0.5f);

            var mesh = new Mesh();
            var verts = new List<Vector3>();
            var tris = new List<int>();

            // Generate 8 corner vertices pushed inwards by chamfer
            // and build faces with beveled edge loops
            Vector3[] corners = new Vector3[]
            {
                new Vector3(-hx, -hy, -hz), new Vector3(hx, -hy, -hz),
                new Vector3(hx, -hy, hz),  new Vector3(-hx, -hy, hz),
                new Vector3(-hx, hy, -hz),  new Vector3(hx, hy, -hz),
                new Vector3(hx, hy, hz),   new Vector3(-hx, hy, hz)
            };

            // Standard beveled box cube subdivision
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            var baseMesh = go.GetComponent<MeshFilter>().sharedMesh;
            Vector3[] bVerts = baseMesh.vertices;
            int[] bTris = baseMesh.triangles;
            Vector2[] bUv = baseMesh.uv;

            // Apply chamfer smoothing to outer vertices
            Vector3[] resVerts = new Vector3[bVerts.Length];
            for (int i = 0; i < bVerts.Length; i++)
            {
                Vector3 v = bVerts[i];
                resVerts[i] = new Vector3(
                    Mathf.Sign(v.x) * (hx - c + Mathf.Abs(v.x) * c),
                    Mathf.Sign(v.y) * (hy - c + Mathf.Abs(v.y) * c),
                    Mathf.Sign(v.z) * (hz - c + Mathf.Abs(v.z) * c)
                );
            }

            GameObject.DestroyImmediate(go);

            mesh.vertices = resVerts;
            mesh.triangles = bTris;
            mesh.uv = bUv;
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            return mesh;
        }

        public static Mesh CreateWedge(float width, float height, float length)
        {
            var mesh = new Mesh();
            float hx = width * 0.5f;
            float hy = height * 0.5f;
            float hz = length * 0.5f;

            // 18 vertices with dedicated face normals for crisp shading
            Vector3[] verts = new Vector3[]
            {
                // Bottom face (-Y): 0..3
                new Vector3(-hx, -hy, -hz),
                new Vector3( hx, -hy, -hz),
                new Vector3( hx, -hy,  hz),
                new Vector3(-hx, -hy,  hz),

                // Back vertical face (-Z): 4..7
                new Vector3(-hx, -hy, -hz),
                new Vector3(-hx,  hy, -hz),
                new Vector3( hx,  hy, -hz),
                new Vector3( hx, -hy, -hz),

                // Sloped top roof face (+Y, +Z): 8..11
                new Vector3(-hx,  hy, -hz),
                new Vector3(-hx, -hy,  hz),
                new Vector3( hx, -hy,  hz),
                new Vector3( hx,  hy, -hz),

                // Left triangular gable (-X): 12..14
                new Vector3(-hx, -hy, -hz),
                new Vector3(-hx, -hy,  hz),
                new Vector3(-hx,  hy, -hz),

                // Right triangular gable (+X): 15..17
                new Vector3( hx, -hy, -hz),
                new Vector3( hx,  hy, -hz),
                new Vector3( hx, -hy,  hz)
            };

            int[] tris = new int[]
            {
                // Bottom face (-Y): normal pointing down
                0, 1, 2,  0, 2, 3,

                // Back vertical face (-Z): normal pointing back
                4, 5, 6,  4, 6, 7,

                // Sloped face (+Y, +Z): normal pointing up & forward
                8, 9, 10,  8, 10, 11,

                // Left triangle (-X): normal pointing left
                12, 13, 14,

                // Right triangle (+X): normal pointing right
                15, 16, 17
            };

            Vector2[] uvs = new Vector2[]
            {
                // Bottom
                new Vector2(0, 0), new Vector2(1, 0), new Vector2(1, 1), new Vector2(0, 1),
                // Back
                new Vector2(0, 0), new Vector2(0, 1), new Vector2(1, 1), new Vector2(1, 0),
                // Sloped roof
                new Vector2(0, 0), new Vector2(0, 1), new Vector2(1, 1), new Vector2(1, 0),
                // Left
                new Vector2(0, 0), new Vector2(1, 0), new Vector2(0, 1),
                // Right
                new Vector2(1, 0), new Vector2(1, 1), new Vector2(0, 0)
            };

            Vector3 slopedNormal = Vector3.Normalize(new Vector3(0f, hz, hy));
            Vector3[] normals = new Vector3[]
            {
                // Bottom (-Y): 0..3
                Vector3.down, Vector3.down, Vector3.down, Vector3.down,
                // Back (-Z): 4..7
                Vector3.back, Vector3.back, Vector3.back, Vector3.back,
                // Sloped (+Y, +Z): 8..11
                slopedNormal, slopedNormal, slopedNormal, slopedNormal,
                // Left (-X): 12..14
                Vector3.left, Vector3.left, Vector3.left,
                // Right (+X): 15..17
                Vector3.right, Vector3.right, Vector3.right
            };

            mesh.vertices = verts;
            mesh.triangles = tris;
            mesh.normals = normals;
            mesh.uv = uvs;
            mesh.RecalculateBounds();
            return mesh;
        }

        public static Mesh CreateCowcatcher(float width, float height, float length)
        {
            var mesh = new Mesh();
            float hx = width * 0.5f;
            float hy = height * 0.5f;
            float hz = length * 0.5f;

            // Centered cowcatcher wedge with tapered front plow apex
            Vector3[] verts = new Vector3[]
            {
                new Vector3(-hx, -hy, -hz), // 0: back bottom left
                new Vector3( hx, -hy, -hz), // 1: back bottom right
                new Vector3(  0, -hy,  hz), // 2: front apex bottom
                new Vector3(-hx,  hy, -hz), // 3: back top left
                new Vector3( hx,  hy, -hz), // 4: back top right
                new Vector3(  0, -hy * 0.6f, hz) // 5: front apex top
            };

            int[] tris = new int[]
            {
                // Bottom
                0, 2, 1,
                // Back
                0, 1, 4, 0, 4, 3,
                // Left slope
                0, 3, 5, 0, 5, 2,
                // Right slope
                1, 2, 5, 1, 5, 4,
                // Top slope
                3, 4, 5
            };

            mesh.vertices = verts;
            mesh.triangles = tris;
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            return mesh;
        }

        public static Mesh CreateTriangularPrism(float width, float height, float length)
        {
            return CreateWedge(width, height, length);
        }

        public static Mesh CreateBarrelLid(float width, float height, float length, int segments = 16)
        {
            var mesh = new Mesh();
            float hx = width * 0.5f;
            float hy = height;
            float hz = length * 0.5f;

            var verts = new List<Vector3>();
            var uvs = new List<Vector2>();
            var tris = new List<int>();

            // 1. Curved roof vault (along Z, arched in XY)
            for (int s = 0; s <= segments; s++)
            {
                float t = (float)s / segments;
                float angle = Mathf.PI * t;
                float x = -hx * Mathf.Cos(angle);
                float y = hy * Mathf.Sin(angle) - hy * 0.5f;

                verts.Add(new Vector3(x, y, -hz));
                uvs.Add(new Vector2(t, 0f));

                verts.Add(new Vector3(x, y, hz));
                uvs.Add(new Vector2(t, 1f));
            }

            for (int s = 0; s < segments; s++)
            {
                int b0 = s * 2;
                int f0 = s * 2 + 1;
                int b1 = (s + 1) * 2;
                int f1 = (s + 1) * 2 + 1;

                // Outward vault face
                tris.Add(b0); tris.Add(b1); tris.Add(f1);
                tris.Add(b0); tris.Add(f1); tris.Add(f0);
                // Double-sided inner support
                tris.Add(b0); tris.Add(f1); tris.Add(b1);
                tris.Add(b0); tris.Add(f0); tris.Add(f1);
            }

            // 2. Flat bottom floor (-Y)
            int botBase = verts.Count;
            verts.Add(new Vector3(-hx, -hy * 0.5f, -hz));
            verts.Add(new Vector3( hx, -hy * 0.5f, -hz));
            verts.Add(new Vector3( hx, -hy * 0.5f,  hz));
            verts.Add(new Vector3(-hx, -hy * 0.5f,  hz));
            uvs.Add(new Vector2(0, 0)); uvs.Add(new Vector2(1, 0));
            uvs.Add(new Vector2(1, 1)); uvs.Add(new Vector2(0, 1));

            // Outward + Inward bottom floor
            tris.Add(botBase); tris.Add(botBase + 1); tris.Add(botBase + 2);
            tris.Add(botBase); tris.Add(botBase + 2); tris.Add(botBase + 3);
            tris.Add(botBase); tris.Add(botBase + 2); tris.Add(botBase + 1);
            tris.Add(botBase); tris.Add(botBase + 3); tris.Add(botBase + 2);

            // 3. Front arch end cap (z = hz)
            int frontCenter = verts.Count;
            verts.Add(new Vector3(0, -hy * 0.5f, hz));
            uvs.Add(new Vector2(0.5f, 0.5f));
            int frontArcStart = verts.Count;
            for (int s = 0; s <= segments; s++)
            {
                float t = (float)s / segments;
                float angle = Mathf.PI * t;
                float x = -hx * Mathf.Cos(angle);
                float y = hy * Mathf.Sin(angle) - hy * 0.5f;
                verts.Add(new Vector3(x, y, hz));
                uvs.Add(new Vector2(t, 1f));
            }
            for (int s = 0; s < segments; s++)
            {
                // Outward (+Z)
                tris.Add(frontCenter);
                tris.Add(frontArcStart + s + 1);
                tris.Add(frontArcStart + s);
                // Inward
                tris.Add(frontCenter);
                tris.Add(frontArcStart + s);
                tris.Add(frontArcStart + s + 1);
            }

            // 4. Back arch end cap (z = -hz)
            int backCenter = verts.Count;
            verts.Add(new Vector3(0, -hy * 0.5f, -hz));
            uvs.Add(new Vector2(0.5f, 0.5f));
            int backArcStart = verts.Count;
            for (int s = 0; s <= segments; s++)
            {
                float t = (float)s / segments;
                float angle = Mathf.PI * t;
                float x = -hx * Mathf.Cos(angle);
                float y = hy * Mathf.Sin(angle) - hy * 0.5f;
                verts.Add(new Vector3(x, y, -hz));
                uvs.Add(new Vector2(t, 0f));
            }
            for (int s = 0; s < segments; s++)
            {
                // Outward (-Z)
                tris.Add(backCenter);
                tris.Add(backArcStart + s);
                tris.Add(backArcStart + s + 1);
                // Inward
                tris.Add(backCenter);
                tris.Add(backArcStart + s + 1);
                tris.Add(backArcStart + s);
            }

            mesh.vertices = verts.ToArray();
            mesh.triangles = tris.ToArray();
            mesh.uv = uvs.ToArray();
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            return mesh;
        }

        public static Mesh CreateTorus(float radius, float tubeRadius, int radialSegments = 16, int tubularSegments = 24)
        {
            var mesh = new Mesh();
            var verts = new List<Vector3>();
            var uvs = new List<Vector2>();
            var tris = new List<int>();

            for (int i = 0; i <= tubularSegments; i++)
            {
                float u = (float)i / tubularSegments * Mathf.PI * 2f;
                float cu = Mathf.Cos(u);
                float su = Mathf.Sin(u);

                for (int j = 0; j <= radialSegments; j++)
                {
                    float v = (float)j / radialSegments * Mathf.PI * 2f;
                    float cv = Mathf.Cos(v);
                    float sv = Mathf.Sin(v);

                    float x = (radius + tubeRadius * cv) * cu;
                    float y = tubeRadius * sv;
                    float z = (radius + tubeRadius * cv) * su;

                    verts.Add(new Vector3(x, y, z));
                    uvs.Add(new Vector2((float)i / tubularSegments, (float)j / radialSegments));
                }
            }

            for (int i = 0; i < tubularSegments; i++)
            {
                for (int j = 0; j < radialSegments; j++)
                {
                    int a = i * (radialSegments + 1) + j;
                    int b = (i + 1) * (radialSegments + 1) + j;
                    int c = (i + 1) * (radialSegments + 1) + (j + 1);
                    int d = i * (radialSegments + 1) + (j + 1);

                    // Outward normals
                    tris.Add(a); tris.Add(d); tris.Add(b);
                    tris.Add(b); tris.Add(d); tris.Add(c);
                    // Double-sided inward support
                    tris.Add(a); tris.Add(b); tris.Add(d);
                    tris.Add(b); tris.Add(c); tris.Add(d);
                }
            }

            mesh.vertices = verts.ToArray();
            mesh.triangles = tris.ToArray();
            mesh.uv = uvs.ToArray();
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            return mesh;
        }
    }
}
#endif
