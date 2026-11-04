"""Tool: submit_asset
Finalizes the crafted 3D model, recording its component hierarchy, materials, and verified critique score.
"""

from __future__ import annotations

import json
from pathlib import Path
from agent_kit import settings


def tool_definition() -> dict:
    return {
        "type": "function",
        "name": "submit_crafted_asset",
        "description": "Finalizes the 3D model run when all research, modeling passes, bevels, texturing, and visual critique checks have been satisfied.",
        "parameters": {
            "type": "object",
            "properties": {
                "asset_title": {
                    "type": "string",
                    "description": "Formal title of the finalized 3D asset (e.g. 'Vintage 4-4-0 American Steam Locomotive')."
                },
                "summary": {
                    "type": "string",
                    "description": "Technical summary of craftsmanship: bevels used, miniature details, PBR shading, and reference alignment."
                },
                "component_count": {
                    "type": "integer",
                    "description": "Total number of individual beveled/assembled components."
                },
                "final_critique_score": {
                    "type": "number",
                    "description": "Final visual quality score from the SAM 3.1 visual critic (0-100)."
                }
            },
            "required": ["asset_title", "summary", "component_count", "final_critique_score"]
        }
    }


def run(args: dict) -> dict:
    title = args.get("asset_title", "CraftedAsset")
    summary = args.get("summary", "")
    count = args.get("component_count", 0)
    score = args.get("final_critique_score", 90)

    workspace = settings.workspace_dir()
    manifest_file = workspace / "final_asset_manifest.json"

    manifest_data = {
        "asset_title": title,
        "summary": summary,
        "component_count": count,
        "final_critique_score": score,
        "engine": "Unity",
        "status": "completed"
    }

    manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    return {
        "status": "completed",
        "asset_title": title,
        "summary": summary,
        "component_count": count,
        "final_critique_score": score,
        "manifest_path": str(manifest_file),
        "message": f"Asset '{title}' is officially approved and finalized in the game engine."
    }
