"""Read-only sprite inventory and key-reference audit; write a dated evidence snapshot.
Counts describe available files, not proof that an action is selected or looks correct.
"""
import json
from pathlib import Path
import sys
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
DIRS=('east','north-east','north','north-west','west','south-west','south','south-east')


def inventory(name):
    folder=ROOT/'assets/characters'/name
    stills=[];anims={};sheets={};named=set()
    meta_path=folder/'look.json'
    meta=json.loads(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}
    cell=meta.get('_size',{}).get('cell',[96,64])
    for p in folder.rglob('*.png'):
        if p.parent.name=='rotations' and p.stem in DIRS:
            stills.append(p.stem)
        elif p.parent.name in DIRS:
            action='walk' if 'walk' in p.parent.parent.name.lower() else p.parent.parent.name.lower()
            anims.setdefault(action,{}).setdefault(p.parent.name,[]).append(p.stem)
            named.add((action,p.parent.name,p.stem))
        elif p.parent==folder:
            with Image.open(p) as im:
                sheets[p.stem]={'size':list(im.size),'cell':cell,'horizontal_frames':im.width//cell[0]}
    keys_path=folder/'keyframes.json'
    keys=json.loads(keys_path.read_text(encoding='utf-8')) if keys_path.exists() else {}
    missing=[];refs=0
    def check(table,label):
        nonlocal refs
        for d,spec in table.items():
            if d not in DIRS or not isinstance(spec,dict):continue
            for stage in ('windup','hit','recover'):
                step=spec.get(stage)
                if not step:continue
                key=(step.get('anim',spec.get('anim')),step.get('dir',d),str(step['frame']))
                refs+=1
                if key not in named:missing.append({'table':label,'direction':d,'stage':stage,'key':key})
    for key,table in keys.items():
        if key=='variants':
            for variant,sub in table.items():check(sub,'variants.'+variant)
        elif isinstance(table,dict):check(table,key)
    summary={action:{'directions':len(bydir),'frames_by_direction':{d:len(files) for d,files in bydir.items()}}
             for action,bydir in sorted(anims.items())}
    return {'folder':str(folder),'stills':sorted(set(stills)),'animations':summary,'sheets':sheets,
            'default_attack_variant':keys.get('default_variant'),'aim_styles':keys.get('aim_styles',[]),
            'key_refs_checked':refs,'missing_key_refs':missing}


def main():
    result={'date':'2026-11-23','scope':'file availability and direct loader probes; Hero.draw/has/feature flags further constrain reachable states; not a full playthrough or visual quality test',
            'families':{n:inventory(n) for n in ('hero_3d','hero_px40','hero_dot')}}
    result['new_preview_files']={p.name:len(list(p.rglob('*.png'))) for p in (ROOT/'assets/characters/previews').iterdir()
                                 if p.is_dir() and p.name.startswith(('hero_redjacket','hero_poseguided','hero_pistol'))}
    if '--runtime' in sys.argv:
        result['loader_routes']=loader_routes()
    dest=ROOT/'docs/planning/HERO_MOTION_INVENTORY.json'
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    for name,entry in result['families'].items():
        print(name,'stills',len(entry['stills']),'key_refs',entry['key_refs_checked'],'missing',len(entry['missing_key_refs']))
        for action,a in entry['animations'].items():
            print(' ',action,a['directions'],'dirs; frames',sorted(set(a['frames_by_direction'].values())))
        if entry['sheets']:print(' SHEETS', {n:e['horizontal_frames'] for n,e in entry['sheets'].items()})
    print('SAVED',dest)


def loader_routes():
    """Load the real look classes and resolve their selection/fallback paths, in a hidden window."""
    from math import pi
    sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
    import pico2d,sdl2
    from pico2d import pico2d as p2
    from character_look import SheetLook,DirLook,FALLBACK
    from run_redjacket_trial import RedJacketLook
    create=p2.SDL_CreateWindow
    p2.SDL_CreateWindow=lambda t,x,y,w,h,f:create(t,x,y,w,h,(f|sdl2.SDL_WINDOW_HIDDEN)&~sdl2.SDL_WINDOW_SHOWN)
    pico2d.open_canvas(128,128,sync=False)
    probes={'idle':('idle',.2,None),'walk':('run',.2,None),'sneak':('sneak',.2,None),
            'sneak_idle':('sneak_idle',.2,None),'aim_chop':('ready_stand_chop',.2,None),
            'aimstep_chop':('ready_chop',.2,None),'hurt':('hurt',.5,None),'down':('down',.8,None),
            'pickup':('pickup',.5,None),'push':('push',.5,None),'roll':('roll',.5,None),
            'roll_spin':('roll_spin',.5,None),'stomp':('stomp',.5,.5),
            'chop_prepare':('chop',.2,.5),'chop_hit':('chop',.51,.5),'chop_recover':('chop',.9,.5),
            'pistol_shot_stab':('stab',.51,.15)}
    results={}
    try:
        base=SheetLook(ROOT/'assets/characters/hero_dot')
        for family in ('hero_3d','hero_px40'):
            look=DirLook(ROOT/'assets/characters'/family,base);routes={}
            for name,(pose,t,contact) in probes.items():
                bydir={}
                for i,d in enumerate(DIRS):
                    keyed=look.key_pose(pose,t,contact,i*pi/4)
                    pic=None if keyed else look.picture(pose,t,i*pi/4,contact)
                    if keyed:route='key_attack:'+keyed[3]
                    elif pic:route='picture:'+pic[2]+':'+pic[3]
                    else:
                        fallback=pose if pose in base.sheets else FALLBACK.get(pose,('idle',None))[0]
                        route='base_sheet:'+(fallback if fallback in base.sheets else 'idle')
                    bydir[d]=route
                routes[name]=bydir
            routes['gun_has_dedicated_stand_aim']=look.has('ready_stand_stab')
            routes['gun_has_dedicated_moving_aim']=look.has('ready_stab')
            results[family]=routes
        results['new_melee_trial_adapter']={name:RedJacketLook.frame_for(pose,t,contact,24.)
                                      for name,(pose,t,contact) in probes.items()}
        results['new_effective_dodge']='has_dir=False; Hero.draw requests run, so walk frames/afterimages are used, not the direct unsupported roll probe above'
        from run_pistol_comparison import ComparisonLook
        comparison=ComparisonLook(base)
        results['current_pistol_comparison']={'default':comparison.mode,'modes':['A','B','C','D'],
            'C_images':sorted(comparison.flow.images),'runtime_check':'assets/characters/previews/hero_pistol_flow_v3/runtime_check.json',
            'foot_audit':'assets/characters/previews/hero_pistol_flow_v3/foot_audit.json',
            'D_images':sorted(comparison.gait.images),
            'D_refined_default':comparison.refined,
            'D_identity_revision':comparison.gait.identity_revision,
            'D_identity_sources':{name:str(path.relative_to(ROOT)) for name,path in comparison.gait.identity_sources.items()},
            'D_identity_check':'assets/characters/previews/hero_pistol_gait_v4/identity/runtime_check.json',
            'D_refinement_record':'assets/characters/previews/hero_pistol_gait_v4/refinement/README.md',
            'D_runtime_check':'assets/characters/previews/hero_pistol_gait_v4/runtime_check.json',
            'D_foot_audit':'assets/characters/previews/hero_pistol_gait_v4/foot_audit.json'}
        print('LOADER_ROUTES_PROBED',len(probes),'poses x 8 directions x 2 old families; new adapter also checked')
        return results
    finally:pico2d.close_canvas()


if __name__=='__main__':main()
