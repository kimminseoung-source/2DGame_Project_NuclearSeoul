"""Put a Mixamo action on the MPFB hero and render it (2026-11-20).

    blender -b <busan_hero.blend> -P tools/blender/mpfb_pose.py -- --anim assets/source3d/mixamo/Breathing_Idle.fbx
        --frames 1 --out <dir> [--size 640 | --pixel 64 --person-px 36] [--turn 0 45 90] [--tilt 10]

The MPFB "mixamo" skeleton has Mixamo's bone names. Mixamo rotations are relative to Mixamo's
own rest pose, which is not ours (T-pose vs MPFB's A-pose, other bone rolls), so each frame is
retargeted by world orientation: for every bone, target world rotation = source world rotation
x (source rest -> target rest) offset, from the hips down the chain; the hips also take the
source's travel, scaled by leg length. The rig is then posed frame by frame.

--size: a large soft-lit check render. --pixel: a sprite-size render, no smoothing, figure
person_px tall (feet on the same row in every frame), for tools/sprites/dots_from_render.py.

--pass id / light (with --pixel): like render_sprites.py, for tools/sprites/repaint.py.
Realistic textures turn to mud at 36 px, so the figure is split into parts and each part gets
one flat ID colour (id pass); a white figure under the studio light gives the light (light
pass); repaint.py then paints each part with a 3-step colour ramp. Parts come from the MPFB
objects (body = skin, hair, eyebrows, eyes, shoes) and, for the one-mesh outfit, from the
outfit texture under each face: blue = jeans, light, red or near-black = shirt, the rest
(mid grey-green) = jacket. ids.json is written next to the frames.
"""

import argparse
import math
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector


def args():
    p = argparse.ArgumentParser()
    p.add_argument("--anim", required=True)
    p.add_argument("--frames", type=int, default=1)
    p.add_argument("--out", required=True)
    p.add_argument("--size", type=int, default=640)
    p.add_argument("--pixel", type=int, default=0)
    p.add_argument("--person-px", type=int, default=36)
    p.add_argument("--feet", type=int, default=6)
    p.add_argument("--turn", type=float, nargs="+", default=[0, 45, 90])
    p.add_argument("--tilt", type=float, default=10)
    p.add_argument("--name", default="act")
    p.add_argument("--pass", dest="render_pass", choices=["color", "id", "light"], default="color")
    p.add_argument("--weapon", type=float, default=0.0, help="test pipe length in metres (0 = none)")
    p.add_argument("--weapon-axis", default="z", choices=["x", "-x", "z", "-z"],
                   help="which way the pipe leaves the fist, in the hand bone's axes")
    p.add_argument("--damp", nargs="*", default=[], help="bone=share, e.g. Spine=0.5 (mixamorig: added)")
    p.add_argument("--upper", default=None, help="another Mixamo action for the spine and above (aim while walking)")
    p.add_argument("--upper-at", type=float, default=0.4, help="which moment of --upper, 0..1 of its length")
    p.add_argument("--hide-weapon", action="store_true",
                   help="keep the test pipe out of the picture (the game draws the weapon) but still measure it")
    p.add_argument("--record", default=None,
                   help="json: per picture the hand (picture px, x right, y down) and where the weapon points "
                        "(degrees, y up), for the game's hands.json / keyframes.json")
    return p.parse_args(sys.argv[sys.argv.index("--") + 1:])


def target_rig():
    return next(o for o in bpy.data.objects if o.type == "ARMATURE")


def import_source(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.abspath(path), automatic_bone_orientation=False)
    new = [o for o in bpy.data.objects if o not in before]
    src = next(o for o in new if o.type == "ARMATURE")
    for o in new:
        if o.type == "MESH":
            o.hide_render = True
            o.hide_viewport = True
    return src


def snapshot(src, frame):
    """The source's bones at a frame, in world space (so two sources can be mixed)."""
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    return {b.name: src.matrix_world @ b.matrix for b in src.pose.bones}


def retarget(src, dst, frame, damp=None, snap=None, only=None, rebase=None):
    """Pose dst like src at this frame (world orientations, rest offsets kept).
    damp: bone -> share of its own turn to keep (0.5 = half). Only that bone's local turn is
    eased; its children are still set to the source's world directions, so arms and head
    point the same way while the torso bends less (2026-11-20: "허리가 과하게 젖혀짐").
    snap / only / rebase mix two actions (2026-11-20, "하체를 분리해서 조준 상태에서도 걷게"):
    only these bones are set, from a snapshot of another source, turned by `rebase` so they
    sit on the hips the first action already posed."""
    damp = damp or {}
    snap = snap or snapshot(src, frame)
    rebase = rebase or Quaternion()
    sw, dw = src.matrix_world, dst.matrix_world
    order = []

    def walk(b):
        order.append(b.name)
        for c in b.children:
            walk(c)
    for b in dst.data.bones:
        if b.parent is None:
            walk(b)
    src_rest_h = (sw @ src.data.bones["mixamorig:Hips"].matrix_local).to_translation()
    dst_rest_h = (dw @ dst.data.bones["mixamorig:Hips"].matrix_local).to_translation()
    k = dst_rest_h.z / max(1e-6, src_rest_h.z)
    for name in order:
        db = dst.pose.bones.get(name)
        if name not in snap or db is None or (only is not None and name not in only):
            continue
        s_rest = (sw @ src.data.bones[name].matrix_local).to_quaternion()
        d_rest = (dw @ dst.data.bones[name].matrix_local).to_quaternion()
        s_now = rebase @ snap[name].to_quaternion()
        # Bones point along their Y axis. Turn our rest bone onto the source's rest direction
        # (T-pose vs A-pose arms), keep our roll, then follow the source's turn from there:
        # each bone ends up pointing exactly where the source bone points.
        y = Vector((0, 1, 0))
        align = (d_rest @ y).rotation_difference(s_rest @ y)
        want = s_now @ (s_rest.inverted() @ (align @ d_rest))
        loc = (dw @ db.matrix).to_translation()
        if name == "mixamorig:Hips":
            loc = dst_rest_h + (snap[name].to_translation() - src_rest_h) * k
        m = Matrix.Translation(loc) @ want.to_matrix().to_4x4()
        db.matrix = dw.inverted() @ m
        if name in damp:
            db.rotation_mode = "QUATERNION"
            db.rotation_quaternion = Quaternion().slerp(db.rotation_quaternion, damp[name])
        if name == "mixamorig:Head" and dst.get("head_scale"):
            db.scale = (dst["head_scale"],) * 3                  # the sprite head size (mpfb_hero.py)
        bpy.context.view_layer.update()


def upper_bones(rig):
    """The spine and everything above it (the part that aims), by the rig's own hierarchy."""
    out = set()

    def walk(b):
        out.add(b.name)
        for c in b.children:
            walk(c)
    walk(rig.data.bones["mixamorig:Spine"])
    return out


PARTS = {"skin": (0.85, 0.55, 0.40), "hair": (0.10, 0.10, 0.10), "eyes": (0.05, 0.9, 0.3),
         "jacket": (0.9, 0.7, 0.1), "shirt": (0.95, 0.95, 0.95), "jeans": (0.1, 0.2, 0.9),
         "boots": (0.6, 0.1, 0.6), "top": (1.0, 0.45, 0.0), "weapon": (0.5, 0.5, 0.55)}


def part_of_object(o):
    n = o.name.lower()
    for key, part in (("eyebrow", "hair"), ("short", "hair"), ("hair", "hair"), ("low-poly", "eyes"),
                      ("high-poly", "eyes"), ("shoes", "boots"), ("body", "skin"),
                      ("sweater", "top"), ("shirt", "top"), ("pants", "jeans"), ("weapon", "weapon")):
        if key in n:
            return part
    return None


def texture_of(o):
    for slot in o.material_slots:
        if slot.material and slot.material.use_nodes:
            for nd in slot.material.node_tree.nodes:
                if nd.type == "TEX_IMAGE" and nd.image and "diffuse" in nd.image.name.lower():
                    return nd.image
    return None


def outfit_part(rgb):
    r, g, b = rgb
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    if b > r + 0.08 and b > g:
        return "jeans"
    if r > g + 0.1 or lum < 0.16 or lum > 0.55:          # stripes, a print, or a light T-shirt
        return "shirt"
    return "jacket"


def paint_ids():
    """One flat colour per part on every face (colour attribute, face corners)."""
    for o in [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render]:
        part = part_of_object(o)
        img = texture_of(o) if part is None else None
        px = list(img.pixels) if img else None
        me = o.data
        for a in list(me.color_attributes):
            me.color_attributes.remove(a)
        attr = me.color_attributes.new("id", "FLOAT_COLOR", "CORNER")
        uv = me.uv_layers.active.data if me.uv_layers.active else None
        for poly in me.polygons:
            name = part
            if name is None and img and uv:
                u = sum(uv[i].uv[0] for i in poly.loop_indices) / poly.loop_total
                v = sum(uv[i].uv[1] for i in poly.loop_indices) / poly.loop_total
                x = min(img.size[0] - 1, max(0, int(u % 1 * img.size[0])))
                y = min(img.size[1] - 1, max(0, int(v % 1 * img.size[1])))
                k = (y * img.size[0] + x) * 4
                name = outfit_part(px[k:k + 3])
            col = PARTS.get(name or "jacket")
            for i in poly.loop_indices:
                attr.data[i].color = (*col, 1.0)
        me.color_attributes.active_color = attr


def setup_workbench(scene, render_pass):
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.render_aa = "OFF"
    sh = scene.display.shading
    if render_pass == "id":
        sh.light = "FLAT"
        sh.color_type = "VERTEX"
    else:
        sh.light = "STUDIO"
        sh.studiolight_rotate_z = math.radians(-40)
        sh.color_type = "SINGLE"
        sh.single_color = (1.0, 1.0, 1.0)
    sh.show_object_outline = False
    sh.show_cavity = False
    scene.view_settings.view_transform = "Standard"


def setup(a):
    scene = bpy.context.scene
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in engines else engines[0]
    scene.render.film_transparent = True
    if a.pixel:
        scene.render.resolution_x = scene.render.resolution_y = a.pixel
        scene.render.filter_size = 0.0                          # no smoothing between pixels
        try:
            scene.eevee.taa_render_samples = 1
        except AttributeError:
            pass
    else:
        scene.render.resolution_x = scene.render.resolution_y = a.size
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.type = "ORTHO"
    scene.collection.objects.link(cam)
    scene.camera = cam
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(50), 0, math.radians(-35))   # from the front-left, above
    scene.collection.objects.link(sun)
    world = scene.world or bpy.data.worlds.new("w")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    return cam


def frame_cam(cam, a, rest_pts):
    """Camera for the whole action, fixed from the standing body: in --pixel mode the standing
    figure is person_px tall ON SCREEN (the tilt shortens it) and its lowest point sits a.feet px
    above the bottom edge, so every frame and direction shares one scale and one floor row."""
    tilt = math.radians(a.tilt)
    d = 10.0
    lo = Vector([min(p[i] for p in rest_pts) for i in range(3)])
    hi = Vector([max(p[i] for p in rest_pts) for i in range(3)])
    centre = (lo + hi) / 2
    cam.rotation_euler = (math.radians(90) - tilt, 0, 0)
    cam.location = centre + Vector((0, -d * math.cos(tilt), d * math.sin(tilt)))
    bpy.context.view_layer.update()
    inv = cam.matrix_world.inverted()
    ys = [(inv @ p).y for p in rest_pts]
    tall = max(ys) - min(ys)                                     # on-screen height, metres
    if not a.pixel:
        cam.data.ortho_scale = tall * 1.15
        return
    px = tall / a.person_px
    cam.data.ortho_scale = px * a.pixel
    want = -a.pixel / 2 * px + a.feet * px                       # feet row in camera space
    up = cam.matrix_world.to_quaternion() @ Vector((0, 1, 0))
    cam.location += up * (min(ys) - want)
    bpy.context.view_layer.update()


def add_weapon(rig, length, axis="x"):
    """A test pipe in the right fist (for judging the motion only; the game draws its own
    weapon at the hand, character_look.draw_weapon)."""
    import bmesh
    me = bpy.data.meshes.new("weapon")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.022, radius2=0.022, depth=length)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new("weapon_pipe", me)
    bpy.context.scene.collection.objects.link(obj)
    mat = bpy.data.materials.new("pipe")
    mat.diffuse_color = (0.45, 0.45, 0.5, 1)
    me.materials.append(mat)
    bone = rig.data.bones["mixamorig:RightHand"]
    rest = rig.matrix_world @ bone.matrix_local
    # fist ~8 cm along the hand; the pipe crosses the palm (hand X), most of it on the thumb side
    turn = {"x": Matrix.Rotation(math.radians(90), 4, "Y"), "-x": Matrix.Rotation(math.radians(-90), 4, "Y"),
            "z": Matrix(), "-z": Matrix.Rotation(math.radians(180), 4, "Y")}[axis]
    along = turn @ Vector((0, 0, length * 0.35))
    place = rest @ Matrix.Translation(Vector((0, 0.08, 0)) + along) @ turn
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone.name
    bpy.context.view_layer.update()
    obj.matrix_world = place
    return obj


def hand_and_weapon(scene, cam, rig, axis):
    """The right fist's picture pixel and the pipe's screen angle (degrees, y up) this frame."""
    from bpy_extras.object_utils import world_to_camera_view
    pb = rig.pose.bones["mixamorig:RightHand"]
    m = rig.matrix_world @ pb.matrix
    grip = m @ Vector((0, 0.08, 0))
    along = {"x": Vector((1, 0, 0)), "-x": Vector((-1, 0, 0)), "z": Vector((0, 0, 1)), "-z": Vector((0, 0, -1))}[axis]
    tip = grip + (m.to_quaternion() @ along) * 0.5
    w, h = scene.render.resolution_x, scene.render.resolution_y
    g, e = world_to_camera_view(scene, cam, grip), world_to_camera_view(scene, cam, tip)
    gx, gy = g.x * w, (1 - g.y) * h
    ex, ey = e.x * w, (1 - e.y) * h
    return [round(gx - 0.5, 1), round(gy - 0.5, 1)], round(math.degrees(math.atan2(-(ey - gy), ex - gx)), 1)


def main():
    a = args()
    record = {}
    dst = target_rig()
    src = import_source(a.anim)
    up_src = import_source(a.upper) if a.upper else None
    act = src.animation_data.action if src.animation_data else None
    f0, f1 = (int(act.frame_range[0]), int(act.frame_range[1])) if act else (1, 1)
    frames = [round(f0 + (f1 - f0) * i / max(1, a.frames)) for i in range(a.frames)]
    if up_src is not None:
        ua = up_src.animation_data.action
        u0, u1 = ua.frame_range
        up_snap = snapshot(up_src, round(u0 + (u1 - u0) * a.upper_at))
        upper = upper_bones(dst)
    cam = setup(a)
    if a.weapon:
        pipe = add_weapon(dst, a.weapon, a.weapon_axis)
        if a.hide_weapon:
            pipe.hide_render = True
    if a.render_pass != "color":
        setup_workbench(bpy.context.scene, a.render_pass)
        if a.render_pass == "id":
            paint_ids()
    meshes = [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render and not o.name.startswith("weapon")]
    dg = bpy.context.evaluated_depsgraph_get()
    rest_pts = []
    for o in meshes:                                             # the standing body as it is drawn
        ev = o.evaluated_get(dg)
        m = ev.to_mesh()
        rest_pts += [o.matrix_world @ v.co for k, v in enumerate(m.vertices) if k % 7 == 0]
        ev.to_mesh_clear()
    frame_cam(cam, a, rest_pts)
    os.makedirs(a.out, exist_ok=True)
    if a.render_pass == "id":
        import json
        with open(os.path.join(a.out, "ids.json"), "w", encoding="utf-8") as f:
            json.dump({k: [round(c * 255) for c in v] for k, v in PARTS.items()}, f, indent=1)
    scene = bpy.context.scene
    for t in a.turn:
        for i, f in enumerate(frames):
            dst.rotation_euler[2] = 0                            # pose facing the source, then turn
            bpy.context.view_layer.update()
            snap = snapshot(src, f)
            retarget(src, dst, f, {("mixamorig:" + k): float(v) for k, v in (d.split("=") for d in a.damp)}, snap)
            if up_src is not None:                               # the aiming upper body on these legs
                turn = snap["mixamorig:Hips"].to_quaternion() @ up_snap["mixamorig:Hips"].to_quaternion().inverted()
                retarget(up_src, dst, f, snap=up_snap, only=upper, rebase=turn)
            dst.rotation_euler[2] = math.radians(t)
            bpy.context.view_layer.update()
            scene.render.filepath = os.path.join(a.out, f"{a.name}_t{int(t)}_{i}.png")
            if a.record:
                hand, ang = hand_and_weapon(scene, cam, dst, a.weapon_axis)
                record.setdefault(str(int(t)), []).append({"hand": hand, "weapon": ang})
            bpy.ops.render.render(write_still=True)
            print("saved", scene.render.filepath)
        dst.rotation_euler[2] = 0
    if a.record:
        import json
        with open(a.record, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=1)
        print("recorded", a.record)


if __name__ == "__main__":
    main()
