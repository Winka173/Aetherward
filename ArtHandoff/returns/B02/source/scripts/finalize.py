"""Final provenance receipts and return summary; run after image production and QA."""
from pipeline import *
import hashlib
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=ROOT/'DELIVERABLE_MANIFEST.json';d=read(p)
    requested={a['id']:a for g in read(REPO/'ArtHandoff/requests/B02/INPUT_MANIFEST.json')['groups'] for a in g['assets']}
    assert set(requested)=={a['id'] for a in d['assets']}
    receipt=[]
    for a in d['assets']:
        if a['status']!='delivered':continue
        export=ROOT/a['export'];master=ROOT/a['master'];source=ROOT/a['source'];prompt=ROOT/a['prompt']
        im=Image.open(export);mi=Image.open(master);si=Image.open(source)
        assert list(im.size)==requested[a['id']]['size'] and im.mode=='RGBA'
        assert mi.width>=im.width*2 and mi.height>=im.height*2
        assert min(si.size)>=800 and prompt.exists()
        assert im.info.get('srgb')==0 and np.array(im).dtype==np.uint8
        a.update(exportSha256=sha(export),sourceSha256=sha(source),sourceSize=list(si.size))
        a['cleanup']='source/scripts/pipeline.py; source/scripts/jobs.json (manual torso landmarks in source/scripts/anchors.json)'
        a['selfAssessment']='Painterly generated art; manually registered torso and aligned alpha foot row. Review secondary cloth/prop drift in Unity and fine trim at 720p.'
        if 'cinder_evoB' in a['id']:a['selfAssessment']+=' Below intended design fidelity: armor remains warmer/darker than the requested ash-grey plate.'
        if 'freya_evoA' in a['id']:a['selfAssessment']+=' Below intended design fidelity: the Blizzard Witch still reads more regal than wild.'
        receipt.append({'id':a['id'],'exportSha256':a['exportSha256'],'sourceSha256':a['sourceSha256'],'masterSize':list(mi.size),'sourceSize':list(si.size)})
    report=read(ROOT/'qa/intake.json')
    d['producer']='Codex (art production; built-in image generation)'
    d['summary']={'requested':len(requested),'delivered':sum(a['status']=='delivered' for a in d['assets']),'blocked':sum(a['status']=='blocked' for a in d['assets']),'intakeBlocking':len(report['blocking']),'intakeNotes':len(report['notes'])}
    d['heroCheckpoints']={hero:{'delivered':sum(a['status']=='delivered' for a in d['assets'] if a['id'].split('/')[1].split('_')[0]==hero),'complete':all(a['status']=='delivered' for a in d['assets'] if a['id'].split('/')[1].split('_')[0]==hero)} for hero in ('terra','sylph','marina','ignis','cinder','volt','freya')}
    d['knownIssues']=['B01 and live project files changed concurrently; reconcile B02 identities against the latest B01 revision before acceptance.','Cinder Ash Guardian is warmer/darker than the ash-grey brief; Freya Blizzard Witch remains regal.','Fine trim compresses at 720p; whole-pose swaps require Unity review for secondary cloth/prop and perceived-scale drift.']
    d['blockers']=[]
    d['extras']=[{'path':'qa/intake.json','kind':'handoff intake report'},{'path':'qa/local_measurements.json','kind':'bounds/foot/edge measurements'},{'path':'qa/source_receipts.json','kind':'source/export hashes and resolution receipts'},{'path':'qa/scope_audit.json','kind':'concurrent working-tree change audit'},{'path':'previews/roster_colour_1440p.png','kind':'2560x1440 offline review; not Unity'},{'path':'previews/roster_gray_720p.png','kind':'grayscale at 720p game scale'},{'path':'previews/roster_silhouette_720p.png','kind':'silhouettes at 720p game scale'}]
    write(ROOT/'qa/source_receipts.json',receipt);write(p,d)
    print(d['summary'])
if __name__=='__main__':main()
