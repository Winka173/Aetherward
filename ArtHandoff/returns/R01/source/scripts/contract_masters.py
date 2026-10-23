"""Keep the explicit 400/800 hero pair alongside 512/1024 game versions."""
import json,msvcrt
from pathlib import Path
from PIL import Image,ImageCms
ROOT=Path(__file__).resolve().parents[2]
profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
mp=ROOT/'DELIVERABLE_MANIFEST.json'
with (ROOT/'_work/manifest.write.lock').open('a+b') as lock:
    if lock.tell()==0:lock.write(b'0');lock.flush()
    lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_LOCK,1)
    try:
        m=json.loads(mp.read_text(encoding='utf-8'));count=0
        for item in m['assets']:
            if not item['id'].startswith('Heroes/') or item['status']!='delivered':continue
            target=ROOT/'source/masters'/f"{item['id']}@800.png"
            Image.open(ROOT/item['master']).convert('RGBA').resize((800,800),Image.Resampling.LANCZOS).save(target,icc_profile=profile)
            item['contractExport']=f"source/contracts/{item['id']}.png"
            item['contractMaster']=target.relative_to(ROOT).as_posix()
            item['contractSize']=[400,400];item['contractPPU']=200
            count+=1
        temporary=mp.with_name(mp.name+'.tmp');temporary.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');temporary.replace(mp)
    finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
print('Saved',count,'800px hero contract masters; 1024px masters retained.')
