"""Shots for C: a claw coming -> [우클릭]; held by two -> [Space]; just hit -> red edge; bleeding -> [1]."""
import sys, random; sys.path.insert(0, "src")
from math import pi
import pico2d, sdl2, play, settings, ui, infected
from pico2d import pico2d as canvas
from PIL import Image, ImageDraw, ImageFont
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()


def grab(g):
    pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    sdl2.SDL_SaveBMP(s, b"docs/planning/_t.bmp")
    return Image.open("docs/planning/_t.bmp").convert("RGB").resize((640, 360))


def game():
    random.seed(3); g = play.Game(); g.to_spawn = 0
    g.used |= {"move", "attack", "roll", "charge", "sneak", "pick"}
    h = g.hero; h.x, h.y = 420, 300
    z = infected.Zombie(g.zombie_look, h.x + 40, h.y); z.prone = False
    g.zombies[:] = [z]
    for _ in range(5): g.update(1 / 60, keys)
    return g, h, z


shots, notes = [], []
g, h, z = game()
z.state, z.timer, z.heading, z.turn_in = "windup", 0.5, pi, 99
shots.append(("할퀴기 예고: [우클릭] 밀치기", grab(g))); notes.append(g.marks_now())
g, h, z = game()
h.grabbed = 1.0; g.hurt_flash = 0.2
shots.append(("붙잡힘 + 막 맞음: [Space], 붉은 테두리", grab(g))); notes.append(g.marks_now())
g, h, z = game()
z.x = h.x + 300
g.condition.wound(); g.condition.wound(); g.bag["bandage"] = 1
shots.append(("피 흘림 + 붕대 있음: [1] 붕대", grab(g))); notes.append(g.marks_now())
import os; os.remove("docs/planning/_t.bmp")
font = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 16)
sheet = Image.new("RGB", (640 * 3, 360 + 30), (20, 20, 22)); d = ImageDraw.Draw(sheet); d.fontmode = "1"
for i, (t, im) in enumerate(shots):
    sheet.paste(im, (i * 640, 30)); d.text((i * 640 + 8, 6), t, font=font, fill=(196, 170, 92))
sheet.save("docs/planning/react_marks_ingame.png"); print(notes, g.condition.bleeding)
