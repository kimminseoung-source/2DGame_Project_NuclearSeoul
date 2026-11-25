"""Shared lower-body test: two AI upper bodies, existing eight lower poses, separate pistol.
No limb rotation or character deformation; only crop/alignment/layer assembly.
"""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'assets/characters/previews/hero_pistol_shared_v2'
SEAM=42


def source_poses():
    source=Image.open(OUT/'generated_emptyhands.png').convert('RGBA')
    cells=[source.crop((i*source.width//2,0,(i+1)*source.width//2,source.height)) for i in range(2)]
    for cell in cells:cell.putalpha(cell.getchannel('A').point(lambda a:255 if a>=128 else 0))
    b=cells[0].getbbox();scale=36/(b[3]-b[1]);poses=[]
    for cell in cells:
        box=cell.getbbox()
        # Root from boots, not the upper body's changing arm bbox.
        boot=cell.crop((0,box[3]-round((box[3]-box[1])*.08),cell.width,box[3])).getbbox()
        rootx=(boot[0]+boot[2])/2
        small=cell.resize((round(cell.width*scale),round(cell.height*scale)),Image.Resampling.NEAREST)
        im=Image.new('RGBA',(64,64));im.alpha_composite(small,(round(32-rootx*scale),round(58-box[3]*scale)))
        delta=58-im.getbbox()[3]
        if delta:
            shifted=Image.new('RGBA',(64,64));shifted.alpha_composite(im,(0,delta));im=shifted
        poses.append(im)
    return poses,scale


def layer(im,top,bottom):
    result=Image.new('RGBA',(64,64));result.paste(im.crop((0,top,64,bottom)),(0,top))
    return result


def main():
    poses,scale=source_poses()
    # Keep the exact same head across arm states, not a freshly generated second head.
    poses[1].paste(poses[0].crop((0,0,64,31)),(0,0))
    upper={name:layer(im,0,SEAM) for name,im in zip(('low','aim'),poses)}
    lower_idle=layer(poses[0],SEAM,64)
    lowers=[layer(Image.open(ROOT/f'assets/characters/previews/hero_poseguided_ai_v2_twohanded/walk_{i}.png').convert('RGBA'),SEAM,64) for i in range(8)]
    lower_idle.save(OUT/'lower_idle.png')
    for name,im in upper.items():im.save(OUT/f'upper_{name}.png')
    for i,im in enumerate(lowers):im.save(OUT/f'lower_walk_{i}.png')
    pistol=Image.open(ROOT/'assets/weapons/pistol.png').convert('RGBA');pistol.save(OUT/'pistol.png')
    anchors={'low':{'grip':[34,39],'angle_clockwise':45},'aim':{'grip':[39,33],'angle_clockwise':0}}
    def weapon(name):
        data=anchors[name];gx,gy=data['grip']
        im=Image.new('RGBA',(64,64));im.alpha_composite(pistol,(gx-2,gy-2))
        return im.rotate(-data['angle_clockwise'],resample=Image.Resampling.NEAREST,center=(gx,gy))
    def compose(name,lower):
        im=lower.copy();im.alpha_composite(weapon(name));im.alpha_composite(upper[name]);return im
    stills={name:compose(name,lower_idle) for name in upper}
    walking={name:[compose(name,lo) for lo in lowers] for name in upper}
    for name,im in stills.items():im.save(OUT/f'{name}_idle.png')
    for name,ims in walking.items():
        for i,im in enumerate(ims):im.save(OUT/f'{name}_walk_{i}.png')
    # The lower layer must be identical for low and aimed states, including each moving leg.
    assert stills['low'].crop((0,47,64,64)).tobytes()==stills['aim'].crop((0,47,64,64)).tobytes()
    font=lambda size:ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',size)
    def board(left,right,title):
        im=Image.new('RGBA',(760,410),(27,30,32,255));d=ImageDraw.Draw(im)
        d.text((20,16),title,font=font(22),fill=(235,226,207))
        for j,(sprite,label) in enumerate(((left,'낮춰 들기'),(right,'팔을 들어 조준'))):
            im.alpha_composite(sprite.resize((320,320),Image.Resampling.NEAREST),(30+j*380,30))
            d.text((35+j*380,65),label,font=font(18),fill=(221,217,202))
        d.text((20,367),'같은 하체 공유 · 기존 걷는 다리 재사용 · 총은 별도 이미지',font=font(16),fill=(172,189,181))
        return im.convert('RGB')
    board(stills['low'],stills['aim'],'기본 자세 폭 축소 · 정지 하체 동일').save(OUT/'stance_comparison.png')
    frames=[board(walking['low'][i],walking['aim'][i],'이동할 때는 양쪽 모두 같은 다리가 움직임') for i in range(8)]
    frames[0].save(OUT/'walk_comparison.png')
    frames[0].save(OUT/'shared_walk.gif',save_all=True,append_images=frames[1:],duration=[70,80]*4,loop=0,disposal=2)
    hashes=[hashlib.sha256(im.tobytes()).hexdigest() for im in lowers]
    assert len(set(hashes))==8,'walking needs eight distinct lower-body pictures'
    for name,ims in walking.items():
        for i,im in enumerate(ims):
            box=im.getbbox();assert box and 0<box[0]<box[2]<64 and 0<box[1]<box[3]<64,(name,i,box)
    from PIL import ImageSequence
    cycle=sum(im.info.get('duration',0) for im in ImageSequence.Iterator(Image.open(OUT/'shared_walk.gif')))
    assert cycle==600,cycle
    def boot_width(im):
        box=im.crop((0,54,64,58)).getbbox()
        return box[2]-box[0]
    data={'scale':scale,'cell':[64,64],'seam_y':SEAM,'head_shared_rows':[0,31],
          'upper_poses':2,'idle_lower':1,'walking_lowers':8,'weapon_images':1,
          'source_walking':'hero_poseguided_ai_v2_twohanded/walk_0..7.png',
          'anchors':anchors,'same_lower_bytes_per_state':True,
          'anchors_are_preview_estimates':True,'all_16_composites_inside_canvas':True,
          'distinct_walk_lower_hashes':len(set(hashes)),'gif_cycle_ms':cycle,
          'standing_boot_span_px':{'old_aim':boot_width(Image.open(ROOT/'assets/characters/previews/hero_pistol_v1/aim_36px.png').convert('RGBA')),
                                  'new_low':boot_width(stills['low']),'new_aim':boot_width(stills['aim'])},
          'upper_layer_sha256':{n:hashlib.sha256(im.tobytes()).hexdigest() for n,im in upper.items()},
          'scope':'single-direction layer/composition study, not game-integrated; no foot-world-lock claim'}
    (OUT/'layers.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    print('SHARED_PISTOL_STUDY_READY',OUT)


if __name__=='__main__':main()
