"""Final provenance, blocked-concept drafts and honest production summary."""
import hashlib,json,msvcrt,re
from pathlib import Path
from PIL import Image,ImageCms,ImageOps
ROOT=Path(__file__).resolve().parents[2];REPO=ROOT.parents[2]
profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assess={
 'glacius':'Broad ice shield and frost plate read guardian; metal and ice scuffs are dense at720p.',
 'ignis':'Pointed hood, caged focus and ember robes read fire mage; gold and hem ornament is busier than ideal.',
 'veyra':'Long bow and narrow violet silhouette read ranger; torso was aligned independently of the bow bounds.',
 'marina':'Wave crozier and veil read tide healer; pearl jewelry remains dense at small sizes.',
 'grunt':'Hunched fused helm and notched blade read fodder; remaining armor is more elaborate than a minimal mob.',
 'runner':'Low hound-man outline and claws read speed; passing-step motion is restrained to preserve overlap.',
 'hexcaster':'Tall thin hood and lantern read caster; chains and torn hems merge at low resolution.',
 'juggernaut':'Massive shoulders and slab hammer read brute; weapon uses much of the canvas width.',
 'ravager':'Crown, spikes and twin blades read elite; magenta blade accents are conspicuous.',
 'rift_warden':'Cracked halo and glaive read boss; tell and impact need Unity swapping/timing review.'}
request=json.loads((REPO/'ArtHandoff/requests/R01/INPUT_MANIFEST.json').read_text(encoding='utf-8-sig'))
facts={a['id']:a for g in request['groups'] for a in g['assets']}
measure=json.loads((ROOT/'qa/measurements.json').read_text(encoding='utf-8'))
measure={a['id']:a for a in measure}
intake=json.loads((ROOT/'qa/intake.json').read_text(encoding='utf-8'))
concept_records=[]
for name in ['hud_concept','combat_scene_concept']:
    selected=(ROOT/'source/generations/concepts'/f'{name}.png') if name=='hud_concept' else (ROOT/'source/generations/concepts'/f'{name}_native_v1.png')
    draft=ROOT/'concepts'/f'{name}_LOW_RES_DRAFT.png'
    im=Image.open(selected).convert('RGBA');im.save(draft,icc_profile=profile)
    ImageOps.fit(im,(1280,720),method=Image.Resampling.LANCZOS).save(ROOT/'previews'/f'{name}_draft_720p.png',icc_profile=profile)
    attempts=[]
    for suffix,requested in [('_native_v1',[2560,1440]),('',[3840,2160])]:
        path=ROOT/'source/generations/concepts'/f'{name}{suffix}.png'
        attempts.append(dict(requestedSize=requested,returnedSize=list(Image.open(path).size),source=path.relative_to(ROOT).as_posix(),promptFile=f"source/prompts/concepts__{name}{'_v1' if suffix else ''}.txt"))
    concept_records.append(dict(id='concepts/'+name,draftPath=draft.relative_to(ROOT).as_posix(),draftSource=selected.relative_to(ROOT).as_posix(),draftSize=list(im.size),attempts=attempts,status='blocked',reason='Both native2560x1440 and native3840x2160 requests returned1672x941. Required2560x1440 delivery is blocked; no generation was upscaled.'))
(ROOT/'qa/concept_resolution.json').write_text(json.dumps(concept_records,indent=2)+'\n',encoding='utf-8')
with (ROOT/'_work/manifest.write.lock').open('a+b') as lock:
    if lock.tell()==0:lock.write(b'0');lock.flush()
    lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_LOCK,1)
    try:
        mp=ROOT/'DELIVERABLE_MANIFEST.json';m=json.loads(mp.read_text(encoding='utf-8'))
        assert set(facts)=={x['id'] for x in m['assets']}
        for item in m['assets']:
            aid=item['id'];f=facts[aid]
            for key in ['ppu','pivot','border','footRowFromTop','new','like']:
                if key in f:item[key]=f[key]
            name=next(n for n in assess if aid.split('/')[1]==n or aid.split('/')[1].startswith(n+'_'))
            item['selfAssessment']=assess[name]
            if aid.startswith('Portraits/'):
                item['selfAssessment']='Head-and-shoulders identity matches the sprite; flat violet background has a one-pixel transparent perimeter for the RGBA intake gate.'
            if 'silhouetteIoU' in measure[aid]:item['silhouetteIoU']=measure[aid]['silhouetteIoU']
            if not aid.startswith('Portraits/'):item['edgeBandLuminance']=measure[aid]['edgeLuminance']
            promptfile=ROOT/'source/prompts'/f"final__{aid.replace('/','__')}.txt";promptfile.write_text(item['prompt'],encoding='utf-8')
            height=re.search(r'--height ([\d.]+)',item['cleanup']).group(1);offset=re.search(r'--offset (-?[\d.]+)',item['cleanup']).group(1)
            item['promptFile']=promptfile.relative_to(ROOT).as_posix()
            item['cleanup']=f"python source/scripts/production.py process --id {aid} --source {item['source']} --prompt {item['promptFile']} --height {height} --offset {offset}"
            item['sha256']={key:digest(ROOT/item[key]) for key in ['export','source','master','contractExport','contractMaster'] if item.get(key)}
        for record in concept_records:
            extra=next(x for x in m['extras'] if x.get('id')==record['id']);extra.update(record)
            extra['requestedSize']=[2560,1440]
            extra['selfAssessment']=('MOCKUP / concept, low-resolution draft only. HUD widgets are present; the small Marina field figure has duplicated crozier tips. The two dim portrait cards are reserve slots, not extra delivered heroes.' if record['id'].endswith('hud_concept') else 'MOCKUP / concept, low-resolution draft only. All four heroes, elite, boss and oversized magic read; VFX may obscure targets under heavier density.')
        m['counts']=dict(requestedGameAssets=47,deliveredGameAssets=47,blockedGameAssets=0,requestedConcepts=2,deliveredConcepts=0,blockedConcepts=2,totalRequested=49,totalDelivered=47,totalBlocked=2)
        m['returnStatus']='47 contract sprite/portrait exports delivered; two native2K concepts blocked with labelled low-resolution drafts.'
        m['approvalStatus']='Self-QA only; no lead or owner approval claimed.'
        m['postCleanup']=['python source/scripts/contract_masters.py','python source/scripts/finalize.py']
        m['qa']=dict(intake='qa/intake.json',blocking=len(intake['blocking']),notes=len(intake['notes']),strayWorkingTreeChanges=len(intake['strayWorkingTreeChanges']),measurements='qa/measurements.json',conceptResolution='qa/concept_resolution.json',manualAnchors=['qa/manual_alignment.json','qa/manual_enemy_alignment.json','qa/manual_cast_alignment.json'])
        m['styleLock']['palette']=['#1b1226','#3b2f6b','#7fe3ff','#c0281a','#ff7a1a','#a98bff','#fff36a','#2fb8b0','#5fe0ff','#ff3d8b','#8a2be2']
        m['knownIssues']=[
          'R01 prose requests400/800 hero pairs while INPUT_MANIFEST/intake require512. Both are supplied:512 exports with1024 masters, plus400 contract copies and800 masters.',
          'Both concept size requests failed at1672x941, including fresh4K attempts. Only labelled LOW_RES_DRAFT copies are in concepts/.',
          'Cast/tell poses and manually aligned torsos require lead review while swapping frames in Unity; a numeric intake pass is not animation or beauty approval.',
          'Fine metal scuffs, cloth motifs, pearls and enemy fragments merge at720p. High-density VFX readability remains a concept target.',
          'Portraits retain a flat dark-violet background with a one-export-pixel clear perimeter to satisfy the input RGBA transparency gate.',
          f"Intake lists{len(intake['strayWorkingTreeChanges'])} out-of-scope working-tree changes. This run made workspace writes only inside R01 and left those paths alone."]
        m['blockers']=[r['id']+': '+r['reason'] for r in concept_records]
        m['inputs']=['ArtHandoff/requests/R01/CODEX_ART_REQUEST.md','ArtHandoff/requests/COMMON_CONTRACT.md','ArtHandoff/requests/R01/INPUT_MANIFEST.json','ArtProduction/ART_BIBLE.md (superseded style rules not applied)','ArtProduction/designs/heroes.json','ArtProduction/designs/enemies.json','Assets/_Aetherward/Resources/Content/heroes.json','Assets/_Aetherward/Resources/Content/enemies.json','Assets/_Aetherward/Resources/Content/elements.json','ArtHandoff/requests/R01/references/','ArtHandoff/requests/pose_refs/']
        temporary=mp.with_name(mp.name+'.tmp');temporary.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');temporary.replace(mp)
        summary=dict(counts=m['counts'],intake=m['qa'],maxUnitInk=max(x['edgeLuminance'] for aid,x in measure.items() if not aid.startswith('Portraits/')),heroWalkMinIoU=min(x['silhouetteIoU'] for aid,x in measure.items() if '_walk_' in aid),enemyWalkMinIoU=min(x['silhouetteIoU'] for aid,x in measure.items() if aid.startswith('Enemies/') and 'silhouetteIoU' in x))
        (ROOT/'qa/production_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
        readme=(ROOT/'source/README_TEMPLATE.md').read_text(encoding='utf-8')
        replacements={'{{BLOCKING}}':str(summary['intake']['blocking']),'{{NOTES}}':str(summary['intake']['notes']),'{{STRAY}}':str(summary['intake']['strayWorkingTreeChanges']),'{{MAX_INK}}':f"{summary['maxUnitInk']:.3f}",'{{HERO_IOU}}':f"{summary['heroWalkMinIoU']:.3f}",'{{ENEMY_IOU}}':f"{summary['enemyWalkMinIoU']:.3f}"}
        for before,after in replacements.items():readme=readme.replace(before,after)
        (ROOT/'README.md').write_text(readme,encoding='utf-8')
    finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
print(json.dumps(summary,indent=2))
