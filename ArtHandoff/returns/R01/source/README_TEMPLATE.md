# Aetherward R01 art return

**47 sprite/portrait assets delivered; 2 required 2K concepts blocked.** Native low-resolution concept drafts are included for review. Built-in `image_gen` produced all artwork. No lead or owner approval is claimed; no Unity screenshot or gameplay integration is claimed.

The literal `requests$B` path did not exist. This return uses `ArtHandoff/requests/R01` and writes workspace outputs only inside `ArtHandoff/returns/R01`. There was no earlier README or deliverable manifest to resume.

## Direction and contract conflicts

R01 replaces COMMON_CONTRACT section2, the old art bible's style rules, the B01 lock, and the old rim-light/value-separation requirements. This return uses original dark arcane fantasy comic ink: tapered black-violet `#1b1226` contours, 2–3 hard cel tones, warm upper-left-front key, cool violet-blue shadows and jewel-color heroes. No rim light was added. Rift enemies use muted bone, rust and charcoal with magenta/violet cracks.

R01 asks for 400px heroes plus 800px masters; INPUT_MANIFEST and intake require 512px exports. **Both versions are supplied:**

| Version | Location | Purpose |
|---|---|---|
| 512×512, PPU256 | `exports/Art/Heroes/` | Exact input-manifest game exports |
| 1024×1024 | `source/masters/Heroes/*@2x.png` | Native high-resolution game masters |
| 400×400, PPU200 | `source/contracts/Heroes/` | Requested art-contract copies |
| 800×800 | `source/masters/Heroes/*@800.png` | Explicit 2× masters of the 400 contract |

The pairs share proportional framing and pivot `(0.5,0.07)`. Guardians are wider rather than taller. R01 also wins over the old design notes for Runner's biped hound-man anatomy, Juggernaut's slab hammer and Ravager's twin blades.

## Delivered inventory

| Character | Frames | Count |
|---|---|---:|
| Glacius, Ignis, Veyra, Marina | Each: idle, attack, cast, downed, walk_a, walk_b, portrait | 28 |
| Grunt, Runner, Hexcaster, Juggernaut, Ravager | Each: a, b, attack | 15 |
| Rift Warden | a, b, tell, attack | 4 |
| **Total game assets** | | **47** |

Portraits are192×192 with384×384 masters. Regular enemies are256×256 with512×512 masters. The boss is512×512 with1024×1024 masters. Every game export is an8-bit straight-RGBA PNG with sRGB profile. Unit backgrounds are genuinely transparent and contain no ground shadow, projectile or ground VFX. Portraits use dark-violet backdrops with a one-export-pixel clear perimeter to satisfy the input RGBA transparency gate.

## Method, prompts and provenance

Glacius identity was generated first and became the shared local style reference. Other poses used their character identity, Glacius where appropriate, and the closest useful repository pose/camera reference. Heroes preceded enemies; Grunt was the first enemy identity, then the boss and concepts. Later revisions addressed measured ink/overlap failures and cast proportions.

All source art is original built-in generation using repository-owned references. There are no third-party art inputs, artist/game imitation prompts, CLI/API calls or new Blender renders. An early HUD prompt called selected local portrait references "approved" as a prompting label; **that was not owner/lead approval**.

- `DELIVERABLE_MANIFEST.json` traces every export to its source, master, exact final prompt, cleanup command and SHA-256 hashes.
- `source/prompts/final__*.txt` is the authoritative final unit/portrait prompt set. Concept prompts and the first attempt's `_v1.txt` copies are retained too.
- `source/generations/` contains the selected generation pixels; `_rejected_v1` / `_scale_rejected_v1` files preserve discarded iterations.
- Python utilities perform alpha handling, proportional scale, foot alignment, torso translation, Lanczos downscale, reference packing, QA composites and RGB defringe only. **They never redraw anatomy or paint replacement artwork.**
- For alpha<32, final RGB comes from the nearest neighbor with alpha≥128. Masters and contract copies receive the same cleanup.

For exact reconstruction, use each manifest entry's final `cleanup` command followed by `postCleanup`. Historical `manual_*` scripts document alignment iterations; they are not a sequence to replay blindly. Final manifest offsets are authoritative. All temporary/stage output is under `_work/`.

## Drift and weakest assets

Early Glacius/Grunt/Runner passing poses and Ignis contact pose changed the silhouette too much; those were regenerated. Veyra's bright bowstring initially broke the dark-edge rule. Marina's pale hems and downed frame needed stronger ink. These revisions now pass the measured gates.

Torso alignment was checked separately from alpha bounding-box centering; large bows, shields and glaives otherwise displace the body. `qa/anchors_*.png`, `qa/cast_pair_review.png` and the manual-alignment JSON files show the separate QA overlays. None of those lines are in a production sprite.

The **weakest animation frames remain Ignis_cast, Veyra_cast and rift_warden_tell**: compact cast revisions improve body scale, but pose/prop foreshortening and the ideal ~6% lift are approximate. They need live frame-swap review. Metal scuffs, cloth motifs, pearls and enemy fragments are denser than ideal at720p, though the main role silhouettes read. Grunt still carries more armor detail than minimal fodder.

## MOCKUP / concept — blocked native 2K delivery

The tool produced1672×941 on both the explicit2560×1440 requests and fresh3840×2160 requests. The return does **not upscale these generations**. Required2560×1440 concept delivery is therefore blocked, and no compliant final file is claimed.

| Low-resolution draft | What it demonstrates |
|---|---|
| `concepts/hud_concept_LOW_RES_DRAFT.png` | Wave banner, Crystal HP/shield, gold, boss bar, red cracked-Crystal alert, six portrait cards with HP/skill/ultimate widgets, shield/scales/swords stance switcher |
| `concepts/combat_scene_concept_LOW_RES_DRAFT.png` | Four heroes, Crystal, rift wave, Ravager and Warden; exaggerated meteor burst, chain-lightning web, ice bloom and water heal dome |

HUD uses the later layout attempt; its small Marina field figure has duplicated crozier tips and is below final polish. Two dim cards demonstrate reserve slots; they are not two additional delivered heroes. UI uses symbols and blank text slots to respect the no-painted-text rule. Combat uses the first attempt for its clear foreground elite and boss staging. All attempts, native pixel sizes and prompts are recorded in `qa/concept_resolution.json` and the manifest. Native720p draft previews are included; no1080p draft was manufactured by upscaling.

These are direction targets, not screenshots, implemented HUD, VFX sprites or production battlefield art. The only resolution blocker is the observed built-in output size; no CLI/API fallback or external service was used.

## Self-QA

Final intake: **47/47 game exports, {{BLOCKING}} blocking problems, {{NOTES}} notes**. The input manifest covers47 game assets; intake does not certify the two blocked concepts. Reports are in `qa/`.

- Every unit's3px edge band is≤0.22 luminance; maximum measured **{{MAX_INK}}**.
- Minimum hero walk/idle silhouette IoU: **{{HERO_IOU}}**, required≥0.55.
- Minimum enemy b/a silhouette IoU: **{{ENEMY_IOU}}**, required≥0.60.
- Foot placement, exact game canvas sizes, RGBA mode and required files passed intake. Brute widths and enemy/boss height ranges were also reviewed in `qa/measurements.json`.
- Silhouette and grayscale boards were visually inspected at720p. This is self-QA, not beauty or animation approval.

Commands ran from the repository root, with TEMP/TMP inside this return and Python bytecode writes disabled:

```text
python Tools\ArtPipeline\handoff.py preview --batch R01 --overlay ArtHandoff\returns\R01\exports\Art --out ArtHandoff\returns\R01\previews --tag R01
python Tools\ArtPipeline\handoff.py intake --batch R01 --stage-dir ArtHandoff\returns\R01\_work\stage --qa-dir ArtHandoff\returns\R01\qa
```

`previews/scene_R01_*` are the provided pipeline's offline composites, which fall back to the B01 benchmark placement layout. `previews/toon_readability_*` use the supplied toon battlefield and generated returns only, with mirrored enemies and nominal visible heroes around190px at1440p. Both sets include1440p,1080p and720p. Color, grayscale and silhouette boards include1080p/720p versions. **None is a Unity screenshot.**

## Top three risks

1. **Concept resolution:** both required2K concept exports remain blocked; only1672×941 drafts exist.
2. **Frame swapping:** numeric overlap and manual torso alignment do not replace a Unity popping/foreshortening check, particularly casts and boss tell.
3. **Small-scale density:** fine ornament and oversized concept VFX can reduce target/Crystal clarity at720p or under heavier enemy density.

## Scope and handoff

No Assets, Tools, ProjectSettings, content data or original `.meta` files were edited. No git state changes were performed. Intake lists **{{STRAY}} out-of-scope working-tree changes**; this run left those paths alone. `_work/stage` contains the pipeline's disposable copies of live art/metadata for QA.

The lead owns Unity import, wiring the14 new frames, animation, shaders, particles, dynamic-party gameplay and acceptance. This return changes no game code or data. License inputs are the repository's own files and this run's original generations; no external CC0 material was used.
