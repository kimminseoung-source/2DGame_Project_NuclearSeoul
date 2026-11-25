"""Drive the actual D game at 60Hz; audit moving shots and annotated foot trajectories."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'src'),str(Path(__file__).resolve().parent)]
from run_pistol_comparison import PistolComparison
from pistol_gait_look import ART
from check_pistol_flow import capture
from settings import WIDTH,HEIGHT,DOT
from infected import Zombie
import pico2d,sdl2,ui
from pico2d import pico2d as p2

def main():
    create=p2.SDL_CreateWindow
    p2.SDL_CreateWindow=lambda t,x,y,w,h,flags:create(t,x,y,w,h,(flags|sdl2.SDL_WINDOW_HIDDEN)&~sdl2.SDL_WINDOW_SHOWN)
    pico2d.open_canvas(WIDTH,HEIGHT,sync=False)
    checks=[];samples=[];frames=[]
    meta=json.loads((ART/'gait_meta.json').read_text(encoding='utf-8'))
    try:
        ui.enable_blending();g=PistolComparison();keys=(sdl2.Uint8*sdl2.SDL_NUM_SCANCODES)()
        g.zombies=[];g.used.update(a for a,_ in g.TEACH);g.dev.god=True
        assert g.hero_look.mode=='D'
        def tick():
            g.update(1/60,keys)
            return g.hero_look.active_flow
        for _ in range(3):tick()
        keys[sdl2.SDL_SCANCODE_D]=1
        observed=set()
        for i in range(100):
            f=tick();observed.add(f.sprite)
            k=int(f.sprite.rsplit('_',1)[1]);leg=meta['candidate_support'][k]
            px,py=meta[f'{leg}_boot'][k]
            samples.append({'tick':i,'key':k,'support':leg,'phase':f.phase,'root_x':g.hero.x,
                            'boot_native_world_x':g.hero.x*DOT+(px-32)*g.hero.facing})
        assert {f'walk_{i}' for i in range(8)}<=observed
        checks.append('all 8 normal walking phases selected by actual displacement')
        keys[sdl2.SDL_SCANCODE_D]=0
        for _ in range(12):tick()
        g.hero.start_ready()
        for _ in range(15):tick()
        assert g.hero_look.gait.sprite=='aim'
        keys[sdl2.SDL_SCANCODE_D]=1
        for _ in range(130):observed.add(tick().sprite)
        assert {f'aim_walk_{i}' for i in range(8)}<=observed
        checks.append('all 8 aim-walk phases and raised stationary aim reachable')
        # A visible shot while moving must never replace the legs with one stationary recoil pose.
        z=Zombie(g.zombie_look,g.hero.x+85,g.hero.y);g.zombies=[z];hp=z.health
        scale=g.zoom*DOT;sx=(z.x-g.cam[0])*scale;sy=HEIGHT-1-(z.y+22-g.cam[1])*scale
        g.aim=(sx,sy);ammo=g.ammo;g.release(sx,sy)
        during=[]
        for _ in range(35):
            f=tick()
            if f.recoil>0:
                during.append({'sprite':f.sprite,'phase':f.phase})
                assert f.sprite.startswith('aim_walk_'),during[-1]
        assert g.ammo==ammo-1 and z.health<hp and during
        assert len({round(s['phase'],5) for s in during})>1
        checks.append('real moving release hits and consumes 1 round; legs display and phase continue during recoil')
        keys[sdl2.SDL_SCANCODE_D]=0
        for _ in range(30):tick()
        phase=g.hero_look.gait.phase
        for _ in range(15):tick()
        assert g.hero_look.gait.phase==phase
        # Blocked displacement leaves phase untouched even if movement input is still requested.
        f=g.hero_look.gait;g.hero.moving=True;f.advance(g.hero,1/60,0,0)
        assert f.phase==phase
        checks.append('stationary / blocked displacement does not advance gait')
        g.hero.start_ready();g.aim=(0,HEIGHT//2);keys[sdl2.SDL_SCANCODE_D]=1
        p=f.phase;f=tick();assert g.hero.facing==-1 and f.phase!=p
        checks.append('aim facing can remain left while moving right; backward phase traversal works')
        keys[sdl2.SDL_SCANCODE_D]=0;g.hero.moving=False
        f.advance(g.hero,1/60,0,0);p=f.phase;f.advance(g.hero,0,10,0);assert f.phase==p
        checks.append('paused presentation clock does not advance gait')
        g.reset();g.zombies=[];tick();assert g.hero_look.gait.sprite=='low'
        # A tap from low-ready must fire from the raised pose that the shot displays,
        # even though Game.fire precedes this tick's sprite selection.
        keys[sdl2.SDL_SCANCODE_D]=1;tick()
        _,my=g.hero_look.gait.firing_muzzle(g.hero)
        assert my>g.hero.y+35
        z=Zombie(g.zombie_look,g.hero.x+85,g.hero.y);g.zombies=[z];hp=z.health
        sx=(z.x-g.cam[0])*scale;sy=HEIGHT-1-(z.y+22-g.cam[1])*scale
        g.aim=(sx,sy);ammo=g.ammo;g.release(sx,sy)
        for _ in range(35):
            x=g.hero.x;f=tick()
            if g.hero.moving and g.hero.x!=x:assert f.sprite!='recoil'
        assert g.ammo==ammo-1 and z.health<hp
        checks.append('moving quick tap from low-ready uses raised muzzle and retains walking')
        keys[sdl2.SDL_SCANCODE_D]=0;g.reset();g.zombies=[];tick()
        for expected in ('A','B','C','D'):
            before=(g.hero.x,g.hero.y,g.hero.hp,g.ammo)
            g.key_down(sdl2.SDLK_F8,keys)
            assert g.hero_look.mode==expected
            assert before==(g.hero.x,g.hero.y,g.hero.hp,g.ammo)
            tick()
        checks.append('A/B/C/D comparison preserves position, health and ammo; reset clears motion')
        # Record held-key drift separately from complete candidate-support runs.
        held=[];support=[];h=[];s=[]
        for r in samples:
            if h and r['key']!=h[-1]['key']:held.append(h);h=[]
            if s and r['support']!=s[-1]['support']:support.append(s);s=[]
            h.append(r);s.append(r)
        if h:held.append(h)
        if s:support.append(s)
        span=lambda rs:max(r['boot_native_world_x'] for r in rs)-min(r['boot_native_world_x'] for r in rs)
        foot={'method':meta['annotation_method'],'max_held_key_drift_native_px':max(map(span,held)),
              'max_candidate_support_spread_native_px':max(map(span,support)),
              'zero_foot_lock':False,'samples':samples,
              'limitation':'boot-centre approximation; candidate intervals and heel-to-toe movement require visual review'}
        (ART/'foot_audit.json').write_text(json.dumps(foot,indent=2),encoding='utf-8')
        # Matched runtime footage of old C and new D, actual camera/player motion on the same map.
        from PIL import Image,ImageDraw,ImageFont
        clips={}
        for mode in ('C','D'):
            g.reset();g.zombies=[];g.hero_look.mode=mode;g.used.update(a for a,_ in g.TEACH)
            clip=[];g.aim=(1000,HEIGHT//2)
            for i in range(240):
                keys[sdl2.SDL_SCANCODE_D]=int(10<=i<95 or 125<=i<210)
                if i==105:g.hero.start_ready()
                if i==155:g.hero.start_slash(g.hero.x+100,g.hero.y+22)
                tick()
                if i%3==0:
                    pico2d.clear_canvas();g.draw();im=capture()
                    # Camera viewport is zoomed; crop around the player's projected position.
                    x=round((g.hero.x-g.cam[0])*g.zoom*DOT);y=HEIGHT-round((g.hero.y+28-g.cam[1])*g.zoom*DOT)
                    crop=im.crop((x-135,y-150,x+135,y+150));clip.append(crop)
                    pico2d.update_canvas()
            clips[mode]=clip
        font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
        for a,b in zip(clips['C'],clips['D']):
            board=Image.new('RGB',(540,330),(27,30,32));board.paste(a,(0,30));board.paste(b,(270,30))
            d=ImageDraw.Draw(board);d.text((15,6),'C previous 4 keys',font=font,fill='white');d.text((285,6),'D new 8 phases',font=font,fill='white')
            frames.append(board)
        frames[0].save(ART/'game_comparison.gif',save_all=True,append_images=frames[1:],duration=50,loop=0)
        frames[50].save(ART/'game_comparison.png')
        result={'checks':checks,'observed':sorted(observed),'moving_shot':during,
                'max_held_key_drift_native_px':round(foot['max_held_key_drift_native_px'],3),
                'max_candidate_support_spread_native_px':round(foot['max_candidate_support_spread_native_px'],3),
                'scope':'side view mirrored; moving-body recoil not authored, muzzle flash/tracer/camera remain; no full 8-direction guarantee'}
        (ART/'runtime_check.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
    finally:pico2d.close_canvas()

if __name__=='__main__':main()
