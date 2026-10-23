"""Choose a small horizontal translation for failing walk overlaps. No drawing."""
import json, re, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
manifest=json.loads((ROOT/'DELIVERABLE_MANIFEST.json').read_text(encoding='utf-8'))
for item in manifest['assets']:
    aid=item['id']
    if item['status']!='delivered':continue
    if '_walk_' in aid:
        identity=aid.rsplit('_walk_',1)[0]+'_idle';minimum=.55
    elif aid.startswith('Enemies/') and aid.endswith('_b'):
        identity=aid[:-1]+'a';minimum=.6
    else:continue
    a=np.array(Image.open(ROOT/item['export']))[:,:,3]>128
    b=np.array(Image.open(ROOT/'exports/Art'/f'{identity}.png'))[:,:,3]>128
    iou=lambda m:float((m&b).sum()/(m|b).sum())
    before=iou(a)
    if before>=minimum:continue
    candidates=[(iou(np.roll(a,dx,axis=1)),dx) for dx in range(-8,9)]
    best,dx=max(candidates,key=lambda x:(x[0],-abs(x[1])))
    print(aid,'IoU',round(before,4),'->',round(best,4),'shift',dx)
    if best<minimum:
        print('REGENERATE:',aid);continue
    cleanup=item['cleanup']
    height=re.search(r'--height ([\d.]+)',cleanup).group(1)
    old_offset=float(re.search(r'--offset (-?[\d.]+)',cleanup).group(1))
    pp=ROOT/'_work'/f'{aid.replace("/","__")}_alignment_prompt.txt'
    pp.write_text(item['prompt'],encoding='utf-8')
    subprocess.run([sys.executable,str(ROOT/'source/scripts/production.py'),'process','--id',aid,'--source',str(ROOT/item['source']),'--prompt',str(pp),'--height',height,'--offset',str(old_offset+dx)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
