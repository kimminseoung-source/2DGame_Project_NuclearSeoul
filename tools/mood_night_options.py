"""밤 시야 넓히기 후보(2026-11-26 사용자 "밤일 때 시야가 너무 짧은 것 같음").
mood_preview.py의 A(밤 어둠)+D(비네트)를 그대로 쓰고 반지름·바깥 밝기만 바꿔 2x2로 비교한다.
    .venv\\Scripts\\python.exe tools/checks/run_hidden.py tools/mood_night_options.py"""
import json
from PIL import Image, ImageDraw
import mood_preview as mp

OPTIONS = {
    "지금": {"ambient": 0.45, "light_radius_px": 150, "soft_px": 90},
    "1안": {"ambient": 0.55, "light_radius_px": 240, "soft_px": 140},
    "2안": {"ambient": 0.62, "light_radius_px": 320, "soft_px": 180},
    "3안": {"ambient": 0.70, "light_radius_px": 400, "soft_px": 220},
}


def main():
    mp.pico2d.open_canvas(mp.W, mp.H, sync=False); mp.ui.enable_blending()
    gn, night = mp.scene(23.0, hide_teach=True)
    mp.pico2d.close_canvas()
    # 주인공을 화면 가운데 근처로 본 경우도 함께 보려면 실제 위치 사용
    hx = (gn.hero.x - gn.cam[0]) * mp.W / gn.view_w; hy = mp.H - (gn.hero.y - gn.cam[1]) * mp.H / gn.view_h
    w, h = mp.W // 2, mp.H // 2
    sheet = Image.new("RGB", (w * 2 + 12, (h + 40) * 2), (18, 18, 20))
    d = ImageDraw.Draw(sheet); fn = mp.font(20)
    base = dict(mp.PARAMS["A_night_dark"])
    for i, (name, p) in enumerate(OPTIONS.items()):
        mp.PARAMS["A_night_dark"] = {**base, **p}
        im = mp.vignette(mp.night_dark(night, hx, hy))
        x, y = (i % 2) * (w + 12), (i // 2) * (h + 40)
        d.text((x + 8, y + 8), f"{name}: 밝은 반지름 {p['light_radius_px']}px, 바깥 밝기 {round(p['ambient'] * 100)}%",
               fill=(235, 235, 235), font=fn)
        sheet.paste(im.resize((w, h)), (x, y + 40))
    sheet.save(mp.OUT / "night_options.png")
    (mp.OUT / "night_options.json").write_text(json.dumps(OPTIONS, ensure_ascii=False, indent=1), encoding="utf-8")
    print("saved", mp.OUT / "night_options.png", "hero", round(hx), round(hy))


if __name__ == "__main__":
    main()
