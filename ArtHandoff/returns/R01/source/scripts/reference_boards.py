"""Pack original generated identities as labelled-in-prose concept references."""
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'source/sheets';OUT.mkdir(exist_ok=True)
groups={
 'reference_heroes':(['Heroes/'+n+'_idle' for n in ['glacius','ignis','veyra','marina']],4,512,640),
 'reference_portraits':(['Portraits/'+n for n in ['glacius','ignis','veyra','marina']],4,512,512),
 'reference_enemies':(['Enemies/'+n+'_a' for n in ['grunt','runner','hexcaster','juggernaut','ravager','rift_warden']],3,512,640),
}
for name,(ids,cols,cw,ch) in groups.items():
    board=Image.new('RGBA',(cols*cw,((len(ids)+cols-1)//cols)*ch),(36,25,47,255))
    for i,aid in enumerate(ids):
        p=ROOT/'source/generations'/f'{aid}.png'
        if not p.exists():continue
        im=Image.open(p).convert('RGBA')
        if not aid.startswith('Portraits/'):
            bbox=im.getchannel('A').point(lambda p:255 if p>128 else 0).getbbox()
            im=im.crop(bbox)
        im.thumbnail((cw-24,ch-24),Image.Resampling.LANCZOS)
        board.alpha_composite(im,((i%cols)*cw+(cw-im.width)//2,(i//cols)*ch+(ch-im.height)//2))
    board.save(OUT/f'{name}.png')
    print(name,board.size)
