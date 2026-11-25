"""Compose one existing head layer at neck anchors. No generation, limb warping or body scale changes."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'assets/characters/previews/hero_pistol_gait_v4'
STATES=ROOT/'assets/characters/previews/hero_pistol_flow_v3'
OUT=ART/'identity'
CANON_ROWS={22:(29,33),23:(28,34),24:(27,35),25:(27,36),26:(26,36),27:(27,36),28:(28,34),29:(29,34),30:(30,32)}
OLD_HEAD_ROWS={
    'low':{28:(32,35),29:(32,34),30:(32,35)},
    'raise':{28:(31,35),29:(31,35),30:(32,35)},
    'aim':{28:(30,35),29:(30,35),30:(30,35),31:(31,34)},
    'recoil':{28:(30,34),29:(29,34),30:(30,34)},
    'settle':{28:(30,35),29:(30,35),30:(31,34)},
    'hurt':{28:(23,30),29:(24,30),30:(25,29)}}

def main():
    OUT.mkdir(exist_ok=True);(OUT/'refinement').mkdir(exist_ok=True)
    original=Image.open(ART/'walk_0.png').convert('RGBA')
    head=Image.new('RGBA',(10,9))
    for y,(left,right) in CANON_ROWS.items():
        for x in range(left,right):head.putpixel((x-26,y-22),original.getpixel((x,y)))
    head.save(OUT/'head.png');digest=hashlib.sha256(head.tobytes()).hexdigest()
    anchors={'low':(33,30),'raise':(33,30),'aim':(32,31),'recoil':(31,30),'settle':(32,30),'hurt':(27,30)}
    sources=[(name,STATES/f'{name}.png',anchor) for name,anchor in anchors.items()]
    for gait in ('walk','aim_walk'):
        sources.extend((f'{gait}_{i}',ART/f'{gait}_{i}.png',(31,30)) for i in range(8))
        sources.extend((f'refinement/{gait}_{i}',ART/'refinement'/f'{gait}_{i}.png',(31,30)) for i in (2,6))
    records=[]
    for name,path,(nx,ny) in sources:
        im=Image.open(path).convert('RGBA');body=im.copy()
        # Explicit head/neck masks avoid erasing the raised arms beside the chin.
        # No other upright asset reaches above row28; the lower masks were reviewed
        # on the enlarged native-pixel head region grid.
        rows=OLD_HEAD_ROWS.get(name,{28:(28,35),29:(29,34),30:(30,33)})
        for y in range(28):
            for x in range(64):body.putpixel((x,y),(0,0,0,0))
        for y,(left,right) in rows.items():
            for x in range(left,right):body.putpixel((x,y),(0,0,0,0))
        target=(nx-5,ny-8);body.alpha_composite(head,target)
        body.save(OUT/f'{name}.png')
        # Every nontransparent head pixel is identical after translation to its anchor.
        recovered=Image.new('RGBA',head.size)
        for y in range(head.height):
            for x in range(head.width):
                if head.getpixel((x,y))[3]:recovered.putpixel((x,y),body.getpixel((target[0]+x,target[1]+y)))
        assert recovered.tobytes()==head.tobytes(),name
        # Motion-defining lower body must remain untouched.
        assert im.crop((0,32,64,64)).tobytes()==body.crop((0,32,64,64)).tobytes(),name
        if name=='aim':assert im.crop((35,31,45,32)).tobytes()==body.crop((35,31,45,32)).tobytes()
        records.append({'key':name,'source':str(path.relative_to(ROOT)),'neck_anchor':[nx,ny],
                        'head_top_left':list(target),'shared_head_sha256':digest})
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    names=('low','aim','walk_0','walk_2','aim_walk_0')
    board=Image.new('RGB',(1000,400),(27,30,32));d=ImageDraw.Draw(board)
    for i,name in enumerate(names):
        im=Image.open(OUT/f'{name}.png');big=im.resize((192,192),Image.Resampling.NEAREST)
        board.paste(big,(i*200,35),big);d.text((i*200+10,8),name,font=font,fill='white')
        record=next(r for r in records if r['key']==name);x,y=record['head_top_left']
        h=im.crop((x-1,y,x+11,y+10)).resize((120,100),Image.Resampling.NEAREST)
        board.paste(h,(i*200+35,250),h)
    board.save(OUT/'head_comparison.png')
    (OUT/'validation.json').write_text(json.dumps({'canonical_source':'walk_0.png','head_size':[10,9],
        'canonical_neck':[31,30],'shared_head_sha256':digest,'records':records,
        'scope':'same-view upright keys only; fall/down keep their original angled artwork; original A/B/C assets untouched'},indent=2),encoding='utf-8')
    print('SHARED_HEAD',len(records),digest)

if __name__=='__main__':main()
