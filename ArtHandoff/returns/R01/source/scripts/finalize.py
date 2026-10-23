"""Final technical cleanup of already generated art, never drawing anatomy."""
import json,msvcrt
from pathlib import Path
import numpy as np
from PIL import Image, ImageCms
from scipy.ndimage import distance_transform_edt

ROOT=Path(__file__).resolve().parents[2]
profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
count=0
for folder in ['exports/Art','source/masters','source/contracts']:
    for path in (ROOT/folder).rglob('*.png'):
        im=Image.open(path).convert('RGBA'); a=np.array(im)
        opaque=a[:,:,3]>=128; low=a[:,:,3]<32
        if opaque.any():
            near=distance_transform_edt(~opaque,return_distances=False,return_indices=True)
            a[low,:3]=a[near[0][low],near[1][low],:3]
        Image.fromarray(a,'RGBA').save(path,icc_profile=profile)
        count+=1
with (ROOT/'_work/manifest.write.lock').open('a+b') as lock:
    if lock.tell()==0:lock.write(b'0');lock.flush()
    lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_LOCK,1)
    try:
        mp=ROOT/'DELIVERABLE_MANIFEST.json';m=json.loads(mp.read_text(encoding='utf-8'))
        m['finalCleanup']='source/scripts/finalize.py: for alpha<32, RGB from nearest alpha>=128 neighbor; 8-bit straight RGBA PNG and sRGB ICC profile.'
        temporary=mp.with_name(mp.name+'.tmp')
        temporary.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');temporary.replace(mp)
    finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
print(f'Finalized {count} export/master/contract PNGs.')
