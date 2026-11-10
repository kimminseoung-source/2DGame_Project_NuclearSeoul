"""Render a rigged 3D character into side-view pixel sprite sheets (Dead Cells style).

Run with Blender in the background (full command examples are kept in
assets/characters/CHARACTER_WORKFLOW.md):

    blender -b -P tools/blender/render_sprites.py -- --model <body.gltf>
        --anim-file <animations.glb> --out assets/characters/base
        --map walk=Walk_Loop pickup=Fixing_Kneeling@0-30 --frames-for walk=8 pickup=4
        --head 1.45 --bulk 1.25 --flat 0.80,0.62,0.50 --bands 3 --outline

What it does (cell rules: assets/characters/CHARACTER_SPEC.md):
- imports the body, borrows actions from another file with the same bone names, and
  turns the model to face screen-right;
- optional body proportions: a bigger head (--head) and a thicker build (--bulk), held
  by bone constraints so the animation cannot undo them;
- an orthographic side camera: one cell is 96 x 64 px, the feet stand on y = 60 from the
  top, 1.8 m is 54 px;
- flat studio lighting, no anti-aliasing, transparent background; optionally one flat
  colour for the whole body (--flat);
- after rendering: light is cut into a few bands (--bands, cel shading) and a 1 px dark
  outline is drawn around the figure (--outline);
- the frames of each action are glued into one horizontal sheet: <out>/<sheet>.png.
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
OUTLINE_RGB = (0.06, 0.07, 0.10)
LIGHT_TURN_DEG = 70             # studio light rotation around the vertical axis


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--anim-file", default=None,
                        help="file whose actions are borrowed (same bone names), e.g. the animation library")
    parser.add_argument("--map", nargs="*", default=None,
                        help="sheet=action pairs, optionally with a frame range: pickup=Fixing_Kneeling@0-30")
    parser.add_argument("--frames", type=int, default=8)
    parser.add_argument("--frames-for", nargs="*", default=None,
                        help="sheet=count pairs overriding --frames, e.g. walk=8 hurt=3")
    parser.add_argument("--list", action="store_true", help="only print the actions and stop")
    parser.add_argument("--turn", type=float, default=90.0, help="degrees to turn the model to face right")
    parser.add_argument("--tilt", type=float, default=0.0,
                        help="degrees the camera looks down from above (0 = eye level)")
    parser.add_argument("--head", type=float, default=1.0, help="head size multiplier")
    parser.add_argument("--bulk", type=float, default=1.0, help="thickness multiplier for torso, arms and legs")
    parser.add_argument("--legs", type=float, default=1.0,
                        help="leg length multiplier; the body is lowered so the feet stay on the floor line")
    parser.add_argument("--shift-for", nargs="*", default=None,
                        help="sheet=px pairs moving that sheet's figure right, e.g. down=14 so a fall stays in the cell")
    parser.add_argument("--flat", default=None, help="one body colour as r,g,b in 0..1 (base mannequin)")
    parser.add_argument("--bands", type=int, default=0, help="light bands for cel shading (0 = off)")
    parser.add_argument("--outline", action="store_true", help="draw a 1 px dark outline around the figure")
    return parser.parse_args(argv)


# Scene ---------------------------------------------------------------------------

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


def import_animations(path):
    """Import a file only for its actions; its own objects are removed again."""
    before = set(bpy.data.objects)
    import_model(path)
    for action in bpy.data.actions:
        action.use_fake_user = True
    for obj in set(bpy.data.objects) - before:
        bpy.data.objects.remove(obj, do_unlink=True)


def find_armature():
    return next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)


def remove_loose_meshes(armature):
    """Drop helper meshes that are neither parented nor skinned (e.g. a preview sphere)."""
    for obj in list(bpy.data.objects):
        skinned = any(m.type == "ARMATURE" for m in getattr(obj, "modifiers", []))
        if obj.type == "MESH" and obj.parent is None and not skinned and armature is not None:
            bpy.data.objects.remove(obj, do_unlink=True)


def hold_scale(armature, bone, x, y, z):
    """Fix a bone's local scale after the animation is applied (Limit Scale with min = max)."""
    pose_bone = armature.pose.bones.get(bone)
    if pose_bone is None:
        return
    c = pose_bone.constraints.new("LIMIT_SCALE")
    c.use_min_x = c.use_max_x = c.use_min_y = c.use_max_y = c.use_min_z = c.use_max_z = True
    c.min_x = c.max_x = x
    c.min_y = c.max_y = y
    c.min_z = c.max_z = z
    c.owner_space = "LOCAL"


def shape_body(armature, head, bulk, legs=1.0):
    """Bone-local Y runs along the bone, so X/Z thicken it and Y lengthens or shortens it."""
    if armature is None:
        return
    if bulk != 1.0 or legs != 1.0:
        # Children inherit scale, so set it where it does not double up: the calf and foot
        # follow the thigh, the forearm follows the upper arm.
        for bone in ("thigh_l", "thigh_r"):
            hold_scale(armature, bone, bulk, legs, bulk)
        for bone in ("pelvis", "upperarm_l", "upperarm_r", "spine_02"):
            hold_scale(armature, bone, bulk, 1.0, bulk)
    # Shorter legs leave the feet in the air; snap_to_floor puts every frame back on the floor
    # (lowering the body here instead would push lying poses below the cell).
    if head != 1.0:
        inherited = bulk if bulk != 1.0 else 1.0    # spine_02's thickness already reaches the head
        hold_scale(armature, "Head", head / inherited, head, head / inherited)


def setup_camera(scene, tilt_deg=0.0):
    metres_per_px = PERSON_HEIGHT_M / PERSON_HEIGHT_PX
    cam_data = bpy.data.cameras.new("SpriteCam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = CELL_W * metres_per_px          # ortho scale spans the wider side
    cam = bpy.data.objects.new("SpriteCam", cam_data)
    scene.collection.objects.link(cam)
    # Look along +Y from the front side of the screen; X is screen-right, Z is up.
    centre_z = CELL_H * metres_per_px / 2 - FEET_FROM_BOTTOM * metres_per_px
    # Tilt looks down from slightly above, like the game's street (seen from above the road).
    tilt = math.radians(tilt_deg)
    cam.location = (0.0, -10.0 * math.cos(tilt), centre_z + 10.0 * math.sin(tilt))
    cam.rotation_euler = (math.radians(90) - tilt, 0.0, 0.0)
    scene.camera = cam


def setup_render(scene, flat):
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
    # Light from the front-left of the figure so its side shows a lit and a shaded half.
    shading.studiolight_rotate_z = math.radians(LIGHT_TURN_DEG)
    if flat:
        shading.color_type = "SINGLE"
        shading.single_color = flat
    else:
        shading.color_type = "TEXTURE"                  # skin and clothes come from their textures
    shading.show_object_outline = False                 # the outline is drawn after rendering
    shading.show_cavity = False                         # cavity reads as noise at this size
    scene.view_settings.view_transform = "Standard"


# Frames and sheets ---------------------------------------------------------------

def frames_of(action, count, frame_range=None):
    start, end = frame_range or action.frame_range
    if count <= 1:
        return [int(start)]
    if frame_range is None and action.name.endswith("_Loop"):
        step = (end - start) / count                     # loop: the last frame equals the first
    else:
        step = (end - start) / (count - 1)               # one-shot or a cut: keep the final pose
    return [round(start + i * step) for i in range(count)]


def assign_action(armature, action):
    data = armature.animation_data or armature.animation_data_create()
    data.action = action
    # Blender 4.4+ actions have slots; a borrowed action must be pointed at its slot.
    slots = getattr(action, "slots", None)
    if slots and getattr(data, "action_slot", None) is None:
        data.action_slot = slots[0]


def finish_pixels(pixels, bands, outline):
    """Cel bands on the light and a 1 px outline; pixels is a flat RGBA list, bottom row first."""
    px = list(pixels)
    solid = [px[i + 3] >= 0.5 for i in range(0, len(px), 4)]
    for n, is_solid in enumerate(solid):
        i = n * 4
        if not is_solid:
            px[i:i + 4] = [0.0, 0.0, 0.0, 0.0]
            continue
        if bands:
            r, g, b = px[i:i + 3]
            value = max(r, g, b, 1e-6)
            banded = max(1, round(value * bands)) / bands
            px[i:i + 3] = [min(1.0, r * banded / value), min(1.0, g * banded / value), min(1.0, b * banded / value)]
        px[i + 3] = 1.0
    if outline:
        for n, is_solid in enumerate(solid):
            if is_solid:
                continue
            x, y = n % CELL_W, n // CELL_W
            near = any(0 <= x + dx < CELL_W and 0 <= y + dy < CELL_H and solid[(y + dy) * CELL_W + x + dx]
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if near:
                px[n * 4:n * 4 + 4] = [*OUTLINE_RGB, 1.0]
    return px


def snap_to_floor(px):
    """Move the frame up or down so its lowest solid pixel sits on the floor line.

    Whatever touches the ground (a foot while walking, the back while lying down) ends on
    the same line, so a shortened body never floats or sinks through the floor.
    """
    row_len = CELL_W * 4
    lowest = next((y for y in range(CELL_H) if any(px[y * row_len + x * 4 + 3] > 0 for x in range(CELL_W))), None)
    target = FEET_FROM_BOTTOM                            # rows count from the bottom: row 59 from the top
    if lowest is None or lowest == target:
        return px
    shift = target - lowest
    out = [0.0] * len(px)
    for y in range(CELL_H):
        src = y - shift
        if 0 <= src < CELL_H:
            out[y * row_len:(y + 1) * row_len] = px[src * row_len:(src + 1) * row_len]
    return out


def render_sheet(scene, armature, action, count, out_dir, tmp_dir, sheet_name, frame_range, args):
    assign_action(armature, action)
    frames = frames_of(action, count, frame_range)
    sheet = bpy.data.images.new(f"sheet_{sheet_name}", CELL_W * len(frames), CELL_H, alpha=True)
    sheet_px = [0.0] * (CELL_W * len(frames) * CELL_H * 4)
    for index, frame in enumerate(frames):
        scene.frame_set(frame)
        path = os.path.join(tmp_dir, f"{sheet_name}_{index}.png")
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        image = bpy.data.images.load(path)
        px = snap_to_floor(finish_pixels(image.pixels[:], args.bands, args.outline))
        for y in range(CELL_H):
            src = y * CELL_W * 4
            dst = (y * CELL_W * len(frames) + index * CELL_W) * 4
            sheet_px[dst:dst + CELL_W * 4] = px[src:src + CELL_W * 4]
        bpy.data.images.remove(image)
    sheet.pixels[:] = sheet_px
    sheet.filepath_raw = os.path.join(out_dir, f"{sheet_name}.png")
    sheet.file_format = "PNG"
    sheet.save()
    print(f"saved {sheet.filepath_raw} ({len(frames)} frames: {frames})")


def parse_map_entry(entry):
    """'pickup=Fixing_Kneeling@0-30' -> ('pickup', 'Fixing_Kneeling', (0, 30))."""
    sheet_name, action_part = entry.split("=", 1)
    frame_range = None
    if "@" in action_part:
        action_part, span = action_part.split("@", 1)
        start, end = span.split("-")
        frame_range = (float(start), float(end))
    return sheet_name, action_part, frame_range


def safe_name(name):
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name).lower()


def main():
    args = parse_args()
    clear_scene()
    import_model(os.path.abspath(args.model))
    if args.anim_file:
        import_animations(os.path.abspath(args.anim_file))
    if args.list:
        for action in bpy.data.actions:
            print(f"ACTION {action.name} {tuple(action.frame_range)}")
        return
    scene = bpy.context.scene
    armature = find_armature()
    remove_loose_meshes(armature)
    for obj in bpy.data.objects:
        if obj.parent is None and obj.type in ("ARMATURE", "MESH", "EMPTY"):
            obj.rotation_mode = "XYZ"                    # glTF imports use quaternions; switch first
            obj.rotation_euler[2] += math.radians(args.turn)
    shape_body(armature, args.head, args.bulk, args.legs)
    flat = tuple(float(v) for v in args.flat.split(",")) if args.flat else None
    setup_camera(scene, args.tilt)
    setup_render(scene, flat)
    out_dir = os.path.abspath(args.out)
    tmp_dir = os.path.join(out_dir, "_frames")
    os.makedirs(tmp_dir, exist_ok=True)
    counts = dict(pair.split("=") for pair in (args.frames_for or []))
    shifts = {k: float(v) for k, v in (pair.split("=") for pair in (args.shift_for or []))}
    if armature is None:
        scene.render.filepath = os.path.join(out_dir, "rest.png")
        bpy.ops.render.render(write_still=True)
        print("saved rest pose only (no armature)")
        return
    entries = [parse_map_entry(e) for e in args.map] if args.map else \
        [(safe_name(a.name), a.name, None) for a in bpy.data.actions]
    for sheet_name, action_name, frame_range in entries:
        action = bpy.data.actions.get(action_name)
        if action is None:
            print(f"missing action {action_name}")
            continue
        # Moving the camera left moves the figure right in the cell.
        scene.camera.location.x = -shifts.get(sheet_name, 0.0) * PERSON_HEIGHT_M / PERSON_HEIGHT_PX
        render_sheet(scene, armature, action, int(counts.get(sheet_name, args.frames)),
                     out_dir, tmp_dir, sheet_name, frame_range, args)


main()
