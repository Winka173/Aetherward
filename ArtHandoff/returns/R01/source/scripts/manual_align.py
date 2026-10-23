"""Utility-only torso translations chosen from qa/anchors_*.png overlays."""
import json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
# Absolute offset from centered alpha bounding box, in export pixels.
adjust={
 'Heroes/veyra_idle':(None,32),
 'Heroes/veyra_walk_a':(None,8),
 'Heroes/veyra_walk_b':(None,17),
 'Heroes/veyra_attack':(None,17),
 'Heroes/veyra_cast':(None,24),
 'Heroes/veyra_downed':(None,8),
 'Heroes/glacius_attack':(None,6),
 'Heroes/glacius_downed':(None,6),
 'Heroes/ignis_attack':(322,16),
 'Heroes/ignis_downed':(None,-16),
 'Heroes/marina_attack':(None,16),
}
manifest=json.loads((ROOT/'DELIVERABLE_MANIFEST.json').read_text(encoding='utf-8'))
records=[]
for aid,(height,offset) in adjust.items():
    item=next(x for x in manifest['assets'] if x['id']==aid)
    if height is None:height=float(re.search(r'--height ([\d.]+)',item['cleanup']).group(1))
    pp=ROOT/'_work'/f'{aid.replace("/","__")}_manual_alignment_prompt.txt'
    pp.write_text(item['prompt'],encoding='utf-8')
    subprocess.run([sys.executable,str(ROOT/'source/scripts/production.py'),'process','--id',aid,'--source',str(ROOT/item['source']),'--prompt',str(pp),'--height',str(height),'--offset',str(offset)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    records.append(dict(id=aid,height=height,offset=offset,method='Visual torso alignment from separate overlays; no anatomy redrawn.'))
(ROOT/'qa/manual_alignment.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
print('Aligned',len(records),'frames; source/masters and 400 contracts use identical framing.')
