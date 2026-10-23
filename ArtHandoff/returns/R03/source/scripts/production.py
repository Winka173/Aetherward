import argparse, json, shutil, os
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageCms
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parents[2]
REQUEST = REPO / 'ArtHandoff/requests/R03/INPUT_MANIFEST.json'
ASSETS = [a for g in json.loads(REQUEST.read_text(encoding='utf-8'))['groups'] for a in g['assets']]
MP = ROOT / 'DELIVERABLE_MANIFEST.json'
STYLE = 'Premium dark arcane fantasy comic-ink game UI. Bold tapered black-violet #1b1226 ink contours, 2-3 flat hard-edged cel tones per material, cool violet-blue shadows and warm upper-left key. Forged dark gunmetal, violet-black recesses, worn bronze/gold edge trim, restrained jewel inlays. No soft painterly blending, candy gradients, bubbly shapes or mobile-casual styling. Original design, no letters, numbers, words, watermarks or labels. '

def dump(obj,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')

def init():
    for p in ['_work/tmp','exports/Art/UI','exports/Art/Icons','source/masters/UI','source/masters/Icons','source/sheets','source/prompts','previews','qa']:
        (ROOT/p).mkdir(parents=True,exist_ok=True)
    if not MP.exists():
        dump(dict(batch='R03',producer='Codex',date='2026-10-21',styleLock=dict(palette=['#1b1226','#3b2f6b','#fff1dc'],light='warm upper-left front',edge='black-violet comic ink; old B01/rim rules superseded',promptTemplate=STYLE),tools=[dict(name='image_gen built-in',version='not reported'),dict(name='Python',packages=['Pillow','numpy','scipy'])],assets=[dict(id=a['id'],status='blocked',reason='Not yet generated; production pending') for a in ASSETS],extras=[],knownIssues=[],blockers=[]),MP)
    descriptions={
    'auto':'a clockwise circular arrow enclosing a small angular lightning bolt; automatic combat',
    'check':'a single bold emerald check mark made of forged metal',
    'close':'one bold crimson X made of crossed flat metal bars',
    'codex':'an open ancient violet-bound book with blank parchment pages and bronze corners',
    'crystal':'one upright faceted cyan crystal shard in a minimal bronze cradle',
    'essence':'a violet flame-shaped wisp enclosed by a small arcane bronze vessel',
    'evolve':'three upward-pointing gold chevrons with a small violet crystal at base',
    'gold':'a stack of three thick worn gold coins; geometric crystal stamp, no lettering',
    'heart':'one bold crimson heart with angular cel highlights',
    'history':'an antique bronze circular clock with two simple hands and a counterclockwise arrow; no numerals',
    'leak':'a cracked cyan crystal with a red downward arrow indicating a breached defense',
    'lock':'a closed iron padlock with bronze shackle and simple keyhole',
    'pause':'two upright parallel silver forged bars; pause symbol',
    'play':'one silver triangular play symbol pointing screen-right',
    'reroll':'two bronze circular arrows chasing each other around a small violet dice with dots only',
    'settings':'one forged iron cogwheel with bronze bevel and central hole',
    'shield':'one broad steel kite shield with small cyan central facet',
    'speed':'two bold gold right-pointing chevrons; fast-forward symbol',
    'star':'one five-pointed forged gold star',
    'sword':'one diagonally upright silver sword with bronze crossguard',
    'trophy':'one bronze-gold trophy cup with two angular handles',
    'wave':'three parallel curling cyan wave crests, a bold readable wave symbol',
    'xp':'one luminous emerald four-pointed experience spark in a bronze diamond frame, no letters',
    'stance_defensive':'a tall rectangular steel tower shield with reinforced bronze edges and cyan central gem; distinct from the smaller kite shield icon',
    'stance_balanced':'a symmetrical bronze balance scale with central upright and two equally suspended gold pans',
    'stance_aggressive':'two crossed steel swords with crimson details and bronze hilts'}
    ids=['UI/panel_dark']
    ids += [f'UI/button_{tone}_{state}' for tone in ['primary','secondary','danger','ghost'] for state in ['normal','hover','pressed','disabled']]
    ids += ['UI/bar_bg','UI/bar_fill','UI/panel_glass','UI/panel_light','UI/panel_danger','UI/tooltip']
    ids += ['UI/card_'+r for r in ['common','rare','epic','legendary','cursed']]
    ids += ['UI/title_emblem','UI/vignette']
    ids += [a['id'] for a in ASSETS if a['id'].startswith('Icons/')]
    jobs=[]
    for aid in ids:
        a=next(a for a in ASSETS if a['id']==aid); name=aid.split('/')[1]
        prompt=STYLE+'Use case: stylized-concept. Generate ONE isolated production asset, never a sheet or scene. '
        if aid.startswith('Icons/'):
            prompt+='Square 1024x1024 canvas, genuine transparent background. Subject: '+descriptions[name[3:]]+'. Bold silhouette, 2-3 large colour planes, minimal inner detail. Ink weight must remain clear when downsampled to 32px. Centre the complete symbol inside the central 80 percent of canvas. No surrounding panel, badge background, cast shadow or scenery. '
        elif name=='title_emblem':
            prompt+='Wide landscape 3072x960 canvas (aspect 3.2:1), at least 2048x640 native pixels required. Transparent outside silhouette. A wide forged dark-metal title plate with an original arcane sigil and upright cyan crystal crest at top centre, bronze angular end caps, deep violet recessed EMPTY broad title band. Entire emblem fully inside canvas, 5 percent padding. Blank title band, absolutely no letters. Single front-facing logo plate. '
        elif name=='vignette':
            prompt='Use case: stylized-concept. One plain technical black edge vignette on transparent background, landscape 16:9 canvas 1536x864. Soft smoothly fading dark corners and outer edges, fully transparent large centre. Neutral black/grey only. No ornament, objects, frame, lettering, texture or colour. This asset alone is a soft technical mask. '
        else:
            w,h=a['size']; l,b,r,t=a['border']
            prompt+=f'Front-facing {w}:{h} aspect ratio rectangular nine-slice UI frame, generate at least {max(w*3,768)}x{max(h*3,768)} native resolution preserving the aspect ratio. Transparent outside frame with 3 percent padding. '
            prompt+=f'Export contract {w}x{h}, border left {l}, bottom {b}, right {r}, top {t} px. All important ornaments confined to corner squares within those border bands. Continuous straight stretchable rails, no centre-edge medallions or fixed art across stretch zones. Plain low-contrast dark centre for white overlaid game text, centre luminance below 0.16. No text. '
            if name.startswith('button_'):
                _,tone,state=name.split('_'); accents=dict(primary='worn gold and ember',secondary='arcane teal',danger='crimson',ghost='dark iron with very faint bronze accents')
                states=dict(normal='neutral raised ready state',hover='slightly brighter edge accents with a narrow restrained emissive rim; keep centre dark',pressed='darker recessed inset face and inward bevel',disabled='strongly desaturated muted metal, subdued accents, clearly inactive')
                prompt+=f'Button with {accents[tone]} trim, {states[state]}. Broad empty label area. Match reference geometry and corner proportions closely. '
            elif name=='bar_fill':
                prompt+='NEUTRAL WHITE AND GREY ONLY, no coloured ink or hue; this sprite is multiplied by colour in code. Light silver-grey continuous fill with subtle hard bevel and thin charcoal ink edge. Plain light centre, no ornament; override dark-centre instruction. '
            elif name=='bar_bg': prompt+='Empty bar track of deeply recessed dark iron, simple rail, no gems or decoration. '
            elif name=='panel_glass':prompt+='Translucent glass panel: frame about 70 percent alpha, plain centre about 55 percent alpha. Bronze corners, dark violet glass. '
            elif name=='panel_light':prompt+='Lighter parchment-metal border, aged ivory and bronze rim; centre remains dark muted parchment-violet so white text reads clearly. '
            elif name=='panel_danger':prompt+='Crimson-trimmed alert panel, pointed metal corner caps, restrained red inlays. '
            elif name=='tooltip':prompt+='Compact restrained dark metal tooltip, subtle worn bronze corners, no large gems. '
            elif name.startswith('card_'):
                rarity=name[5:]; acc=dict(common='common iron',rare='rare blue steel',epic='epic violet',legendary='legendary gold',cursed='cursed sick green-black with cracks confined to border')
                prompt+=f'Portrait draft card frame: {acc[rarity]}. Keep BOTH the art window and text area blank, plain and dark. No inner divider across centre, illustration, portrait or lettering. All rarity details inside border. '
            else:prompt+='Main HUD frame matching reference: dark gunmetal with worn bronze angular corner caps, tiny violet gems confined to corners. '
        jobs.append(dict(id=aid,prompt=prompt,transparent_background=True))
    dump(jobs,ROOT/'_work/jobs.json')
    print('Initialized',len(jobs),'jobs')

def defringe(im):
    arr=np.array(im.convert('RGBA')); opaque=arr[:,:,3]>=128; low=arr[:,:,3]<32
    if opaque.any():
        iy,ix=distance_transform_edt(~opaque,return_distances=False,return_indices=True)
        arr[low,:3]=arr[iy[low],ix[low],:3]
    return Image.fromarray(arr,'RGBA')

def pack_borders(im,target,border,kind):
    # Repack generated UI regions into the immutable nine-slice bands.
    # This only downsamples source pixels; it does not draw or invent ornament.
    sw,sh=im.size; W,H=target;l,b,r,t=[v*2 for v in border]
    fx,fy=(.30,.25) if kind=='card' else (.23,.45)
    sx=[0,round(sw*fx),round(sw*(1-fx)),sw];sy=[0,round(sh*fy),round(sh*(1-fy)),sh]
    dx=[0,l,W-r,W];dy=[0,t,H-b,H]; out=Image.new('RGBA',target)
    for j in range(3):
        for i in range(3):
            patch=im.crop((sx[i],sy[j],sx[i+1],sy[j+1]));size=(dx[i+1]-dx[i],dy[j+1]-dy[j])
            if size[0]>patch.width or size[1]>patch.height:raise ValueError('Nine-slice pack would upscale a region')
            out.paste(patch.resize(size,Image.Resampling.LANCZOS),(dx[i],dy[j]))
    return out

def register(aid,path,prompt=None):
    a=next(a for a in ASSETS if a['id']==aid)
    name=aid.replace('/','__')
    src=ROOT/'source/sheets'/f'{name}.png'; shutil.copy2(path,src)
    im=Image.open(src).convert('RGBA'); w,h=a['size']
    # Preserve artwork. Canvas fitting is utility only; never upscale generated pixels.
    scale=min(im.width/(w*2),im.height/(h*2))
    if scale<1: raise ValueError(f'Native source {im.size} below 2x contract {(w*2,h*2)}')
    target=(w*2,h*2); fit=ImageOps.contain(im,target,Image.Resampling.LANCZOS)
    master=Image.new('RGBA',target); master.alpha_composite(fit,((target[0]-fit.width)//2,(target[1]-fit.height)//2))
    if aid.startswith(('UI/card_','UI/button_')):
        master=pack_borders(im,target,a['border'],'card' if aid.startswith('UI/card_') else 'button')
    if aid.startswith('UI/button_'):
        state=aid.rsplit('_',1)[1]
        ar=np.array(master); rgb=ar[:,:,:3].astype(float)
        if state=='disabled':
            grey=rgb @ [0.2126,0.7152,0.0722]
            rgb=(rgb*.18+grey[:,:,None]*.82)*.62
        elif state=='pressed': rgb*=.66
        elif state=='hover': rgb=np.minimum(rgb*1.12,255)
        if '_ghost_' in aid: rgb*=.82
        ar[:,:,:3]=np.clip(rgb,0,255).astype('uint8'); master=Image.fromarray(ar,'RGBA')
    if aid=='UI/bar_fill':
        ar=np.array(master); grey=np.round(ar[:,:,:3] @ [0.2126,0.7152,0.0722]).astype('uint8'); ar[:,:,:3]=grey[:,:,None]; master=Image.fromarray(ar,'RGBA')
    if aid=='UI/panel_glass':
        ar=np.array(master); dark=ar[:,:,:3].max(axis=2)<80
        ar[:,:,3]=np.round(ar[:,:,3]*np.where(dark,.55,.7)).astype('uint8'); master=Image.fromarray(ar,'RGBA')
    profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    master=defringe(master); mp=ROOT/'source/masters'/f'{aid}@2x.png'; mp.parent.mkdir(parents=True,exist_ok=True); master.save(mp,icc_profile=profile)
    out=defringe(master.resize((w,h),Image.Resampling.LANCZOS)); ep=ROOT/'exports/Art'/f'{aid}.png'; ep.parent.mkdir(parents=True,exist_ok=True); out.save(ep,icc_profile=profile)
    jobs=json.loads((ROOT/'_work/jobs.json').read_text(encoding='utf-8'))
    prompt=prompt or next(j['prompt'] for j in jobs if j['id']==aid)
    pp=ROOT/'source/prompts'/f'{name}.txt'; pp.write_text(prompt,encoding='utf-8')
    dm=json.loads(MP.read_text(encoding='utf-8')); entry=next(d for d in dm['assets'] if d['id']==aid)
    entry.clear();entry.update(dict(id=aid,status='delivered',export=ep.relative_to(ROOT).as_posix(),size=[w,h],source=src.relative_to(ROOT).as_posix(),nativeSize=list(im.size),master=mp.relative_to(ROOT).as_posix(),generator='image_gen built-in',prompt=pp.relative_to(ROOT).as_posix(),cleanup='source/scripts/production.py register '+aid,thirdPartyInputs=[],selfAssessment='Generated art, utility fit, button state value/saturation adjustment where applicable, alpha defringe. Pending lead visual acceptance.',ppu=a['ppu'],pivot=a['pivot'],border=a['border']))
    dump(dm,MP); print(aid,'saved',im.size,'->',out.size)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command');p.add_argument('aid',nargs='?');p.add_argument('path',nargs='?');a=p.parse_args()
    if a.command=='init':init()
    elif a.command=='register':register(a.aid,a.path)
    elif a.command=='rebuild':
        folder=ROOT/'_work/rebuild';folder.mkdir(parents=True,exist_ok=True)
        for asset in ASSETS:
            aid=asset['id'];name=aid.replace('/','__')+'.png';copy=folder/name
            shutil.copy2(ROOT/'source/sheets'/name,copy);register(aid,copy)
