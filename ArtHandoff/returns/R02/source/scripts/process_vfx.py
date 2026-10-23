"""Utility-only alpha, colour profile, framing, downscale and provenance cleanup."""
import argparse, json, shutil, os
from pathlib import Path
import numpy as np
from PIL import Image, ImageCms
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parents[2]
for key in ('TEMP','TMP'):
    os.environ[key]=str(ROOT/'_work/tmp')

def save(im, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    a = np.array(im.convert('RGBA'))
    name=path.stem.split('@')[0]
    if name in ('ring','telegraph') or name.startswith(('zone_','field_')):
        hh,ww=a.shape[:2]; yy,xx=np.ogrid[:hh,:ww]
        interior=(xx-ww/2)**2+(yy-hh/2)**2 < (min(ww,hh)*.29)**2
        a[:,:,3][interior]=np.minimum(a[:,:,3][interior],89)
    opaque = a[:,:,3] >= 32
    if opaque.any():
        nearest = distance_transform_edt(~opaque, return_distances=False, return_indices=True)
        a[~opaque,:3] = a[nearest[0][~opaque],nearest[1][~opaque],:3]
    Image.fromarray(a, 'RGBA').save(path, icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes())

def main():
    p=argparse.ArgumentParser(); p.add_argument('name'); p.add_argument('input'); p.add_argument('--prompt',required=True)
    a=p.parse_args(); name=a.name
    req=json.loads((REPO/'ArtHandoff/requests/R02/INPUT_MANIFEST.json').read_text('utf-8'))
    fact=next(f for g in req['groups'] for f in g['assets'] if f['id']=='Vfx/'+name)
    raw=ROOT/'source/generations'/f'{name}.png'
    if Path(a.input).resolve()!=raw.resolve(): shutil.copy2(a.input,raw)
    im=Image.open(raw).convert('RGBA')
    if min(im.size)<2*max(fact['size']): raise ValueError('Generation below 2x contract')
    if im.getchannel('A').getextrema()[0]==255: raise ValueError('Generation has no transparency')
    # Preserve the generated design; fit opaque bounds to prescribed coverage.
    bbox=im.getchannel('A').point(lambda v:255 if v>8 else 0).getbbox()
    crop=im.crop(bbox); coverage=.70 if name=='fireball' else .85
    msize=1024; scale=coverage*msize/max(crop.size)
    if scale>1: scale=1 # never upscale generated detail
    crop=crop.resize(tuple(round(v*scale) for v in crop.size),Image.Resampling.LANCZOS)
    master=Image.new('RGBA',(msize,msize)); master.alpha_composite(crop,((msize-crop.width)//2,(msize-crop.height)//2))
    if name.startswith('burst_'):
        # Effects render over units: apply a uniform opacity cap, preserving all artwork.
        master.putalpha(master.getchannel('A').point(lambda v:round(v*.65)))
    if name in ('ring','telegraph','spark'):
        rgb=master.convert('RGB').convert('L'); master=Image.merge('RGBA',(rgb,rgb,rgb,master.getchannel('A')))
    if name in ('ring','telegraph') or name.startswith(('zone_','field_')):
        arr=np.array(master); yy,xx=np.ogrid[:msize,:msize]
        interior=(xx-msize/2)**2+(yy-msize/2)**2 < (msize*.29)**2
        arr[:,:,3][interior]=np.minimum(arr[:,:,3][interior],89)
        master=Image.fromarray(arr,'RGBA')
    mp=ROOT/'source/masters/Vfx'/f'{name}@4x.png'; save(master,mp)
    ep=ROOT/'exports/Art/Vfx'/f'{name}.png'; save(master.resize(tuple(fact['size']),Image.Resampling.LANCZOS),ep)
    prompt=Path(a.prompt).read_text('utf-8'); manifest=ROOT/'DELIVERABLE_MANIFEST.json'
    dm=json.loads(manifest.read_text('utf-8'))
    entry=dict(id=fact['id'],status='delivered',export=ep.relative_to(ROOT).as_posix(),size=fact['size'],source=raw.relative_to(ROOT).as_posix(),master=mp.relative_to(ROOT).as_posix(),generator='image_gen.imagegen (built-in)',prompt=prompt,cleanup='source/scripts/process_vfx.py '+name+' source/generations/'+name+'.png --prompt source/prompts/'+name+'.txt',thirdPartyInputs=[],selfAssessment='Generated comic VFX; offline review pending, Unity animation and blend validation remain with the lead.')
    dm['assets']=[entry if d['id']==fact['id'] else d for d in dm['assets']]
    manifest.write_text(json.dumps(dm,indent=2)+'\n',encoding='utf-8')
    print(name,im.size,'->',fact['size'])

if __name__=='__main__': main()
