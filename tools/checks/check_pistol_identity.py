"""Verify head reuse in actual D loaders and reproduce the prior 601-text cache boundary."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'src'),str(Path(__file__).resolve().parent)]
from PIL import Image,ImageDraw,ImageFont
from run_pistol_comparison import PistolComparison
from pistol_gait_look import ART
from check_pistol_flow import capture
from settings import WIDTH,HEIGHT,DOT
from pico2d import pico2d as p2
import pico2d,sdl2,ui,pixel_ui as px
OUT=ART/'identity'

def main():
    checked=[];meta=json.loads((OUT/'validation.json').read_text(encoding='utf-8'))
    head=Image.open(OUT/'head.png').convert('RGBA');digest=hashlib.sha256(head.tobytes()).hexdigest()
    assert digest==meta['shared_head_sha256']
    for r in meta['records']:
        im=Image.open(OUT/(r['key']+'.png')).convert('RGBA');x0,y0=r['head_top_left']
        recovered=Image.new('RGBA',head.size)
        for y in range(head.height):
            for x in range(head.width):
                if head.getpixel((x,y))[3]:recovered.putpixel((x,y),im.getpixel((x+x0,y+y0)))
        assert recovered.tobytes()==head.tobytes(),r['key']
        original=Image.open(ROOT/r['source']).convert('RGBA')
        assert original.crop((0,32,64,64)).tobytes()==im.crop((0,32,64,64)).tobytes()
    checked.append('26 upright base/refined pose assets share identical 10x9 head pixels without resampling; rows32+ unchanged')
    create=p2.SDL_CreateWindow
    p2.SDL_CreateWindow=lambda t,x,y,w,h,flags:create(t,x,y,w,h,(flags|sdl2.SDL_WINDOW_HIDDEN)&~sdl2.SDL_WINDOW_SHOWN)
    pico2d.open_canvas(WIDTH,HEIGHT,sync=False)
    try:
        ui.enable_blending();g=PistolComparison();g.zombies=[];g.used.update(a for a,_ in g.TEACH)
        keys=(sdl2.Uint8*sdl2.SDL_NUM_SCANCODES)()
        assert g.hero_look.mode=='D' and g.hero_look.gait.identity_revision=='FACE-R1'
        for look in (g.hero_look.gait,g.hero_look.gait_before):
            assert len(look.identity_sources)==22
            assert all(p.is_file() and p.is_relative_to(OUT) for p in look.identity_sources.values())
        checked.append('both F10 branches actually load shared-head state/movement assets; C original images stay separate')
        # Original crash occurred when a new item pushed the cache to 601 and clear()
        # deleted the very key being returned. Exercise real SDL/TTF and texture creation.
        px._texts.clear()
        for i in range(650):
            texture=px._text_image(f'IDENTITY_CACHE_{i:04}',(222,216,198),False)
            assert texture.w>0 and texture.h>0
        assert len(px._texts)==600
        last=px._text_image('IDENTITY_CACHE_0649',(222,216,198),False)
        assert last is px._texts[('IDENTITY_CACHE_0649',(222,216,198),False)]
        checked.append('650 real SDL/TTF cache insertions stay bounded at600 and retain the newest texture')
        clips=[]
        for refined in (False,True):
            g.hero_look.refined=refined;g.reset();g.zombies=[];g.used.update(a for a,_ in g.TEACH)
            g.hero_look.refined=refined;clip=[];g.aim=(1000,HEIGHT//2)
            for i in range(210):
                keys[sdl2.SDL_SCANCODE_D]=int(20<=i<75 or 130<=i<190)
                if i==95:g.hero.start_ready()
                g.update(1/60,keys)
                if i%3==0:
                    pico2d.clear_canvas();g.draw();im=capture();pico2d.update_canvas()
                    if refined and i==0:im.save(OUT/'build_FACE-R1.png')
                    x=round((g.hero.x-g.cam[0])*g.zoom*DOT);y=HEIGHT-round((g.hero.y+28-g.cam[1])*g.zoom*DOT)
                    clip.append(im.crop((x-125,y-135,x+125,y+135)))
            clips.append(clip)
        font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16);frames=[]
        for a,b in zip(*clips):
            im=Image.new('RGB',(500,300),(27,30,32));im.paste(a,(0,30));im.paste(b,(250,30))
            d=ImageDraw.Draw(im);d.text((12,7),'FACE-R1 / knee before',font=font,fill='white');d.text((262,7),'FACE-R1 / knee after',font=font,fill='white');frames.append(im)
        frames[0].save(OUT/'game_transitions.gif',save_all=True,append_images=frames[1:],duration=50,loop=0)
        checked.append('actual idle/walk/aim/aim-walk transitions render after cache pressure; FACE-R1 build screenshot saved')
        result={'checks':checked,'head_sha256':digest,'verified_pose_assets':len(meta['records']),
                'cache_limit':600,'cache_insertions':650,'scope':'same-view upright head consistency, not angled death redraw or body-wide design equivalence'}
        (OUT/'runtime_check.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
    finally:pico2d.close_canvas()

if __name__=='__main__':main()
