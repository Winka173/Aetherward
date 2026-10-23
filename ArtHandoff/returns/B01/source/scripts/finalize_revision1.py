"""Record measured final R1 results. Run after final intake and previews."""
from pipeline import *
import collections

def run():
    d=read(MANIFEST); metrics=read(ROOT/'qa/r1_metrics.json'); intake=read(ROOT/'qa/intake.json')
    records=read(ROOT/'source/revision1_records.json'); changed={r['id']:r for r in records}
    unit_metrics={r['id']:r for r in metrics['units']}
    for a in d['assets']:
        uid=a['id']
        if uid in changed:
            a['revision']=1
            if uid.startswith('Icons/'):
                a['changeNote']='R1: produced section 6.7 engraved bronze/slate medallion with specified symbol; reviewed at 32 px.'
            else:
                r=unit_metrics[uid]
                extra=' Brighter ash mantle and warm hood rim.' if uid.startswith('Heroes/ignis') else ' Pale bone-grey hood lining and brighter sigil.' if 'hexcaster' in uid else ''
                a['changeNote']=f"R1 D2: cool rim and lifted key planes; edge luminance {r['beforeEdgeL']:.3f} -> {r['edgeL']:.3f}."+extra
                a['selfAssessment']='Reference-guided lighting regeneration; original identity retained with some fold/contour drift. Walk-pair IoU and foot alignment checked; Unity acceptance pending.'
                a['qa']='qa/r1_metrics.json; qa/r1_d2_before_after.png'
        else:
            a.setdefault('revision',0)
            a['changeNote']='Retained R0 export; D1/D3 replacement belongs to the lead.' if uid=='World/arena_background' or uid.startswith('World/crystal_') else 'Retained R0 export; outside R1 icon/D2 scope.'
    d['revision']=1
    d['revisionScope']={'newIcons':17,'revisedUnitFrames':11,'retainedPriorExports':49,'leadOwned':['D1: battlefield and layers','D3: Crystal states'],'note':'The 77-export package retains old battlefield/Crystal for continuity; it does not contain the lead replacements.'}
    d['revisionSummary']={'delivered':sum(a['status']=='delivered' for a in d['assets']),'blocked':sum(a['status']=='blocked' for a in d['assets']),'intakeBlocking':len(intake['blocking']),'intakeNotes':len(intake['notes']),'D2ValueNotes':[x for x in intake['notes'] if any(uid+':' in x for uid in unit_metrics)],'minD2EdgeL':min(r['edgeL'] for r in metrics['units']),'groundL':metrics['groundL']}
    d['knownIssues']=[
        'D1 battlefield and D3 Crystal remain R0 in this return. The lead supplies replacements; offline previews show retained R0 environment.',
        'Reference-guided regeneration changes small folds and contours; selective brighter Ignis mantle and hexcaster lining should be checked against unmodified poses in Unity.',
        'Native built-in generations are 1254x1254 despite requests for 2048. All R1 masters meet 2x without upscaling; real Unity/CVD review remains pending.'
    ]
    d['blockers']=[]
    d['revisionQA']={'intake':'qa/intake.json','metrics':'qa/r1_metrics.json','localChecks':'qa/local_metrics.json','icons':'qa/r1_icons_32px.png','beforeAfter':'qa/r1_d2_before_after.png','offlinePreviews':'previews/scene_b01_r1_1440p.png; previews/scene_b01_r1_1080p.png; previews/scene_b01_r1_720p.png','promptSet':'source/prompts/r1_*.json; source/prompts/r1v2_*.json','selectedSources':'source/revision1_records.json','replay':'source/scripts/revision1.py; source/scripts/rebuild.py'}
    write(MANIFEST,d)
    text=(ROOT/'README.md').read_text(encoding='utf-8').replace('## Revision round 1 (in progress)','## Revision round 1').replace('in production','revision 1 delivered',1)
    text=text.split('\n## R1 final results\n')[0]
    s=d['revisionSummary']; notes='\n'.join('- '+x for x in intake['notes']) or '- None.'
    text+='\n## R1 final results\n\n'
    text+=f"Delivered {s['delivered']}/77 batch exports: 17 new icons, 11 revised D2 frames, 49 retained exports. Blocked: {s['blocked']}. Manifest revision: 1. D1/D3 exports and battlefield source layers were not regenerated.\n\n"
    text+=f"Final intake: {s['intakeBlocking']} blocking problems, {s['intakeNotes']} notes, {len(s['D2ValueNotes'])} D2 value notes. Minimum D2 edge luminance: {s['minD2EdgeL']:.3f}; retained battlefield mean: {s['groundL']:.3f}. All 11 D2 frames meet 0.27 and the current battlefield +0.10 criterion. Local utility QA reports 77 exports with no size/foot/walk-pair problems; original Crystal registration is retained. See `qa/intake.json`, `qa/r1_metrics.json` and `qa/local_metrics.json`.\n\n"
    text+='Intake notes remaining outside D2:\n\n'+notes+'\n\n'
    text+='`handoff.py preview` produced 2560x1440, 1920x1080 and 1280x720 offline composites, plus colour, grayscale and silhouette sheets. These use this return\'s R0 battlefield and Crystal until the lead replaces them. They are not Unity screenshots.\n\n'
    text+='Raw R1 generations are native 1254 square. No generation was upscaled. Masters are 800 square for heroes, 512 square for ordinary enemies, 1024 square for the boss, and 192/256 square for icons. Exports use the exact INPUT_MANIFEST dimensions, straight RGBA, sRGB metadata, Lanczos reduction and nearest-opaque defringe. Full actual prompt set: `source/prompts/r1_*.json` and `source/prompts/r1v2_*.json`; chosen raw sources and prompt paths: `source/revision1_records.json`. Mode: built-in image_gen, version not exposed.\n\n'
    text+='Reproduce the R1 exports with `python source/scripts/revision1.py`; it discovers completed first-pass prompts and applies selections from `source/revision1_selections.json`. `python source/scripts/rebuild.py` replays the earlier production pipeline followed by R1 selections. R0 frame masters and rejected first lighting attempts remain available for provenance. `revision1_qa.py` reproduces the R1 metrics and review sheets.\n\n'
    text+='Top three risks:\n\n1. Final scene balance depends on the lead\'s replacement battlefield and Crystal; this return retains the old versions.\n2. Small contour/fold drift and stronger cloth highlights can create lighting variation against unchanged poses; the hexcaster pair has a visibly brighter bone-grey lining and outer folds.\n3. No Unity capture or owner acceptance was performed; 32 px icon readability and 1440p sprite clarity were judged in offline images.\n\n'
    text+='The native generations are detailed; fine cloth texture still compresses at 720p. The brighter directional planes improve separation, but this is not an owner approval. No gameplay/code/import changes are requested. All authored files, QA stage and process temp paths are inside B01. The initial BattleController.cs change is documented in the baseline; final intake lists concurrent external working-tree changes separately. R1 commands did not edit those paths.\n'
    (ROOT/'README.md').write_text(text,encoding='utf-8')
    print(json.dumps(s,indent=2))

if __name__=='__main__':run()
