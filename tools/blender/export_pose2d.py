"""Export 2D joint positions of an action, as seen by the sprite camera, for cut-out rigs.

    blender -b -P tools/blender/export_pose2d.py -- --anim-file <lib.glb>
        --map "swing=Sword_Regular_A,Sword_Regular_A_Rec@7-23" --frames-for swing=6,3 --out poses.json

Same body, turn, root pin, camera tilt and frame choice as render_sprites.py, but instead of
pictures it writes, per frame, where each joint lands on screen (metres, x right, y down,
origin at the pinned root). tools/sprites/cutout_rig.py takes only the joint ANGLES from
this and poses the concept art's own parts with them (the art keeps its proportions).
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = [sys.argv[0], "--"] + sys.argv[sys.argv.index("--") + 1:] + ["--out", "_unused"] \
    if "--out" not in sys.argv[sys.argv.index("--"):] else sys.argv
import render_sprites as rs  # noqa: E402  (its main() only runs when executed directly)

JOINTS = {
    "hip": ("pelvis", "head"), "neck": ("neck_01", "head"), "head_top": ("Head", "tail"),
    "shoulder_r": ("upperarm_r", "head"), "elbow_r": ("lowerarm_r", "head"), "wrist_r": ("hand_r", "head"),
    "hand_r": ("hand_r", "tail"),
    "shoulder_l": ("upperarm_l", "head"), "elbow_l": ("lowerarm_l", "head"), "wrist_l": ("hand_l", "head"),
    "hand_l": ("hand_l", "tail"),
    "hip_r": ("thigh_r", "head"), "knee_r": ("calf_r", "head"), "ankle_r": ("foot_r", "head"), "toe_r": ("ball_r", "head"),
    "hip_l": ("thigh_l", "head"), "knee_l": ("calf_l", "head"), "ankle_l": ("foot_l", "head"), "toe_l": ("ball_l", "head"),
}
BAT_DIR = Vector((0.0, 0.82, 0.57))          # bat axis in hand_r space (costume weapon rotate -55)


def main():
    import argparse
    argv = sys.argv[sys.argv.index("--") + 1:]
    p = argparse.ArgumentParser()
    p.add_argument("--anim-file", required=True)
    p.add_argument("--map", nargs="*", required=True)
    p.add_argument("--frames-for", nargs="*", default=[])
    p.add_argument("--tilt", type=float, default=20.0)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    rs.clear_scene()
    rs.import_model(os.path.join(rs.PROJECT_ROOT, rs.costumes.BODIES["male"]))
    rs.import_animations(os.path.abspath(a.anim_file))
    arm = rs.find_armature()
    for obj in bpy.data.objects:
        if obj.parent is None and obj.type in ("ARMATURE", "MESH", "EMPTY"):
            obj.rotation_mode = "XYZ"
            obj.rotation_euler[2] += math.radians(90)
    rs.pin_root(arm)
    scene = bpy.context.scene
    rs.setup_camera(scene, a.tilt)
    bpy.context.view_layer.update()                     # camera and turned body in place before reading
    cam = scene.camera
    to_cam = cam.matrix_world.inverted()
    counts = dict(pair.split("=") for pair in a.frames_for)
    result = {}
    for entry in a.map:
        sheet, parts = rs.parse_map_entry(entry)
        sheet_counts = [int(c) for c in str(counts.get(sheet, 8)).split(",")]
        frames = []
        for i, (name, frame_range, blend) in enumerate(parts):
            action = bpy.data.actions[name]
            over = (bpy.data.actions[blend[0]], blend[1]) if blend else None
            rs.assign_action(arm, action, over)
            for f in rs.frames_of(action, sheet_counts[min(i, len(sheet_counts) - 1)], frame_range):
                scene.frame_set(int(f), subframe=f - int(f))
                root = to_cam @ (arm.matrix_world @ arm.pose.bones["root"].head)
                pose = {}
                for joint, (bone, end) in JOINTS.items():
                    pb = arm.pose.bones[bone]
                    w = arm.matrix_world @ (pb.head if end == "head" else pb.tail)
                    c = to_cam @ w
                    pose[joint] = [round(c.x - root.x, 4), round(-(c.y - root.y), 4)]
                hand = arm.matrix_world @ arm.pose.bones["hand_r"].matrix
                d = (to_cam.to_3x3() @ (hand.to_3x3() @ BAT_DIR))
                pose["bat_dir"] = [round(d.x, 4), round(-d.y, 4)]
                frames.append(pose)
        result[sheet] = frames
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1)
    print("saved", a.out, {k: len(v) for k, v in result.items()})


main()
