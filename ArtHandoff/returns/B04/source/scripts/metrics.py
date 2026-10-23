from pathlib import Path
import json
from PIL import Image
import numpy as np
from scipy.ndimage import binary_erosion
root=Path(__file__).resolve().parents[2]
metrics=[]
for p in sorted((root/'exports/Art/Heroes').glob('*.png')):
 a=np.array(Image.open(p).convert('RGBA'));m=a[:,:,3]>128;e=m&~binary_erosion(m,iterations=3);yy,xx=np.where(m)
 metrics.append(dict(id='Heroes/'+p.stem,edgeLuminance=float(np.mean(a[:,:,:3][e]@np.array([.2126,.7152,.0722]))/255),bbox=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],footRow=int(yy.max()),size=list(a.shape[1::-1])))
(root/'qa/local_metrics.json').write_text(json.dumps(metrics,indent=2))
print(json.dumps(metrics,indent=2))
