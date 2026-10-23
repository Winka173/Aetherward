"""R1 measurements and labelled comparisons; never modifies sprite art."""
import hashlib
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt
from produce import ROOT, read, write

dm=read(ROOT/'DELIVERABLE_MANIFEST.json')
rows=[]
for a in dm['assets']:
    n=a['id'].split('/')[-1]
    im=Image.open(ROOT/a['export']).convert('RGBA'); ar=np.array(im)
    old=np.array(Image.open(ROOT/'source/revision0/exports/Art'/f'{a["id"]}.png').convert('RGBA'))
    mask=ar[:,:,3]>128; om=old[:,:,3]>128
    hsv=np.array(im.convert('RGB').convert('HSV')).astype(float)/255
    red=mask & ((hsv[:,:,0]<.04)|(hsv[:,:,0]>.92)) & (hsv[:,:,1]>.4) & (hsv[:,:,2]>.15)
    ind=distance_transform_edt(~mask,return_distances=False,return_indices=True)
    low=ar[:,:,3]<32
    fringe_ok=bool(np.all(ar[low,:3]==ar[ind[0][low],ind[1][low],:3]))
    rows.append({'id':a['id'],'revision':a.get('revision',0),'edgeLuminance':a['metrics']['edgeLuminance'],'footRow':a['metrics']['footRow'],'size':list(im.size),'hasSRGB':b'sRGB' in (ROOT/a['export']).read_bytes(),'masterSize':list(Image.open(ROOT/a['master']).size),'redPixelFractionDiagnostic':float(red.sum()/mask.sum()),'r0SilhouetteIoU':float((mask&om).sum()/(mask|om).sum()),'nearestOpaqueDefringe':fringe_ok})
for page in range((len(rows)+8)//9):
    sheet=Image.new('RGB',(1536,880),'#292b30'); d=ImageDraw.Draw(sheet)
    d.text((12,8),'B08 R1 / OFFLINE BEFORE (left) AND AFTER (right) / SAME 256 CANVAS / PAGE '+str(page+1),fill='white')
    for j,row in enumerate(rows[page*9:page*9+9]):
        x=(j%3)*512;y=30+(j//3)*282;n=row['id'].split('/')[-1]
        for k,path in enumerate([ROOT/'source/revision0/exports/Art'/f'{row["id"]}.png',ROOT/'exports/Art'/f'{row["id"]}.png']):
            im=Image.open(path).convert('RGBA');sheet.paste(im,(x+k*256,y),im)
        d.text((x+8,y+256),n+' R0 | R1',fill='white')
    sheet.save(ROOT/f'qa/r1_before_after_{page+1}.png')
write(ROOT/'qa/r1_metrics.json',{'revision':1,'frames':rows,'redDiagnostic':'HSV colour count is a diagnostic, not a material-area or semantic palette measurement; warm reflected light can be included. Palette placement is visually assessed.','minEdge':min(r['edgeLuminance'] for r in rows),'allRevised':all(r['revision']==1 for r in rows),'minR0SilhouetteIoU':min(r['r0SilhouetteIoU'] for r in rows)})
print({'frames':len(rows),'revised':sum(r['revision']==1 for r in rows),'minEdge':min(r['edgeLuminance'] for r in rows),'maxRedDiagnostic':max(r['redPixelFractionDiagnostic'] for r in rows),'defringeProblems':[r['id'] for r in rows if not r['nearestOpaqueDefringe']]})
