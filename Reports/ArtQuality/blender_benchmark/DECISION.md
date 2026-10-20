# Blender 3D→2D benchmark — Crystal (3 damage states)

- Command: `python3 Tools/ArtPipeline/ap.py render --stage Temp/ArtStageBlender --only crystal`
  (script: `Tools/ArtPipeline/blender/crystal_benchmark.py`, Blender 4.0.2, Cycles CPU, 48 samples, single thread)
- EEVEE is **BLOCKED** in this container (`libEGL.so.1` missing; Blender aborts). Cycles was used instead.
- Reproducibility: two runs are not byte-identical. They differ by ≤5/255 on 23 pixels (~0.02%).
  `ap.py diff/import` treats that as "unchanged" (`RENDER_TOLERANCE`).
- Style: cel bands come from an emission colour ramp on the normal (fixed light direction); the outline is an inverted hull (solidify, back faces only); the ground shadow comes from a shadow catcher.

| Metric (intact) | 2D pipeline | Blender |
|---|---|---|
| Opaque share of the frame | 0.391 | 0.217 |
| Silhouette height (px) | 359 | 242 |
| Median luminance | 0.427 | 0.611 |
| Value spread (p90−p10) | 0.715 | 0.850 |

**Decision: REWORK — not adopted** (human review: Claude, 2026-10-20; still needs a second human reviewer).

Next to the current vector set, the 3D render reads weaker:
- the outline is thinner;
- there is no glow halo or sparkle highlights, which the 2D set uses as its "precious objective" cue;
- the silhouette is smaller;
- the pedestal reads as a stacked cylinder.

The benchmark gate in the prompt ("use 3D-to-2D as default only after the benchmark confirms it matches") is **not met**. The 2D procedural pipeline stays the default. The Blender path stays available and reproducible, for assets where 3D helps, such as rotating props.

Comparison image: `crystal_2d_vs_blender.jpg`.
