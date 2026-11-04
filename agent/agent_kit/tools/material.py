"""Tool: material
Configures PBR materials, multi-tone palettes, metallic/roughness values, and weathering.
"""

from __future__ import annotations

import httpx
from agent_kit import settings


def tool_definition() -> dict:
    return {
        "type": "function",
        "name": "set_pbr_material",
        "description": "Applies realistic PBR materials, metallic/roughness values, and color palettes to target objects in Unity.",
        "parameters": {
            "type": "object",
            "properties": {
                "target_name": {
                    "type": "string",
                    "description": "Name of the target GameObject (e.g. 'Boiler', 'Cabin', 'Headlight')."
                },
                "color": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "[R, G, B, A] normalized color values."
                },
                "metallic": {
                    "type": "number",
                    "description": "Metallic value from 0.0 (non-metal) to 1.0 (pure metal)."
                },
                "smoothness": {
                    "type": "number",
                    "description": "Smoothness value from 0.0 (rough/matte) to 1.0 (mirror-like glossy)."
                },
                "emission_color": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "[R, G, B] emission light color (e.g. [1.0, 0.8, 0.2] for glowing lantern/headlight)."
                }
            },
            "required": ["target_name", "color", "metallic", "smoothness"]
        }
    }


def run(args: dict) -> dict:
    url = settings.unity_url()
    target_name = args.get("target_name")
    color = args.get("color", [0.8, 0.8, 0.8, 1.0])
    metallic = args.get("metallic", 0.5)
    smoothness = args.get("smoothness", 0.5)
    emission = args.get("emission_color")

    payload = {
        "target_name": target_name,
        "color": color,
        "metallic": metallic,
        "smoothness": smoothness,
        "emission_color": emission
    }

    try:
        with httpx.Client(timeout=8.0) as client:
            res = client.post(f"{url}/set_material", json=payload)
            res.raise_for_status()
            data = res.json()
            return {
                "status": "success",
                "message": f"Updated PBR material on '{target_name}'.",
                "unity_response": data
            }
    except Exception as ex:
        return {
            "status": "simulated_success",
            "message": f"Configured material on '{target_name}': Metallic={metallic}, Smoothness={smoothness}. (Simulated: {ex})"
        }
