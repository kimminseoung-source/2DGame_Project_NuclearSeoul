"""Design a two-hand sword guide over actual 3D walk legs, then package AI output."""
import json,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'assets/characters/previews/hero_poseguided_ai_v2_twohanded'


def guide():
    data=json.loads((OUT/'pose_joints.json').read_text(encoding='utf-8'))
    base=data['records'][0]['joints'];records=[]
    for source in data['records']:
        joints=dict(source['joints'])
        dy=max(-.25,min(.25,joints['pelvis'][1]-base['pelvis'][1]))
        for name in ('head','neck','chest','L_shoulder','R_shoulder'):
            joints[name]=[base[name][0],base[name][1]+dy]
        for name,point in {'L_elbow':[37.,30.2],'L_wrist':[35.5,34.2],
                           'R_elbow':[28.8,32.3],'R_wrist':[34.2,35.5]}.items():
            joints[name]=[point[0],point[1]+dy]
        records.append({'frame':source['frame'],'joints':joints,
                        'sword_grip':[34.2,35.5+dy],'sword_guard':[36.3,33.4+dy],'sword_tip':[48.,21.7+dy]})
    # Fixed orthographic projected coordinates; keep the sword in the user's up-right direction.
    scale=10.;miny=17.;board=Image.new('RGB',(2048,1024),(35,39,44));d=ImageDraw.Draw(board)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
    for i,r in enumerate(records):
        ox,oy=i%4*512,i//4*512
        point=lambda p:(ox+256+(p[0]-32)*scale,oy+80+(p[1]-miny)*scale)
        p={name:point(v) for name,v in r['joints'].items()}
        d.rectangle((ox,oy,ox+511,oy+511),outline=(70,77,82),width=2)
        d.text((ox+18,oy+18),f'{i+1} / same two-hand guard',font=font,fill=(225,225,217))
        for side,col in (('L',(91,166,216)),('R',(241,153,73))):
            for chain in ((side+'_shoulder',side+'_elbow',side+'_wrist'),(side+'_hip',side+'_knee',side+'_ankle',side+'_toe')):
                d.line([p[n] for n in chain],fill=col,width=9)
                for name in chain:
                    x,y=p[name];d.ellipse((x-5,y-5,x+5,y+5),fill=col)
        for chain in (('head','neck','chest','pelvis'),('L_shoulder','R_shoulder'),('L_hip','R_hip')):
            d.line([p[n] for n in chain],fill=(220,215,198),width=8)
        x,y=p['head'];d.ellipse((x-18,y-25,x+18,y+13),outline=(239,232,213),width=5)
        d.line((point(r['sword_grip']),point(r['sword_guard'])),fill=(181,135,92),width=12)
        d.line((point(r['sword_guard']),point(r['sword_tip'])),fill=(191,230,204),width=9)
    board.save(OUT/'twohand_guide.png')
    (OUT/'designed_pose_joints.json').write_text(json.dumps({'note':'original 3D legs; designed stable upper body and two-hand grip; not unmodified 3D pose',
        'records':records},indent=2),encoding='utf-8')


def package():
    source=Image.open(OUT/'generated_walk.png').convert('RGBA')
    cells=[source.crop((i%4*source.width//4,i//4*source.height//2,(i%4+1)*source.width//4,(i//4+1)*source.height//2)) for i in range(8)]
    for im in cells:im.putalpha(im.getchannel('A').point(lambda a:255 if a>=128 else 0))
    b=cells[0].getbbox();scale=36/(b[3]-b[1]);records=[]
    for i,cell in enumerate(cells):
        bbox=cell.getbbox();small=cell.resize((round(cell.width*scale),round(cell.height*scale)),Image.Resampling.NEAREST)
        im=Image.new('RGBA',(64,64));im.alpha_composite(small,(round(32-cell.width/2*scale),round(58-bbox[3]*scale)))
        bottom=im.getbbox()[3]
        if bottom!=58:
            shifted=Image.new('RGBA',(64,64));shifted.alpha_composite(im,(0,58-bottom));im=shifted
        bounds=im.getbbox();assert bounds and 0<bounds[0]<bounds[2]<64 and 0<bounds[1]<bounds[3]<64,(i,bounds)
        im.save(OUT/f'walk_{i}.png');records.append({'i':i,'bbox':bounds})
    font=lambda size:ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',size)
    # Equal 600ms cycles: 24 common time steps compare 6-frame and 8-frame results fairly.
    comparison=[];solo=[]
    for n in range(24):
        oldi=n*6//24;newi=n*8//24
        board=Image.new('RGBA',(760,410),(27,30,32,255));d=ImageDraw.Draw(board)
        d.text((20,16),'걷기 보완 · 양손으로 검을 오른쪽 위로',font=font(22),fill=(235,228,212))
        for col,(label,path) in enumerate((('이전 · 한손 걷기',ROOT/f'assets/characters/previews/hero_poseguided_ai_v1/walk_{oldi}.png'),
                                          ('수정 · 양손 준비 자세',OUT/f'walk_{newi}.png'))):
            im=Image.open(path).convert('RGBA').resize((320,320),Image.Resampling.NEAREST)
            board.alpha_composite(im,(30+col*380,30))
            d.text((35+col*380,65),label,font=font(18),fill=(222,216,200))
        d.text((20,365),'같은 0.6초 주기 / AI 그림 / 한 방향 시험',font=font(17),fill=(169,188,179))
        comparison.append(board.convert('RGB'))
    for i in range(8):
        bg=Image.new('RGBA',(64,64),(27,30,32,255));bg.alpha_composite(Image.open(OUT/f'walk_{i}.png').convert('RGBA'))
        solo.append(bg.convert('RGB').resize((384,384),Image.Resampling.NEAREST))
    comparison[0].save(OUT/'comparison.png')
    # GIF uses 10ms timing units. Alternating 20/30 preserves an exact 600ms common cycle.
    comparison[0].save(OUT/'comparison.gif',save_all=True,append_images=comparison[1:],duration=[20,30]*12,loop=0,disposal=2)
    solo[0].save(OUT/'walk.gif',save_all=True,append_images=solo[1:],duration=[70,80]*4,loop=0,disposal=2)
    solo[0].save(OUT/'walk_slow.gif',save_all=True,append_images=solo[1:],duration=150,loop=0,disposal=2)
    from PIL import ImageSequence
    durations={name:sum(frame.info.get('duration',0) for frame in ImageSequence.Iterator(Image.open(OUT/name)))
               for name in ('comparison.gif','walk.gif','walk_slow.gif')}
    assert durations['comparison.gif']==durations['walk.gif']==600,durations
    (OUT/'validation.json').write_text(json.dumps({'scale':scale,'cell':[64,64],'pivot':[32,58],'gif_cycle_ms':durations,
        'frames':records,'scope':'one-direction two-hand AI appearance study, not integrated'},indent=2),encoding='utf-8')


if __name__=='__main__':guide() if '--guide' in sys.argv else package()
