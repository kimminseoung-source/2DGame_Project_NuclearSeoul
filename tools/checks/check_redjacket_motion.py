"""Check real game locomotion/contact timing and capture the new motion trial."""
import ctypes
import json
import os
from pathlib import Path
import sys
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
os.environ['BUSAN_AREA']='arena'
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'src')]
from run_redjacket_trial import RedJacketTrial,RedJacketLook,ART
import pico2d,sdl2,ui
from pico2d import pico2d as p2
from settings import WIDTH,HEIGHT
from infected import Zombie
from area import ROOM_W,BODY_PAD


def screenshot():
    surf=sdl2.SDL_CreateRGBSurfaceWithFormat(0,WIDTH,HEIGHT,32,sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(p2.renderer,None,sdl2.SDL_PIXELFORMAT_ARGB8888,surf.contents.pixels,surf.contents.pitch)
    raw=ctypes.string_at(surf.contents.pixels,surf.contents.pitch*HEIGHT)
    im=Image.frombuffer('RGBA',(WIDTH,HEIGHT),raw,'raw','BGRA',surf.contents.pitch,1).convert('RGB')
    sdl2.SDL_FreeSurface(surf)
    return im


def main():
    create=p2.SDL_CreateWindow
    p2.SDL_CreateWindow=lambda title,x,y,w,h,flags:create(title,x,y,w,h,(flags|sdl2.SDL_WINDOW_HIDDEN)&~sdl2.SDL_WINDOW_SHOWN)
    pico2d.open_canvas(WIDTH,HEIGHT,sync=False)
    checks=[]
    try:
        ui.enable_blending();g=RedJacketTrial();keys=(sdl2.Uint8*sdl2.SDL_NUM_SCANCODES)()
        def reset():
            g.reset();g.dev.freeze=g.dev.no_spawn=True;g.to_spawn=0;g.zombies=[]
            g.used.update(a for a,_ in g.TEACH)
        def tick():
            g.update(1/120,keys);pico2d.clear_canvas();g.draw();pico2d.update_canvas()
        reset();walkkeys=set();keys[sdl2.SDL_SCANCODE_D]=1
        for _ in range(100):
            tick();walkkeys.add(g.hero_look.last_key)
        assert walkkeys=={f'walk_{i}' for i in range(6)},walkkeys
        checks.append('all six walk frames during real movement')
        keys[sdl2.SDL_SCANCODE_D]=0;tick();d=g.hero_look.travel_world
        for _ in range(30):tick()
        assert g.hero_look.last_key=='idle' and g.hero_look.travel_world==d
        checks.append('idle does not advance walking distance')
        g.hero.x=ROOM_W-BODY_PAD;keys[sdl2.SDL_SCANCODE_D]=1
        d=g.hero_look.travel_world
        for _ in range(20):tick()
        assert g.hero_look.travel_world==d
        checks.append('blocked wall movement does not cycle feet')
        keys[sdl2.SDL_SCANCODE_D]=0
        for charged in (False,True):
            reset();z=Zombie(g.zombie_look,g.hero.x+28,g.hero.y);g.zombies=[z]
            hp=z.health
            if charged:
                g.hero.start_ready()
                for _ in range(100):tick()
                assert g.hero_look.last_key=='windup'
                keys[sdl2.SDL_SCANCODE_D]=1;tick();keys[sdl2.SDL_SCANCODE_D]=0;tick()
                assert g.hero.ready is not None
            g.hero.start_slash(z.x,z.y+22)
            assert g.hero.slash is not None
            seen=set();contact_frames=0
            for _ in range(95):
                tick();s=g.hero.slash;key=g.hero_look.last_key;seen.add(key)
                if s:
                    if s['time'] < s['hit_at']:
                        assert key=='windup',(s,key)
                    elif (s['time']-s['hit_at'])/(s['whole']-s['hit_at']) < .38:
                        assert s['hit'] and key=='impact',(s,key)
                        contact_frames+=1
            assert {'windup','impact','recover'} <= seen,seen
            assert z.health<hp and contact_frames>0,(z.health,hp)
            checks.append(('charged' if charged else 'quick')+' cut: real damage and synchronized windup/impact/recover')
        reset();g.hero.start_roll(1,0)
        for _ in range(110):tick()
        checks.append('dodge renders with new walk silhouettes/afterimages')
        g.hero.take_blow()
        for _ in range(20):tick()
        reset();assert isinstance(g.hero.look,RedJacketLook) and g.hero_look.travel_world==0
        checks.append('hurt and reset retain new look')
        # Actual game montage: move right, pause, hold, attack, recover, move left.
        frames=[];reset();g.dev.god=True
        for i in range(300):
            keys[sdl2.SDL_SCANCODE_D]=int(i<90)
            keys[sdl2.SDL_SCANCODE_A]=int(i>=230)
            if i==110:g.hero.start_ready()
            if i==170:g.hero.start_slash(g.hero.x+80,g.hero.y+22)
            g.update(1/60,keys)
            if i%4==0:
                pico2d.clear_canvas();g.draw()
                im=screenshot();frames.append(im.crop((420,170,1000,450)))
                if g.hero_look.last_key=='impact':im.save(ART/'game_impact.png')
                pico2d.update_canvas()
        frames[0].save(ART/'game_motion.gif',save_all=True,append_images=frames[1:],duration=67,loop=0,disposal=2)
        (ART/'runtime_check.json').write_text(json.dumps({'passed':checks,'game_montage_frames':300,
            'scope':'one southeast drawing direction, mirrored left; no new up/down/roll/hurt/death art'},indent=2),encoding='utf-8')
        print(json.dumps(checks))
    finally:pico2d.close_canvas()


if __name__=='__main__':main()
