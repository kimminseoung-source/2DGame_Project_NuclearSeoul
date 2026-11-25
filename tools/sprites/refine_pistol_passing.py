"""Sample four AI leg corrections; preserve original upper pixels and support boots."""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'assets/characters/previews/hero_pistol_gait_v4'
OUT=ART/'refinement'

def main():
    source=Image.open(OUT/'passing_edit_output.png').convert('RGBA')
    meta=json.loads((ART/'validation.json').read_text(encoding='utf-8'))['sheets']
    report=[];cells=[]
    for i in range(4):
        c=source.crop((i%2*source.width//2,i//2*source.height//2,(i%2+1)*source.width//2,(i//2+1)*source.height//2))
        c=c.resize((512,512),Image.Resampling.NEAREST)
        c.putalpha(c.getchannel('A').point(lambda a:255 if a>=128 else 0));cells.append(c)
    edited_ground=cells[0].getbbox()[3]
    for j,(g,i) in enumerate((('walk',2),('walk',6),('aim_walk',2),('aim_walk',6))):
        old=Image.open(ART/f'{g}_{i}.png').convert('RGBA');s=meta[g]['scale']
        small=cells[j].resize((round(512*s),round(512*s)),Image.Resampling.NEAREST)
        new=Image.new('RGBA',(64,64));new.alpha_composite(small,(round(32-256*s),round(58-edited_ground*s)))
        # Registered masks preserve approved arms/face and grounded boot. The swing
        # leg is AI redrawn, never a rotated or stretched original pixel limb.
        new.paste(old.crop((0,0,64,40)),(0,0));new.paste(old.crop((22,51,33,59)),(22,51))
        new.save(OUT/f'{g}_{i}.png')
        assert new.crop((0,0,64,40)).tobytes()==old.crop((0,0,64,40)).tobytes()
        assert new.crop((22,51,33,59)).tobytes()==old.crop((22,51,33,59)).tobytes()
        report.append({'key':f'{g}_{i}','upper_rows_preserved':[0,40],
                       'support_boot_preserved':[22,51,33,59],'bbox':new.getbbox(),
                       'changed_pixels':sum(a!=b for a,b in zip(new.getdata(),old.getdata()))})
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
    board=Image.new('RGB',(1024,530),(27,30,32));d=ImageDraw.Draw(board)
    for j,r in enumerate(report):
        key=r['key'];x=j%2*512;y=j//2*265
        for side,folder in enumerate((ART,OUT)):
            im=Image.open(folder/f'{key}.png').resize((256,256),Image.Resampling.NEAREST)
            board.paste(im,(x+side*256,y),im)
            d.text((x+side*256+10,y+10),key+(' before' if side==0 else ' after'),font=font,fill='white')
    board.save(OUT/'passing_comparison.png')
    (OUT/'validation.json').write_text(json.dumps({'method':'AI redraw of four swing legs; registered original upper/grounded boot masks','common_edited_ground':edited_ground,'frames':report},indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
