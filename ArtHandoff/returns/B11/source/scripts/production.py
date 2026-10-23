"""B11 utility cleanup only: crop, register, Lanczos, alpha defringe; no drawn art."""
from pathlib import Path
import json, re, sys, shutil, os, msvcrt
import numpy as np
from PIL import Image, PngImagePlugin
from scipy.ndimage import distance_transform_edt, binary_erosion

ROOT=Path(__file__).resolve().parents[2]
REPO=ROOT.parents[2]
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,v):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+f'.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
    tmp.replace(p)
def init():
    if (ROOT/'DELIVERABLE_MANIFEST.json').exists():
        print('Existing B11 manifest retained; use rebuild.py to continue accepted sources.'); return
    for d in ['source/masters/Enemies','source/sheets','source/prompts','exports/Art/Enemies','qa','previews','_work/tmp']:
        (ROOT/d).mkdir(parents=True,exist_ok=True)
    req=read(REPO/'ArtHandoff/requests/B11/INPUT_MANIFEST.json')
    lock=read(ROOT.parent/'B01/DELIVERABLE_MANIFEST.json')['styleLock']
    write(ROOT/'DELIVERABLE_MANIFEST.json',dict(batch='B11',producer='Codex',date='2026-10-20',styleLock=lock,tools=[dict(name='image_gen built-in',version='not exposed'),dict(name='Python',version=sys.version,packages=['Pillow','numpy','scipy'])],assets=[dict(id=f['id'],status='pending',size=f['size']) for g in req['groups'] for f in g['assets']],extras=[],knownIssues=[],blockers=[]))
    brief=(REPO/'ArtHandoff/requests/B11/CODEX_ART_REQUEST.md').read_text(encoding='utf-8')
    designs={}
    for m in re.finditer(r'#### (.*?) \(`([^`]+)`\).*?Design: (.*?)(?=\n\n)',brief,re.S):
        designs[m[2]]=dict(name=m[1],design=m[3].strip())
    write(ROOT/'source/designs.json',designs)
    sys.path.insert(0,str(REPO/'Tools/ArtPipeline'))
    import handoff
    content=handoff.jsonc(str(REPO/'Assets/_Aetherward/Resources/Content/enemies.json'))
    write(ROOT/'qa/content_reference.json',[e for e in content['enemies'] if e['id'] in designs])
    write(ROOT/'qa/contract_facts.json',req)
    print(json.dumps(designs,ensure_ascii=True))

def defringe(im):
    a=np.array(im); m=a[:,:,3]>128; fringe=a[:,:,3]<32
    if not m.any(): raise ValueError('empty alpha')
    idx=distance_transform_edt(~m,return_distances=False,return_indices=True)
    a[fringe,:3]=a[idx[0][fringe],idx[1][fringe],:3]
    return Image.fromarray(a,'RGBA')
def save(im,p):
    meta=PngImagePlugin.PngInfo(); meta.add(b'sRGB',b'\x00')
    tmp=Path(p).with_suffix(f'.{os.getpid()}.tmp.png'); im.save(tmp,pnginfo=meta); tmp.replace(p)
def _process(aid,raw,prompt):
    raw=str(Path(raw).resolve())
    im=Image.open(raw).convert('RGBA'); arr=np.array(im)
    ys,xs=np.where(arr[:,:,3]>128)
    if not len(xs): raise ValueError('no foreground')
    x0,x1,y0,y1=int(xs.min()),int(xs.max())+1,int(ys.min()),int(ys.max())+1
    # Common scale for all poses of a character: identity 420 px tall; no enlargement.
    char=aid.rsplit('_',1)[0]
    recpath=ROOT/'source/records.json'; records=read(recpath) if recpath.exists() else {}
    key=char+'_a'
    scale=records.get(key,{}).get('scale',840/(y1-y0))
    # Keep complete wide attack poses inside canvas, preserving uniform proportions.
    scale=min(max(scale,802/(y1-y0)),960/(x1-x0),900/(y1-y0),1.0)
    anchorpath=ROOT/'source/torso_anchors.json'
    anchors=read(anchorpath) if anchorpath.exists() else {}
    anchor=anchors.get(aid)
    if anchor is not None:
        scale=min(scale,500/max(anchor-x0,x1-anchor))
    if y1-y0<800: raise ValueError(f'native character too small for >=2x master: {y1-y0}')
    crop=im.crop((max(0,x0-3),max(0,y0-3),min(im.width,x1+3),min(im.height,y1+3)))
    nw,nh=round(crop.width*scale),round(crop.height*scale)
    crop=crop.resize((nw,nh),Image.Resampling.LANCZOS)
    ar=np.array(crop); yy,xx=np.where(ar[:,:,3]>128)
    # Use torso cross section instead of weapon/wing extent for horizontal registration.
    band=ar[int(nh*.32):int(nh*.57),:,3]>128
    cols=band.sum(axis=0); candidates=np.where(cols>=max(2,cols.max()*.60))[0]
    cx=float(np.median(candidates)) if len(candidates) else (xx.min()+xx.max())/2
    if anchor is not None:
        cx=(anchor-max(0,x0-3))*scale
    ox=round(512-cx); oy=972-int(yy.max())
    ox=max(-int(xx.min())+16,min(ox,1007-int(xx.max())))
    master=Image.new('RGBA',(1024,1024)); master.alpha_composite(crop,(ox,oy)); master=defringe(master)
    native=defringe(master.resize((512,512),Image.Resampling.LANCZOS))
    mp=ROOT/f'source/masters/{aid}@2x.png'; ep=ROOT/f'exports/Art/{aid}.png'
    mp.parent.mkdir(parents=True,exist_ok=True); ep.parent.mkdir(parents=True,exist_ok=True)
    save(master,mp); save(native,ep)
    a=np.array(native); mask=a[:,:,3]>128; edge=mask & ~binary_erosion(mask,iterations=3)
    lum=(a[:,:,:3]@[.2126,.7152,.0722])/255
    metrics=dict(rawSize=list(im.size),rawOpaqueBounds=[x0,y0,x1,y1],scale=scale,footRow=int(np.where(mask)[0].max()),height=int(np.where(mask)[0].max()-np.where(mask)[0].min()+1),edgeLuminance=float(lum[edge].mean()),torsoAnchorTarget=256,registeredTorsoX=round((ox+cx)/2,2),rawTorsoAnchorX=anchor,registration='authored torso anchor' if anchor is not None else 'upper torso alpha cross-section; visual review required')
    records[aid]=dict(source=str(Path(raw).relative_to(ROOT)).replace('\\','/'),master=str(mp.relative_to(ROOT)).replace('\\','/'),prompt=prompt,**metrics)
    write(recpath,records)
    dm=read(ROOT/'DELIVERABLE_MANIFEST.json')
    for d in dm['assets']:
        if d['id']==aid:
            d.update(status='delivered',export=f'exports/Art/{aid}.png',source=records[aid]['source'],master=records[aid]['master'],generator='image_gen built-in; version not exposed',prompt=prompt,cleanup=f'python source/scripts/production.py process {aid} {records[aid]["source"]} {prompt}',thirdPartyInputs=[],selfAssessment='Generated painterly boss pose; native alpha retained, uniform fit, registration and nearest-opaque defringe. Offline review pending.',metrics=metrics)
    write(ROOT/'DELIVERABLE_MANIFEST.json',dm)
    print(json.dumps(dict(id=aid,**metrics)))

def process(*args):
    # Serialize registry/export writes when independent generations complete together.
    with open(ROOT/'_work/production.lock','a+b') as lock:
        if lock.tell()==0: lock.write(b'0'); lock.flush()
        lock.seek(0); msvcrt.locking(lock.fileno(),msvcrt.LK_LOCK,1)
        try: return _process(*args)
        finally:
            lock.seek(0); msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)

if __name__=='__main__':
    if sys.argv[1]=='init':init()
    elif sys.argv[1]=='process':process(*sys.argv[2:])
