from pathlib import Path
import sys,json
import pipeline
root=pipeline.ROOT
uid=sys.argv[1];hero=uid.split('/')[-1];portrait=uid.startswith('Portraits/')
job=dict(id=uid,source=f'source/sheets/{hero}{"_portrait" if portrait else ""}.png',prompt=f'source/prompts/{hero}{"_portrait" if portrait else ""}.json')
if not portrait:
 job.update(height=190 if hero.endswith('_downed') else 280,torsoXRatio=.5)
anchors=root/'source/scripts/anchors.json'
if anchors.exists():job.update(json.loads(anchors.read_text(encoding='utf-8-sig')).get(uid,{}))
jobs_path=root/'source/scripts/jobs.json'
jobs=json.loads(jobs_path.read_text(encoding='utf-8-sig')) if jobs_path.exists() else []
jobs=[j for j in jobs if j['id']!=uid]+[job]
jobs_path.write_text(json.dumps(jobs,indent=2),encoding='utf-8')
pipeline.ingest(job)
print('Registered',uid)
