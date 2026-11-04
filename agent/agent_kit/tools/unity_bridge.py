"""Tool: unity_bridge
Inspects and manages connection with the local Unity Editor instance.
Detects real running Unity processes, exact active project paths, and HTTP RPC bridge status.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
import httpx
import psutil
from agent_kit import settings


def detect_unity_process() -> dict:
    """Inspects OS process table for running Unity Editor instances and project paths."""
    candidates = []
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = p.info.get("name") or ""
            if name.lower() == "unity.exe":
                cmd = p.info.get("cmdline") or []
                # Exclude Hub background worker or licensing processes
                if any(x in [c.lower() for c in cmd] for x in ["-adb2", "serve", "licensingipc"]):
                    # If it has -projectpath, we still want it!
                    pass

                project_path = None
                for i, arg in enumerate(cmd):
                    if arg.lower() in ["-projectpath", "-project_path"] and i + 1 < len(cmd):
                        project_path = cmd[i + 1]
                        break

                if project_path:
                    proj_name = os.path.basename(os.path.normpath(project_path))
                    bridge_file = Path(project_path) / "Assets" / "Editor" / "ForgeArtisanBridge.cs"
                    return {
                        "running": True,
                        "pid": p.info["pid"],
                        "project_path": project_path,
                        "project_name": proj_name,
                        "bridge_installed": bridge_file.exists()
                    }
                else:
                    candidates.append(p.info["pid"])
        except Exception:
            continue

    if candidates:
        return {
            "running": True,
            "pid": candidates[0],
            "project_path": None,
            "project_name": "Unity Editor",
            "bridge_installed": False
        }

    return {
        "running": False,
        "pid": None,
        "project_path": None,
        "project_name": None,
        "bridge_installed": False
    }


def tool_definition() -> dict:
    return {
        "type": "function",
        "name": "unity_status",
        "description": "Checks whether Unity Editor is running, detects the active project name, and verifies HTTP bridge status.",
        "parameters": {
            "type": "object",
            "properties": {
                "clear_workspace": {
                    "type": "boolean",
                    "description": "If true, clears existing generated objects in ForgeArtisan_Workspace."
                }
            }
        }
    }


def run(args: dict) -> dict:
    url = settings.unity_url()
    clear = args.get("clear_workspace", False)
    proc_info = detect_unity_process()

    if not proc_info["running"]:
        return {
            "status": "not_running",
            "connected": False,
            "project_name": None,
            "message": "Unity is not currently running. Please launch your Unity project.",
            "url": url
        }

    project_name = proc_info.get("project_name") or "Unity Project"
    project_path = proc_info.get("project_path")

    # If bridge script is missing in the project, auto-install it
    if project_path and not proc_info["bridge_installed"]:
        try:
            editor_dir = Path(project_path) / "Assets" / "Editor"
            editor_dir.mkdir(parents=True, exist_ok=True)
            src_bridge = settings.root_dir() / "unity_package" / "ForgeArtisanBridge.cs"
            if src_bridge.exists():
                shutil.copy2(src_bridge, editor_dir / "ForgeArtisanBridge.cs")
                proc_info["bridge_installed"] = True
        except Exception:
            pass

    # Now probe the HTTP bridge
    try:
        if clear:
            with httpx.Client(timeout=3.0) as client:
                res = client.post(f"{url}/clear")
                res.raise_for_status()

        with httpx.Client(timeout=3.0) as client:
            res = client.get(f"{url}/status")
            res.raise_for_status()
            data = res.json()
            return {
                "status": "connected",
                "connected": True,
                "engine": data.get("engine", "Unity"),
                "unity_version": data.get("unity_version"),
                "project_name": project_name,
                "project_path": project_path,
                "active_scene": data.get("active_scene", "SampleScene"),
                "workspace_objects": data.get("workspace_objects", 0),
                "url": url,
                "message": f"Connected to Unity project '{project_name}'"
            }
    except Exception:
        # Unity process is running, but the bridge server has not yet initialized
        return {
            "status": "project_detected",
            "connected": False,
            "project_name": project_name,
            "project_path": project_path,
            "bridge_installed": proc_info["bridge_installed"],
            "url": url,
            "message": f"Unity is open with project '{project_name}'. Please click into the Unity Editor window once to compile the bridge."
        }
