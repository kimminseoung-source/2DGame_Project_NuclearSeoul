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
outfit texture under each face: blue = jeans, red or near-black stripes = shirt, the rest =
jacket. ids.json is written next to the frames.
"""

import argparse
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector


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


def retarget(src, dst, frame):
    """Pose dst like src at this frame (world orientations, rest offsets kept)."""
    scene = bpy.context.scene
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    sw, dw = src.matrix_world, dst.matrix_world
    order = []

    def walk(b):
        order.append(b.name)
        for c in b.children:
            walk(c)
    for b in dst.data.bones:
        if b.parent is None:
            walk(b)
    src_hips = src.pose.bones.get("mixamorig:Hips")
    src_rest_h = (sw @ src.data.bones["mixamorig:Hips"].matrix_local).to_translation()
    dst_rest_h = (dw @ dst.data.bones["mixamorig:Hips"].matrix_local).to_translation()
    k = dst_rest_h.z / max(1e-6, src_rest_h.z)
    for name in order:
        sb, db = src.pose.bones.get(name), dst.pose.bones.get(name)
        if sb is None or db is None:
            continue
        s_rest = (sw @ src.data.bones[name].matrix_local).to_quaternion()
        d_rest = (dw @ dst.data.bones[name].matrix_local).to_quaternion()
        s_now = (sw @ sb.matrix).to_quaternion()
        # Bones point along their Y axis. Turn our rest bone onto the source's rest direction
        # (T-pose vs A-pose arms), keep our roll, then follow the source's turn from there:
        # each bone ends up pointing exactly where the source bone points.
        y = Vector((0, 1, 0))
        align = (d_rest @ y).rotation_difference(s_rest @ y)
        want = s_now @ (s_rest.inverted() @ (align @ d_rest))
        loc = (dw @ db.matrix).to_translation()
        if name == "mixamorig:Hips" and src_hips is not None:
            move = (sw @ src_hips.matrix).to_translation() - src_rest_h
            loc = dst_rest_h + move * k
        m = Matrix.Translation(loc) @ want.to_matrix().to_4x4()
        db.matrix = dw.inverted() @ m
        bpy.context.view_layer.update()


PARTS = {"skin": (0.85, 0.55, 0.40), "hair": (0.10, 0.10, 0.10), "eyes": (0.05, 0.9, 0.3),
         "jacket": (0.9, 0.7, 0.1), "shirt": (0.95, 0.95, 0.95), "jeans": (0.1, 0.2, 0.9),
         "boots": (0.6, 0.1, 0.6)}


def part_of_object(o):
    n = o.name.lower()
    for key, part in (("eyebrow", "hair"), ("short", "hair"), ("hair", "hair"), ("low-poly", "eyes"),
                      ("high-poly", "eyes"), ("shoes", "boots"), ("body", "skin")):
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
    if r > g + 0.1 or lum < 0.16:
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


def frame_cam(cam, a, height_m, centre, feet_z):
    tilt = math.radians(a.tilt)
    d = 10.0
    if a.pixel:
        px = height_m / a.person_px                              # metres per pixel
        cam.data.ortho_scale = px * a.pixel
        # feet a.feet px above the bottom edge (seen through the tilt)
        aim_z = feet_z + (a.pixel / 2 - a.feet) * px / math.cos(tilt)
        aim = Vector((centre.x, centre.y, aim_z))
    else:
        cam.data.ortho_scale = height_m * 1.15
        aim = centre
    cam.location = aim + Vector((0, -d * math.cos(tilt), d * math.sin(tilt)))
    cam.rotation_euler = (math.radians(90) - tilt, 0, 0)


def main():
    a = args()
    dst = target_rig()
    src = import_source(a.anim)
    act = src.animation_data.action if src.animation_data else None
    f0, f1 = (int(act.frame_range[0]), int(act.frame_range[1])) if act else (1, 1)
    frames = [round(f0 + (f1 - f0) * i / max(1, a.frames)) for i in range(a.frames)]
    cam = setup(a)
    if a.render_pass != "color":
        setup_workbench(bpy.context.scene, a.render_pass)
        if a.render_pass == "id":
            paint_ids()
    meshes = [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render]
    rest_pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    height = max(p.z for p in rest_pts) - min(p.z for p in rest_pts)
    feet_z = min(p.z for p in rest_pts)
    centre = Vector((0, 0, feet_z + height / 2))
    os.makedirs(a.out, exist_ok=True)
    if a.render_pass == "id":
        import json
        with open(os.path.join(a.out, "ids.json"), "w", encoding="utf-8") as f:
            json.dump({k: [round(c * 255) for c in v] for k, v in PARTS.items()}, f, indent=1)
    scene = bpy.context.scene
    for t in a.turn:
        for i, f in enumerate(frames):
            retarget(src, dst, f)
            dst.rotation_euler[2] = math.radians(t)
            bpy.context.view_layer.update()
            frame_cam(cam, a, height, centre, feet_z)
            scene.render.filepath = os.path.join(a.out, f"{a.name}_t{int(t)}_{i}.png")
            bpy.ops.render.render(write_still=True)
            print("saved", scene.render.filepath)
        dst.rotation_euler[2] = 0


if __name__ == "__main__":
    main()
