# B04 art return — production in progress

Scope: Nyxara, Ashara, Nerissa, Voltrix, Eirwen and Kael; ten unit frames and one portrait each (66 assets). No earlier B04 manifest or artwork existed at start. All authored project files stay inside B04. The initial repository status is recorded in `qa/workspace_baseline.txt`.

## Style lock

Dark Mythic Fantasy, painterly stylized 2.5D. Palette: charcoal `#2a2c31`, ash `#625c55`, oxblood `#6b2734`, basalt edge `#1d1f24`; fire `#ff6a2b`, Crystal `#8fe3ff` and `#2b5cff`. Key upper-left-front `#ffe9d0`, rim back-right `#9fe8ff`, ambient `#16233a`. Dark local-hue edge, no uniform black outline; cool 1–3 px rim; controlled broad brush planes.

Shared prompt prefix: “Dark Mythic Fantasy, painterly stylized 2.5D; orthographic 38.3-degree elevation, three-quarter front body turned 25 degrees toward screen-right. Key upper-left-front #ffe9d0, rim back-right #9fe8ff, ambient #16233a. Controlled broad brush planes, coloured local-hue dark edges without black outlines.”

The manifest retains the B01 styleLock object verbatim, including its original replacement character in the edge description. References are repository-owned exports. `source/references/approved_style_atlas.png` contains all six specified B01 frames plus B02 Cinder and Freya idle, composited over neutral grey without altering the artwork. The atlas is a supporting reference, not a deliverable sprite.

## Method and prompts

Mode: built-in image_gen. Full actual prompts and attached paths are in `source/prompts/`. Every generation must attach the approved style atlas and closest matching clay pose/camera reference. Subsequent poses must additionally attach the appropriate generated identity frame. Tool version is not exposed. The first call was rejected with exact error: `referenced_image_paths` must contain at most 5 paths. The atlas resolves this limit.

Unit generation requests genuine alpha, no ground shadow, no projectile/beam/slash, crisp painterly materials and edge luminance at least 0.27 against basalt near 0.16. Utility processing only crops, uniformly downsamples, centres, aligns feet, reduces downed saturation and defringes; it never paints anatomy. Preserve 800-square masters for 400-square units and at least 384-square masters for portraits. Never upscale source artwork.

## Contract resolutions

B04 explicitly requires basic attack frames, overriding the older art bible. Cast poses must read as raised/lifted while their ground contact respects the foot-row gate. Portraits permit a vignette, but intake also requires at least one transparent pixel. All previews are offline composites, not Unity screenshots or owner approval.

## Current state

The manifest marks unfinished assets blocked with an explicit production-pending reason. Final counts, intake evidence, assessments and risks will replace this section when production ends.
