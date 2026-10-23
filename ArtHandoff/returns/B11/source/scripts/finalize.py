"""Finalize provenance after exports, visual review, local QA and formal intake."""
import json, hashlib
from pathlib import Path
from PIL import Image
import numpy as np
from scipy.ndimage import distance_transform_edt
import production as p

ASSESS={
'siegebreaker_golem':'Stone/iron ram-arm silhouette reads clearly; revised impact has stronger follow-through. Fine cracks compress at 720p.',
'ignaroth':'Magma seams and heavy fists read clearly against basalt. Vent and crust detail is dense at 720p.',
'vaelith':'Copper wings and violet spear distinguish her silhouette. Feather contour and cloth folds vary slightly across poses.',
'mirrath':'Mirror halo and asymmetric silver facets remain recognizable; revised attack includes the whole glass focus. Focus contours vary with grip and foreshortening.',
'aetherion':'Corrected weapon-free crystal identity is maintained in all four poses. Small floating-facet contours vary between key poses.',
'thornmother':'Rooted trunk, thorn arms and pale bark separate well from basalt. Blossoms and fine branches soften at 720p.',
'ironclad_warlord':'Block siege hammer, riveted bulk and back banner read as a faction apex. Banner folds and rivets vary slightly between poses.',
'ashen_matriarch':'Cocoon abdomen, long claws and clinging imps give a distinct hunched silhouette. Tiny imps are secondary detail at 720p.',
'nyxhollow':'Central maw, eye ring and jointed limbs break the armored-human rhythm. Small star-holes are secondary detail at 720p.',
'seraphyne':'Ice-spire crown, glacier hem and frost sceptre form a regal silhouette. Fine ice cuts soften at 720p.',
'gravemaw':'Chest maw vent and shoulder mortars distinguish the siege titan. Fine plate/rust detail is dense at 720p.',
'rift_warden':'B01 identity references anchor the new raised-glaive tell and downward impact. Small halo/cloak/weapon contours vary with the changed pose.'}

def run():
    dm=p.read(p.ROOT/'DELIVERABLE_MANIFEST.json')
    req=p.read(p.ROOT/'qa/contract_facts.json')
    facts={f['id']:f for g in req['groups'] for f in g['assets']}
    records=p.read(p.ROOT/'source/records.json')
    local=p.read(p.ROOT/'qa/local_metrics.json')
    intake=p.read(p.ROOT/'qa/intake.json')
    if local['problems']:raise ValueError(local['problems'])
    if intake['blocking']:raise ValueError(intake['blocking'])
    audit=[]
    for d in dm['assets']:
        aid=d['id']; r=records[aid]; f=facts[aid]
        if d['status']!='delivered':raise ValueError('not delivered: '+aid)
        for field in ['source','master','prompt','export']:
            if not (p.ROOT/d[field]).is_file():raise ValueError('missing '+d[field])
        raw=Image.open(p.ROOT/d['source']); master=Image.open(p.ROOT/d['master']); im=Image.open(p.ROOT/d['export'])
        assert master.size==(1024,1024) and im.size==(512,512) and im.mode=='RGBA'
        assert r['scale']<=1 and min(raw.size)>=1024
        assert r['rawTorsoAnchorX'] is not None and abs(r['registeredTorsoX']-256)<=8
        ra=np.asarray(raw.convert('RGBA'))[:,:,3]>128
        raw_border=int(ra[0].sum()+ra[-1].sum()+ra[:,0].sum()+ra[:,-1].sum())
        assert raw_border==0, 'source touches canvas: '+aid
        a=np.asarray(im); opaque=a[:,:,3]>128; fringe=a[:,:,3]<32
        idx=distance_transform_edt(~opaque,return_distances=False,return_indices=True)
        assert np.array_equal(a[fringe,:3],a[idx[0][fringe],idx[1][fringe],:3]), 'defringe: '+aid
        assert p.read(p.ROOT/d['prompt'])['prompt'].startswith(dm['styleLock']['promptTemplate'])
        d.update(ppu=f['ppu'],pivot=f['pivot'],border=f['border'],footRowFromTop=f['footRowFromTop'],selfAssessment=ASSESS[aid.rsplit('_',1)[0].split('/')[-1]])
        d['sha256']={k:hashlib.sha256((p.ROOT/d[k]).read_bytes()).hexdigest() for k in ['source','master','export','prompt']}
        audit.append(dict(id=aid,rawSize=list(raw.size),masterSize=list(master.size),exportSize=list(im.size),sRGB=im.info.get('srgb'),nativeScale=r['scale'],source=d['source'],rawBorderOpaqueCount=raw_border,defringeVerified=True,registeredTorsoX=r['registeredTorsoX']))
    dm['extras']=[dict(path=str(x.relative_to(p.ROOT)).replace('\\','/'),kind='offline QA composite/sheet; not gameplay or approval') for x in sorted((p.ROOT/'previews').glob('*.png'))]
    dm['knownIssues']=['Small facet, branch, feather, rivet and imp details soften at 720p.','Minor generated contour/cloth/prop variation remains across pose changes.','Offline review only; Unity runtime blending, sorting and owner acceptance are not performed.']
    dm['blockers']=[]
    dm['summary']=dict(requested=46,delivered=len(audit),blocked=0,intakeBlocking=len(intake['blocking']),intakeNotes=len(intake['notes']),minimumEdgeLuminance=min(x['edgeLuminance'] for x in local['assets']),minimumWalkIoU=min(x['walkIoU'] for x in local['assets'] if 'walkIoU'in x))
    p.write(p.ROOT/'qa/provenance_audit.json',audit)
    p.write(p.ROOT/'DELIVERABLE_MANIFEST.json',dm)
    print(json.dumps(dm['summary']))

if __name__=='__main__':run()
