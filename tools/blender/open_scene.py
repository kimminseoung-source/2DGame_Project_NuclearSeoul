"""Build a Blender scene of a costume on the base body and save it as a .blend to look at.

    blender -b -P tools/blender/open_scene.py -- --costume assets/characters/costumes/hero_b.json
        --anim-file <lib.glb> --action Walk_Loop --out assets/source3d/scenes/hero_b.blend
    blender assets/source3d/scenes/hero_b.blend

Same body, costume, turn, root pin and sprite camera as render_sprites.py, with the action
playing on the timeline and the viewport showing the costume colours. The .blend lives in
assets/source3d/ (not committed: large, rebuilt from this script).
"""

import argparse
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_sprites as rs  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
p = argparse.ArgumentParser()
p.add_argument("--costume", required=True)
p.add_argument("--anim-file", required=True)
p.add_argument("--action", default="Walk_Loop")
p.add_argument("--out", required=True)
p.add_argument("--tilt", type=float, default=20.0)
a = p.parse_args(argv)

outfit = rs.costumes.load(a.costume)
rs.clear_scene()
rs.import_model(rs.costumes.model_path(outfit, rs.PROJECT_ROOT))
rs.import_animations(os.path.abspath(a.anim_file))
arm = rs.find_armature()
rs.remove_loose_meshes(arm)
for obj in bpy.data.objects:
    if obj.parent is None and obj.type in ("ARMATURE", "MESH", "EMPTY"):
        obj.rotation_mode = "XYZ"
        obj.rotation_euler[2] += math.radians(90)
rs.costumes.apply(arm, outfit, rs.PROJECT_ROOT)
rs.pin_root(arm)
rs.shape_body(arm, outfit.get("head", 1.0), outfit.get("bulk", 1.0), outfit.get("legs", 1.0))
scene = bpy.context.scene
rs.setup_camera(scene, a.tilt)
rs.setup_render(scene, None, painted=True)
action = bpy.data.actions[a.action]
rs.assign_action(arm, action)
scene.frame_start, scene.frame_end = int(action.frame_range[0]), int(action.frame_range[1])
scene.render.resolution_x, scene.render.resolution_y = 96 * 6, 64 * 6   # bigger preview in the camera view
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.out))
print("saved", a.out)
