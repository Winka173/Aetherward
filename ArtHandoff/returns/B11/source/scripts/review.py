"""Measure delivered sprites and assemble offline color/grayscale/silhouette sheets."""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_erosion
ROOT=Path(__file__).resolve().parents[2]
def run():
    dm=json.loads((ROOT/'DELIVERABLE_MANIFEST.json').read_text(encoding='utf-8'))
    assets=[x for x in dm['assets'] if x['status']=='delivered']
    rows=[]; problems=[]
    records=json.loads((ROOT/'source/records.json').read_text(encoding='utf-8'))
    for d in assets:
        im=Image.open(ROOT/d['export']).convert('RGBA'); a=np.array(im); m=a[:,:,3]>128
        y,x=np.where(m); edge=m & ~binary_erosion(m,iterations=3)
        lum=a[:,:,:3]@[.2126,.7152,.0722]/255
        band=m[160:290]; counts=band.sum(0); cols=np.where(counts>=counts.max()*.6)[0]
        torso=float(np.median(cols)) if len(cols) else None
        registration=records[d['id']].get('registeredTorsoX')
        r=dict(id=d['id'],size=list(im.size),footRow=int(y.max()),height=int(y.max()-y.min()+1),edgeLuminance=float(lum[edge].mean()),silhouetteCrossSectionMedian=torso,registeredTorsoX=registration)
        if registration is None or abs(registration-256)>8:problems.append(d['id']+': torso registration')
        if im.size!=(512,512):problems.append(d['id']+': size')
        if abs(y.max()-486)>6:problems.append(d['id']+': foot')
        if r['edgeLuminance']<.27:problems.append(d['id']+': edge luminance <0.27')
        if not (400<=r['height']<=450):problems.append(d['id']+': height outside 400-450')
        if d['id'].endswith('_b'):
            ap=ROOT/('exports/Art/'+d['id'][:-1]+'a.png')
            if ap.exists():
                am=np.array(Image.open(ap))[:,:,3]>128
                r['walkIoU']=float((am&m).sum()/(am|m).sum())
                if r['walkIoU']<.6:problems.append(d['id']+': walk IoU <0.6')
        rows.append(r)
    out=ROOT/'qa'; out.mkdir(exist_ok=True)
    (out/'local_metrics.json').write_text(json.dumps(dict(assets=rows,problems=problems),indent=2),encoding='utf-8')
    chars=list(dict.fromkeys(d['id'].rsplit('_',1)[0] for d in assets))
    # Each family row preserves the exact common 512 canvas at 180px display size.
    for kind in ['color','grayscale','silhouette']:
        page=Image.new('RGB',(1280,max(720,len(chars)*206+40)),(37,39,44)); draw=ImageDraw.Draw(page)
        draw.text((12,10),'B11 OFFLINE QA - '+kind+'; not gameplay / not approval',fill=(220,225,232))
        for ri,ch in enumerate(chars):
            draw.text((10,ri*206+45),ch.split('/')[-1],fill=(225,225,225))
            for ci,s in enumerate(['a','b','tell','attack']):
                p=ROOT/f'exports/Art/{ch}_{s}.png'
                if not p.exists() and ch.endswith('rift_warden') and s in ['a','b']:
                    p=ROOT.parent/f'B01/exports/Art/{ch}_{s}.png'
                if not p.exists():continue
                im=Image.open(p).convert('RGBA')
                if kind=='grayscale':
                    alpha=im.getchannel('A'); im=im.convert('L').convert('RGBA'); im.putalpha(alpha)
                elif kind=='silhouette':
                    alpha=im.getchannel('A'); im=Image.new('RGBA',im.size,(215,225,235)); im.putalpha(alpha)
                im=im.resize((180,180),Image.Resampling.LANCZOS)
                pos=(265+ci*245,ri*206+35); page.paste(im,pos,im)
                draw.text((pos[0]+70,pos[1]+180),s,fill=(215,220,230))
        page.save(ROOT/f'previews/b11_{kind}_sheet.png')
        # 720p pages prevent a huge all-boss sheet from hiding small-scale problems.
        for pagei,start in enumerate(range(0,len(chars),3)):
            panel=Image.new('RGB',(1280,720),(37,39,44))
            panel.paste(page.crop((0,start*206+30,1280,min(page.height,(start+3)*206+30))),(0,40))
            ImageDraw.Draw(panel).text((12,10),'B11 OFFLINE '+kind+' 720p - not gameplay / not approval',fill=(220,225,232))
            panel.save(ROOT/f'previews/b11_{kind}_720p_{pagei+1}.png')
    # 1440p display scale: 512px / 160 PPU * 96 px/u * boss 1.25 = 384px.
    groundpath=ROOT.parents[2]/'ArtProduction/generated/World/arena_background.png'
    for pagei,start in enumerate(range(0,len(chars),3)):
        page=Image.open(groundpath).convert('RGBA').resize((2560,1440),Image.Resampling.LANCZOS) if groundpath.exists() else Image.new('RGBA',(2560,1440),(37,39,44,255))
        draw=ImageDraw.Draw(page)
        draw.text((25,15),'B11 OFFLINE BASALT READABILITY - actual 1440p boss scale; not gameplay / not approval',fill=(240,240,240))
        for ri,ch in enumerate(chars[start:start+3]):
            draw.text((20,80+ri*430),ch.split('/')[-1],fill=(240,240,240))
            for ci,s in enumerate(['a','b','tell','attack']):
                p=ROOT/f'exports/Art/{ch}_{s}.png'
                if not p.exists() and ch.endswith('rift_warden') and s in ['a','b']:
                    p=ROOT.parent/f'B01/exports/Art/{ch}_{s}.png'
                if not p.exists():continue
                im=Image.open(p).convert('RGBA').resize((384,384),Image.Resampling.LANCZOS)
                pos=(350+ci*520,75+ri*430); page.alpha_composite(im,pos)
                draw.text((pos[0]+180,pos[1]+385),s,fill=(240,240,240))
        for h in [1440,1080,720]:
            page.convert('RGB').resize((h*16//9,h),Image.Resampling.LANCZOS).save(ROOT/f'previews/b11_basalt_page{pagei+1}_{h}p.png')
    print(json.dumps(dict(delivered=len(assets),problems=problems,minimumEdge=min((r['edgeLuminance'] for r in rows),default=None),walkPairs=[(r['id'],r['walkIoU']) for r in rows if 'walkIoU' in r])))
if __name__=='__main__':run()
