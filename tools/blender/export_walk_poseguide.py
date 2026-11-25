"""Read original rig and animation; export actual projected joints without saving the blend."""
import argparse,json,math,sys
from pathlib import Path
import bpy
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0,str(Path(__file__).resolve().parent))
import mpfb_pose as motion
import hero_sword_preview as factory

root=Path(__file__).resolve().parents[2]
ap=argparse.ArgumentParser()
ap.add_argument('--out',default='assets/characters/previews/hero_poseguided_ai_v1')
ap.add_argument('--frames',type=int,default=6)
options=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
out=(root/options.out).resolve()
out.mkdir(parents=True,exist_ok=True)
rig=motion.target_rig()
src=motion.import_source(str(root/'assets/source3d/mixamo/Walking.fbx'))
f0,f1=[int(v) for v in src.animation_data.action.frame_range]
frames=[round(f0+(f1-f0)*i/options.frames) for i in range(options.frames)]
motion.retarget(src,rig,frames[0]);rig.rotation_euler[2]=math.radians(45)
scene=bpy.context.scene
scene.render.resolution_x=scene.render.resolution_y=64
cam=factory.camera_for_body(scene,rig,{'tilt_degrees':30,'sprite_canvas':64,'body_pixels':36,'feet_from_bottom':12})
names={'head':('Head','tail'),'neck':('Neck','head'),'chest':('Spine2','head'),'pelvis':('Hips','head'),
       'L_shoulder':('LeftArm','head'),'L_elbow':('LeftForeArm','head'),'L_wrist':('LeftHand','head'),
       'R_shoulder':('RightArm','head'),'R_elbow':('RightForeArm','head'),'R_wrist':('RightHand','head'),
       'L_hip':('LeftUpLeg','head'),'L_knee':('LeftLeg','head'),'L_ankle':('LeftFoot','head'),
       'L_toe':('LeftToeBase','tail'),'R_hip':('RightUpLeg','head'),'R_knee':('RightLeg','head'),
       'R_ankle':('RightFoot','head'),'R_toe':('RightToeBase','tail')}
records=[]
for frame in frames:
    rig.rotation_euler[2]=0;bpy.context.view_layer.update();motion.retarget(src,rig,frame)
    rig.rotation_euler[2]=math.radians(45);bpy.context.view_layer.update()
    joints={}
    for key,(bone,end) in names.items():
        p=rig.matrix_world@getattr(rig.pose.bones['mixamorig:'+bone],end)
        v=world_to_camera_view(scene,cam,p)
        joints[key]=[round(v.x*64,3),round((1-v.y)*64,3)]
    records.append({'frame':frame,'joints':joints})
(out/'pose_joints.json').write_text(json.dumps({'source':'original MPFB rig + Walking.fbx',
    'turn':45,'camera':'fixed orthographic 30-degree tilt','canvas':64,'records':records},indent=2),encoding='utf-8')
print('EXPORTED_POSE_JOINTS',out)
