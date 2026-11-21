import sys, random; sys.path.insert(0,"src")
import pico2d, sdl2, play, settings, ui, weapons
from pico2d import pico2d as canvas
from PIL import Image, ImageDraw, ImageFont
keys=(sdl2.Uint8*sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
rows=[]
for wkey in ("knife","machete","bat"):
    random.seed(1); g=play.Game(); g.to_spawn=0; g.zombies[:]=[]
    h=g.hero; h.x,h.y=300,300; h.weapon=weapons.WEAPONS[wkey]
    for _ in range(60): g.update(1/60,keys)
    k=g.zoom*settings.DOT
    g.press(*( (h.x+200-g.cam[0])*k, settings.HEIGHT-1-(h.y+30-g.cam[1])*k ))
    keys[sdl2.SDL_SCANCODE_D]=1
    cells=[]
    for i in range(48):
        g.update(1/60,keys)
        if i % 8 == 7:
            pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
            s=sdl2.SDL_CreateRGBSurfaceWithFormat(0,settings.WIDTH,settings.HEIGHT,32,sdl2.SDL_PIXELFORMAT_ARGB8888)
            sdl2.SDL_RenderReadPixels(canvas.renderer,None,sdl2.SDL_PIXELFORMAT_ARGB8888,s.contents.pixels,s.contents.pitch)
            sdl2.SDL_SaveBMP(s,b"docs/planning/_t.bmp"); im=Image.open("docs/planning/_t.bmp").convert("RGB")
            cx=(h.x-g.cam[0])*k; cy=settings.HEIGHT-(h.y-g.cam[1])*k
            cells.append(im.crop((int(cx-60),int(cy-130),int(cx+80),int(cy+20))))
    keys[sdl2.SDL_SCANCODE_D]=0
    rows.append((weapons.WEAPONS[wkey]["name"],cells))
import os; os.remove("docs/planning/_t.bmp")
W,H=rows[0][1][0].size
font=ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf",20)
sheet=Image.new("RGB",(W*6+120,H*3),(20,20,22)); d=ImageDraw.Draw(sheet); d.fontmode="1"
for r,(n,cells) in enumerate(rows):
    d.text((8,r*H+H//2-10),n,font=font,fill=(196,170,92))
    for c,im in enumerate(cells): sheet.paste(im,(120+c*W,r*H))
sheet.save("docs/planning/ready_walk_ingame.png"); print(sheet.size)
