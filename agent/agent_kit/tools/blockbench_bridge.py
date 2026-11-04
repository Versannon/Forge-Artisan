"""Blockbench Voxel Studio Bridge & .bbmodel Exporter.

Converts 3D compound geometry specifications into native Blockbench JSON (.bbmodel)
files compatible with Blockbench, Minecraft bedrock/java models, and low-poly game pipelines.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


WORKSPACE_DIR = Path(r"C:\Soham\Repositories\Hackathon-meta\forge-artisan\workspace")
BLOCKBENCH_PROJECT_DIR = Path(r"C:\Soham\UE_projects\BharatRailSimulator(assests)\blockbench")


def convert_spec_to_bbmodel(spec: dict) -> dict[str, Any]:
    """Converts a compound model specification into a valid Blockbench .bbmodel JSON structure."""
    root_name = spec.get("root_name", "VoxelAsset")
    parts = spec.get("parts", [])

    elements = []
    outliner = []

    for idx, p in enumerate(parts):
        name = p.get("name", f"Cube_{idx}")
        pos = p.get("position", [0, 0, 0])
        s = p.get("scale", [1, 1, 1])

        # Blockbench units: 16 units = 1 meter
        bx = pos[0] * 16.0
        by = pos[1] * 16.0
        bz = pos[2] * 16.0
        bw = max(1.0, s[0] * 16.0)
        bh = max(1.0, s[1] * 16.0)
        bd = max(1.0, s[2] * 16.0)

        elem_id = f"elem_{idx}"
        elem = {
            "name": name,
            "box_uv": True,
            "rescale": False,
            "locked": False,
            "from": [round(bx - bw/2, 2), round(by, 2), round(bz - bd/2, 2)],
            "to": [round(bx + bw/2, 2), round(by + bh, 2), round(bz + bd/2, 2)],
            "autouv": 0,
            "color": idx % 8,
            "origin": [round(bx, 2), round(by, 2), round(bz, 2)],
            "faces": {
                "north": {"uv": [0, 0, 16, 16], "texture": None},
                "east": {"uv": [0, 0, 16, 16], "texture": None},
                "south": {"uv": [0, 0, 16, 16], "texture": None},
                "west": {"uv": [0, 0, 16, 16], "texture": None},
                "up": {"uv": [0, 0, 16, 16], "texture": None},
                "down": {"uv": [0, 0, 16, 16], "texture": None}
            },
            "uuid": elem_id
        }
        elements.append(elem)
        outliner.append(elem_id)

    bbmodel = {
        "meta": {
            "format_version": "4.5",
            "model_format": "free",
            "box_uv": True
        },
        "name": root_name,
        "geometry_name": root_name,
        "visible_box": [1, 1, 0],
        "variable_placeholders": "",
        "variable_placeholder_buttons": [],
        "timeline": {},
        "resolution": {"width": 64, "height": 64},
        "elements": elements,
        "outliner": outliner,
        "textures": []
    }

    return bbmodel


def build_in_blockbench(spec: dict) -> dict[str, Any]:
    """Generates and writes a .bbmodel file for Blockbench."""
    root_name = spec.get("root_name", "VoxelAsset")
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

    bbmodel_data = convert_spec_to_bbmodel(spec)
    out_file = WORKSPACE_DIR / f"{root_name}.bbmodel"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(bbmodel_data, f, indent=2)

    # Copy to project blockbench directory if available
    if BLOCKBENCH_PROJECT_DIR.exists():
        try:
            with open(BLOCKBENCH_PROJECT_DIR / f"{root_name}.bbmodel", "w", encoding="utf-8") as f:
                json.dump(bbmodel_data, f, indent=2)
        except Exception:
            pass

    return {
        "success": True,
        "engine": "blockbench",
        "bbmodel_path": str(out_file),
        "elements_count": len(bbmodel_data.get("elements", []))
    }
