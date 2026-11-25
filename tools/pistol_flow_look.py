"""Coherent whole-body C trial. Presentation clocks advance in update, not in draw."""
from pathlib import Path
import json
import pico2d
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'assets/characters/previews/hero_pistol_flow_v3'


class PistolFlowLook:
    FRAME_TIME=.12
    keys={}
    ART_DIR=ART
    WALK_KEYS=4
    STRIDES={'walk':52.,'aim_walk':40.}
    KEEP_WALK_DURING_RECOIL=False
    MODE='C'

    def __init__(self,base):
        self.base=base
        names=('low','raise','aim','recoil','settle','hurt','fall','down')
        self.images={name:pico2d.load_image(str(ART/f'{name}.png')) for name in names}
        self.images.update({f'{g}_{i}':pico2d.load_image(str(self.ART_DIR/f'{g}_{i}.png'))
                            for g in ('walk','aim_walk') for i in range(self.WALK_KEYS)})
        self.muzzles=json.loads((ART/'muzzles.json').read_text(encoding='utf-8'))['points']
        if self.ART_DIR!=ART:
            self.muzzles.update(json.loads((self.ART_DIR/'muzzles.json').read_text(encoding='utf-8'))['points'])
        self.reset()

    def __getattr__(self,name):return getattr(self.base,name)
    def has(self,pose):return pose.startswith('ready_') or pose in ('idle','walk','run','sneak')
    def has_dir(self,pose,angle):return False
    def blade_lines(self,*args,**kwargs):return None

    def reset(self):
        self.phase=0.;self.raise_amount=0.;self.settling=0.;self.recoil=0.;self.linger=0.
        self.was_moving=False;self.seen_shot=None;self.sprite='low';self.last_state=(self.MODE,'low')

    def advance(self,hero,dt,dx=0.,dy=0.):
        from math import hypot
        if dt<=0:return
        self.recoil=max(0.,self.recoil-dt);self.linger=max(0.,self.linger-dt)
        self.settling=max(0.,self.settling-dt)
        shot=hero.slash if hero.slash and hero.slash['weapon'].get('shot') else None
        if shot is not None and shot.get('hit') and shot is not self.seen_shot:
            self.seen_shot=shot;self.recoil=.11;self.linger=.18
        aimed=hero.ready is not None or shot is not None or self.linger>0
        self.raise_amount=max(0.,min(1.,self.raise_amount+(1 if aimed else -1)*dt/.12))
        moving=hero.moving and hero.roll<=0 and hypot(dx,dy)>1e-6
        if moving:
            stride=self.STRIDES['aim_walk' if aimed else 'walk']
            direction=-1 if dx*hero.facing < -.01 else 1
            self.phase=(self.phase+direction*hypot(dx,dy)/stride)%1
        if self.was_moving and not moving and aimed:self.settling=.09
        self.was_moving=moving
        if hero.dead:self.sprite='fall' if hero.dead<.22 else 'down'
        elif hero.reeling>0:self.sprite='hurt'
        elif hero.roll>0:self.sprite='settle'
        elif moving and (self.recoil<=0 or self.KEEP_WALK_DURING_RECOIL):
            gait='aim_walk' if aimed else 'walk'
            self.sprite=f'{gait}_{int(self.phase*self.WALK_KEYS)%self.WALK_KEYS}'
        elif self.recoil>0:self.sprite='recoil'
        elif self.settling>0:self.sprite='settle'
        elif .12<self.raise_amount<.88:self.sprite='raise'
        else:self.sprite='aim' if self.raise_amount>=.88 else 'low'
        self.last_state=(self.MODE,self.sprite)

    def muzzle(self,hero,key):
        k=32/54
        px,py=self.muzzles.get(key,self.muzzles['aim'])
        return hero.x+(px-32)/k*hero.facing,hero.y+(58-py)/k

    def firing_muzzle(self,hero):
        key=self.sprite if self.KEEP_WALK_DURING_RECOIL and self.was_moving else 'recoil'
        return self.muzzle(hero,key)

    def draw(self,pose,time,x,feet_y,facing,contact=None,distance=None,alpha=1.,held=None,tint=None,angle=None,**kwargs):
        im=self.images[self.sprite];k=32/54
        im.opacify(alpha)
        try:im.composite_draw(0,'' if facing>0 else 'h',x,feet_y+26/k,64/k,64/k)
        finally:im.opacify(1.)
        return None
