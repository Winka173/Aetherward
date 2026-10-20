# Art quality report

- Assets: **795** · blocking: **0** · warnings: **301** · waived: 0
- Decisions (automated): KEEP 545 · REFINE 250 · REMAKE 0 · human review: PENDING for all (aesthetics are not scored numerically)

## Issues by check
| Check | Severity | Count | Waived |
|---|---|---|---|
| cvd_confusable | info | 8 | 0 |
| foot_pivot_mismatch | warning | 19 | 0 |
| frame_jump | warning | 3 | 0 |
| lighting_direction | warning | 28 | 0 |
| low_contrast_battlefield | warning | 111 | 0 |
| low_contrast_spells | warning | 86 | 0 |
| outside_safe_bounds | warning | 3 | 0 |
| overdraw_waste | info | 22 | 0 |
| scale_outlier | warning | 3 | 0 |
| texture_budget | warning | 1 | 0 |
| white_halo | warning | 47 | 0 |

## Texture memory (RGBA32 upper bound, MB)
| Category | MB |
|---|---|
| Cards | 7.81 |
| Enemies | 44.0 |
| Heroes | 153.81 |
| Icons | 5.74 |
| Portraits | 5.06 |
| Relics | 5.06 |
| UI | 5.02 |
| Vfx | 14.48 |
| World | 99.95 |

## Battlefield luminance (centre median)
arena_background.png 0.026, bg_frostfall_bastion.png 0.621, bg_molten_crater.png 0.060, bg_shattered_aether.png 0.194, bg_stormspire_citadel.png 0.138, bg_sunken_archive.png 0.152

## Blocking issues (first 60)
- none

## Warnings (first 80)
- `Enemies/frost_wraith_a.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Enemies/frost_wraith_b.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Enemies/goblin_sprinter_a.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Enemies/goblin_sprinter_a.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Enemies/goblin_sprinter_b.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Enemies/goblin_sprinter_b.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Enemies/ironclad_warlord_b.png` outside_safe_bounds: silhouette within 2px of the edge
- `Enemies/mirrath_a.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Enemies/mirrath_b.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Enemies/nyxhollow_a.png` outside_safe_bounds: silhouette within 2px of the edge
- `Enemies/nyxhollow_b.png` outside_safe_bounds: silhouette within 2px of the edge
- `Enemies/soul_binder_a.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Enemies/soul_binder_b.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Enemies/spore_carrier_a.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Enemies/spore_carrier_b.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Enemies/thornmother_a.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Enemies/thornmother_b.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/aeris_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/aeris_downed.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/aeris_evoA.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/aeris_evoA_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/aeris_evoA_cast.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/aeris_evoB.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/aeris_evoB_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/aeris_idle.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/eirwen_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/eirwen_downed.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/eirwen_evoA.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/eirwen_evoA_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/eirwen_evoB.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/eirwen_evoB_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/eirwen_idle.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/elowen_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/elowen_downed.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/elowen_evoB.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/elowen_evoB_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/elowen_idle.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/freya_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/freya_evoA.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/freya_evoA_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/freya_evoB.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/freya_evoB_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/freya_idle.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/glacius_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/glacius_evoA_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/glacius_evoB.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/glacius_evoB_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/glacius_idle.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/isolde_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/isolde_evoA_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/isolde_evoB.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/isolde_evoB_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/isolde_idle.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/kael_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/kael_evoB.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/kael_evoB_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/marina_evoB_cast.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/mirel_evoB.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/mirel_evoB_cast.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/nerissa_cast.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/nerissa_evoA.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/nerissa_evoB_cast.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/nerissa_idle.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/seren_evoB.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/seren_evoB_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/solenne_cast.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/solenne_downed.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/solenne_idle.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/sylph_evoB.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/sylph_evoB_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/zephyr_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/zephyr_cast.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/zephyr_downed.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/zephyr_evoA.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/zephyr_evoB.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/zephyr_evoB_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/zephyr_evoB_cast.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/zephyr_idle.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Enemies/chaos_elemental_a.png` foot_pivot_mismatch: lowest opaque row is -10px from the pivot (units float or sink)
- `Enemies/chaos_elemental_b.png` foot_pivot_mismatch: lowest opaque row is -10px from the pivot (units float or sink)
