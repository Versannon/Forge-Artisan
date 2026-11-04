"""Engine Intent Router & Contextual Pipeline Dispatcher.

Analyzes user prompts for engine-specific textual context:
- Blender: "in blender", ".fbx", "subdivision", "high definition 3dmodel", "cycles", "eevee", "geometry nodes", "bpy"
- Blockbench: "in blockbench", ".bbmodel", "voxel", "minecraft", "cuboid", "pixel art"
- Unreal Engine: "in unreal", "ue5", "nanite", "lumen", "chaos", "blueprint", ".uasset"
- Unity: "in unity", "unity 6", "prefab", "gameobject", "urp", "hdrp"

Intelligently routes instructions to Meta Model API (muse-spark-1.3) and dispatches
execution to the corresponding engine runtime (Blender MCP, Unity Bridge, or Blockbench).
"""

from __future__ import annotations

import re
from typing import Any
from agent_kit.tools import engine_detector


ENGINE_KEYWORDS = {
    "blender": [
        "blender", "blender 3d", ".fbx", "fbx", "fbx file", ".blend", "blend file",
        "subdivision", "sub-d", "subd", "high poly", "high-poly", "high definition 3d",
        "high definition 3dmodel", "high definition model", "principled bsdf",
        "geometry nodes", "cycles", "eevee", "bpy", "sculpt", "render in blender"
    ],
    "blockbench": [
        "blockbench", "block bench", ".bbmodel", "bbmodel", "voxel", "voxels",
        "minecraft", "cuboid", "pixel art", "pixel texture", "bedrock model",
        "low poly block", "blocky"
    ],
    "unreal": [
        "unreal", "unreal engine", "unreal 5", "ue5", "ue4", "nanite", "lumen",
        "chaos physics", "blueprint", ".uasset", "uasset", "niagara", "quixel"
    ],
    "unity": [
        "unity", "unity 6", "unity engine", "prefab", ".prefab", "gameobject",
        "c# script", "urp", "hdrp", "unity bridge"
    ]
}


def resolve_target_engine(prompt: str) -> dict[str, Any]:
    """Analyzes prompt text to intelligently resolve target creation engine.
    If explicitly cued in the text (e.g. 'in blender' or '.fbx file'), routes to that engine.
    Otherwise, defaults to the currently running engine (or Unity if connected).
    """
    p_lower = prompt.lower()
    
    # Check for explicit engine cues
    detected_scores: dict[str, list[str]] = {}
    for eng, keywords in ENGINE_KEYWORDS.items():
        matched = []
        for kw in keywords:
            # Word boundary check for short words like fbx, ue5, etc.
            pattern = r'\b' + re.escape(kw) + r'\b' if len(kw) <= 5 else re.escape(kw)
            if re.search(pattern, p_lower):
                matched.append(kw)
        if matched:
            detected_scores[eng] = matched

    if detected_scores:
        # Pick the engine with highest matched keyword count
        best_engine = max(detected_scores.items(), key=lambda item: len(item[1]))[0]
        cues = detected_scores[best_engine]
        
        display_names = {
            "blender": "Blender 3D",
            "blockbench": "Blockbench",
            "unreal": "Unreal Engine 5",
            "unity": "Unity 6"
        }
        
        return {
            "engine": best_engine,
            "engine_name": display_names.get(best_engine, best_engine.capitalize()),
            "detected_from": "prompt_context",
            "matched_cues": cues,
            "reason": f"Detected from directive context: {', '.join(repr(c) for c in cues[:3])}",
            "is_override": True
        }

    # Fallback to currently running engine
    status = engine_detector.get_current_engine_status()
    active_eng = status.get("active_engine")
    if active_eng:
        eng_type = active_eng.get("type", "unity")
        return {
            "engine": eng_type,
            "engine_name": active_eng.get("name", "Active Game Engine"),
            "detected_from": "running_process",
            "matched_cues": [],
            "reason": f"Auto-detected running engine: {active_eng.get('display_name')}",
            "is_override": False
        }

    return {
        "engine": "unity",
        "engine_name": "Unity 6",
        "detected_from": "default",
        "matched_cues": [],
        "reason": "Default game engine runtime (Unity 6 test project)",
        "is_override": False
    }


def get_engine_system_instructions(engine: str) -> str:
    """Returns specialized technical guidelines for Meta Model API (muse-spark-1.3)
    tailored to the target engine's geometry and shading conventions."""
    if engine == "blender":
        return """TARGET ENGINE: BLENDER 3D & .FBX PIPELINE.
Architect the 3D compound geometry for high-definition 3D modeling and FBX export in Blender:
- Structure parts with clear logical naming for Blender Outliner Collections.
- PBR Shading corresponds to Blender's Principled BSDF node (Base Color, Metallic, Roughness, Emission Strength, Transmission).
- Metric scale: 1.0 unit = 1.0 meter.
- Quad-friendly primitive decomposition: beveled_box (Subdivision Surface / Bevel Modifier ready), cylinder, sphere, wedge, torus.
- Focal accent component should have emission_color and accent_name specified."""

    elif engine == "blockbench":
        return """TARGET ENGINE: BLOCKBENCH (Voxel & Low-Poly Studio).
Architect the 3D compound geometry using low-poly voxel cuboid elements snapped to a clean structural grid:
- Primitive types must strictly be 'beveled_box' (representing voxel cuboids).
- Integer or 0.5-increment metric dimensions and positions for authentic blocky aesthetics.
- Clean Minecraft / Low-Poly hierarchy with bone grouping structure.
- Distinct color palette per component."""

    elif engine == "unreal":
        return """TARGET ENGINE: UNREAL ENGINE 5 (Nanite & Lumen).
Architect the 3D compound geometry for Unreal Engine 5:
- Coordinates should reflect Unreal conventions: Z-up, centimeters (multiply positions and scales by 100).
- Modular component breakdown ready for Nanite geometric clustering.
- PBR material parameters compatible with Unreal Standard Material (BaseColor, Metallic, Specular, Roughness, EmissiveColor)."""

    else: # Unity
        return """TARGET ENGINE: UNITY 6 (Universal Render Pipeline).
Architect the 3D compound geometry for Unity 6 URP:
- Metric scale: 1.0 unit = 1.0 meter (Y-up coordinates).
- Primitives: beveled_box (0.05m-0.08m bevel chamfers), cylinder, sphere, wedge, torus.
- Soft, calibrated emission values without bloom blow-out (RGB 0.0 - 0.7 max).
- Progressive assembly hierarchy centered around root [0, y, 0]."""
