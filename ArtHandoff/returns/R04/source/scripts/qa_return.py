from pathlib import Path
import json, shutil, hashlib
from PIL import Image
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
REF=ROOT.parents[1]/'requests'/'R04'/'references'
def build(version):
    src=ROOT/'source'/'masters'/f'verdant_{version}.png'
    im=Image.open(src).convert('RGB')
    layout=np.asarray(Image.open(REF/'verdant_layout.png').convert('RGB'),dtype=float)
    guide=np.asarray(Image.open(REF/'verdant_guide.png').convert('RGB'),dtype=float)
    # Isolate actual guide annotation pixels by differencing the matched source.
    # No original terrain is blended into the new painting.
    delta=np.max(np.abs(guide-layout),axis=2)
    mask=(delta>5).astype(np.uint8)*128
    overlay=Image.fromarray(guide.astype(np.uint8),'RGB').convert('RGBA')
    overlay.putalpha(Image.fromarray(mask,'L'))
    overlay=overlay.resize(im.size,Image.Resampling.LANCZOS)
    out=Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB')
    out.save(ROOT/'qa'/f'layout_overlay_{version}.png')
    return im,out
if __name__=='__main__':
    import sys
    im,out=build(sys.argv[1])
    if '--final' in sys.argv:
        shutil.copyfile(ROOT/'source'/'masters'/f'verdant_{sys.argv[1]}.png', ROOT/'exports'/'World'/'verdant_paint.png')
        out.save(ROOT/'exports'/'World'/'verdant_paint_on_guide.png')
        for h in (1080,720):
            # Preview resampling only. Final export remains byte-for-byte native.
            p=im.resize((round(h*16/9),h),Image.Resampling.LANCZOS)
            p.save(ROOT/'previews'/f'verdant_offline_{h}p.png')
            p.convert('L').save(ROOT/'previews'/f'verdant_grayscale_{h}p.png')
        a=np.asarray(im,dtype=float)/255
        lum=a@np.array([.2126,.7152,.0722])
        silhouette=Image.fromarray(np.where(lum<.20,0,255).astype(np.uint8),'L')
        silhouette.resize((1280,720),Image.Resampling.LANCZOS).save(ROOT/'previews'/'verdant_dark_mass_720p.png')
        sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        report={'batch':'R04','kind':'standalone artifact checks; not standard intake or approval',
                'size':list(im.size),'mode':im.mode,'nativeExportUntouched':sha(ROOT/'exports'/'World'/'verdant_paint.png')==sha(ROOT/'source'/'masters'/f'verdant_{sys.argv[1]}.png'),
                'meanGammaLuminance':float(lum.mean()),'previewOnlyResampling':True,
                'guideOverlay':'Source guide annotations isolated by source-layout difference >5; annotation pixels composited at alpha 128/255. Includes cyan socket. No terrain copied.',
                'silhouette':'No unit sprites requested; dark-mass threshold sheet is a composition aid, not unit silhouette QA.',
                'standardIntake':{'status':'blocked','error':"FileNotFoundError: [Errno 2] No such file or directory: requests/R04/INPUT_MANIFEST.json",'log':'qa/standard_intake.log'},
                'standardPreview':{'status':'blocked','log':'qa/standard_preview.log'}}
        (ROOT/'qa'/'artifact_checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'size':im.size,'mode':im.mode}))
