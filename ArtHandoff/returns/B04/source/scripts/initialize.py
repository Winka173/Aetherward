import json,re,subprocess
from pathlib import Path
r=Path('C:/Users/Winka/Projects/Aetherward'); out=Path.cwd()
ids=['nyxara','ashara','nerissa','voltrix','eirwen','kael']
def read(p):return json.loads(re.sub(r'//[^\n]*','',p.read_text(encoding='utf-8-sig')))
content={}
for name in ['heroes','evolutions','elements']:
 data=read(r/f'Assets/_Aetherward/Resources/Content/{name}.json');content[name]=data
(out/'source/references/content_snapshot.json').write_text(json.dumps(content,indent=2),encoding='utf-8')
req=read(r/'ArtHandoff/requests/B04/INPUT_MANIFEST.json');(out/'source/references/input_manifest.json').write_text(json.dumps(req,indent=2),encoding='utf-8')
lock=read(r/'ArtHandoff/returns/B01/DELIVERABLE_MANIFEST.json')['styleLock']
m={'batch':'B04','producer':'Codex','date':'2026-10-20','styleLock':lock,'tools':[{'name':'image_gen (Codex built-in)','version':'not exposed'},{'name':'Python','packages':['Pillow','numpy','scipy']}],'assets':[dict(id=f['id'],status='blocked',size=f['size'],reason='Production pending; no generated export yet.') for g in req['groups'] for f in g['assets']],'extras':[{'path':'source/references/approved_style_atlas.png','kind':'repository-owned approved B01/B02 style references, composited over neutral ground'}],'knownIssues':[],'blockers':[]}
(out/'DELIVERABLE_MANIFEST.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
baseline=subprocess.run(['git','status','--porcelain','--untracked-files=all'],cwd=r,text=True,capture_output=True)
(out/'qa/workspace_baseline.txt').write_text(baseline.stdout,encoding='utf-8')
print('Initialized manifest:',len(m['assets']),'assets. Read content snapshots.')
