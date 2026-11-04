"""Agent run progress persistence and checkpointing."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any
from agent_kit import settings


def new_run(root: Path, instructions: str, objective: str) -> str:
    run_id = f"run_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    run_dir = settings.workspace_dir(root) / "runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    data = {
        "run_id": run_id,
        "created_at": time.time(),
        "status": "running",
        "turn": 0,
        "instructions": instructions,
        "objective": objective,
        "messages": [],
        "artifacts": [],
        "critique_history": []
    }
    
    (run_dir / f"{run_id}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    return run_id


def load_progress(root: Path, run_id: str) -> dict[str, Any]:
    file = settings.workspace_dir(root) / "runs" / f"{run_id}.json"
    if not file.exists():
        raise FileNotFoundError(f"Run {run_id} not found at {file}")
    return json.loads(file.read_text(encoding="utf-8"))


def save_progress(
    root: Path,
    run_id: str,
    messages: list[Any],
    response: Any = None,
    status: str = "running",
    error: str | None = None,
    artifacts: list[dict] | None = None,
    critique: dict | None = None
) -> None:
    file = settings.workspace_dir(root) / "runs" / f"{run_id}.json"
    if not file.exists():
        data = {
            "run_id": run_id,
            "created_at": time.time(),
            "status": status,
            "turn": 0,
            "messages": [],
            "artifacts": [],
            "critique_history": []
        }
    else:
        data = json.loads(file.read_text(encoding="utf-8"))

    data["status"] = status
    data["turn"] = data.get("turn", 0) + 1
    data["updated_at"] = time.time()
    
    # Clean messages for JSON serialization
    serialized_msgs = []
    for m in messages:
        if isinstance(m, dict):
            serialized_msgs.append(m)
        elif hasattr(m, "model_dump"):
            serialized_msgs.append(m.model_dump())
        else:
            serialized_msgs.append(str(m))
            
    data["messages"] = serialized_msgs
    
    if error:
        data["error"] = error
    if artifacts:
        data.setdefault("artifacts", []).extend(artifacts)
    if critique:
        data.setdefault("critique_history", []).append(critique)

    file.write_text(json.dumps(data, indent=2), encoding="utf-8")


def list_runs(root: Path) -> list[dict]:
    run_dir = settings.workspace_dir(root) / "runs"
    if not run_dir.exists():
        return []
    runs = []
    for f in sorted(run_dir.glob("*.json"), reverse=True):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            runs.append({
                "run_id": d.get("run_id"),
                "status": d.get("status"),
                "turn": d.get("turn"),
                "created_at": d.get("created_at"),
                "objective": d.get("objective", "")[:60]
            })
        except Exception:
            continue
    return runs
