"""Render the top-view area's ground and its wrecks in Blender (no downloads: procedural materials).

    "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b -P tools/blender/render_area.py

Writes into assets/area/:
- ground.png: the whole area seen straight from above, 1 px = 1 world px (src/area.py ROOM_W x
  ROOM_H): cracked, patched asphalt, faded lane marks, oil and dirt stains, a curb and pavement
  along the top and bottom edges, a few manhole covers and scattered debris.
- wreck_<i>.png: each block of area.BLOCKS as a picture (wrecked cars, a rubble heap), seen from
  the same 3/4 angle the game draws them at (the front face is 18 px tall), on a clear background.
Rendered with Cycles at twice the size and shrunk, then lightly posterised so it sits with the
pixel characters.
"""

import math
import os
import random
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
from area import BLOCKS, ROOM_H, ROOM_W  # noqa: E402

OUT = os.path.join(ROOT, "assets", "area")
U = 0.1                       # Blender units per world px (1000 px area = 100 units)
SS = 2                        # supersampling: render twice as big, shrink afterwards
FRONT = 18                    # px of a block's front face in the game's 3/4 view
random.seed(7)


# ------------------------------------------------------------------ scene setup
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "CUDA"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        scene.cycles.device = "GPU"
    except Exception:
        scene.cycles.device = "CPU"
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.new("sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.6, 0.65, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.25
    scene.world = world
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = 1.1
    sun.angle = math.radians(12)
    o = bpy.data.objects.new("sun", sun)
    o.rotation_euler = (math.radians(38), math.radians(-18), math.radians(30))
    scene.collection.objects.link(o)
    return scene


def node_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs[0], nt.nodes["Material Output"].inputs[0])
    return mat, nt, bsdf


def mix_colors(nt, factor, a, b):
    m = nt.nodes.new("ShaderNodeMix")
    m.data_type = "RGBA"
    nt.links.new(factor, m.inputs[0])
    if isinstance(a, tuple):
        m.inputs[6].default_value = a
    else:
        nt.links.new(a, m.inputs[6])
    if isinstance(b, tuple):
        m.inputs[7].default_value = b
    else:
        nt.links.new(b, m.inputs[7])
    return m.outputs[2]


def ramp(nt, value, stops):
    r = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(value, r.inputs[0])
    els = r.color_ramp.elements
    els[0].position, els[0].color = stops[0]
    els[1].position, els[1].color = stops[-1]
    for pos, col in stops[1:-1]:
        e = els.new(pos)
        e.color = col
    return r.outputs[0]


def noise(nt, scale, detail=6, rough=0.6, vector=None):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    if vector is not None:
        nt.links.new(vector, n.inputs["Vector"])
    return n


# ------------------------------------------------------------------ materials
def asphalt():
    mat, nt, bsdf = node_mat("asphalt")
    coord = nt.nodes.new("ShaderNodeTexCoord").outputs["Object"]
    grain = noise(nt, 6, 2, 0.8, coord).outputs["Fac"]                      # aggregate (~2 px grains)
    blotch = noise(nt, 0.12, 8, 0.65, coord).outputs["Fac"]                 # wear and dirt (~80 px patches)
    base = ramp(nt, blotch, [(0.3, (0.075, 0.075, 0.08, 1)), (0.55, (0.11, 0.11, 0.115, 1)),
                             (0.75, (0.085, 0.08, 0.075, 1))])
    speck = ramp(nt, grain, [(0.45, (0, 0, 0, 1)), (0.75, (1, 1, 1, 1))])
    col = mix_colors(nt, speck, base, (0.16, 0.16, 0.165, 1))
    # cracks: voronoi edges, kept only where a noise says so
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 0.09                              # crack cells ~110 px
    warp = noise(nt, 0.3, 4, 0.5, coord)
    add = nt.nodes.new("ShaderNodeVectorMath")
    add.operation = "ADD"
    nt.links.new(coord, add.inputs[0])
    sc = nt.nodes.new("ShaderNodeVectorMath")
    sc.operation = "SCALE"
    sc.inputs["Scale"].default_value = 3.0
    nt.links.new(warp.outputs["Color"], sc.inputs[0])
    nt.links.new(sc.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], vor.inputs["Vector"])
    crack = ramp(nt, vor.outputs["Distance"], [(0.0, (1, 1, 1, 1)), (0.035, (0, 0, 0, 1))])
    keep = ramp(nt, noise(nt, 0.06, 3, 0.5, coord).outputs["Fac"], [(0.45, (0, 0, 0, 1)), (0.55, (1, 1, 1, 1))])
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs[0].default_value = 1
    nt.links.new(crack, mul.inputs[6])
    nt.links.new(keep, mul.inputs[7])
    col = mix_colors(nt, mul.outputs[2], col, (0.025, 0.025, 0.028, 1))
    # oil and damp stains
    stain = ramp(nt, noise(nt, 0.25, 5, 0.6, coord).outputs["Fac"], [(0.64, (0, 0, 0, 1)), (0.7, (1, 1, 1, 1))])
    col = mix_colors(nt, stain, col, (0.04, 0.038, 0.035, 1))
    nt.links.new(col, bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.92
    return mat


def flat(name, color, rough=0.9, noise_scale=None, dark=None):
    mat, nt, bsdf = node_mat(name)
    if noise_scale:
        coord = nt.nodes.new("ShaderNodeTexCoord").outputs["Object"]
        f = noise(nt, noise_scale, 6, 0.6, coord).outputs["Fac"]
        col = mix_colors(nt, f, dark or tuple(c * 0.6 for c in color[:3]) + (1,), color)
        nt.links.new(col, bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = rough
    return mat


def rust_metal(name, paint):
    mat, nt, bsdf = node_mat(name)
    coord = nt.nodes.new("ShaderNodeTexCoord").outputs["Object"]
    f = ramp(nt, noise(nt, 0.8, 8, 0.7, coord).outputs["Fac"], [(0.4, (0, 0, 0, 1)), (0.6, (1, 1, 1, 1))])
    rust = mix_colors(nt, noise(nt, 4, 4, 0.6, coord).outputs["Fac"], (0.08, 0.035, 0.02, 1), (0.16, 0.07, 0.03, 1))
    col = mix_colors(nt, f, paint, rust)
    nt.links.new(col, bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.75
    bsdf.inputs["Metallic"].default_value = 0.3
    return mat


# ------------------------------------------------------------------ helpers
def box(name, x, y, z, sx, sy, sz, mat, bevel=0.0, rot=0.0):
    bpy.ops.mesh.primitive_cube_add(location=(x, y, z + sz / 2))
    o = bpy.context.active_object
    o.name = name
    o.scale = (sx / 2, sy / 2, sz / 2)
    o.rotation_euler[2] = rot
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        m = o.modifiers.new("bevel", "BEVEL")
        m.width = bevel
        m.segments = 2
    o.data.materials.append(mat)
    return o


def cylinder(name, x, y, z, r, depth, mat, axis="y"):
    rot = (math.radians(90), 0, 0) if axis == "y" else (0, math.radians(90), 0)
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=(x, y, z), rotation=rot, vertices=16)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    return o


def ortho_camera(scene, cx, cy, width, height, tilt_deg=0.0, cz=0.0):
    cam = bpy.data.cameras.new("cam")
    cam.type = "ORTHO"
    cam.ortho_scale = max(width, height)
    o = bpy.data.objects.new("cam", cam)
    scene.collection.objects.link(o)
    t = math.radians(tilt_deg)
    o.location = (cx, cy - 50 * math.sin(t), cz + 50 * math.cos(t))
    o.rotation_euler = (t, 0, 0)
    scene.camera = o
    scene.render.resolution_x = round(width / U) * SS if width >= height else round(width / height * height / U) * SS
    scene.render.resolution_y = round(height / U) * SS
    scene.render.resolution_x = round(width / U) * SS
    return o


def save(scene, name, size):
    path = os.path.join(OUT, name)
    scene.render.filepath = path
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(path)
    img.scale(*size)                               # shrink the supersampled render
    img.save_render(path)
    print("saved", name, size)


# ------------------------------------------------------------------ ground
def ground():
    scene = reset()
    W, H = ROOM_W * U, ROOM_H * U
    bpy.ops.mesh.primitive_plane_add(size=1, location=(W / 2, H / 2, 0))
    plane = bpy.context.active_object
    plane.scale = (W, H, 1)
    bpy.ops.object.transform_apply(scale=True)
    plane.data.materials.append(asphalt())
    paint = flat("lane_paint", (0.32, 0.27, 0.13, 1), 0.85, 2.0, (0.1, 0.09, 0.07, 1))
    for lane in range(80, ROOM_H, 160):                 # faded dashed lane marks (same rows as before)
        for x0 in range(0, ROOM_W, 60):
            if random.random() < 0.15:
                continue                                 # worn away
            box("lane", (x0 + 15) * U, (lane + 1) * U, 0.0, 3.0, 0.3, 0.004, paint)
    curb = flat("curb", (0.24, 0.23, 0.22, 1), 0.9, 1.5)
    walk = flat("pavement", (0.16, 0.155, 0.15, 1), 0.95, 0.8, (0.08, 0.078, 0.075, 1))
    for y0, y1 in ((0, 26), (ROOM_H - 26, ROOM_H)):  # pavement strips along the top and bottom
        box("pavement", W / 2, (y0 + y1) / 2 * U, 0.0, W, (y1 - y0) * U, 0.03, walk)
        cy = (y1 if y0 == 0 else y0) * U
        box("curb", W / 2, cy, 0.0, W, 0.35, 0.06, curb)
    for x in range(40, ROOM_W, 80):                     # pavement slab joints
        for y0 in (0, ROOM_H - 26):
            box("joint", x * U, (y0 + 13) * U, 0.031, 0.06, 2.6, 0.001, flat("joint", (0.08, 0.08, 0.08, 1)))
    iron = flat("manhole", (0.09, 0.085, 0.08, 1), 0.6, 4)
    for mx, my in ((430, 250), (820, 470), (180, 140)):
        cylinder("manhole", mx * U, my * U, 0.002, 1.3, 0.01, iron, axis="z")
    debris = [flat("concrete", (0.2, 0.195, 0.185, 1), 0.95, 3), flat("brick", (0.18, 0.085, 0.055, 1), 0.9, 3),
              flat("glass", (0.14, 0.17, 0.17, 1), 0.2), flat("trash", (0.13, 0.12, 0.08, 1), 0.9, 3)]
    for _ in range(160):                                # small debris everywhere, more near edges
        x, y = random.uniform(10, ROOM_W - 10), random.uniform(10, ROOM_H - 10)
        s = random.uniform(0.15, 0.6)
        box("bit", x * U, y * U, 0.0, s, s * random.uniform(0.5, 1.2), s * 0.4, random.choice(debris),
            rot=random.uniform(0, 3.14))
    ortho_camera(scene, W / 2, H / 2, W, H)
    scene.render.film_transparent = False
    save(scene, "ground.png", (ROOM_W, ROOM_H))


# ------------------------------------------------------------------ wrecks
def car(w, d, paint):
    """A burnt-out car filling w x d units on the ground, long side along x."""
    body = rust_metal("car_paint", paint)
    glass = flat("broken_glass", (0.05, 0.06, 0.07, 1), 0.15)
    tyre = flat("tyre", (0.03, 0.03, 0.03, 1), 0.9)
    box("body", 0, 0, 0.3, w * 0.98, d * 0.92, 0.75, body, bevel=0.15)          # lower body
    box("hood", w * 0.33, 0, 1.0, w * 0.3, d * 0.86, 0.12, body, bevel=0.08)     # bonnet, a bit lower
    box("trunk", -w * 0.38, 0, 1.0, w * 0.2, d * 0.86, 0.2, body, bevel=0.08)
    box("cabin_glass", -w * 0.04, 0, 1.0, w * 0.5, d * 0.84, 0.7, glass, bevel=0.12)   # dark windows all round
    box("roof", -w * 0.06, 0, 1.68, w * 0.36, d * 0.7, 0.1, body, bevel=0.05)
    box("dent", -w * 0.1, d * 0.1, 1.74, w * 0.12, d * 0.25, 0.06, rust_metal("dent", (0.05, 0.04, 0.035, 1)))
    for sy in (-1, 1):                                                              # dead headlights
        box("lamp", w * 0.49, sy * d * 0.3, 0.75, 0.08, d * 0.16, 0.18, glass)
    for wx in (-w * 0.32, w * 0.32):
        for wy in (-d * 0.42, d * 0.42):
            if random.random() < 0.8:                    # a wheel or two is gone
                cylinder("wheel", wx, wy, 0.35, 0.35, 0.25, tyre)


def rubble(w, d):
    mats = [flat("concrete", (0.2, 0.195, 0.185, 1), 0.95, 2), flat("brick", (0.18, 0.085, 0.055, 1), 0.9, 2),
            flat("rebar", (0.18, 0.09, 0.05, 1), 0.6)]
    for _ in range(26):
        s = random.uniform(0.4, 1.6)
        box("chunk", random.uniform(-w / 2.6, w / 2.6), random.uniform(-d / 2.6, d / 2.6), random.uniform(0, 0.8),
            s, s * random.uniform(0.5, 1.1), s * random.uniform(0.3, 0.8), random.choice(mats[:2]),
            rot=random.uniform(0, 3.14))
    for _ in range(5):
        cylinder("rebar", random.uniform(-w / 3, w / 3), random.uniform(-d / 3, d / 3), 1.2, 0.04,
                 random.uniform(1.5, 2.5), mats[2], axis="x")


def wrecks():
    paints = [(0.07, 0.09, 0.11, 1), (0.14, 0.135, 0.12, 1), (0.11, 0.04, 0.035, 1)]
    for i, (l, b, r, t) in enumerate(BLOCKS):
        scene = reset()
        w, d = (r - l) * U, (t - b) * U
        if w >= d * 1.6:
            car(w, d, paints[i % len(paints)])
        else:
            rubble(w, d)
        # the game draws a block from its ground bottom up to its top + FRONT px: frame that
        # with a camera tilted so the front face shows FRONT px tall
        frame_h = (t - b + FRONT) * U
        tilt = math.degrees(math.atan2(FRONT, t - b)) * 1.6
        cam = ortho_camera(scene, 0, 0, w + 0.4, frame_h + 0.4, tilt, cz=0.75)   # aim at mid-height
        cam.data.ortho_scale = max(w + 0.4, frame_h + 0.4)
        scene.render.resolution_x = round((w + 0.4) / U) * SS
        scene.render.resolution_y = round((frame_h + 0.4) / U) * SS
        save(scene, f"wreck_{i}.png", (round((w + 0.4) / U), round((frame_h + 0.4) / U)))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    ground()
    wrecks()
