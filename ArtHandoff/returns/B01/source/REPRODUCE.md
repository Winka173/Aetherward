# Reproduce B01

Run from `ArtHandoff/returns/B01` with Python 3.11.5, Pillow 10.0.1, NumPy 2.4.6 and SciPy 1.17.1:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TEMP=(Join-Path (Get-Location) '_work\tmp')
$env:TMP=$env:TEMP
python source/scripts/rebuild.py
```

To regenerate geometry from scripts before cleanup, use `python source/scripts/rebuild.py --render`. This uses Blender 4.5.14 LTS, Cycles OPTIX on the RTX GPU, 64 samples for the Crystal and 48 for the battlefield, with denoising. Scripts and `.blend` files are retained under `source/blender`. All temporary/render/export paths resolve inside B01.

Generated images are nondeterministic. Their original PNGs are retained in `source/sheets`, with complete built-in generation prompts in `source/prompts`. `source/prompts/P0_verbatim.json` records the initial three prompts. No API/CLI fallback or third-party art was used. The built-in model/tool version is not exposed.

`source/scripts/jobs.json` records the crop/scale/anchor jobs. `pipeline.py` implements Lanczos downsampling, threshold-aware feet placement, neutral tint conversion and nearest-opaque RGB defringing below alpha32. Detached neighbouring sheet fragments touching a crop boundary can be removed as a mask utility. Raw outputs are preserved intact. `ingest_sheets.py` specifies sheet crop boundaries and selects the final revised Terra, hexcaster and harpy sources. Harpy frames share uniform scale and a lifted anchor.

`ingest_singles.py` also reproduces portrait transparency compatibility pixels, pure-black 75% shadow alpha, the telegraph's inner35%alpha cap, and impact centre60%alpha caps. Tint-controlled sprites are converted to exact greyscale. VFX/icons are fitted with transparent margins without aspect distortion. Nine-slice preparation clears the card's variable centre to true alpha, flattens panel/tooltip centre swatches, and replaces horizontal centre texture variation with median source swatches per row on bars/buttons; the generated borders are retained. Final files use straight8-bit RGBA with the PNG sRGB chunk; battlefield uses RGB.

`finish_geometry.py` composites the eight Blender source layers in bible order, applies a broad edge fade to `#1d1f24`, and saves the layout overlay. Unfinished render layers remain in `source/battlefield/renders`. The retained generated paint-over supplies bounded high-frequency surface modulation inside eroded opaque layer masks; alpha, object boundaries, road courses, node positions and low-frequency geometry shading remain from Blender. This is a controlled material finish, not adoption of a generated layout. Layers are isolated renders; cross-layer prop occlusion is represented in the separate shadow layer rather than a full-scene shadow pass. The source `.blend` retains the complete scene.

`local_qa.py` records opaque bounds, foot rows, alpha ranges and enemy-frame IoU. `nineslice_qa.py` stretches each HUD asset to three times its width with fixed borders (card48 on all four sides).

The lead's read-only-to-Assets preview/intake commands should use explicit B01 output directories:

Run from the repository root:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python Tools/ArtPipeline/handoff.py preview --batch B01 --overlay ArtHandoff/returns/B01/exports/Art --out ArtHandoff/returns/B01/previews --tag b01
python Tools/ArtPipeline/handoff.py intake --batch B01 --stage-dir ArtHandoff/returns/B01/_work/stage --qa-dir ArtHandoff/returns/B01/qa
```

Intake staging is a disposable copy under `_work/stage`, never Assets. Owner/Unity review remains separate from offline compositing and automated format checks.
