"""F8 switches A/B/C/D: static, spliced, four-key, eight-phase contact study.
A has no authored walk cycle; C is a one-direction pilot, not an eight-direction release.
"""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from run_shared_pistol_trial import SharedPistolLook,SharedPistolTrial
import pico2d,sdl2,pixel_ui as px
from pistol_flow_look import PistolFlowLook
from pistol_gait_look import PistolGaitLook
from settings import WIDTH


class ComparisonLook(SharedPistolLook):
    def __init__(self,base):
        super().__init__(base)
        self.mode='D'
        self.flow=PistolFlowLook(base)
        self.gait=PistolGaitLook(base,refined=True)
        self.gait_before=PistolGaitLook(base)
        self.refined=True
        folder=ROOT/'assets/characters/previews/hero_pistol_v1'
        self.wide={name:pico2d.load_image(str(folder/f'{name}_36px.png')) for name in ('low_ready','aim')}

    def draw(self,pose,time,x,feet_y,facing,contact=None,distance=None,alpha=1.,held=None,tint=None,angle=None,**kwargs):
        if self.mode in ('C','D'):
            result=self.active_flow.draw(pose,time,x,feet_y,facing,contact,distance,alpha,held,tint,angle,**kwargs)
            self.last_state=self.active_flow.last_state
            return result
        if self.mode=='B':
            return super().draw(pose,time,x,feet_y,facing,contact,distance,alpha,held,tint,angle,**kwargs)
        state='aim' if pose.startswith('ready_') or pose=='stab' else 'low_ready'
        self.last_state=('A_'+state,None)
        im=self.wide[state];k=32/54
        im.opacify(alpha)
        try:im.composite_draw(0,'' if facing>0 else 'h',x,feet_y+26/k,64/k,64/k)
        finally:im.opacify(1.)
        return None

    @property
    def active_flow(self):
        if self.mode=='D':return self.gait if self.refined else self.gait_before
        return self.flow


class PistolComparison(SharedPistolTrial):
    def __init__(self):
        super().__init__()
        self.hero_look=ComparisonLook(self.hero_look.base)
        self.hero.look=self.hero_look

    def reset(self):
        super().reset()
        self.dev.freeze=True        # move/aim freely first; F9 releases the same enemies
        self.message='권총 동작 비교 · F8 A/B/C/D · F9 적 정지/재개'
        if isinstance(self.hero_look,ComparisonLook):
            self.hero_look.flow.reset();self.hero_look.gait.reset();self.hero_look.gait_before.reset()
        self.foot_contacts=0

    def key_down(self,key,keys):
        if key==sdl2.SDLK_F10 and self.hero_look.mode=='D':
            old=self.hero_look.active_flow
            self.hero_look.refined=not self.hero_look.refined
            new=self.hero_look.active_flow
            for attr in ('phase','raise_amount','settling','recoil','linger','was_moving','seen_shot','sprite','last_state'):
                setattr(new,attr,getattr(old,attr))
            new.contacts=[]
            return
        if key==sdl2.SDLK_F8:
            modes=('A','B','C','D')
            self.hero_look.mode=modes[(modes.index(self.hero_look.mode)+1)%len(modes)]
            return
        if key==sdl2.SDLK_F9:
            self.dev.freeze=not self.dev.freeze
            return
        super().key_down(key,keys)

    def update(self,dt,keys):
        before=self.hero;x,y,t=before.x,before.y,before.time
        before.walk_while_shooting=self.hero_look.mode=='D'
        before.distance_step_audio=not(self.hero_look.mode=='D' and self.hero_look.refined)
        super().update(dt,keys)
        if self.hero is before:
            if self.hero_look.mode in ('C','D') and self.aim[0] is not None and (self.hero.ready is not None or self.hero.slash):
                ax,_=self.mouse_world(*self.aim)
                self.hero.facing=1 if ax>=self.hero.x else -1
            self.hero_look.active_flow.advance(self.hero,max(0.,self.hero.time-t),self.hero.x-x,self.hero.y-y)
            if self.hero_look.mode=='D' and self.hero_look.refined:
                from math import atan2
                from dodge_fx import Dust
                for contact in self.hero_look.active_flow.contacts:
                    self.foot_contacts+=1
                    self.sounds.play('step',.08 if self.hero.sneaking else .20)
                    if not self.hero.sneaking:
                        self.effects.append(Dust(contact['x'],contact['y'],atan2(self.hero.y-y,self.hero.x-x),kind='step'))

    def fire(self,slash,shot):
        if self.hero_look.mode not in ('C','D'):return super().fire(slash,shot)
        # Same pistol damage/ammo/noise rules, but tracer and hit ray originate at the new muzzle.
        from math import atan2,cos,sin
        import area
        from settings import CHEST
        from vision_cone import ray_hit
        from slash_fx import Tracer,Spark
        self.ammo-=1
        if self.aim[0] is not None:
            ax,_=self.mouse_world(*self.aim);self.hero.facing=1 if ax>=self.hero.x else -1
        ox,oy=self.hero_look.active_flow.firing_muzzle(self.hero)
        angle=slash['angle']
        if self.aim[0] is not None:
            ax,ay=self.mouse_world(*self.aim);angle=atan2(ay-oy,ax-ox)
        ux,uy=cos(angle),sin(angle);reach=shot['range']
        limit=min(reach,ray_hit(ox,oy,ux,uy,area.sight_blocks(ox-reach,oy-reach,ox+reach,oy+reach)))
        struck,at=None,limit
        for z in self.zombies:
            if not z.alive:continue
            for up in ((6,) if z.prone else (8,CHEST,40)):
                dx,dy=z.x-ox,z.y+up-oy;t=dx*ux+dy*uy
                if 0<t<at and abs(dx*uy-dy*ux)<=shot['width']:struck,at=z,t
        self.effects.append(Tracer(ox,oy,ox+ux*at,oy+uy*at))
        self.effects.append(Spark(ox,oy))
        self.sounds.play('shot',1.);self.jolt('light')
        if self.senses:self.make_noise(shot['noise'])
        return struck

    def draw_aim(self,cx,cy):
        if self.hero_look.mode not in ('C','D'):return super().draw_aim(cx,cy)
        hero=self.hero;flow=self.hero_look.active_flow
        if self.aim[0] is None or hero.dead or self.left or self.bag_open or hero.slash or flow.raise_amount<.88:return
        from math import atan2,cos,sin
        import area
        from settings import DOT
        from vision_cone import ray_hit
        sx,sy=flow.muzzle(hero,flow.sprite);tx,ty=self.mouse_world(*self.aim)
        ang=atan2(ty-sy,tx-sx);ux,uy=cos(ang),sin(ang)
        length=hero.weapon['shot']['range']
        far=min(length,ray_hit(sx,sy,ux,uy,area.sight_blocks(sx-length,sy-length,sx+length,sy+length)))
        colour=(196,170,92) if hero.charge>=1 else (176,172,158) if self.ammo else (120,60,54)
        for distance in range(8,int(far),3*self.DOT_GAP):
            x=round((sx+ux*distance-cx)*DOT)/DOT;y=round((sy+uy*distance-cy)*DOT)/DOT
            pico2d.draw_rectangle(x,y,x+1.99/DOT,y+1.99/DOT,*colour,filled=True)
        target=self.aimed(*self.aim) if hero.charge>=1 else None
        if target is not None:
            import weapons,ui
            z,part=target
            low,high,half=(0,14,weapons.PART_HALF_WIDTH*2) if z.prone else next(
                (lo,hi,weapons.PART_HALF_WIDTH) for p,lo,hi in weapons.PARTS if p==part)
            left,right=z.x-half-cx,z.x+half-cx;bottom,top=z.y+low-cy,z.y+min(high,56)-cy
            for x0,y0,dx,dy in ((left,top,1,-1),(right,top,-1,-1),(left,bottom,1,1),(right,bottom,-1,1)):
                pico2d.draw_rectangle(min(x0,x0+5*dx),y0-1,max(x0,x0+5*dx),y0,*colour,filled=True)
                pico2d.draw_rectangle(x0,min(y0,y0+5*dy),x0+1,max(y0,y0+5*dy),*colour,filled=True)
            ui.world_text_center(z.x-cx,z.y+(24 if z.prone else 62)-cy,weapons.PART_NAMES[part],colour,12)

    def draw(self):
        super().draw()
        mode=self.hero_look.mode
        text={'A':'A · 처음 넓은 자세 / 걷기 그림 없음',
              'B':'B · 좁힌 자세 / 공통 다리 8장',
              'C':'C · 이전 전신 4장 보행 / 사격 중 다리 멈춤',
              'D':'D · 접지 8단계 / 이동 사격 중 다리 유지'}[mode]
        px.text((WIDTH-18)/px.K,14,text,(245,223,164),anchor='r')
        px.text((WIDTH-18)/px.K,30,'F8 A/B/C/D 전환 · F9 적 '+('정지 중' if self.dev.freeze else '활동 중'),
                (210,215,205),anchor='r')
        if mode=='D':
            px.text((WIDTH-18)/px.K,46,'F10 무릎·접지 리듬 '+('수정 후' if self.hero_look.refined else '수정 전'),(210,215,205),anchor='r')
        px.text((WIDTH-18)/px.K,62,'BUILD FACE-R1 · '+('D 얼굴 공유' if mode=='D' else mode+' 이전 비교'),(235,235,205),bold=True,anchor='r')


if __name__=='__main__':
    import main
    main.Game=PistolComparison
    main.main()
