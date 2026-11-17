"""The 2nd presentation slides (2026-11-16): the guide asks for three pages - the game, progress
against the 1st plan, and what changed in the plan (the user: only the map change).

    python tools/presentation/make_second.py   -> docs/presentation/2차발표_부산까지.pptx
"""
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "presentation"
IMG = OUT / "img"
FONT = "Malgun Gothic"
BG, CARD, TEXT, DIM = RGBColor(0x1B, 0x1D, 0x21), RGBColor(0x29, 0x2C, 0x31), RGBColor(0xE6, 0xE1, 0xD4), RGBColor(0xA8, 0xA3, 0x96)
GOLD, GREEN, RED, TRACK = RGBColor(0xC9, 0xAC, 0x5E), RGBColor(0x7F, 0xA3, 0x7A), RGBColor(0xC0, 0x5A, 0x48), RGBColor(0x3A, 0x3D, 0x43)


def crops():
    IMG.mkdir(parents=True, exist_ok=True)
    plan = ROOT / "docs" / "planning"
    alley = Image.open(plan / "alley_map.png")
    alley.crop((0, 40, alley.width, alley.height)).save(IMG / "alley_map.png")
    alley.crop((0, 40, alley.width, 40 + round(alley.width / 2.04))).save(IMG / "alley_north.png")
    tuk = Image.open(plan / "tuk_text_map.png")
    tuk.crop((0, 40, tuk.width, tuk.height)).save(IMG / "tuk.png")
    house = Image.open(plan / "house_plan_view.png")
    house.crop((house.width // 2 + 10, 40, house.width, house.height)).save(IMG / "house_inside.png")


def text(slide, x, y, w, h, runs, size=16, color=TEXT, bold=False, align=PP_ALIGN.LEFT):
    """A text box; runs: a string, or a list of lines (each a string or (string, colour, bold))."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    lines = runs if isinstance(runs, list) else [runs]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(6)
        s, c, b = (line, color, bold) if isinstance(line, str) else line
        r = p.add_run()
        r.text = s
        r.font.name, r.font.size, r.font.color.rgb, r.font.bold = FONT, Pt(size), c, b
    return box


def rect(slide, x, y, w, h, fill, rounded=True):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
                                   Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.fill.background()
    if rounded:
        shape.adjustments[0] = 0.08
    return shape


def picture(slide, path, x, y, w=None, h=None, alt=""):
    pic = slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w) if w else None, Inches(h) if h else None)
    pic._element.nvPicPr.cNvPr.set("descr", alt)
    return pic


def new_slide(prs, title):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG
    if title:
        text(s, 0.6, 0.45, 12, 0.7, title, size=32, color=GOLD, bold=True)
    return s


def main():
    crops()
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)

    # 1. the game
    s = new_slide(prs, None)
    text(s, 0.6, 0.45, 6, 0.8, "부산까지", size=40, color=GOLD, bold=True)
    text(s, 0.6, 1.25, 6, 0.9, "핵 재난 이후의 한국, 서울에서 부산까지 걸어가는 2D 도트 생존 액션 (탑뷰 · 싱글)",
         size=16, color=DIM)
    feats = [("보고 듣는 피폭체", "앞을 보고 소리를 듣고, 발견하면 '!'와 함께 달려온다"),
             ("노리고 받아치는 근접 전투", "머리·몸통·다리를 노려 베고, 예고 끝에 밀쳐 받아친다"),
             ("물자를 챙겨 출구로", "집을 뒤져 물자를 챙기고 지하철 입구로 빠져나간다")]
    for i, (head, body) in enumerate(feats):
        y = 2.35 + i * 1.35
        rect(s, 0.6, y, 5.7, 1.15, CARD)
        text(s, 0.85, y + 0.17, 5.3, 0.4, head, size=18, color=TEXT, bold=True)
        text(s, 0.85, y + 0.6, 5.3, 0.5, body, size=14, color=DIM)
    picture(s, IMG / "alley_map.png", 6.75, 1.35, w=6.0, alt="손으로 설계한 골목 구역 전체 그림")
    text(s, 6.75, 6.05, 6.0, 0.4, "지금 구역: 직접 설계한 골목 (들어갈 수 있는 집, 지하철 출구)", size=12, color=DIM)
    text(s, 0.6, 6.75, 12.1, 0.4, "WASD 이동 · 클릭 공격 · 누르고 있으면 조준 · 우클릭 밀치기 · Space 구르기 · E 줍기 · Tab 배낭",
         size=12, color=DIM)
    s.notes_slide.notes_text_frame.text = (
        "부산까지는 핵 재난 이후의 한국에서 서울부터 부산까지 걸어가는 2D 도트 생존 액션입니다. "
        "피폭체는 앞을 보고 소리를 듣고, 저를 발견하면 달려옵니다. 머리·몸통·다리를 조준해 베고, 할퀴기 직전에 밀쳐 받아칠 수 있습니다. "
        "집 안을 뒤져 물자를 챙기고 지하철 입구로 빠져나가는 것이 한 구역의 목표입니다.")

    # the demo: the game playing itself (tools/presentation/record_demo.py), a GIF that plays in the show
    if (IMG / "demo.gif").exists():
        s = new_slide(prs, "게임 시연")
        picture(s, IMG / "demo.gif", 1.9, 1.35, w=9.5, alt="골목 구역 시연: 전투, 집에서 물자 챙기기, 지하철 출구로 탈출")
        text(s, 1.9, 6.8, 9.5, 0.4, "발견하면 달려오는 피폭체 → 머리 조준 · 받아치기 → 집에서 물자 → 지하철 입구로 탈출",
             size=13, color=DIM, align=PP_ALIGN.CENTER)
        s.notes_slide.notes_text_frame.text = (
            "실제 게임 화면입니다. 앞을 비추는 시야만 보이고, 피폭체는 저를 발견하면 느낌표와 함께 달려옵니다. "
            "클릭을 누르고 있으면 머리를 노릴 수 있고, 할퀴기 직전에 밀치면 휘청여서 반격할 틈이 생깁니다. "
            "집에 들어가면 지붕이 걷히고, 물자를 챙겨 지하철 입구로 빠져나가면 한 구역이 끝납니다.")

    # 2. progress against the 1st plan
    s = new_slide(prs, "1차 계획 대비 진행 상황")
    stages = [("01 탐색 기반", "20%", 100, GREEN, "완료", "이동·충돌, 물자 줍기·사용, 배낭(칸·무게), 출구로 탈출"),
              ("02 전투 시제품", "25%", 100, GREEN, "완료", "무기 5종, 부위 조준, 받아치기, 기력, 피폭체 감각"),
              ("03 생존과 여정", "30%", 40, GOLD, "일부", "상처·출혈·붕대, 들어가는 집  /  남음: 구역 이동, 결말"),
              ("04 완성·검수", "25%", 45, GOLD, "진행 중", "도트 캐릭터, UI, 손도트 집·가구  /  남음: 소리, 그림")]
    for i, (name, weight, pct, col, state, detail) in enumerate(stages):
        y = 1.55 + i * 1.22
        rect(s, 0.6, y, 8.6, 1.02, CARD)
        text(s, 0.85, y + 0.14, 2.6, 0.4, name, size=18, bold=True)
        text(s, 0.85, y + 0.56, 2.6, 0.4, f"계획 비중 {weight}", size=12, color=DIM)
        text(s, 3.45, y + 0.14, 4.5, 0.4, detail, size=13, color=TEXT)
        rect(s, 3.45, y + 0.66, 4.3, 0.16, TRACK)
        rect(s, 3.45, y + 0.66, 4.3 * pct / 100, 0.16, col)
        text(s, 7.95, y + 0.55, 1.1, 0.4, state, size=13, color=col, bold=True)
    total = round(sum(int(w[:-1]) * p for _, w, p, *_ in stages) / 100)
    rect(s, 9.55, 1.55, 3.2, 2.2, CARD)
    text(s, 9.55, 1.75, 3.2, 1.0, f"약 {total}%", size=54, color=GOLD, bold=True, align=PP_ALIGN.CENTER)
    text(s, 9.55, 2.95, 3.2, 0.6, "계획 비중으로 계산한 전체 진행", size=12, color=DIM, align=PP_ALIGN.CENTER)
    hw, hh = Image.open(IMG / "house_inside.png").size
    picture(s, IMG / "house_inside.png", 9.55 + (3.2 - 2.75 * hw / hh) / 2, 3.95, h=2.75, alt="손도트로 그린 집 안: 방 두 칸과 가구")
    text(s, 9.55, 6.8, 3.2, 0.4, "들어갈 수 있는 집 (손도트)", size=12, color=DIM, align=PP_ALIGN.CENTER)
    s.notes_slide.notes_text_frame.text = (
        f"1차 계획의 네 단계 중 탐색과 전투는 끝났습니다. 생존과 여정은 상처와 출혈, 들어가는 집까지 했고 구역 이동과 결말이 남았습니다. "
        f"그래픽은 도트 캐릭터와 UI, 손으로 찍은 집과 가구까지 진행했습니다. 계획 비중으로 보면 약 {total}%입니다.")

    # 3. what we tried on the way (2026-11-16 "개발하면서 여러 시도들이 있었잖아요, 그런 것들도")
    s = new_slide(prs, "개발하며 해 본 시도들")
    tries = [("시점", "횡스크롤 · 턴제 · 탑뷰 시험판을 직접 해 보고 → 탑뷰", None),
             ("전투", "한 방 전투 → 무기별 피해 + 머리·몸통·다리 조준", "try_aim.png"),
             ("캐릭터 그림", "매끈한 3D 렌더 → 키 32px 도트", "try_art.png"),
             ("UI", "상자와 글이 많은 화면 → 도트 쪽지, 글 대신 화면 반응", "try_ui.png"),
             ("가구·건물", "3D 모델 렌더 → 칸마다 찍은 손도트", "try_furniture.png"),
             ("맵", "실제 지도 기반 → 직접 설계한 골목 (다음 쪽)", "alley_north.png")]
    cw, chh = 3.85, 2.55
    for i, (head, body, pic) in enumerate(tries):
        x, y = 0.6 + (i % 3) * (cw + 0.3), 1.45 + (i // 3) * (chh + 0.25)
        rect(s, x, y, cw, chh, CARD)
        ix, iy, iw, ih = x + 0.15, y + 0.15, cw - 0.3, 1.35
        if pic:
            pw, ph = Image.open(IMG / pic).size
            w = min(iw, ih * pw / ph)
            h = w * ph / pw
            picture(s, IMG / pic, ix + (iw - w) / 2, iy + (ih - h) / 2, w=w, alt=f"{head}: 바꾸기 전과 후")
        else:                                       # three small boxes for the three views tried
            for k, (label, col) in enumerate((("횡스크롤", DIM), ("턴제", DIM), ("탑뷰", GOLD))):
                bx = ix + k * (iw / 3) + 0.05
                box = rect(s, bx, iy + 0.25, iw / 3 - 0.1, 0.85, TRACK)
                text(s, bx, iy + 0.5, iw / 3 - 0.1, 0.4, [(label, col, k == 2)], size=14, align=PP_ALIGN.CENTER)
        text(s, x + 0.2, y + 1.6, cw - 0.4, 0.35, head, size=16, bold=True)
        text(s, x + 0.2, y + 1.98, cw - 0.4, 0.55, body, size=12, color=DIM)
    s.notes_slide.notes_text_frame.text = (
        "개발하면서 여러 가지를 직접 해 보고 정했습니다. 시점은 횡스크롤과 턴제, 탑뷰 시험판을 만들어 비교한 뒤 탑뷰로 정했고, "
        "전투는 한 방에 끝나는 방식에서 무기별 피해와 부위 조준으로 바꿨습니다. 그림은 3D 렌더에서 도트로, 가구와 건물은 칸마다 찍은 손도트로 바꿨고, "
        "UI는 글을 줄이고 화면 반응으로 알려 주게 했습니다.")

    # 4. the plan change: how maps are made
    s = new_slide(prs, "기획 변경: 맵 만드는 방식")
    picture(s, IMG / "tuk.png", 0.6, 1.5, w=5.95, alt="실제 지도(한국공학대)를 글자 지도로 바꿔 그린 시험")
    picture(s, IMG / "alley_north.png", 6.8, 1.5, w=5.95, alt="직접 설계한 골목")
    text(s, 0.6, 4.5, 5.95, 0.4, [("시도: 실제 지도(한국공학대) 기반", RED, True)], size=16)
    text(s, 6.8, 4.5, 5.95, 0.4, [("변경: 직접 설계한 맵 (골목)", GREEN, True)], size=16)
    reasons = ["실제 건물(고층·대형 건물)을 비슷하게 그려 내기가 사실상 어려움",
               "실제 길은 숨을 곳·좁은 골목·출구 같은 게임 동선과 맞지 않음",
               "→ '주택가 골목, 상가 거리, 역 앞' 같은 동네 느낌만 참고해 1글자 = 1m 글자 지도로 직접 설계"]
    rect(s, 0.6, 5.1, 12.15, 1.5, CARD)
    text(s, 0.9, 5.3, 11.6, 1.5, reasons, size=15)
    s.notes_slide.notes_text_frame.text = (
        "기획에서 바뀐 점은 맵을 만드는 방식입니다. 처음에는 실제 지도, 예를 들어 한국공학대 주변 지도를 바탕으로 맵을 만들려고 했습니다. "
        "하지만 고층 건물이 많은 실제 건물을 비슷하게 그리기 어렵고, 실제 길은 게임 동선과 맞지 않아서, "
        "동네의 느낌만 참고해 직접 설계하는 방식으로 바꿨습니다.")

    path = OUT / "2차발표_부산까지.pptx"
    prs.save(path)
    print(path)


if __name__ == "__main__":
    main()
