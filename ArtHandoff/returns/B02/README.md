# B02 starter hero return

57 requested assets, produced with built-in image generation: Terra 7, Sylph 7, Marina 7, Ignis 3, Cinder 11, Volt 11 and Freya 11. No Unity import or owner approval is claimed. The manifest is checkpointed throughout production.

## Style lock

Dark Mythic Fantasy, painterly stylized 2.5D. Palette: charcoal `#2a2c31`, ash `#625c55`, oxblood `#6b2734`, basalt edge `#1d1f24`; fire `#ff6a2b`, Crystal `#8fe3ff` and `#2b5cff`. Key upper-left-front `#ffe9d0`, rim back-right `#9fe8ff`, ambient `#16233a`. Dark local-hue edge, no uniform black outline; cool 1–3 px rim; controlled broad brush planes.

Shared prompt prefix (verbatim from B01): “Dark Mythic Fantasy, painterly stylized 2.5D; orthographic 38.3-degree elevation, three-quarter front body turned 25 degrees toward screen-right. Key upper-left-front #ffe9d0, rim back-right #9fe8ff, ambient #16233a. Controlled broad brush planes, coloured local-hue dark edges without black outlines.”

## Method and provenance

Read the complete art bible, common contract, exact input manifest, hero designs and relevant game content. Reviewed the per-frame guides in a contact sheet. Exact prompts and attached reference paths are recorded in `source/prompts/`. Approved B01 exports are attached to generation calls. The tool allows five reference paths maximum; rotate the six requested style references while retaining the applicable identity. Each evolution uses the base identity; its actions use the evolution identity. No third-party inputs.

Raw built-in outputs are copied into `source/sheets/`; generated alpha is preserved. `source/scripts/pipeline.py` only crops, uniformly downsamples, registers the torso/feet, defringes and exports sRGB RGBA. It refuses to upscale smaller source artwork. Masters are 800×800 for 400×400 unit exports. Every pixel with alpha <32 receives the RGB of its nearest opaque neighbour. Those hidden RGB values may look like radial colour streaks in viewers that ignore alpha; they are not painted backgrounds.

## Contract conflicts and production notes

- B02 explicitly requires basic-attack frames, overriding the older art bible's procedural-only attack guidance.
- The common contract's 10% flyer rule overrides the bible's older tether rule (no flyers in this batch).
- Portraits use a tiny transparent corner because intake requires transparency even though the brief permits a full vignette.
- The first reference call was rejected with exact error: `referenced_image_paths` must contain at most 5 paths. Retried with five references.
- The first Terra Bedrock Warden had a back aegis extending too high; regenerated with a lower aegis before action-frame production.
- Existing repository changes were recorded read-only in `_work/baseline.json`; nothing outside B02 is authored by this run. Built-in generation saves raw outputs in its own managed directory; selected results are copied here.

## Evidence

Previews are offline composites, not game screenshots. A passing format check is not artistic approval. `roster_*` sheets show all 54 unit frames at the actual canvas display size for 1440p, 1080p and 720p; the 1440p sheet is 2560×1440. Colour, grayscale and silhouette variants are included. Standard `scene_b02_*` previews use the live project for unrequested assets; `scene_b02_style_lock_*` additionally overlay a local B01 environment snapshot. Neither is a Unity capture.

## Review notes and remaining risks

Torso locations were manually estimated from the source contact sheet and recorded in `source/scripts/anchors.json`, then mapped to x=200. Uniform scale keeps all equipment within the icon crop. These are manual art landmarks, not an automated anatomical proof. Five overly wide melee poses were regenerated after the final scale review. Downed frames receive a 40% saturation reduction in utility cleanup. Tiny disconnected alpha specks under 12 source pixels are removed.

B01 and live repository files changed concurrently during production. `_work/baseline.json` and `qa/scope_audit.json` record the observed differences. The B02 producer has authored only inside B02; the repository as a whole did not remain unchanged. References were attached at call time and the B01 style-lock text captured at the start is retained verbatim in this manifest. A lead should reconcile the B02 identities with the latest B01 revision before accepting this batch.

The weakest design matches are Cinder's Ash Guardian (more blackened bronze and red cloth than the requested ash-grey plate) and Freya's Blizzard Witch (still regal rather than strongly wild). The shield/cleaver and jagged ice silhouette do distinguish their branches, but these designs remain below the intended design-fidelity bar. They are supplied for review, not represented as approved.

Fine metal trim, ice lace and emissive details compress at 720p. Full-frame swaps also need an actual Unity review for secondary cloth/prop drift and perceived scale changes; local foot/box/edge checks do not prove animation continuity. No code change is requested or included.
