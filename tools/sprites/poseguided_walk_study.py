"""Pose diagrams from real joint projections; package AI outputs without drawing final art."""
import json
from pathlib import Path
import sys
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'assets/characters/previews/hero_poseguided_ai_v1'


def guide():
    data=json.loads((OUT/'pose_joints.json').read_text(encoding='utf-8'))
    allpoints=[p for record in data['records'] for p in record['joints'].values()]
    miny,maxy=min(p[1] for p in allpoints),max(p[1] for p in allpoints)
    scale=350/(maxy-miny)
    board=Image.new('RGB',(1536,1024),(35,39,44));d=ImageDraw.Draw(board)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
    for i,record in enumerate(data['records']):
        ox,oy=(i%3)*512,(i//3)*512
        p={key:(ox+256+(v[0]-32)*scale,oy+90+(v[1]-miny)*scale) for key,v in record['joints'].items()}
        d.rectangle((ox,oy,ox+511,oy+511),outline=(74,79,84),width=2)
        d.text((ox+18,oy+16),f'{i+1} / Walking source frame {record["frame"]}',font=font,fill=(220,222,227))
        d.line((ox+50,oy+444,ox+462,oy+444),fill=(73,80,80),width=2)
        for side,colour in (('L',(87,166,218)),('R',(240,153,75))):
            for chain in ((side+'_shoulder',side+'_elbow',side+'_wrist'),(side+'_hip',side+'_knee',side+'_ankle',side+'_toe')):
                d.line([p[j] for j in chain],fill=colour,width=10)
                for j in chain:
                    x,y=p[j];d.ellipse((x-6,y-6,x+6,y+6),fill=colour)
        for chain in (('head','neck','chest','pelvis'),('L_shoulder','R_shoulder'),('L_hip','R_hip')):
            d.line([p[j] for j in chain],fill=(220,218,199),width=9)
        x,y=p['head'];d.ellipse((x-19,y-26,x+19,y+13),outline=(238,231,210),width=5)
    board.save(OUT/'pose_guide.png')


def package():
    source=Image.open(OUT/'generated_walk.png').convert('RGBA')
    cells=[source.crop((i%3*source.width//3,i//3*source.height//2,(i%3+1)*source.width//3,(i//3+1)*source.height//2)) for i in range(6)]
    for cell in cells:cell.putalpha(cell.getchannel('A').point(lambda a:255 if a>=128 else 0))
    box=cells[0].getbbox();scale=36/(box[3]-box[1]);records=[]
    for i,cell in enumerate(cells):
        bbox=cell.getbbox()
        small=cell.resize((round(cell.width*scale),round(cell.height*scale)),Image.Resampling.NEAREST)
        im=Image.new('RGBA',(64,64));im.alpha_composite(small,(round(32-cell.width/2*scale),round(58-bbox[3]*scale)))
        bottom=im.getbbox()[3]
        if bottom!=58:
            shifted=Image.new('RGBA',(64,64));shifted.alpha_composite(im,(0,58-bottom));im=shifted
        bounds=im.getbbox()
        assert bounds and 0<bounds[0]<bounds[2]<64 and 0<bounds[1]<bounds[3]<64,(i,bounds)
        im.save(OUT/f'walk_{i}.png');records.append({'i':i,'bbox':bounds})
    frames=[]
    font=lambda size:ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',size)
    oldfirst=Image.open(ROOT/'assets/characters/hero_3d/Walking/south-east/0.png').convert('RGBA')
    oldground=oldfirst.getbbox()[3]
    for i in range(6):
        board=Image.new('RGBA',(1050,425),(27,30,32,255));d=ImageDraw.Draw(board)
        d.text((24,16),'3D는 자세 안내만 · 최종 캐릭터는 AI 그림',font=font(23),fill=(237,225,208))
        groups=[('기존 자연스러운 동작',ROOT/f'assets/characters/hero_3d/Walking/south-east/{i}.png',oldground),
                ('앞선 AI 걷기',ROOT/f'assets/characters/previews/hero_redjacket_motion_v1/walk_{i}.png',58),
                ('3D 자세를 참고한 AI 그림',OUT/f'walk_{i}.png',58)]
        for j,(label,path,ground) in enumerate(groups):
            im=Image.open(path).convert('RGBA');im=im.resize((im.width*5,im.height*5),Image.Resampling.NEAREST)
            board.alpha_composite(im,(15+j*350,330-ground*5))
            d.text((25+j*350,67),label,font=font(17),fill=(222,218,204))
            d.line((25+j*350,330,325+j*350,330),fill=(67,76,76))
        d.text((24,375),'동일한 6개 걷기 시점 안내 / AI가 자세를 정확하게 강제 복사하는 방식은 아님',font=font(17),fill=(168,187,177))
        frames.append(board.convert('RGB'))
    frames[0].save(OUT/'comparison.png')
    frames[0].save(OUT/'walk_comparison.gif',save_all=True,append_images=frames[1:],duration=100,loop=0,disposal=2)
    (OUT/'validation.json').write_text(json.dumps({'shared_scale':scale,'frames':records,
        'scope':'pose-reference AI drawing; one-direction six-frame study; not integrated'},indent=2),encoding='utf-8')


if __name__=='__main__':
    guide() if '--guide' in sys.argv else package()
