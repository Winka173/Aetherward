"""R1 utility export only: crop, fit, align, Lanczos, defringe. Never paints art."""
from pipeline import *
from scipy.ndimage import binary_erosion

def export_one(record):
    uid=record['id']; d=read(MANIFEST)
    entry=next(x for x in d['assets'] if x['id']==uid)
    im=Image.open(ROOT/record['source']).convert('RGBA')
    w,h=entry['size']; mult=2
    a=np.array(im); box=Image.fromarray(np.uint8(a[:,:,3]>32)*255).getbbox()
    if not box: raise ValueError(uid+': empty alpha')
    cropped=im.crop(box)
    out=Image.new('RGBA',(w*mult,h*mult))
    if uid.startswith('Icons/'):
        factor=min(w*mult*.88/cropped.width,h*mult*.88/cropped.height)
        if factor>1:raise ValueError(uid+': source too small; cannot upscale')
        cropped=cropped.resize((round(cropped.width*factor),round(cropped.height*factor)),Image.Resampling.LANCZOS)
        out.paste(cropped,((out.width-cropped.width)//2,(out.height-cropped.height)//2))
    else:
        before=Image.open(ROOT/record['reference']).convert('RGBA')
        bb=Image.fromarray(np.uint8(np.array(before)[:,:,3]>32)*255).getbbox()
        factor=min((bb[2]-bb[0])/cropped.width,(bb[3]-bb[1])/cropped.height)
        if factor>1:raise ValueError(uid+': source too small; cannot upscale')
        cropped=cropped.resize((round(cropped.width*factor),round(cropped.height*factor)),Image.Resampling.LANCZOS)
        x=(bb[0]+bb[2]-cropped.width)//2
        oldlow=np.where(np.array(before)[:,:,3]>128)[0].max()
        low=np.where(np.array(cropped)[:,:,3]>128)[0].max()
        out.paste(cropped,(x,int(oldlow-low)))
    master=f'source/masters/{uid}@2x.png'; save(out,ROOT/master)
    final=out.resize((w,h),Image.Resampling.LANCZOS)
    save(final,ROOT/f'exports/Art/{uid}.png')
    entry.update(status='delivered',revision=1,changeNote=record['changeNote'],export=f'exports/Art/{uid}.png',source=record['source'],master=master,generator='image_generation (built-in image_gen; version not exposed)',prompt=record['promptFile'],cleanup='source/scripts/revision1.py',selfAssessment='R1 generated art; owner acceptance pending.')
    entry.pop('reason',None);d['revision']=1;write(MANIFEST,d)
    if not uid.startswith('Icons/'):
        ar=np.array(final); mask=ar[:,:,3]>128;edge=mask&~binary_erosion(mask,iterations=3)
        print(uid,'edge luminance',float((ar[:,:,:3]@[.2126,.7152,.0722]/255)[edge].mean()))

if __name__=='__main__':
    records=[]
    selection_path=ROOT/'source/revision1_selections.json'
    selections=read(selection_path) if selection_path.exists() else {}
    if len(sys.argv)>1 and sys.argv[1]=='select':
        uid,source,prompt_file=sys.argv[2:5]
        selections[uid]=dict(source=source,promptFile=prompt_file)
        write(selection_path,selections)
    for p in sorted((ROOT/'source/prompts').glob('r1_*.json')):
        prompt=read(p);stem=p.stem
        if stem.startswith('r1_icons_'):
            uid='Icons/'+stem[len('r1_icons_'):]
            rec=dict(id=uid,source='source/sheets/'+stem+'.png',promptFile=p.relative_to(ROOT).as_posix(),changeNote='R1: generated engraved medallion with the specified symbol.')
        else:
            ref=prompt.get('reference','')
            if not ref.startswith('source/revision0/'):continue
            uid=ref[len('source/revision0/'):-4]
            rec=dict(id=uid,source='source/sheets/'+stem+'.png',reference=ref,promptFile=p.relative_to(ROOT).as_posix(),changeNote='R1 D2: strengthened back-right rim and lifted key planes using original frame as reference.')
        rec.update(selections.get(uid,{}))
        if (ROOT/rec['source']).exists():records.append(rec)
    write(ROOT/'source/revision1_records.json',records)
    for record in records:
        if (ROOT/record['source']).exists():export_one(record)
