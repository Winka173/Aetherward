# Art quality report

- Assets: **816** · blocking: **63** · warnings: **343** · waived: 0
- Decisions (automated): KEEP 534 · REFINE 261 · REMAKE 21 · human review: PENDING for all (aesthetics are not scored numerically)

## Issues by check
| Check | Severity | Count | Waived |
|---|---|---|---|
| import_settings_missing | error | 21 | 0 |
| manifest_missing | error | 21 | 0 |
| meta_missing | error | 21 | 0 |
| cvd_confusable | info | 8 | 0 |
| element_signal_weak | warning | 1 | 0 |
| foot_pivot_mismatch | warning | 19 | 0 |
| frame_jump | warning | 4 | 0 |
| lighting_direction | warning | 27 | 0 |
| low_contrast_battlefield | warning | 157 | 0 |
| low_contrast_spells | warning | 88 | 0 |
| outside_safe_bounds | warning | 3 | 0 |
| overdraw_waste | info | 22 | 0 |
| scale_outlier | warning | 3 | 0 |
| texture_budget | warning | 2 | 0 |
| white_halo | warning | 39 | 0 |

## Texture memory (RGBA32 upper bound, MB)
| Category | MB |
|---|---|
| Cards | 7.81 |
| Enemies | 44.0 |
| Heroes | 166.63 |
| Icons | 5.74 |
| Portraits | 5.06 |
| Relics | 5.06 |
| UI | 5.02 |
| Vfx | 14.48 |
| World | 99.95 |

## Battlefield luminance (centre median)
arena_background.png 0.026, bg_frostfall_bastion.png 0.621, bg_molten_crater.png 0.060, bg_shattered_aether.png 0.194, bg_stormspire_citadel.png 0.138, bg_sunken_archive.png 0.152

## Blocking issues (first 60)
- `Heroes/cinder_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Heroes/cinder_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Heroes/cinder_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Heroes/cinder_evoA_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Heroes/cinder_evoA_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Heroes/cinder_evoA_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Heroes/cinder_evoB_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Heroes/cinder_evoB_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Heroes/cinder_evoB_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Heroes/freya_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Heroes/freya_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Heroes/freya_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Heroes/freya_evoA_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Heroes/freya_evoA_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Heroes/freya_evoA_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Heroes/freya_evoB_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Heroes/freya_evoB_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Heroes/freya_evoB_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Heroes/ignis_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Heroes/ignis_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Heroes/ignis_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Heroes/ignis_evoA_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Heroes/ignis_evoA_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Heroes/ignis_evoA_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Heroes/ignis_evoB_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Heroes/ignis_evoB_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Heroes/ignis_evoB_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Heroes/marina_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Heroes/marina_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Heroes/marina_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Heroes/marina_evoA_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Heroes/marina_evoA_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Heroes/marina_evoA_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Heroes/marina_evoB_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Heroes/marina_evoB_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Heroes/marina_evoB_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Heroes/sylph_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Heroes/sylph_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Heroes/sylph_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Heroes/sylph_evoA_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Heroes/sylph_evoA_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Heroes/sylph_evoA_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Heroes/sylph_evoB_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Heroes/sylph_evoB_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Heroes/sylph_evoB_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Heroes/terra_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Heroes/terra_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Heroes/terra_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Heroes/terra_evoA_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Heroes/terra_evoA_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Heroes/terra_evoA_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Heroes/terra_evoB_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Heroes/terra_evoB_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Heroes/terra_evoB_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Heroes/volt_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Heroes/volt_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Heroes/volt_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)
- `Heroes/volt_evoA_attack.png` **manifest_missing**: no provenance entry in manifest.staged.json
- `Heroes/volt_evoA_attack.png` **import_settings_missing**: no import settings (pivot/PPU) for this sprite
- `Heroes/volt_evoA_attack.png` **meta_missing**: Unity .meta missing (run Tools/gen_meta.py)

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
- `Enemies/riftling_a.png` foot_pivot_mismatch: lowest opaque row is -11px from the pivot (units float or sink)
- `Enemies/riftling_b.png` foot_pivot_mismatch: lowest opaque row is -17px from the pivot (units float or sink)
- `Enemies/rootbound_treant_a.png` foot_pivot_mismatch: lowest opaque row is +9px from the pivot (units float or sink)
- `Enemies/rootbound_treant_b.png` foot_pivot_mismatch: lowest opaque row is +9px from the pivot (units float or sink)
- `Enemies/soul_binder_a.png` foot_pivot_mismatch: lowest opaque row is -11px from the pivot (units float or sink)
- `Enemies/soul_binder_b.png` foot_pivot_mismatch: lowest opaque row is -17px from the pivot (units float or sink)
- `Enemies/spirit_wisp_a.png` foot_pivot_mismatch: lowest opaque row is -16px from the pivot (units float or sink)
