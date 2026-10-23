from PIL import Image,ImageDraw
from pathlib import Path
r=Path('C:/Users/Winka/Projects/Aetherward')
paths=['B01/exports/Art/Heroes/'+n+'.png' for n in ['ignis_idle','ignis_cast','ignis_evoA','terra_idle','sylph_idle','marina_idle']]+['B02/exports/Art/Heroes/cinder_idle.png','B02/exports/Art/Heroes/freya_idle.png']
a=Image.new('RGB',(1600,840),(41,43,48));d=ImageDraw.Draw(a)
for i,p in enumerate(paths):
 im=Image.open(r/'ArtHandoff/returns'/p).convert('RGBA');x=i%4*400;y=i//4*420;a.paste(im,(x,y),im);d.text((x+5,y+402),p.split('/')[0]+' '+Path(p).stem,fill='white')
a.save('source/references/approved_style_atlas.png')
