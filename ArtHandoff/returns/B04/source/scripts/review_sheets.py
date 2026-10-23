"""Offline review sheets; composition only, no asset artwork is drawn."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw,ImageOps
root=Path(__file__).resolve().parents[2]
req=json.loads((root/'source/references/input_manifest.json').read_text())
heroes=['nyxara','ashara','nerissa','voltrix','eirwen','kael']
suffixes=['idle','cast','downed','evoA','evoA_cast','evoB','evoB_cast','attack','evoA_attack','evoB_attack']
for width,height,cell in [(2560,1440,220),(1920,1080,165),(1280,720,110)]:
 for mode in ['colour','grayscale','silhouette']:
  out=Image.new('RGB',(width,height),(170,173,178) if mode=='silhouette' else (38,41,46));d=ImageDraw.Draw(out)
  d.text((16,8),f'B04 OFFLINE REVIEW / {mode} / {width}x{height} / not a Unity capture',fill='white')
  for row,hero in enumerate(heroes):
   for col,suffix in enumerate(suffixes):
    p=root/f'exports/Art/Heroes/{hero}_{suffix}.png'
    x=20+col*(width-40)//10;y=32+row*(height-40)//6
    if not p.exists():d.text((x,y+40),'PENDING',fill=(150,100,100));continue
    im=Image.open(p).convert('RGBA');alpha=im.getchannel('A')
    if mode=='grayscale':im=ImageOps.grayscale(im).convert('RGBA');im.putalpha(alpha)
    if mode=='silhouette':im=Image.new('RGBA',im.size,(0,0,0,255));im.putalpha(alpha)
    im.thumbnail((cell,cell),Image.Resampling.LANCZOS);out.paste(im,(x,y),im)
    d.text((x,y+cell-6),f'{hero}_{suffix}',fill=(215,215,215))
  out.save(root/f'previews/roster_{mode}_{height}p.png')
print('Saved offline colour/grayscale/silhouette sheets at 1440p,1080p,720p.')
