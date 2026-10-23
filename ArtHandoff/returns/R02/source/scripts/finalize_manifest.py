"""Complete provenance and evidence links after production and QA."""
import hashlib, json, platform
from pathlib import Path
import PIL, numpy, scipy
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'DELIVERABLE_MANIFEST.json'; dm=json.loads(p.read_text('utf-8'))
corrected={'burst_lightning','impact_fire','impact_ice','ring','telegraph','spark','zone_thunderstorm','zone_healing_rain'}
concept='../R01/concepts/combat_scene_concept_LOW_RES_DRAFT.png'
for f in dm['assets']:
    if f['status']!='delivered': continue
    name=f['id'][4:]
    previous='source/generations/burst_water.png'
    if name in corrected or name=='burst_ice': previous='source/generations/burst_fire.png'
    if name=='burst_water': previous='source/generations/rejected/burst_lightning_v1.png'
    f['references']=[{'path':concept,'role':'comic VFX target; repository-owned concept, not gameplay'}]
    if name!='burst_fire': f['references'].append({'path':previous,'role':'previous burst graphic treatment; initial pass attached its processed master, corrective passes attached raw fire source'})
    f['promptFile']='source/prompts/'+name+'.txt'
    f['sourceSha256']=hashlib.sha256((ROOT/f['source']).read_bytes()).hexdigest()
    f['exportSha256']=hashlib.sha256((ROOT/f['export']).read_bytes()).hexdigest()
    f['selfAssessment']='Reviewed in colour, grayscale and silhouette offline sheets; specific element/direction and transparency contract checked. Runtime tint, blend, motion and stacking remain unverified.'
    if name=='burst_fire': f['selfAssessment']='Strong concept-like curling fire and open arch; dense small embers are the weakest detail at 720p. Uniform 0.65 alpha protects the hero, reducing punch.'
    elif name=='burst_ice': f['selfAssessment']='Large facets and open centre read clearly; small splinters and interior facets compress at game scale. Uniform 0.65 alpha protects the hero.'
    elif name=='burst_lightning': f['selfAssessment']='Corrected to a hard-banded bolt web with open gaps, removing inherited crystals and broad haze. Uniform 0.65 alpha protects the hero.'
    elif name=='burst_water': f['selfAssessment']='Clear curled crown and open protective dome; peripheral cyan halo is softer than the strongest ink/cel target. Uniform 0.65 alpha protects the hero.'
    elif name in ('projectile_fire','projectile_ice','projectile_lightning','projectile_water','fireball'): f['selfAssessment']='Right-facing head and left wake checked; small in the literal PPU preview, so runtime scale and white-core visibility on pale lanes need Unity review.'
    elif name=='telegraph': f['selfAssessment']='Regenerated as a circular hazard rim with inward chevrons; neutral greys and interior opacity verified. Red tint and top-layer visibility need Unity review.'
dm['tools']=[{'name':'image_gen.imagegen (built-in)','version':'not reported by tool'},{'name':'Python','version':platform.python_version(),'packages':{'Pillow':PIL.__version__,'numpy':numpy.__version__,'scipy':scipy.__version__}}]
dm['extras']=[{'path':q.relative_to(ROOT).as_posix(),'kind':'offline composite / contact sheet, not gameplay'} for q in sorted((ROOT/'previews').glob('*.png'))]
dm['knownIssues']=[
 'Runtime blend, opacity, scaling, animation and multi-effect stacking are not verified in Unity; burst exports have a uniform 0.65 alpha multiplier.',
 'Fire embers, ice facets and water foam have more inner detail than ideal at small sizes; burst_water retains a soft peripheral halo.',
 'Neutral telegraph requires runtime red tint and top-layer ordering; tiny projectiles can lose white-core contrast on pale lanes.'
]
dm['blockers']=[f['id']+': '+f.get('reason','') for f in dm['assets'] if f['status']=='blocked']
dm['qa']={'intake':'qa/intake.json','additionalChecks':'qa/vfx_checks.json','preview':'previews/vfx_on_battlefield_1440.png','evidence':'Offline composite only; no Unity approval claimed'}
p.write_text(json.dumps(dm,indent=2)+'\n',encoding='utf-8')
intake=json.loads((ROOT/'qa/intake.json').read_text('utf-8'))
checks=json.loads((ROOT/'qa/vfx_checks.json').read_text('utf-8'))
summary={'delivered':sum(f['status']=='delivered' for f in dm['assets']),'blocked':sum(f['status']=='blocked' for f in dm['assets']),'intakeBlocking':len(intake['blocking']),'additionalBlocking':len(checks['blocking']),'risks':dm['knownIssues']}
(ROOT/'qa/production_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
