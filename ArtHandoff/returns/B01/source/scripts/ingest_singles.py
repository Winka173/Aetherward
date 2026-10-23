from pipeline import *
def single(name,id,neutral=False):
    f=ROOT/f'source/sheets/{name}.png'
    if not f.exists():return
    req=next(a for g in read(REQUEST/'INPUT_MANIFEST.json')['groups'] for a in g['assets'] if a['id']==id)
    j=dict(source=f'source/sheets/{name}.png',prompt=f'source/prompts/{name}.json',assets=[dict(id=id,size=req['size'],masterScale=4 if id.startswith(('Icons/','Vfx/','UI/')) else 2,neutral=neutral)])
    if id.startswith('Vfx/') or id.startswith('Icons/'):j['assets'][0].update(fit=True,margin=.06)
    raw=Image.open(f).convert('RGBA');ar=np.array(raw)
    if id.startswith('World/node_'):
        box=Image.fromarray(np.uint8(ar[:,:,3]>32)*255).getbbox();pad=round(raw.width*.035);j['assets'][0]['crop']=[box[0]-pad,box[1]-pad,box[2]+pad,box[3]+pad]
    jobs=read(ROOT/'source/scripts/jobs.json');jobs=[q for q in jobs if q['source']!=j['source']];jobs.append(j);write(ROOT/'source/scripts/jobs.json',jobs);process(j)
    if id.startswith('Portraits/'):
        # Request allows opaque portraits, but lead intake currently requires one transparent pixel.
        path=ROOT/f'exports/Art/{id}.png';im=Image.open(path);a=np.array(im);a[0,0,3]=0;save(Image.fromarray(a),path)
    if id.startswith('UI/'):
        path=ROOT/f'exports/Art/{id}.png';im=Image.open(path);a=np.array(im);h,w=a.shape[:2];b=48 if id=='UI/card_rare' else req['border'][0]
        if id=='UI/card_rare':
            # Cut the variable centre to true alpha, retaining the generated fixed border.
            a[b:h-b,b:w-b,3]=0
        elif id in ['UI/panel_dark','UI/tooltip']:
            centre=a[b:h-b,b:w-b];pixels=centre[:,:,:3][centre[:,:,3]>128]
            if len(pixels):a[b:h-b,b:w-b,:3]=np.uint8(np.median(pixels,axis=0))
            a[b:h-b,b:w-b,3]=255
        else:
            # Nine-slice packing: retain the painted vertical highlight profile,
            # use one median source swatch per row through the stretching centre.
            for y in range(b,h-b):a[y,b:w-b]=np.uint8(np.median(a[y,b:w-b],axis=0))
        save(Image.fromarray(a),path)
    if id=='World/shadow':
        path=ROOT/f'exports/Art/{id}.png';im=Image.open(path);a=np.array(im);a[:,:,:3]=0;a[:,:,3]=np.uint8(a[:,:,3].astype(float)*(.75*255/max(1,a[:,:,3].max())));save(Image.fromarray(a),path)
    if id=='Vfx/telegraph':
        path=ROOT/f'exports/Art/{id}.png';im=Image.open(path);a=np.array(im);h,w=a.shape[:2];yy,xx=np.indices((h,w));mask=(xx-w/2)**2+(yy-h/2)**2<(w*.32)**2;a[:,:,3][mask]=np.minimum(a[:,:,3][mask],89);save(Image.fromarray(a),path)
    if id in ['Vfx/impact_fire','Vfx/impact_water','Vfx/impact_wind','Vfx/impact_earth']:
        path=ROOT/f'exports/Art/{id}.png';im=Image.open(path);a=np.array(im);h,w=a.shape[:2];yy,xx=np.indices((h,w));mask=(xx-w/2)**2+(yy-h/2)**2<(w*.20)**2;a[:,:,3][mask]=np.minimum(a[:,:,3][mask],153);save(Image.fromarray(a),path)
def run():
    for name in ['ignis','terra','sylph','marina']:single('portrait_'+name,'Portraits/'+name)
    for name in ['node_empty','node_occupied','node_highlight','lane_arrow','shadow']:single(name,'World/'+name,name.startswith('node_'))
    req=read(REQUEST/'INPUT_MANIFEST.json')
    for g in req['groups']:
        for a in g['assets']:
            if a['id'].startswith(('Vfx/','Icons/','UI/')):
                cat,name=a['id'].split('/');single(cat.lower()+'_'+name,a['id'],a['id'] in ['Vfx/ring','Vfx/telegraph','Vfx/glow','UI/bar_fill'])
    single('vfx_glow_v2','Vfx/glow',True)
    single('vfx_zone_burning_ground_v2','Vfx/zone_burning_ground')
if __name__=='__main__':run()
