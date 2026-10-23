# R05 animation return — incomplete, unapproved candidates

This return contains **25 generated candidate exports and 12 blocked frames** of the 37 requested. Built-in `image_gen` exhausted its daily usage allowance at `Enemies/runner_windup`; every remaining asset was attempted and returned HTTP 429 `usage_limit_reached`. Exact errors are in `qa/generation_errors.json`. The service supplied reset epoch 1792611365–1792611366. No substitute art or code-drawn characters were used. CLI/API fallback exists, requires `OPENAI_API_KEY` and explicit user opt-in, and was not used.

**Do not integrate this batch wholesale.** Seventeen of the generated candidates are marked `reviewStatus: needs regeneration` in the manifest. The other eight remain unapproved candidates. The manifest's `status: delivered` means a generated file was physically returned, not that it meets every visual requirement or has owner approval.

| Character | Candidate PNGs | Quota-blocked frames |
|---|---:|---:|
| glacius | 5 | 0 |
| ignis | 5 | 0 |
| veyra | 5 | 0 |
| marina | 5 | 0 |
| grunt | 3 | 0 |
| runner | 2 | 1 |
| hexcaster | 0 | 3 |
| juggernaut | 0 | 3 |
| ravager | 0 | 3 |
| rift_warden | 0 | 2 |
| Total | 25 | 12 |

## Direction and method

The literal `requests$B` path does not exist. Batch R05 was resolved from the user's stated batch and workspace to `ArtHandoff/requests/R05/`. No earlier README or deliverable manifest existed in this folder.

Read R05 first, then COMMON_CONTRACT, R01's replacement direction/camera, Art Bible v3, the R05 input manifest and frame guides, and the hero/enemy design data. The comic-ink v3 direction replaces COMMON_CONTRACT section 2, the B01 lock, and the old rim-light/value rules: black-violet tapered ink, hard cel shadows, warm upper-left key, jewel hero colours, muted rift enemies. There is no imposed cyan rim light.

Used the built-in image generation tool once per requested pose, with identity, neighbouring pose and canvas guide attached (three references, never more than five). Outputs were transparent 1254×1254 PNGs; the generator did not follow the requested numeric resolution exactly. Each successful raw output is preserved in `source/raw/<Category>/`. No smaller generation was enlarged.

`source/scripts/produce.py` performs only uniform Lanczos reduction, whole-image translation, canvas alignment, nearest-opaque RGB defringe for alpha <32, RGBA export, and sRGB tagging. It does not redraw, warp, separate limbs or synthesize anatomy. Masters are 1024² for heroes and 512² for the generated small enemies. Exports use the R05 manifest's exact 512²/256² canvases. Feet are aligned to row 476/236. Approximate hand-inspected head and torso landmarks are recorded in `source/landmarks.json`; these are alignment aids, not a proof of ±6/±8 px anatomical continuity. Keeping wide/raised props inside the hero icon box required body-scale compromises in several candidates; the manifest flags them.

The manifest was persisted after every successful asset, including every completed character, and after recording the blocked entries. No gameplay, Unity data, repository tools, `.meta` files or git state was edited. The image tool creates its own managed cache outside the return; all project artifacts, scripts, stage output and reports from this work are inside R05.

## Prompts and provenance

`source/prompts/<Category>/<frame>.txt` contains each full generation prompt. `source/prompts/addenda.json` records the exact character-specific suffixes added to applicable calls. The saved prompt files include those suffixes after finalization. `source/prompts/glacius_walk_c_initial.txt` records the first call's distinct prompt verbatim. Reference paths are recorded per asset in `DELIVERABLE_MANIFEST.json`, which traces every export to its raw image, master, prompt and cleanup script. Inputs are project-owned reference images and original built-in generations; no external art or artist/game-style imitation prompts were used.

## QA result and known defects

`qa/intake.json`: **12 blocking problems, 2 ink-edge warnings; exit 1**. All 25 exported candidates passed the intake checks for dimensions, RGBA mode, transparency and foot row. The 12 quota-blocked frames prevent the required zero-blocking result. The intake console says `37/37 delivered` because that script counts manifest entries, including blocked entries; actual generated files number 25.

Marina windup and follow edge luminance is approximately 0.25 and 0.26, above the v3 maximum 0.22. Regeneration should strengthen their dark outer contour. Do not restore the retired rim-light rule.

Silhouette and grayscale sheets were inspected at their 720p-sized rows. Roles remain recognizable, but several sequence requirements are below the bar:

- Ignis `walk_c` swaps the staff hand. Regenerate it; never mirror it as a fix because facing and costume would also reverse.
- Glacius and Veyra `walk_c`/`walk_d` do not distinguish opposite-leg contact and passing strongly enough.
- All four `idle_b` generations change more of the pose/contours than the requested 2–3 px breath. They should not be treated as finished breathing animation.
- Wide follow-throughs and raised props make body scale vary even after uniform alignment. Ignis `follow` is especially weak: the raw focus touches the source edge and fitting the icon box noticeably reduces the body. Multiple windup/follow candidates require regeneration at the identity scale.
- Marina `windup` needs handedness review as well as a stronger ink contour. Other prop/hand connections require lead visual review in the supplied sequences.

The manifest identifies all 17 candidates needing regeneration. No failed visual requirement has been waived because intake passed the file checks. The eight other candidates are Ignis walk_d; Marina walk_c/walk_d; grunt c/d/windup; runner c/d. They still require lead review for four-step timing, stride order and identity continuity.

Intake also reports 15 working-tree changes outside return folders. Those are repository state observed by its global git scan, not a before/after attribution. This run did not edit those paths; it did not revert or suppress them. The permitted workspace limited writes to this return folder.

## Offline previews

Everything in `previews/` is an **offline preview/composite**, not gameplay or a Unity screenshot. New missing frames are visibly labelled `BLOCKED`; existing live frames are included only as sequence references and were not exported as newly generated assets.

- `cycles_1440.png`: 2560×1440 overview of all ten character walk and attack rows. Rows are reduced to fit this overview.
- `cycles_game_scale.png`: vertically scrolling contact sheet retaining the contract's nominal 1440p game sizes (hero canvas 192 px, enemy 154 px, boss 384 px).
- `cycles_page_1_1440.png` through `cycles_page_4_1440.png`: 2560×1440 pages at those game sizes, with each character's full walk and attack sequence together.
- `<character>_walk.gif`: nominal 8 fps walk. GIF's centisecond clock alternates 120/130 ms delays.
- `<character>_attack.gif`: nominal 12 fps attack; GIF delays use 80/90 ms cadence.
- `<character>.gif`: combined walk/attack offline preview. Thirty GIFs total, including visibly incomplete previews for quota-blocked characters.
- `scene_R05_1440p.png`, `_1080p.png`, `_720p.png` and `units_R05_{colour,silhouette,gray}.png`: supplied pipeline previews.
- `review_{colour,silhouette,grayscale}.png`: compact candidate-only review sheets. `cycles_1080.png` and `cycles_720.png` provide smaller overviews.

## Reproduction and continuation

Run commands from the repository root with `PYTHONDONTWRITEBYTECODE=1` and `TEMP`/`TMP` set to `ArtHandoff/returns/R05/_work/tmp`:

```powershell
python Tools/ArtPipeline/handoff.py preview --batch R05 --overlay ArtHandoff/returns/R05/exports/Art --out ArtHandoff/returns/R05/previews --tag R05
python Tools/ArtPipeline/handoff.py intake --batch R05 --stage-dir ArtHandoff/returns/R05/_work/stage --qa-dir ArtHandoff/returns/R05/qa
python ArtHandoff/returns/R05/source/scripts/previews.py
```

Continue from the manifest and existing raw files. First generate the 12 `blocked` entries when the built-in quota is available, then regenerate the 17 visual failures. Keep identity and adjacent pose references, constrain body scale before props, and persist the manifest after each character. `source/scripts/produce.py finish` preserves the current quota failures; update its finalization logic when those assets are successfully generated rather than reintroducing stale blocked statuses. Do not run `init` over revised prompts without preserving them.

Top three risks: (1) missing frames due to tool quota; (2) continuity defects in handedness, opposite-leg steps, breathing and body scale; (3) Marina's insufficient ink contour at game size. The batch has not met the definition of done.
