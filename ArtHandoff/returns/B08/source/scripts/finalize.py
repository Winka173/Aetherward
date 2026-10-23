from produce import ROOT,REPO,read,write
from pathlib import Path
import numpy as np
from PIL import Image

dm=read(ROOT/'DELIVERABLE_MANIFEST.json'); rep=read(ROOT/'qa/validator/report.json'); req=read(REPO/'ArtHandoff/requests/B08/INPUT_MANIFEST.json')
issues=rep['issues']; errors=[i for i in issues if i.get('severity')=='error' and not i.get('waived')]
write(ROOT/'qa/validation_status.json',{'intake':{'delivered':34,'blocking':0,'notes':0},'extendedValidator':{'exitCode':1,'assetsScanned':len(rep['assets']),'blocking':len(errors),'checks':sorted(set(i['check'] for i in errors)),'reason':'14 new attack sprites have no live Unity metadata, import settings or lead-owned asset manifest entries. Intake does not synthesize these. No .meta or live code/data changes are authorized for this art batch. See source/import_plan.json for lead integration facts.'}})
facts=[f for g in req['groups'] for f in g['assets']]
write(ROOT/'source/import_plan.json',{'batch':'B08','owner':'lead integration','instructions':'Read-only plan; no Unity metadata authored by Codex. Apply fixed input-manifest PPU, pivots, borders and flyer flags when importing new attack sprites.','assets':[{k:f[k] for k in ['id','size','ppu','pivot','border','footRowFromTop','flyer','new','like','guid'] if k in f} for f in facts]})
dm['knownIssues']=['Lighting variation across corrected Sapper, Summoner and Banner poses may flicker during swaps.','Torso anchors are visual estimates; fine-detail drift and compact Grunt/Banner attack framing require animation review.','Extended validator has 42 integration-metadata blockers on 14 new attack sprites; lead must create live .meta/import settings and provenance entries. No Unity acceptance performed.']
dm['blockers']=[];dm['integrationRequirements']=['14 new attack sprites need lead-owned Unity metadata, import settings and asset manifest entries; source/import_plan.json records exact contract facts.']
dm['qa']={'intake':'qa/intake.json','local':'qa/local_metrics.json','extended':'qa/validation_status.json','hashes':'qa/artifact_hashes.json','generationCalls':len(list((ROOT/'source/sheets').glob('*.png')))}
dm['extras']=[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'kind':'offline review composite, not a Unity screenshot' if 'scene' in p.name or 'basalt' in p.name else 'offline sprite review sheet'} for p in sorted((ROOT/'previews').glob('*.png'))]
for a in dm['assets']:
 a['selfAssessment']='Readable role silhouette and passing native size/value checks; minor etched and cloth detail changes remain between poses.'
 if 'banner' in a['id']: a['selfAssessment']='Clear banner role; brightened identity cloth differs in value from passing frame, and compact attack approaches the canvas margin.'
 if 'summoner' in a['id'] or 'sapper' in a['id']:a['selfAssessment']='Distinctive staff/bomb identity retained; revised lighting can produce value variation during pose swaps.'
 if 'runner_attack' in a['id']:a['selfAssessment']='Distinct compact bite pose; tail curl changes secondary silhouette relative to walk.'
write(ROOT/'DELIVERABLE_MANIFEST.json',dm)
alpha=[]
for a in dm['assets']:
 ar=np.asarray(Image.open(ROOT/a['export']));alpha.append({'id':a['id'],'mode':'RGBA','bitDepth':8,'hasSRGB':b'sRGB' in (ROOT/a['export']).read_bytes(),'transparentPixels':int((ar[:,:,3]==0).sum())})
write(ROOT/'qa/format_check.json',alpha)
bg=np.asarray(Image.open(REPO/'ArtProduction/generated/World/arena_background.png').convert('RGB'))
write(ROOT/'qa/ground_value.json',{'input':'ArtProduction/generated/World/arena_background.png','meanSRGBLuminance':float((bg@np.array([.2126,.7152,.0722])/255).mean()),'minUnitEdge':min(a['metrics']['edgeLuminance'] for a in dm['assets'])})
print({'delivered':len(dm['assets']),'generationCalls':dm['qa']['generationCalls'],'extendedErrors':len(errors),'errorChecks':dm['qa']})
