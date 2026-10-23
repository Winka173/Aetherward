"""B04 utility-only processing; never draws anatomy. All writes stay in B04."""
from pathlib import Path
import json, os, sys, shutil
import numpy as np
from PIL import Image, ImageEnhance
from PIL.PngImagePlugin import PngInfo
from scipy.ndimage import distance_transform_edt, label
ROOT=Path(__file__).resolve().parents[2]
REPO=ROOT.parents[2]
os.environ['TEMP']=os.environ['TMP']=str(ROOT/'_work/tmp')
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding='utf-8')
def save(im,p):
    a=np.array(im.convert('RGBA')); mask=a[:,:,3]<32
    if np.any(a[:,:,3]>128):
        ind=distance_transform_edt(a[:,:,3]<=128,return_distances=False,return_indices=True)
        a[:,:,:3][mask]=a[ind[0][mask],ind[1][mask],:3]
    p.parent.mkdir(parents=True,exist_ok=True)
    info=PngInfo();info.add(b'sRGB',b'\x00')
    Image.fromarray(a).save(p,pnginfo=info)
def init():
    d=read(REPO/'ArtHandoff/requests/B01/DELIVERABLE_MANIFEST.template.json')
    d.update(batch='B04',date='2026-10-20',assets=[],extras=[],knownIssues=[],blockers=[])
    d['styleLock']=read(REPO/'ArtHandoff/returns/B01/DELIVERABLE_MANIFEST.json')['styleLock']
    d['tools']=[{'name':'image_generation (Codex built-in)','version':'not exposed'},{'name':'Python','version':sys.version.split()[0],'packages':['Pillow','numpy','scipy']}]
    for g in read(REPO/'ArtHandoff/requests/B04/INPUT_MANIFEST.json')['groups']:
        for a in g['assets']:
            d['assets'].append(dict(id=a['id'],status='blocked',size=a['size'],reason='Pending generation; batch in production.',thirdPartyInputs=[]))
    write(ROOT/'DELIVERABLE_MANIFEST.json',d)
def ingest(job):
    im=Image.open(ROOT/job['source']).convert('RGBA')
    im=im.crop(job.get('crop',[0,0,*im.size]))
    if job['id'].startswith('Portraits/'):
        if min(im.size)<384: raise ValueError('Portrait source too small')
        out=im.resize((384,384),Image.Resampling.LANCZOS)
        a=np.array(out);a[0,0,3]=0;out=Image.fromarray(a)
        uid=job['id'];master=f'source/masters/{uid}@2x.png';save(out,ROOT/master)
        final=out.resize((192,192),Image.Resampling.LANCZOS);a=np.array(final);a[0,0,3]=0;save(Image.fromarray(a),ROOT/f'exports/Art/{uid}.png')
        register(job,master)
        return
    if 'downed' in job['id']: im=ImageEnhance.Color(im).enhance(.6)
    a=np.array(im); components,n=label(a[:,:,3]>32)
    if n:
        counts=np.bincount(components.ravel()); tiny=np.isin(components,np.where((counts<12)&(np.arange(len(counts))>0))[0]);a[tiny,3]=0;im=Image.fromarray(a)
    bbox=im.getchannel('A').point(lambda v:255 if v>32 else 0).getbbox()
    if not bbox: raise ValueError('Empty alpha')
    fullw,fullh=im.size
    im=im.crop(bbox)
    height=job.get('height',260)*2; maxw=job.get('maxWidth',312)*2
    scale=min(height/im.height,maxw/im.width)
    anchor=None
    if 'torsoXRatio' in job:
        anchor=job['torsoXRatio']*fullw-bbox[0]
        scale=min(scale,318/max(1,anchor),318/max(1,im.width-anchor))
    if scale>1.001: raise ValueError('Source too small: no upscaling permitted')
    im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
    low=np.where(np.array(im)[:,:,3]>128)[0].max()
    out=Image.new('RGBA',(800,800))
    xpos=round(400-anchor*scale) if anchor is not None else (800-im.width)//2+job.get('dx',0)*2
    out.paste(im,(xpos,744-int(low)))
    uid=job['id']; master=f'source/masters/{uid}@2x.png';save(out,ROOT/master)
    save(out.resize((400,400),Image.Resampling.LANCZOS),ROOT/f'exports/Art/{uid}.png')
    register(job,master)
def register(job,master):
    uid=job['id'];d=read(ROOT/'DELIVERABLE_MANIFEST.json'); a=next(x for x in d['assets'] if x['id']==uid)
    a.update(status='delivered',export=f'exports/Art/{uid}.png',source=job['source'],master=master,generator='image_generation (built-in)',prompt=job['prompt'],cleanup='source/scripts/pipeline.py; source/scripts/jobs.json',selfAssessment='Generated painterly art; requires owner review for identity, role and pose quality.');a.pop('reason',None)
    write(ROOT/'DELIVERABLE_MANIFEST.json',d)
if __name__=='__main__':
    if sys.argv[1]=='init':init()
    elif sys.argv[1]=='run':
        for j in read(ROOT/'source/scripts/jobs.json'):ingest(j)

