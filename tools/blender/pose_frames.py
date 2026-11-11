"""Render single pose guide images (one pose per PNG) from any rigged model and actions.

    blender -b -P tools/blender/pose_frames.py -- --costume assets/characters/costumes/hero_alex.json
        --anim-file a.fbx b.fbx --pose walk_1=Walking@1 walk_2=Walking@10 --out assets/characters/guides/hero
        [--scale 6] [--strip contact.png]

Each guide is a grey figure on flat magenta, side view facing right, with the front (right)
arm and leg lighter than the back ones and the costume's props (bat, backpack) in their own
colours, so an image model can redraw the concept character in exactly that pose
("edit this image to match the pose", CHARACTER_WORKFLOW.md section 6). With --strip the
poses are also laid side by side in one small contact image, to choose key frames.
"""

import argparse
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_sprites as rs  # noqa: E402

MAGENTA = (1.0, 0.0, 1.0)


def side_of(bone):
    name = bone.split(":", 1)[-1]
    if name.endswith("_r") or name.startswith("Right"):
        return "front"
    if name.endswith("_l") or name.startswith("Left"):
        return "back"
    return "mid"


def paint_grey(arm):
    shades = {"front": (0.85, 0.85, 0.85), "back": (0.35, 0.35, 0.38), "mid": (0.6, 0.6, 0.62)}
    for body in [o for o in arm.children if rs.costumes.is_body(o)]:
        names = {g.index: g.name for g in body.vertex_groups}
        for attr in list(body.data.color_attributes):
            body.data.color_attributes.remove(attr)
        attr = body.data.color_attributes.new("guide", "FLOAT_COLOR", "POINT")
        for v in body.data.vertices:
            best = max(v.groups, key=lambda g: g.weight, default=None)
            attr.data[v.index].color = (*shades[side_of(names.get(best.group, "") if best else "")], 1.0)
        body.data.color_attributes.active_color = attr
    for o in arm.children:
        if o.type == "MESH" and not rs.costumes.is_body(o) and not o.name.startswith("prop_"):
            o.hide_render = True                        # eyes, brows, hair: noise in a guide


def render_rgba(scene, path):
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(path)
    w, h = img.size
    px = list(img.pixels[:])
    bpy.data.images.remove(img)
    for i in range(0, len(px), 4):                      # composite on magenta
        a = px[i + 3]
        for c in range(3):
            px[i + c] = px[i + c] * a + MAGENTA[c] * (1 - a)
        px[i + 3] = 1.0
    return w, h, px


def save(name, w, h, px):
    img = bpy.data.images.new(os.path.basename(name), w, h, alpha=True)
    img.pixels[:] = px
    img.filepath_raw = name
    img.file_format = "PNG"
    img.save()


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    p = argparse.ArgumentParser()
    p.add_argument("--costume", required=True)
    p.add_argument("--anim-file", nargs="+", required=True)
    p.add_argument("--pose", nargs="+", required=True, help="name=Action@frame")
    p.add_argument("--scale", type=int, default=6)
    p.add_argument("--tilt", type=float, default=20.0)
    p.add_argument("--out", required=True)
    p.add_argument("--strip", default=None)
    a = p.parse_args(argv)
    outfit = rs.costumes.load(a.costume)
    rs.clear_scene()
    rs.import_model(rs.costumes.model_path(outfit, rs.PROJECT_ROOT))
    for f in a.anim_file:
        rs.import_animations(os.path.abspath(f))
    arm = rs.find_armature()
    rs.remove_loose_meshes(arm)
    for obj in bpy.data.objects:
        if obj.parent is None and obj.type in ("ARMATURE", "MESH", "EMPTY"):
            obj.rotation_mode = "XYZ"
            obj.rotation_euler[2] += math.radians(90)
    rs.costumes.add_props(arm, outfit)
    paint_grey(arm)
    rs.pin_root(arm)
    scene = bpy.context.scene
    rs.setup_camera(scene, a.tilt)
    rs.setup_render(scene, None, painted=True)
    scene.render.resolution_x, scene.render.resolution_y = rs.CELL_W * a.scale, rs.CELL_H * a.scale
    scene.display.render_aa = "8"
    scene.render.film_transparent = True
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    strip = []
    for entry in a.pose:
        name, spec = entry.split("=", 1)
        action_name, frame = spec.split("@")
        rs.assign_action(arm, bpy.data.actions[action_name])
        f = float(frame)
        scene.frame_set(int(f), subframe=f - int(f))
        w, h, px = render_rgba(scene, os.path.join(out, "_frames", f"{name}.png"))
        save(os.path.join(out, f"{name}.png"), w, h, px)
        strip.append((w, h, px))
        print("saved", os.path.join(out, f"{name}.png"))
    if a.strip and strip:
        w, h = strip[0][0], strip[0][1]
        big = [0.0] * (w * len(strip) * h * 4)
        for i, (_, _, px) in enumerate(strip):
            for y in range(h):
                s = y * w * 4
                d = (y * w * len(strip) + i * w) * 4
                big[d:d + w * 4] = px[s:s + w * 4]
        save(os.path.abspath(a.strip), w * len(strip), h, big)
        print("saved", a.strip)


if __name__ == "__main__":
    main()
