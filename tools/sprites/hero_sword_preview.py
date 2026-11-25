"""Package the Blender idle study, measure it, and capture a temporary in-game preview.

Only rendered images are quantized/outlined; this script never draws a character from code.
The screenshot monkeypatch lasts for this process and does not replace the game's assets.
"""
import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from repaint import repaint


def font(size):
    return ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', size)


def outline_repaint(source, spec, out):
    ids = json.loads((source / 'ids.json').read_text(encoding='utf-8'))
    reports, frames = [], {}
    for kind in ('body', 'held'):
        frames[kind] = []
        for i in range(2):
            id_image = Image.open(source/kind/'id'/f'{i}.png').convert('RGBA')
            light = Image.open(source/kind/'light'/f'{i}.png').convert('RGBA')
            result = repaint(id_image, light, ids, spec['palette'], {}, [110, 165],
                             outline=(17,17,21,255), cleanup=True)
            dest = out/kind/'Breath'/'south-east'
            dest.mkdir(parents=True,exist_ok=True)
            result.save(dest/f'{i}.png')
            if i == 0:
                idle = out/kind/'Idle'/'rotations'
                idle.mkdir(parents=True,exist_ok=True)
                result.save(idle/'south-east.png')
            box = result.getchannel('A').getbbox()
            if not box: raise RuntimeError('Empty sprite')
            w,h=result.size
            edge = box[0] == 0 or box[1] == 0 or box[2] == w or box[3] == h
            reports.append({'kind':kind,'frame':i,'size':[w,h], 'bbox':box,
                            'height':box[3]-box[1],'touches_edge':edge,
                            'opaque_colors':len({p for p in result.getdata() if p[3]})})
            if edge: raise RuntimeError(f'Clipped preview candidate: {kind} {i}')
            frames[kind].append(result)
    return frames, reports


def on_background(im, size):
    rgba=im.convert('RGBA')
    box=rgba.getchannel('A').getbbox()
    if box: rgba=rgba.crop(box)
    rgba.thumbnail(size, Image.Resampling.NEAREST)
    return rgba


def board(frames, source, out, reports):
    canvas=Image.new('RGB',(1200,950),(25,28,31));d=ImageDraw.Draw(canvas)
    fg=(226,224,211);muted=(159,169,162)
    d.text((28,18),'검 주인공 · 3D → 도트 1차 제작',font=font(24),fill=fg)
    d.text((28,55),'남동 대기 한 방향 / 기존 리깅 모델 재사용 / 몸과 검 분리 / 게임 정식 교체 전',font=font(15),fill=muted)
    reference=Image.open(ROOT/'assets/characters/concepts/hero_codex_v1/hero_concept_v4_sword.png').convert('RGBA')
    reference=reference.crop((20,5,475,980))
    reference.thumbnail((300,410),Image.Resampling.LANCZOS)
    large_front=on_background(Image.open(source/'model_front.png'),(300,410))
    large_back=on_background(Image.open(source/'model_back.png'),(300,410))
    for centre,label,img in zip((205,600,995),('기준 콘셉트','3D · 앞쪽','3D · 뒤쪽'),(reference,large_front,large_back)):
        d.text((centre-70,94),label,font=font(18),fill=fg)
        canvas.paste(img,(centre-img.width//2,130+410-img.height),img)
    d.line((25,560,1175,560),fill=(73,81,77))
    d.text((28,578),'실제 도트 확인 · 원본 픽셀을 정수 배율로 확대',font=font(18),fill=fg)
    old=Image.open(ROOT/'assets/characters/hero_3d/Idle/rotations/south-east.png').convert('RGBA')
    items=[(175,'기존 · 3배',old,3),(445,'새 몸 · 3배',frames['body'][0],3),
           (710,'검 포함 · 3배',frames['held'][0],3),(1000,'검 포함 · 6배',frames['held'][0],6)]
    baseline=866
    for centre,label,img,k in items:
        d.text((centre-67,624),label,font=font(16),fill=fg)
        bbox=img.getchannel('A').getbbox();native=img.crop(bbox)
        enlarged=native.resize((native.width*k,native.height*k),Image.Resampling.NEAREST)
        canvas.paste(enlarged,(centre-enlarged.width//2,baseline-enlarged.height),enlarged)
        d.line((centre-105,baseline,centre+105,baseline),fill=(73,81,77))
        d.text((centre-50,baseline+10),f'{native.width} × {native.height}px',font=font(13),fill=muted)
    d.text((28,918),'아래 줄은 외형 비교용 발끝 정렬 / 게임 캡처는 렌더에서 기록한 고정 지면 피벗 사용',font=font(13),fill=muted)
    canvas.save(out/'comparison.png')
    gif_frames=[]
    for im in frames['held']:
        bg=Image.new('RGBA',im.size,(25,28,31,255));bg.alpha_composite(im)
        gif_frames.append(bg.convert('RGB').resize((384,384),Image.Resampling.NEAREST))
    gif_frames[0].save(out/'idle_preview.gif',save_all=True,append_images=gif_frames[1:],
                       duration=600,loop=0,disposal=2)


def game_capture(out, anchors):
    sys.path.insert(0,str(ROOT/'src'))
    import ctypes, random
    import pico2d,sdl2,play,settings,ui
    from pico2d import pico2d as p2
    create=p2.SDL_CreateWindow
    p2.SDL_CreateWindow=lambda title,x,y,w,h,flags:create(title,x,y,w,h,
        (flags|sdl2.SDL_WINDOW_HIDDEN)&~sdl2.SDL_WINDOW_SHOWN)
    pico2d.open_canvas(settings.WIDTH,settings.HEIGHT,sync=False)
    try:
        ui.enable_blending();random.seed(1);g=play.Game();g.dev.freeze=True;g.dev.no_spawn=True
        keys=(sdl2.Uint8*sdl2.SDL_NUM_SCANCODES)()
        for _ in range(3):g.update(1/60,keys)
        image=pico2d.load_image(str(out/'held/Idle/rotations/south-east.png'))
        k=g.hero_look.k;point=anchors['records'][0]['ground'];grip=anchors['records'][0]['grip']
        def preview_draw(pose,time,x,feet_y,facing,*args,**kwargs):
            cx=x+(32-point[0]-.5)/k;cy=feet_y+(point[1]+.5-32)/k
            image.draw(cx,cy,64/k,64/k)
            return (cx+(grip[0]+.5-32)/k,cy+(32-grip[1]-.5)/k)
        g.hero_look.draw=preview_draw
        g.hero.weapon=dict(g.hero.weapon,name='검 외형 시안')
        pico2d.clear_canvas();g.draw()
        w,h=settings.WIDTH,settings.HEIGHT
        surf=sdl2.SDL_CreateRGBSurfaceWithFormat(0,w,h,32,sdl2.SDL_PIXELFORMAT_ARGB8888)
        sdl2.SDL_RenderReadPixels(p2.renderer,None,sdl2.SDL_PIXELFORMAT_ARGB8888,
                                 surf.contents.pixels,surf.contents.pitch)
        raw=ctypes.string_at(surf.contents.pixels,surf.contents.pitch*h)
        shot=Image.frombuffer('RGBA',(w,h),raw,'raw','BGRA',surf.contents.pitch,1).convert('RGB')
        shot.save(out/'game_preview.png');sdl2.SDL_FreeSurface(surf);pico2d.update_canvas()
    finally:pico2d.close_canvas()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--capture-game',action='store_true')
    args=ap.parse_args();out=(ROOT/args.out).resolve();out.mkdir(parents=True,exist_ok=True)
    spec=json.loads((ROOT/'assets/characters/concepts/hero_codex_v1/production_v1.json').read_text(encoding='utf-8'))
    source=out/'renders';anchors=json.loads((source/'anchors.json').read_text(encoding='utf-8'))
    frames,report=outline_repaint(source,spec,out)
    for kind in ('body','held'):
        points=[f['grip'] for f in anchors['records']]
        hands={'idle':{'south-east':[points[0]]},'breath':{'south-east':points}}
        (out/kind/'hands.json').write_text(json.dumps(hands,indent=2),encoding='utf-8')
        (out/kind/'pivot.json').write_text(json.dumps(anchors,indent=2),encoding='utf-8')
    board(frames,source,out,report)
    if args.capture_game:game_capture(out,anchors)
    (out/'validation.json').write_text(json.dumps({'frames':report,'anchors':anchors,
        'scope':'idle only; no attack, no other directions; temporary game draw override'},indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=1));print('PREVIEW_PACKAGED',out)


if __name__=='__main__':main()
