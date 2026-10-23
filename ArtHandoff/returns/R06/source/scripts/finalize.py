"""Utility cleanup only: background, uniform framing, color encoding, QA and previews."""
import json, hashlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageCms, ImageDraw
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[2]
ICC = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
names = ['front', 'threequarter', 'back']
assets, checks, thumbs, gray, silhouettes = [], [], [], [], []
manifest = dict(batch='R06', producer='Codex', date='2026-10-21',
    purpose='Glacius image-to-3D A-pose references; not game sprites',
    tools=[dict(name='image_gen.imagegen (built-in)', version='not reported'),
           dict(name='Python', packages=['Pillow', 'numpy', 'scipy'])],
    styleLock=dict(direction='R01 section 1 comic-ink; R06 neutral flat lighting override',
                   palette=['#1b1226','#3b2f6b','#7fe3ff','#d0d0d0'],
                   light='Even neutral diffuse; no rim light', edge='Tapering black-violet ink'),
    assets=assets,
    knownIssues=['Backplate, shield mounting and rear cloth are inferred from front-only identity.',
                 'Small armor facet and ornament differences remain across views.',
                 'Native generator returned 1254 square despite request for 2048; no upscaling or artificial 2x masters.',
                 'Standard intake unavailable: R06 request has no INPUT_MANIFEST.json.'],
    blockers=['Standard sprite intake cannot run without the lead-owned R06 INPUT_MANIFEST.json.'])

for view in names:
    stem = 'glacius_' + view + '_apose'
    src = ROOT/'source/masters'/f'{stem}.png'
    im = Image.open(src).convert('RGB')
    a = np.asarray(im).astype(np.int16)
    # Background is near-neutral grey; border-connected only, so silver interior stays intact.
    candidates = (a.max(2)-a.min(2) <= 12) & (a.min(2) >= 145)
    seeds = np.zeros(candidates.shape, bool)
    seeds[0,:] = candidates[0,:]; seeds[-1,:] = candidates[-1,:]
    seeds[:,0] = candidates[:,0]; seeds[:,-1] = candidates[:,-1]
    bg = ndi.binary_propagation(seeds, mask=candidates)
    fg = ~bg
    labels, n = ndi.label(fg)
    sizes = np.bincount(labels.ravel()); sizes[0] = 0
    fg = labels == sizes.argmax()
    # Include antialiasing at the ink contour; no anatomy painting.
    fg = ndi.binary_dilation(fg, iterations=1)
    ys,xs = np.where(fg)
    bbox = (int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1))
    rgba = np.dstack((np.asarray(im), fg.astype('uint8')*255))
    cut = Image.fromarray(rgba, 'RGBA').crop(bbox)
    size = im.width
    scale = min(size*.88/cut.width, size*.88/cut.height)
    cut = cut.resize((round(cut.width*scale),round(cut.height*scale)), Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', (size,size), (208,208,208,255))
    pos = ((size-cut.width)//2,(size-cut.height)//2)
    canvas.alpha_composite(cut, pos)
    out = ROOT/'exports'/f'{stem}.png'
    canvas.save(out, icc_profile=ICC)
    # Clean native master, with raw generation separately retained at source/masters.
    mask = Image.new('L', (size,size), 0)
    mask.paste(cut.getchannel('A'), pos)
    bb = mask.point(lambda x: 255 if x>128 else 0).getbbox()
    margin = min(bb[0],bb[1],size-bb[2],size-bb[3])/size
    arr = np.asarray(canvas)
    checks.append(dict(file=str(out.relative_to(ROOT)), size=list(canvas.size),
        mode=canvas.mode, opaque=bool((arr[:,:,3]==255).all()),
        backgroundCornerRGBA=arr[0,0].tolist(), foregroundBounds=list(bb),
        minimumMarginFraction=round(margin,4), sourceSize=list(im.size),
        noUpscaling=scale<=1, sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
        passed=margin>=.059 and scale<=1 and canvas.mode=='RGBA'))
    assets.append(dict(id=stem, character='glacius', status='delivered',
        export=str(out.relative_to(ROOT)).replace('\\','/'), size=list(canvas.size),
        source=f'source/masters/{stem}.png', master=f'source/masters/{stem}.png',
        generator='image_gen.imagegen (built-in)', prompt=f'source/prompts/{stem}.txt',
        references=['source/references/glacius_idle.png'] + ([] if view=='front' else ['source/masters/glacius_front_apose.png']) + (['source/masters/glacius_threequarter_apose.png'] if view=='back' else []),
        cleanup='python source/scripts/finalize.py', thirdPartyInputs=[],
        selfAssessment='Identity and prop handedness retained; small facet drift. Rear-only surfaces inferred.' if view=='back' else 'Strong ice-guardian identity; clean torso silhouette; some extra faceting versus game sprite.'))
    (ROOT/'DELIVERABLE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    thumbs.append(canvas.convert('RGB'))
    gray.append(canvas.convert('L').convert('RGB'))
    sil = Image.new('RGB', canvas.size, '#d0d0d0'); sil.paste((27,18,38), mask=mask)
    silhouettes.append(sil)

for h in [1080,720]:
    for kind, images in [('comparison',thumbs),('grayscale',gray),('silhouette',silhouettes)]:
        w=round(h*16/9); tile=w//3
        sheet=Image.new('RGB',(w,h),'#d0d0d0'); d=ImageDraw.Draw(sheet)
        d.text((16,16),'OFFLINE REFERENCE COMPOSITE - not a game screenshot',fill='#1b1226')
        for i,(v,im) in enumerate(zip(names,images)):
            thumb=im.resize((tile,tile),Image.Resampling.LANCZOS)
            sheet.paste(thumb,(i*tile,(h-tile)//2))
            d.text((i*tile+16,h-35),v,fill='#1b1226')
        sheet.save(ROOT/'previews'/f'{kind}_{h}p.png',icc_profile=ICC)
(ROOT/'qa/reference_validation.json').write_text(json.dumps(dict(
    kind='Custom R06 reference-image checks; not standard intake or art approval',
    delivered=len(assets), blockedAssets=0, blockingImageChecks=sum(not x['passed'] for x in checks),
    standardIntake='BLOCKED: missing requests/R06/INPUT_MANIFEST.json', checks=checks),indent=2)+'\n',encoding='utf-8')
print(json.dumps(checks,indent=2))
