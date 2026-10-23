"""R1 utility cleanup only: crop, uniform fit, registration, resample, defringe."""
import sys, shutil
from pathlib import Path
from produce import ROOT, read, write, process

def run(name):
    record=read(ROOT/f'source/prompts/r1/{name}.json')
    old=read(ROOT/'source/revision0/DELIVERABLE_MANIFEST.json')
    original=next(a for a in old['assets'] if a['id']==f'Enemies/{name}')
    job=read(ROOT/'source/revision0/source/prompts/registered'/f'{name}.json')
    job.update(record)
    job['sourceName']='r1_'+name
    job['revision']=1
    job['registration']='Original R0 crop-relative torso anchor retained; inspect R1 comparison for residual drift.'
    path=ROOT/f'source/prompts/r1/{name}.json'
    write(path,job)
    process(path)
    dm=read(ROOT/'DELIVERABLE_MANIFEST.json');dm['revision']=1
    for a in dm['assets']:
        if a['id']==f'Enemies/{name}':
            a['revision']=1
            a['revisionReference']='source/revision0/exports/Art/Enemies/'+name+'.png'
            a['selfAssessment']='R1 palette edit of original pose; utility-only alignment. See R1 QA for final technical and visual assessment.'
    write(ROOT/'DELIVERABLE_MANIFEST.json',dm)

if __name__=='__main__':
    for name in sys.argv[1:]: run(name)
