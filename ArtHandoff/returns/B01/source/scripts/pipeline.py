"""B01 reproducible utility processing. No anatomy or final art drawn here."""
from pathlib import Path
import json, sys, shutil
import numpy as np
from PIL import Image, ImageFilter
from PIL.PngImagePlugin import PngInfo
from scipy.ndimage import distance_transform_edt, label, find_objects
ROOT=Path(__file__).resolve().parents[2]
REPO=ROOT.parents[2]
REQUEST=REPO/'ArtHandoff/requests/B01'
MANIFEST=ROOT/'DELIVERABLE_MANIFEST.json'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding='utf-8')
def defringe(im):
    a=np.array(im.convert('RGBA')); mask=a[:,:,3]<32
    if np.any(~mask):
        ind=distance_transform_edt(a[:,:,3]<=128,return_distances=False,return_indices=True)
        a[:,:,:3][mask]=a[ind[0][mask],ind[1][mask],:3]
    return Image.fromarray(a)
def save(im,p):
    p.parent.mkdir(parents=True,exist_ok=True)
    info=PngInfo();info.add(b'sRGB',b'\x00');defringe(im).save(p,pnginfo=info)
def init():
    d=read(REQUEST/'DELIVERABLE_MANIFEST.template.json'); d['date']='2026-10-20';d['assets']=[];d['extras']=[];d['knownIssues']=[];d['blockers']=[]
    d['styleLock']={'palette':['#2a2c31','#625c55','#6b2734','#ff6a2b','#8fe3ff','#2b5cff','#1d1f24'], 'light':'key upper-left-front #ffe9d0, rim back-right #9fe8ff, ambient #16233a','edge':'Dark local-hue edge, no uniform black outline; cool 1–3 px rim; controlled broad brush planes.', 'promptTemplate':'Dark Mythic Fantasy, painterly stylized 2.5D; orthographic 38.3-degree elevation, three-quarter front body turned 25 degrees toward screen-right. Key upper-left-front #ffe9d0, rim back-right #9fe8ff, ambient #16233a. Controlled broad brush planes, coloured local-hue dark edges without black outlines.'}
    d['tools'][0]['version']='built-in image_gen (version not exposed)'
    for g in read(REQUEST/'INPUT_MANIFEST.json')['groups']:
        for a in g['assets']: d['assets'].append({'id':a['id'],'status':'blocked','size':a['size'],'reason':'Pending production in priority order','priority':g['priority'],'thirdPartyInputs':[]})
    write(MANIFEST,d)
    for s in ['exports/Art','source/masters','source/sheets','source/blender','source/battlefield/layers','previews','qa','_work/tmp']: (ROOT/s).mkdir(parents=True,exist_ok=True)
def register(id,source,prompt,generator='image_generation',master=None,assessment='Requires owner review at game scale.'):
    d=read(MANIFEST); a=next(a for a in d['assets'] if a['id']==id)
    a.update(status='delivered',export=f'exports/Art/{id}.png',source=source,generator=generator,prompt=prompt,cleanup='source/scripts/pipeline.py; source/scripts/jobs.json',selfAssessment=assessment)
    a.pop('reason',None)
    if master:a['master']=master
    write(MANIFEST,d)
def process(job):
    raw=Image.open(ROOT/job['source']).convert('RGBA')
    for spec in job['assets']:
        id=spec['id']; im=raw.crop(spec.get('crop',(0,0,*raw.size)))
        if spec.get('removeCutNeighbours'):
            a=np.array(im);lab,n=label(a[:,:,3]>32);slices=find_objects(lab)
            if n:
                sizes=np.bincount(lab.ravel());largest=1+np.argmax(sizes[1:])
                for k,sl in enumerate(slices,1):
                    if sl is not None and k!=largest and (sl[1].start<2 or sl[1].stop>=im.width-2):a[:,:,3][lab==k]=0
                im=Image.fromarray(a)
        if spec.get('flip'):im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if spec.get('neutral'):
            aa=im.getchannel('A'); im=im.convert('L').convert('RGBA'); im.putalpha(aa)
        w,h=spec['size']; mult=spec.get('masterScale',2)
        if 'height' in spec:
            ar=np.array(im); box=Image.fromarray(np.uint8(ar[:,:,3]>32)*255).getbbox()
            if not box: raise ValueError('Empty source: '+id)
            im=im.crop(box); fac=min(spec['height']*mult/im.height,spec.get('maxWidth',w-24)*mult/im.width)
            im=im.resize((round(im.width*fac),round(im.height*fac)),Image.Resampling.LANCZOS)
            out=Image.new('RGBA',(w*mult,h*mult)); x=round(w*mult/2-im.width/2)+spec.get('dx',0)*mult
            # Threshold-aware exact foot alignment, after resize.
            low=np.where(np.array(im)[:,:,3]>128)[0].max()
            y=round(spec['foot']*mult-low)
            out.paste(im,(x,y))
        elif spec.get('fit'):
            a=np.array(im);box=Image.fromarray(np.uint8(a[:,:,3]>32)*255).getbbox()
            if box:im=im.crop(box)
            margin=spec.get('margin',.06);fac=min(w*mult*(1-margin*2)/im.width,h*mult*(1-margin*2)/im.height)
            im=im.resize((max(1,round(im.width*fac)),max(1,round(im.height*fac))),Image.Resampling.LANCZOS);out=Image.new('RGBA',(w*mult,h*mult));out.paste(im,((out.width-im.width)//2,(out.height-im.height)//2))
        else: out=im.resize((w*mult,h*mult),Image.Resampling.LANCZOS)
        master=f'source/masters/{id}@{mult}x.png';save(out,ROOT/master)
        final=out.resize((w,h),Image.Resampling.LANCZOS)
        if spec.get('centreAlphaCap'):
            aa=np.array(final); yy,xx=np.indices((h,w));mask=((xx-w/2)**2+(yy-h/2)**2)<(min(w,h)*.20)**2
            aa[:,:,3][mask]=np.minimum(aa[:,:,3][mask],spec['centreAlphaCap']);final=Image.fromarray(aa)
        save(final,ROOT/f'exports/Art/{id}.png')
        register(id,job['source'],job['prompt'],master=master,assessment=spec.get('assessment','Generated painterly art; identity and readability require owner review.'))
def run():
    for job in read(ROOT/'source/scripts/jobs.json'):process(job)
if __name__=='__main__':
    if sys.argv[1]=='init':init()
    elif sys.argv[1]=='run':run()
