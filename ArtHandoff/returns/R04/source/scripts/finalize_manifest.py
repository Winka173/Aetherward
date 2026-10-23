from pathlib import Path
import json, hashlib
R=Path(__file__).resolve().parents[2]
def sha(rel): return hashlib.sha256((R/rel).read_bytes()).hexdigest()
m=json.loads((R/'DELIVERABLE_MANIFEST.json').read_text(encoding='utf-8'))
m['status']='delivered_with_validation_blocker'
m['assets']=[
 {'id':'World/verdant_paint','status':'delivered','export':'exports/World/verdant_paint.png',
  'size':[1672,941],'mode':'RGB','source':'source/masters/verdant_v3.png','master':'source/masters/verdant_v3.png',
  'generator':'image_gen.imagegen (built-in)','prompt':'source/prompts/verdant_v3.txt',
  'promptHistory':['source/prompts/verdant_v1.txt','source/prompts/verdant_v2.txt','source/prompts/verdant_v3.txt'],
  'cleanup':'None. Byte-identical copy of native output; source/scripts/qa_return.py v3 --final',
  'thirdPartyInputs':[],'selfAssessment':'Clear six-lane composition and comic ink; repeated foliage/masonry still busy. Layout assessed visually, awaiting lead review.'},
 {'id':'World/verdant_paint_on_guide','status':'delivered','export':'exports/World/verdant_paint_on_guide.png',
  'size':[1672,941],'mode':'RGB','source':'source/masters/verdant_v3.png',
  'generator':'Python Pillow/numpy: source/scripts/qa_return.py',
  'prompt':'Derived QA overlay; painting prompt source/prompts/verdant_v3.txt',
  'cleanup':'source/scripts/qa_return.py v3 --final; annotation-only overlay at 50% opacity',
  'thirdPartyInputs':[],'selfAssessment':'Source guide annotation overlay enables direct visual inspection; not automated layout certification.'}]
for a in m['assets']: a['sha256']=sha(a['export'])
m['generationReferences']={
 'v1':['../../../requests/R04/references/'+n for n in ['verdant_layout.png','verdant_guide.png','style_ref_hud_concept.png','style_ref_combat_concept.png']],
 'v2':['source/masters/verdant_v1.png','../../requests/R04/references/verdant_guide.png','../../requests/R04/references/verdant_layout.png'],
 'v3':['source/masters/verdant_v2.png','../../requests/R04/references/verdant_guide.png']}
# Paths above are rooted relative to the return folder.
m['generationReferences']['v1']=[p.replace('../../../','../../') for p in m['generationReferences']['v1']]
m['extras']=[{'path':str(p.relative_to(R)).replace('\\','/'),'kind':'offline inspection image, not gameplay'} for p in sorted((R/'previews').glob('*.png'))]
m['knownIssues']=['Native output 1672x941 despite requested 3840x2160; untouched approximate 16:9 aspect retained.',
 'Generative layout visually assessed, not pixel-exact certified.',
 'Repeated foliage and masonry may gain excess contrast during planned lead upscale.',
 'RGB output has no explicit ICC profile; interpret as sRGB.']
m['counts']={'deliveredImages':2,'blockedImages':0,'blockedWorkflowChecks':2}
m['validation']={'standardIntake':'blocked: missing requests/R04/INPUT_MANIFEST.json',
 'standardPreview':'blocked: missing requests/R04/INPUT_MANIFEST.json','artifactChecks':'qa/artifact_checks.json',
 'layoutReview':'Visual overlay assessed within approximate quarter-lane-width tolerance; no approval claim.'}
(R/'DELIVERABLE_MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
intake={'batch':'R04','status':'blocked','generatedBy':'Codex blocker record; standard handoff.py failed before creating its report',
 'delivered':2,'blockedImageAssets':0,'blocking':['Missing ArtHandoff/requests/R04/INPUT_MANIFEST.json'],
 'standardToolResult':None,'zeroBlockingConfirmed':False,'log':'qa/standard_intake.log'}
(R/'qa'/'intake.json').write_text(json.dumps(intake,indent=2)+'\n',encoding='utf-8')
assert all((R/a['export']).is_file() and (R/a['source']).is_file() for a in m['assets'])
assert sha('exports/World/verdant_paint.png')==sha('source/masters/verdant_v3.png')
print('Manifest saved: 2 delivered images; 0 blocked images; standard intake blocked. Native export hash verified.')
