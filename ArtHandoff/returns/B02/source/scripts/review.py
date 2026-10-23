"""Offline review sheets at actual unit display scale; no art is authored here."""
from pipeline import *
from PIL import ImageDraw, ImageFont, ImageOps
def main():
    d=read(ROOT/'DELIVERABLE_MANIFEST.json');items=[a for a in d['assets'] if a['status']=='delivered' and a['id'].startswith('Heroes/')]
    for h in (1440,1080,720):
        w=round(h*16/9);canvas=round(h*2/15);cw=w//10;ch=(h-60)//6
        for mode in ('colour','gray','silhouette'):
            out=Image.new('RGB',(w,h),(25,30,42));draw=ImageDraw.Draw(out)
            draw.text((12,12),f'B02 / {h}p / {mode} / OFFLINE REVIEW - NOT A UNITY SCREENSHOT',fill='white')
            for i,a in enumerate(items):
                im=Image.open(ROOT/a['export']).convert('RGBA');alpha=im.getchannel('A')
                if mode=='gray':im=ImageOps.grayscale(im).convert('RGBA');im.putalpha(alpha)
                if mode=='silhouette':im=Image.new('RGBA',im.size,(230,235,245,0));im.putalpha(alpha)
                im=im.resize((canvas,canvas),Image.Resampling.LANCZOS)
                x=(i%10)*cw+(cw-canvas)//2;y=42+(i//10)*ch
                out.paste(im,(x,y),im)
                draw.text(((i%10)*cw+3,y+canvas+1),a['id'].split('/')[1],fill=(210,215,225))
            out.save(ROOT/f'previews/roster_{mode}_{h}p.png')
    fs=[a for a in items if (ROOT/a['source']).exists()]
    out=Image.new('RGB',(1600,((len(fs)+7)//8)*224),(25,30,42));draw=ImageDraw.Draw(out)
    for i,a in enumerate(fs):
        im=Image.open(ROOT/a['source']).convert('RGBA').resize((200,200),Image.Resampling.LANCZOS)
        x=(i%8)*200;y=(i//8)*224;out.paste(im,(x,y),im);draw.text((x,y+201),a['id'].split('/')[1],fill='white')
    out.save(ROOT/'_work/final_sources_contact.png')
if __name__=='__main__':main()
