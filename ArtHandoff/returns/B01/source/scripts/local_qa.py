from pipeline import *
from PIL import ImageDraw
def run():
    req=read(REQUEST/'INPUT_MANIFEST.json');rows=[];problems=[]
    for g in req['groups']:
        for a in g['assets']:
            p=ROOT/f"exports/Art/{a['id']}.png"
            if not p.exists():continue
            im=Image.open(p);ar=np.array(im);row={'id':a['id'],'size':list(im.size),'mode':im.mode}
            if im.mode=='RGBA':
                ys,xs=np.where(ar[:,:,3]>128)
                row['opaqueBounds']=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())] if len(xs) else None
                row['lowestOpaque']=int(ys.max()) if len(ys) else None
                row['alphaRange']=[int(ar[:,:,3].min()),int(ar[:,:,3].max())]
                row['comX']=round(float((xs*ar[ys,xs,3]).sum()/ar[ys,xs,3].sum()),2) if len(xs) else None
            if list(im.size)!=a['size']:problems.append(a['id']+': dimensions')
            if 'footRowFromTop' in a:
                low=row['lowestOpaque'];target=a['footRowFromTop']
                if a.get('flyer'):
                    if low>target-.10*im.height:problems.append(a['id']+': flyer')
                elif abs(low-target)>6+(12 if 'downed' in a['id'] else 0):problems.append(a['id']+': foot')
            rows.append(row)
    pairs=[]
    for name in ['grunt','juggernaut','hexcaster','storm_harpy','rift_warden']:
        paths=[ROOT/f'exports/Art/Enemies/{name}_{s}.png' for s in ['a','b']]
        if all(p.exists() for p in paths):
            aa,bb=[np.array(Image.open(p))[:,:,3]>128 for p in paths];iou=float((aa&bb).sum()/(aa|bb).sum());pairs.append({'enemy':name,'iou':iou})
            if iou<.6:problems.append(name+': IoU below .6')
    crystals=[]
    for s in ['intact','cracked','critical']:
        rr=next((r for r in rows if r['id']=='World/crystal_'+s),None)
        if rr:crystals.append(rr['opaqueBounds'])
    if len(crystals)==3 and len(set(tuple(x) for x in crystals))!=1:problems.append('crystal state bounds differ')
    report=dict(rows=rows,enemyPairs=pairs,crystalBounds=crystals,problems=problems);write(ROOT/'qa/local_metrics.json',report)
    # Explicit dark-background contact sheet, avoiding RGB display ambiguity on alpha previews.
    units=[r for r in rows if r['id'].startswith(('Heroes/','Enemies/','World/crystal'))]
    sheet=Image.new('RGB',(800,((len(units)+4)//5)*170),'#1d1f24');dr=ImageDraw.Draw(sheet)
    for i,r in enumerate(units):
        im=Image.open(ROOT/f"exports/Art/{r['id']}.png");im.thumbnail((145,145),Image.Resampling.LANCZOS);x=(i%5)*160+(160-im.width)//2;y=(i//5)*170;sheet.paste(im,(x,y),im);dr.text(((i%5)*160+3,y+148),r['id'].split('/')[1],fill='#dae4eb')
    sheet.save(ROOT/'qa/units_dark_contact.png');print(json.dumps({'exportCount':len(rows),'problems':problems,'enemyPairs':pairs,'crystalBounds':crystals},indent=2))
if __name__=='__main__':run()
