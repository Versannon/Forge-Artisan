import bpy, os, json, math

spec = json.loads('{"root_name": "AncientDwarvenWarhammer", "asset_title": "Ancient Dwarven Warhammer", "category": "prop", "summary": "Two-handed dwarven warhammer with steel head, rear war-pick and crown spike on a leather-wrapped haft, built from beveled quad-ready primitives at meter scale for Subdivision and FBX export.", "expected_features": ["glowing cyan rune inlay on hammer head", "beveled steel hammer block with cylindrical striking face", "rear war-pick spike and top crown spike", "leather-wrapped haft with brass coils and pommel stone"], "accent_name": "Head_Rune_Inlay_Cyan", "accent_emission": [0.0, 1.0, 1.0], "parts": [{"name": "Handle_Shaft_Core", "primitive_type": "cylinder", "position": [0.0, -0.2, 0.0], "rotation": [0.0, 0.0, 0.0], "scale": [0.05, 1.1, 0.05], "color": [0.25, 0.15, 0.08], "metallic": 0.1, "smoothness": 0.4, "bevel_radius": 0.01}, {"name": "Leather_Grip_Sleeve", "primitive_type": "cylinder", "position": [0.0, -0.35, 0.0], "rotation": [0.0, 0.0, 0.0], "scale": [0.062, 0.55, 0.062], "color": [0.18, 0.11, 0.07], "metallic": 0.0, "smoothness": 0.35, "bevel_radius": 0.01}, {"name": "Grip_Coil_Ring_Lower", "primitive_type": "torus", "position": [0.0, -0.55, 0.0], "rotation": [90.0, 0.0, 0.0], "scale": [0.07, 0.07, 0.05], "color": [0.45, 0.32, 0.12], "metallic": 0.9, "smoothness": 0.6, "bevel_radius": 0.01}, {"name": "Grip_Coil_Ring_Upper", "primitive_type": "torus", "position": [0.0, -0.12, 0.0], "rotation": [90.0, 0.0, 0.0], "scale": [0.07, 0.07, 0.05], "color": [0.45, 0.32, 0.12], "metallic": 0.9, "smoothness": 0.6, "bevel_radius": 0.01}, {"name": "Pommel_Cap_Disc", "primitive_type": "cylinder", "position": [0.0, -0.78, 0.0], "rotation": [0.0, 0.0, 0.0], "scale": [0.08, 0.06, 0.08], "color": [0.55, 0.4, 0.15], "metallic": 0.95, "smoothness": 0.7, "bevel_radius": 0.015}, {"name": "Pommel_Rune_Stone", "primitive_type": "sphere", "position": [0.0, -0.84, 0.0], "rotation": [0.0, 0.0, 0.0], "scale": [0.05, 0.05, 0.05], "color": [0.05, 0.3, 0.35], "metallic": 0.1, "smoothness": 0.9, "bevel_radius": 0.01, "emission_color": [0.0, 0.9, 1.0]}, {"name": "Shaft_Top_Collar", "primitive_type": "cylinder", "position": [0.0, 0.28, 0.0], "rotation": [0.0, 0.0, 0.0], "scale": [0.075, 0.12, 0.075], "color": [0.22, 0.23, 0.26], "metallic": 0.9, "smoothness": 0.6, "bevel_radius": 0.012}, {"name": "Hammer_Head_Block", "primitive_type": "beveled_box", "position": [0.0, 0.5, 0.0], "rotation": [0.0, 0.0, 0.0], "scale": [0.52, 0.22, 0.22], "color": [0.28, 0.29, 0.32], "metallic": 0.9, "smoothness": 0.55, "bevel_radius": 0.03}, {"name": "Strike_Face_Drum", "primitive_type": "cylinder", "position": [0.32, 0.5, 0.0], "rotation": [0.0, 0.0, 90.0], "scale": [0.14, 0.1, 0.14], "color": [0.35, 0.36, 0.38], "metallic": 0.95, "smoothness": 0.7, "bevel_radius": 0.015}, {"name": "Strike_Face_Rim", "primitive_type": "torus", "position": [0.37, 0.5, 0.0], "rotation": [0.0, 90.0, 0.0], "scale": [0.14, 0.14, 0.05], "color": [0.5, 0.35, 0.15], "metallic": 1.0, "smoothness": 0.65, "bevel_radius": 0.01}, {"name": "Rear_Spike_Base", "primitive_type": "beveled_box", "position": [-0.32, 0.5, 0.0], "rotation": [0.0, 0.0, 0.0], "scale": [0.12, 0.16, 0.16], "color": [0.25, 0.26, 0.29], "metallic": 0.9, "smoothness": 0.55, "bevel_radius": 0.02}, {"name": "Rear_War_Pick_Spike", "primitive_type": "wedge", "position": [-0.45, 0.5, 0.0], "rotation": [0.0, 0.0, 90.0], "scale": [0.2, 0.12, 0.08], "color": [0.33, 0.34, 0.37], "metallic": 0.95, "smoothness": 0.6, "bevel_radius": 0.01}, {"name": "Crown_Top_Spike", "primitive_type": "wedge", "position": [0.0, 0.69, 0.0], "rotation": [0.0, 0.0, 0.0], "scale": [0.08, 0.14, 0.08], "color": [0.4, 0.31, 0.13], "metallic": 0.95, "smoothness": 0.65, "bevel_radius": 0.01}, {"name": "Side_Rune_Plate_Trim", "primitive_type": "beveled_box", "position": [0.0, 0.5, 0.115], "rotation": [0.0, 0.0, 0.0], "scale": [0.34, 0.14, 0.05], "color": [0.45, 0.32, 0.12], "metallic": 0.95, "smoothness": 0.6, "bevel_radius": 0.01}, {"name": "Head_Rune_Inlay_Cyan", "primitive_type": "beveled_box", "position": [0.0, 0.5, 0.125], "rotation": [0.0, 0.0, 0.0], "scale": [0.28, 0.08, 0.05], "color": [0.0, 0.8, 0.9], "metallic": 0.0, "smoothness": 0.9, "bevel_radius": 0.01, "emission_color": [0.0, 1.0, 1.0]}]}')
root_name = spec.get("root_name", "CompoundAsset")
parts = spec.get("parts", [])
accent_name = spec.get("accent_name", "")

# 1. Clean or create ForgeArtisan collection
col_name = f"ForgeArtisan_{root_name}"
if col_name in bpy.data.collections:
    col = bpy.data.collections[col_name]
    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
else:
    col = bpy.data.collections.new(col_name)
    bpy.context.scene.collection.children.link(col)

created_objects = []

for idx, p in enumerate(parts):
    name = p.get("name", f"Part_{idx}")
    ptype = str(p.get("primitive_type", "beveled_box")).lower()
    pos = p.get("position", [0, 0, 0])
    rot = p.get("rotation", [0, 0, 0])
    scale = p.get("scale", [1, 1, 1])
    color = p.get("color", [0.5, 0.5, 0.5])
    metallic = p.get("metallic", 0.5)
    smoothness = p.get("smoothness", 0.5)
    bevel_radius = p.get("bevel_radius", 0.05)
    emission = p.get("emission_color") or ([0, 0, 0] if name != accent_name else spec.get("accent_emission", [1, 0.5, 0]))

    # Convert Unity/Standard Y-up to Blender Z-up
    # x -> x, y -> z, z -> -y
    b_loc = (pos[0], -pos[2], pos[1])
    b_rot = (math.radians(rot[0]), math.radians(rot[2]), math.radians(rot[1]))
    b_scl = (scale[0] / 2.0, scale[2] / 2.0, scale[1] / 2.0)

    if ptype in ["sphere"]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=b_loc)
    elif ptype in ["cylinder"]:
        bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0, location=b_loc)
    elif ptype in ["torus"]:
        bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.2, location=b_loc)
    else: # beveled_box / cube
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=b_loc)

    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_euler = b_rot
    obj.scale = b_scl

    # Move to ForgeArtisan collection
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)

    # Add Bevel modifier for high-poly chamfers
    if ptype == "beveled_box":
        bev = obj.modifiers.new(name="Bevel", type='BEVEL')
        bev.width = max(0.01, min(bevel_radius, 0.1))
        bev.segments = 3

    # Setup PBR Material with Principled BSDF
    mat = bpy.data.materials.new(name=f"{name}_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = metallic
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = max(0.05, 1.0 - smoothness)
        # Calibrated Emission (soft, rich glow)
        if sum(emission) > 0.05:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = (emission[0], emission[1], emission[2], 1.0)
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = 1.5
    obj.data.materials.append(mat)
    created_objects.append(obj.name)

# Export FBX
export_dir = os.path.dirname('C:/Soham/Repositories/Hackathon-meta/forge-artisan/workspace/AncientDwarvenWarhammer.fbx')
os.makedirs(export_dir, exist_ok=True)
try:
    bpy.ops.export_scene.fbx(filepath='C:/Soham/Repositories/Hackathon-meta/forge-artisan/workspace/AncientDwarvenWarhammer.fbx', check_existing=False)
    print(f"SUCCESS: Exported {len(created_objects)} parts to FBX: {repr('C:/Soham/Repositories/Hackathon-meta/forge-artisan/workspace/AncientDwarvenWarhammer.fbx')}")
except Exception as e:
    print(f"FBX Export Warning: {e}")
