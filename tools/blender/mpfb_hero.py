"""Build the hero as a proper 3D person with MPFB2 (MakeHuman for Blender), 2026-11-20.

    blender -b -P tools/blender/mpfb_hero.py -- --spec assets/characters/mpfb/hero.json
        --blend C:/Users/doboh/busan_ai/mpfb/busan_hero.blend --preview <dir>

The spec (JSON) is MPFB's own human format: body sliders ("phenotype": a young slim Asian
man), skin, eyes, eyebrows, hair and clothes from the MakeHuman asset packs (CC0), and the
"mixamo" skeleton so Mixamo actions play on it. Saves the .blend and, with --preview, renders
the figure large from the front, south-east and side (textures, soft light) to check the
character itself before anything is turned into pixels.
Needs the MPFB extension and the MakeHuman system assets installed in Blender (both free).
"""

import json
import math
import os
import sys

import addon_utils
import bpy
from mathutils import Vector


def args():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--spec", required=True)
    p.add_argument("--blend", required=True)
    p.add_argument("--preview", default=None)
    p.add_argument("--size", type=int, default=640)
    p.add_argument("--hair", default=None, help="try another hair (asset name) without editing the spec")
    return p.parse_args(sys.argv[sys.argv.index("--") + 1:])


def mpfb():
    mod = next(m for m in addon_utils.modules() if m.__name__.endswith(".mpfb") or m.__name__ == "mpfb")
    addon_utils.enable(mod.__name__)
    import importlib
    return importlib.import_module(mod.__name__ + ".services")


def preview(out, size, turns=(0, 45, 90)):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in [e.identifier for e in
                                                                 bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.film_transparent = True
    meshes = [o for o in scene.objects if o.type == "MESH" and o.visible_get()]
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    centre, height = (lo + hi) / 2, hi.z - lo.z
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = height * 1.12
    cam = bpy.data.objects.new("cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(50), 0, math.radians(-35))
    scene.collection.objects.link(sun)
    world = scene.world or bpy.data.worlds.new("w")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    rig = next((o for o in scene.objects if o.type == "ARMATURE"), None)
    root = rig if rig else meshes[0]
    for t in turns:
        root.rotation_euler[2] = math.radians(t)
        bpy.context.view_layer.update()
        d = 10.0
        tilt = math.radians(10)
        cam.location = centre + Vector((0, -d * math.cos(tilt), d * math.sin(tilt)))
        cam.rotation_euler = (math.radians(90) - tilt, 0, 0)
        scene.render.filepath = os.path.join(out, f"turn{t}.png")
        bpy.ops.render.render(write_still=True)
        print("saved", scene.render.filepath)
    root.rotation_euler[2] = 0


def main():
    a = args()
    services = mpfb()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mpfb()
    spec = json.loads(open(a.spec, encoding="utf-8").read())
    if a.hair:
        spec["hair"] = f"{a.hair}/{a.hair}.mhclo"
    settings = services.HumanService.get_default_deserialization_settings()
    settings["subdiv_levels"] = 0
    basemesh = services.HumanService.deserialize_from_dict(spec, settings)
    print("built", basemesh.name, [o.name for o in bpy.context.scene.objects])
    # A bigger head for sprites (36 px: a real head is 5 px and the face disappears). Kept as a
    # pose scale on the head bone (hair, eyes and eyebrows follow it); mpfb_pose.py reapplies it.
    rig = next((o for o in bpy.context.scene.objects if o.type == "ARMATURE"), None)
    if rig and spec.get("head_scale", 1.0) != 1.0:
        rig["head_scale"] = spec["head_scale"]
        rig.pose.bones["mixamorig:Head"].scale = (spec["head_scale"],) * 3
    os.makedirs(os.path.dirname(a.blend), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=a.blend)
    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        preview(a.preview, a.size)


if __name__ == "__main__":
    main()
