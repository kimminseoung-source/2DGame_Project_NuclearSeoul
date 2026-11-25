"""Draw joint-reference diagrams, never final character art. Original 3D stays untouched."""
import json, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'assets/characters/previews/hero_pistol_gait_v4'

def clear_ground_guide():
    """Explicit contact design over the rig study: analytical IK is only a drawing guide."""
    im=Image.new('RGB',(1536,832),(27,30,32));d=ImageDraw.Draw(im)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    d.text((15,8),'DESIGNED CONTACT STUDY | blue NEAR leg, orange FAR leg | opposite contact at 0 / 4',font=font,fill='white')
    xs=(8,4,0,-4,-8,-5,0,5);lift=(0,0,0,0,0,3,6,3)
    names=('near CONTACT','near LOAD','far PASS','far REACH','far CONTACT','far LOAD','near PASS','near REACH')
    records=[]
    for i in range(8):
        ox=i%4*384;oy=40+i//4*384
        bob=(0,1,0,-1,0,1,0,-1)[i]
        joints={}
        for side,offset,col in (('far',4,(238,149,69)),('near',0,(70,156,241))):
            phase=(i+offset)%8;hy=39+bob;hx=32+(-1 if side=='far' else 1)
            fx=32+xs[phase];fy=58-(2 if side=='far' else 0)-lift[phase]
            dx,dy=fx-hx,fy-hy;dist=math.hypot(dx,dy)
            # Equal 11px bones, intersection choosing the knee forward of the hip.
            midx,midy=(hx+fx)/2,(hy+fy)/2;h=math.sqrt(max(0,11**2-(dist/2)**2))
            kx,ky=midx+dy/dist*h,midy-dx/dist*h
            pts=[(hx,hy),(kx,ky),(fx,fy),(fx+3,fy)]
            joints[side]=pts
            screen=[(ox+25+x*5.2,oy+y*5.2) for x,y in pts]
            d.line(screen,fill=col,width=15)
            for x,y in screen[:-1]:d.ellipse((x-7,y-7,x+7,y+7),fill=col)
        d.line((ox+32*5.2+25,oy+(39+bob)*5.2,ox+32*5.2+25,oy+(27+bob)*5.2),fill=(195,195,180),width=30)
        cx=ox+32*5.2+25;cy=oy+(23+bob)*5.2
        d.ellipse((cx-15,cy-18,cx+15,cy+12),fill=(195,195,180))
        d.line((ox+20,oy+58*5.2+9,ox+360,oy+58*5.2+9),fill=(100,105,105),width=1)
        d.text((ox+24,oy+339),f'{i} {names[i]}',font=font,fill='white')
        records.append({'phase':i/8,'name':names[i],'joints':joints,'bob':bob})
    im.save(OUT/'contact_guide.png')
    (OUT/'designed_contacts.json').write_text(json.dumps({'note':'Designed ground-contact IK schematic after reviewing source 3D guide. Not actual captured rig or final art. Near/far foot ground planes differ by 2px for perspective.','records':records},indent=2),encoding='utf-8')

def main():
    raw=json.loads((OUT/'pose_joints.json').read_text(encoding='utf-8'))
    # Review of projected ankle/toe paths: frame 6 and frame 24 are opposite contacts.
    # Shift phase only; keep the sampled source poses and their true L/R bone identities.
    records=raw['records'][1:]+raw['records'][:1]
    labels=('L contact','L load','R pass','R swing','R contact','R load','L pass','L swing')
    board=Image.new('RGB',(1536,832),(27,30,32));d=ImageDraw.Draw(board)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
    d.text((18,8),'POSE REFERENCE ONLY | blue = anatomical L | orange = anatomical R | 3D legs, designed gun arms',font=font,fill='white')
    guides=[]
    for i,r in enumerate(records):
        j={k:[v[0]-r['joints']['pelvis'][0]+32,v[1]+6] for k,v in r['joints'].items()}
        guides.append({'source_frame':r['frame'],'phase':i/8,'label':labels[i],'joints':j})
        for row in range(2):
            ox=i%4*384;oy=40+(i//4)*384
            if row: continue
            def point(name):return (ox+j[name][0]*5.4+18,oy+j[name][1]*5.4)
            d.line((ox+25,oy+319,ox+355,oy+319),fill=(105,109,110),width=1)
            for side,col in (('L',(75,154,242)),('R',(243,153,74))):
                for a,b in (('hip','knee'),('knee','ankle'),('ankle','toe')):
                    d.line((point(f'{side}_{a}'),point(f'{side}_{b}')),fill=col,width=9)
                for name in ('hip','knee','ankle','toe'):
                    x,y=point(f'{side}_{name}');d.ellipse((x-4,y-4,x+4,y+4),fill=col)
            for a,b in (('pelvis','chest'),('chest','neck'),('neck','head')):
                d.line((point(a),point(b)),fill=(205,206,197),width=13)
            x,y=point('head');d.ellipse((x-11,y-14,x+11,y+8),fill=(205,206,197))
            # Purpose-designed two-hand aim; these arms are not a solved original rig pose.
            cx,cy=j['chest'];shoulder=(cx,cy-2);elbow=(cx+6,cy+1);hand=(cx+11,cy-2)
            pts=[(ox+x*5.4+18,oy+y*5.4) for x,y in (shoulder,elbow,hand)]
            d.line(pts,fill=(194,187,174),width=7)
            d.text((ox+22,oy+343),f'{i}: {labels[i]} / FBX {r["frame"]}',font=font,fill='white')
    board.save(OUT/'pose_guide.png')
    (OUT/'gait_reference.json').write_text(json.dumps({'source':raw['source'],'note':'8 sampled 3D poses reordered after joint review; arms are design only, contact labels approximate; not final foot IK','records':guides},indent=2),encoding='utf-8')
    print(OUT/'pose_guide.png')
    clear_ground_guide()

if __name__=='__main__':main()
