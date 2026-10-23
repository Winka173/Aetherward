# R02 — elemental VFX return

Complete return: **21 delivered, 0 blocked, 0 skipped**. Required intake: **0 blocking problems, 0 notes, 0 stray changes**. Additional VFX checks: **21 checked, 0 blocking problems**. See `DELIVERABLE_MANIFEST.json` for per-asset provenance; it was updated after every export.

## Direction and inputs

This return follows Art Bible v3, R01 section 1 and R02's comic VFX direction. These replace the old B01 style lock and the old rim-light/value-separation rules. Hard cel shapes use black-violet ink on solid forms; pure light has no ink requirement. No named artist or game is used in generation prompts.

The literal `requests$B` location in the message does not exist. The batch was resolved to `ArtHandoff/requests/R02`, consistent with the current working directory and request title. All authored files are inside `ArtHandoff/returns/R02`.

Read: R02 request and INPUT_MANIFEST; R01 request section 1; COMMON_CONTRACT; Art Bible v3. R02's reference/guides directory is empty. The exact manifest and written shapes supply the framing rules. The R01 combat concept is a low-resolution direction reference, not gameplay evidence. The R01 battlefield and heroes are repository-owned compositing inputs.

## Method and prompts

Every sprite is a separate built-in `image_gen.imagegen` generation. Fire is first, then ice, lightning, water, impacts, projectiles, fireball, shared sprites and zones. The combat concept and previous burst are generation references (two inputs maximum; fire initially uses only the concept). Corrective generations use the concept and the raw fire burst, explicitly as graphic-treatment references. Raw generated PNGs are retained under `source/generations`; full prompts are under `source/prompts` and repeated in the manifest. The run used 29 successful image generations: 21 initial assets and eight replacements.

`source/scripts/process_vfx.py` performs utility cleanup only: preserve generated alpha, fit/centre the generated silhouette with transparent margins, Lanczos downscale, attach an sRGB profile and defringe RGB beneath alpha <32. It never draws effects. Masters are 1024², so the historical `@4x` filename means at least four times the largest 256² export; smaller exports have larger ratios. No generated detail is upscaled.

Bursts use a uniform 0.65 alpha multiplier to retain unit visibility. Ring/telegraph/spark are neutral greys for code tinting. Ground decal interiors within radius 0.29 of the canvas are capped at 89/255 alpha (35%); the rim can remain opaque. Top-down ground circles are exported unsquashed; only previews apply the game's 0.62 floor squash.

Built-in imagegen stores its original tool output in its managed generation directory. Selected raw outputs are copied into this return; no shell writes target locations outside R02. Python tool processes use the R02 `_work/tmp` directory for temporary files.

## Evidence and integration

All previews are **offline composites**, not Unity screenshots or acceptance. `source/scripts/preview_vfx.py` makes the effect contact sheet over the supplied toon battlefield with a matching R01 hero underneath each burst, plus grayscale and silhouette sheets. Bursts are displayed at 3 units (~225 px at 75 px/unit); other sprites use their manifest PPU. Shared preview sprites are untinted. Runtime tint, blend mode, timing, layering, opacity and scale remain the lead's integration work.

No gameplay, content data, Unity files, metadata or git state is changed. The four new burst IDs require the lead's normal import/integration; the manifest inherits the requested PPU 128 and centre pivot, while the 3-unit preview uses runtime scale 1.5 over their nominal 2-unit canvas.

## QA and risks

`qa/intake.json` records 21/21 exports with status OK, zero blocking problems, zero notes and zero stray working-tree changes. `qa/vfx_checks.json` independently checks exact size/RGBA, transparent margins, neutral tint sprites, ground-interior alpha, defringe and master resolution: 21 checked, zero problems. The source scripts, raw generations, 1024² masters, prompts and export hashes are recorded in the manifest.

The required repository preview generated 1440p, 1080p and 720p scenes plus `flat_R02.png`. The custom `vfx_on_battlefield_1440.png` contains all 21 effects at the documented display scales, with one matching R01 hero behind each burst. Its 1080p and 720p siblings and the 720p grayscale/silhouette sheets are also included. The custom preview uses a quieter lane crop of the supplied battlefield to avoid hiding projectiles behind the bright Crystal. Demonstration heroes are normalized to 190 px visible height; this is a readability comparison, not measured Unity rendering.

Reproduce the required preview/intake plus additional checks with:

```powershell
python source\scripts\run_qa.py
```

That wrapper runs the repository's prescribed `handoff.py preview --batch R02` and `handoff.py intake --batch R02`, with explicit R02 overlay, output, stage and QA paths. Command logs are in `qa/`. All four commands returned exit 0. `qa/production_summary.json` records the final counts and risks.

## Drift notes and visual assessment

The first lightning burst inherited crystals from the preceding ice reference; its replacement is an open hard-banded bolt web. Fire and ice impacts initially inherited burst/ring composition; their replacements are radial hit stars. The first ring, telegraph and spark inherited water decoration; their replacements are a white shock ring, a chevron hazard rim and a four-point glint. Thunderstorm and healing-rain zones were regenerated with explicit central sigils. Rejected raw generations and their prompts remain in the `rejected/` subfolders for audit, and are not exports.

Final colour, grayscale and silhouette sheets were visually inspected. All four projectiles and fireball point +X; slash opens toward +X. Ground sprites are circular before the preview squash. The heroes remain identifiable under the burst overlays, although these static samples cannot establish animation or multi-effect readability.

**Weakest / below the strongest visual target:** the small embers in `burst_fire`, fine facets in `burst_ice`, and foam detail in `burst_water` remain denser than ideal at reduced scale. `burst_water` also retains a softer peripheral cyan halo than the strongest hard-cel target. These are delivered review candidates, not claimed approvals. There are no unresolved production-tool blockers.

## Top three risks

1. Unity blend, opacity, runtime scale, animation and stacked effects remain unverified; the uniform 0.65 burst alpha can reduce impact if another runtime opacity cap multiplies it.
2. Fine fire embers, ice facets and water foam can compress at small sizes; the water halo is still somewhat soft.
3. Telegraph needs runtime red tint and top-layer ordering. Small projectiles may lose white-core contrast on pale lanes; the lead should verify their display scale in Unity.

No asset is claimed approved; all evidence here is offline.
