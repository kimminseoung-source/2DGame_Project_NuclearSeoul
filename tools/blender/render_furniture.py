"""Render furniture models (Kenney Furniture Kit, CC0) as 3/4-view pictures for the game
(2026-11-16 art pass A: "3D 무료 모델 → 도트 렌더", small first: four pieces).

    "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b -P tools/blender/render_furniture.py -- <out dir>

For each piece in PIECES: import the .glb from assets/source3d/kenney_furniture (not committed),
scale it to its real size in metres, and render it with an orthographic camera looking down at
ELEVATION degrees from the front, sun from the upper left like the rest of the game, at RES px per
metre on a clear background. tools/map/furniture_pixels.py then shrinks it to the game's dot size.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KIT = os.path.join(ROOT, "assets", "source3d", "kenney_furniture", "x", "Models", "GLTF format")
ELEVATION = 55             # camera angle above the floor, degrees (top and front both show)
RES = 160                  # render px per metre (shrunk later to the game's ~19 px per metre)
MUTE, DIM = 0.5, 0.72      # colour: share of the saturation kept, brightness kept
# name: model file, its longest floor side in metres, turn about the up axis (degrees)
PIECES = {"fridge": ("kitchenFridge", 0.8, 0), "stove": ("kitchenStove", 0.8, 0),
          "bed": ("bedSingle", 2.0, 0), "table": ("table", 1.2, 0)}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 32
    scene.cycles.device = "CPU"
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.new("sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.53, 0.58, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.22
    scene.world = world
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = 2.6
    sun.angle = math.radians(20)
    o = bpy.data.objects.new("sun", sun)
    o.rotation_euler = (math.radians(40), math.radians(-25), math.radians(20))   # from the upper left
    scene.collection.objects.link(o)
    return scene


def render(name, model, side_m, turn, out):
    scene = reset()
    bpy.ops.import_scene.gltf(filepath=os.path.join(KIT, model + ".glb"))
    objs = [o for o in scene.objects if o.type == "MESH"]
    # Kenney's bright toy colours, muted to the game's worn, dark world: half the saturation,
    # three quarters of the brightness, a little roughness
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        for node in mat.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                r, g, b, a = node.inputs["Base Color"].default_value
                grey = (r + g + b) / 3
                node.inputs["Base Color"].default_value = (
                    (grey + (r - grey) * MUTE) * DIM, (grey + (g - grey) * MUTE) * DIM, (grey + (b - grey) * MUTE) * DIM, a)
                node.inputs["Roughness"].default_value = max(0.6, node.inputs["Roughness"].default_value)
    root = bpy.data.objects.new("root", None)
    scene.collection.objects.link(root)
    for o in scene.objects:
        if o.parent is None and o is not root and o.type != "LIGHT":
            o.parent = root
    root.rotation_euler = (0, 0, math.radians(turn))
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    s = side_m / max(hi.x - lo.x, hi.y - lo.y)
    root.scale = (s, s, s)
    root.location = (-(lo.x + hi.x) / 2 * s, -(lo.y + hi.y) / 2 * s, -lo.z * s)
    w, d, h = (hi.x - lo.x) * s, (hi.y - lo.y) * s, (hi.z - lo.z) * s
    e = math.radians(ELEVATION)
    frame_w = w + 0.1
    frame_h = d * math.sin(e) + h * math.cos(e) + 0.1                # what the camera sees, metres
    cam = bpy.data.cameras.new("cam")
    cam.type = "ORTHO"
    cam.ortho_scale = max(frame_w, frame_h)
    co = bpy.data.objects.new("cam", cam)
    scene.collection.objects.link(co)
    target = Vector((0, 0, h / 2))
    co.location = target + Vector((0, -20 * math.cos(e), 20 * math.sin(e)))
    co.rotation_euler = (math.radians(90) - e, 0, 0)
    scene.camera = co
    scene.render.resolution_x = round(frame_w * RES)
    scene.render.resolution_y = round(frame_h * RES)
    scene.render.filepath = os.path.join(out, f"{name}.png")
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED {name}: {w:.2f} x {d:.2f} x {h:.2f} m -> {scene.render.resolution_x}x{scene.render.resolution_y}")


if __name__ == "__main__":
    out = sys.argv[sys.argv.index("--") + 1]
    os.makedirs(out, exist_ok=True)
    for name, (model, side, turn) in PIECES.items():
        render(name, model, side, turn, out)
