from pipeline import *
import platform, PIL, scipy, hashlib
def run():
    d=read(MANIFEST);d['producer']='Codex';d['tools']=[{'name':'image_gen (Codex built-in)','version':'not exposed','mode':'built-in; no CLI/API fallback'},{'name':'Blender','version':'4.5.14 LTS','path':'C:/Users/Winka/Tools/blender-4.5.14-windows-x64/blender.exe','renderer':'Cycles OPTIX, denoising, RTX GPU'},{'name':'Python','version':platform.python_version(),'packages':{'Pillow':PIL.__version__,'numpy':np.__version__,'scipy':scipy.__version__}}]
    for a in d['assets']:
        if a['status']!='delivered':continue
        id=a['id'];a['cleanup']='python source/scripts/rebuild.py';a['license']='Original generated or authored B01 art; no third-party inputs';a['humanReview']='PENDING'
        p=ROOT/a['export'];a['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
        if id.startswith('Heroes/'):
            a['selfAssessment']='Character identity retained across sheet poses; ornate cloth/metal detail compresses at720p. Cast bodies can read smaller when raised props consume the crop.'
        if id.startswith('Heroes/ignis_evo'):
            a['selfAssessment']='Ignis face/oxblood anchor retained; Archmage mass and Weaver veil/threads differ. Weaver staff stays closer to a caged orb than the requested spindle spiral; fine threadwork softens at game scale.'
        if id.startswith('Portraits/'):
            a['selfAssessment']='Generated from same base sheet; silhouette/costume retained, close-up face rendering may drift subtly. One transparent corner pixel accommodates intake despite full-bleed portrait allowance.'
        if id.startswith('Enemies/'):
            a['selfAssessment']='Final a/b pair passes local silhouette IoU>=.6. Grunt is mirrored to enforce screen-right, flipping its baked light. Harpy was regenerated for modest wing motion; no tether/shadow baked into body.' if 'grunt' in id else 'Same sheet identity and measured silhouette IoU>=.6; finer armour/feather detail needs owner review at crowded game scale.'
        if id.startswith('World/node_'):a['selfAssessment']='Same generated socket family; neutralised for runtime tint and fitted to perspective ellipse. Carved ticks may simplify at phone scale.'
        if id=='World/arena_background':a['sources']=['source/blender/battlefield.blend','source/blender/battlefield.py','source/sheets/battlefield_paint_finish.png','source/battlefield/renders','source/battlefield/layers'];a['master']=None
        if id.startswith(('Icons/','UI/')):a['selfAssessment']='Generated engraved material family, downsampled from retained master; review symbols at32px and HUD in the fixed-border stretch previews.'
        if id.startswith('Vfx/'):a['selfAssessment']='Generated painterly energy; neutral tint sprites explicitly greyscale, centre alpha caps applied to hits/tell. Intensity still requires Unity review in dense combat.'
    d['knownIssues']=[
        'Human/Unity aesthetic acceptance is PENDING. Offline frames are composites, never game screenshots.',
        'Fine costume and engraving detail can compress into noise at720p; cast body scale varies as raised props share the fixed hero crop.',
        'Ignis and Sylph inherited similar facial features from the style reference; roles separate through bow/staff, silhouette and palette.',
        'Weaver staff remains closer to the base orb staff than a true short spindle spiral; evolution silhouette and palette are distinct.',
        'Crystal geometry/registered damage work is crisp and more render-like than the painterly characters. Battlefield finish is deliberately bounded to preserve layout.',
        'Some conceptual details are restrained: no elaborate pillar sculpting, no new glow roads. The concept frame is more elaborate than production terrain.',
        'Runtime battle clear colour needs lead change to #1d1f24 to match the supplied edge; current green clear colour is outside this writable scope.',
        'Portrait request permits full opacity, but intake requires transparent pixels: one corner pixel is cleared as a compatibility measure.',
        'OpenCV import failed (numpy.core.multiarray failed to import / _ARRAY_API not found under NumPy2). SciPy/Pillow utilities replace its cleanup use.',
        'Built-in generator version is not exposed. Raw generated dimensions can differ from requested; all actual raw PNGs and2x/4x canvas masters are retained.',
        'External working-tree changes were observed during production and not edited by this batch; see qa/workspace_observations.json.'
    ]
    d['blockers']=[a['id']+': '+a.get('reason','') for a in d['assets'] if a['status']=='blocked']
    d['counts']={s:sum(a['status']==s for a in d['assets']) for s in ['delivered','blocked','skipped','placeholder']}
    if (ROOT/'qa/intake.json').exists():
        intake=read(ROOT/'qa/intake.json');d['intake']={'path':'qa/intake.json','blockingCount':len(intake['blocking']),'strayWorkingTreeChanges':intake.get('strayWorkingTreeChanges',[])}
    write(MANIFEST,d)
if __name__=='__main__':run()
