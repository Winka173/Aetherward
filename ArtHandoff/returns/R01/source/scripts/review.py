"""Offline sprite contact sheets and measurements; no generated artwork."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy.ndimage import binary_erosion

ROOT=Path(__file__).resolve().parents[2]
REPO=ROOT.parents[2]
OUT=ROOT/'previews';OUT.mkdir(exist_ok=True)
manifest=json.loads((ROOT/'DELIVERABLE_MANIFEST.json').read_text(encoding='utf-8'))
entries=[x for x in manifest['assets'] if x['status']=='delivered']
bg=Image.open(REPO/'ArtHandoff/requests/R01/references/battlefield_toon_verdant.png').convert('RGB')
rows=[]
for item in entries:
    im=Image.open(ROOT/item['export']).convert('RGBA'); ar=np.array(im); m=ar[:,:,3]>128
    yy,xx=np.where(m); ed=m&~binary_erosion(m,iterations=3)
    row=dict(id=item['id'],size=list(im.size),bounds=[int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())],edgeLuminance=float((ar[:,:,:3]/255@np.array([.2126,.7152,.0722]))[ed].mean()),transparentPixels=int((ar[:,:,3]==0).sum()))
    if '_walk_' in item['id'] or item['id'].endswith('_b'):
        base=item['id'].rsplit('_walk_',1)[0]+'_idle' if '_walk_' in item['id'] else item['id'][:-1]+'a'
        f=ROOT/'exports/Art'/f'{base}.png'
        if f.exists():
            other=np.array(Image.open(f))[:,:,3]>128
            row['silhouetteIoU']=float((m&other).sum()/(m|other).sum())
    rows.append(row)
for mode in ['colour','grayscale','silhouette']:
    width=1280;cw,ch=160,200; nr=max(1,(len(entries)+7)//8)
    sheet=Image.new('RGB',(width,nr*ch+40),(33,25,43));d=ImageDraw.Draw(sheet)
    d.text((12,12),'R01 OFFLINE COMPOSITE / '+mode+' / generated returns only',fill='white')
    for i,item in enumerate(entries):
        x=(i%8)*cw;y=(i//8)*ch+40
        tile=bg.crop((600,400,1000,800)).resize((cw,ch))
        im=Image.open(ROOT/item['export']).convert('RGBA')
        im.thumbnail((154,154),Image.Resampling.LANCZOS)
        if mode=='grayscale':
            a=im.getchannel('A'); im=ImageOps.grayscale(im).convert('RGBA');im.putalpha(a)
        if mode=='silhouette':
            a=im.getchannel('A');im=Image.new('RGBA',im.size,(15,9,25));im.putalpha(a)
        tile.paste(im,((cw-im.width)//2,8),im)
        sheet.paste(tile,(x,y));d.text((x+3,y+170),item['id'].split('/')[-1][:25],fill='white')
    sheet.save(OUT/f'{mode}_sheet.png')
    for height in [1080,720]:
        width=round(height*16/9)
        fitted=sheet.copy();fitted.thumbnail((width,height),Image.Resampling.LANCZOS)
        canvas=Image.new('RGB',(width,height),(33,25,43))
        canvas.paste(fitted,((width-fitted.width)//2,(height-fitted.height)//2))
        canvas.save(OUT/f'{mode}_sheet_{height}p.png')
(ROOT/'qa/measurements.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(reviewed=len(rows),
    inkFailures=[dict(id=r['id'],value=round(r['edgeLuminance'],3)) for r in rows if not r['id'].startswith('Portraits/') and r['edgeLuminance']>.22],
    walkChecks=[dict(id=r['id'],iou=round(r['silhouetteIoU'],3)) for r in rows if 'silhouetteIoU' in r]),indent=2))
