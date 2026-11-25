"""Research-driven D pilot: eight contact phases and uninterrupted moving-shot legs."""
import json
from pathlib import Path
from pistol_flow_look import PistolFlowLook

ART=Path(__file__).resolve().parents[1]/'assets/characters/previews/hero_pistol_gait_v4'

class PistolGaitLook(PistolFlowLook):
    ART_DIR=ART
    WALK_KEYS=8
    KEEP_WALK_DURING_RECOIL=True
    MODE='D'

    def __init__(self,base,refined=False):
        super().__init__(base)
        self.refined=refined
        import pico2d
        identity=ART/'identity'
        self.identity_sources={}
        for name in ('low','raise','aim','recoil','settle','hurt'):
            path=identity/f'{name}.png'
            self.images[name]=pico2d.load_image(str(path));self.identity_sources[name]=path
        for gait in ('walk','aim_walk'):
            for i in range(8):
                folder=identity/'refinement' if refined and i in (2,6) else identity
                key=f'{gait}_{i}';path=folder/f'{key}.png'
                self.images[key]=pico2d.load_image(str(path));self.identity_sources[key]=path
        self.identity_revision='FACE-R1'
        self.STRIDES=json.loads((ART/'gait_meta.json').read_text(encoding='utf-8'))['cycle_distance_world']

    def reset(self):
        super().reset()
        self.contacts=[]

    def advance(self,hero,dt,dx=0.,dy=0.):
        old=self.phase;self.contacts=[]
        super().advance(hero,dt,dx,dy)
        if not self.refined or dt<=0 or not self.sprite.startswith(('walk_','aim_walk_')):
            return
        before,after=int(old*2),int(self.phase*2)
        if before==after:return
        # A contact boundary is shared by both traversals; backwards does not turn
        # the far foot into the near foot. This is event timing, not a solved foot IK.
        backwards=dx*hero.facing<-.01
        key=(4 if before==1 else 0) if backwards else (4 if after==1 else 0)
        from settings import DOT
        self.contacts=[{'key':key,'x':hero.x+4/DOT*hero.facing,'y':hero.y+1/DOT}]

    def firing_muzzle(self,hero):
        # Game.fire runs before this frame's presentation update. A quick tap may still
        # have a low-ready sprite here, but the shot will display the raised gait.
        key=f'aim_walk_{int(self.phase*self.WALK_KEYS)%self.WALK_KEYS}' if hero.moving else 'recoil'
        return self.muzzle(hero,key)
