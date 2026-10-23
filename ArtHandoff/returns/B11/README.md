# B11 boss art return

Scope: 46 frames for 12 bosses, authored only inside this B11 return. Built-in image_gen stores raw generations in the Codex user directory; selected results are copied into `source/sheets/`. No Unity import or git change is performed.

## Style lock

Dark Mythic Fantasy, painterly stylized 2.5D. Palette: charcoal `#2a2c31`, ash `#625c55`, oxblood `#6b2734`, basalt edge `#1d1f24`; fire `#ff6a2b`, Crystal `#8fe3ff` and `#2b5cff`. Key upper-left-front `#ffe9d0`, rim back-right `#9fe8ff`, ambient `#16233a`. Dark local-hue edge, no uniform black outline; cool 1–3 px rim; controlled broad brush planes.

Shared prompt prefix: “Dark Mythic Fantasy, painterly stylized 2.5D; orthographic 38.3-degree elevation, three-quarter front body turned 25 degrees toward screen-right. Key upper-left-front #ffe9d0, rim back-right #9fe8ff, ambient #16233a. Controlled broad brush planes, coloured local-hue dark edges without black outlines.”

The B01 manifest's `styleLock` object is copied verbatim. Rift Warden a/b and grunt a are attached as style references. Each new character's a frame is generated first and attached to every later pose. Rift Warden's existing B01 a/b exports supply its identity. Full call parameters are retained in `source/prompts/`.

## Method

Built-in image_gen, version not exposed. One generation per frame. Actual retained raw rasters are 1254 square, despite the prompt requesting at least 1536; their dimensions and opaque bounds are recorded in `source/records.json`. Native generations are never upscaled. `source/scripts/production.py` performs utility-only cropping, uniform scaling, authored torso registration, foot alignment, Lanczos reduction and nearest-opaque RGB defringe. Each accepted export has a 1024-square master and exact 512-square straight RGBA/sRGB export. Generated alpha is retained. `source/torso_anchors.json` records the manually reviewed torso coordinates; no anatomy is drawn or repaired with code.

The intended battlefield is dark basalt, mean luminance about 0.16. Export edge luminance must reach 0.27. Bright directional key planes and cyan rims supply separation. No ground shadows, red ground glow or attack VFX belong in these frames.

## Evidence and limitations

All previews are offline composites, not game screenshots or approval. B11 adds no code, data, import or gameplay changes. The standard `handoff.py preview` uses its benchmark layout; the additional `b11_basalt_page*_1440p.png` pages display every boss pose at the actual 1440p runtime canvas scale (384 px), on the specified generated basalt battlefield. Matching 1080p and 720p pages and color/grayscale/silhouette sheets are included.

Contract resolution: current COMMON_CONTRACT animation requirements override the older ART_BIBLE passages that say attacks are procedural only. All bosses in INPUT_MANIFEST are grounded; Vaelith has wings but is not flagged as a flyer. No tether or ground shadow is painted. Ashen Matriarch's clinging imps are part of her specified identity, not summoned-unit or projectile VFX.

## Selected revisions and identity

`source/revisions.json` records four rejected first passes and their replacements. Aetherion's first identity incorrectly inherited a glaive from the style references; its selected identity removes that prop, and all selected dependent poses reference the corrected image. Ironclad's first banner tip was clipped; the corrected identity was used for the later poses. Mirrath's attack was reframed to include the complete focus. Siegebreaker's attack was revised for a stronger torso lean, raised off-hand and ram follow-through. Rejected raw generations are retained for provenance and are not selected exports.

Each new boss has a contact walk, passing walk, tell and impact pose. Rift Warden contributes only its two requested new poses; B01 a/b remain identity references and are shown for comparison in review sheets. The B11 export total excludes those two B01 reference files.

## Reproduction and prompt set

From this B11 folder, `python source/scripts/rebuild.py` replays the selected raw sources through utility cleanup, and `python source/scripts/review.py` rebuilds local metrics and review sheets. The records file selects the corrected raw images. `production.py` serializes registry writes and saves PNG/JSON outputs atomically. Source, master, export, actual prompt parameters, input references and cleanup command are traced in the manifest; final hashes are recorded for every accepted asset.

Full actual prompts and attached reference paths: `source/prompts/*.json`. Mode: built-in image_gen throughout; no CLI/API fallback, external stock, third-party artwork, Blender stand-ins or code-painted character art. Inputs are the project's own B01 images and this batch's own generations.

## Visual limits and review risks

The broad silhouettes, lit planes and faction accents read in the offline 720p review. The weakest small details are Ashen Matriarch's clinging imps, Thornmother's blossoms and thin branches, and fine crystal/feather/rivet textures. These details soften at game scale; the main body and attack cues remain the intended read.

Minor generated cloth, halo, facet and prop contours vary across key poses, especially Mirrath's focus and Rift Warden's cloak/glaive foreshortening. These are pose illustrations, not a geometry-locked animation rig. Unity procedural animation, sorting and final scene balance require lead review; no owner acceptance is claimed.
