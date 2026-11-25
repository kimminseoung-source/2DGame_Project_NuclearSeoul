"""Real game state transitions, shot synchronization, reset, and a frame-by-frame foot audit."""
import ctypes,json,sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'src')]
from run_pistol_comparison import PistolComparison
from pistol_flow_look import ART
import pico2d,sdl2,ui
from pico2d import pico2d as p2
from infected import Zombie
from settings import WIDTH,HEIGHT,DOT


def capture():
    surf=sdl2.SDL_CreateRGBSurfaceWithFormat(0,WIDTH,HEIGHT,32,sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(p2.renderer,None,sdl2.SDL_PIXELFORMAT_ARGB8888,surf.contents.pixels,surf.contents.pitch)
    raw=ctypes.string_at(surf.contents.pixels,surf.contents.pitch*HEIGHT)
    im=Image.frombuffer('RGBA',(WIDTH,HEIGHT),raw,'raw','BGRA',surf.contents.pitch,1).convert('RGB')
    sdl2.SDL_FreeSurface(surf);return im


def main():
    create=p2.SDL_CreateWindow
    p2.SDL_CreateWindow=lambda t,x,y,w,h,flags:create(t,x,y,w,h,(flags|sdl2.SDL_WINDOW_HIDDEN)&~sdl2.SDL_WINDOW_SHOWN)
    pico2d.open_canvas(WIDTH,HEIGHT,sync=False)
    checks=[];states=set();foot_samples=[]
    try:
        ui.enable_blending();g=PistolComparison();keys=(sdl2.Uint8*sdl2.SDL_NUM_SCANCODES)()
        g.hero_look.mode='C'      # preserved four-key baseline, even though launcher now starts D
        g.zombies=[];g.used.update(a for a,_ in g.TEACH)
        def tick(dt=1/60):
            g.update(dt,keys);pico2d.clear_canvas();g.draw()
            states.add(g.hero_look.flow.sprite);pico2d.update_canvas()
        for _ in range(3):tick()
        assert g.hero_look.mode=='C' and g.hero_look.flow.sprite=='low'
        keys[sdl2.SDL_SCANCODE_D]=1
        # Manually estimated boot centres in the rendered pixel grid; not an automatic joint solver.
        right_boot={0:(39,56),1:(32,56),2:(24,56),3:(28,54)}
        for i in range(60):
            tick();flow=g.hero_look.flow
            if flow.sprite.startswith('walk_'):
                frame=int(flow.sprite.rsplit('_',1)[1]);p=right_boot[frame]
                foot_samples.append({'tick':i,'key':frame,'phase':flow.phase,'root_world_x':g.hero.x,
                    'estimated_right_boot_world_x':g.hero.x+(p[0]-32)/DOT,'candidate_stance':frame in (0,1)})
        assert {f'walk_{i}' for i in range(4)}<=states
        checks.append('normal walk uses all four full-body keys')
        keys[sdl2.SDL_SCANCODE_D]=0
        for _ in range(8):tick()
        g.hero.start_ready()
        for _ in range(14):tick()
        assert 'raise' in states and g.hero_look.flow.sprite=='aim'
        checks.append('stationary raise reaches planted A-like aim')
        keys[sdl2.SDL_SCANCODE_D]=1
        for _ in range(70):tick()
        assert {f'aim_walk_{i}' for i in range(4)}<=states
        keys[sdl2.SDL_SCANCODE_D]=0
        for _ in range(12):tick()
        assert 'settle' in states and g.hero_look.flow.sprite=='aim'
        checks.append('aimed movement uses short-step keys, then settles before idle aim')
        # Actual hit through the same game update. Feed a mouse target for muzzle-to-target ray.
        z=Zombie(g.zombie_look,g.hero.x+85,g.hero.y);g.zombies=[z];hp=z.health
        scale=g.zoom*DOT;sx=(z.x-g.cam[0])*scale;sy=HEIGHT-1-(z.y+22-g.cam[1])*scale
        g.aim=(sx,sy);ammo=g.ammo;g.release(sx,sy)
        for _ in range(35):tick()
        assert g.ammo==ammo-1 and z.health<hp and 'recoil' in states,(g.ammo,z.health,states)
        checks.append('real release consumes one bullet, hurts target and triggers recoil')
        g.hero.take_blow();tick();assert g.hero_look.flow.sprite=='hurt'
        g.hero.dead=.001
        for _ in range(28):tick()
        assert 'fall' in states and g.hero_look.flow.sprite=='down'
        checks.append('hurt and death have real body keys instead of standing idle')
        g.reset();g.zombies=[];tick();assert g.hero_look.flow.sprite=='low'
        for expected in ('D','A','B','C'):
            before=(g.hero.x,g.hero.y,g.hero.hp,g.ammo)
            g.key_down(sdl2.SDLK_F8,keys);assert g.hero_look.mode==expected
            assert before==(g.hero.x,g.hero.y,g.hero.hp,g.ammo)
            tick()
        checks.append('reset and A/B/C/D switching retain position/health/ammo')
        # Per-pose hold drift quantifies the remaining pixel-animation foot slide, not zero foot-lock.
        runs=[];run=[]
        for sample in foot_samples:
            if not sample['candidate_stance']:
                if run:runs.append(run);run=[]
                continue
            if run and sample['key']!=run[-1]['key']:runs.append(run);run=[]
            run.append(sample)
        if run:runs.append(run)
        drift=max((abs(r[-1]['estimated_right_boot_world_x']-r[0]['estimated_right_boot_world_x'])*DOT for r in runs),default=0.)
        foot={'method':'estimated boot centre sampled each 1/60s; per-held-key candidate-stance drift',
              'max_drift_canvas_px':round(drift,3),'zero_foot_lock':False,'samples':foot_samples,
              'limitation':'art boot annotation is approximate; does not verify anatomy or full gait contact intervals'}
        (ART/'foot_audit.json').write_text(json.dumps(foot,indent=2),encoding='utf-8')
        # Render whole gameplay sequence, including stops and action interruptions.
        g.reset();g.zombies=[];g.dev.god=True;g.used.update(a for a,_ in g.TEACH)
        frames=[]
        for i in range(300):
            keys[sdl2.SDL_SCANCODE_D]=int(10<=i<65 or 110<=i<165)
            if i==80:g.hero.start_ready()
            if i==190:g.hero.start_slash(g.hero.x+100,g.hero.y+22)
            if i==250:g.hero.take_blow()
            g.update(1/60,keys)
            if i%3==0:
                pico2d.clear_canvas();g.draw();im=capture();frames.append(im.crop((400,150,1020,470)))
                if i==180:im.save(ART/'game_flow.png')
                pico2d.update_canvas()
        frames[0].save(ART/'game_flow.gif',save_all=True,append_images=frames[1:],duration=50,loop=0,disposal=2)
        result={'checks':checks,'states_observed':sorted(states),'montage_frames':300,
                'foot_drift_canvas_px':round(drift,3),'direction_scope':'one direction mirrored; no dedicated vertical/roll/pickup keys'}
        (ART/'runtime_check.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result))
    finally:pico2d.close_canvas()


if __name__=='__main__':main()
