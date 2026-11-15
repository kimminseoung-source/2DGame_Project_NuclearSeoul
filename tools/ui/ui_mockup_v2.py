"""UI mockup v2 (2026-11-16, "AI 티가 안 나게"): drawn on a 640x360 pixel canvas with no
anti-aliasing, then scaled x2 with nearest neighbour over a real game frame. Rules come from
docs/research/UI_NOT_AI_RESEARCH.md: no rounded cards / pills / side-stripe rows / glass blur,
a pixel font (Galmuri), colours taken from the world, things the hero would carry (a taped note,
a pocket notebook) instead of app panels.

usage: python tools/ui/ui_mockup_v2.py <frame dir with bg_play.png> <project root> <out dir>
"""
import random
import sys

from PIL import Image, ImageDraw, ImageFont

FRAMES, ROOT, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
W, H, K = 640, 360, 2                         # pixel canvas, scale to the 1280x720 screen
REG = ROOT + "/assets/fonts/galmuri/Galmuri11.ttf"
BOLD = ROOT + "/assets/fonts/galmuri/Galmuri11-Bold.ttf"

# colours sampled from the world (asphalt, faded road paint, rust, the hero's jacket, blood)
INK = (34, 30, 28)
PAPER = (200, 192, 168)
PAPER_DARK = (170, 160, 136)
TAPE = (196, 182, 120)
LIGHT = (222, 216, 198)
GREY = (122, 122, 118)
ASPHALT = (28, 31, 35)
ROAD = (196, 170, 92)          # faded road-line yellow: things you can use
RUST = (128, 72, 48)
BLOOD = (168, 34, 30)
BLOOD_DARK = (92, 18, 18)
PENCIL = (78, 74, 70)


def f(path, px=12):
    return ImageFont.truetype(path, px)


def crisp(d):
    d.fontmode = "1"                           # no anti-aliasing: pixel text
    return d


def outlined(d, xy, s, font, fill, edge=(8, 8, 10), anchor="la"):
    """Classic pixel-game text: a 1px dark outline, not a soft shadow."""
    x, y = xy
    for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1)):
        d.text((x + ox, y + oy), s, font=font, fill=edge, anchor=anchor)
    d.text(xy, s, font=font, fill=fill, anchor=anchor)


def paper(d, box, seed, colour=PAPER, torn_bottom=True):
    """A scrap of paper: straight top, uneven torn bottom edge, a few darker fibres."""
    rnd = random.Random(seed)
    l, t, r, b = box
    d.rectangle((l, t, r, b - 2), fill=colour)
    if torn_bottom:
        for x in range(l, r + 1):
            d.line((x, b - 2, x, b - 2 + rnd.choice((0, 1, 1, 2, 2, 3))), fill=colour)
    for _ in range((r - l) * (b - t) // 40):  # paper grain
        d.point((rnd.randint(l, r), rnd.randint(t, b - 4)), fill=PAPER_DARK)


def tape(d, x, y, w=18, h=7):
    for yy in range(y, y + h):                 # dithered translucent tape
        for xx in range(x, x + w):
            if (xx + yy) % 2 == 0:
                d.point((xx, yy), fill=TAPE)


def pix_icon(d, name, x, y, mono=None):
    """Hand-placed 16x16 pixel icons (ours). Vector icons shrunk to 12-16 px turned into
    blobs (checked), so every icon is drawn pixel by pixel. `mono` draws it in one ink colour."""
    def rect(l, t, r, b, col):
        d.rectangle((x + l, y + t, x + r, y + b), fill=mono or col)
    hole = PAPER if mono else None
    if name == "bandage":                       # a roll with a loose end
        rect(2, 5, 10, 12, (226, 220, 204))
        rect(10, 9, 14, 11, (226, 220, 204))
        d.rectangle((x + 5, y + 7, x + 7, y + 9), fill=hole or (176, 170, 150))
        if not mono:
            rect(2, 11, 10, 12, (150, 170, 140))
    elif name == "can":                         # tin can: rim, label, body
        rect(4, 3, 11, 14, (150, 152, 156))
        rect(4, 7, 11, 10, (190, 110, 56))
        if mono:
            d.rectangle((x + 5, y + 7, x + 10, y + 10), fill=hole)
        else:
            rect(4, 3, 11, 3, (210, 210, 214))
    elif name == "pill":
        rect(5, 5, 10, 14, (196, 150, 70))
        rect(4, 3, 11, 5, (226, 220, 204))
    elif name == "drop":                        # blood drop
        rows = ((7, 8), (7, 8), (6, 9), (6, 9), (5, 10), (4, 11), (4, 11), (4, 11), (5, 10), (6, 9))
        for i, (l, r) in enumerate(rows):
            d.line((x + l, y + 3 + i, x + r, y + 3 + i), fill=mono or (200, 40, 34))
        d.point((x + 6, y + 9), fill=mono or (240, 120, 100))
    elif name == "machete":
        d.polygon([(x + 1, y + 11), (x + 11, y + 4), (x + 14, y + 4), (x + 12, y + 8), (x + 4, y + 12)],
                  fill=mono or (206, 210, 214))
        rect(0, 11, 3, 14, (110, 70, 45))
    elif name == "backpack":
        rect(3, 4, 12, 14, (120, 104, 76))
        rect(5, 2, 10, 4, (90, 78, 58))
        if mono:
            d.rectangle((x + 5, y + 9, x + 10, y + 12), outline=hole)
        else:
            rect(5, 9, 10, 12, (96, 82, 60))
    elif name == "snail":                       # slowed
        d.ellipse((x + 6, y + 4, x + 13, y + 11), outline=mono or (150, 170, 200))
        rect(2, 11, 14, 12, (150, 170, 200))


def dither_edge(img, colour, strength):
    """Bleeding: the screen edge goes red in an ordered dither, heaviest in the corners."""
    d = ImageDraw.Draw(img)
    bayer = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))
    for y in range(H):
        for x in range(W):
            r = ((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2
            level = 16 * strength * max(0.0, min(1.0, (r - 0.95) / 0.8))
            if bayer[y % 4][x % 4] < level:
                d.point((x, y), fill=colour + (255,))


def hud():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dither_edge(img, BLOOD_DARK, 0.6)
    d = crisp(ImageDraw.Draw(img))
    small, bold = f(REG), f(BOLD)
    # goal: a taped, torn note in the hero's hand
    paper(d, (12, 10, 172, 48), 3)
    tape(d, 6, 7)
    d.text((20, 15), "지하철 입구로", font=bold, fill=INK)
    d.line((20, 29, 88, 28), fill=BLOOD)      # a pen underline, a little crooked
    d.text((20, 32), "붕대·통조림 있으면 챙기기", font=small, fill=PENCIL)
    # health: square pixel bar with a 1px frame, red fill and the pale trail, number in front
    x, y = 14, 320
    outlined(d, (x, y - 2), "58", f(BOLD, 24), LIGHT)
    bx, by, bw = x + 34, y + 9, 96
    d.rectangle((bx - 1, by - 1, bx + bw, by + 5), fill=(8, 8, 10))
    d.rectangle((bx, by, bx + int(bw * .80) - 1, by + 4), fill=(150, 120, 112))
    d.rectangle((bx, by, bx + int(bw * .58) - 1, by + 4), fill=BLOOD)
    d.line((bx, by, bx + int(bw * .58) - 1, by), fill=(210, 80, 64))   # 1px highlight
    # status: only what asks for an action (bleeding -> bandage, slowed), icon + word, no chips.
    # The full wound list lives in the notebook.
    ix = x - 2
    for name, colour, label in (("drop", (226, 120, 100), "출혈"), ("snail", (150, 170, 200), "느림")):
        pix_icon(d, name, ix, y + 18)
        outlined(d, (ix + 16, y + 20), label, small, colour)
        ix += 16 + int(d.textlength(label, font=small)) + 8
    # quick slots: plain squares with a bevel like the wrecks' metal, no rounded corners
    left = 320 - (3 * 26 + 2 * 4) // 2
    for i, (name, n) in enumerate((("bandage", 2), ("can", 1), (None, 0))):
        l, t = left + i * 30, 326
        d.rectangle((l, t, l + 25, t + 25), fill=(20, 22, 26) if name else None, outline=(64, 66, 70))
        d.line((l + 1, t + 1, l + 24, t + 1), fill=(84, 86, 90))
        if name:
            pix_icon(d, name, l + 5, t + 4)
            outlined(d, (l + 24, t + 25), str(n), small, LIGHT, anchor="rd")
        outlined(d, (l + 1, t - 13), str(i + 1), small, GREY)
    outlined(d, (left + 96, 336), "Tab", small, GREY)
    # message: pixel text with a hard outline
    outlined(d, (320, 286), "찢어짐  -22%", f(BOLD), (236, 196, 150), anchor="ma")
    # use prompt beside the thing: a key box like a keyboard key, then the word
    px, py = 452, 180
    d.rectangle((px, py, px + 11, py + 12), fill=ROAD, outline=(8, 8, 10))
    d.text((px + 3, py + 1), "E", font=bold, fill=INK)
    outlined(d, (px + 15, py + 1), "통조림", small, LIGHT)
    return img


def bag():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = crisp(ImageDraw.Draw(img))
    # dim the world with a dither, not a smooth glass layer
    for y in range(H):
        for x in range(W):
            if (x + y) % 2 == 0 or y % 2 == 0:
                d.point((x, y), fill=(6, 6, 8, 255))
    small, bold = f(REG), f(BOLD)
    # an open pocket notebook: two ruled pages, a spine, a dog-eared corner
    l, t, r, b = 92, 40, 548, 318
    d.rectangle((l + 3, t + 3, r + 3, b + 3), fill=(4, 4, 6))          # hard drop shadow
    paper(d, (l, t, 318, b), 11, torn_bottom=False)
    paper(d, (322, t, r, b), 12, torn_bottom=False)
    d.rectangle((318, t, 321, b), fill=RUST)                            # spine
    for yy in range(t + 30, b - 8, 16):                                 # ruled lines
        d.line((l + 6, yy, 312, yy), fill=(176, 172, 158))
        d.line((328, yy, r - 6, yy), fill=(176, 172, 158))
    d.polygon([(r - 12, t), (r, t), (r, t + 12)], fill=PAPER_DARK)      # dog-ear
    # left page: the body, like a first-aid record
    d.text((l + 10, t + 10), "몸", font=bold, fill=INK)
    d.text((300, t + 10), "58", font=bold, fill=BLOOD, anchor="ra")
    cx, cy = l + 50, t + 40
    o = PENCIL
    d.ellipse((cx - 7, cy, cx + 7, cy + 14), outline=o)
    d.rectangle((cx - 12, cy + 17, cx + 12, cy + 58), outline=o)
    d.rectangle((cx - 19, cy + 18, cx - 14, cy + 54), outline=o)
    d.rectangle((cx + 14, cy + 18, cx + 19, cy + 54), outline=o)
    d.rectangle((cx - 11, cy + 60, cx - 2, cy + 100), outline=o)
    d.rectangle((cx + 2, cy + 60, cx + 11, cy + 100), outline=o)
    for (wx, wy) in ((cx + 16, cy + 38), (cx - 17, cy + 28)):           # wounds as ink crosses
        d.line((wx - 2, wy - 2, wx + 2, wy + 2), fill=BLOOD)
        d.line((wx - 2, wy + 2, wx + 2, wy - 2), fill=BLOOD)
    d.text((l + 90, t + 46), "오른팔  물림", font=small, fill=INK)
    d.text((l + 90, t + 61), "피가 난다", font=small, fill=BLOOD)
    d.text((l + 90, t + 94), "왼팔  긁힘", font=small, fill=INK)
    d.text((l + 10, b - 44), "손", font=small, fill=PENCIL)
    d.text((l + 80, b - 44), "등", font=small, fill=PENCIL)
    pix_icon(d, "machete", l + 28, b - 28, INK)
    pix_icon(d, "backpack", l + 96, b - 28, INK)
    # right page: the bag as a handwritten list; the chosen line is circled in pen
    x = 334
    d.text((x, t + 10), "배낭", font=bold, fill=INK)
    d.text((r - 10, t + 10), "0.6/2.0", font=small, fill=PENCIL, anchor="ra")
    rows = (("bandage", "붕대", "x2", "0.2"), ("can", "통조림", "x1", "0.4"))
    yy = t + 33
    for i, (name, label, n, w) in enumerate(rows):
        pix_icon(d, name, x, yy - 2, INK)
        d.text((x + 18, yy), label, font=bold if i == 0 else small, fill=INK)
        d.text((x + 18 + int(d.textlength(label, font=bold)) + 4, yy), n, font=small, fill=PENCIL)
        d.text((r - 10, yy), w, font=small, fill=PENCIL, anchor="ra")
        if i == 0:                                                       # pen circle, a bit off
            d.ellipse((x - 4, yy - 5, x + 96, yy + 14), outline=BLOOD)
        yy += 16
    d.text((x, yy + 8), "근처", font=bold, fill=INK)
    pix_icon(d, "can", x, yy + 23, INK)
    d.text((x + 18, yy + 25), "통조림", font=small, fill=INK)
    d.text((r - 10, yy + 25), "0.4", font=small, fill=PENCIL, anchor="ra")
    # the chosen thing, in pencil, and the keys at the foot of the page
    d.text((x, b - 66), "붕대 - 피를 멈춘다. 체력 +15", font=small, fill=PENCIL)
    for row, keys in enumerate(((("Enter", "쓰기"), ("X", "버리기")), (("F", "다 줍기"), ("Tab", "닫기")))):
        kx, ky = x, b - 42 + row * 16
        for key, label in keys:
            kw = int(d.textlength(key, font=small)) + 5
            d.rectangle((kx, ky, kx + kw, ky + 12), fill=LIGHT, outline=INK)
            d.text((kx + 3, ky + 1), key, font=small, fill=INK)
            d.text((kx + kw + 4, ky + 1), label, font=small, fill=PENCIL)
            kx += kw + int(d.textlength(label, font=small)) + 14
    return img


def over(frame, ui):
    big = ui.resize((W * K, H * K), Image.NEAREST)
    return Image.alpha_composite(frame.convert("RGBA"), big).convert("RGB")


bg = Image.open(FRAMES + "/bg_play.png")
a, b = over(bg, hud()), over(bg, bag())
a.save(OUT + "/v2_play.png")
b.save(OUT + "/v2_bag.png")
v1p, v1b = Image.open(OUT + "/new_play.png"), Image.open(OUT + "/new_bag.png")
lab = ImageFont.truetype(BOLD, 24)
for one, two, name in ((v1p, a, "compare_v1_v2_play.png"), (v1b, b, "compare_v1_v2_bag.png")):
    c = Image.new("RGB", (1280 * 2 + 20, 770), (24, 24, 26))
    c.paste(one, (0, 50))
    c.paste(two, (1300, 50))
    cd = ImageDraw.Draw(c)
    cd.fontmode = "1"
    cd.text((16, 12), "1차 제안 (AI 느낌)", font=lab, fill=(200, 200, 200))
    cd.text((1316, 12), "2차 제안", font=lab, fill=ROAD)
    c.save(OUT + "/" + name)
print("ok")
