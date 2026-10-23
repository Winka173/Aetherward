"""Checkpoint generated sources to the manifest, safe to rerun after each hero."""
from pipeline import *
def scan():
    jobsfile=ROOT/'source/scripts/jobs.json';jobs=read(jobsfile) if jobsfile.exists() else []
    anchors=read(ROOT/'source/scripts/anchors.json')
    byid={j['id']:j for j in jobs}
    for item in read(ROOT/'DELIVERABLE_MANIFEST.json')['assets']:
        uid=item['id'];name=uid.split('/')[1];key=name+('_portrait' if uid.startswith('Portraits/') else '')
        src=f'source/sheets/{key}.png';prompt=f'source/prompts/{key}.json'
        if not (ROOT/src).exists():continue
        j=byid.get(uid,dict(id=uid,source=src,prompt=prompt,height=270))
        if name in anchors:j['torsoXRatio']=anchors[name]
        if uid=='Heroes/terra_evoA':j.update(height=255,dx=-20)
        if uid=='Heroes/terra_evoB':j.update(height=245,dx=-28)
        if uid=='Heroes/cinder_idle':j.update(height=245,dx=0)
        if uid=='Heroes/volt_idle':j.update(height=285,dx=-8)
        if 'downed' in uid:j.update(height=175)
        byid[uid]=j
        ingest(j)
    write(jobsfile,list(byid.values()))
    print('Checkpointed',len(byid),'assets')
if __name__=='__main__':scan()
