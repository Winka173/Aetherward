"""Save built-in concept outputs without upscaling; maintain provenance."""
import argparse,json,msvcrt
from pathlib import Path
from PIL import Image,ImageCms,ImageOps
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--id',required=True);p.add_argument('--source',required=True);p.add_argument('--prompt',required=True);a=p.parse_args()
im=Image.open(a.source).convert('RGBA')
source=ROOT/'source/generations'/f'{a.id}.png';source.parent.mkdir(parents=True,exist_ok=True);im.save(source)
entry=dict(id=a.id,kind='MOCKUP / concept — not a game asset or screenshot',generator='image_gen (built-in)',source=source.relative_to(ROOT).as_posix(),nativeSize=list(im.size),prompt=Path(a.prompt).read_text(encoding='utf-8'),cleanup='source/scripts/save_concept.py: native PNG retained; Lanczos downscale/crop only; no upscale; sRGB RGBA8.')
if im.width<2560 or im.height<1440:
    entry.update(status='blocked',reason=f'Built-in image_gen returned {im.width}x{im.height}; required 2560x1440. Upscaling a smaller generation is prohibited.')
else:
    out=ROOT/f'{a.id}.png';out.parent.mkdir(parents=True,exist_ok=True)
    im=ImageOps.fit(im,(2560,1440),method=Image.Resampling.LANCZOS)
    im.save(out,icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes())
    entry.update(status='delivered',path=out.relative_to(ROOT).as_posix(),size=[2560,1440])
    for h in [1080,720]:
        im.resize((round(h*16/9),h),Image.Resampling.LANCZOS).save(ROOT/'previews'/f'{Path(a.id).name}_{h}p.png')
with (ROOT/'_work/manifest.write.lock').open('a+b') as lock:
    if lock.tell()==0:lock.write(b'0');lock.flush()
    lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_LOCK,1)
    try:
        mp=ROOT/'DELIVERABLE_MANIFEST.json';m=json.loads(mp.read_text(encoding='utf-8'))
        m['extras']=[x for x in m.get('extras',[]) if x.get('id')!=a.id]+[entry]
        temporary=mp.with_name(mp.name+'.tmp')
        temporary.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        temporary.replace(mp)
    finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
print(json.dumps({k:v for k,v in entry.items() if k!='prompt'},indent=2))
