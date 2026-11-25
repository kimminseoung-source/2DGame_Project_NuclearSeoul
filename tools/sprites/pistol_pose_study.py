"""Package the pistol appearance keys at a shared scale; not gameplay or weapon separation."""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'assets/characters/previews/hero_pistol_v1'


def main():
    source=Image.open(OUT/'generated_poses.png').convert('RGBA')
    cells=[source.crop((i*source.width//2,0,(i+1)*source.width//2,source.height)) for i in range(2)]
    for im in cells:im.putalpha(im.getchannel('A').point(lambda a:255 if a>=128 else 0))
    b=cells[0].getbbox();scale=36/(b[3]-b[1]);records=[]
    board=Image.new('RGB',(760,390),(27,30,32));d=ImageDraw.Draw(board)
    font=lambda size:ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',size)
    d.text((20,14),'권총 기준 자세 · 외형 확인 1차',font=font(22),fill=(235,228,211))
    for i,(name,label) in enumerate((('low_ready','낮춰 들기'),('aim','양손 조준'))):
        cell=cells[i];bbox=cell.getbbox()
        small=cell.resize((round(cell.width*scale),round(cell.height*scale)),Image.Resampling.NEAREST)
        im=Image.new('RGBA',(64,64));im.alpha_composite(small,(round(32-cell.width/2*scale),round(58-bbox[3]*scale)))
        bottom=im.getbbox()[3]
        if bottom!=58:
            shifted=Image.new('RGBA',(64,64));shifted.alpha_composite(im,(0,58-bottom));im=shifted
        box=im.getbbox();assert box and 0<box[0]<box[2]<64 and 0<box[1]<box[3]<64
        im.save(OUT/f'{name}_36px.png');records.append({'pose':name,'bbox':box})
        large=im.resize((320,320),Image.Resampling.NEAREST);board.paste(large,(30+i*380,15),large)
        d.text((45+i*380,65),label,font=font(18),fill=(222,217,200))
    d.text((20,347),'공통 배율 · 총 포함 시안 / 분리·기준점·게임 연결은 다음 단계',font=font(15),fill=(174,189,179))
    board.save(OUT/'comparison.png')
    (OUT/'validation.json').write_text(json.dumps({'cell':[64,64],'pivot':[32,58],'shared_scale':scale,
        'frames':records,'weapon_separated':False,'game_integrated':False},indent=2),encoding='utf-8')
    print('PISTOL_POSE_KEYS_PACKAGED',OUT)


if __name__=='__main__':main()
