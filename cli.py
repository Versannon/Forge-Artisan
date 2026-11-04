"""ForgeArtisan CLI: Unified Command-Line Interface."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

# Add agent directory to sys.path
AGENT_DIR = Path(__file__).resolve().parent / "agent"
sys.path.insert(0, str(AGENT_DIR))

from agent_kit import client as client_module
from agent_kit.tools import unity_bridge
from artisan_agent import loop


def cmd_status(args):
    print("🔍 Checking Unity Editor Bridge connection...")
    res = unity_bridge.run({})
    if res.get("status") == "connected":
        print(f"✅ Connected to Unity {res.get('unity_version')} (Scene: {res.get('active_scene')}) at {res.get('url')}")
    else:
        print(f"⚠️  {res.get('message')}")


def cmd_run(args):
    prompt = args.prompt
    turns = args.turns
    print(f"⚒️  ForgeArtisan starting autonomous craft run...")
    print(f"🎯 Objective: {prompt}")

    root = Path(__file__).resolve().parent
    c = client_module.make_client()

    def on_step(s):
        print(f"   [Turn {s['turn']}] ⚙️  {s['action']} -> {s.get('args', '')[:70]}...")

    result = loop.run_agent(
        root=root,
        client=c,
        prompt=prompt,
        turns=turns,
        on_step_callback=on_step
    )

    print(f"\n🎉 Run completed with status: {result.get('status')}")
    print(f"📁 Manifest & logs saved to: {root / 'workspace'}")


def cmd_ui(args):
    print(f"🌐 Starting ForgeArtisan Web Studio on http://{args.host}:{args.port} ...")
    from web_ui import app as web_app
    web_app.start_server(host=args.host, port=args.port)


def cmd_mcp(args):
    from mcp_server import server
    server.run_stdio()


def cmd_install_unity(args):
    dest = Path(args.unity_project)
    if not dest.exists():
        print(f"❌ Error: Path does not exist: {dest}")
        sys.exit(1)

    assets_editor = dest / "Assets" / "Editor"
    assets_editor.mkdir(parents=True, exist_ok=True)

    src = Path(__file__).resolve().parent / "unity_package" / "ForgeArtisanBridge.cs"
    target = assets_editor / "ForgeArtisanBridge.cs"

    shutil.copyfile(src, target)
    print(f"✅ Successfully installed ForgeArtisanBridge.cs into: {target}")
    print("Open your Unity Editor to activate the bridge.")


def cmd_dev(args):
    from dev import main as dev_main
    dev_main()


def main():
    parser = argparse.ArgumentParser(
        prog="forge-artisan",
        description="ForgeArtisan: Autonomous 3D Technical Artist & Engine MCP Copilot"
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # dev
    p_dev = subparsers.add_parser("dev", help="Launch in hot-reload dev mode (no rebuild needed).")
    p_dev.set_defaults(func=cmd_dev)

    # run
    p_run = subparsers.add_parser("run", help="Run the autonomous 3D artist agent on a prompt.")
    p_run.add_argument("prompt", type=str, help="What 3D model or environment to create.")
    p_run.add_argument("--turns", type=int, default=10, help="Maximum agent turns (default: 10).")
    p_run.set_defaults(func=cmd_run)

    # ui
    p_ui = subparsers.add_parser("ui", help="Launch the local web studio.")
    p_ui.add_argument("--host", type=str, default="0.0.0.0", help="Host interface (default: 0.0.0.0)")
    p_ui.add_argument("--port", type=int, default=7860, help="Port (default: 7860)")
    p_ui.set_defaults(func=cmd_ui)

    # mcp
    p_mcp = subparsers.add_parser("mcp", help="Run as a Model Context Protocol (MCP) server over stdio.")
    p_mcp.set_defaults(func=cmd_mcp)

    # status
    p_status = subparsers.add_parser("status", help="Check status of connected game engines (Unity).")
    p_status.set_defaults(func=cmd_status)

    # install-bridge
    p_bridge = subparsers.add_parser("install-unity-bridge", help="Install ForgeArtisanBridge into a Unity project.")
    p_bridge.add_argument("unity_project", type=str, help="Path to Unity project root folder.")
    p_bridge.set_defaults(func=cmd_install_unity)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
