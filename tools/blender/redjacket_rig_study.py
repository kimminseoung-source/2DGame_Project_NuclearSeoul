"""Reuse the existing MPFB rig and exact Walking time samples on a new costume copy.
Run in Blender on the ORIGINAL busan_hero.blend; never overwrite that original.
"""
import argparse
import json
import math
from pathlib import Path
import sys
import bpy
from mathutils import Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
import hero_sword_preview as factory
import mpfb_pose as motion


def inflate(obj, rig, groups, factor):
    for v in obj.data.vertices:
        weights=[(g.weight,obj.vertex_groups[g.group].name) for g in v.groups]
        name=max(weights,default=(0,''))[1]
        if not any(name.endswith(s) for s in groups) or name not in rig.data.bones:
            continue
        bone=rig.data.bones[name]
        # Rest coordinates of these saved MPFB meshes are the rig's coordinates.
        axis=(bone.tail_local-bone.head_local).normalized()
        centre=bone.head_local+axis*(v.co-bone.head_local).dot(axis)
        v.co=centre+(v.co-centre)*factor
    obj.data.update()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--spec',required=True);ap.add_argument('--out',required=True)
    ap.add_argument('--model-out',required=True)
    args=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
    spec=json.loads(Path(args.spec).resolve().read_text(encoding='utf-8'))
    root=Path(__file__).resolve().parents[2];out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)
    model=Path(args.model_out).resolve();model.parent.mkdir(parents=True,exist_ok=True)
    if model.exists():raise RuntimeError('Refusing to overwrite model study')
    rig,sword,grip,tip,mats=factory.build(spec)
    for o in list(bpy.data.objects):
        if 'backpack' in o.name.lower():bpy.data.objects.remove(o,do_unlink=True)
    body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.endswith('.body'))
    jacket=bpy.data.objects['hero_v1_work_jacket']
    # Bare hands, adult forearms, short rolled sleeves, no inherited black gloves.
    for poly in body.data.polygons:
        if poly.material_index==2:poly.material_index=0
    inflate(body,rig,('LeftArm','RightArm','LeftForeArm','RightForeArm'),1.28)
    inflate(jacket,rig,('LeftArm','RightArm'),1.14)
    # Uniform red shoulders rather than the first study's black shoulder blocks.
    factory.put_material(jacket,mats['jacket'])
    for o in bpy.data.objects:
        if o.type=='MESH' and 'pants' in o.name.lower():
            inflate(o,rig,('LeftUpLeg','RightUpLeg'),1.36)
            inflate(o,rig,('LeftLeg','RightLeg'),1.32)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(model))
    src=motion.import_source(str(root/'assets/source3d/mixamo/Walking.fbx'))
    f0,f1=[int(v) for v in src.animation_data.action.frame_range]
    frames=[round(f0+(f1-f0)*i/6) for i in range(6)]
    motion.retarget(src,rig,frames[0]);rig.rotation_euler[2]=math.radians(45)
    scene=bpy.context.scene;factory.setup_render(scene)
    scene.render.resolution_x=scene.render.resolution_y=64
    cam=factory.camera_for_body(scene,rig,spec['camera'])
    factory.calibrate_visible_body(scene,cam,sword,spec['camera'],out)
    ids={name:[(i+1)*13%241+8,(i+1)*71%241+8,(i+1)*113%241+8] for i,name in enumerate(mats)}
    (out/'ids.json').write_text(json.dumps(ids,indent=2),encoding='utf-8')
    records=[]
    for i,frame in enumerate(frames):
        rig.rotation_euler[2]=0;bpy.context.view_layer.update();motion.retarget(src,rig,frame)
        rig.rotation_euler[2]=math.radians(45);bpy.context.view_layer.update()
        records.append({'index':i,'source_frame':frame,'ground':factory.project(scene,cam,rig.matrix_world@Vector((0,0,0))),
                        'grip':factory.project(scene,cam,sword.matrix_world@grip),
                        'tip':factory.project(scene,cam,sword.matrix_world@tip)})
        for kind in ('id','light'):
            scene.display.render_aa='OFF';scene.display.shading.color_type='MATERIAL' if kind=='id' else 'SINGLE'
            scene.display.shading.light='FLAT' if kind=='id' else 'STUDIO'
            scene.display.shading.show_shadows=kind!='id';scene.display.shading.single_color=(1,1,1)
            if kind=='id':
                for name,mat in mats.items():mat.diffuse_color=(*[v/255 for v in ids[name]],1)
            for held in (False,True):
                sword.hide_render=not held
                dest=out/('held' if held else 'body')/kind;dest.mkdir(parents=True,exist_ok=True)
                scene.render.filepath=str(dest/f'{i}.png');bpy.ops.render.render(write_still=True)
    (out/'anchors.json').write_text(json.dumps({'animation':'Walking.fbx','samples_match':'mpfb_pose.main frames=6',
        'camera_fixed':True,'records':records},indent=2),encoding='utf-8')
    print('REDJACKET_RIG_STUDY_DONE',out,flush=True)


if __name__=='__main__':main()
