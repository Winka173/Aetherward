# R06 — Glacius image-to-3D reference views

Delivered 3 of 3 requested images for one character; 0 blocked images. Generated with the built-in `image_gen.imagegen` tool on 2026-10-21. These are reference paintings for the lead's TRELLIS.2 / Blender experiment, not game sprites or approved meshes.

## Files

- [Front A-pose](exports/glacius_front_apose.png)
- [35-degree left turn A-pose](exports/glacius_threequarter_apose.png)
- [Back A-pose](exports/glacius_back_apose.png)

All exports are native-canvas 1254 × 1254 PNG, 8-bit straight RGBA, fully opaque, embedded sRGB, on uniform `#d0d0d0`. Complete silhouettes have approximately 6% minimum margin. Largest native square resolution was requested (ideally 2048); the tool returned 1254 square in all three calls. No upscaling was performed. Raw generations are retained in `source/masters/` at their original resolution. A larger 2× master is unavailable; fabricating one would violate the no-upscaling rule. Export normalization only shrinks the native art slightly for margins.

## Direction and precedence

The supplied literal `requests$B` path does not exist. The batch was resolved from the working directory to `ArtHandoff/requests/R06/CODEX_ART_REQUEST.md`; writes stayed in `returns/R06`.

Read R06, COMMON_CONTRACT, ART_BIBLE v3, R01 section 1 and Glacius's design entry. R06 explicitly overrides the shared game-sprite camera, transparent background, icon box, foot-row and frame requirements: these images use an eye-level front / rotated / rear A-pose, opaque grey background, separated equipment and neutral even lighting. R01 replaces the old B01 style lock, rim and edge-luminance rules. No old B01 prompt or rim light was used. R06 contains no INPUT_MANIFEST, guides, content-data references or mannequin requirement; the game-camera pose mannequins would conflict with this eye-level A-pose request. No unrelated characters, sprites or effects were produced.

## Prompts and reference images

Exact prompts are preserved without abbreviation:

- [Front prompt](source/prompts/glacius_front_apose.txt): `source/references/glacius_idle.png` attached as identity/costume reference.
- [Three-quarter prompt](source/prompts/glacius_threequarter_apose.txt): generated front master and original game sprite attached.
- [Back prompt](source/prompts/glacius_back_apose.txt): generated front and three-quarter masters plus original game sprite attached.

The original reference was copied read-only from `Assets/_Aetherward/Resources/Art/Heroes/glacius_idle.png`. It defines the closed crest helm, blue steel plate, cyan ice, shield sigil, short mace and navy tabard. Original game pose and dark backdrop were excluded from the generations. All inputs are project-owned; no third-party images or artist/game imitation prompts were used.

The three-quarter image turns Glacius toward his anatomical left: nose toward screen-right, right mace arm nearer camera. Rear image correctly reverses screen positions of equipment. Backplate articulation, shield straps/braces and rear cloth are inferred because the game identity only shows the front. These details require lead review.

## Cleanup and verification

Run `python source/scripts/finalize.py` from this folder to reproduce exports, manifest, image QA and previews. Utility processing replaces border-connected near-neutral generated backdrop with exact grey, preserves the largest connected character silhouette, uses Lanczos to fit a 6% margin, and embeds sRGB. No anatomy or costume is drawn in code. Manifest is persisted after each exported view, completing the character record after the back view.

`qa/reference_validation.json` reports 3 passing image checks and 0 blocking image-check failures: square native resolution, RGBA, opaque alpha, grey background corners, margins and no enlargement. These checks do not prove art approval, exact camera angle, cross-view geometric consistency or mesh quality.

Standard `handoff.py intake --batch R06` was attempted with stage and QA paths inside R06; it exited 1 with `FileNotFoundError` for `ArtHandoff/requests/R06/INPUT_MANIFEST.json`. **Intake has not passed.** Exact traceback is in `qa/intake.log`, summarized in `qa/intake.json`. Creating the missing lead-owned request outside R06 is outside the authorized write scope. Standard preview also fails on the missing manifest (`qa/preview.log`). No project code or request was changed.

Custom offline comparison, grayscale and silhouette sheets are in `previews/` at 1920×1080 and 1280×720. They are labelled offline reference composites, not game screenshots. Reviewed comparison, silhouette and grayscale at 720p for silhouette and identity. Shield and mace remain recognizable, torso is visible, no ground or VFX is included. Shield joins its forearm naturally; separation is from torso, not disconnected equipment.

## Self-assessment and top three risks

1. **Cross-view geometry:** rear surfaces are invented and small armor facets / tabard ornament differ between views; these are coherent references, not a mathematically exact CAD turnaround. Lead should resolve these during mesh cleanup.
2. **Reconstruction ambiguity:** ink, crystal facets, shoulder/forearm overlap and attached shield can become baked texture or fused geometry. The flat shading helps, but TRELLIS.2 reconstruction was not run here. No claim of successful rigging or animation is made.
3. **Validation and resolution:** standard intake is blocked by the missing input manifest, and the tool returned 1254 rather than the requested ideal 2048. Native sources are retained; no artificial 2× masters. Custom checks pass but cannot replace lead acceptance.

The images are suitable for an initial image-to-3D experiment; exact multi-view agreement remains below a production modeling turnaround bar. No approval is claimed.
