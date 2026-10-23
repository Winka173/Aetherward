from pipeline import *
def ingest(name,specs):
    path=ROOT/f'source/sheets/{name}.png'
    if not path.exists():return
    raw=Image.open(path);w,h=raw.size
    assets=[]
    for i,(id,size,height,foot,maxwidth) in enumerate(specs):
        cuts={'ignis_evolutions':[0,460,1025,1515,2048],'terra_base':[0,560,1200,1774],'terra_wide':[0,730,1370,2048],'sylph_base':[0,550,1240,1774],'marina_base':[0,550,1320,1774]}.get(name)
        crop=[cuts[i],0,cuts[i+1],h] if cuts else [round(w*i/len(specs)),0,round(w*(i+1)/len(specs)),h]
        if name=='storm_harpy':
            crop=([0,0,950,h] if i==0 else [900,0,w,h])
            if i==1:
                aa=np.array(raw.crop([0,0,950,h]))[:,:,3];bb=np.array(raw.crop(crop))[:,:,3]
                ya=np.where(aa>32)[0];yb=np.where(bb>32)[0];height=205*(yb.max()-yb.min()+1)/(ya.max()-ya.min()+1)
        if name=='storm_harpy_v3' and i==1:
            aa=np.array(raw.crop([0,0,w//2,h]))[:,:,3];bb=np.array(raw.crop(crop))[:,:,3];ya=np.where(aa>32)[0];yb=np.where(bb>32)[0];height=184*(yb.max()-yb.min()+1)/(ya.max()-ya.min()+1)
        assets.append(dict(id=id,size=size,crop=crop,height=height,foot=foot,maxWidth=maxwidth,removeCutNeighbours=True))
    j=dict(source=f'source/sheets/{name}.png',prompt=f'source/prompts/{name}.json',assets=assets)
    jobs=read(ROOT/'source/scripts/jobs.json');jobs=[q for q in jobs if q['source']!=j['source']];jobs.append(j);write(ROOT/'source/scripts/jobs.json',jobs);process(j)
def run():
    for name in ['terra','sylph','marina']:
        ingest(name+'_base',[(f'Heroes/{name}_{s}',[400,400],height,372,316 if name=='terra' else 308) for s,height in [('idle',270 if name=='terra' else 280),('cast',285),('downed',225)]])
    ingest('ignis_evolutions',[(f'Heroes/ignis_{s}',[400,400],h,372,312) for s,h in [('evoA',288),('evoA_cast',288),('evoB',280),('evoB_cast',280)]])
    for name,height,width in [('juggernaut',210,224),('hexcaster',185,208),('storm_harpy',205,232),('rift_warden',435,464)]:
        size=[512,512] if name=='rift_warden' else [256,256];foot=486 if name=='rift_warden' else (208 if name=='storm_harpy' else 236)
        ingest(name,[(f'Enemies/{name}_{s}',size,height,foot,width) for s in ['a','b']])
    ingest('terra_wide',[(f'Heroes/terra_{s}',[400,400],height,372,316) for s,height in [('idle',270),('cast',285),('downed',225)]])
    ingest('hexcaster_v2',[(f'Enemies/hexcaster_{s}',[256,256],185,236,208) for s in ['a','b']])
    ingest('storm_harpy_v2',[(f'Enemies/storm_harpy_{s}',[256,256],173,202,228) for s in ['a','b']])
    ingest('storm_harpy_v3',[(f'Enemies/storm_harpy_{s}',[256,256],184,202,232) for s in ['a','b']])
if __name__=='__main__':run()
