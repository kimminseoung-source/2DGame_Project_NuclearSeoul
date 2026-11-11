"""Costumes for the shared base body: region colours, hair and simple props (Blender side).

A costume is a JSON file in assets/characters/costumes/ (format: CHARACTER_WORKFLOW.md).
Every character is the same rigged body and the same actions; only these change:

- body: "male" or "female" base mesh, plus head / bulk / legs proportions;
- regions: colours painted onto the body by which bone moves each vertex most
  (head, hands, forearms, top, bottom, shoes), so a shirt, trousers and boots need no
  extra meshes and bend with the body;
- hair: one of the free rigged hairstyles, recoloured;
- shells: clothes with volume. A copy of the body keeps only the chosen regions and is
  pushed out along its normals (a puffy jacket, baggy trousers, chunky boots); it is
  skinned to the same bones, so it moves with the body in every action;
- props: boxes, cylinders, spheres and cones fixed to a bone (hood, hard hat, backpack,
  bag, bat, pipe ...). They follow that bone in every action.

All colours are flat; the render's light bands and outline give the pixel-art shading.

ID mode (apply(..., ids=True)) paints every part in its own flat ID colour instead
(regions, hair, eyes, each shell and prop by name). A render of that tells, per pixel,
which part it is, so tools/sprites/repaint.py can repaint the frame with the concept
art's colours part by part (rotoscoping, CHARACTER_WORKFLOW.md section 6).
"""

import json
import math
import os

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

BASE_DIR = "assets/source3d/quaternius_base_characters"
BODIES = {
    "male": f"{BASE_DIR}/Base Characters/Godot - UE/Superhero_Male_FullBody.gltf",
    "female": f"{BASE_DIR}/Base Characters/Godot - UE/Superhero_Female_FullBody.gltf",
}
HAIR_DIR = f"{BASE_DIR}/Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)"
COLOR_ATTR = "costume"

DEFAULT_REGIONS = {
    "head": [0.80, 0.62, 0.50],
    "hands": [0.80, 0.62, 0.50],
    "forearms": [0.80, 0.62, 0.50],
    "top": [0.80, 0.62, 0.50],
    "bottom": [0.80, 0.62, 0.50],
    "shoes": [0.80, 0.62, 0.50],
}


ID_COLORS = [
    (230, 25, 75), (60, 180, 75), (255, 225, 25), (0, 130, 200), (245, 130, 48), (145, 30, 180),
    (70, 240, 240), (240, 50, 230), (210, 245, 60), (250, 190, 212), (0, 128, 128), (220, 190, 255),
    (170, 110, 40), (255, 250, 200), (128, 0, 0), (170, 255, 195), (128, 128, 0), (255, 215, 180),
]
_ids = None                                             # name -> 0..1 rgb while in ID mode


def part_color(name, rgb):
    """The colour to paint a part: its costume colour, or its ID colour in ID mode."""
    if _ids is None:
        return rgb
    if name not in _ids:
        r, g, b = ID_COLORS[len(_ids) % len(ID_COLORS)]
        _ids[name] = [r / 255, g / 255, b / 255]
    return _ids[name]


def id_map():
    """name -> 0..255 rgb of the ID colours used, for repaint.py."""
    return {k: [round(v * 255) for v in c] for k, c in (_ids or {}).items()}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def model_path(costume, root):
    """The costume's own "model" file (e.g. a Mixamo character), else a base body."""
    if costume.get("model"):
        return os.path.join(root, costume["model"])
    return os.path.join(root, BODIES[costume.get("body", "male")])


def is_body(obj):
    """The body mesh: the packs' "SuperHero_Male" / "Superhero_Female", or a Mixamo
    character's single skinned mesh (any mesh with an Armature modifier and vertex groups
    named mixamorig:...)."""
    if obj.type != "MESH":
        return False
    if obj.name.lower().startswith("superhero"):
        return True
    return any(g.name.startswith("mixamorig:") for g in obj.vertex_groups)


MIXAMO_REGIONS = {
    "Head": "head", "HeadTop_End": "head", "Neck": "head",
    "Hand": "hands", "ForeArm": "forearms", "Arm": "top", "Shoulder": "top",
    "Spine": "top", "Spine1": "top", "Spine2": "top",
    "Hips": "bottom", "UpLeg": "bottom", "Leg": "bottom",
    "Foot": "shoes", "ToeBase": "shoes", "Toe_End": "shoes",
}


def region_of(bone):
    """Which costume region a bone belongs to (Quaternius or Mixamo bone names)."""
    if bone.startswith("mixamorig:"):
        name = bone.split(":", 1)[1]
        for side in ("Left", "Right"):
            if name.startswith(side):
                name = name[len(side):]
        if name.startswith("Hand") or any(f in name for f in ("Thumb", "Index", "Middle", "Ring", "Pinky")):
            return "hands"
        return MIXAMO_REGIONS.get(name, "top")
    if bone in ("Head", "neck_01"):
        return "head"
    if bone.startswith(("hand_", "index_", "middle_", "pinky_", "ring_", "thumb_")):
        return "hands"
    if bone.startswith("lowerarm_"):
        return "forearms"
    if bone.startswith(("foot_", "ball_")):
        return "shoes"
    if bone.startswith(("thigh_", "calf_")) or bone == "pelvis":
        return "bottom"
    return "top"                                        # spine, clavicles, upper arms


def fill_color(mesh, rgb):
    attr = mesh.color_attributes.get(COLOR_ATTR) or mesh.color_attributes.new(COLOR_ATTR, "FLOAT_COLOR", "POINT")
    for item in attr.data:
        item.color = (*rgb, 1.0)
    mesh.color_attributes.active_color = attr


def paint_regions(obj, regions):
    """Colour each vertex by the bone that moves it most."""
    colors = {k: part_color(k, v) for k, v in {**DEFAULT_REGIONS, **regions}.items()}
    names = {g.index: g.name for g in obj.vertex_groups}
    mesh = obj.data
    attr = mesh.color_attributes.new(COLOR_ATTR, "FLOAT_COLOR", "POINT")
    for v in mesh.vertices:
        best = max(v.groups, key=lambda g: g.weight, default=None)
        bone = names.get(best.group, "spine_02") if best else "spine_02"
        attr.data[v.index].color = (*colors[region_of(bone)], 1.0)
    mesh.color_attributes.active_color = attr


def paint_body(armature, costume):
    regions = costume.get("regions", {})
    hair_rgb = costume.get("hair_color", [0.15, 0.12, 0.10])
    for obj in armature.children:
        if obj.type != "MESH":
            continue
        if obj.name.startswith("Eyes"):
            fill_color(obj.data, part_color("eyes", [0.08, 0.07, 0.07]))
        elif obj.name.startswith("Eyebrows"):
            fill_color(obj.data, part_color("hair", hair_rgb))
        elif is_body(obj):
            # Only the body: hair and clothes are children of the armature too and keep
            # their own colour (painting them by region turned the hair skin-coloured).
            paint_regions(obj, regions)


def add_hair(armature, costume, root):
    """Import a rigged hairstyle and skin it to this body's armature."""
    names = costume.get("hair") or []
    if isinstance(names, str):
        names = [names]                                 # e.g. "Hair_Buns" or ["Hair_Buzzed", "Hair_Beard"]
    for name in names:
        import_hair(armature, costume, os.path.join(root, HAIR_DIR, f"{name}.gltf"))


def import_hair(armature, costume, path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = set(bpy.data.objects) - before
    for obj in new:
        if obj.type == "MESH" and any(m.type == "ARMATURE" for m in obj.modifiers):
            matrix = obj.matrix_world.copy()
            obj.parent = armature
            obj.matrix_world = matrix
            for m in obj.modifiers:
                if m.type == "ARMATURE":
                    m.object = armature
            fill_color(obj.data, part_color("hair", costume.get("hair_color", [0.15, 0.12, 0.10])))
    for obj in new:
        if obj.type != "MESH" or obj.parent is not armature:
            bpy.data.objects.remove(obj, do_unlink=True)


def primitive(shape, size):
    """A unit primitive scaled to size (x, y, z) in metres, centred on its origin."""
    mesh = bpy.data.meshes.new(shape)
    bm = bmesh.new()
    if shape == "box":
        bmesh.ops.create_cube(bm, size=1.0)
    elif shape == "cylinder":
        bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.5, radius2=0.5, depth=1.0)
    elif shape == "taper":                              # thin at -z, full at +z (a bat: handle to barrel)
        bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.22, radius2=0.5, depth=1.0)
    elif shape == "rbox":                               # box with rounded edges (bags, backpacks)
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.18, segments=2, affect="EDGES")
    elif shape == "cone":
        bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.5, radius2=0.0, depth=1.0)
    elif shape == "sphere":
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.5)
    elif shape == "dome":                               # upper half of a sphere, flat side down
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.5)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-4], context="VERTS")
    else:
        raise SystemExit(f"unknown prop shape: {shape}")
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def add_props(armature, costume):
    """Fix each prop to its bone at rest pose; it then follows that bone in every action.

    offset / rotate are in the bone's own axes at rest: Y runs along the bone; for the head
    Y is up and Z points to the face; for the spine Z points to the chest.
    """
    bpy.context.view_layer.update()
    for i, prop in enumerate(costume.get("props", [])):
        bone = armature.data.bones[prop["bone"]]
        obj = bpy.data.objects.new(f"prop_{i}_{prop.get('name', prop['shape'])}",
                                   primitive(prop["shape"], prop.get("size", [0.1, 0.1, 0.1])))
        bpy.context.scene.collection.objects.link(obj)
        fill_color(obj.data, part_color(prop.get("name", prop["shape"]), prop.get("color", [0.5, 0.5, 0.5])))
        rot = Euler([math.radians(a) for a in prop.get("rotate", [0, 0, 0])]).to_matrix().to_4x4()
        rest = armature.matrix_world @ bone.matrix_local
        # Position and turn only: a Mixamo armature is scaled 0.01 (centimetres), which would
        # shrink every prop to nothing; sizes and offsets are always metres.
        loc, turn, _ = rest.decompose()
        rest = Matrix.Translation(loc) @ turn.to_matrix().to_4x4()
        target = rest @ Matrix.Translation(Vector(prop.get("offset", [0, 0, 0]))) @ rot
        obj.parent = armature
        obj.parent_type = "BONE"
        obj.parent_bone = bone.name
        bpy.context.view_layer.update()
        obj.matrix_world = target


def add_shells(armature, costume):
    """Clothes with volume: copies of the body, cut to some regions and pushed outwards."""
    body = next((o for o in armature.children if o.type == "MESH" and is_body(o)), None)
    if body is None:
        return
    for shell in costume.get("shells", []):
        obj = body.copy()
        obj.data = body.data.copy()
        obj.name = f"shell_{shell.get('name', 'cloth')}"
        bpy.context.scene.collection.objects.link(obj)
        names = {g.index: g.name for g in obj.vertex_groups}
        keep = set(shell["regions"])
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        deform = bm.verts.layers.deform.verify()
        drop = []
        for v in bm.verts:
            groups = v[deform]
            bone = names.get(max(groups.items(), key=lambda kv: kv[1])[0], "spine_02") if groups else "spine_02"
            if region_of(bone) not in keep:
                drop.append(v)
        bmesh.ops.delete(bm, geom=drop, context="VERTS")
        bm.to_mesh(obj.data)
        bm.free()
        # Push out before skinning, so the thickness follows the body in every pose.
        disp = obj.modifiers.new("inflate", "DISPLACE")
        disp.direction = "NORMAL"
        disp.mid_level = 0.0
        disp.strength = shell.get("inflate", 0.02)
        obj.modifiers.move(len(obj.modifiers) - 1, 0)
        for attr in list(obj.data.color_attributes):
            obj.data.color_attributes.remove(attr)
        fill_color(obj.data, part_color(shell.get("name", "cloth"), shell.get("color", [0.5, 0.5, 0.5])))


def apply(armature, costume, root, ids=False):
    """Hair, clothes, props and colours; call at rest pose, before actions and constraints."""
    global _ids
    _ids = {} if ids else None
    add_hair(armature, costume, root)
    paint_body(armature, costume)
    add_shells(armature, costume)
    add_props(armature, costume)
