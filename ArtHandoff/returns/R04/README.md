# R04 — Verdant Sanctuary return

Delivered two PNGs:
- `exports/World/verdant_paint.png`: untouched native built-in image generation output, 1672 × 941, 8-bit RGB, opaque.
- `exports/World/verdant_paint_on_guide.png`: same painting with source guide annotations at 50% opacity, including red lane bands, yellow dais ring, white intercept boundary, and cyan socket.

This is original generated production background art awaiting lead/owner review. It is not approved and the previews are offline images, not Unity screenshots.

## Direction and scope

Read R04 CODEX_ART_REQUEST, COMMON_CONTRACT, and Art Bible v3 completely. The literal user path `requests$B` was absent; used `requests/R04`, consistent with the requested batch and writable directory. No earlier README or manifest existed here.

R04 overrides the B01 style lock, old rim-light/value rules, Blender battlefield method, background dimensions and standard export path: this return uses comic ink and native painting under `exports/World/`. No units or characters were requested; per-character frame/alpha/master rules do not apply. R04 contains no INPUT_MANIFEST, references/guides directory or cited content JSON. Read arena.json as additional context; supplied geometry guide remains authoritative.

All task-created files are under returns/R04. No Assets, Tools, content data, meta files or git state were changed. No git command was issued. The built-in tool saved its own original outputs in its default managed location; selected generations were copied here.

## Generation, prompts and references

Used built-in `image_gen.imagegen`; no CLI/API fallback, external service, downloaded asset or named-artist imitation. No anatomy or environment was drawn with code.

Exact prompts:
1. `source/prompts/verdant_v1.txt`
2. `source/prompts/verdant_v2.txt`
3. `source/prompts/verdant_v3.txt` — selected final.

Attached references, in prompt order:
- v1: requests/R04/references/verdant_layout.png (composition), verdant_guide.png (geometry), style_ref_hud_concept.png and style_ref_combat_concept.png (style only).
- v2: source/masters/verdant_v1.png (edit target), original verdant_guide.png and verdant_layout.png (geometry/composition).
- v3: source/masters/verdant_v2.png (edit target), original verdant_guide.png (geometry).

All reference inputs belong to the project. No third-party inputs added.
The first pass had a tree obstructing the northeast lane and central vegetation. The second removed those, but retained an arch inside the intercept field. The third removed that arch, widened the paths and lowered the empty socket. All three native versions are retained in source/masters. No geometric warping, repainting with code, sharpening or upscaling was applied to the final painting. Requested the largest native 16:9 output and suggested 3840 × 2160 on every call; all calls returned 1672 × 941. This is approximately 16:9 (same aspect as supplied references); it was not cropped to force an exact ratio. Lead's proposed Real-ESRGAN upscale is not part of this return.

## Reproduction and checks

Run `python source/scripts/qa_return.py v3 --final` from this directory.
It copies the native PNG byte-for-byte, isolates guide annotations by differencing the original guide and layout, scales that annotation overlay to native output size, and composites annotation pixels at alpha 128/255. Original terrain is not blended into the painting. Red bands retain their original translucency and are additionally composited at 50%.

Previews: colour and grayscale at 1920 × 1080 and 1280 × 720; `verdant_dark_mass_720p.png` is a threshold composition study. No unit silhouette sheet applies to a battlefield-only batch. 1080p previews are enlarged for inspection only; the delivered painting remains native.

Inspected final guide overlay and 720p grayscale. Six lane bends and entry locations visually track the guide within approximately a quarter of a lane width. No large standing prop crosses the lanes or remains within the intercept circle. Ring and socket closely track guide marks. This is visual assessment, not a pixel-exact geometry certification. Existing peripheral pillars, ruins, static statues and crystals remain; two small lit braziers are present. The central Crystal, living units, UI and temporary combat effects are absent. Major pillar shadows cast upper-right; short rubble shadows vary. See qa/artifact_checks.json for measured luminance and byte identity.

Both required standard commands were attempted from repository root with temp variables and output paths inside this return:
- `handoff.py preview --batch R04 --overlay ArtHandoff/returns/R04/exports/Art --out ArtHandoff/returns/R04/previews --tag R04`
- `handoff.py intake --batch R04 --stage-dir ArtHandoff/returns/R04/_work/stage --qa-dir ArtHandoff/returns/R04/qa`

Both stop with `FileNotFoundError: [Errno 2] No such file or directory: .../requests/R04/INPUT_MANIFEST.json`. Exact tracebacks: qa/standard_preview.log and qa/standard_intake.log. Standard intake did not produce a result; zero blocking problems cannot be claimed. qa/intake.json records this blocked state, not a fabricated successful intake. Did not create inputs outside scope or modify the validator.

## Honest assessment and top three risks

Compared with the HUD concept, the ground is more saturated and its small leaf/stone patterns repeat more. The concept's character and UI hierarchy gives it stronger focal drama; this background intentionally leaves the centre empty. Edge foliage and pale lane masonry can still be busy at 720p. The ink and material separation are much cleaner than the original layout render.

1. **Validation blocked:** missing R04 INPUT_MANIFEST prevents standard intake and preview. Lead must supply a compatible request manifest/workflow before formal acceptance.
2. **Geometry remains generative:** lanes/ring/socket are visually close, not mathematically identical. Review the delivered overlay at full size and confirm integration framing, especially the socket footprint and north bend.
3. **Native resolution/detail:** 1672 × 941 is the largest returned in these calls. Planned 4× upscale may exaggerate repeated foliage, lane cracks and fine edges; test at target display size. Painting is RGB with no explicit ICC profile; treat as sRGB as requested.

Delivered: 1 painting + 1 guide overlay (2 image deliverables). Blocked image assets: 0. Blocked workflow checks: standard intake and standard preview. No approval claim.

