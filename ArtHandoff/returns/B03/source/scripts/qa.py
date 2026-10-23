import json,sys,os
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from PIL import Image,ImageDraw,ImageFont,ImageOps
ROOT=Path(__file__).resolve().parents[2];REPO=ROOT.parents[2]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def dump(p,d):Path(p).write_text(json.dumps(d,indent=2),encoding='utf-8')
dm=read(ROOT/'DELIVERABLE_MANIFEST.json');jobs={j['id']:j for j in read(ROOT/'source/jobs.json')}
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',13)
heroes=['tidal','raiden','glacius','zephyr','magnus','seren']
states=['idle','cast','downed','attack','evoA','evoA_cast','evoA_attack','evoB','evoB_cast','evoB_attack']
metrics=[]
for d in dm['assets']:
 p=ROOT/d.get('export','missing')
 if not p.is_file():continue
 im=Image.open(p);a=np.array(im);m=a[:,:,3]>128;b=im.getchannel('A').point(lambda v:255 if v>128 else 0).getbbox()
 edge=m & ~ndi.binary_erosion(m,iterations=3);lum=a[:,:,:3]@np.array([.2126,.7152,.0722])/255
 r={'id':d['id'],'size':list(im.size),'mode':im.mode,'alphaRange':list(im.getchannel('A').getextrema()),'bbox':b,'edgeLuminance':float(lum[edge].mean()),'masterSize':list(Image.open(ROOT/d['master']).size)}
 if d['id'].startswith('Heroes/'):
  r['footRow']=b[3]-1;r['iconBoundsPass']=b[0]>=40 and b[2]<=361 and b[1]>=80 and b[3]<=400;r['edgePass']=r['edgeLuminance']>=.27
 metrics.append(r)
dump(ROOT/'qa/local_metrics.json',metrics)
for mode in ['colour','gray','silhouette']:
 for canvaspx,tag in [(192,'1440p'),(96,'720p')]:
  cellw=canvaspx+12;cellh=canvaspx+22
  sheet=Image.new('RGB',(cellw*10,cellh*6),(41,42,44) if mode!='silhouette' else (185,185,185));draw=ImageDraw.Draw(sheet)
  for row,h in enumerate(heroes):
   for col,s in enumerate(states):
    p=ROOT/f'exports/Art/Heroes/{h}_{s}.png'
    if not p.exists():continue
    im=Image.open(p).convert('RGBA').resize((canvaspx,canvaspx),Image.Resampling.LANCZOS);alpha=im.getchannel('A')
    if mode=='gray':im=ImageOps.grayscale(im).convert('RGBA');im.putalpha(alpha)
    if mode=='silhouette':im=Image.new('RGBA',im.size,(0,0,0));im.putalpha(alpha)
    x=col*cellw;y=row*cellh;sheet.paste(im,(x,y),im);draw.text((x+3,y+canvaspx+2),h+' '+s,fill=(230,230,230) if mode!='silhouette' else (20,20,20),font=font)
  sheet.save(ROOT/f'previews/review_{mode}_{tag}.png')
print(json.dumps({'exports':len(metrics),'minimumEdge':min(x['edgeLuminance'] for x in metrics if x['id'].startswith('Heroes/')),'lowEdges':[x['id'] for x in metrics if x['id'].startswith('Heroes/') and not x['edgePass']],'outsideIcon':[x['id'] for x in metrics if x['id'].startswith('Heroes/') and not x['iconBoundsPass']]}))

# Explicit B03 offline scenes use the requested generated basalt, not a Unity capture.
sys.path.insert(0,str(REPO/'Tools/ArtPipeline'));import handoff as H
settings=H.A.read_json(H.A.SETTINGS)
for d in dm['assets']:
 if d['id'].startswith('Heroes/'):settings[H.LIVE_REL+d['id']+'.png']={'ppu':200,'pivot':[.5,.07]}
art=H.ArtSet(str(ROOT/'exports/Art'),settings)
bg=REPO/'ArtProduction/generated/World/arena_background.png'
art.cache['World/arena_background']=(Image.open(bg).convert('RGBA'),80,[.5,.5])
layout=read(REPO/'ArtHandoff/requests/B01/benchmark_layout.json')
layout['heroes']=layout['heroes'][:6]
for h,name in zip(layout['heroes'],heroes):h['sprite']='Heroes/'+name+'_idle'
for ht in [1440,1080,720]:H.render_scene(art,layout,ht,'OFFLINE B03 COMPOSITE - generated basalt - not Unity / not approved').save(ROOT/f'previews/scene_b03_basalt_{ht}p.png')
bg_a=np.array(Image.open(bg).convert('RGB'));dump(ROOT/'qa/basalt_reference.json',{'source':str(bg),'meanLuminance':float((bg_a@np.array([.2126,.7152,.0722])/255).mean()),'layout':'B01 benchmark with six B03 idle heroes substituted','evidence':'offline composite only'})
