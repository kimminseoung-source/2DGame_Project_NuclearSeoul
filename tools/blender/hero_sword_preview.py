"""Non-destructive sword hero idle study. Run inside Blender on the old MPFB .blend.

All authored geometry is saved to a separate .blend. Existing models and game assets are
never overwritten. Uses the existing Mixamo retargeter, fixed orthographic camera, material
ID/light passes and explicit grip/tip/ground projections for later pixel processing.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view


def arguments():
    p = argparse.ArgumentParser()
    p.add_argument('--spec', required=True)
    p.add_argument('--model-out', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--anim', required=True)
    return p.parse_args(sys.argv[sys.argv.index('--') + 1:])


def material(name, color):
    m = bpy.data.materials.new('hero_v1_' + name)
    m.diffuse_color = (*[c / 255 for c in color], 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = m.diffuse_color
    bsdf.inputs['Roughness'].default_value = 0.85
    m['part'] = name
    return m


def put_material(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.material_index = 0


def attach(obj, rig, bone):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = 'BONE'
    obj.parent_bone = 'mixamorig:' + bone
    bpy.context.view_layer.update()
    obj.matrix_world = world


def box(name, at, size, mat, rig, bone='Spine2', bevel=0.012):
    bpy.ops.mesh.primitive_cube_add(size=1, location=at)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    put_material(o, mat)
    if bevel:
        mod = o.modifiers.new('soft fabric corners', 'BEVEL')
        mod.width, mod.segments = bevel, 2
    attach(o, rig, bone)
    return o


def mesh_piece(name, vertices, faces, mat, rig, bone='Spine2'):
    me = bpy.data.meshes.new(name)
    me.from_pydata(vertices, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    put_material(o, mat)
    attach(o, rig, bone)
    return o


def strap(name, points, width, mat, rig):
    verts = []
    for x, y, z in points:
        verts.extend([(x - width / 2, y, z), (x + width / 2, y, z)])
    faces = [(i, i + 1, i + 3, i + 2) for i in range(0, len(verts) - 2, 2)]
    o = mesh_piece(name, verts, faces, mat, rig)
    solid = o.modifiers.new('strap thickness', 'SOLIDIFY')
    solid.thickness = 0.004
    return o


def dominant(obj, poly):
    scores = {}
    for idx in poly.vertices:
        for group in obj.data.vertices[idx].groups:
            n = obj.vertex_groups[group.group].name
            scores[n] = scores.get(n, 0) + group.weight
    return max(scores, key=scores.get, default='')


def build(spec):
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    # Keep bone weights and rest pose. Slight overall breadth stays within the art guide.
    rig.scale.x *= spec['body']['width_scale']
    rig['head_scale'] = spec['body']['head_scale']
    rig.pose.bones['mixamorig:Head'].scale = (rig['head_scale'],) * 3
    mats = {k: material(k, v[1]) for k, v in spec['palette'].items()}
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    body = next(o for o in meshes if o.name.endswith('.body'))
    jacket = next(o for o in meshes if 'sweater' in o.name)
    jacket.name = 'hero_v1_work_jacket'
    # Reuse the fitted/skinned garment, open the front and roll back the sleeves.
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(jacket.data)
    remove = []
    for face in bm.faces:
        c = face.calc_center_median()
        centre_open = abs(c.x) < 0.045 and c.y < -0.06 and 0.84 < c.z < 1.31
        sleeve_end = abs(c.x) > 0.345 and c.z < 1.13
        if centre_open or sleeve_end:
            remove.append(face)
    bmesh.ops.delete(bm, geom=remove, context='FACES')
    bm.to_mesh(jacket.data)
    bm.free()
    put_material(jacket, mats['jacket'])
    jacket.data.materials.append(mats['strap'])
    for poly in jacket.data.polygons:
        c = poly.center
        if abs(c.x) > 0.155 and c.z > 1.24:
            poly.material_index = 1
    put_material(body, mats['skin'])
    body.data.materials.append(mats['shirt'])
    body.data.materials.append(mats['gloves'])
    for poly in body.data.polygons:
        bone = dominant(body, poly)
        if any(s in bone for s in ('Spine', 'Shoulder')):
            poly.material_index = 1
        elif bone.endswith('Hand'):
            poly.material_index = 2
    for o in meshes:
        if o in (body, jacket):
            continue
        n = o.name.lower()
        part = 'jeans' if 'pants' in n else 'boots' if 'shoes' in n else 'eyes' if 'low-poly' in n else 'hair'
        put_material(o, mats[part])
    # Fabric geometry: small pockets and short lapels, no bedroll or surplus gear.
    for sign in (-1, 1):
        x = sign * 0.115
        box('jacket_chest_pocket', (x, -0.176, 1.155), (0.085, 0.025, 0.09), mats['jacket'], rig)
        box('jacket_pocket_flap', (x, -0.192, 1.197), (0.09, 0.013, 0.022), mats['jacket'], rig)
        verts = [(sign * 0.028, -0.17, 1.28), (sign * 0.09, -0.145, 1.31),
                 (sign * 0.12, -0.18, 1.24), (sign * 0.052, -0.20, 1.20)]
        mesh_piece('jacket_lapel', verts, [(0, 1, 2, 3)], mats['jacket'], rig)
    pack = spec['backpack']
    box('compact_backpack', (0, 0.175, 1.135),
        (pack['width'], pack['depth'], pack['height']), mats['backpack'], rig, bevel=0.035)
    box('backpack_front_pocket', (0, 0.26, 1.08), (0.23, 0.045, 0.13), mats['backpack'], rig, bevel=0.014)
    box('backpack_top_flap', (0, 0.265, 1.245), (0.235, 0.025, 0.10), mats['backpack'], rig, bevel=0.01)
    for sign in (-1, 1):
        x = sign * 0.125
        strap('backpack_shoulder_strap', [(x, 0.19, 1.25), (x, 0.03, 1.295),
                                        (x, -0.135, 1.28), (x, -0.20, 1.21),
                                        (x, -0.18, 1.015)], 0.028, mats['strap'], rig)
        box('backpack_buckle', (sign * 0.074, 0.294, 1.155),
            (0.019, 0.013, 0.035), mats['grip'], rig, bevel=0.002)
    # Cloth wrap around the left forearm, in the rig's rest coordinates.
    bone = rig.data.bones['mixamorig:LeftForeArm']
    at = rig.matrix_world @ (bone.head_local.lerp(bone.tail_local, 0.80))
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.039, depth=0.07, location=at)
    wrap = bpy.context.object
    wrap.name = 'left_forearm_cloth'
    direction = (rig.matrix_world.to_3x3() @ (bone.tail_local - bone.head_local)).normalized()
    wrap.rotation_euler = Vector((0, 0, 1)).rotation_difference(direction).to_euler()
    put_material(wrap, mats['wrap'])
    attach(wrap, rig, 'LeftForeArm')
    sword, grip_local, tip_local = make_sword(spec['sword'], mats, rig)
    bpy.context.view_layer.update()
    return rig, sword, grip_local, tip_local, mats


def make_sword(spec, mats, rig):
    length, width = spec['blade_length'], spec['blade_width']
    # A shallow diamond cross-section with slight sweep: sword, not broad machete.
    verts = []
    for z, centre, half in [(0.025, 0, width / 2), (length * 0.72, 0.012, width / 2),
                            (length * 0.94, 0.026, width * 0.35)]:
        verts.extend([(centre - half, 0, z), (centre, -0.006, z),
                      (centre + half, 0, z), (centre, 0.006, z)])
    verts.append((0.043, 0, length))
    faces = []
    for start in (0, 4):
        faces.extend([(start + j, start + (j + 1) % 4,
                       start + 4 + (j + 1) % 4, start + 4 + j) for j in range(4)])
    faces.extend([(8 + j, 8 + (j + 1) % 4, 12) for j in range(4)])
    me = bpy.data.meshes.new('sword_blade')
    me.from_pydata(verts, [], faces)
    me.materials.append(mats['steel']); me.materials.append(mats['edge'])
    for poly in me.polygons:
        poly.material_index = 1 if poly.index % 4 == 1 else 0
    blade = bpy.data.objects.new('sword_blade', me)
    bpy.context.collection.objects.link(blade)
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.018, depth=spec['grip_length'],
                                      location=(0, 0, -spec['grip_length'] / 2))
    handle = bpy.context.object; handle.name = 'sword_grip'; put_material(handle, mats['grip'])
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=1, location=(0, 0, 0))
    guard = bpy.context.object; guard.name = 'sword_guard'
    guard.scale = (spec['guard_width'] / 2, 0.028, 0.008)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    put_material(guard, mats['steel'])
    bpy.ops.object.select_all(action='DESELECT')
    for o in (blade, handle, guard): o.select_set(True)
    bpy.context.view_layer.objects.active = blade
    bpy.ops.object.join()
    sword = bpy.context.object; sword.name = 'hero_sword_separate'
    # The palm lies below the guard, so the right hand wraps the handle.
    grip_local = Vector((0, 0, -0.075))
    desired = Vector((0.40, -0.90, 0.05)).normalized()
    rotation = (Vector((0, 0, 1)).rotation_difference(desired).to_matrix().to_4x4()
                @ Matrix.Rotation(math.radians(70), 4, 'Z'))
    hand = rig.matrix_world @ rig.data.bones['mixamorig:RightHand'].matrix_local
    grip_world = hand @ Vector((0, 0.08, 0))
    sword.matrix_world = Matrix.Translation(grip_world - rotation.to_3x3() @ grip_local) @ rotation
    attach(sword, rig, 'RightHand')
    return sword, grip_local, Vector((0.043, 0, length))


def camera_for_body(scene, rig, spec):
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render
              and o.name != 'hero_sword_separate']
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in meshes:
        ev = o.evaluated_get(dg); me = ev.to_mesh()
        pts.extend(o.matrix_world @ v.co for v in me.vertices)
        ev.to_mesh_clear()
    cam = bpy.data.objects.new('hero_preview_camera', bpy.data.cameras.new('hero_preview_camera'))
    cam.data.type = 'ORTHO'
    scene.collection.objects.link(cam); scene.camera = cam
    tilt = math.radians(spec['tilt_degrees'])
    cam.rotation_euler = (math.pi / 2 - tilt, 0, 0)
    cam.location = (0, -10 * math.cos(tilt), 10 * math.sin(tilt))
    bpy.context.view_layer.update()
    inverse = cam.matrix_world.inverted()
    ys = [(inverse @ p).y for p in pts]
    # A 34px body leaves one outline pixel each side for a measured ~36px sprite.
    pixel_world = (max(ys) - min(ys)) / (spec['body_pixels'] - 2)
    cam.data.ortho_scale = pixel_world * spec['sprite_canvas']
    up = cam.matrix_world.to_quaternion() @ Vector((0, 1, 0))
    desired_min = -cam.data.ortho_scale / 2 + spec['feet_from_bottom'] * pixel_world
    cam.location += up * (min(ys) - desired_min)
    bpy.context.view_layer.update()
    return cam


def setup_render(scene):
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.film_transparent = True
    scene.render.resolution_percentage = 100
    scene.render.use_compositing = False
    scene.render.use_sequencer = False
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.studiolight_rotate_z = math.radians(-35)
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = False
    scene.display.shading.show_object_outline = False
    scene.view_settings.view_transform = 'Standard'


def project(scene, camera, point):
    v = world_to_camera_view(scene, camera, point)
    return [round(v.x * scene.render.resolution_x - .5, 3),
            round((1 - v.y) * scene.render.resolution_y - .5, 3)]


def calibrate_visible_body(scene, cam, sword, spec, out):
    """Fit the first visible idle once, not loose/hidden mesh vertices or each frame."""
    sword.hide_render = True
    scene.display.shading.light = 'STUDIO'; scene.display.shading.color_type = 'MATERIAL'
    scene.display.render_aa = 'OFF'
    size = spec['sprite_canvas']; target = spec['body_pixels'] - 2
    samples = []
    for attempt in range(3):
        path = out / f'calibration_{attempt}.png'
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(str(path), check_existing=False)
        raw = list(im.pixels)
        occupied = [(x, y) for y in range(size) for x in range(size)
                    if raw[(y * size + x) * 4 + 3] > .5]
        bpy.data.images.remove(im)
        if not occupied: raise RuntimeError('Empty calibration render')
        low = min(y for x,y in occupied); high = max(y for x,y in occupied) + 1
        height = high - low
        samples.append({'attempt':attempt, 'height':height, 'bottom_from_canvas':low})
        if abs(height-target) <= 1 and abs(low-spec['feet_from_bottom']) <= 1:
            break
        old_pixel = cam.data.ortho_scale / size
        new_pixel = old_pixel * height / target
        centre = (low + high) / 2
        wanted = spec['feet_from_bottom'] + target / 2
        up = cam.matrix_world.to_quaternion() @ Vector((0,1,0))
        cam.location += up * ((centre-size/2)*old_pixel - (wanted-size/2)*new_pixel)
        cam.data.ortho_scale = new_pixel * size
        bpy.context.view_layer.update()
    (out/'calibration.json').write_text(json.dumps(samples,indent=2),encoding='utf-8')


def main():
    a = arguments(); spec = json.loads(Path(a.spec).resolve().read_text(encoding='utf-8'))
    # Blender resolves relative render filepaths differently after saving a .blend.
    # Resolve every input/output before the save so previews stay in the workspace.
    animation = Path(a.anim).resolve()
    out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    model_out = Path(a.model_out).resolve(); model_out.parent.mkdir(parents=True, exist_ok=True)
    if model_out.exists(): raise RuntimeError('Refusing to overwrite authored model')
    rig, sword, grip, tip, mats = build(spec)
    bpy.ops.wm.save_as_mainfile(filepath=str(model_out.resolve()))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import mpfb_pose as motion
    source = motion.import_source(str(animation))
    f0, f1 = source.animation_data.action.frame_range
    # Calibrate the same camera from the first posed body, including its actual head scale.
    motion.retarget(source, rig, int(f0))
    rig.rotation_euler[2] = math.radians(45)
    bpy.context.view_layer.update()
    scene = bpy.context.scene; setup_render(scene)
    scene.render.resolution_x = scene.render.resolution_y = spec['camera']['sprite_canvas']
    cam = camera_for_body(scene, rig, spec['camera'])
    calibrate_visible_body(scene, cam, sword, spec['camera'], out)
    original_colors = {m.name: tuple(m.diffuse_color) for m in mats.values()}
    id_colors = {name: [(i + 1) * 13 % 241 + 8, (i + 1) * 71 % 241 + 8,
                        (i + 1) * 113 % 241 + 8] for i, name in enumerate(mats)}
    (out / 'ids.json').write_text(json.dumps(id_colors, indent=2), encoding='utf-8')
    frames = [int(f0), int(f0 + (f1 - f0) * .50)]
    records = []
    for i, frame in enumerate(frames):
        rig.rotation_euler[2] = 0; bpy.context.view_layer.update()
        motion.retarget(source, rig, frame)
        rig.rotation_euler[2] = math.radians(45); bpy.context.view_layer.update()
        scene.render.resolution_x = scene.render.resolution_y = 64
        record = {'frame': frame, 'grip': project(scene, cam, sword.matrix_world @ grip),
                  'tip': project(scene, cam, sword.matrix_world @ tip),
                  'ground': project(scene, cam, rig.matrix_world @ Vector((0, 0, 0)))}
        records.append(record)
        for render_pass in ('id', 'light'):
            if render_pass == 'id':
                scene.display.shading.light = 'FLAT'; scene.display.shading.color_type = 'MATERIAL'
                scene.display.shading.show_shadows = False
                for name, m in mats.items(): m.diffuse_color = (*[c / 255 for c in id_colors[name]], 1)
            else:
                scene.display.shading.light = 'STUDIO'; scene.display.shading.color_type = 'SINGLE'
                scene.display.shading.show_shadows = True
                scene.display.shading.single_color = (1, 1, 1)
            for with_sword in (False, True):
                sword.hide_render = not with_sword
                path = out / ('held' if with_sword else 'body') / render_pass
                path.mkdir(parents=True, exist_ok=True)
                scene.display.render_aa = 'OFF'
                scene.render.filepath = str(path / f'{i}.png')
                bpy.ops.render.render(write_still=True)
    for m in mats.values(): m.diffuse_color = original_colors[m.name]
    scene.display.shading.light = 'STUDIO'; scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.show_shadows = True
    scene.display.render_aa = '16'; scene.render.resolution_x = scene.render.resolution_y = 512
    sword.hide_render = False
    for turn, name in ((45, 'front'), (135, 'back')):
        rig.rotation_euler[2] = math.radians(turn); bpy.context.view_layer.update()
        scene.render.filepath = str(out / f'model_{name}.png')
        bpy.ops.render.render(write_still=True)
    (out / 'anchors.json').write_text(json.dumps({'canvas': [64,64], 'records': records,
        'note': 'Fixed camera; no per-frame crop or rescaling. Ground is projected model origin.'}, indent=2), encoding='utf-8')
    print('HERO_PREVIEW_COMPLETE', str(out), flush=True)


if __name__ == '__main__': main()
