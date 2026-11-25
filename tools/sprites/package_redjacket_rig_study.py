"""Compare the original walk, AI poses, and a new costume on the original animation."""
import json
from pathlib import Path
import sys
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path(__file__).resolve().parent))
from repaint import repaint

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'assets/characters/previews/hero_redjacket_rig_v1'


def main():
    source=OUT/'renders'
    spec=json.loads((OUT/'production.json').read_text(encoding='utf-8'))
    ids=json.loads((source/'ids.json').read_text(encoding='utf-8'))
    anchors=json.loads((source/'anchors.json').read_text(encoding='utf-8'))
    records=[]
    for kind in ('body','held'):
        dest=OUT/kind;dest.mkdir(exist_ok=True)
        for i in range(6):
            im=repaint(Image.open(source/kind/'id'/f'{i}.png').convert('RGBA'),
                       Image.open(source/kind/'light'/f'{i}.png').convert('RGBA'),ids,spec['palette'],{},[110,165],
                       outline=(17,17,21,255),cleanup=True)
            bbox=im.getbbox()
            if not bbox or bbox[0]<=0 or bbox[1]<=0 or bbox[2]>=64 or bbox[3]>=64:
                raise RuntimeError((kind,i,bbox))
            im.save(dest/f'{i}.png')
            records.append({'kind':kind,'i':i,'bbox':bbox})
    images=[]
    font=lambda size:ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',size)
    old0=Image.open(ROOT/'assets/characters/hero_3d/Walking/south-east/0.png').convert('RGBA')
    old_ground=old0.getbbox()[3]
    new_ground=Image.open(OUT/'held/0.png').getbbox()[3]
    for i in range(6):
        board=Image.new('RGBA',(1050,420),(27,30,32,255));d=ImageDraw.Draw(board)
        d.text((24,16),'같은 걷기 동작 재사용 · 한 방향 비교',font=font(23),fill=(236,226,207))
        groups=[('기존 주인공',Image.open(ROOT/f'assets/characters/hero_3d/Walking/south-east/{i}.png').convert('RGBA'),(32,old_ground)),
                ('새 AI 그림 걷기',Image.open(ROOT/f'assets/characters/previews/hero_redjacket_motion_v1/walk_{i}.png').convert('RGBA'),(32,58)),
                ('기존 뼈대 + 붉은 재킷 모델',Image.open(OUT/f'held/{i}.png').convert('RGBA'),(anchors['records'][0]['ground'][0],new_ground))]
        for j,(label,im,pivot) in enumerate(groups):
            im=im.resize((im.width*5,im.height*5),Image.Resampling.NEAREST)
            x=175+j*350-round(pivot[0]*5);y=330-round(pivot[1]*5)
            board.alpha_composite(im,(x,y))
            d.text((25+j*350,65),label,font=font(17),fill=(219,216,198))
            d.line((25+j*350,330,325+j*350,330),fill=(67,76,76))
        d.text((24,368),'기존과 새 3D 모델은 Walking.fbx의 같은 6개 시간 표본 / 외형 일치는 아직 보완 필요',font=font(17),fill=(170,188,181))
        images.append(board.convert('RGB'))
    images[0].save(OUT/'walk_comparison.gif',save_all=True,append_images=images[1:],duration=100,loop=0,disposal=2)
    images[0].save(OUT/'comparison.png')
    (OUT/'validation.json').write_text(json.dumps({'frames':records,'animation':anchors,
        'scope':'one-direction walk study; original rig and original six time samples'},indent=2),encoding='utf-8')
    print('PACKAGED_RIG_COMPARISON',OUT)


if __name__=='__main__':main()
