"""Method 2 (hand pixel) vs method 3 (side-view 3D pose -> flat pixel overpaint) for one
concept, the gas-mask wanderer: hood + tarp cape (point colour, rust red), gas mask with a
canister snout, one cracked lens glowing green, charcoal coat, machete."""
import json, math, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

M3 = Path(sys.argv[1]); OUT = sys.argv[2]
sys.path.insert(0, str(Path.cwd() / "tools/sprites"))
from repaint import to_display

PAL = {
    "K": (14, 14, 20), "R": (122, 40, 32), "r": (168, 62, 44), "C": (42, 44, 52), "c": (66, 70, 80),
    "M": (70, 72, 74), "m": (104, 106, 104), "W": (190, 200, 196), "G": (120, 255, 140), "g": (60, 150, 80),
    "T": (34, 36, 42), "t": (52, 54, 62), "B": (20, 18, 18), "S": (210, 214, 218), "s": (130, 134, 140),
    "H": (70, 46, 30), "F": (150, 100, 76),
}

# ---------------------------------------------------------------- method 3
ids = json.loads((M3 / "id/ids.json").read_text())
shown = {p: to_display(c) for p, c in ids.items()}
COAT = {"top", "top_r", "top_l", "forearms_r", "forearms_l"}
LEGS = {"bottom", "bottom_r", "bottom_l"}


def parts(img):
    px = img.load(); w, h = img.size
    out = {}
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a >= 128:
                out[(x, y)] = min(shown, key=lambda p: sum((u - v) ** 2 for u, v in zip(shown[p], (r, g, b))))
    return out


def centroid(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)) if pts else None


def paint(idc, lit, motion):
    part = parts(idc); L = lit.load()
    img = Image.new("RGBA", idc.size); px = img.load()
    by = {}
    for p, n in part.items():
        by.setdefault(n, []).append(p)
    head = by.get("head", []) + by.get("hair", []) + by.get("eyes", [])
    hx0 = min(p[0] for p in head); hx1 = max(p[0] for p in head)
    hy0 = min(p[1] for p in head); hy1 = max(p[1] for p in head)
    torso = by.get("top", [])
    # cape first (behind the body): from the back of the neck, trailing away from the motion
    nx, ny = hx0 + 1, hy1 + 1
    back = [p for p in torso if p[1] <= hy1 + 6]
    if back:
        nx = min(p[0] for p in back)
    low = max(p[1] for p in torso) + 6 if torso else ny + 18
    sweep = {"idle": 2, "run": 9, "swing": 12}[motion]
    d = ImageDraw.Draw(img)
    tip = (nx - sweep - 3, low - sweep // 2)
    poly = [(nx + 3, ny - 1), (nx - 2, ny), (tip[0] + 2, tip[1] - 4), (tip[0], tip[1]),
            (tip[0] + 3, tip[1] - 1), (tip[0] + 5, tip[1] + 1), (tip[0] + 8, tip[1] - 2), (nx + 2, low - 4)]
    d.polygon(poly, fill=PAL["R"])
    d.line([(nx, ny + 1), (tip[0] + 3, tip[1] - 3)], fill=PAL["r"])
    for (x, y), n in part.items():
        lv = 0 if L[x, y][0] < 130 else 1
        far = n.endswith("_l")
        if n in ("head", "hair", "eyes"):
            col = "m" if lv else "M"
            if y <= hy0 + (hy1 - hy0) * 0.45 or x <= hx0 + (hx1 - hx0) * 0.45:
                col = "r" if lv else "R"            # hood over the top and back of the head
        elif n in COAT:
            col = "c" if lv and not far else "C"
        elif n in LEGS:
            col = "t" if lv and not far else "T"
        elif n.startswith("shoes"):
            col = "B"
        elif n.startswith("hands"):
            col = "B" if far else "K"
        else:
            col = "C"
        px[x, y] = PAL[col] + (255,)
    # gas mask: snout forward-low of the face, cracked glowing lens, clear lens
    sx, sy = hx1, hy0 + int((hy1 - hy0) * 0.62)
    for dx, dy, c in ((1, 0, "M"), (2, 0, "M"), (1, 1, "M"), (2, 1, "m"), (3, 1, "M"), (1, -1, "K"), (3, 0, "K")):
        px[sx + dx, sy + dy] = PAL[c] + (255,)
    ex, ey = hx1 - 1, hy0 + int((hy1 - hy0) * 0.4)
    px[ex, ey] = PAL["G"] + (255,); px[ex - 1, ey] = PAL["g"] + (255,); px[ex, ey + 1] = PAL["g"] + (255,)
    # machete in the near hand along the forearm
    hand = centroid(by.get("hands_r", [])); fore = centroid(by.get("forearms_r", []))
    if hand and fore:
        ax, ay = hand[0] - fore[0], hand[1] - fore[1]; n = math.hypot(ax, ay) or 1
        ax, ay = ax / n, ay / n
        if motion == "idle":
            ax, ay = 0.5, 0.85
        d = ImageDraw.Draw(img)
        d.line([hand, (hand[0] + ax * 3, hand[1] + ay * 3)], fill=PAL["H"])
        d.line([(hand[0] + ax * 3, hand[1] + ay * 3), (hand[0] + ax * 13, hand[1] + ay * 13)], fill=PAL["S"], width=2)
    # outline
    a = img.getchannel("A").load(); w, h = img.size
    ol = [(x, y) for y in range(h) for x in range(w) if a[x, y] == 0 and any(
        0 <= x + i < w and 0 <= y + j < h and a[x + i, y + j] for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for p in ol:
        px[p] = PAL["K"] + (255,)
    return img


def m3_frames():
    out = []
    for sheet, frames in (("idle", (0,)), ("run", (0, 2, 4, 6)), ("swing", (0, 2, 3))):
        ida = Image.open(M3 / "id" / f"{sheet}.png").convert("RGBA"); la = Image.open(M3 / "light" / f"{sheet}.png").convert("RGBA")
        for f in frames:
            box = (f * 96, 0, f * 96 + 96, 64)
            out.append(paint(ida.crop(box), la.crop(box), sheet))
    return out


# ---------------------------------------------------------------- method 2 (hand placed pixels)
IDLE = """
........KKK.........
......KKrrrK........
.....KrrrrrrK.......
....KRrrMMMMK.......
....KRrMMmWMMK......
....KRRMMMMMMMK.....
....KRRKMMMGMMMK....
...KRRRRKMMMKMK.....
...KRRRCCKKKKK......
..KRRRCCCCcK........
..KRRRCCCccK........
..KRRRCCCccCK.......
..KRRRCCCcCCK.......
.KRRRRCCCcKcK.......
.KRRRRCCCCKcK.......
.KRRRRCCCCKFK.......
.KRRrRCCCCKKHK......
.KRRRrCCCCK.KHK.....
KRRrRRCCCCK..KSK....
KRRRKRCCCCK..KSsK...
KRK.KRTTTTK...KSsK..
KK..KKTTtTK....KSK..
....KTTTKTTK....KK..
....KTTK.KTK........
....KTTK.KTTK.......
....KTTK..KTK.......
....KTTK..KTK.......
...KTTTK..KTTK......
...KBBBK..KBBK......
...KBBBBK.KBBBK.....
...KKKKKK.KKKKK.....
"""
SLASH = """
...........KKK..................
.........KKrrrK.................
........KrrrrrrK................
.......KRrrMMMMK................
KK.....KRrMMmWMMK...............
KRKK...KRRMMMMMMMK..............
KRRRKK.KRRKMMMGMMMK.............
.KRRRRKKRRRKMMMKMK...........KK.
..KRRRRRRRCCKKKcccKK.......KKSK.
...KKRRRRRCCCCCCcccccKKKKKKSSsK.
.....KKRRRCCCCCCKKKKKFHHKSSsK...
.......KRRCCCCcK.....KKKSsK.....
........KRCCCCcK.......KKK......
........KCCCCCcK................
........KCCCCCCK................
.........KTTTTTK................
........KTTTTKTTK...............
.......KTTTK.KtTTK..............
......KTTTK...KTTTK.............
.....KTTTK.....KTTK.............
....KTTTK.......KTTK............
...KTTTK.........KTTK...........
..KBBBK..........KBBBK..........
..KBBBBK.........KBBBBK.........
..KKKKKK.........KKKKKK.........
"""


def from_map(text, w=40, h=40):
    rows = [r for r in text.strip("\n").split("\n")]
    img = Image.new("RGBA", (w, h))
    oy = h - len(rows) - 2
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                img.putpixel((x + 4, y + oy), PAL[ch] + (255,))
    return img


# ---------------------------------------------------------------- sheet
def strip(frames, scale, cw):
    W = cw * len(frames)
    s = Image.new("RGBA", (W * scale, frames[0].height * scale))
    for i, f in enumerate(frames):
        f2 = f.resize((f.width * scale, f.height * scale), Image.NEAREST)
        s.alpha_composite(f2, (i * cw * scale + (cw * scale - f2.width) // 2, 0))
    return s


BG = (30, 32, 40)
f1 = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 26)
f2 = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 18)
m3 = m3_frames(); m2 = [from_map(IDLE), from_map(SLASH)]
S = 4
top = strip([f.crop((16, 0, 80, 64)) for f in m3], S, 64)
bot = strip(m2, S, 40)
# 1x game-size row: both methods side by side on a dark street
small = Image.new("RGBA", (420, 70), BG + (255,))
for i, f in enumerate(m3[:1] + m3[4:5]):
    small.alpha_composite(f.crop((16, 0, 80, 64)), (10 + i * 60, 2))
for i, f in enumerate(m2):
    small.alpha_composite(f, (220 + i * 50, 26))
small = small.resize((420 * 3, 70 * 3), Image.NEAREST)

W = max(top.width, bot.width, small.width) + 40
H = 60 + top.height + 80 + bot.height + 80 + small.height + 30
sheet = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(sheet)
y = 14
d.text((20, y), "3번 방법: Blender 옆모습 동작(3D) → 위에 도트로 덧칠", font=f1, fill=(240, 236, 226))
d.text((20, y + 32), "서 있기 · 달리기 4칸 · 베기 3칸 (자동으로 모든 동작 가능)", font=f2, fill=(180, 180, 180)); y += 60
sheet.paste(top, (20, y), top); y += top.height + 20
d.text((20, y), "2번 방법: 손으로 한 칸씩 찍은 도트 (Claude가 직접)", font=f1, fill=(240, 236, 226))
d.text((20, y + 32), "서 있기 · 베기 (동작마다 전부 손으로 그려야 함)", font=f2, fill=(180, 180, 180)); y += 60
sheet.paste(bot, (20, y), bot); y += bot.height + 20
d.text((20, y), "실제 게임 크기 3배 (왼쪽 3번, 오른쪽 2번)", font=f1, fill=(240, 236, 226)); y += 40
sheet.paste(small, (20, y))
sheet.save(OUT); print("ok", sheet.size)
