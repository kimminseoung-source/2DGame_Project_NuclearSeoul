"""Render pose guide sheets: a grey mannequin in the key poses of an action, for AI redrawing.

    blender -b -P tools/blender/pose_guides.py -- --anim-file <lib.glb>
        --map "swing=Sword_Regular_A,Sword_Regular_A_Rec@7-23" --frames-for swing=6,3 --pick swing=0,2,3,4,6,8
        --out assets/characters/guides

Same body, turn, root pin, camera tilt and frame choice as render_sprites.py, but rendered
large (each cell 6x the game cell) and smooth on a flat magenta background, so an image
model can follow the poses exactly ("redraw the attached character in these poses",
rotoscoping B in CHARACTER_WORKFLOW.md). The front (right) arm and leg are lighter than
the back ones so the model can tell them apart. One PNG per sheet: <out>/<sheet>_guide.png.
"""

import argparse
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_sprites as rs  # noqa: E402

SCALE = 6
MAGENTA = (1.0, 0.0, 1.0)


def paint_front_back(arm):
    """Front limbs light grey, back limbs dark grey, the rest mid grey (vertex colours)."""
    body = next(o for o in arm.children if rs.costumes.is_body(o))
    names = {g.index: g.name for g in body.vertex_groups}
    attr = body.data.color_attributes.new("guide", "FLOAT_COLOR", "POINT")
    for v in body.data.vertices:
        best = max(v.groups, key=lambda g: g.weight, default=None)
        bone = names.get(best.group, "") if best else ""
        if bone.endswith("_r"):
            c = (0.85, 0.85, 0.85)
        elif bone.endswith("_l"):
            c = (0.35, 0.35, 0.38)
        else:
            c = (0.6, 0.6, 0.62)
        attr.data[v.index].color = (*c, 1.0)
    body.data.color_attributes.active_color = attr
    for o in arm.children:
        if o.type == "MESH" and o is not body:
            o.hide_render = True                        # eyes and brows only add noise


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    p = argparse.ArgumentParser()
    p.add_argument("--anim-file", required=True)
    p.add_argument("--map", nargs="*", required=True)
    p.add_argument("--frames-for", nargs="*", default=[])
    p.add_argument("--pick", nargs="*", default=[], help="sheet=i,j,k: keep only these frames")
    p.add_argument("--tilt", type=float, default=20.0)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    rs.clear_scene()
    rs.import_model(os.path.join(rs.PROJECT_ROOT, rs.costumes.BODIES["male"]))
    rs.import_animations(os.path.abspath(a.anim_file))
    arm = rs.find_armature()
    rs.remove_loose_meshes(arm)
    for obj in bpy.data.objects:
        if obj.parent is None and obj.type in ("ARMATURE", "MESH", "EMPTY"):
            obj.rotation_mode = "XYZ"
            obj.rotation_euler[2] += math.radians(90)
    rs.pin_root(arm)
    paint_front_back(arm)
    scene = bpy.context.scene
    rs.setup_camera(scene, a.tilt)
    rs.setup_render(scene, None, painted=True)
    scene.render.resolution_x, scene.render.resolution_y = rs.CELL_W * SCALE, rs.CELL_H * SCALE
    scene.display.render_aa = "8"                       # smooth: a guide, not the final pixels
    scene.render.film_transparent = True
    counts = dict(pair.split("=") for pair in a.frames_for)
    picks = {k: [int(i) for i in v.split(",")] for k, v in (pair.split("=") for pair in a.pick)}
    out_dir = os.path.abspath(a.out)
    os.makedirs(out_dir, exist_ok=True)
    for entry in a.map:
        sheet_name, parts = rs.parse_map_entry(entry)
        sheet_counts = [int(c) for c in str(counts.get(sheet_name, 8)).split(",")]
        cells = []
        for i, (name, frame_range, blend) in enumerate(parts):
            action = bpy.data.actions[name]
            over = (bpy.data.actions[blend[0]], blend[1]) if blend else None
            cells += [(action, over, f) for f in rs.frames_of(action, sheet_counts[min(i, len(sheet_counts) - 1)], frame_range)]
        chosen = [cells[i] for i in picks.get(sheet_name, range(len(cells)))]
        w, h = rs.CELL_W * SCALE, rs.CELL_H * SCALE
        sheet = bpy.data.images.new(f"guide_{sheet_name}", w * len(chosen), h, alpha=True)
        px = [0.0] * (w * len(chosen) * h * 4)
        for index, (action, over, frame) in enumerate(chosen):
            rs.assign_action(arm, action, over)
            scene.frame_set(int(frame), subframe=frame - int(frame))
            path = os.path.join(out_dir, "_frames", f"{sheet_name}_{index}.png")
            scene.render.filepath = path
            bpy.ops.render.render(write_still=True)
            img = bpy.data.images.load(path)
            src = img.pixels[:]
            for y in range(h):
                for x in range(w):
                    s = (y * w + x) * 4
                    d = (y * w * len(chosen) + index * w + x) * 4
                    alpha = src[s + 3]
                    for c in range(3):                  # composite on magenta
                        px[d + c] = src[s + c] * alpha + MAGENTA[c] * (1 - alpha)
                    px[d + 3] = 1.0
            bpy.data.images.remove(img)
        sheet.pixels[:] = px
        sheet.filepath_raw = os.path.join(out_dir, f"{sheet_name}_guide.png")
        sheet.file_format = "PNG"
        sheet.save()
        print("saved", sheet.filepath_raw, len(chosen), "frames")


main()
