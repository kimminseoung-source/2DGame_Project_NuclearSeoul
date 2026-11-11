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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import costume as costumes                              # noqa: E402  (Blender adds no script dir)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CELL_W, CELL_H = 96, 64
FEET_FROM_BOTTOM = 4            # px: the feet line is y = 60 from the top
PERSON_HEIGHT_M = 1.8
PERSON_HEIGHT_PX = 54
OUTLINE_RGB = (0.06, 0.07, 0.10)
LIGHT_TURN_DEG = 70             # studio light rotation around the vertical axis


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None, help="body file; not needed with --costume")
    parser.add_argument("--costume", default=None,
                        help="costume JSON (assets/characters/costumes/): body, proportions, colours, hair, props")
    parser.add_argument("--out", required=True)
    parser.add_argument("--anim-file", nargs="*", default=None,
                        help="file whose actions are borrowed (same bone names), e.g. the animation library")
    parser.add_argument("--map", nargs="*", default=None,
                        help="sheet=action pairs, optionally with a frame range: pickup=Fixing_Kneeling@0-30")
    parser.add_argument("--frames", type=int, default=8)
    parser.add_argument("--frames-for", nargs="*", default=None,
                        help="sheet=count pairs overriding --frames, e.g. walk=8 hurt=3")
    parser.add_argument("--list", action="store_true", help="only print the actions and stop")
    parser.add_argument("--turn", type=float, default=90.0, help="degrees to turn the model to face right")
    parser.add_argument("--keep-root", action="store_true",
                        help="let the root bone travel (default: pinned so sprites stay on the spot)")
    parser.add_argument("--pass", dest="render_pass", choices=["color", "id", "light", "tex"], default="color",
                        help="id: each costume part in a flat ID colour; light: white body, light only "
                             "(both for tools/sprites/repaint.py). Bands and outline are skipped for them.")
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
    """Import a file only for its actions; its own objects are removed again.

    A file with one motion (a Mixamo download: every action is called "mixamo.com")
    names its longest new action after the file, e.g. Walking.fbx -> action "Walking".
    """
    before = set(bpy.data.objects)
    old_actions = set(bpy.data.actions)
    import_model(path)
    new = [a for a in bpy.data.actions if a not in old_actions]
    if new and os.path.splitext(path)[1].lower() == ".fbx":
        longest = max(new, key=lambda a: a.frame_range[1] - a.frame_range[0])
        longest.name = os.path.splitext(os.path.basename(path))[0]
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
        hips = armature.pose.bones.get("mixamorig:Hips")
        if hips is not None:
            # Mixamo rigs have no root: hold the hips over their rest spot (world X and Y)
            # but let them bob and crouch (world Z).
            bpy.context.view_layer.update()
            rest = armature.matrix_world @ hips.head
            c = hips.constraints.new("LIMIT_LOCATION")
            c.use_min_x = c.use_max_x = c.use_min_y = c.use_max_y = True
            c.min_x = c.max_x = rest.x
            c.min_y = c.max_y = rest.y
            c.owner_space = "WORLD"
        return
    c = pose_bone.constraints.new("LIMIT_SCALE")
    c.use_min_x = c.use_max_x = c.use_min_y = c.use_max_y = c.use_min_z = c.use_max_z = True
    c.min_x = c.max_x = x
    c.min_y = c.max_y = y
    c.min_z = c.max_z = z
    c.owner_space = "LOCAL"


def pin_root(armature, bone="root"):
    """Keep the root bone in place so every sheet is drawn on the spot.

    Some actions carry their travel on the root (Sword_Regular_A steps about 1 m forward);
    the game moves the character itself, so a travelling sprite would jump back at the end.
    """
    pose_bone = armature.pose.bones.get(bone)
    if pose_bone is None:
        return
    c = pose_bone.constraints.new("LIMIT_LOCATION")
    c.use_min_x = c.use_max_x = c.use_min_y = c.use_max_y = c.use_min_z = c.use_max_z = True
    c.min_x = c.max_x = c.min_y = c.max_y = c.min_z = c.max_z = 0.0
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


def setup_render(scene, flat, painted=False, render_pass="color"):
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
    if render_pass == "id":
        shading.light = "FLAT"                          # pure part colours, no light
        shading.color_type = "VERTEX"
    elif render_pass == "tex":
        shading.light = "FLAT"                          # the model's own texture, no light
        shading.color_type = "TEXTURE"
    elif render_pass == "light":
        shading.color_type = "SINGLE"                   # white everywhere: only the light shows
        shading.single_color = (1.0, 1.0, 1.0)
    elif painted:
        shading.color_type = "VERTEX"                   # costume colours painted on the meshes
    elif flat:
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
    # Keep fractions: evenly spaced cells matter for walk cycles (the feet stay planted).
    return [round(start + i * step, 3) for i in range(count)]


def assign_action(armature, action, blend=None):
    """Play one action, or mix a second one over it: blend = (action, weight 0..1).

    Mixing lets a free pack make poses it lacks, e.g. sneak = walk with a little crouch.
    The second action is stretched to the first one's length so both loops stay in step.
    """
    data = armature.animation_data or armature.animation_data_create()
    for track in list(data.nla_tracks):
        data.nla_tracks.remove(track)
    data.action = action
    # Blender 4.4+ actions have slots; a borrowed action must be pointed at its slot.
    slots = getattr(action, "slots", None)
    if slots and getattr(data, "action_slot", None) is None:
        data.action_slot = slots[0]
    if blend is None:
        return
    over, weight = blend
    data.action = None
    base_start, base_end = action.frame_range
    over_start, over_end = over.frame_range
    for act, influence in ((action, None), (over, weight)):
        track = data.nla_tracks.new()
        strip = track.strips.new(act.name, int(base_start), act)
        if getattr(act, "slots", None) and hasattr(strip, "action_slot"):
            strip.action_slot = act.slots[0]
        strip.blend_type = "REPLACE"
        if act is over:
            # COMBINE adds the second pose on top with proper rotation maths (REPLACE mixes
            # quaternions component by component and can flip a leg backwards).
            strip.blend_type = "COMBINE"
            strip.scale = (base_end - base_start) / max(1e-6, over_end - over_start)
            strip.use_animated_influence = True
            strip.influence = influence
            strip.keyframe_insert("influence", frame=int(base_start))


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


def render_sheet(scene, armature, segments, out_dir, tmp_dir, sheet_name, args):
    """Render one sheet from one or more segments played one after another.

    segments: [(action, frame_range, blend, count)]. Several segments let an attack be
    followed by its recovery, e.g. swing = Sword_Regular_A then Sword_Regular_A_Rec.
    """
    cells = []                                          # (segment index, action frame)
    for seg_index, (action, frame_range, blend, count) in enumerate(segments):
        cells += [(seg_index, f) for f in frames_of(action, count, frame_range)]
    sheet = bpy.data.images.new(f"sheet_{sheet_name}", CELL_W * len(cells), CELL_H, alpha=True)
    sheet_px = [0.0] * (CELL_W * len(cells) * CELL_H * 4)
    current = None
    for index, (seg_index, frame) in enumerate(cells):
        if seg_index != current:
            action, _, blend, _ = segments[seg_index]
            assign_action(armature, action, blend)
            current = seg_index
        scene.frame_set(int(frame), subframe=frame - int(frame))
        path = os.path.join(tmp_dir, f"{sheet_name}_{index}.png")
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        image = bpy.data.images.load(path)
        px = snap_to_floor(finish_pixels(image.pixels[:], args.bands, args.outline))
        for y in range(CELL_H):
            src = y * CELL_W * 4
            dst = (y * CELL_W * len(cells) + index * CELL_W) * 4
            sheet_px[dst:dst + CELL_W * 4] = px[src:src + CELL_W * 4]
        bpy.data.images.remove(image)
    sheet.pixels[:] = sheet_px
    sheet.filepath_raw = os.path.join(out_dir, f"{sheet_name}.png")
    sheet.file_format = "PNG"
    sheet.save()
    print(f"saved {sheet.filepath_raw} ({len(cells)} frames: {[f for _, f in cells]})")


def parse_segment(text):
    """'Fixing_Kneeling@0-30' -> ('Fixing_Kneeling', (0, 30), None).
    'Walk_Loop+Crouch_Fwd_Loop*0.4' -> ('Walk_Loop', None, ('Crouch_Fwd_Loop', 0.4))."""
    frame_range = None
    blend = None
    if "+" in text:
        text, over = text.split("+", 1)
        over_name, weight = over.split("*") if "*" in over else (over, "0.5")
        blend = (over_name, float(weight))
    if "@" in text:
        text, span = text.split("@", 1)
        start, end = span.split("-")
        frame_range = (float(start), float(end))
    return text, frame_range, blend


def parse_map_entry(entry):
    """'swing=Sword_Regular_A,Sword_Regular_A_Rec' -> ('swing', [segment, segment]).
    Segments are played in order; each is parsed by parse_segment."""
    sheet_name, action_part = entry.split("=", 1)
    return sheet_name, [parse_segment(part) for part in action_part.split(",")]


def safe_name(name):
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name).lower()


def main():
    args = parse_args()
    outfit = costumes.load(args.costume) if args.costume else None
    if outfit:
        # The costume decides the body and its proportions.
        args.model = args.model or costumes.model_path(outfit, PROJECT_ROOT)
        args.head = outfit.get("head", args.head)
        args.bulk = outfit.get("bulk", args.bulk)
        args.legs = outfit.get("legs", args.legs)
    if not args.model:
        raise SystemExit("--model or --costume is required")
    clear_scene()
    import_model(os.path.abspath(args.model))
    for anim_file in args.anim_file or []:
        import_animations(os.path.abspath(anim_file))
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
    if outfit and armature is not None:
        # Every pass needs the same clothes and props; only the id pass repaints them.
        costumes.apply(armature, outfit, PROJECT_ROOT, ids=args.render_pass == "id")
    if armature is not None and not args.keep_root:
        pin_root(armature)
    shape_body(armature, args.head, args.bulk, args.legs)
    flat = tuple(float(v) for v in args.flat.split(",")) if args.flat else None
    setup_camera(scene, args.tilt)
    setup_render(scene, flat, painted=bool(outfit), render_pass=args.render_pass)
    if args.render_pass != "color":
        args.bands, args.outline = 0, False             # repaint.py shades and outlines later
    out_dir = os.path.abspath(args.out)
    tmp_dir = os.path.join(out_dir, "_frames")
    os.makedirs(tmp_dir, exist_ok=True)
    if args.render_pass == "id":
        import json
        with open(os.path.join(out_dir, "ids.json"), "w", encoding="utf-8") as f:
            json.dump(costumes.id_map(), f, ensure_ascii=False, indent=2)
    counts = dict(pair.split("=") for pair in (args.frames_for or []))
    shifts = {k: float(v) for k, v in (pair.split("=") for pair in (args.shift_for or []))}
    if armature is None:
        scene.render.filepath = os.path.join(out_dir, "rest.png")
        bpy.ops.render.render(write_still=True)
        print("saved rest pose only (no armature)")
        return
    entries = [parse_map_entry(e) for e in args.map] if args.map else         [(safe_name(a.name), [(a.name, None, None)]) for a in bpy.data.actions]
    for sheet_name, parts in entries:
        # --frames-for swing=6,3 gives each segment its own frame count.
        sheet_counts = [int(c) for c in str(counts.get(sheet_name, args.frames)).split(",")]
        segments = []
        for seg_index, (action_name, frame_range, blend) in enumerate(parts):
            action = bpy.data.actions.get(action_name)
            over = bpy.data.actions.get(blend[0]) if blend else None
            if action is None or (blend and over is None):
                print(f"missing action {action_name if action is None else blend[0]}")
                segments = None
                break
            count = sheet_counts[min(seg_index, len(sheet_counts) - 1)]
            segments.append((action, frame_range, (over, blend[1]) if blend else None, count))
        if not segments:
            continue
        # Moving the camera left moves the figure right in the cell.
        scene.camera.location.x = -shifts.get(sheet_name, 0.0) * PERSON_HEIGHT_M / PERSON_HEIGHT_PX
        render_sheet(scene, armature, segments, out_dir, tmp_dir, sheet_name, args)


if __name__ == "__main__":                              # also importable (export_pose2d.py)
    main()
