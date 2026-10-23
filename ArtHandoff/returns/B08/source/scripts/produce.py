import json, sys, shutil
from pathlib import Path
import numpy as np
from PIL import Image, PngImagePlugin
from scipy.ndimage import distance_transform_edt, binary_erosion

ROOT=Path(__file__).resolve().parents[2]
REPO=ROOT.parents[2]
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v):
 p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
def save(im,p):
 p.parent.mkdir(parents=True,exist_ok=True)
 meta=PngImagePlugin.PngInfo(); meta.add(b'sRGB',b'\x00'); im.save(p,pnginfo=meta)
def defringe(im):
 a=np.array(im); mask=a[:,:,3]>128
 inds=distance_transform_edt(~mask,return_distances=False,return_indices=True)
 low=a[:,:,3]<32; a[low,:3]=a[inds[0][low],inds[1][low],:3]
 return Image.fromarray(a,'RGBA')
def init():
 for d in ['_work/tmp','source/sheets','source/masters/Enemies','source/prompts','exports/Art/Enemies','previews','qa']: (ROOT/d).mkdir(parents=True,exist_ok=True)
 facts=read(REPO/'ArtHandoff/requests/B08/INPUT_MANIFEST.json')
 b01=read(ROOT.parent/'B01/DELIVERABLE_MANIFEST.json')
 manifest={'batch':'B08','producer':'Codex','date':'2026-10-20','styleLock':b01['styleLock'],'tools':[{'name':'image_gen (Codex built-in)','version':'not exposed'},{'name':'Python','packages':['Pillow','numpy','scipy']}],'assets':[],'extras':[],'knownIssues':[],'blockers':[]}
 for g in facts['groups']:
  for f in g['assets']: manifest['assets'].append({'id':f['id'],'status':'blocked','reason':'Production pending','size':f['size']})
 if not (ROOT/'DELIVERABLE_MANIFEST.json').exists(): write(ROOT/'DELIVERABLE_MANIFEST.json',manifest)
def process(jobpath):
 jobpath=Path(jobpath).resolve()
 job=read(jobpath); aid=job['id']; name=aid.split('/')[-1]; char=job['character']
 raw=ROOT/f"source/sheets/{job.get('sourceName',name)}.png"
 if Path(job['raw']).resolve()!=raw.resolve(): shutil.copy2(job['raw'],raw)
 im=Image.open(raw).convert('RGBA'); a=np.array(im); mask=a[:,:,3]>128
 yy,xx=np.where(mask); box=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1))
 crop=im.crop(box); w,h=crop.size
 # Preserve anatomy; only crop, uniform scale, pivot alignment, resample and defringe.
 height=job['height']; maxwidth=job.get('width',232)
 scale=min(height*2/h,maxwidth*2/w)
 if scale>1: raise ValueError('Raw generation too small for 2x master')
 nw,nh=round(w*scale),round(h*scale)
 crop=crop.resize((nw,nh),Image.Resampling.LANCZOS)
 # Torso anchors are measured on source and normalized per frame.
 anchor=job.get('anchor',0.5)*w*scale
 x=round(256-anchor); x=max(6,min(506-nw,x))
 bottom=job.get('bottom',236)*2+1
 master=Image.new('RGBA',(512,512)); master.alpha_composite(crop,(x,bottom-nh+1))
 master=defringe(master); export=defringe(master.resize((256,256),Image.Resampling.LANCZOS))
 mp=ROOT/f'source/masters/{aid}@2x.png'; ep=ROOT/f'exports/Art/{aid}.png'; save(master,mp); save(export,ep)
 ar=np.array(export); m=ar[:,:,3]>128; edge=m & ~binary_erosion(m,iterations=3)
 lum=(ar[:,:,:3]@np.array([.2126,.7152,.0722]))/255
 y,xs=np.where(m)
 metrics={'rawSize':list(im.size),'masterSize':[512,512],'bounds':[int(xs.min()),int(y.min()),int(xs.max()),int(y.max())],'height':int(y.max()-y.min()+1),'width':int(xs.max()-xs.min()+1),'footRow':int(y.max()),'edgeLuminance':float(lum[edge].mean()),'torsoX':(round((x+anchor)/2,1)),'anchorFraction':job.get('anchor',.5)}
 write(ROOT/f'qa/metrics/{name}.json',metrics)
 manifest=read(ROOT/'DELIVERABLE_MANIFEST.json')
 entry={'id':aid,'status':'delivered','export':str(ep.relative_to(ROOT)).replace('\\','/'),'size':[256,256],'source':str(raw.relative_to(ROOT)).replace('\\','/'),'master':str(mp.relative_to(ROOT)).replace('\\','/'),'generator':'image_gen (Codex built-in), version not exposed','prompt':str(Path(jobpath).relative_to(ROOT)).replace('\\','/'),'cleanup':'python source/scripts/produce.py '+str(Path(jobpath).relative_to(ROOT)).replace('\\','/'),'thirdPartyInputs':[],'selfAssessment':'Generated painterly sprite; final pose and identity assessed in offline sheets.','metrics':metrics}
 manifest['assets']=[entry if v['id']==aid else v for v in manifest['assets']]; write(ROOT/'DELIVERABLE_MANIFEST.json',manifest)
 print(json.dumps({'id':aid,**metrics}))
if __name__=='__main__':
 init()
 if len(sys.argv)>1: process(sys.argv[1])
