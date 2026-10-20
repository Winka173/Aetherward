# Benchmarks (all measured in this container unless marked NOT MEASURED)

| What | Number | Evidence |
|---|---|---|
| Art regeneration (795 sprites, pycairo) | ~25 s, byte-identical rerun | `ap.py generate` + `ap.py diff` → 0 changed |
| Art Quality Validator (795 assets) | ~20 s | `python3 Tools/ArtPipeline/validate.py` |
| Blender crystal benchmark (3 states, Cycles CPU 48 spp, 1 thread) | ~6–20 s | `ap.py render --only crystal` |
| Headless simulation soak (40 Endless waves) | ~0.02 ms/tick avg, max 8.4 ms (first tick); retained memory flat ~1.5 MB | `Reports/Performance/headless_soak.md` |
| Balance lab (3780 runs) | ~50 s on 4 threads | `Reports/Balance/lab/summary.md` |
| Training Chamber run (20 s fight) | < 100 ms headless | `TrainingChamberTests` duration |
| Hero sprite working set (6 deployed, RGBA32) | 25.6 MB | validator `heroWorkingSetMB_RGBA32` |
| Unity FPS / frame time / draw calls / device memory | **NOT MEASURED** | no Unity editor/player or device |
| Compressed texture sizes on device | **NOT MEASURED** | needs Unity import |
