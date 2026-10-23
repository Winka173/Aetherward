import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageOps
from scipy.ndimage import binary_erosion
from produce import ROOT,REPO,read,write

def run():
 dm=read(ROOT/'DELIVERABLE_MANIFEST.json'); assets=[a for a in dm['assets'] if a['status']=='delivered']; problems=[]; pairs={}
 for a in assets:
  im=Image.open(ROOT/a['export']); ar=np.array(im); m=ar[:,:,3]>128
  if im.size!=(256,256) or im.mode!='RGBA': problems.append(a['id']+': format')
  if a['metrics']['edgeLuminance']<.27: problems.append(a['id']+': edge value below .27')
  n=a['id'].split('/')[-1]; cls='brute' if n.startswith(('ravager','juggernaut')) else 'small' if n.startswith(('runner','swarmling','sapper','riftling','grunt')) else 'medium'
  h=a['metrics']['height']; low,high={'small':(120,160),'medium':(160,190),'brute':(190,215)}[cls]
  if not low<=h<=high: problems.append(a['id']+': size class height '+str(h))
  if cls=='brute' and a['metrics']['width']<200: problems.append(a['id']+': brute width')
  if n.endswith('_a'):
   bp=ROOT/a['export'].replace('_a.png','_b.png')
   if bp.exists():
    b=np.array(Image.open(bp))[:,:,3]>128; iou=float((m&b).sum()/(m|b).sum());pairs[n[:-2]]=iou
    if iou<.6: problems.append(n+': walk IoU '+str(iou))
 for mode in ['colour','grayscale','silhouette']:
  sheet=Image.new('RGB',(1280,720),'#292b30'); draw=ImageDraw.Draw(sheet);draw.text((12,8),'B08 - OFFLINE sprite QA at 720p - '+mode,fill='white')
  for i,a in enumerate(assets):
   im=Image.open(ROOT/a['export']).convert('RGBA')
   if mode=='grayscale': im=Image.merge('RGBA',(*([ImageOps.grayscale(im)]*3),im.getchannel('A')))
   if mode=='silhouette': im=Image.new('RGBA',im.size,'#dce8ee');im.putalpha(Image.open(ROOT/a['export']).getchannel('A'))
   im=im.resize((112,112),Image.Resampling.LANCZOS); x=12+(i%8)*158;y=30+(i//8)*135;sheet.paste(im,(x+18,y),im);draw.text((x,y+112),a['id'][8:],fill='white')
  sheet.save(ROOT/f'previews/b08_{mode}_720p.png')
 write(ROOT/'qa/local_metrics.json',{'delivered':len(assets),'problems':problems,'walkIoU':pairs,'minEdge':min(a['metrics']['edgeLuminance'] for a in assets)})
 print(json.dumps({'problems':problems,'walkIoU':pairs},indent=2))
if __name__=='__main__':run()
