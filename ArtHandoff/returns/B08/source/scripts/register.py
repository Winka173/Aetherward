from produce import ROOT,read,write,process

# Torso positions estimated by visual inspection of the generated anatomy,
# not the asymmetric silhouette or weapon bounds. Fractions are of opaque crop.
ADJUST={
 'shieldbearer_a':{'anchor':.53},'shieldbearer_b':{'anchor':.53},'shieldbearer_attack':{'anchor':.46},
 'sapper_a':{'anchor':.58},'sapper_b':{'anchor':.58},'sapper_attack':{'anchor':.60},
 'warded_a':{'anchor':.57},'warded_b':{'anchor':.57},'warded_attack':{'anchor':.58},
 'summoner_a':{'anchor':.63},'summoner_b':{'anchor':.63},'summoner_attack':{'anchor':.56},
 'banner_a':{'anchor':.70},'banner_b':{'anchor':.70},'banner_attack':{'anchor':.40,'width':210},
 'ravager_attack':{'anchor':.63},'grunt_attack':{'anchor':.39,'width':195},
 'juggernaut_attack':{'anchor':.64},'hexcaster_attack':{'anchor':.60},'storm_harpy_attack':{'anchor':.60}
}
dm=read(ROOT/'DELIVERABLE_MANIFEST.json')
for a in dm['assets']:
 if a['status']!='delivered':continue
 name=a['id'].split('/')[-1]
 job=read(ROOT/a['prompt']); job.update(ADJUST.get(name,{})); job['raw']=str(ROOT/a['source']); job['sourceName']=__import__('pathlib').Path(a['source']).stem
 job['registration']='Torso centre visually estimated; uncertainty approximately 5–8 native export pixels.'
 p=ROOT/f'source/prompts/registered/{name}.json';write(p,job);process(p)
