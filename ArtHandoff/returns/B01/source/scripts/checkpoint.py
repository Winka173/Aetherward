from pipeline import *
from PIL import ImageDraw
import shutil
if __name__=='__main__':
    name=sys.argv[1]
    if name=='P0':
        src=ROOT/'source/sheets/style_concept.png'
        im=Image.open(src).convert('RGB').resize((1920,1080),Image.Resampling.LANCZOS)
        dr=ImageDraw.Draw(im);dr.rectangle((0,1048,1920,1080),fill='#1d1f24');dr.text((16,1057),'CONCEPT PAINTING - composition study; not a Unity screenshot or production battlefield',fill='#dae4eb')
        im.save(ROOT/'previews/style_frame_1080p.png')
        # Reprocess refined Crystal render.
        jobs=read(ROOT/'source/scripts/jobs.json')
        for j in jobs:
            if 'crystal_intact' in j['source']:process(j)
        register('World/crystal_intact','source/blender/crystal.blend','source/blender/crystal.py','blender:source/blender/crystal.py',assessment='Faceted relic with procedural painterly surface; requires owner review.')
    d=read(MANIFEST);d.setdefault('checkpoints',[]).append({'tier':name,'delivered':sum(a['status']=='delivered' for a in d['assets'])});write(MANIFEST,d);write(ROOT/f'qa/manifest_{name}.json',d)
