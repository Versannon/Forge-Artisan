"""ForgeArtisan Tools Module: Definitions and Execution Dispatcher."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from openai import OpenAI

from agent_kit.tools import (
    critic_sam,
    material,
    modeler,
    research_reference,
    submit_artifact,
    unity_bridge,
)

_TOOLS = {
    "research_reference": research_reference,
    "unity_status": unity_bridge,
    "build_compound_model": modeler,
    "set_pbr_material": material,
    "critique_visual_render": critic_sam,
    "submit_crafted_asset": submit_artifact,
}


def definitions(root: Path | None = None, run_id: str | None = None) -> list[dict]:
    """Returns tool schemas compatible with OpenAI / Meta Model API."""
    return [mod.tool_definition() for mod in _TOOLS.values()]


def run(client: OpenAI, root: Path, run_id: str, call: Any) -> dict[str, Any]:
    """Dispatches a function call returned by the model."""
    name = call.function.name if hasattr(call, "function") else call.get("name")
    raw_args = call.function.arguments if hasattr(call, "function") else call.get("arguments", "{}")

    if isinstance(raw_args, str):
        try:
            args = json.loads(raw_args)
        except Exception:
            args = {}
    else:
        args = raw_args or {}

    module = _TOOLS.get(name)
    if not module:
        return {
            "status": "error",
            "message": f"Tool '{name}' is not recognized. Available tools: {list(_TOOLS.keys())}"
        }

    try:
        return module.run(args)
    except Exception as ex:
        return {
            "status": "error",
            "message": f"Execution error in tool '{name}': {ex}"
        }
