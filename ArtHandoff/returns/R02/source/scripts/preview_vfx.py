"""Offline contact sheets; no painted VFX or gameplay evidence."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
ROOT=Path(__file__).resolve().parents[2]; REPO=ROOT.parents[2]
OUT=ROOT/'previews'; OUT.mkdir(exist_ok=True)
font=lambda n: ImageFont.truetype('arial.ttf',n)
req=json.loads((REPO/'ArtHandoff/requests/R02/INPUT_MANIFEST.json').read_text('utf-8'))
assets=[f for g in req['groups'] for f in g['assets']]
bg=Image.open(REPO/'ArtHandoff/requests/R01/references/battlefield_toon_verdant.png').convert('RGBA')
canvas=Image.new('RGBA',(2560,1440),(25,20,38,255)); d=ImageDraw.Draw(canvas)
d.text((32,18),'R02 VFX — OFFLINE COMPOSITE — not a Unity screenshot',font=font(30),fill='white')
d.text((32,58),'Bursts: 3-unit display (~225 px); heroes: ~190 px; other effects use manifest PPU. Ground decals squash to 0.62.',font=font(20),fill='white')
for i,f in enumerate(assets):
    x=20+(i%7)*363; y=100+(i//7)*435
    tile=ImageOps.fit(bg,(350,400),centering=(.15,.5))
    name=f['id'].split('/')[1]; p=ROOT/'exports/Art'/f"{f['id']}.png"
    if p.exists():
        fx=Image.open(p).convert('RGBA')
        size=225 if name.startswith('burst_') else round(f['size'][0]/f['ppu']*75)
        height=round(size*.62) if name in ('ring','telegraph') or name.startswith(('zone_','field_')) else size
        fx=fx.resize((size,height),Image.Resampling.LANCZOS)
        if name.startswith('burst_'):
            hero={'fire':'ignis','ice':'glacius','lightning':'veyra','water':'marina'}[name[6:]]
            hp=REPO/'ArtHandoff/returns/R01/exports/Art/Heroes'/f'{hero}_idle.png'
            him=Image.open(hp).convert('RGBA')
            hb=him.getchannel('A').getbbox(); him=him.crop(hb)
            him=him.resize((round(him.width*190/him.height),190),Image.Resampling.LANCZOS)
            tile.alpha_composite(him,((350-him.width)//2,110))
        tile.alpha_composite(fx,((350-size)//2,(400-height)//2))
    else:
        ImageDraw.Draw(tile).text((35,170),'BLOCKED — no generated asset',font=font(18),fill='white')
    canvas.alpha_composite(tile,(x,y)); d.text((x+8,y+370),name,font=font(18),fill='white')
canvas.convert('RGB').save(OUT/'vfx_on_battlefield_1440.png')
for h in (1080,720): canvas.convert('RGB').resize((h*16//9,h),Image.Resampling.LANCZOS).save(OUT/f'vfx_on_battlefield_{h}.png')
for mode in ('gray','silhouette'):
    sheet=Image.new('RGB',(1280,720),(55,52,64)); sd=ImageDraw.Draw(sheet)
    sd.text((15,10),'R02 '+mode+' — OFFLINE contact sheet',font=font(20),fill='white')
    for i,f in enumerate(assets):
        p=ROOT/'exports/Art'/f"{f['id']}.png"
        if not p.exists(): continue
        im=Image.open(p).convert('RGBA').resize((145,145),Image.Resampling.LANCZOS)
        if mode=='gray':
            g=ImageOps.grayscale(im); im=Image.merge('RGBA',(g,g,g,im.getchannel('A')))
        else: im=Image.merge('RGBA',(*[Image.new('L',im.size,255)]*3,im.getchannel('A')))
        x=10+(i%7)*182;y=45+(i//7)*220
        sheet.paste(im,(x,y),im);sd.text((x,y+155),f['id'][4:],font=font(12),fill='white')
    sheet.save(OUT/f'vfx_{mode}_720.png')
print('Offline VFX preview sheets saved')
