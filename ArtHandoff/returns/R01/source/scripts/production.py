"""R01 utility-only production: provenance, scale, alignment, alpha defringe."""
import argparse, json, os
from pathlib import Path
import numpy as np
from PIL import Image, ImageCms
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parents[2]
REQUEST = REPO / 'ArtHandoff/requests/R01'
MANIFEST = ROOT / 'DELIVERABLE_MANIFEST.json'
os.environ['TEMP']=str(ROOT/'_work/tmp')
os.environ['TMP']=str(ROOT/'_work/tmp')

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temporary.replace(path)

def initialize():
    if MANIFEST.exists():
        return
    req = json.loads((REQUEST/'INPUT_MANIFEST.json').read_text(encoding='utf-8-sig'))
    assets = [dict(id=a['id'], status='pending', size=a['size'], generator='image_gen (built-in)', reason='Awaiting production in required character order.') for g in req['groups'] for a in g['assets']]
    save_json(MANIFEST, dict(batch='R01', producer='Codex', date='2026-10-21', styleLock=dict(palette=['#1b1226','#3b2f6b','#7fe3ff','#c0281a','#ff7a1a','#a98bff','#2fb8b0','#ff3d8b'], light='Warm key upper-left front; cool violet-blue cel shadows; no rim light.', edge='Tapered black-violet brush-pen ink; outer 3px band mean luminance <= 0.22.', promptTemplate='Original dark arcane fantasy, premium hand-inked comic 2.5D. Bold tapered black-violet contours. 2-3 hard flat cel tones per material. Warm upper-left-front key, cool violet-blue shadows. No airbrush, gradients, chibi, vector, rim light, copied characters or artist/game imitation.'), tools=[dict(name='image_gen (built-in)', version='as provided'),dict(name='Python',version='3.11.5',packages=['Pillow','numpy','scipy'])], assets=assets, extras=[], knownIssues=['R01 text requests 400 hero exports with 800 masters; INPUT_MANIFEST and intake require 512. Store 400 contract copies in source/contracts and 512 exports derived from >=1024 originals, plus >=1024 masters.'], blockers=[]))

def process(a):
    m=json.loads(MANIFEST.read_text(encoding='utf-8'))
    item=next(x for x in m['assets'] if x['id']==a.id)
    # Built-in output hints include both directory and file, separated by ' as '.
    source_path=a.source.rsplit(' as ',1)[-1]
    raw=Image.open(source_path).convert('RGBA')
    source=ROOT/'source/generations'/f'{a.id}.png'
    source.parent.mkdir(parents=True,exist_ok=True)
    raw.save(source)
    w,h=item['size']
    if raw.width < 2*w or raw.height < 2*h:
        raise ValueError(f'Generation {raw.size} smaller than required 2x {w,h}; never upscale')
    arr=np.array(raw); mask=arr[:,:,3]>128
    ys,xs=np.where(mask)
    if not len(xs): raise ValueError('Empty alpha')
    # Uniform fitting and translation only. Torso x is visually inspected.
    box=(xs.min(),ys.min(),xs.max()+1,ys.max()+1)
    crop=raw.crop(box)
    hero=a.id.startswith('Heroes/')
    portrait=a.id.startswith('Portraits/')
    scale_canvas=2
    mw,mh=w*scale_canvas,h*scale_canvas
    target_h=a.height*scale_canvas if a.height else (250/400*mh if hero else .74*mh)
    if portrait:
        master=raw.resize((mw,mh),Image.Resampling.LANCZOS)
        # Keep the requested flat backdrop, with a one-export-pixel clear perimeter
        # for the input manifest's RGBA transparency gate.
        alpha=master.getchannel('A')
        alpha.paste(0,(0,0,mw,2)); alpha.paste(0,(0,mh-2,mw,mh))
        alpha.paste(0,(0,0,2,mh)); alpha.paste(0,(mw-2,0,mw,mh))
        master.putalpha(alpha)
    else:
        fit=min(target_h/crop.height, .79*mw/crop.width if hero else .94*mw/crop.width, 1.)
        crop=crop.resize((round(crop.width*fit),round(crop.height*fit)),Image.Resampling.LANCZOS)
        master=Image.new('RGBA',(mw,mh))
        foot=(372/400*mh if hero else (486 if w==512 else 236)*scale_canvas)
        master.alpha_composite(crop,(round(mw/2-crop.width/2+a.offset*scale_canvas), round(foot-crop.height+1)))
    def finish(im):
        ar=np.array(im)
        opaque=ar[:,:,3]>=32
        nearest=distance_transform_edt(~opaque,return_distances=False,return_indices=True)
        low=~opaque
        ar[low,:3]=ar[nearest[0][low],nearest[1][low],:3]
        return Image.fromarray(ar,'RGBA')
    profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    master=finish(master)
    mp=ROOT/'source/masters'/f'{a.id}@2x.png'; mp.parent.mkdir(parents=True,exist_ok=True)
    master.save(mp,icc_profile=profile)
    out=ROOT/'exports/Art'/f'{a.id}.png';out.parent.mkdir(parents=True,exist_ok=True)
    finish(master.resize((w,h),Image.Resampling.LANCZOS)).save(out,icc_profile=profile)
    if hero:
        cp=ROOT/'source/contracts'/f'{a.id}.png'; cp.parent.mkdir(parents=True,exist_ok=True)
        finish(master.resize((400,400),Image.Resampling.LANCZOS)).save(cp,icc_profile=profile)
    item.update(status='delivered',export=out.relative_to(ROOT).as_posix(),source=source.relative_to(ROOT).as_posix(),master=mp.relative_to(ROOT).as_posix(),prompt=Path(a.prompt).read_text(encoding='utf-8'),cleanup=f'source/scripts/production.py process --id {a.id} --source <generation> --prompt <prompt> --height {a.height} --offset {a.offset}',thirdPartyInputs=[],selfAssessment=a.assessment)
    item.pop('reason',None)
    save_json(MANIFEST,m)
    print(json.dumps(item,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True)
    s.add_parser('init')
    q=s.add_parser('process');q.add_argument('--id',required=True);q.add_argument('--source',required=True);q.add_argument('--prompt',required=True);q.add_argument('--height',type=float,default=0);q.add_argument('--offset',type=float,default=0);q.add_argument('--assessment',default='Generated art; requires lead review at game scale.')
    args=p.parse_args()
    if args.command=='init':initialize()
    else:
        # Serialize export + manifest mutations if independent generations finish together.
        import msvcrt
        with (ROOT/'_work/manifest.write.lock').open('a+b') as lock:
            if lock.tell()==0:lock.write(b'0');lock.flush()
            lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_LOCK,1)
            try:process(args)
            finally:
                lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
