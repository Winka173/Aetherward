# B08 art return

Delivered 34/34 enemy frames using the built-in image_gen tool. Blocked: 0. All 34 have a 512×512 master, an exact 256×256 straight-RGBA PNG export, full prompts and input references. No Unity import or owner approval is claimed.

## Style lock

Dark Mythic Fantasy, painterly stylized 2.5D. Palette: charcoal `#2a2c31`, ash `#625c55`, oxblood `#6b2734`, basalt edge `#1d1f24`; fire `#ff6a2b`, Crystal `#8fe3ff` and `#2b5cff`. Key upper-left-front `#ffe9d0`, rim back-right `#9fe8ff`, ambient `#16233a`. Dark local-hue edge, no uniform black outline; cool 1–3 px rim; controlled broad brush planes.

Shared prompt prefix, reused verbatim from B01:

“Dark Mythic Fantasy, painterly stylized 2.5D; orthographic 38.3-degree elevation, three-quarter front body turned 25 degrees toward screen-right. Key upper-left-front #ffe9d0, rim back-right #9fe8ff, ambient #16233a. Controlled broad brush planes, coloured local-hue dark edges without black outlines.”

The manifest copies B01's entire `styleLock` object verbatim. B01 grunt, juggernaut, hexcaster and storm_harpy enemy exports were attached as style references. Each new enemy's `_a` was generated first and attached for `_b` and `_attack`. The four existing B01 enemies use their B01 `_a` as identity. The old live art was not used as a design reference.

## Method and prompts

43 separate built-in generation calls produced 34 first-pass frames and nine corrective variants. Tool version is not exposed. All raw generations are retained in `source/sheets/`; discarded variants remain for provenance. Most native generations are 1254 square; a few action revisions have a wider native canvas. The actual dimensions are recorded per export in the manifest and `qa/metrics/`. No generation was upscaled.

The complete final prompt set is `source/prompts/registered/*.json`. Each contains the full actual prompt, original reference paths, selected local raw source, canvas-fit parameters and torso registration. The first-pass and corrective prompts are retained beside that directory. `DELIVERABLE_MANIFEST.json` links each export, selected source, prompt, master and cleanup command. Original work for Aetherward; only built-in generations and repository-owned references were used, with no external downloads.

`source/scripts/produce.py` performs utility-only opaque cropping, uniform scaling, torso registration, foot alignment, Lanczos reduction and nearest-opaque RGB defringe for alpha <32. PNGs include an sRGB chunk. It refuses source upscaling. It never draws anatomy, lighting or costume. All lighting and pose corrections used image_gen.

`source/scripts/register.py` reproduces the selected exports from their local raw sources and measured torso anchors. Torso anchors are visual estimates, with approximately 5–8 export pixels of uncertainty; the manifest records the resulting anchor positions, including canvas-boundary clamps. These estimates are not an automated anatomical measurement. Rebuild with `python source/scripts/register.py`, then `python source/scripts/qa.py` and `python source/scripts/review.py`, from this folder. Set TEMP and TMP to `_work/tmp` before running production utilities.

The manifest was saved after each generated frame, so every completed character was checkpointed immediately. Initial pending records were replaced as production completed.

## Corrections and assessment

Sapper identity, Summoner identity/attack, and Banner identity/attack received brighter lit planes and selective rim light after their original contours measured below 0.27. Banner and Shieldbearer attacks were compacted to retain the size class and fit the entire prop. Hound bite and Swarmling leap were regenerated for clearer action. A too-wide intermediate Hound bite is retained as a rejected variant.

The enemies read as their roles in the 720p silhouette sheet: low quadruped, spiny crawler, tower shield, bomb carrier, ringed stone golem, staff priest, banner bearer, pale prism husk, crimson shard spawn and horn-crowned elite. The neutral stone-grey ward ring and pale prism plates remain the intended tintable/adaptive motifs. The four B01 attack frames retain their established costume families.

No selected frame is knowingly below the required technical bar. The Grunt strike is compact and the Banner attack approaches the right canvas margin after torso alignment; these are the weakest framing choices. Fine cracks, cloth tears and etched details compress at 720p. The revised Hound bite has a curled tail and more compact posture than its walk frames; minor secondary-detail drift remains.

## QA and evidence

`qa/intake.json`: **34/34 delivered, 0 blocking problems, 0 notes**. All requested rows are OK. Local QA in `qa/local_metrics.json` reports no size-class, format, edge-value or walk-overlap problems. Minimum 3 px edge luminance is **0.278**, above 0.27. Ten walk-pair silhouette IoUs range from **0.615 to 0.899**, above 0.60. Grounded frames have their lowest opaque row at 235–236; Harpy is at 208, lifted 28 px above row 236. Brutes meet the height and ≥200 px width rule. All masters are 2× native exports.

Requested `handoff.py preview` and `intake` commands were run from the repository root with outputs and stage confined to B08. The additional `--validate` run scanned 833 staged assets and exited 1: **42 blocking integration-metadata issues** (14 each of `manifest_missing`, `import_settings_missing` and `meta_missing`) on the 14 new attack sprites. The live repository does not yet register these new files. `qa/validation_status.json` records the result; this is not an extended validator pass. Per scope, Codex did not author .meta files or modify live import settings/provenance. `source/import_plan.json` gives the lead the exact fixed size, PPU, pivot and border facts for all 34 files.

`previews/scene_b08_{1440p,1080p,720p}.png` are the standard B01 benchmark-layout offline composites, so that scene primarily exercises the established B01 lineup. `previews/b08_all_frames_basalt_{1440p,1080p,720p}.png` additionally shows **all 34 delivered frames** over the supplied generated basalt battlefield at approximate runtime PPU scale (including Swarmling ×0.8 and Ravager ×1.3). These are labelled offline review composites, not gameplay. `b08_colour_720p.png`, `b08_grayscale_720p.png` and `b08_silhouette_720p.png` show the entire return for small-scale review; standard unit sheets are also retained. The supplied battlefield is a read-only preview input, not a B08 deliverable. Input guides were read and assembled in `qa/input_guides_read.png`.

`qa/artifact_hashes.json` records selected source/master/export/prompt hashes and the supplied battlefield hash. `qa/workspace_baseline.txt` records pre-existing tracked repository changes before B08 export production. Intake reports concurrent external changes separately; B08 commands authored only this return's files. Built-in imagegen raw files are automatically saved in the Codex user directory, then copied here as required by the imagegen skill. No gameplay, content, Unity, import metadata or Git state changes were authored by this batch.

## Contract resolution

The batch/common contract takes precedence over the older art bible's flyer tether and 15% lift: Harpy has ≥10% lift, with no painted ground shadow or tether. The explicit requested overhead Sapper/Juggernaut/Ravager attacks take precedence over the generic melee end-of-swing guidance. B08 has no battlefield production scope; the generated arena is used only for review. No implementation change is requested.

## Top three risks

1. Lighting variation between corrected and unchanged poses is visible, especially on Sapper, Summoner and Banner; procedural animation may emphasize the change.
2. Fine-detail and secondary-shape drift remains, and torso registration is visually estimated. Grunt/Banner framing and the Hound tail deserve animation review.
3. Fourteen new attack frames still need lead-owned Unity metadata, import settings and live provenance entries (42 extended-validator blockers). Evidence is offline; animation, mirroring and owner acceptance remain with the lead.
