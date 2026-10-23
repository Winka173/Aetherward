from pipeline import *
from PIL import ImageDraw
from scipy.ndimage import gaussian_filter
def finish():
    jobs=read(ROOT/'source/scripts/jobs.json')
    for state in ['intact','cracked','critical']:
        id='World/crystal_'+state
        j={'source':f'source/masters/World/crystal_{state}_render@2x.png','prompt':'source/blender/crystal.py','assets':[{'id':id,'size':[320,400],'height':306,'foot':372,'maxWidth':276}]}
        jobs=[q for q in jobs if q['source']!=j['source']];jobs.append(j);process(j)
        register(id,'source/blender/crystal.blend','source/blender/crystal.py','blender:source/blender/crystal.py',assessment='Same camera, pedestal and exterior bounds. Damage changes seams/core/glyphs; shards fall inside fixed bounds. Crisp render remains less painterly than character art.')
    write(ROOT/'source/scripts/jobs.json',jobs)
    rawdir=ROOT/'source/battlefield/renders';rawdir.mkdir(parents=True,exist_ok=True)
    if not list(rawdir.glob('*.png')):
        for p in (ROOT/'source/battlefield/layers').glob('*.png'):shutil.copy2(p,rawdir/p.name)
    paintpath=ROOT/'source/sheets/battlefield_paint_finish.png';paint=None
    if paintpath.exists():
        paint=np.array(Image.open(paintpath).convert('RGB').resize((2400,1360),Image.Resampling.LANCZOS))/255.
        low=gaussian_filter(paint,sigma=(14,14,0));texture=np.clip((paint+.035)/(low+.035),.72,1.35)
    for p in rawdir.glob('*.png'):
        im=Image.open(p).convert('RGBA')
        if paint is not None and p.name[:2] in ['01','02','03','04','05','07']:
            a=np.array(im);interior=np.clip(distance_transform_edt(a[:,:,3]>128)/8,0,1)
            strength={'01':.22,'02':.40,'03':.25,'04':.55,'05':.20,'07':.70}[p.name[:2]]
            factor=1+(texture-1)*strength*interior[:,:,None];a[:,:,:3]=np.uint8(np.clip(a[:,:,:3]*factor,0,255));im=Image.fromarray(a)
        save(im,ROOT/'source/battlefield/layers'/p.name)
    layers=sorted((ROOT/'source/battlefield/layers').glob('*.png'))
    if len(layers)!=8:raise RuntimeError('Expected eight layers, got '+str(len(layers)))
    im=Image.new('RGBA',(2400,1360),'#1d1f24')
    for p in layers:im=Image.alpha_composite(im,Image.open(p).convert('RGBA'))
    # Broad edge fade is a compositing utility, not a new painted terrain asset.
    a=np.array(im.convert('RGB'));yy,xx=np.indices((1360,2400));edge=np.minimum.reduce([xx,2399-xx,yy,1359-yy]);f=np.clip(edge/140,0,1);f=f*f*(3-2*f)
    a=np.uint8(a*f[:,:,None]+np.array([29,31,36])*(1-f[:,:,None]));im=Image.fromarray(a)
    dest=ROOT/'exports/Art/World/arena_background.png';dest.parent.mkdir(parents=True,exist_ok=True);info=PngInfo();info.add(b'sRGB',b'\x00');im.save(dest,pnginfo=info)
    register('World/arena_background','source/blender/battlefield.blend','source/blender/battlefield.py; source/prompts/battlefield_paint_finish.json','blender:source/blender/battlefield.py + image_generation surface finish',assessment='Geometry follows live lane/node coordinates. Eight isolated render layers with geometry-preserving generated brush texture; cross-layer shadows approximated in layer08. Terrain remains more restrained than concept.')
    guide=Image.open(REQUEST/'references/guides/layout__World__arena_background.png').convert('RGBA');Image.blend(im.convert('RGBA'),guide,.32).save(ROOT/'qa/layout_overlay.png')
    d=read(MANIFEST);d['extras']=[{'path':'previews/style_frame_1080p.png','kind':'concept painting'}]+[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'kind':'battlefield layer'} for p in layers];write(MANIFEST,d)
if __name__=='__main__':finish()
