"""Utility torso centering from separate enemy anchor overlays."""
import json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
offsets={
 'grunt_a':-16,'grunt_b':-16,'grunt_attack':8,
 'runner_a':-8,'runner_b':-8,
 'juggernaut_a':6,'juggernaut_attack':6,
 'ravager_b':-8,'ravager_attack':-6,
 'rift_warden_a':-24,'rift_warden_b':-24,
 'rift_warden_tell':-16,'rift_warden_attack':-16,
}
manifest=json.loads((ROOT/'DELIVERABLE_MANIFEST.json').read_text(encoding='utf-8'))
records=[]
for name,offset in offsets.items():
    aid='Enemies/'+name;item=next(x for x in manifest['assets'] if x['id']==aid)
    height=float(re.search(r'--height ([\d.]+)',item['cleanup']).group(1))
    pp=ROOT/'_work'/f'Enemies__{name}_manual_alignment_prompt.txt';pp.write_text(item['prompt'],encoding='utf-8')
    subprocess.run([sys.executable,str(ROOT/'source/scripts/production.py'),'process','--id',aid,'--source',str(ROOT/item['source']),'--prompt',str(pp),'--height',str(height),'--offset',str(offset)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    records.append(dict(id=aid,height=height,offset=offset,method='Visual torso alignment from separate overlays; no anatomy redrawn.'))
(ROOT/'qa/manual_enemy_alignment.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
print('Aligned',len(records),'enemy frames.')
