"""Crop and consistently sample AI artwork. No final character is drawn or warped here."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'assets/characters/previews/hero_pistol_gait_v4'

def extract(filename):
    src=Image.open(OUT/filename).convert('RGBA');cells=[]
    for i in range(8):
        c=src.crop((i%4*src.width//4,i//4*src.height//2,(i%4+1)*src.width//4,(i//4+1)*src.height//2))
        c=c.resize((512,512),Image.Resampling.NEAREST)
        c.putalpha(c.getchannel('A').point(lambda a:255 if a>=128 else 0));cells.append(c)
    box=cells[0].getbbox();scale=36/(box[3]-box[1]);ground=box[3]
    frames=[]
    for c in cells:
        im=Image.new('RGBA',(64,64));small=c.resize((round(512*scale),round(512*scale)),Image.Resampling.NEAREST)
        im.alpha_composite(small,(round(32-256*scale),round(58-ground*scale)));frames.append(im)
    return frames,{'source':filename,'scale':scale,'source_ground':ground,'bboxes':[im.getbbox() for im in frames]}

def main():
    report={};allframes={};muzzles={}
    for name,filename in (('walk','generated_walk.png'),('aim_walk','generated_aimwalk.png')):
        frames,report[name]=extract(filename)
        for i,im in enumerate(frames):
            key=f'{name}_{i}';box=im.getbbox();assert box and 0<box[0]<box[2]<64 and 0<box[1]<box[3]<64
            im.save(OUT/f'{key}.png');allframes[key]=im
            # Every firing origin is phase-specific, including a low-ready -> release shot.
            grey=[]
            for y in range(24,43):
                for x in range(34,49):
                    r,g,b,a=im.getpixel((x,y))
                    if a and r>65 and abs(r-g)<18 and abs(g-b)<18:grey.append((x,y))
            assert grey,key
            front=max(x for x,y in grey);ys=[y for x,y in grey if x==front]
            muzzles[key]=[front+.5,sum(ys)/len(ys)+.5]
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
    board=Image.new('RGB',(1280,550),(27,30,32));draw=ImageDraw.Draw(board)
    for row,g in enumerate(('walk','aim_walk')):
        for i in range(8):
            # 2x actual pixel sampling, plus labels for visual contact/identity review.
            im=allframes[f'{g}_{i}'].resize((160,160),Image.Resampling.NEAREST)
            board.paste(im,(i*160,row*270+40),im)
            draw.text((i*160+12,row*270+15),f'{g} {i}',font=font,fill='white')
            draw.line((i*160+8,row*270+185,i*160+151,row*270+185),fill=(83,90,90))
    board.save(OUT/'frame_board.png')
    preview=[]
    for i in range(8):
        frame=Image.new('RGB',(520,330),(27,30,32));d=ImageDraw.Draw(frame)
        for col,g in enumerate(('walk','aim_walk')):
            im=allframes[f'{g}_{i}'].resize((256,256),Image.Resampling.NEAREST)
            frame.paste(im,(col*260,25),im);d.text((col*260+15,15),g,font=font,fill='white')
        preview.append(frame)
    preview[0].save(OUT/'motion_preview.gif',save_all=True,append_images=preview[1:],duration=80,loop=0)
    (OUT/'muzzles.json').write_text(json.dumps({'method':'front grey barrel pixel, per full-body phase; side-view only','points':muzzles},indent=2),encoding='utf-8')
    (OUT/'validation.json').write_text(json.dumps({'cell':[64,64],'body_height_reference':36,'walk_keys':8,'aim_walk_keys':8,'per_frame_scale_or_ground_snap':False,'sheets':report},indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
