"""Night dark around the hero + screen-edge vignette (2026-11-26 사용자 "A+D 같이 넣어줘",
밤 시야는 "2안": docs/planning/mood_preview/night_options.png, tools/mood_night_options.py).
- A: at night only a circle around the hero stays bright; outside it the screen is NIGHT_AMBIENT bright.
  Fades in with the dusk (Daylight.light 1 -> 0).
- D: the screen edges are a little darker all the time; when health is low they turn red and deeper.
Each layer is one texture made once at a quarter of the screen size and stretched, so a frame costs
three texture copies."""
import ctypes
import math
import sdl2
from pico2d import pico2d as canvas
from settings import WIDTH, HEIGHT, HERO_HP

NIGHT_RADIUS = 320          # px on screen that stay bright around the hero at night (2안; was 150)
NIGHT_SOFT = 180            # px over which the bright circle fades out
NIGHT_AMBIENT = 0.62        # how bright the screen is outside the circle at full night (2안; was 0.45)
VIG_START = 0.45            # vignette starts this far from the centre (0 centre .. 1 corner)
VIG_STRENGTH = 0.75         # darkest corner alpha, always
LOWHP_STRENGTH = 0.70       # red corner alpha at the lowest health
LOWHP_COLOR = (120, 0, 0)
LOWHP_FROM = 0.5            # red starts below this share of health, full at LOWHP_FULL
LOWHP_FULL = 0.2
STEP = 4                    # mask texel = STEP screen px (stretched, linear filtered)

_tex = {}


def _make(name, w, h, rgb, alpha_of):
    """A w x h texture of one colour whose alpha is alpha_of(x, y) in screen px (centre of the texel)."""
    buf = bytearray(w * h * 4)
    r, g, b = rgb
    i = 0
    for y in range(h):
        for x in range(w):
            buf[i] = r; buf[i + 1] = g; buf[i + 2] = b
            buf[i + 3] = alpha_of((x + 0.5) * STEP, (y + 0.5) * STEP)
            i += 4
    sdl2.SDL_SetHint(sdl2.SDL_HINT_RENDER_SCALE_QUALITY, b"1")
    t = sdl2.SDL_CreateTexture(canvas.renderer, sdl2.SDL_PIXELFORMAT_ABGR8888, sdl2.SDL_TEXTUREACCESS_STATIC, w, h)
    sdl2.SDL_SetHint(sdl2.SDL_HINT_RENDER_SCALE_QUALITY, b"0")
    raw = (ctypes.c_ubyte * len(buf)).from_buffer(buf)
    sdl2.SDL_UpdateTexture(t, None, raw, w * 4)
    sdl2.SDL_SetTextureBlendMode(t, sdl2.SDL_BLENDMODE_BLEND)
    _tex[name] = t
    return t


def night_alpha(d):
    """Darkness alpha (0..255) at distance d px from the hero at full night."""
    t = 0.0 if d < NIGHT_RADIUS else min(1.0, (d - NIGHT_RADIUS) / NIGHT_SOFT)
    return round(255 * t * (1 - NIGHT_AMBIENT))


def vignette_alpha(x, y, strength):
    R = math.hypot(WIDTH / 2, HEIGHT / 2)
    d = math.hypot(x - WIDTH / 2, y - HEIGHT / 2) / R
    return round(255 * strength * max(0.0, (d - VIG_START) / (1 - VIG_START)) ** 1.5)


def _textures():
    if not _tex:
        # the night mask is twice the screen so the hero can be anywhere on it; its centre is the hero
        nw, nh = 2 * WIDTH // STEP, 2 * HEIGHT // STEP
        _make("night", nw, nh, (0, 0, 0), lambda x, y: night_alpha(math.hypot(x - WIDTH, y - HEIGHT)))
        vw, vh = WIDTH // STEP, HEIGHT // STEP
        _make("vig", vw, vh, (0, 0, 0), lambda x, y: vignette_alpha(x, y, VIG_STRENGTH))
        _make("red", vw, vh, LOWHP_COLOR, lambda x, y: vignette_alpha(x, y, LOWHP_STRENGTH))
    return _tex


def night_amount(light):
    return max(0.0, min(1.0, 1.0 - light))


def lowhp_amount(hp):
    share = hp / HERO_HP
    return max(0.0, min(1.0, (LOWHP_FROM - share) / (LOWHP_FROM - LOWHP_FULL)))


def draw(game):
    """Screen-space layers over the world, under the HUD."""
    tex = _textures()
    ren = canvas.renderer
    night = night_amount(game.daylight.light)
    if night > 0:
        hx = (game.hero.x - game.cam[0]) * WIDTH / game.view_w
        hy = HEIGHT - (game.hero.y - game.cam[1]) * HEIGHT / game.view_h
        sdl2.SDL_SetTextureAlphaMod(tex["night"], round(255 * night))
        sdl2.SDL_RenderCopy(ren, tex["night"], None,
                            sdl2.SDL_Rect(round(hx - WIDTH), round(hy - HEIGHT), 2 * WIDTH, 2 * HEIGHT))
    full = sdl2.SDL_Rect(0, 0, WIDTH, HEIGHT)
    sdl2.SDL_RenderCopy(ren, tex["vig"], None, full)
    red = lowhp_amount(game.hero.hp)
    if red > 0:
        sdl2.SDL_SetTextureAlphaMod(tex["red"], round(255 * red))
        sdl2.SDL_RenderCopy(ren, tex["red"], None, full)
