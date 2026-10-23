import hashlib, json
from pathlib import Path
from PIL import Image
import numpy as np
from produce import ROOT, FACTS, savejson, bbox, finish_manifest

addenda=json.loads((ROOT/'source/prompts/addenda.json').read_text(encoding='utf-8'))
for aid,extra in addenda.items():
 p=ROOT/'source/prompts'/(aid+'.txt');s=p.read_text(encoding='utf-8')
 if not s.endswith(extra):p.write_text(s+extra,encoding='utf-8')
first=ROOT/'source/prompts/Heroes/glacius_walk_c.txt'
first.write_text((ROOT/'source/prompts/glacius_walk_c_initial.txt').read_text(encoding='utf-8'),encoding='utf-8')
finish_manifest()
dm=json.loads((ROOT/'DELIVERABLE_MANIFEST.json').read_text(encoding='utf-8'))
dm['qa']={'intake':'qa/intake.json','blocking':12,'notes':2,'physicalExports':25,'visualCandidatesNeedingRegeneration':17,'accepted':False}
for a in dm['assets']:
 if a['status']=='delivered':
  a['promptAddendum']='source/prompts/addenda.json' if a['id'] in addenda else None
  a['exportSha256']=hashlib.sha256((ROOT/a['export']).read_bytes()).hexdigest()
dm['knownIssues']+=['Marina windup/follow outer edge luminance 0.25/0.26 exceeds the v3 maximum 0.22.','Intake delivered=37 counts manifest entries including blocked; only 25 PNGs exist.']
savejson(ROOT/'DELIVERABLE_MANIFEST.json',dm)
rows=[]
for a in dm['assets']:
 if a['status']!='delivered':continue
 f=next(f for f in FACTS if f['id']==a['id']);p=ROOT/a['export'];im=Image.open(p);master=Image.open(ROOT/a['master']);b=bbox(im)
 errors=[]
 if list(im.size)!=f['size']:errors.append('wrong canvas')
 if im.mode!='RGBA':errors.append('wrong mode')
 if p.read_bytes()[24]!=8:errors.append('not 8-bit PNG')
 if not im.info.get('icc_profile'):errors.append('missing sRGB profile')
 if abs(b[3]-1-f['footRowFromTop'])>6:errors.append('foot row')
 if min(master.size[0]/im.width,master.size[1]/im.height)<2:errors.append('master below 2x')
 if im.getchannel('A').getextrema()[0]!=0:errors.append('no fully transparent pixels')
 rows.append({'id':a['id'],'bounds':list(b),'footRow':b[3]-1,'masterSize':list(master.size),'errors':errors})
savejson(ROOT/'qa/export_integrity.json',{'checked':len(rows),'blocking':sum(bool(r['errors']) for r in rows),'scope':'File integrity only; does not override intake or visual QA.','rows':rows})
savejson(ROOT/'qa/resume_queue.json',{'generateMissing':[a['id'] for a in dm['assets'] if a['status']=='blocked'],'regenerateCandidates':[{'id':a['id'],'reason':a['selfAssessment']} for a in dm['assets'] if a.get('reviewStatus')=='needs regeneration']})
print(json.dumps({'counts':dm['counts'],'integrityFailures':sum(bool(r['errors']) for r in rows),'previewFiles':len(dm['extras'])}))
