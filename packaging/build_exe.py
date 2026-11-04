"""Build script to compile ForgeArtisan into a standalone Windows .exe using PyInstaller."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"


def build():
    print("🔨 Building ForgeArtisan Windows Executable...")

    cli_script = ROOT / "cli.py"

    # PyInstaller flags
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name=forge-artisan",
        "--onedir",
        f"--add-data={ROOT / 'unity_package'};unity_package",
        f"--add-data={ROOT / 'agent'};agent",
        f"--add-data={ROOT / 'mcp_server'};mcp_server",
        f"--add-data={ROOT / 'web_ui'};web_ui",
        "--hidden-import=httpx",
        "--hidden-import=httpcore",
        "--hidden-import=duckduckgo_search",
        "--hidden-import=agent_kit",
        "--hidden-import=agent_kit.client",
        "--hidden-import=agent_kit.progress",
        "--hidden-import=agent_kit.proportional_models",
        "--hidden-import=agent_kit.render_snapshots",
        "--hidden-import=agent_kit.sessions",
        "--hidden-import=agent_kit.settings",
        "--hidden-import=agent_kit.tools",
        "--hidden-import=agent_kit.tools.critic_sam",
        "--hidden-import=agent_kit.tools.material",
        "--hidden-import=agent_kit.tools.modeler",
        "--hidden-import=agent_kit.tools.research_reference",
        "--hidden-import=agent_kit.tools.submit_artifact",
        "--hidden-import=agent_kit.tools.unity_bridge",
        "--hidden-import=agent_kit.tools.engine_detector",
        "--hidden-import=artisan_agent.loop",
        "--hidden-import=uvicorn",
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.protocols.http",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.protocols.websockets",
        "--hidden-import=uvicorn.protocols.websockets.auto",
        "--hidden-import=uvicorn.lifespan",
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=fastapi",
        "--hidden-import=pydantic",
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        "--hidden-import=openai",
        str(cli_script),
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        print("❌ Build failed.")
        sys.exit(result.returncode)

    print("\n✅ Build succeeded!")
    print(f"📦 Dist output located at: {DIST_DIR / 'forge-artisan'}")


if __name__ == "__main__":
    build()
