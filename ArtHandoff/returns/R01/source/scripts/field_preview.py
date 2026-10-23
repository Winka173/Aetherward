"""Offline compositing on the supplied R01 ground, using generated sprites only."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

ROOT=Path(__file__).resolve().parents[2]
REPO=ROOT.parents[2]
W,H=2560,1440
bg=Image.open(REPO/'ArtHandoff/requests/R01/references/battlefield_toon_verdant.png').convert('RGB')
scene=ImageOps.fit(bg,(W,H),method=Image.Resampling.LANCZOS).convert('RGBA')
units=[
 ('Heroes/glacius_idle',.40,.49,300,False),
 ('Heroes/ignis_idle',.30,.63,300,False),
 ('Heroes/veyra_idle',.43,.73,300,False),
 ('Heroes/marina_idle',.53,.68,300,False),
 ('Enemies/grunt_a',.60,.48,256,True),
 ('Enemies/runner_a',.70,.77,256,True),
 ('Enemies/hexcaster_a',.77,.55,256,True),
 ('Enemies/juggernaut_a',.81,.75,256,True),
 ('Enemies/ravager_a',.65,.65,256,True),
 ('Enemies/rift_warden_a',.68,.33,460,True),
]
for aid,x,y,canvas,mirror in sorted(units,key=lambda r:r[2]):
    p=ROOT/'exports/Art'/f'{aid}.png'
    if not p.exists():continue
    im=Image.open(p).convert('RGBA')
    if mirror:im=ImageOps.mirror(im)
    im=im.resize((canvas,canvas),Image.Resampling.LANCZOS)
    px=round(W*x-canvas/2);py=round(H*y-canvas*.93)
    scene.alpha_composite(im,(px,py))
label=Image.new('RGB',(1280,25),(24,17,35));d=ImageDraw.Draw(label)
d.text((8,7),'R01 OFFLINE COMPOSITE / supplied toon battlefield + generated returns / enemies mirrored / not a Unity screenshot',fill='white')
scene.paste(label.resize((2560,50),Image.Resampling.NEAREST),(0,0))
for height in [1440,1080,720]:
    scene.convert('RGB').resize((round(height*16/9),height),Image.Resampling.LANCZOS).save(ROOT/'previews'/f'toon_readability_{height}p.png')
print('Saved supplied-ground readability previews at 1440p, 1080p and 720p.')
