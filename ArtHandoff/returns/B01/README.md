# B01 art return — revision 1 delivered

All authored repository outputs are confined to this return folder. Built-in image generation stores its raw result under the Codex user directory; selected raw results are copied here. No Unity import is performed.

## Revision round 1

Scope: the 17 icons in B01 section 6.7 and the 11 unit frames explicitly listed in D2. D1 battlefield and D3 Crystal belong to the lead under the review's updated scope note; their existing exports and layers are retained unchanged. Existing portraits, node sockets and other unit frames are retained.

R1 uses built-in image_gen, one call per icon/frame, with the exact shared prompt prefix. Icons use the first generated fire medallion as their family reference. Every D2 frame uses its original frame as the design and pose reference. R0 D2 masters are retained under `source/revision0/`. Full prompts and input references are recorded under `source/prompts/r1_*.json`; additional lighting attempts use `r1v2_*`. Raw generated results are retained under `source/sheets/`.

`source/scripts/revision1.py` performs utility-only crop, uniform fit, pivot registration, Lanczos reduction and nearest-opaque defringe. It saves 2x masters and exact native exports, and refuses any crop that would need upscaling. The tool chooses its actual raster dimensions; a requested 2048 square is not evidence of a 2048 output. Actual raw/master sizes are recorded in `qa/r1_metrics.json`. The target is readability at 2560x1440, with 720p checks as well.

`qa/r1_d2_before_after.png` compares original and revised frames on the same dark background; `qa/r1_icons_32px.png` includes native icons and 32 px colour/grayscale samples. These are offline QA images, not Unity captures or owner approval. The old battlefield export averages about 0.227 luminance; R1 checks both the new fixed edge threshold 0.27 and the current intake's stronger old-ground threshold of about 0.327.

R1 worktree baseline: `Assets/_Aetherward/Scripts/Unity/Battle/BattleController.cs` was already modified before R1 production writes. See `qa/r1_workspace_baseline.json`. No R1 command edits it.

## Style lock

Dark Mythic Fantasy, painterly stylized 2.5D. Palette: charcoal `#2a2c31`, ash `#625c55`, oxblood `#6b2734`, basalt edge `#1d1f24`; fire `#ff6a2b`, Crystal `#8fe3ff` and `#2b5cff`. Key upper-left-front `#ffe9d0`, rim back-right `#9fe8ff`, ambient `#16233a`. Dark local-hue edge, no uniform black outline; cool 1–3 px rim; controlled broad brush planes.

Shared prompt prefix: “Dark Mythic Fantasy, painterly stylized 2.5D; orthographic 38.3-degree elevation, three-quarter front body turned 25 degrees toward screen-right. Key upper-left-front #ffe9d0, rim back-right #9fe8ff, ambient #16233a. Controlled broad brush planes, coloured local-hue dark edges without black outlines.”

Full actual prompts are recorded in `source/prompts.json`. Image generation tool version is not exposed. Python utilities only crop, align, resample and defringe; they do not draw anatomy.

## Contract conflicts

- Request wins over bible: flyer minimum lift 10%; no painted tether to the foot row.
- Request and runtime use a uniform 48 px card border; INPUT_MANIFEST records 80 px at the bottom from the old metadata.
- Current data/old bible palette disagreements are resolved in favour of `elements.json` as directed.
- Intake requires transparency even for portraits although the request allows full bleed; reserve an invisible edge pixel if necessary and document it.

## Workspace baseline

Before any production write, read-only git status showed a pre-existing change to `Assets/_Aetherward/Scripts/Unity/Core/Services.cs`. This file is untouched by this batch. Initial untracked return log: `_work/codex_events.jsonl`.

## Evidence and quality

Generated sheets, Blender renders, concept frames and offline composites are distinct evidence. None is a Unity screenshot or owner approval. Review painterly texture at 720p; fine folds may compress into noise. Final intake, risks and per-family assessments will be recorded when production ends.

## R1 final results

Delivered 77/77 batch exports: 17 new icons, 11 revised D2 frames, 49 retained exports. Blocked: 0. Manifest revision: 1. D1/D3 exports and battlefield source layers were not regenerated.

Final intake: 0 blocking problems, 7 notes, 0 D2 value notes. Minimum D2 edge luminance: 0.328; retained battlefield mean: 0.227. All 11 D2 frames meet 0.27 and the current battlefield +0.10 criterion. Local utility QA reports 77 exports with no size/foot/walk-pair problems; original Crystal registration is retained. See `qa/intake.json`, `qa/r1_metrics.json` and `qa/local_metrics.json`.

Intake notes remaining outside D2:

- Heroes/ignis_cast: edge luminance 0.31 vs ground 0.23 (needs >= +0.10): add rim light / lift edge values
- Heroes/ignis_evoA_cast: edge luminance 0.30 vs ground 0.23 (needs >= +0.10): add rim light / lift edge values
- Heroes/terra_idle: edge luminance 0.29 vs ground 0.23 (needs >= +0.10): add rim light / lift edge values
- Heroes/sylph_idle: edge luminance 0.28 vs ground 0.23 (needs >= +0.10): add rim light / lift edge values
- Heroes/sylph_downed: edge luminance 0.29 vs ground 0.23 (needs >= +0.10): add rim light / lift edge values
- Enemies/storm_harpy_a: edge luminance 0.29 vs ground 0.23 (needs >= +0.10): add rim light / lift edge values
- Enemies/storm_harpy_b: edge luminance 0.28 vs ground 0.23 (needs >= +0.10): add rim light / lift edge values

`handoff.py preview` produced 2560x1440, 1920x1080 and 1280x720 offline composites, plus colour, grayscale and silhouette sheets. These use this return's R0 battlefield and Crystal until the lead replaces them. They are not Unity screenshots.

Raw R1 generations are native 1254 square. No generation was upscaled. Masters are 800 square for heroes, 512 square for ordinary enemies, 1024 square for the boss, and 192/256 square for icons. Exports use the exact INPUT_MANIFEST dimensions, straight RGBA, sRGB metadata, Lanczos reduction and nearest-opaque defringe. Full actual prompt set: `source/prompts/r1_*.json` and `source/prompts/r1v2_*.json`; chosen raw sources and prompt paths: `source/revision1_records.json`. Mode: built-in image_gen, version not exposed.

Reproduce the R1 exports with `python source/scripts/revision1.py`; it discovers completed first-pass prompts and applies selections from `source/revision1_selections.json`. `python source/scripts/rebuild.py` replays the earlier production pipeline followed by R1 selections. R0 frame masters and rejected first lighting attempts remain available for provenance. `revision1_qa.py` reproduces the R1 metrics and review sheets.

Top three risks:

1. Final scene balance depends on the lead's replacement battlefield and Crystal; this return retains the old versions.
2. Small contour/fold drift and stronger cloth highlights can create lighting variation against unchanged poses; the hexcaster pair has a visibly brighter bone-grey lining and outer folds.
3. No Unity capture or owner acceptance was performed; 32 px icon readability and 1440p sprite clarity were judged in offline images.

The native generations are detailed; fine cloth texture still compresses at 720p. The brighter directional planes improve separation, but this is not an owner approval. No gameplay/code/import changes are requested. All authored files, QA stage and process temp paths are inside B01. The initial BattleController.cs change is documented in the baseline; final intake lists concurrent external working-tree changes separately. R1 commands did not edit those paths.
