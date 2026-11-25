"""Package two generated appearance keys; shared scale, no synthetic character drawing.
Capture them temporarily through the real game renderer without changing game assets.
"""
import ctypes
import json
import os
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'assets/characters/previews/hero_redjacket_v1'


def package():
    im = Image.open(OUT / 'generated_poses.png').convert('RGBA')
    cells = [im.crop((n * im.width // 2, 0, (n + 1) * im.width // 2, im.height)) for n in range(2)]
    for cell in cells:
        cell.putalpha(cell.getchannel('A').point(lambda a: 255 if a >= 128 else 0))
    # Idle blade is below the head, so its bbox height is the body height.
    box = cells[0].getbbox()
    scale = 36 / (box[3] - box[1])
    records = []
    for name, cell in zip(('idle', 'guard'), cells):
        bbox = cell.getbbox()
        crop = cell.crop(bbox)
        small = crop.resize((round(crop.width*scale), round(crop.height*scale)), Image.Resampling.NEAREST)
        frame = Image.new('RGBA', (64,64))
        frame.alpha_composite(small, (32-small.width//2, 58-small.height))
        frame.save(OUT / f'{name}_36px.png')
        bounds = frame.getbbox()
        assert bounds and bounds[0] > 0 and bounds[1] > 0 and bounds[2] < 64 and bounds[3] < 64
        records.append({'pose':name, 'source_bbox':bbox, 'output_bbox':bounds, 'pivot':[32,58]})
    (OUT / 'validation.json').write_text(json.dumps({'shared_scale':scale, 'frames':records,
        'scope':'two appearance keys with baked sword; no model/rig/animation or game replacement'}, indent=2), encoding='utf-8')


def capture():
    os.environ['BUSAN_AREA'] = 'arena'
    sys.path.insert(0, str(ROOT/'src'))
    import pico2d, sdl2, ui
    from pico2d import pico2d as p2
    from play import Game
    from settings import WIDTH, HEIGHT
    create = p2.SDL_CreateWindow
    p2.SDL_CreateWindow = lambda title,x,y,w,h,flags:create(title,x,y,w,h,
        (flags|sdl2.SDL_WINDOW_HIDDEN)&~sdl2.SDL_WINDOW_SHOWN)
    pico2d.open_canvas(WIDTH, HEIGHT, sync=False)
    try:
        ui.enable_blending()
        g = Game()
        g.dev.freeze = g.dev.no_spawn = True
        g.zombies, g.people, g.ground_weapons = [], [], []
        g.used.update(a for a,_ in g.TEACH)
        keys = (sdl2.Uint8*sdl2.SDL_NUM_SCANCODES)()
        for _ in range(3):g.update(1/60, keys)
        original = g.hero_look.draw
        for name in ('existing', 'idle', 'guard'):
            if name != 'existing':
                sprite = pico2d.load_image(str(OUT/f'{name}_36px.png'))
                def draw(pose,time,x,feet_y,facing,*args,**kwargs):
                    k=32/54
                    sprite.draw(x, feet_y+(58-32)/k, 64/k, 64/k)
                    return None
                g.hero_look.draw = draw
            pico2d.clear_canvas();g.draw()
            surf=sdl2.SDL_CreateRGBSurfaceWithFormat(0,WIDTH,HEIGHT,32,sdl2.SDL_PIXELFORMAT_ARGB8888)
            sdl2.SDL_RenderReadPixels(p2.renderer,None,sdl2.SDL_PIXELFORMAT_ARGB8888,surf.contents.pixels,surf.contents.pitch)
            raw=ctypes.string_at(surf.contents.pixels,surf.contents.pitch*HEIGHT)
            shot=Image.frombuffer('RGBA',(WIDTH,HEIGHT),raw,'raw','BGRA',surf.contents.pitch,1).convert('RGB')
            shot.save(OUT/f'game_{name}.png')
            sdl2.SDL_FreeSurface(surf);pico2d.update_canvas()
        g.hero_look.draw = original
    finally:
        pico2d.close_canvas()


def board():
    font=lambda size:ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',size)
    board=Image.new('RGB',(1000,650),(27,30,32));d=ImageDraw.Draw(board)
    d.text((26,18),'세 번째 시안 · 붉은 재킷 주인공 / 외형 확인 2장',font=font(23),fill=(235,229,216))
    d.text((26,55),'실제 크기 36px 기준 → 정수 배율 확대 / 검은 그림에 포함 / 동작 제작 전',font=font(15),fill=(172,183,179))
    for i,(name,label) in enumerate((('idle','대기 · 검을 낮춤'),('guard','준비 · 낮고 넓게'))):
        frame=Image.open(OUT/f'{name}_36px.png').convert('RGBA')
        frame=frame.resize((320,320),Image.Resampling.NEAREST)
        board.paste(frame,(90+i*490,60),frame)
        d.text((130+i*490,365),label,font=font(19),fill=(235,229,216))
    for i,(name,label) in enumerate((('existing','기존 주인공'),('idle','새 대기'),('guard','새 검 준비'))):
        im=Image.open(OUT/f'game_{name}.png').crop((500,205,780,395))
        board.paste(im,(35+i*325,420))
        d.text((55+i*325,615),label+' · 게임 화면',font=font(15),fill=(199,205,196))
    board.save(OUT/'comparison.png')


if __name__=='__main__':
    package();capture();board()
    print('Appearance study saved:',OUT)
