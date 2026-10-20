# CODEX ART REQUEST — R02: elemental VFX sample (Aetherward, Art Bible v3)

Written by the lead (Claude Code) on 2026-10-21. R01 locked the v3 comic-ink style: 47 assets were integrated and look right in Unity.

Your `concepts/combat_scene_concept_LOW_RES_DRAFT.png` from R01 is now the **VFX target**:
- the giant hard-edged fire;
- the ice-crystal walls;
- the violet lightning web;
- the water vortex dome.

The in-game effects are currently far smaller and softer than that. This batch paints the shapes; the lead animates them in Unity (scale pop, spin, fade, layering with Blender flipbooks, shockwaves, shake).

Read with this file:
- `ArtHandoff/requests/R01/CODEX_ART_REQUEST.md`, section 1 (style).
- `ArtHandoff/requests/COMMON_CONTRACT.md`, sections 4 and 6–10 (technical, method, scope, layout, done, blockers). Its section 2 is replaced by R01.
- `ArtHandoff/requests/R02/INPUT_MANIFEST.json`: 21 assets with exact sizes. Each guide is under `references/guides/`. Every pivot is the canvas centre.

## 1. Style for effects
- **Comic VFX.** Hard-edged flat colour shapes in 3–4 bands per effect: a white-hot or pale core, the element colour, a deep edge colour. Bold black-violet ink accents (`#1b1226`) on the solid parts: shards, rocks, splash crowns, flame tongues. No ink on pure light such as glows and halos.
- **No soft airbrush gradients.** At most a thin soft halo outside the shape.
- **Exaggerated:** big curling flame tongues, oversized shards, thick jagged bolts, chunky water crowns. They must read at about 150–300 px on a 1440p screen.
- **Background:** transparent, straight alpha, no baked shadow, no ground under the effect.
- **Element palettes:**

  | Element | Colours |
  |---|---|
  | Fire | `#fff3b0` → `#ffd23a` → `#ff7a1a` → `#c0281a` |
  | Ice | `#ffffff` → `#bff4ff` → `#7fe3ff` → `#2a6fd0` |
  | Lightning | `#ffffff` → `#fff36a` → `#a98bff` → `#5a2bd0` |
  | Water | `#e8fbff` → `#5fe0ff` → `#2fb8b0` → `#1f5fd0` |
  | Shared (ring, slash, spark, telegraph) | White / gold, tinted by code |

## 2. Each asset
| Asset | Canvas | What it is |
|---|---|---|
| `impact_<fire/ice/lightning/water>` | 192 | Hit burst at the target, centred and radial. Fire: flame petals. Ice: shard star. Lightning: forked spark star. Water: splash crown. Fills ~85 % of the canvas |
| `projectile_<…>` | 128 | Travels toward **+X** (pointing right). The head on the right, the tail fading left. Fire: comet. Ice: spear shard. Lightning: jagged bolt segment, full width. Water: droplet orb with a wake |
| `fireball` | 192 | A big fire comet toward +X: head on the right, flame tail left, ~70 % of the width |
| `burst_<fire/ice/lightning/water>` | 256, new | **The signature big effects**, drawn for a 3-unit area. Fire: meteor explosion with a mushroom of flame tongues and flying embers. Ice: ice bloom with a ring of huge crystal spikes erupting outward (seen from the 38° game camera). Lightning: thunder dome, a web of bolts in a rough sphere. Water: tidal heal dome, a swirling water ring with a crown splash |
| `ring` | 256 | Shockwave ring, **top-down circle** (the game squashes ground decals to 0.62). White, thick, broken comic edge |
| `telegraph` | 256 | Danger zone, top-down circle. Thick hazard rim with inward chevrons, a lighter interior. White (code tints it red). Must stay readable under other effects |
| `slash` | 256 | A melee arc: crescent swoosh with a speed-line tail, opening toward +X |
| `spark` | 48 | Small 4-point star glint |
| `zone_burning_ground` | 256 | Top-down circle of burning cracks and low flames, transparent between flames |
| `zone_thunderstorm` | 256 | Top-down circle with a storm rune, crackling arcs on the rim |
| `zone_healing_rain` | 256 | Top-down circle with a water sigil, droplets and ripples |
| `field_ice_cover` | 256 | Top-down frozen patch with ice-shard clusters on the rim |

**Opacity:** effects are drawn over units. The interiors of zones and rings are mostly transparent (≤ 35 % alpha), so units inside them stay visible. Solid parts (shards, flame tongues) can be opaque.

## 3. Order
1. Do `burst_fire` first. Iterate it until it matches the concept's fire.
2. Then the other three bursts.
3. Then impacts, projectiles, fireball, the shared sprites, and the zones.

Use the R01 combat concept and the previous burst as references, with at most 5 reference images.

## 4. Self-QA and return
- Self-QA as in COMMON_CONTRACT section 6, with `--batch R02`. Intake must report 0 blocking problems.
- Also make a sheet `previews/vfx_on_battlefield_1440.png`. Composite each effect at game size over `ArtHandoff/requests/R01/references/battlefield_toon_verdant.png`, with one R01 hero standing inside each burst to prove the hero stays readable.
- Label that sheet as an **offline composite**.
- The final message must give delivered/blocked counts, the intake result and the top three risks.
