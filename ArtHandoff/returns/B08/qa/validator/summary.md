# Art quality report

- Assets: **833** · blocking: **42** · warnings: **323** · waived: 0
- Decisions (automated): KEEP 555 · REFINE 264 · REMAKE 14 · human review: PENDING for all (aesthetics are not scored numerically)

## Issues by check
| Check | Severity | Count | Waived |
|---|---|---|---|
| import_settings_missing | error | 14 | 0 |
| manifest_missing | error | 14 | 0 |
| meta_missing | error | 14 | 0 |
| cvd_confusable | info | 8 | 0 |
| element_signal_weak | warning | 1 | 0 |
| foot_pivot_mismatch | warning | 16 | 0 |
| frame_jump | warning | 4 | 0 |
| lighting_direction | warning | 27 | 0 |
| low_contrast_battlefield | warning | 155 | 0 |
| low_contrast_spells | warning | 74 | 0 |
| outside_safe_bounds | warning | 3 | 0 |
| overdraw_waste | info | 19 | 0 |
| scale_outlier | warning | 1 | 0 |
| texture_budget | warning | 2 | 0 |
| weak_evolution | warning | 1 | 0 |
| white_halo | warning | 39 | 0 |

## Texture memory (RGBA32 upper bound, MB)
| Category | MB |
|---|---|
| Cards | 7.81 |
| Enemies | 47.5 |
| Heroes | 273.0 |
| Icons | 5.74 |
| Portraits | 5.06 |
| Relics | 5.06 |
| UI | 5.02 |
| Vfx | 14.48 |
| World | 198.37 |

## Battlefield luminance (centre median)
arena_background.png 0.026, bg_frostfall_bastion.png 0.019, bg_molten_crater.png 0.020, bg_shattered_aether.png 0.026, bg_stormspire_citadel.png 0.025, bg_sunken_archive.png 0.039

## Blocking issues (first 60)
- `Enemies/banner_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Enemies/banner_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Enemies/banner_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Enemies/grunt_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Enemies/grunt_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Enemies/grunt_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Enemies/hexcaster_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Enemies/hexcaster_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Enemies/hexcaster_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Enemies/juggernaut_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Enemies/juggernaut_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Enemies/juggernaut_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Enemies/mimic_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Enemies/mimic_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Enemies/mimic_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Enemies/ravager_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Enemies/ravager_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Enemies/ravager_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Enemies/riftling_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Enemies/riftling_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Enemies/riftling_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Enemies/runner_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Enemies/runner_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Enemies/runner_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Enemies/sapper_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Enemies/sapper_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Enemies/sapper_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Enemies/shieldbearer_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Enemies/shieldbearer_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Enemies/shieldbearer_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Enemies/storm_harpy_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Enemies/storm_harpy_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Enemies/storm_harpy_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Enemies/summoner_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Enemies/summoner_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Enemies/summoner_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Enemies/swarmling_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Enemies/swarmling_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Enemies/swarmling_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Enemies/warded_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Enemies/warded_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Enemies/warded_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)

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
- `Enemies/mana_leech_a.png` foot_pivot_mismatch: lowest opaque row is -13px from the pivot (units float or sink)
- `Enemies/mana_leech_b.png` foot_pivot_mismatch: lowest opaque row is -21px from the pivot (units float or sink)
- `Enemies/rootbound_treant_a.png` foot_pivot_mismatch: lowest opaque row is +9px from the pivot (units float or sink)
- `Enemies/rootbound_treant_b.png` foot_pivot_mismatch: lowest opaque row is +9px from the pivot (units float or sink)
- `Enemies/soul_binder_a.png` foot_pivot_mismatch: lowest opaque row is -11px from the pivot (units float or sink)
- `Enemies/soul_binder_b.png` foot_pivot_mismatch: lowest opaque row is -17px from the pivot (units float or sink)
- `Enemies/spirit_wisp_a.png` foot_pivot_mismatch: lowest opaque row is -16px from the pivot (units float or sink)
- `Enemies/spirit_wisp_b.png` foot_pivot_mismatch: lowest opaque row is -22px from the pivot (units float or sink)
- `Enemies/storm_harpy_a.png` foot_pivot_mismatch: lowest opaque row is -34px from the pivot (units float or sink)
