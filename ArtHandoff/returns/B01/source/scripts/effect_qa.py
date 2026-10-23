from pipeline import *
from PIL import ImageDraw
def tint(im,hex):
    a=np.array(im.convert('RGBA'));c=np.array([int(hex[i:i+2],16) for i in (1,3,5)])/255;a[:,:,:3]=np.uint8(a[:,:,:3]*c);return Image.fromarray(a)
def run():
    bg=Image.open(ROOT/'exports/Art/World/arena_background.png').crop((900,450,1500,1050)).resize((256,256)).convert('RGBA')
    cases=[('Vfx/telegraph','#ff3a4a'),('Vfx/ring','#ff6a2b'),('Vfx/ring','#2f8cff'),('Vfx/ring','#5fe8c8'),('Vfx/glow','#2f8cff'),('World/node_empty','#ff6a2b'),('World/node_occupied','#c98a3e'),('World/node_highlight','#5fe8c8')]
    out=Image.new('RGBA',(4*270,2*300),'#1d1f24');d=ImageDraw.Draw(out)
    for i,(id,c) in enumerate(cases):
        tile=bg.copy();im=tint(Image.open(ROOT/f'exports/Art/{id}.png'),c)
        if id in ['Vfx/ring','Vfx/telegraph']:im=im.resize((230,143),Image.Resampling.LANCZOS)
        else:im.thumbnail((230,210),Image.Resampling.LANCZOS)
        tile.alpha_composite(im,((256-im.width)//2,(256-im.height)//2));x=(i%4)*270;y=(i//4)*300;out.alpha_composite(tile,(x+7,y));d.text((x+7,y+264),id+' '+c,fill='white')
    out.convert('RGB').save(ROOT/'qa/tinted_vfx.png')
    neutral=[]
    for id in ['Vfx/ring','Vfx/telegraph','Vfx/glow','UI/bar_fill','World/node_empty','World/node_occupied','World/node_highlight']:
        p=ROOT/f'exports/Art/{id}.png'
        if p.exists():
            a=np.array(Image.open(p));neutral.append({'id':id,'maxChannelDifference':int(np.abs(np.diff(a[:,:,:3].astype('int16'),axis=2)).max())})
    write(ROOT/'qa/tint_neutrality.json',neutral)
    reg=[]
    for p in (ROOT/'source/battlefield/renders').glob('*.png'):
        final=ROOT/'source/battlefield/layers'/p.name
        reg.append({'layer':p.name,'alphaUnchanged':bool(np.array_equal(np.array(Image.open(p))[:,:,3],np.array(Image.open(final))[:,:,3]))})
    write(ROOT/'qa/battlefield_registration.json',{'layers':reg,'allAlphaUnchanged':all(x['alphaUnchanged'] for x in reg),'projection':'Ground coordinates from arena.json mapped to(x,y/0.62,0); camera horizontal scale30, elevation asin(0.62); controlled surface texture never changes layer alpha.'})
if __name__=='__main__':run()
