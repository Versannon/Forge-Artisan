"""Development Mode Server for ForgeArtisan.

Runs the FastAPI backend with uvicorn --reload, allowing live testing
of all code changes without requiring rebuilds or reinstallations.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add agent and forge-artisan root to sys.path
ROOT = Path(__file__).resolve().parent
AGENT_DIR = ROOT / "agent"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(AGENT_DIR))

import uvicorn
import webbrowser
import threading
import time


def main():
    print("==========================================================")
    print("🚀 ForgeArtisan Studio — DEV MODE (Hot-Reload Enabled)")
    print("==========================================================")
    print("🌐 Web Studio URL: http://127.0.0.1:7860")
    print("📁 Watching directories: web_ui, agent")
    print("💡 All changes will automatically hot-reload!")
    print("==========================================================")

    def open_browser():
        time.sleep(1.2)
        try:
            webbrowser.open("http://127.0.0.1:7860")
        except Exception:
            pass

    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run(
        "web_ui.app:app",
        host="0.0.0.0",
        port=7860,
        reload=True,
        reload_dirs=[str(ROOT / "web_ui"), str(ROOT / "agent")],
    )


if __name__ == "__main__":
    main()
