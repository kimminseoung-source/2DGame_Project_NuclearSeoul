"""Render a rigged 3D character into side-view pixel sprite sheets (Dead Cells style).

Run with Blender in the background, for example:

    blender -b -P tools/blender/render_sprites.py -- --model path/to/character.glb
        --out assets/characters/render --actions Walk Idle --frames 8

What it does (see assets/characters/CHARACTER_SPEC.md for the cell rules):
- imports the model (.glb/.gltf/.fbx) and turns it to face screen-right;
- places an orthographic camera at the side so one cell is 96 x 64 px, the feet sit
  on y = 60 from the top and a 1.8 m person is about 54 px tall;
- renders each action at N evenly spaced frames with flat studio lighting, no
  anti-aliasing and a dark outline, on a transparent background;
- reduces the colours to a few steps per channel and glues the frames into one
  horizontal sheet per action: <out>/<action>.png.
"""

import argparse
import math
import os
import sys

import bpy

CELL_W, CELL_H = 96, 64
FEET_FROM_BOTTOM = 4            # px: the feet line is y = 60 from the top
PERSON_HEIGHT_M = 1.8
PERSON_HEIGHT_PX = 54
LEVELS = 6                      # colour steps per channel after rendering


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--actions", nargs="*", default=None, help="action names; default: all")
    parser.add_argument("--frames", type=int, default=8)
    parser.add_argument("--list", action="store_true", help="only print the actions in the model")
    parser.add_argument("--turn", type=float, default=90.0, help="degrees to turn the model to face right")
    return parser.parse_args(argv)


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_model(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=path)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=path)
    else:
        raise SystemExit(f"unsupported model type: {ext}")


def find_armature():
    for obj in bpy.data.objects:
        if obj.type == "ARMATURE":
            return obj
    return None


def setup_camera(scene):
    metres_per_px = PERSON_HEIGHT_M / PERSON_HEIGHT_PX
    cam_data = bpy.data.cameras.new("SpriteCam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = CELL_W * metres_per_px          # ortho scale spans the wider side
    cam = bpy.data.objects.new("SpriteCam", cam_data)
    scene.collection.objects.link(cam)
    # Look along +Y from the front side of the screen; X is screen-right, Z is up.
    centre_z = CELL_H * metres_per_px / 2 - FEET_FROM_BOTTOM * metres_per_px
    cam.location = (0.0, -10.0, centre_z)
    cam.rotation_euler = (math.radians(90), 0.0, 0.0)
    scene.camera = cam


def setup_render(scene):
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = CELL_W
    scene.render.resolution_y = CELL_H
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.display.render_aa = "OFF"                     # hard pixel edges
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.color_type = "MATERIAL"
    shading.show_object_outline = True
    shading.object_outline_color = (0.06, 0.07, 0.10)
    shading.show_cavity = True
    shading.cavity_type = "BOTH"
    scene.view_settings.view_transform = "Standard"


def frames_of(action, count):
    start, end = action.frame_range
    if count <= 1:
        return [int(start)]
    step = (end - start) / count                         # loop: the last frame equals the first
    return [round(start + i * step) for i in range(count)]


def posterize(pixels):
    out = list(pixels)
    for i in range(0, len(out), 4):
        alpha = out[i + 3]
        if alpha < 0.5:
            out[i:i + 4] = [0.0, 0.0, 0.0, 0.0]
            continue
        for c in range(3):
            out[i + c] = round(out[i + c] * (LEVELS - 1)) / (LEVELS - 1)
        out[i + 3] = 1.0
    return out


def render_action(scene, armature, action, count, out_dir, tmp_dir):
    armature.animation_data_create()
    armature.animation_data.action = action
    frames = frames_of(action, count)
    sheet = bpy.data.images.new(f"sheet_{action.name}", CELL_W * len(frames), CELL_H, alpha=True)
    sheet_px = [0.0] * (CELL_W * len(frames) * CELL_H * 4)
    for index, frame in enumerate(frames):
        scene.frame_set(frame)
        path = os.path.join(tmp_dir, f"{action.name}_{index}.png")
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        image = bpy.data.images.load(path)
        px = posterize(image.pixels[:])
        for y in range(CELL_H):
            src = y * CELL_W * 4
            dst = (y * CELL_W * len(frames) + index * CELL_W) * 4
            sheet_px[dst:dst + CELL_W * 4] = px[src:src + CELL_W * 4]
        bpy.data.images.remove(image)
    sheet.pixels[:] = sheet_px
    sheet.filepath_raw = os.path.join(out_dir, f"{safe_name(action.name)}.png")
    sheet.file_format = "PNG"
    sheet.save()
    print(f"saved {sheet.filepath_raw} ({len(frames)} frames: {frames})")


def safe_name(name):
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name).lower()


def main():
    args = parse_args()
    clear_scene()
    import_model(os.path.abspath(args.model))
    if args.list:
        for action in bpy.data.actions:
            print(f"ACTION {action.name} {tuple(action.frame_range)}")
        return
    scene = bpy.context.scene
    armature = find_armature()
    for obj in bpy.data.objects:
        if obj.parent is None and obj.type in ("ARMATURE", "MESH", "EMPTY"):
            obj.rotation_euler[2] += math.radians(args.turn)
    setup_camera(scene)
    setup_render(scene)
    out_dir = os.path.abspath(args.out)
    tmp_dir = os.path.join(out_dir, "_frames")
    os.makedirs(tmp_dir, exist_ok=True)
    actions = [a for a in bpy.data.actions if not args.actions or a.name in args.actions]
    if armature is None or not actions:
        # No animation: render the rest pose once so the size and look can be checked.
        scene.render.filepath = os.path.join(out_dir, "rest.png")
        bpy.ops.render.render(write_still=True)
        print("saved rest pose only (no armature or actions)")
        return
    for action in actions:
        render_action(scene, armature, action, args.frames, out_dir, tmp_dir)


main()
