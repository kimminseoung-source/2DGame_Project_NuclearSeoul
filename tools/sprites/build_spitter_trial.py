"""Slice generated key poses; use one scale, fixed foot pivot, separate emissive layer.
No character geometry is drawn here. Source is preserved alongside derived assets.
"""
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'assets/characters/previews/spitter_trial_v1'
NAMES = ('idle', 'walk_a', 'walk_b', 'windup', 'release', 'recover', 'hurt', 'down')


def main():
    src = Image.open(OUT / 'generated_keyposes.png').convert('RGBA')
    cells = [src.crop((i % 4 * src.width // 4, i // 4 * src.height // 2,
                      (i % 4 + 1) * src.width // 4, (i // 4 + 1) * src.height // 2))
             for i in range(8)]
    for im in cells:
        im.putalpha(im.getchannel('A').point(lambda a: 255 if a >= 128 else 0))
    scale = 36 / (cells[0].getbbox()[3] - cells[0].getbbox()[1])
    report = []
    for name, im in zip(NAMES, cells):
        bbox = im.getbbox()
        # One shared scale; only translate to the foot anchor (32, 58).
        crop = im.crop(bbox)
        small = crop.resize((round(crop.width * scale), round(crop.height * scale)), Image.Resampling.NEAREST)
        frame = Image.new('RGBA', (64, 64))
        frame.alpha_composite(small, (32 - small.width // 2, 58 - small.height))
        glow = Image.new('RGBA', frame.size)
        if name in ('windup', 'release'):
            for y in range(64):
                for x in range(64):
                    r, g, b, a = frame.getpixel((x, y))
                    if a and g > 70 and g > r * 1.12 and g > b * 1.6:
                        glow.putpixel((x, y), (r, g, b, a))
                        # Dull tissue under the independently drawn glow.
                        v = min(100, round((r + g + b) / 4))
                        frame.putpixel((x, y), (v, round(v * .92), round(v * .8), a))
        frame.save(OUT / f'{name}.png')
        glow.save(OUT / f'{name}_glow.png')
        report.append({'pose': name, 'bbox': frame.getbbox(), 'glow_pixels': 4096 - glow.getchannel('A').histogram()[0]})
    (OUT / 'validation.json').write_text(json.dumps({'scale': scale, 'cell': [64, 64],
        'pivot': [32, 58], 'native_idle_height': 36, 'frames': report}, indent=2), encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
