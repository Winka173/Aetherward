from produce import ROOT,REPO,read,write
from PIL import Image,ImageDraw
import hashlib
dm=read(ROOT/'DELIVERABLE_MANIFEST.json')
bgpath=REPO/'ArtProduction/generated/World/arena_background.png'
bg=Image.open(bgpath).convert('RGBA').resize((2560,1440),Image.Resampling.LANCZOS)
draw=ImageDraw.Draw(bg);draw.rectangle((0,0,2560,38),fill='#202329');draw.text((20,12),'B08 ALL 34 FRAMES / OFFLINE BASALT REVIEW / 1440p PPU SCALE / NOT A UNITY SCREENSHOT',fill='white')
for i,a in enumerate(dm['assets']):
 im=Image.open(ROOT/a['export']).convert('RGBA');n=a['id'].split('/')[-1]; factor=.6*(1.3 if n.startswith('ravager') else .8 if n.startswith('swarmling') else 1)
 im=im.resize((round(256*factor),round(256*factor)),Image.Resampling.LANCZOS)
 x=32+(i%7)*360;y=55+(i//7)*270
 bg.alpha_composite(im,(x+100,y+35)); draw.rectangle((x+50,y+239,x+280,y+258),fill='#24262c');draw.text((x+60,y+242),n,fill='white')
for size,tag in [((2560,1440),'1440p'),((1920,1080),'1080p'),((1280,720),'720p')]:bg.convert('RGB').resize(size,Image.Resampling.LANCZOS).save(ROOT/f'previews/b08_all_frames_basalt_{tag}.png')
req=read(REPO/'ArtHandoff/requests/B08/INPUT_MANIFEST.json')
guides=Image.new('RGB',(8*256,5*256),'#202329')
for i,f in enumerate([f for g in req['groups'] for f in g['assets']]):
 im=Image.open(REPO/f['guide']).convert('RGB');guides.paste(im,((i%8)*256,(i//8)*256))
guides.save(ROOT/'qa/input_guides_read.png')
paths=[bgpath]+[ROOT/a[k] for a in dm['assets'] for k in ['export','master','source','prompt']]
write(ROOT/'qa/artifact_hashes.json',{str(p.relative_to(REPO)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
