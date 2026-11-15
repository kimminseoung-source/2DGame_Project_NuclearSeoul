"""UI redesign mockup over a real game frame (no HUD). Not game code: a picture to choose from."""
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

D = sys.argv[1]
FONT = "C:/Windows/Fonts/NotoSansKR-VF.ttf"
TEXT = (236, 230, 214)
SUB = (168, 162, 150)
FAINT = (110, 108, 102)
RED = (205, 62, 52)
AMBER = (226, 182, 96)
GREEN = (120, 176, 120)


def font(px, weight="Regular"):
    f = ImageFont.truetype(FONT, px)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


def layer(img):
    return Image.new("RGBA", img.size, (0, 0, 0, 0))


def text(d, xy, s, f, fill=TEXT, anchor="la", shadow=True):
    if shadow:
        d.text((xy[0] + 1, xy[1] + 2), s, font=f, fill=(0, 0, 0, 200), anchor=anchor)
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def icon(d, kind, cx, cy, s):
    if kind == "bandage":
        d.rounded_rectangle((cx - s * .7, cy - s * .5, cx + s * .4, cy + s * .5), 3, fill=(228, 224, 210))
        d.rectangle((cx + s * .4, cy - s * .5, cx + s * .85, cy - s * .2), fill=(228, 224, 210))
        d.rectangle((cx - s * .7, cy - s * .08, cx + s * .4, cy + s * .08), fill=(140, 170, 140))
    elif kind == "can":
        d.rounded_rectangle((cx - s * .55, cy - s * .75, cx + s * .55, cy + s * .75), 3, fill=(160, 162, 168))
        d.rectangle((cx - s * .55, cy - s * .25, cx + s * .55, cy + s * .35), fill=(198, 120, 60))
        d.rectangle((cx - s * .55, cy - s * .75, cx + s * .55, cy - s * .6), fill=(210, 210, 214))
    elif kind == "blade":
        d.polygon([(cx - s, cy + s * .15), (cx + s * .55, cy - s * .15), (cx + s * .9, cy), (cx + s * .55, cy + s * .2)], fill=(206, 210, 214))
        d.rectangle((cx - s * 1.2, cy + s * .02, cx - s * .8, cy + s * .3), fill=(110, 70, 45))
    elif kind == "pack":
        d.rounded_rectangle((cx - s * .6, cy - s * .55, cx + s * .6, cy + s * .75), 5, fill=(120, 104, 76))
        d.rectangle((cx - s * .35, cy - s * .8, cx + s * .35, cy - s * .55), fill=(90, 78, 58))


def vignette(img, colour, strength):
    w, h = img.size
    m = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(m)
    md.rectangle((0, 0, w, h), fill=255)
    md.rounded_rectangle((60, 40, w - 60, h - 40), 120, fill=0)
    m = m.filter(ImageFilter.GaussianBlur(70)).point(lambda v: int(v * strength))
    tint = Image.new("RGBA", (w, h), colour + (255,))
    tint.putalpha(m)
    return Image.alpha_composite(img, tint)


def play_hud(bg):
    img = vignette(bg.convert("RGBA"), (120, 10, 10), 0.35)      # bleeding: the edges go red
    L = layer(img)
    d = ImageDraw.Draw(L)
    # top left: the goal, no box
    text(d, (32, 26), "목표", font(13, "Bold"), AMBER)
    text(d, (32, 46), "물자를 챙겨 지하철 입구로", font(20, "Medium"))
    text(d, (32, 76), "붕대 2 · 통조림 1 챙김", font(14), SUB)
    # bottom left: health number + thin bar, status chips under it
    x, y = 32, 618
    text(d, (x, y), "58", font(34, "Bold"), TEXT)
    text(d, (x + 50, y + 15), "%", font(15, "Medium"), SUB)
    bx, by, bw = x + 78, y + 22, 210
    d.rounded_rectangle((bx, by, bx + bw, by + 6), 3, fill=(0, 0, 0, 150))
    d.rounded_rectangle((bx, by, bx + int(bw * .80), by + 6), 3, fill=(205, 180, 170, 120))  # damage trail
    d.rounded_rectangle((bx, by, bx + int(bw * .58), by + 6), 3, fill=RED)
    cx = x
    for label, col in (("출혈", RED), ("물림", (176, 112, 100)), ("긁힘", (150, 120, 110))):
        f = font(13, "Medium")
        w = d.textlength(label, font=f) + 26
        d.rounded_rectangle((cx, y + 54, cx + w, y + 78), 12, fill=(10, 10, 12, 170))
        d.ellipse((cx + 9, y + 62, cx + 17, y + 70), fill=col)
        text(d, (cx + 21, y + 59), label, f, TEXT, shadow=False)
        cx += w + 6
    # bottom middle: quick slots, soft, no hard borders
    slots = (("bandage", 2, "1"), ("can", 1, "2"), (None, 0, "3"))
    s, gap = 54, 8
    left = 640 - (3 * s + 2 * gap) // 2
    for i, (kind, n, key) in enumerate(slots):
        l, t = left + i * (s + gap), 640
        if kind:
            d.rounded_rectangle((l, t, l + s, t + s), 8, fill=(12, 12, 14, 175))
            icon(d, kind, l + s / 2, t + s / 2 - 2, 15)
            text(d, (l + s - 7, t + s - 5), str(n), font(13, "Bold"), TEXT, anchor="rd")
        else:
            d.rounded_rectangle((l, t, l + s, t + s), 8, outline=(255, 255, 255, 40), width=1)
        text(d, (l + 7, t + 4), key, font(11, "Medium"), FAINT, shadow=False)
    # thin weight line under the slots
    ww = 3 * s + 2 * gap
    d.rounded_rectangle((left, 702, left + ww, 705), 2, fill=(0, 0, 0, 140))
    d.rounded_rectangle((left, 702, left + int(ww * .3), 705), 2, fill=(200, 196, 180, 200))
    text(d, (left + ww + 12, 690), "Tab 배낭", font(12), FAINT)
    # message: just above the slots, fades
    text(d, (640, 600), "찢어짐  체력 -22%", font(18, "Medium"), (240, 200, 150), anchor="ma")
    # world prompt next to a thing you can use
    px, py = 905, 360
    f = font(13, "Medium")
    d.rounded_rectangle((px, py, px + 92, py + 26), 13, fill=(10, 10, 12, 190))
    d.rounded_rectangle((px + 5, py + 4, px + 23, py + 22), 4, fill=AMBER)
    text(d, (px + 14, py + 5), "E", font(12, "Bold"), (20, 18, 14), anchor="ma", shadow=False)
    text(d, (px + 30, py + 4), "통조림", f, TEXT, shadow=False)
    return Image.alpha_composite(img, L)


def inventory(bg):
    img = bg.convert("RGBA")
    img = Image.alpha_composite(img, Image.new("RGBA", img.size, (6, 6, 8, 175)))
    L = layer(img)
    d = ImageDraw.Draw(L)
    top, bottom = 120, 600
    # three columns sharing one frame: body | bag | nearby
    cols = ((150, 420), (440, 850), (870, 1130))
    d.rounded_rectangle((cols[0][0] - 20, top - 20, cols[2][1] + 20, bottom + 20), 14, fill=(16, 16, 19, 248))
    for l, r in cols[1:]:
        d.line((l - 10, top + 10, l - 10, bottom - 10), fill=(40, 40, 44), width=1)
    # body
    l, r = cols[0]
    text(d, (l, top), "몸", font(18, "Bold"), shadow=False)
    text(d, (r, top + 4), "58%", font(15, "Medium"), SUB, anchor="ra", shadow=False)
    cx, base = (l + r) // 2 - 50, top + 60
    o = (200, 196, 186, 150)
    d.ellipse((cx - 18, base, cx + 18, base + 36), outline=o, width=2)
    d.rounded_rectangle((cx - 34, base + 42, cx + 34, base + 150), 14, outline=o, width=2)
    d.rounded_rectangle((cx - 52, base + 46, cx - 38, base + 140), 7, outline=o, width=2)
    d.rounded_rectangle((cx + 38, base + 46, cx + 52, base + 140), 7, outline=o, width=2)
    d.rounded_rectangle((cx - 30, base + 154, cx - 4, base + 260), 10, outline=o, width=2)
    d.rounded_rectangle((cx + 4, base + 154, cx + 30, base + 260), 10, outline=o, width=2)
    d.ellipse((cx + 39, base + 96, cx + 51, base + 108), fill=RED)
    d.ellipse((cx - 51, base + 70, cx - 39, base + 82), fill=(176, 112, 100))
    wy = top + 60
    for name, state, col in (("물림 · 오른팔", "출혈", RED), ("긁힘 · 왼팔", "", (176, 112, 100))):
        text(d, (cx + 80, wy), name, font(13, "Medium"), TEXT, shadow=False)
        if state:
            text(d, (cx + 80, wy + 19), state, font(12), col, shadow=False)
        wy += 46
    text(d, (l, bottom - 64), "손", font(12), FAINT, shadow=False)
    text(d, (l + 120, bottom - 64), "등", font(12), FAINT, shadow=False)
    for i, kind in enumerate(("blade", "pack")):
        gx = l + i * 120
        d.rounded_rectangle((gx, bottom - 44, gx + 100, bottom), 8, fill=(28, 28, 32))
        icon(d, kind, gx + 50, bottom - 22, 15)
    # bag list
    l, r = cols[1]
    text(d, (l, top), "배낭", font(18, "Bold"), shadow=False)
    text(d, (r, top + 4), "0.6 / 2.0", font(15, "Medium"), SUB, anchor="ra", shadow=False)
    d.rounded_rectangle((l, top + 36, r, top + 40), 2, fill=(42, 42, 46))
    d.rounded_rectangle((l, top + 36, l + int((r - l) * .3), top + 40), 2, fill=(200, 196, 180))
    rows = (("bandage", "붕대", 2, "0.2"), ("can", "통조림", 1, "0.4"))
    y = top + 58
    for i, (kind, name, n, w) in enumerate(rows):
        if i == 0:
            d.rounded_rectangle((l, y, r, y + 44), 8, fill=(44, 38, 30))
            d.rounded_rectangle((l, y + 8, l + 3, y + 36), 2, fill=AMBER)
        icon(d, kind, l + 28, y + 22, 13)
        text(d, (l + 54, y + 11), name, font(15, "Medium"), TEXT, shadow=False)
        text(d, (l + 54 + d.textlength(name, font=font(15, "Medium")) + 8, y + 13), f"×{n}", font(13), SUB, shadow=False)
        text(d, (r - 12, y + 13), w, font(13), SUB, anchor="ra", shadow=False)
        y += 50
    # selected item detail
    dy = bottom - 112
    d.line((l, dy - 14, r, dy - 14), fill=(40, 40, 44))
    text(d, (l, dy), "붕대", font(16, "Bold"), shadow=False)
    text(d, (l, dy + 28), "가장 심한 상처의 출혈을 멈추고 체력 +15%", font(14), SUB, shadow=False)
    hx = l
    for key, label in (("Enter", "사용"), ("X", "버리기"), ("W S", "고르기")):
        f = font(12, "Medium")
        kw = d.textlength(key, font=f) + 14
        d.rounded_rectangle((hx, bottom - 26, hx + kw, bottom - 4), 5, fill=(44, 44, 48))
        text(d, (hx + kw / 2, bottom - 23), key, f, TEXT, anchor="ma", shadow=False)
        text(d, (hx + kw + 6, bottom - 24), label, font(12), SUB, shadow=False)
        hx += kw + d.textlength(label, font=font(12)) + 22
    # nearby
    l, r = cols[2]
    text(d, (l, top), "근처", font(18, "Bold"), shadow=False)
    y = top + 58
    icon(d, "can", l + 28, y + 22, 13)
    text(d, (l + 54, y + 11), "통조림", font(15, "Medium"), TEXT, shadow=False)
    text(d, (r - 12, y + 13), "0.4", font(13), SUB, anchor="ra", shadow=False)
    f = font(12, "Medium")
    d.rounded_rectangle((l, bottom - 26, l + 22, bottom - 4), 5, fill=AMBER)
    text(d, (l + 11, bottom - 23), "F", f, (20, 18, 14), anchor="ma", shadow=False)
    text(d, (l + 30, bottom - 24), "모두 줍기", font(12), SUB, shadow=False)
    d.rounded_rectangle((l + 110, bottom - 26, l + 150, bottom - 4), 5, fill=(44, 44, 48))
    text(d, (l + 130, bottom - 23), "Tab", f, TEXT, anchor="ma", shadow=False)
    text(d, (l + 158, bottom - 24), "닫기", font(12), SUB, shadow=False)
    return Image.alpha_composite(img, L)


bg = Image.open(D + "/bg_play.png")
a = play_hud(bg).convert("RGB")
b = inventory(bg).convert("RGB")
a.save(D + "/new_play.png")
b.save(D + "/new_bag.png")
# side-by-side: now (left) vs proposal (right)
for now, new, name in (("now_play.png", a, "compare_play.png"), ("now_bag.png", b, "compare_bag.png")):
    c = Image.new("RGB", (1280 * 2 + 20, 720 + 50), (24, 24, 26))
    c.paste(Image.open(D + "/" + now), (0, 50))
    c.paste(new, (1300, 50))
    cd = ImageDraw.Draw(c)
    cd.text((16, 12), "지금", font=font(24, "Bold"), fill=TEXT)
    cd.text((1316, 12), "제안", font=font(24, "Bold"), fill=AMBER)
    c.save(D + "/" + name)
print("ok")
