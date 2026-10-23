from pipeline import *
from PIL import ImageDraw
def slice9(im,w,h,b):
    sw,sh=im.size;out=Image.new('RGBA',(w,h));sx=[0,b,sw-b,sw];sy=[0,b,sh-b,sh];dx=[0,b,w-b,w];dy=[0,b,h-b,h]
    for j in range(3):
        for i in range(3):
            tile=im.crop((sx[i],sy[j],sx[i+1],sy[j+1]));tile=tile.resize((dx[i+1]-dx[i],dy[j+1]-dy[j]),Image.Resampling.BICUBIC);out.paste(tile,(dx[i],dy[j]))
    return out
def run():
    for g in read(REQUEST/'INPUT_MANIFEST.json')['groups']:
        for a in g['assets']:
            if not a['id'].startswith('UI/'):continue
            p=ROOT/f"exports/Art/{a['id']}.png"
            if not p.exists():continue
            im=Image.open(p).convert('RGBA');w,h=im.size;b=48 if a['id']=='UI/card_rare' else a['border'][0];large=slice9(im,w*3,h,b)
            canvas=Image.new('RGBA',(w*3+24,h*2+66),'#1d1f24');canvas.alpha_composite(im,(12,26));canvas.alpha_composite(large,(12,h+54));d=ImageDraw.Draw(canvas);d.text((12,8),a['id']+' original',fill='white');d.text((12,h+36),'3x width / fixed corners and borders / stretched centre',fill='white');canvas.convert('RGB').save(ROOT/f"qa/nineslice_{a['id'].split('/')[1]}.png")
if __name__=='__main__':run()
