"""Visual torso-anchor overlays, separate from production PNGs."""
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[2]
for name,category in [(n,'Heroes') for n in ['glacius','ignis','veyra','marina']]+[(n,'Enemies') for n in ['grunt','runner','hexcaster','juggernaut','ravager','rift_warden']]:
    poses=['idle','walk_a','walk_b','attack','cast','downed'] if category=='Heroes' else ['a','b','attack','tell']
    ids=[f'{category}/{name}_{p}' for p in poses if (ROOT/'exports/Art'/f'{category}/{name}_{p}.png').exists()]
    if not ids:continue
    board=Image.new('RGBA',(1536,((len(ids)+2)//3)*540),(45,35,56,255))
    d=ImageDraw.Draw(board)
    for i,aid in enumerate(ids):
        x=(i%3)*512;y=(i//3)*540
        im=Image.open(ROOT/'exports/Art'/f'{aid}.png').convert('RGBA');native=im.width
        im=im.resize((512,512),Image.Resampling.NEAREST)
        board.alpha_composite(im,(x,y+28))
        d.text((x+8,y+8),aid+' / red=center, yellow=+/-8 native px',fill='white')
        for col in range(32,512,32):
            d.line((x+col,y+28,x+col,y+539),fill=(90,75,100,255),width=1)
            d.text((x+col+2,y+30),str(round(col*native/512)),fill=(200,190,210,255))
        d.line((x+256,y+28,x+256,y+539),fill=(255,70,70,255),width=2)
        for col in [256-8*512/native,256+8*512/native]:
            d.line((x+int(col),y+28,x+int(col),y+539),fill=(255,230,70,255),width=1)
    board.convert('RGB').save(ROOT/'qa'/f'anchors_{name}.png')
print('Saved separate visual anchor overlays.')
paired=Image.new('RGBA',(1024,2160),(45,35,56,255));pd=ImageDraw.Draw(paired)
for row,name in enumerate(['glacius','ignis','veyra','marina']):
    for col,pose in enumerate(['idle','cast']):
        x=col*512;y=row*540
        im=Image.open(ROOT/'exports/Art/Heroes'/f'{name}_{pose}.png').convert('RGBA')
        paired.alpha_composite(im,(x,y+28))
        pd.text((x+8,y+8),name+' '+pose+' / red torso axis; blue feet; violet head guide',fill='white')
        pd.line((x+256,y+28,x+256,y+539),fill=(255,70,70,255),width=1)
        for column in [248,264]:pd.line((x+column,y+28,x+column,y+539),fill=(255,230,70,255),width=1)
        pd.line((x,y+28+476,x+511,y+28+476),fill=(100,160,240,255),width=1)
        pd.line((x,y+28+166,x+511,y+28+166),fill=(160,100,190,255),width=1)
paired.convert('RGB').save(ROOT/'qa/cast_pair_review.png')
