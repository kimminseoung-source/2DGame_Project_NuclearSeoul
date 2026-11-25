"""Full-body keys at one virtual cell scale. No torso/leg splicing or limb deformation."""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'assets/characters/previews/hero_pistol_flow_v3'
KEYS=('low','raise','aim','recoil','settle','hurt','fall','down')


def cells(name,rows):
    im=Image.open(OUT/name).convert('RGBA');result=[]
    for i in range(rows*4):
        left,right=i%4*im.width//4,(i%4+1)*im.width//4
        nominal_width=right-left
        pad=32 if name=='generated_keys.png' and i==7 else 0
        cell=im.crop((left-pad,i//4*im.height//rows,right+pad,(i//4+1)*im.height//rows))
        cell.putalpha(cell.getchannel('A').point(lambda a:255 if a>=128 else 0))
        # Drop detached neighbour-cell flecks, not connected parts of the character.
        if name=='generated_keys.png' and i in (6,7):
            points={(x,y) for y in range(cell.height) for x in range(cell.width) if cell.getpixel((x,y))[3]}
            components=[]
            while points:
                start=points.pop();stack=[start];component=[start]
                while stack:
                    x,y=stack.pop()
                    for q in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                        if q in points:points.remove(q);stack.append(q);component.append(q)
                components.append(component)
            largest=max(components,key=len)
            for component in components:
                if component is not largest and len(component)<len(largest)*.05:
                    for point in component:cell.putpixel(point,(0,0,0,0))
        result.append(cell.resize((round(cell.width*512/nominal_width),512),Image.Resampling.NEAREST))
    return result


def main():
    keys=cells('generated_keys.png',2);walk=cells('generated_walk_8.png',2)
    bbox=keys[0].getbbox();scale=36/(bbox[3]-bbox[1]);ground=bbox[3]
    named=list(zip(KEYS,keys))+[(f'walk_{i}',im) for i,im in enumerate(walk[:4])]+[(f'aim_walk_{i}',im) for i,im in enumerate(walk[4:])]
    report=[];frames={}
    for name,im in named:
        box=im.getbbox();small=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST)
        final=Image.new('RGBA',(64,64));final.alpha_composite(small,(round(32-im.width/2*scale),round(58-ground*scale)))
        dest=final.getbbox();assert dest and 0<dest[0]<dest[2]<64 and 0<dest[1]<dest[3]<64,(name,dest)
        final.save(OUT/f'{name}.png');frames[name]=final
        report.append({'pose':name,'source_bbox':box,'bbox':dest,'height':dest[3]-dest[1]})
    font=lambda s:ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',s)
    previews=[]
    for i in range(4):
        board=Image.new('RGBA',(1080,395),(27,30,32,255));d=ImageDraw.Draw(board)
        d.text((20,15),'전신 흐름 C · 일반 이동 / 짧은 조준 이동 / 멈춰 버티기',font=font(21),fill=(234,227,213))
        for j,(key,label) in enumerate(((f'walk_{i}','일반 걷기'),(f'aim_walk_{i}','조준 걷기'),('aim','정지 조준'))):
            im=frames[key].resize((320,320),Image.Resampling.NEAREST);board.alpha_composite(im,(20+j*350,15))
            d.text((35+j*350,65),label,font=font(18),fill=(222,217,204))
        d.text((20,355),'전신 그림 사용 · 허리 합성 없음 · 발 교대 핵심 자세 4장 / 게임 전환은 별도 시간 처리',font=font(15),fill=(169,187,177))
        previews.append(board.convert('RGB'))
    previews[0].save(OUT/'motion_board.png')
    previews[0].save(OUT/'motion_preview.gif',save_all=True,append_images=previews[1:],duration=150,loop=0,disposal=2)
    muzzles={}
    for name in ('aim','recoil','settle')+tuple(f'aim_walk_{i}' for i in range(4)):
        im=frames[name]
        grey=[]
        for y in range(25,36):
            for x in range(34,49):
                r,g,b,a=im.getpixel((x,y))
                if a>128 and r>65 and abs(r-g)<20 and abs(g-b)<20:grey.append((x,y))
        assert grey,name
        mx=max(p[0] for p in grey);ys=[y for x,y in grey if x==mx]
        muzzles[name]=[mx+.5,sum(ys)/len(ys)+.5]
    (OUT/'muzzles.json').write_text(json.dumps({'method':'furthest forward grey barrel pixels in chest region, side-view pilot only','points':muzzles},indent=2),encoding='utf-8')
    (OUT/'validation.json').write_text(json.dumps({'cell':[64,64],'fixed_ground':[32,58],
        'virtual_source_cell':[512,512],'common_scale':scale,'source_ground_y':ground,'poses':report,
        'no_per_frame_bbox_scaling_or_floor_alignment':True,'walk_keys':4,'aim_walk_keys':4,
        'scope':'full-body AI art reference guided; one direction mirrored; weapon baked for motion-quality pilot'},indent=2),encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':main()
