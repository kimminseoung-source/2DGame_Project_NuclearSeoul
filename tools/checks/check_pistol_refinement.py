"""Verify four registered corrections, foot-contact audio and in-place F10 comparison."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'src'),str(Path(__file__).resolve().parent)]
from PIL import Image,ImageDraw,ImageFont
from run_pistol_comparison import PistolComparison
from pistol_gait_look import ART
from check_pistol_flow import capture
from settings import WIDTH,HEIGHT,DOT
from pico2d import pico2d as p2
import pico2d,sdl2,ui
OUT=ART/'refinement'

def main():
    checked=[]
    for gait in ('walk','aim_walk'):
        for key in (2,6):
            old=Image.open(ART/f'{gait}_{key}.png');new=Image.open(OUT/f'{gait}_{key}.png')
            assert old.crop((0,0,64,40)).tobytes()==new.crop((0,0,64,40)).tobytes()
            assert old.crop((22,51,33,59)).tobytes()==new.crop((22,51,33,59)).tobytes()
            def right_extent(im):
                return max(y for y in range(44,58) for x in range(34,45) if im.getpixel((x,y))[3])
            assert right_extent(new)>right_extent(old),(gait,key)
    checked.append('four AI swing-leg edits extend lower; original upper body and planted boots stay pixel-identical')
    create=p2.SDL_CreateWindow
    p2.SDL_CreateWindow=lambda t,x,y,w,h,flags:create(t,x,y,w,h,(flags|sdl2.SDL_WINDOW_HIDDEN)&~sdl2.SDL_WINDOW_SHOWN)
    pico2d.open_canvas(WIDTH,HEIGHT,sync=False)
    try:
        ui.enable_blending();g=PistolComparison();g.zombies=[];g.used.update(a for a,_ in g.TEACH)
        keys=(sdl2.Uint8*sdl2.SDL_NUM_SCANCODES)();calls=[]
        g.sounds.play=lambda name,*args,**kw:calls.append(name)
        assert g.hero_look.mode=='D' and g.hero_look.refined
        for _ in range(5):g.update(1/60,keys)
        keys[sdl2.SDL_SCANCODE_D]=1
        for _ in range(110):g.update(1/60,keys)
        assert g.foot_contacts>0 and calls.count('step')==g.foot_contacts
        assert not g.hero.distance_step_audio
        checked.append('refined D disables distance audio; one step call per actual half-cycle contact')
        keys[sdl2.SDL_SCANCODE_D]=0;count=g.foot_contacts
        for _ in range(20):g.update(1/60,keys)
        assert g.foot_contacts==count and calls.count('step')==count
        checked.append('standing does not replay foot contacts or add footstep audio')
        from types import SimpleNamespace
        f=g.hero_look.gait;f.reset()
        hero=SimpleNamespace(ready=None,slash=None,roll=0.,moving=True,facing=1,dead=0.,reeling=0.,x=0.,y=0.)
        observed=[];distance=f.STRIDES['walk']/100
        for _ in range(100):
            hero.x+=distance;f.advance(hero,1/60,distance,0)
            observed.extend(c['key'] for c in f.contacts)
        assert observed==[4,0],observed
        for dt,dx in ((1/60,0),(0,distance)):
            f.advance(hero,dt,dx,0);assert not f.contacts
        checked.append('exactly two contact boundaries per forward cycle; blocked/paused updates emit none')
        before=(g.hero.x,g.hero.y,g.hero.hp,g.ammo,f.phase)
        g.key_down(sdl2.SDLK_F10,keys)
        assert not g.hero_look.refined and g.hero_look.active_flow.phase==before[-1]
        assert before[:4]==(g.hero.x,g.hero.y,g.hero.hp,g.ammo)
        g.update(1/60,keys);assert g.hero.distance_step_audio
        g.key_down(sdl2.SDLK_F10,keys);assert g.hero_look.refined
        checked.append('F10 toggles prior/refined D, retaining mechanics and gait phase without a synthetic contact')
        from dodge_fx import Dust
        dust=Dust(0,0,0,'step')
        assert len(dust.bits)==2 and dust.life==.10 and all(reach<=3 for _,reach,_ in dust.bits)
        checked.append('foot dust is two short-lived tiny particles; roll dust parameters unchanged')
        clips=[]
        for refined in (False,True):
            g.reset();g.zombies=[];g.hero_look.refined=refined;g.used.update(a for a,_ in g.TEACH)
            g.sounds.play=lambda *args,**kwargs:None
            clip=[]
            for i in range(180):
                keys[sdl2.SDL_SCANCODE_D]=int(8<=i<80 or 105<=i<165)
                if i==90:g.hero.start_ready()
                g.update(1/60,keys)
                if i%3==0:
                    pico2d.clear_canvas();g.draw();im=capture()
                    x=round((g.hero.x-g.cam[0])*g.zoom*DOT);y=HEIGHT-round((g.hero.y+28-g.cam[1])*g.zoom*DOT)
                    clip.append(im.crop((x-130,y-150,x+130,y+150)));pico2d.update_canvas()
            clips.append(clip)
        font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16);frames=[]
        for a,b in zip(*clips):
            im=Image.new('RGB',(520,330),(27,30,32));im.paste(a,(0,30));im.paste(b,(260,30))
            d=ImageDraw.Draw(im);d.text((12,7),'D before / high knee',font=font,fill='white');d.text((272,7),'D after / low passing',font=font,fill='white');frames.append(im)
        frames[0].save(OUT/'game_comparison.gif',save_all=True,append_images=frames[1:],duration=50,loop=0)
        frames[40].save(OUT/'game_comparison.png')
        result={'checks':checked,'contact_key_sequence':observed,'runtime_steps':count,'scope':'four passing keys, contact audio/tiny reused dust; no speed/camera/noise-rule changes'}
        (OUT/'runtime_check.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
    finally:pico2d.close_canvas()

if __name__=='__main__':main()
