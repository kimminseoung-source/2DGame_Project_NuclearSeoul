"""Each standing block: its collision rect vs where its picture is drawn (play.draw_world)."""
import sys; sys.path.insert(0, "src")
from PIL import Image
import area, settings
from settings import DOT, ROOT, AREA_DIR

area_dir = ROOT / "assets" / AREA_DIR
seen = set()
for b, look in zip(area.BLOCKS, area.BLOCK_LOOKS):
    if look in ("building", "wall", "window") or look in seen:
        continue
    path = next((f / f"{look}.png" for f in (area.AREA_PATH, area_dir) if f is not None and (f / f"{look}.png").exists()), None)
    if path is None:
        continue
    seen.add(look)
    im = Image.open(path).convert("RGBA")
    w, h = im.width / DOT, im.height / DOT                     # drawn size in world units
    l, bb, r, t = b
    # drawn: centre x (l+r)/2, bottom at b-3 (play.draw_world)
    dl, dr, db, dt = (l + r) / 2 - w / 2, (l + r) / 2 + w / 2, bb - 3, bb - 3 + h
    # where the opaque pixels actually are inside the picture
    box = im.getchannel("A").getbbox()
    ol, oright = dl + box[0] / DOT, dl + box[2] / DOT
    otop, obot = dt - box[1] / DOT, dt - box[3] / DOT
    print(f"{look:14s} rect x {l:.0f}-{r:.0f} y {bb:.0f}-{t:.0f} ({r - l:.0f}x{t - bb:.0f}) | picture {im.width}x{im.height}px = {w:.0f}x{h:.0f} "
          f"| drawn x {dl:.0f}-{dr:.0f} y {db:.0f}-{dt:.0f} | opaque x {ol:.0f}-{oright:.0f} y {obot:.0f}-{otop:.0f}")
