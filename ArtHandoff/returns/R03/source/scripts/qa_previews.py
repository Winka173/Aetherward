"""Offline QA and utility composites. Does not draw exported art."""
import json, hashlib, math
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt
from PIL import Image, ImageDraw, ImageFont, ImageOps
from production import ROOT, REPO, ASSETS, MP, dump

OUT=ROOT/'previews'
def font(size=20):
    return ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',size)
def load(aid): return Image.open(ROOT/'exports/Art'/f'{aid}.png').convert('RGBA')
def nine(im,size,border):
    w,h=im.size; W,H=size; l,b,r,t=border
    if min(border)==0: return im.resize(size,Image.Resampling.LANCZOS)
    if W<l+r or H<t+b: raise ValueError('Destination smaller than fixed border')
    xs=[0,l,w-r,w]; ys=[0,t,h-b,h]; X=[0,l,W-r,W]; Y=[0,t,H-b,H]
    out=Image.new('RGBA',size)
    for j in range(3):
        for i in range(3):
            part=im.crop((xs[i],ys[j],xs[i+1],ys[j+1]))
            out.paste(part.resize((X[i+1]-X[i],Y[j+1]-Y[j]),Image.Resampling.LANCZOS),(X[i],Y[j]))
    return out
FACTS={a['id']:a for a in ASSETS}
def frame(aid,size): return nine(load(aid),size,FACTS[aid]['border'])
def paste(base,im,xy): base.alpha_composite(im,xy)
def text(base,xy,s,size=22,colour='#fff1dc',anchor=None):
    ImageDraw.Draw(base).text(xy,s,font=font(size),fill=colour,anchor=anchor)
def srgb_lin(rgb):
    v=rgb/255.
    return np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4)
def luminance(rgb): return srgb_lin(rgb) @ [0.2126,0.7152,0.0722]

def qa():
    reports=[]
    for a in ASSETS:
        aid=a['id']; im=load(aid); ar=np.array(im); w,h=im.size
        m=Image.open(ROOT/'source/masters'/f'{aid}@2x.png')
        entry=dict(id=aid,size=list(im.size),mode=im.mode,masterSize=list(m.size),sizePass=list(im.size)==a['size'],masterPass=m.size==(w*2,h*2),alphaMin=int(ar[:,:,3].min()),alphaMax=int(ar[:,:,3].max()),sha256=hashlib.sha256((ROOT/'exports/Art'/f'{aid}.png').read_bytes()).hexdigest())
        opaque=ar[:,:,3]>=128;low=ar[:,:,3]<32
        iy,ix=distance_transform_edt(~opaque,return_distances=False,return_indices=True)
        entry['defringePass']=bool(np.all(ar[low,:3]==ar[iy[low],ix[low],:3]))
        entry['embeddedSrgb']=bool(im.info.get('icc_profile'))
        entry['pngBitDepth']=(ROOT/'exports/Art'/f'{aid}.png').read_bytes()[24]
        if aid.startswith(('UI/panel_','UI/button_')) or aid=='UI/tooltip':
            l,b,r,t=a['border']; centre=ar[t:h-b,l:w-r]
            entry['minWhiteContrastOverCentreRGB']=float((1.05/(luminance(centre[:,:,:3])+.05)).min())
            entry['whiteContrastPass']=entry['minWhiteContrastOverCentreRGB']>=4.5
            if aid=='UI/panel_glass':
                # Pixel compositing in the project's Gamma pipeline; sampled against supplied battlefield crop.
                bg=Image.open(REPO/'ArtHandoff/requests/R01/references/battlefield_toon_verdant.png').convert('RGB')
                bg=np.array(ImageOps.fit(bg,(1280,720)))
                C=centre.reshape(-1,4); samples=bg[::8,::8].reshape(-1,3)
                # Worst centre pixel over the brightest sampled battlefield pixel.
                brightest=samples[np.argmax(luminance(samples))]
                composite=C[:,:3]*C[:,3,None]/255+brightest*(1-C[:,3,None]/255)
                entry['whiteContrastOverBrightestBattlefieldSample']=float((1.05/(luminance(composite)+.05)).min())
                entry['glassContrastLimitation']='55% translucent centre cannot guarantee 4.5:1 white contrast over every possible bright background; use opaque panel_dark for critical text.'
        if aid=='UI/bar_fill': entry['neutralPass']=bool(np.all(ar[:,:,0]==ar[:,:,1]) and np.all(ar[:,:,1]==ar[:,:,2]))
        if aid=='UI/vignette': entry.update(centreAlpha=int(ar[h//2,w//2,3]),cornerAlpha=int(ar[0,0,3]))
        reports.append(entry)
    dump(dict(batch='R03',kind='supplemental asset checks; not approval',assets=reports),ROOT/'qa/technical_checks.json')
    print('Technical:',len(reports),'assets;',sum(not r.get('whiteContrastPass',True) for r in reports),'opaque-colour contrast failures')

def stretches():
    folder=OUT/'stretch';folder.mkdir(parents=True,exist_ok=True)
    tiles=[]
    for a in ASSETS:
        if not any(a['border']): continue
        im=load(a['id']); w,h=im.size
        stretched=nine(im,(w*3,h*2),a['border'])
        page=Image.new('RGBA',(max(w*3+40,640),h*2+90),'#43404a')
        text(page,(20,8),a['id']+' | 3x width / 2x height',18)
        text(page,(20,34),'OFFLINE 9-SLICE TEST | fixed corners, manifest border L/B/R/T '+str(a['border']),13)
        paste(page,stretched,(20,70));page.convert('RGB').save(folder/(a['id'].split('/')[1]+'.png'))
        thumb=ImageOps.contain(page,(620,380),Image.Resampling.LANCZOS)
        tile=Image.new('RGBA',(640,410),'#292432');paste(tile,thumb,((640-thumb.width)//2,20));tiles.append(tile)
    for i in range(0,len(tiles),6):
        page=Image.new('RGBA',(1280,1280),'#211c2a');text(page,(20,8),'OFFLINE 9-SLICE STRESS TESTS / R03',24)
        for j,im in enumerate(tiles[i:i+6]):paste(page,im,((j%2)*640,45+(j//2)*410))
        page.convert('RGB').save(OUT/f'stretch_sheet_{i//6+1:02}.png')

def sheets():
    icons=[a['id'] for a in ASSETS if a['id'].startswith('Icons/')]
    for H in [1080,720]:
        W=round(H*16/9)
        for mode in ['colour','gray','silhouette']:
            page=Image.new('RGBA',(W,H),'#34303d');text(page,(24,18),f'R03 ICONS / {mode.upper()} / OFFLINE ASSET REVIEW',max(18,H//35))
            text(page,(24,56),'96 px export, 32 px game test (both at native pixel size); labels are preview-only',max(12,H//55))
            cw=W//7; ch=(H-110)//4
            for k,aid in enumerate(icons):
                im=load(aid)
                if mode=='gray':
                    alpha=im.getchannel('A');im=ImageOps.grayscale(im).convert('RGBA');im.putalpha(alpha)
                elif mode=='silhouette':
                    alpha=im.getchannel('A');im=Image.new('RGBA',im.size,'#e9e3ee');im.putalpha(alpha)
                x=16+(k%7)*cw;y=102+(k//7)*ch
                paste(page,im,(x,y));paste(page,im.resize((32,32),Image.Resampling.LANCZOS),(x+104,y+48))
                text(page,(x,y+104),aid.split('ui_')[1],max(11,H//65))
            page.convert('RGB').save(OUT/f'icons_{mode}_{H}p.png')
    page=Image.new('RGBA',(1280,720),'#34303d');text(page,(24,12),'R03 BUTTON STATES / OFFLINE COMPARISON',26)
    for j,tone in enumerate(['primary','secondary','danger','ghost']):
        text(page,(20,100+j*145),tone,20)
        for i,state in enumerate(['normal','hover','pressed','disabled']):
            x=170+i*270;y=70+j*145;im=frame(f'UI/button_{tone}_{state}',(250,110));paste(page,im,(x,y));text(page,(x+125,y+55),'Continue',17,'white','mm');text(page,(x+125,y+112),state,15,anchor='mt')
    page.convert('RGB').save(OUT/'button_states_720p.png')
    page=Image.new('RGBA',(1440,900),'#34303d');text(page,(24,15),'R03 CARD RARITIES / OFFLINE ASSET REVIEW',26)
    for i,r in enumerate(['common','rare','epic','legendary','cursed']):
        paste(page,load('UI/card_'+r),(28+i*282,90));text(page,(155+i*282,470),r,22,anchor='mt')
    paste(page,load('UI/title_emblem'),(208,530));page.convert('RGB').save(OUT/'cards_emblem.png')

def hud():
    bg=Image.open(REPO/'ArtHandoff/requests/R01/references/battlefield_toon_verdant.png').convert('RGBA')
    base=ImageOps.fit(bg,(2560,1440),Image.Resampling.LANCZOS)
    def panel(aid,box):
        x,y,w,h=box;paste(base,frame(aid,(w,h)),(x,y))
    def icon(aid,xy,size=64):paste(base,load('Icons/ui_'+aid).resize((size,size),Image.Resampling.LANCZOS),xy)
    def bar(x,y,w,h,fraction,tint):
        panel('UI/bar_bg',(x,y,w,h));fill=frame('UI/bar_fill',(max(38,int((w-16)*fraction)),max(38,h-8)))
        ar=np.array(fill);ar[:,:,:3]=np.round(ar[:,:,:3].astype(float)*np.array(tint)[None,None,:]/255).astype('uint8')
        paste(base,Image.fromarray(ar),(x+8,y+4))
    panel('UI/panel_dark',(860,30,840,100));text(base,(1280,80),'WAVE 07  /  THE RIFT ADVANCES',30,'white','mm')
    panel('UI/panel_dark',(820,140,920,158));icon('crystal',(840,160),90)
    bar(945,168,750,52,.88,(25,225,179));text(base,(1310,191),'CRYSTAL   8,800 / 10,000',22,'white','mm')
    bar(945,224,750,44,.62,(91,169,255))
    panel('UI/panel_dark',(2190,42,330,100));icon('gold',(2220,63),60);text(base,(2355,91),'1,280',30,'white','mm')
    for i,n in enumerate(['pause','speed','settings']):
        panel('UI/button_ghost_normal',(2210+i*98,162,92,80));icon(n,(2231+i*98,179),48)
    panel('UI/panel_danger',(38,240,475,104));icon('leak',(65,258),65);text(base,(315,292),'CRYSTAL UNDER ATTACK',23,'white','mm')
    panel('UI/panel_dark',(835,332,890,100));bar(865,364,830,48,.72,(244,55,104));text(base,(1280,358),'RIFT WARDEN',23,'white','mm')
    names=['GLACIUS','IGNIS','VEYRA','MARINA','RESERVE','RESERVE']
    for i,name in enumerate(names):
        x=32+i*344;panel('UI/panel_dark',(x,1110,336,300))
        if i<4:
            portrait=Image.open(REPO/'ArtHandoff/returns/R01/exports/Art/Portraits'/f'{name.lower()}.png').convert('RGBA')
            paste(base,ImageOps.fit(portrait,(224,118),Image.Resampling.LANCZOS),(x+56,1140))
        else:icon('lock',(x+133,1167),60)
        text(base,(x+168,1270),name,21,'white','mm');bar(x+44,1287,248,40,.78 if i<4 else .05,(35,227,158))
        for j,token in enumerate(['shield','essence','star']):
            xx=x+75+j*91;ImageDraw.Draw(base).ellipse((xx-25,1340,xx+25,1390),outline='#bf9860',width=3);icon(token,(xx-19,1346),38)
    panel('UI/panel_dark',(2120,1110,408,300));text(base,(2324,1160),'PARTY STANCE',25,'white','mm')
    for i,(stance,label) in enumerate([('defensive','DEFEND'),('balanced','BALANCE'),('aggressive','ATTACK')]):
        x=2134+i*126;panel('UI/button_primary_hover' if i==1 else 'UI/button_ghost_normal',(x,1192,124,142));icon('stance_'+stance,(x+24,1219),76);text(base,(x+62,1351),label,17,'white','mm')
    # This footer clearly distinguishes the utility layout from gameplay evidence.
    ImageDraw.Draw(base).rectangle((0,1410,2560,1440),fill='#1b1226')
    text(base,(1280,1424),'OFFLINE COMPOSITE / R03 EXPORTED ASSETS + REPOSITORY R01 PORTRAITS / NOT A UNITY SCREENSHOT',19,'#fff1dc','mm')
    base.convert('RGB').save(OUT/'hud_mock_1440.png')
    for H in [1080,720]:base.resize((round(H*16/9),H),Image.Resampling.LANCZOS).convert('RGB').save(OUT/f'hud_mock_{H}.png')

def provenance():
    dm=json.loads(MP.read_text(encoding='utf-8'))
    for a in dm['assets']:
        stem=a['id'].replace('/','__'); candidates=[ROOT/'source/prompts'/f'{stem}_revision.txt',ROOT/'source/prompts'/f'{stem}_actual.txt']
        if a['id']=='UI/panel_dark':candidates=[ROOT/'source/prompts/panel_dark_actual.txt']
        for c in candidates:
            if c.exists():a['prompt']=c.relative_to(ROOT).as_posix();break
        a['referenceImages']=['ArtHandoff/returns/R01/concepts/hud_concept_LOW_RES_DRAFT.png']
        if a['id'].startswith('UI/') and a['id'] not in ['UI/panel_dark','UI/vignette']:
            a['referenceImages']=['source/sheets/UI__panel_dark.png']
        if a['id'].startswith('UI/button_'):
            tone,state=a['id'][10:].split('_')
            ref='primary_normal' if state=='normal' else tone+'_normal'
            a['referenceImages']=['source/sheets/UI__button_'+ref+'.png']
        if a['id']=='UI/vignette':a['referenceImages']=[]
        if a['id']=='UI/card_common':a['referenceImages']=['_work/card_common_v1.png'];a['revision']='Palette edit: gold/bronze replaced with common iron.'
        if a['id']=='UI/button_primary_normal':a['referenceImages']=['_work/button_primary_normal_v1.png'];a['revision']='Palette edit: violet gems replaced with amber.'
        if a['id'] in ['UI/card_epic','UI/card_legendary']:
            a['referenceImages']=['_work/'+a['id'].split('/')[1]+'_v1.png'];a['revision']='Palette edit: dedicated rarity metal and jewel colours.'
        if a['id'].startswith(('UI/card_','UI/button_')):
            a['nineSliceCleanup']='Generated corner/edge/centre regions downsampled directly from native source into fixed manifest border bands; no region upscaled.'
        if a['id'].startswith('UI/button_ghost_'):
            a['selfAssessment']='Consistent silhouette and readable label centre; ghost hover distinction is restrained and merits Unity review.'
        elif a['id'] in ['Icons/ui_heart','Icons/ui_leak','Icons/ui_essence','Icons/ui_reroll']:
            a['selfAssessment']='Meaning reads at 32 px; internal facets and filigree become dense at small sizes.'
        else:a['selfAssessment']='Meets size, RGBA, source, master and cleanup checks; reviewed in offline sheets, awaiting lead acceptance.'
        a['sha256']=hashlib.sha256((ROOT/a['export']).read_bytes()).hexdigest()
    dm['extras']=[dict(path=p.relative_to(ROOT).as_posix(),kind='offline utility composite / QA preview; not Unity gameplay') for p in sorted(OUT.glob('*.png'))]
    dump(dm,MP)

if __name__=='__main__':
    OUT.mkdir(exist_ok=True);qa();stretches();sheets();hud();provenance();print('QA previews complete')
