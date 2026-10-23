"""Additional R02 checks independent of intake (RGBA, margins, alpha, tint and defringe)."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
ROOT=Path(__file__).resolve().parents[2]
dm=json.loads((ROOT/'DELIVERABLE_MANIFEST.json').read_text('utf-8'))
rows=[]; errors=[]
for f in dm['assets']:
    if f['status']!='delivered': continue
    im=Image.open(ROOT/f['export']); a=np.array(im); n=f['id'][4:]
    err=[]; alpha=a[:,:,3]; h,w=alpha.shape
    if im.mode!='RGBA' or list(im.size)!=f['size']: err.append('mode/size mismatch')
    if max(alpha[0].max(),alpha[-1].max(),alpha[:,0].max(),alpha[:,-1].max())>8: err.append('clipped edge')
    if n in ('ring','telegraph','spark') and np.max(np.ptp(a[:,:,:3].astype(int),axis=2))!=0: err.append('not tint-neutral')
    if n in ('ring','telegraph') or n.startswith(('zone_','field_')):
        yy,xx=np.ogrid[:h,:w]; region=(xx-w/2)**2+(yy-h/2)**2<(w*.27)**2
        if alpha[region].max()>90: err.append('interior opacity exceeds 35%')
    opaque=alpha>=32
    if opaque.any():
        ni=distance_transform_edt(~opaque,return_distances=False,return_indices=True)
        if not np.array_equal(a[~opaque,:3],a[ni[0][~opaque],ni[1][~opaque],:3]): err.append('defringe mismatch')
    master=Image.open(ROOT/f['master'])
    if master.width<w*2 or master.height<h*2: err.append('master below 2x')
    rows.append({'id':f['id'],'size':list(im.size),'mode':im.mode,'alphaRange':[int(alpha.min()),int(alpha.max())],'opaqueCoverage':round(float((alpha>128).mean()),3),'issues':err})
    errors.extend(f['id']+': '+e for e in err)
out={'batch':'R02','checked':len(rows),'blocking':errors,'rows':rows,'manualReviewRequired':['+X direction','circular ground shape','hard cel shapes','hero readability','Unity blend and animation']}
(ROOT/'qa/vfx_checks.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checked':len(rows),'blocking':errors}))
