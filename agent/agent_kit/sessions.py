"""Session Management for Multi-Chat & Model Workspaces."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from agent_kit import settings


def sessions_dir() -> Path:
    d = settings.workspace_dir() / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def create_session(title: str = "New Craft Session") -> dict:
    session_id = f"sess_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    now = time.time()
    data = {
        "id": session_id,
        "title": title,
        "created_at": now,
        "updated_at": now,
        "prompt": "",
        "status": "idle",
        "turns_count": 0,
        "steps": [],
        "snapshots_pass1": None,
        "snapshots_pass2": None,
        "pass1_critique": None,
        "pass2_critique": None,
        "critique": None,
        "manifest": None,
        "model_parts": []
    }
    file = sessions_dir() / f"{session_id}.json"
    file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def list_sessions() -> list[dict]:
    d = sessions_dir()
    sessions = []
    for f in sorted(d.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            sessions.append({
                "id": data.get("id"),
                "title": data.get("title", "Untitled Session"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "status": data.get("status", "idle"),
                "turns_count": data.get("turns_count", 0),
                "asset_title": (data.get("manifest") or {}).get("asset_title", "")
            })
        except Exception:
            continue

    if not sessions:
        # Create an initial default session
        default = create_session("Steam Locomotive Session")
        sessions.append({
            "id": default["id"],
            "title": default["title"],
            "created_at": default["created_at"],
            "updated_at": default["updated_at"],
            "status": "idle",
            "turns_count": 0,
            "asset_title": ""
        })

    return sessions


def get_session(session_id: str) -> dict | None:
    file = sessions_dir() / f"{session_id}.json"
    if not file.exists():
        return None
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_session(session_id: str, updates: dict) -> dict:
    file = sessions_dir() / f"{session_id}.json"
    if file.exists():
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except Exception:
            data = {"id": session_id}
    else:
        data = {"id": session_id, "created_at": time.time()}

    data.update(updates)
    data["updated_at"] = time.time()
    file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def delete_session(session_id: str) -> bool:
    file = sessions_dir() / f"{session_id}.json"
    if file.exists():
        try:
            file.unlink()
            return True
        except Exception:
            return False
    return False
