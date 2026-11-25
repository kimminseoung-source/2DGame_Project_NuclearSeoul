"""Slice generated motion keys at one scale with a boot-based ground pivot.
This is asset postprocessing, not drawing or deforming a character in code.
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'assets/characters/previews/hero_redjacket_motion_v1'
NAMES = tuple(f'walk_{i}' for i in range(6)) + ('windup', 'impact', 'recover')


def clean(im, largest_only=False):
    im = im.convert('RGBA')
    im.putalpha(im.getchannel('A').point(lambda a: 255 if a >= 128 else 0))
    # Remove tiny detached generation flecks without altering connected body or sword.
    seen, components = set(), []
    mask = im.getchannel('A')
    for y in range(im.height):
        for x in range(im.width):
            if (x,y) in seen or not mask.getpixel((x,y)):
                continue
            component, stack = [], [(x,y)]
            seen.add((x,y))
            while stack:
                px,py = stack.pop();component.append((px,py))
                for qx,qy in ((px-1,py),(px+1,py),(px,py-1),(px,py+1)):
                    if 0 <= qx < im.width and 0 <= qy < im.height and (qx,qy) not in seen and mask.getpixel((qx,qy)):
                        seen.add((qx,qy));stack.append((qx,qy))
            components.append(component)
    biggest = max(components, key=len)
    for component in components:
            if len(component) < 12 or (largest_only and component is not biggest):
                for point in component:im.putpixel(point,(0,0,0,0))
    return im


def boot_anchor(im):
    box = im.getbbox()
    bottom = box[3]
    band = max(3, round((box[3]-box[1]) * .07))
    xs = [x for y in range(bottom-band,bottom) for x in range(box[0],box[2]) if im.getpixel((x,y))[3]]
    return (min(xs)+max(xs))/2, bottom


def bake(im, scale, name):
    foot = boot_anchor(im)
    # Generated cells share a body root. Never re-centre each sword/body bbox or each stepping foot.
    anchor = (im.width/2, foot[1])
    small = im.resize((round(im.width*scale),round(im.height*scale)), Image.Resampling.NEAREST)
    x, y = round(32-anchor[0]*scale), round(58-anchor[1]*scale)
    dest = Image.new('RGBA',(64,64))
    dest.alpha_composite(small,(x,y))
    low = dest.getbbox()[3]
    if low != 58:
        shifted = Image.new('RGBA',(64,64));shifted.alpha_composite(dest,(0,58-low));dest=shifted
    bbox = dest.getbbox()
    assert bbox and 0 < bbox[0] < bbox[2] < 64 and 0 < bbox[1] < bbox[3] < 64, (name,bbox)
    dest.save(OUT/f'{name}.png')
    return {'pose':name,'source_bbox':im.getbbox(),'source_ground':anchor,'observed_boot_midpoint':foot,
            'bbox':bbox,'scale':scale,'pivot':[32,58]}


def previews():
    frames = {name:Image.open(OUT/f'{name}.png').convert('RGBA') for name in NAMES}
    def bg(im):
        b = Image.new('RGBA',(64,64),(28,31,34,255));b.alpha_composite(im)
        return b.convert('RGB').resize((320,320),Image.Resampling.NEAREST)
    walk = [bg(frames[f'walk_{i}']) for i in range(6)]
    walk[0].save(OUT/'walk.gif',save_all=True,append_images=walk[1:],duration=100,loop=0,disposal=2)
    attack = [bg(frames[n]) for n in ('windup','impact','recover')]
    attack[0].save(OUT/'attack.gif',save_all=True,append_images=attack[1:],duration=[260,120,180],loop=0,disposal=2)
    board = Image.new('RGB',(960,710),(28,31,34));d=ImageDraw.Draw(board)
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
    for i,name in enumerate(NAMES):
        pic=frames[name].resize((256,256),Image.Resampling.NEAREST)
        col,row=i%3,i//3
        board.paste(pic,(col*320+32,row*230-20),pic)
        d.text((col*320+36,row*230+204),name,fill=(228,220,202),font=font)
    board.save(OUT/'motion_board.png')


def main():
    src = Image.open(OUT/'generated_motion.png').convert('RGBA')
    cells = []
    for i in range(9):
        # Windup's sword extends above its nominal grid row: preserve that source area.
        top = i//3*src.height//3 - (32 if i == 6 else 0)
        cell = src.crop((i%3*src.width//3,top,(i%3+1)*src.width//3,(i//3+1)*src.height//3))
        cells.append(clean(cell,largest_only=i==6))
    box=cells[0].getbbox();scale=36/(box[3]-box[1])
    records=[bake(im,scale,name) for name,im in zip(NAMES,cells)]
    old=Image.open(ROOT/'assets/characters/previews/hero_redjacket_v1/generated_poses.png').convert('RGBA')
    oldcells=[clean(old.crop((i*old.width//2,0,(i+1)*old.width//2,old.height))) for i in range(2)]
    oldbox=oldcells[0].getbbox();oldscale=36/(oldbox[3]-oldbox[1])
    records += [bake(im,oldscale,name) for name,im in zip(('idle','guard'),oldcells)]
    (OUT/'validation.json').write_text(json.dumps({'cell':[64,64],'pivot':[32,58],
        'walk_cycle_world':64,'new_motion_shared_scale':scale,'records':records},indent=2),encoding='utf-8')
    previews();print(json.dumps(records))


if __name__=='__main__':main()
