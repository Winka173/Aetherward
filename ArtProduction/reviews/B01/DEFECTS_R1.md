# B01 — revision round 1 (lead review of P0/P1 in a real Unity capture)

> **Scope change (2026-10-20):** the lead now produces the battlefield and the Crystal itself, in Blender 4.5 with real lights and shadows at 2K resolution (`Tools/ArtPipeline/blender/sanctum_env.py`). **Codex: skip D1 and D3.**
>
> Do **D2**, finish the **17 pending icons**, and follow the new 2K + value rules in `ArtHandoff/requests/COMMON_CONTRACT.md` §4.

**Evidence:**
- Unity player screenshots taken with the B01 exports loaded as runtime overrides (33 sprites), same spec and timing as the baseline:
  - `ArtProduction/reviews/B01/unity/b01p1_1920x1080/{prep,t06,t10,t15,t22}.png`
  - `ArtProduction/reviews/B01/unity/b01p1_1280x720/…`
  - Baseline with the old art: `ArtProduction/reviews/B01/unity/baseline_1920x1080/…`
- Crops at 2× in `ArtProduction/reviews/B01/defects_r1/`.
- Numbers come from `handoff.py intake`, value-separation notes in `ArtProduction/reviews/B01/intake_interim/intake.json`.

**Keep as is (strong):**
- Hero, enemy and boss character design and painting.
- Portraits.
- The Rift Warden's threat silhouette.
- The node sockets.

**Fix the following.**

## D1 — Battlefield reads as an untextured Blender greybox (`World/arena_background`) — BLOCKING
Crops: `battlefield_lanes_west_2x.png`, `outer_props_2x.png`.

Problems:
- The ground is flat mid-grey with no material breakup.
- The lanes are **loose square tiles scattered along a band**. They read as floating tiles, not as worn processional roads.
- The moss patches are flat teal polygons.
- The pillars, stumps and dead trees are primitive and unpainted.

The result does not match the painterly characters standing on it.

Do:
- Keep the Blender layout: lane and node alignment is correct.
- Replace the surfaces with **painted materials**:
  - **Ground:** basalt and ash with large-to-small value variation, cracks and grit.
  - **Lanes:** continuous worn flagstone roads with broken edge stones and packed ash between the slabs. The slab joints follow the road direction. No isolated tiles.
  - **Moss:** soft, irregular and desaturated, blending into the stone.
  - **Props:** sculpted and broken ruins with carved detail, ivy and painted AO.
- Then do a **painterly finish pass over the whole image**: an image-generation paint-over or edit using the render as the exact composition reference.

Verify alignment against the layout guide afterwards (`qa/layout_overlay.png`).

**Value targets** (measured on the flattened export):
- whole-image mean luminance **0.14–0.18** (now 0.227);
- lanes +0.08–0.12 above their surroundings;
- the dais around the Crystal may reach 0.25 near the light pool;
- outer ring and edges ≤ 0.12.

## D2 — Units do not separate from the ground (value) — BLOCKING for the listed frames
Measured as the mean luminance of the 3 px edge band vs the ground mean of 0.23. **Target edge ≥ ground + 0.10.** After D1 lowers the ground to ~0.16, the target becomes ≥ 0.26.

| Frame | Edge L |
|---|---|
| `Heroes/ignis_idle` | 0.20 |
| `Heroes/ignis_downed` | 0.23 |
| `Heroes/ignis_evoA` | 0.24 |
| `Enemies/hexcaster_a` | 0.20 |
| `Enemies/hexcaster_b` | 0.19 |
| `Enemies/juggernaut_a` | 0.21 |
| `Enemies/juggernaut_b` | 0.22 |
| `Enemies/rift_warden_a` / `_b` | 0.24 |
| `Enemies/grunt_a` / `_b` | 0.25 |

Do:
- Strengthen the shared rim light (back-right, `#9fe8ff`) to a clear **2–3 px lit edge at export size** on the shadow side.
- Lift the key-lit planes: shoulders, hood, weapon tops.
- Do **not** add a black or uniform outline.

Ignis and the hexcaster are dark red on dark ground. Give Ignis a brighter ash-grey mantle and a warmer lit hood rim. Give the hexcaster a pale bone-grey hood lining and a brighter sigil so a cluster of hexcasters still splits into individuals.

## D3 — Crystal lacks presence (`World/crystal_*`) — BLOCKING
Crop: `crystal_center_2x.png`.

Problems:
- At game scale the crystal body is small and grey-blue.
- The pedestal is a dark cylinder that reads as a "can".
- It is not the clear focal point; Marina's white robes compete with it.

Do:
- Use the full 320×400 canvas: crystal height ~260–300 px above the collar.
- Make the white-hot core and the cyan facets the **brightest values on screen** (p95 L ≥ 0.90; now 0.83).
- Design a carved stone collar with visible glyphs and broken stone teeth, not a cylinder.
- Keep 2–4 suspended shards, clearly separated.
- Keep all three states pixel-registered.

## D4 — Notes (non-blocking)
- `Heroes/marina_*`: the pale robes are good for readability, but slightly reduce the white so the Crystal stays brighter.
- The storm harpy reads well.
- The old swarmling-like purple sprites in the capture are riftlings, which are not in B01; they will be redrawn in B08.
- The old fireball/HUD sprites in the capture are P2/P3 items that are still pending.

## Deliverable for round 1
- Re-export only the affected assets: `World/arena_background` and its layers, the three `World/crystal_*` states and the frames in D2, with the same contract.
- Update `DELIVERABLE_MANIFEST.json`: add the field `"revision": 1` and a one-line change note per asset.
- Re-run intake: the value-separation notes for the D2 frames must disappear.
