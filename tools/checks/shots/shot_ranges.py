import sys, random; sys.path.insert(0,"src")
from math import pi
import pico2d, sdl2, play, settings, ui, infected, weapons
from pico2d import pico2d as canvas
from PIL import Image, ImageDraw, ImageFont
keys=(sdl2.Uint8*sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
crops=[]
for wkey in ("knife","machete","pipe"):
    random.seed(1); g=play.Game(); g.to_spawn=0
    z=infected.Zombie(g.zombie_look,900,600); g.zombies[:]=[z]; h=g.hero; h.x,h.y=420,300; h.weapon=weapons.WEAPONS[wkey]
    for _ in range(90): g.update(1/60,keys)
    z.x,z.y,z.state,z.heading,z.turn_in=h.x+95,h.y,"idle",pi,99
    k=g.zoom*settings.DOT
    sx,sy=(h.x+200-g.cam[0])*k, settings.HEIGHT-1-(h.y+60-g.cam[1])*k
    g.press(sx,sy)
    for _ in range(8): g.update(1/60,keys)
    g.aim=(sx,sy); z.x,z.y=h.x+95,h.y
    pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    s=sdl2.SDL_CreateRGBSurfaceWithFormat(0,settings.WIDTH,settings.HEIGHT,32,sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer,None,sdl2.SDL_PIXELFORMAT_ARGB8888,s.contents.pixels,s.contents.pitch)
    sdl2.SDL_SaveBMP(s,b"docs/planning/_t.bmp"); im=Image.open("docs/planning/_t.bmp").convert("RGB")
    cx=(h.x-g.cam[0])*k; cy=settings.HEIGHT-(h.y-g.cam[1])*k
    crops.append((weapons.WEAPONS[wkey], im.crop((int(cx-60),int(cy-260),int(cx+300),int(cy+40)))))
    if wkey == "bat": im.save("docs/planning/hud_weapon_ingame.png")
import os; os.remove("docs/planning/_t.bmp")
W,H=crops[0][1].size
font=ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf",20)
sheet=Image.new("RGB",(W*3,H+36),(20,20,22)); d=ImageDraw.Draw(sheet); d.fontmode="1"
for i,(w,c) in enumerate(crops):
    sheet.paste(c,(i*W,36)); d.text((i*W+8,8),f"{w['name']}: 범위 {w['cells']}칸, 속도 {weapons.speed_word(w)}",font=font,fill=(196,170,92))
sheet.save("docs/planning/attack_range_ingame.png"); print(sheet.size)
