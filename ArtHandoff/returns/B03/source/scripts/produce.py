import json, sys, shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageCms, ImageEnhance
from scipy import ndimage as ndi

ROOT=Path(__file__).resolve().parents[2]
REPO=ROOT.parents[2]
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding='utf-8')
def save(im,p):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    a=np.array(im.convert('RGBA')); solid=a[:,:,3]>=32
    if solid.any():
        ix=ndi.distance_transform_edt(~solid,return_distances=False,return_indices=True)
        a[~solid,:3]=a[ix[0][~solid],ix[1][~solid],:3]
    Image.fromarray(a).save(p,icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes())
def process(job):
    registration={}
    im=Image.open(ROOT/job['raw']).convert('RGBA')
    if 'crop' in job:
        x0,y0,x1,y1=job['crop'];im=im.crop((round(x0*im.width),round(y0*im.height),round(x1*im.width),round(y1*im.height)))
    if 'downed' in job['id']:
        alpha=im.getchannel('A');im=ImageEnhance.Color(im).enhance(.6);im.putalpha(alpha)
    a=np.array(im); mask=a[:,:,3]>32
    lab,n=ndi.label(mask); sizes=np.bincount(lab.ravel()); keep=sizes>max(12,mask.sum()*.0003);keep[0]=False
    if job.get('largestOnly') and n:
        keep[:]=False;keep[np.argmax(sizes[1:])+1]=True
    a[~keep[lab],3]=0;im=Image.fromarray(a)
    bbox=im.getchannel('A').point(lambda x:255 if x>32 else 0).getbbox()
    if not bbox: raise ValueError('No alpha subject')
    if job['id'].startswith('Portraits/'):
        im=im.crop(bbox)
        if min(im.size)<384:raise ValueError('Portrait source below 2x')
        side=max(im.size)
        # Uniform contain preserves facial anatomy; composite over a dark vignette.
        part=im.copy();part.thumbnail((384,384),Image.Resampling.LANCZOS)
        yy,xx=np.mgrid[:384,:384];rad=np.clip(np.sqrt(((xx-192)/270)**2+((yy-170)/270)**2),0,1)
        bg=np.zeros((384,384,4),dtype=np.uint8)
        for k,(c0,c1) in enumerate([(35,18),(38,21),(45,28)]):bg[:,:,k]=c0*(1-rad)+c1*rad
        bg[:,:,3]=255;im=Image.fromarray(bg);im.alpha_composite(part,((384-part.width)//2,384-part.height))
        # A generated dark vignette may be full bleed; intake requires an alpha edge.
        im.putpixel((0,0),(*im.getpixel((0,0))[:3],0))
    else:
        b=bbox; head=job.get('head',b[1]/im.height)*im.height
        feet=b[3]-1; torso=job.get('torso',.5)*im.width
        height=job.get('height',490 if 'downed' not in job['id'] else 340)
        scale=min(height/max(1,feet-head),630/(b[2]-b[0]),580/(b[3]-b[1]))
        if scale>1:raise ValueError(f'Would upscale {scale:.3f}; source {im.size}, bbox {b}')
        part=im.crop(b).resize((round((b[2]-b[0])*scale),round((b[3]-b[1])*scale)),Image.Resampling.LANCZOS)
        px=round(400-(torso-b[0])*scale);py=745-part.height
        if px<80 or px+part.width>720:
            px=max(80,min(px,720-part.width))
        registration={'uniformScale':scale,'sourceCropSize':list(im.size),'annotatedHeadToFootExport':(feet-head)*scale/2,'annotatedTorsoExportX':(px+(torso-b[0])*scale)/2,'annotationNote':'Manual approximate source head/torso landmarks; not automated anatomy detection.'}
        im=Image.new('RGBA',(800,800));im.alpha_composite(part,(px,py))
    category,name=job['id'].split('/')
    master=f'source/masters/{category}/{name}@2x.png';export=f'exports/Art/{job["id"]}.png'
    save(im,ROOT/master);save(im.resize((400,400) if category=='Heroes' else (192,192),Image.Resampling.LANCZOS),ROOT/export)
    return {'master':master,'export':export,'rawSize':list(Image.open(ROOT/job['raw']).size),'source':job['raw'],'prompt':job['prompt'],'cleanup':'source/scripts/produce.py','generator':'image_generation (built-in image_gen; version not exposed)','thirdPartyInputs':[],'status':'delivered','registration':registration,'selfAssessment':'Reference-guided original generation; identity, material and pose reviewed in offline sheets. Owner approval pending.'}
def rebuild():
    jobs=read(ROOT/'source/jobs.json');dm=read(ROOT/'DELIVERABLE_MANIFEST.json');byid={d['id']:d for d in dm['assets']}
    errors=[]
    for j in jobs:
        try:byid[j['id']].update(process(j))
        except Exception as e:
            byid[j['id']].update(status='blocked',reason=str(e));errors.append([j['id'],str(e)])
    dm['blockers']=errors;write(ROOT/'DELIVERABLE_MANIFEST.json',dm);print(json.dumps({'processed':len(jobs),'errors':errors}))
if __name__=='__main__':rebuild()
