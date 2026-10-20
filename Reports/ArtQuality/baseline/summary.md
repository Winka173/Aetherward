# Art quality report

- Assets: **795** · blocking: **62** · warnings: **230** · waived: 0
- Decisions (automated): KEEP 591 · REFINE 142 · REMAKE 62 · human review: PENDING for all (aesthetics are not scored numerically)

## Issues by check
| Check | Severity | Count | Waived |
|---|---|---|---|
| cropped_silhouette | error | 62 | 0 |
| cvd_confusable | info | 8 | 0 |
| foot_pivot_mismatch | warning | 21 | 0 |
| frame_jump | warning | 3 | 0 |
| lighting_direction | warning | 30 | 0 |
| low_contrast_battlefield | warning | 2 | 0 |
| low_contrast_spells | warning | 91 | 0 |
| outside_safe_bounds | warning | 3 | 0 |
| overdraw_waste | warning | 8 | 0 |
| scale_outlier | warning | 3 | 0 |
| weak_evolution | warning | 22 | 0 |
| white_halo | warning | 47 | 0 |

## Texture memory (RGBA32 upper bound, MB)
| Category | MB |
|---|---|
| Cards | 7.81 |
| Enemies | 44.0 |
| Heroes | 98.44 |
| Icons | 5.74 |
| Portraits | 5.06 |
| Relics | 5.06 |
| UI | 5.02 |
| Vfx | 14.48 |
| World | 76.54 |

## Battlefield luminance (centre median)
arena_background.png 0.334, bg_frostfall_bastion.png 0.621, bg_molten_crater.png 0.060, bg_shattered_aether.png 0.194, bg_stormspire_citadel.png 0.138, bg_sunken_archive.png 0.152

## Blocking issues (first 60)
- `Enemies/goblin_sprinter_b.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Enemies/siege_colossus_a.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Enemies/siege_colossus_b.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Enemies/stone_burrower_a.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Enemies/stone_burrower_b.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/ashara_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/ashara_evoA_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/ashara_evoB_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/cinder_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/cinder_evoA.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/cinder_evoA_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/cinder_evoB.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/cinder_evoB_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/cinder_idle.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/eirwen_downed.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/freya_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/freya_evoA_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/freya_evoB_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/glacius_downed.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/ignis_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/ignis_evoA.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/ignis_evoA_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/ignis_evoB.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/ignis_evoB_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/ignis_idle.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/kael_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/kael_downed.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/kael_evoA.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/kael_evoA_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/kael_evoB.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/kael_evoB_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/kael_idle.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/magnus_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/magnus_downed.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/magnus_evoA.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/magnus_evoA_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/magnus_evoB.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/magnus_evoB_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/magnus_idle.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/marina_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/marina_evoA_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/marina_evoB_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/nerissa_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/nerissa_evoA_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/nerissa_evoB_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/sylph_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/sylph_downed.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/sylph_evoA_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/sylph_evoB_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/terra_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/terra_evoA_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/terra_evoB_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/tidal_downed.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/volt_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/volt_evoA.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/volt_evoA_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/volt_evoB.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/volt_evoB_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/volt_idle.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)
- `Heroes/voltrix_cast.png` **cropped_silhouette**: opaque pixels touch the canvas edge (cropped)

## Warnings (first 80)
- `Enemies/frost_wraith_a.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Enemies/frost_wraith_b.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Enemies/goblin_sprinter_a.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Enemies/goblin_sprinter_a.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Enemies/goblin_sprinter_b.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Enemies/ironclad_warlord_b.png` outside_safe_bounds: silhouette within 2px of the edge
- `Enemies/mirrath_a.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Enemies/mirrath_b.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Enemies/nyxhollow_a.png` outside_safe_bounds: silhouette within 2px of the edge
- `Enemies/nyxhollow_b.png` outside_safe_bounds: silhouette within 2px of the edge
- `Enemies/riftling_a.png` overdraw_waste: only 10% of the quad is opaque (fill-rate cost); consider tighter canvas/mesh
- `Enemies/riftling_b.png` overdraw_waste: only 10% of the quad is opaque (fill-rate cost); consider tighter canvas/mesh
- `Enemies/soul_binder_a.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Enemies/soul_binder_b.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Enemies/spirit_wisp_a.png` overdraw_waste: only 11% of the quad is opaque (fill-rate cost); consider tighter canvas/mesh
- `Enemies/spirit_wisp_b.png` overdraw_waste: only 11% of the quad is opaque (fill-rate cost); consider tighter canvas/mesh
- `Enemies/spore_carrier_a.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Enemies/spore_carrier_b.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Enemies/storm_wisp_a.png` overdraw_waste: only 11% of the quad is opaque (fill-rate cost); consider tighter canvas/mesh
- `Enemies/storm_wisp_b.png` overdraw_waste: only 11% of the quad is opaque (fill-rate cost); consider tighter canvas/mesh
- `Enemies/swarmling_a.png` overdraw_waste: only 10% of the quad is opaque (fill-rate cost); consider tighter canvas/mesh
- `Enemies/swarmling_b.png` overdraw_waste: only 10% of the quad is opaque (fill-rate cost); consider tighter canvas/mesh
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
- `Heroes/freya_evoA_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/freya_evoB.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/freya_evoB_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/freya_idle.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/glacius_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
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
- `Heroes/marina_cast.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/marina_downed.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/marina_idle.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/mirel_evoB.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/mirel_evoB_cast.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/nerissa_cast.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/nerissa_evoA.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/nerissa_evoA_cast.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/nerissa_idle.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/seren_evoB.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/seren_evoB_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/solenne_cast.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/solenne_downed.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/solenne_idle.png` lighting_direction: lower-right brighter than upper-left (shading rule: light from upper-left)
- `Heroes/sylph_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/sylph_evoB.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/sylph_evoB_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/sylph_idle.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
- `Heroes/zephyr_cast.png` white_halo: bright fringe on semi-transparent edge (premultiply/bleed issue)
