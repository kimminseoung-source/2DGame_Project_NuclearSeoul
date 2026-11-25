"""Playable narrow-stance pistol study with genuinely shared animated lower layers.
Existing gun rules are retained; this is not an eight-direction gun animation release.
"""
import json
from math import hypot,pi
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from run_spitter_trial import SpitterTrial
import pico2d
import weapons
from character_look import draw_weapon

ART=ROOT/'assets/characters/previews/hero_pistol_shared_v2'


class SharedPistolLook:
    FRAME_TIME=.1
    keys={}

    def __init__(self,base):
        self.base=base
        self.upper={name:pico2d.load_image(str(ART/f'upper_{name}.png')) for name in ('low','aim')}
        self.idle=pico2d.load_image(str(ART/'lower_idle.png'))
        self.legs=[pico2d.load_image(str(ART/f'lower_walk_{i}.png')) for i in range(8)]
        self.pistol=pico2d.load_image(str(ART/'pistol.png'))
        self.anchors=json.loads((ART/'layers.json').read_text(encoding='utf-8'))['anchors']
        self.travel_world=0.
        self.last_state=('low',None)

    def __getattr__(self,name):return getattr(self.base,name)

    def has(self,pose):return pose.startswith('ready_') or pose in ('idle','walk','run','sneak')

    def has_dir(self,pose,angle):return False

    def blade_lines(self,*args,**kwargs):return None

    def draw(self,pose,time,x,feet_y,facing,contact=None,distance=None,alpha=1.,held=None,tint=None,angle=None,**kwargs):
        aimed=pose.startswith('ready_') or pose=='stab'
        moving=pose in ('run','walk','sneak') or (pose.startswith('ready_') and not pose.startswith('ready_stand_'))
        state='aim' if aimed else 'low'
        frame=int(self.travel_world/64*8)%8 if moving else None
        self.last_state=(state,frame)
        lower=self.idle if frame is None else self.legs[frame]
        k=32/54;flip='' if facing>0 else 'h';cy=feet_y+26/k
        def draw_layer(im):
            im.opacify(alpha)
            try:im.composite_draw(0,flip,x,cy,64/k,64/k)
            finally:im.opacify(1.)
        draw_layer(lower)
        point=self.anchors[state]['grip']
        gx=x+(point[0]-32)/k*facing;gy=feet_y+(58-point[1])/k
        ang=-self.anchors[state]['angle_clockwise']*pi/180
        if facing<0:ang=pi-ang
        self.pistol.opacify(alpha)
        try:draw_weapon(self.pistol,gx,gy,ang,k)
        finally:self.pistol.opacify(1.)
        draw_layer(self.upper[state])
        return gx,gy


class SharedPistolTrial(SpitterTrial):
    def __init__(self):
        super().__init__()
        self.hero_look=SharedPistolLook(self.hero_look)
        self.hero.look=self.hero_look

    def reset(self):
        super().reset()
        self.hero.weapon=weapons.WEAPONS['pistol']
        self.ammo=60           # trial supply, not a change to normal pistol magazine rules
        self.ground_weapons=[]
        self.message='권총 자세 시험 · R 다시 시작'
        if isinstance(self.hero_look,SharedPistolLook):self.hero_look.travel_world=0.

    def update(self,dt,keys):
        before=self.hero;x,y=before.x,before.y
        super().update(dt,keys)
        if self.hero is before and self.hero.moving:
            self.hero_look.travel_world+=hypot(self.hero.x-x,self.hero.y-y)


if __name__=='__main__':
    import main
    main.Game=SharedPistolTrial
    main.main()
