import argparse, json, shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageCms, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parents[2]
REQ = REPO / 'ArtHandoff/requests/R05'
LIVE = REPO / 'Assets/_Aetherward/Resources/Art'
FACTS = [a for g in json.loads((REQ/'INPUT_MANIFEST.json').read_text(encoding='utf-8'))['groups'] for a in g['assets']]
STYLE = 'Dark arcane fantasy, premium hand-inked comic 2.5D; tapered bold black-violet #1b1226 outer contours, thinner internal ink; 2-3 flat cel tones per material; hard cool violet-blue #3b2f6b shadows; warm upper-left-front key; saturated jewel hero colours and muted bone/rust/charcoal enemies with magenta/violet rift accents under 15%. No rim light, no airbrush gradients.'
POSES = {
 'walk_c': 'Opposite-leg CONTACT walking pose relative to the walk_a reference: swap leading and trailing legs, other foot forward toward +X, arms counter-swung the opposite way. Clear foot separation.',
 'walk_d': 'Opposite PASSING pose relative to walk_b reference: reverse leg roles, trailing foot passing under torso, other foot planted, body at highest point of the cycle, arms counter-swung. Exaggerated clear leg separation.',
 'c': 'Opposite-leg CONTACT walking pose relative to a reference: reverse which leg leads and which trails, other foot forward toward +X, arms counter-swung. Clear silhouette.',
 'd': 'Opposite PASSING pose relative to b reference: reverse leg roles, other foot supports body, trailing foot passes underneath. Body at highest cycle point.',
 'windup': 'Strong ANTICIPATION before attack reference. Weight on rear foot, body coiled, torso twisted away from +X; melee weapon drawn BACK and UP behind body, claws pulled back; ranged bow at FULL DRAW with string hand near cheek; caster staff pulled back with tiny charging focus glow. Clearly differs from strike.',
 'follow': 'Strong FOLLOW-THROUGH AFTER attack reference. Weight fully forward, torso leaning toward +X, melee weapon PAST target LOW and ACROSS body; ranged/caster arm still extended with visible recoil, cloth swinging forward. Clearly differs from strike.',
 'idle_b': 'Extremely subtle BREATHING variant of identity idle. Keep feet, legs, head, hands, prop, costume and silhouette position exactly fixed. Raise only chest and shoulders 2-3 export pixels (4-6 master pixels), shift cloth and hair slightly. Must alternate as breathing, never a jump or new stance.'
}

def savejson(path, obj):
 path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')

def init():
 for d in ['source/raw','source/masters','source/prompts','exports/Art','previews','qa','_work/tmp']:(ROOT/d).mkdir(parents=True,exist_ok=True)
 mp=ROOT/'DELIVERABLE_MANIFEST.json'
 if not mp.exists():savejson(mp,{'batch':'R05','producer':'Codex','date':'2026-10-21','styleLock':{'direction':'Art Bible v3; R01 sections 1-2 replace B01 and old rim/value rules','promptTemplate':STYLE},'tools':[{'name':'image_gen built-in','version':'not exposed'},{'name':'Python','packages':['Pillow','numpy','scipy']}],'assets':[],'extras':[],'knownIssues':[],'blockers':[]})
 jobs=[]
 for f in FACTS:
  cat,name=f['id'].split('/');char=f['like'].split('/')[1].rsplit('_',1)[0];suffix=name[len(char)+1:]
  neighbor=char+('_walk_a' if suffix=='walk_c' else '_walk_b' if suffix=='walk_d' else '_a' if suffix=='c' else '_b' if suffix=='d' else '_attack' if suffix in ('windup','follow') else '_walk_b')
  refs=[str(LIVE/(f['like']+'.png')),str(LIVE/cat/(neighbor+'.png')),str(REPO/f['guide'])]
  n=f['size'][0]*2
  prompt=f"Use case: stylized-concept. Production animation sprite {f['id']} for Aetherward. Input 1 is CHARACTER IDENTITY; input 2 is NEIGHBOURING POSE; input 3 is canvas guide ONLY, never draw the guide. Generate ONE character pose on a {n}x{n} genuinely transparent RGBA canvas. Preserve exact identity, face, anatomy, costume, palette, prop design, handedness, and scale of input 1. {POSES[suffix]} "
  if suffix!='idle_b':prompt+='Premium action-game key pose, strong line of action, about 15% more limb stretch than realistic. '
  prompt+=f"Camera unchanged: orthographic three-quarter front, 38 degree elevation, facing screen-RIGHT. Torso on x={n//2}; feet at y={f['footRowFromTop']*2}; match head and body scale of identity. {STYLE} Character only. No background, ground shadow, particles, projectile, beam, extra limbs, labels, letters, guide lines or framing. Only a small local glow on existing weapon/focus allowed. Never redesign the character."
  pp='source/prompts/'+f['id']+'.txt';(ROOT/pp).parent.mkdir(parents=True,exist_ok=True);(ROOT/pp).write_text(prompt,encoding='utf-8')
  jobs.append({'id':f['id'],'references':refs,'prompt':prompt,'promptFile':pp})
 savejson(ROOT/'_work/jobs.json',jobs)
 print('Initialized',len(jobs),'jobs')

def bbox(im):
 a=np.array(im)[:,:,3]>128;y,x=np.where(a);return int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)

def defringe(im):
 a=np.array(im);mask=a[:,:,3]<32
 if mask.any():
  idx=distance_transform_edt(mask,return_distances=False,return_indices=True);a[mask,:3]=a[idx[0][mask],idx[1][mask],:3]
 return Image.fromarray(a,'RGBA')

def process(aid,src):
 f=next(x for x in FACTS if x['id']==aid);mp=ROOT/'DELIVERABLE_MANIFEST.json';dm=json.loads(mp.read_text(encoding='utf-8'))
 raw=ROOT/'source/raw'/(aid+'.png');raw.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,raw)
 im=Image.open(raw).convert('RGBA');ident=Image.open(LIVE/(f['like']+'.png')).convert('RGBA')
 ib=bbox(ident);b=bbox(im);n=f['size'][0]*2
 # Uniform scaling and translation only. Never warp or redraw anatomy.
 lp=ROOT/'source/landmarks.json'
 lm=json.loads(lp.read_text()) if lp.exists() else {}
 point=lm.get(aid)
 scale=2*(ib[3]-ib[1])/(b[3]-b[1])
 requested_scale=scale
 anchor=im.width/2
 if point:
  anchor=point['torsoX'];scale=2*(f['footRowFromTop']-point['identityHeadTop'])/(b[3]-1-point['headTop'])
  requested_scale=scale
 if aid.startswith('Heroes/'):
  # The hero icon box is 10%-90% of canvas width. Keep all props inside it.
  margin=n*.1+3
  scale=min(scale,(n/2-margin)/max(1,anchor-b[0]),(n/2-margin)/max(1,b[2]-anchor))
  scale=min(scale,(f['footRowFromTop']*2-n*.2-3)/(b[3]-b[1]))
 scale=min(scale,(n-16)/(b[2]-b[0]),1.0)
 scaled=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
 sb=bbox(scaled);foot=f['footRowFromTop']*2
 dx=round(n/2-anchor*scale);dy=foot-(sb[3]-1)
 # Keep alpha within the canvas using only global translation.
 dx=max(4-sb[0],min(dx,n-4-sb[2]))
 master=Image.new('RGBA',(n,n));master.alpha_composite(scaled,(dx,dy));master=defringe(master)
 masterpath=ROOT/'source/masters'/(aid+'@2x.png');masterpath.parent.mkdir(parents=True,exist_ok=True)
 profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
 master.save(masterpath,icc_profile=profile)
 out=defringe(master.resize(tuple(f['size']),Image.Resampling.LANCZOS));ep=ROOT/'exports/Art'/(aid+'.png');ep.parent.mkdir(parents=True,exist_ok=True);out.save(ep,icc_profile=profile)
 job=next(j for j in json.loads((ROOT/'_work/jobs.json').read_text(encoding='utf-8')) if j['id']==aid)
 rec={'id':aid,'status':'delivered','reviewStatus':'unapproved candidate','export':ep.relative_to(ROOT).as_posix(),'size':f['size'],'source':raw.relative_to(ROOT).as_posix(),'master':masterpath.relative_to(ROOT).as_posix(),'generator':'image_gen built-in','prompt':job['promptFile'],'references':job['references'],'cleanup':'source/scripts/produce.py process --id '+aid+' --source <generated PNG>','thirdPartyInputs':[],'selfAssessment':'Generated key pose; utility-aligned to a manually estimated torso/head landmark and exact foot row. See README for pose and continuity defects; delivery does not mean approval.','cleanupFacts':{'rawSize':list(im.size),'uniformScale':scale,'requestedBodyScale':requested_scale,'scaleConstrainedByCanvas':scale<requested_scale*.98,'translation':[dx,dy],'exportOpaqueBounds':bbox(out),'landmark':point}}
 dm['assets']=[a for a in dm['assets'] if a['id']!=aid]+[rec];savejson(mp,dm);print(aid,'saved',bbox(out))

def finish_manifest():
 mp=ROOT/'DELIVERABLE_MANIFEST.json';dm=json.loads(mp.read_text(encoding='utf-8'));jobs=json.loads((ROOT/'_work/jobs.json').read_text(encoding='utf-8'));errors=json.loads((ROOT/'qa/generation_errors.json').read_text(encoding='utf-8'))
 for e in errors:
  job=next(j for j in jobs if j['id']==e['id'])
  dm['assets']=[a for a in dm['assets'] if a['id']!=e['id']]+[{'id':e['id'],'status':'blocked','reason':e['error'],'generator':'image_gen built-in','prompt':job['promptFile'],'references':job['references']}]
  savejson(mp,dm)
 dm['assets'].sort(key=lambda a:next(i for i,f in enumerate(FACTS) if f['id']==a['id']))
 issues={
  'Heroes/ignis_walk_c':'Below bar: staff moved to opposite hand. Regenerate before integration.',
  'Heroes/glacius_walk_c':'Below bar: does not clearly reverse the leading leg from walk_a.',
  'Heroes/glacius_walk_d':'Below bar: leg distinction from new walk_c is too weak.',
  'Heroes/veyra_walk_c':'Below bar: opposite-leg contact is insufficiently distinct; compare all four steps.',
  'Heroes/veyra_walk_d':'Below bar: new walk_c/d leg silhouettes are too similar.',
  'Heroes/ignis_follow':'Below bar: raw staff tip touches image edge; icon-box fit reduces body scale.',
  'Heroes/marina_windup':'Below bar: review staff handedness; raised prop forces body scale compromise.',
 }
 for a in dm['assets']:
  if a['status']!='delivered':continue
  if a['id'].endswith('_idle_b'):issues[a['id']]='Below bar: generation changes more contours than a 2-3 pixel breath. Requires identity-preserving regeneration.'
  if a['cleanupFacts']['scaleConstrainedByCanvas']:issues[a['id']]=issues.get(a['id'],'Review: ')+' Body scale reduced to retain props inside icon box; does not meet strict identity-scale continuity.'
  if a['id'] in issues:a['reviewStatus']='needs regeneration';a['selfAssessment']=issues[a['id']]
 dm['knownIssues']=list(dict.fromkeys(issues.values()))
 dm['blockers']=['Built-in image generation daily usage limit: 12 required assets cannot be generated this run. Exact per-asset errors in qa/generation_errors.json.','Quota also prevents regenerating the below-bar candidates identified in selfAssessment.']
 dm['extras']=[{'path':p.relative_to(ROOT).as_posix(),'kind':'offline preview; not gameplay'} for p in sorted((ROOT/'previews').glob('*')) if p.is_file()]
 dm['counts']={'requested':37,'generatedAndExported':sum(a['status']=='delivered' for a in dm['assets']),'blocked':sum(a['status']=='blocked' for a in dm['assets']),'needsRegeneration':sum(a.get('reviewStatus')=='needs regeneration' for a in dm['assets'])}
 savejson(mp,dm);print(dm['counts'])

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command');p.add_argument('--id');p.add_argument('--source');a=p.parse_args()
 if a.command=='init':init()
 elif a.command=='process':process(a.id,a.source)
 elif a.command=='finish':finish_manifest()
