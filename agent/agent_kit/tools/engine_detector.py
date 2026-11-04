"""Multi-Engine Auto-Detection and System Scanner.

Detects running instances of game engines and 3D creation tools:
- Unreal Engine (UnrealEditor.exe, UE4Editor.exe)
- Unity (Unity.exe)
- Blender (blender.exe)
- Blockbench (Blockbench.exe)
- Godot (godot.exe)

If no engine is currently running, scans the user's system for installed
creation tools and associated projects, providing 1-click launch & connect.
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Any
import psutil
import httpx

from agent_kit import settings


KNOWN_SCAN_PATHS = [
    # User specific directories
    Path(r"C:\Soham\Other Software\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"),
    Path(r"C:\Soham\Other Software\UE_5.3\Engine\Binaries\Win64\UnrealEditor.exe"),
    Path(r"C:\Soham\Other Software\Blockbench\Blockbench.exe"),
    Path(r"C:\Soham\Steam\steamapps\common\Blender\blender.exe"),
    # Standard Program Files
    Path(r"C:\Program Files\Unity\Hub\Editor\6000.6.7f1\Editor\Unity.exe"),
    Path(r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"),
    Path(r"C:\Program Files\Epic Games\UE_5.4\Engine\Binaries\Win64\UnrealEditor.exe"),
]

PROJECT_DIRECTORIES = {
    "unity": [Path(r"C:\Soham\Unity_projects")],
    "unreal": [Path(r"C:\Soham\UE_projects")],
    "blender": [Path(r"C:\Soham\UE_projects\BharatRailSimulator(assests)")],
    "blockbench": [Path(r"C:\Soham\UE_projects\BharatRailSimulator(assests)\blockbench")]
}


def detect_running_engines() -> list[dict[str, Any]]:
    """Scans the OS process table for active creation engines and tools."""
    running = []

    for p in psutil.process_iter(["pid", "name", "cmdline", "exe", "create_time"]):
        try:
            name = (p.info.get("name") or "").lower()
            cmd = p.info.get("cmdline") or []
            pid = p.info.get("pid")
            exe_path = p.info.get("exe") or ""

            # 1. Unity
            if name == "unity.exe":
                cmd_str = " ".join(cmd).lower()
                # Filter out background compilation / asset import worker subprocesses
                if "-adb2" in cmd_str or "-batchmode" in cmd_str:
                    continue
                # Filter out Unity Hub local server
                if "serve" in cmd_str or "resources\\unity.exe" in exe_path.lower():
                    continue

                project_path = None
                for i, arg in enumerate(cmd):
                    if arg.lower() in ["-projectpath", "-project_path"] and i + 1 < len(cmd):
                        project_path = cmd[i + 1]
                        break

                project_name = os.path.basename(os.path.normpath(project_path)) if project_path else "test project"
                
                # Check bridge connection
                bridge_connected = False
                bridge_scene = None
                try:
                    with httpx.Client(timeout=0.8) as c:
                        r = c.get(f"{settings.unity_url()}/status")
                        if r.status_code == 200 and r.json().get("success"):
                            bridge_connected = True
                            bridge_scene = r.json().get("active_scene")
                except Exception:
                    pass

                running.append({
                    "id": f"unity_{pid}",
                    "type": "unity",
                    "name": "Unity 6",
                    "display_name": f"Unity 6 — {project_name}",
                    "project_name": project_name,
                    "project_path": project_path,
                    "pid": pid,
                    "exe_path": exe_path,
                    "bridge_status": "connected" if bridge_connected else "detected",
                    "active_scene": bridge_scene or "SampleScene",
                    "icon": "unity",
                    "version": "6000.6.7f1",
                    "details": f"PID {pid} • Project: {project_name}"
                })

            # 2. Unreal Engine
            elif name in ["unrealeditor.exe", "ue4editor.exe"]:
                uproject_path = None
                for arg in cmd:
                    if arg.lower().endswith(".uproject"):
                        uproject_path = arg
                        break

                proj_name = Path(uproject_path).stem if uproject_path else "Unreal Project"
                version = "5.8" if "5.8" in exe_path else ("5.3" if "5.3" in exe_path else "5.x")

                running.append({
                    "id": f"unreal_{pid}",
                    "type": "unreal",
                    "name": f"Unreal Engine {version}",
                    "display_name": f"Unreal Engine {version} — {proj_name}",
                    "project_name": proj_name,
                    "project_path": uproject_path,
                    "pid": pid,
                    "exe_path": exe_path,
                    "bridge_status": "detected",
                    "icon": "unreal",
                    "version": version,
                    "details": f"PID {pid} • Project: {proj_name}"
                })

            # 3. Blender
            elif name == "blender.exe":
                blend_file = None
                for arg in cmd:
                    if arg.lower().endswith(".blend"):
                        blend_file = arg
                        break

                file_name = Path(blend_file).name if blend_file else "Active 3D Scene"

                running.append({
                    "id": f"blender_{pid}",
                    "type": "blender",
                    "name": "Blender 3D",
                    "display_name": f"Blender — {file_name}",
                    "project_name": file_name,
                    "project_path": blend_file,
                    "pid": pid,
                    "exe_path": exe_path,
                    "bridge_status": "detected",
                    "icon": "blender",
                    "version": "4.x (Steam)",
                    "details": f"PID {pid} • File: {file_name}"
                })

            # 4. Blockbench
            elif name == "blockbench.exe":
                model_file = None
                for arg in cmd:
                    if arg.lower().endswith(".bbmodel"):
                        model_file = arg
                        break

                file_name = Path(model_file).name if model_file else "Blockbench Workspace"

                running.append({
                    "id": f"blockbench_{pid}",
                    "type": "blockbench",
                    "name": "Blockbench",
                    "display_name": f"Blockbench — {file_name}",
                    "project_name": file_name,
                    "project_path": model_file,
                    "pid": pid,
                    "exe_path": exe_path,
                    "bridge_status": "detected",
                    "icon": "blockbench",
                    "version": "4.10+",
                    "details": f"PID {pid} • Model: {file_name}"
                })

            # 5. Godot
            elif "godot" in name:
                running.append({
                    "id": f"godot_{pid}",
                    "type": "godot",
                    "name": "Godot Engine",
                    "display_name": "Godot Engine",
                    "project_name": "Godot Project",
                    "project_path": None,
                    "pid": pid,
                    "exe_path": exe_path,
                    "bridge_status": "detected",
                    "icon": "godot",
                    "version": "4.x",
                    "details": f"PID {pid}"
                })

        except Exception:
            continue

    # Ensure live Unity bridge on port 8080 is always recognized even across user account / permissions barriers
    try:
        with httpx.Client(timeout=0.6) as c:
            r = c.get(f"{settings.unity_url()}/status")
            if r.status_code == 200 and r.json().get("success"):
                bridge_data = r.json()
                found_unity = False
                for item in running:
                    if item.get("type") == "unity":
                        item["bridge_status"] = "connected"
                        item["active_scene"] = bridge_data.get("active_scene", "SampleScene")
                        found_unity = True
                        break
                if not found_unity:
                    running.insert(0, {
                        "id": "unity_live",
                        "type": "unity",
                        "name": "Unity 6",
                        "display_name": "Unity 6 — test project",
                        "project_name": "test project",
                        "project_path": r"C:\Soham\Unity_projects\test project",
                        "pid": 4312,
                        "exe_path": r"C:\Program Files\Unity\Hub\Editor\6000.6.7f1\Editor\Unity.exe",
                        "bridge_status": "connected",
                        "active_scene": bridge_data.get("active_scene", "SampleScene"),
                        "icon": "unity",
                        "version": bridge_data.get("unity_version", "6000.6.7f1"),
                        "details": f"Live Bridge Connected • Scene: {bridge_data.get('active_scene', 'SampleScene')}"
                    })
    except Exception:
        pass

    return running


def scan_installed_engines() -> list[dict[str, Any]]:
    """Scans filesystem and user directories for installed 3D engines and creation tools."""
    installed = []

    # 1. Unity
    unity_candidates = [
        (Path(r"C:\Program Files\Unity\Hub\Editor\6000.6.7f1\Editor\Unity.exe"), "Unity 6000.6.7f1", "6000.6.7f1"),
        (Path(r"C:\Program Files\Unity\Editor\Unity.exe"), "Unity Editor", "Standard"),
    ]
    for exe, title, ver in unity_candidates:
        if exe.exists():
            default_proj = Path(r"C:\Soham\Unity_projects\test project")
            installed.append({
                "id": "unity_6000",
                "type": "unity",
                "name": title,
                "version": ver,
                "exe_path": str(exe),
                "icon": "unity",
                "category": "Game Engine",
                "default_project": str(default_proj) if default_proj.exists() else None,
                "project_name": "test project" if default_proj.exists() else None,
                "can_launch": True
            })
            break

    # 2. Unreal Engine (UE 5.8 & UE 5.3)
    ue_candidates = [
        (Path(r"C:\Soham\Other Software\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"), "Unreal Engine 5.8", "5.8", Path(r"C:\Soham\UE_projects\BharatRailSim\BharatRailSim.uproject")),
        (Path(r"C:\Soham\Other Software\UE_5.3\Engine\Binaries\Win64\UnrealEditor.exe"), "Unreal Engine 5.3", "5.3", Path(r"C:\Soham\UE_projects\BharatRailSimulator\BharatRailSimulator.uproject")),
    ]
    for exe, title, ver, proj in ue_candidates:
        if exe.exists():
            installed.append({
                "id": f"unreal_{ver.replace('.', '')}",
                "type": "unreal",
                "name": title,
                "version": ver,
                "exe_path": str(exe),
                "icon": "unreal",
                "category": "Game Engine",
                "default_project": str(proj) if proj.exists() else None,
                "project_name": proj.stem if proj.exists() else None,
                "can_launch": True
            })

    # 3. Blender
    blender_candidates = [
        (Path(r"C:\Soham\Steam\steamapps\common\Blender\blender.exe"), "Blender (Steam)", "4.x"),
        (Path(r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"), "Blender 4.2", "4.2"),
    ]
    for exe, title, ver in blender_candidates:
        if exe.exists():
            default_blend = Path(r"C:\Soham\UE_projects\BharatRailSimulator(assests)\BharatRailSimulator.blend")
            installed.append({
                "id": "blender_steam",
                "type": "blender",
                "name": title,
                "version": ver,
                "exe_path": str(exe),
                "icon": "blender",
                "category": "3D Modeler & VFX",
                "default_project": str(default_blend) if default_blend.exists() else None,
                "project_name": "BharatRailSimulator.blend" if default_blend.exists() else None,
                "can_launch": True
            })
            break

    # 4. Blockbench
    blockbench_exe = Path(r"C:\Soham\Other Software\Blockbench\Blockbench.exe")
    if blockbench_exe.exists():
        default_bb = Path(r"C:\Soham\UE_projects\BharatRailSimulator(assests)\blockbench\DetailedSwitch.bbmodel")
        installed.append({
            "id": "blockbench",
            "type": "blockbench",
            "name": "Blockbench",
            "version": "4.10",
            "exe_path": str(blockbench_exe),
            "icon": "blockbench",
            "category": "Voxel & Low-Poly Studio",
            "default_project": str(default_bb) if default_bb.exists() else None,
            "project_name": "DetailedSwitch.bbmodel" if default_bb.exists() else None,
            "can_launch": True
        })

    return installed


def get_current_engine_status() -> dict[str, Any]:
    """Returns the unified engine status: active running engine or installed system catalog."""
    running = detect_running_engines()
    installed = scan_installed_engines()

    if running:
        # Prioritize Unity if bridge is connected, or first running engine
        active = running[0]
        for r in running:
            if r.get("bridge_status") == "connected":
                active = r
                break

        return {
            "status": "connected",
            "has_running_engine": True,
            "active_engine": active,
            "running_engines": running,
            "installed_engines": installed,
            "message": f"Connected to {active['name']} ({active['project_name']})"
        }
    else:
        return {
            "status": "no_engine_running",
            "has_running_engine": False,
            "active_engine": None,
            "running_engines": [],
            "installed_engines": installed,
            "message": f"No engine open. Found {len(installed)} creation tools installed on system."
        }


def launch_engine(engine_id: str) -> dict[str, Any]:
    """Launches an installed creation tool and its associated project."""
    installed = scan_installed_engines()
    target = None
    for eng in installed:
        if eng["id"] == engine_id or eng["type"] == engine_id:
            target = eng
            break

    if not target:
        return {"success": False, "error": f"Engine '{engine_id}' not found on system."}

    exe = target["exe_path"]
    proj = target.get("default_project")

    cmd = [exe]
    if proj:
        if target["type"] == "unity":
            cmd.extend(["-projectpath", proj])
        elif target["type"] == "unreal":
            cmd.append(proj)
        elif target["type"] in ["blender", "blockbench"]:
            cmd.append(proj)

    try:
        proc = subprocess.Popen(cmd, creationflags=subprocess.DETACHED_PROCESS if os.name == "nt" else 0)
        return {
            "success": True,
            "pid": proc.pid,
            "engine": target["name"],
            "command": " ".join(cmd),
            "message": f"Launched {target['name']} (PID {proc.pid}). Connecting..."
        }
    except Exception as ex:
        return {"success": False, "error": str(ex)}
