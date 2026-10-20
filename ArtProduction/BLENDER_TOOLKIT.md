# Blender toolkit for Aetherward (lead-owned; verified 2026-10-20)

Blender 4.5.14 LTS at `C:\Users\Winka\Tools\blender-4.5.14-windows-x64\blender.exe`.
- Run headless with `-b --factory-startup`.
- Add `--online-mode` when installing extensions.
- Cycles uses OPTIX on the RTX 5070 Ti.

## Extensions (curated)
Rules: well-known only, one tool per job, and each one has a concrete use in the project.

| Extension | Origin | Job in Aetherward | Used by |
|---|---|---|---|
| **Sapling Tree Gen** | classic official add-on | Dead and corrupted trees with real branching, all biomes | `sanctum_env.py` (env v2) |
| **IvyGen** | classic official add-on | Ivy and creepers over pillars, arches and statues (verdant, archive) | `sanctum_env.py` (env v2) |
| **Cell Fracture** | classic official add-on | Broken pillars and rubble; the Crystal shatter sequence on defeat | `sanctum_env.py`, `crystal_states.py` |
| **Extra Mesh Objects** | classic official add-on | Gem, star and stair primitives: crystal shards, steps | `crystal_states.py`, props |
| **Archimesh** | classic official add-on | Shelves, columns and stairs for the Sunken Archive and the citadel | `sanctum_env.py` (archive, storm) |
| **MPFB** | MakeHuman community | Human base mesh + rig: pose-reference mannequins for Codex | `pose_mannequins.py` |
| **Brushstroke Tools** | Blender Studio | Painted brushstroke surfaces on props and the dais, for the painterly look | env v2 |
| Rigify, Node Wrangler, glTF/FBX | bundled | Rigging, node editing, exchange | as needed |

**Removed:** the same day's other installs. They duplicated a kept tool (other tree, scatter and ivy generators, sprite-sheet and bake helpers), were interactive-only modelling or lighting UI with no headless use, or were obscure.

**Not mine:** Align Tools, Bool Tool, Copy Attributes, EasyWeight, Extra Curve Objects, F2, Material Library and Wiggle 2 were already in this Blender profile. I did not install or remove them.

## CC0 inputs and where each is used
Licences and URLs are in `ArtProduction/REFERENCE_MANIFEST.json`. Every input must be used; unused ones are deleted from the cache and the manifest.

| Input | Source | Used for |
|---|---|---|
| burned_ground_01, aerial_ground_rock, cobblestone_large_01, cliff_side, castle_wall_slates, broken_wall, dark_rock, mossy_rock | Poly Haven | Verdant ground, roads, cliffs, dais, ruins, rocks |
| cracked_red_ground, dark_rock_02, patterned_slate_tiles, rock_boulder_cracked | Poly Haven | Molten Crater |
| rock_ground, large_floor_tiles_02, marble_cliff_01, castle_wall_varriation | Poly Haven | Frostfall Bastion (and storm/archive walls) |
| rocks_ground_02, herringbone_pavement | Poly Haven | Shattered Aether |
| rocks_ground_05, herringbone_pavement_02 | Poly Haven | Stormspire Citadel |
| marble_tiles, old_planks_02, dark_wooden_planks | Poly Haven | Sunken Archive |
| gothic_statue, rock_moss_set_01/02, namaqualand_boulder_02/05, dead_tree_trunk_02, dead_quiver_trunk, root_cluster_01, stone_fire_pit, tree_stump_01 | Poly Haven | Props in every biome |
| kloppenheim_02_puresky | Poly Haven HDRI | World light: verdant, frost |
| dikhololo_night | Poly Haven HDRI | World light: molten, aether (env v2) |
| moonless_golf | Poly Haven HDRI | World light: storm, archive (env v2) |
| Lava004 | ambientCG | Molten lava layer (colour + emission) |
| Lava001 | ambientCG | Molten vent pools at the hazard points (env v2) |
| Snow015 | ambientCG | Frost snow layer |
| Snow010A | ambientCG | Snow caps on frost props (env v2) |
| Ice002 | ambientCG | Ice crystals, covers |
| Ice003 | ambientCG | Frozen-tile nodes (env v2) |
| Moss002 | ambientCG | Verdant moss layer, replacing the flat tint (env v2) |
| Rock064 | ambientCG | Verdant rock patches (env v2) |
| Rock058 | ambientCG | Stormspire cliffs (env v2) |
| Ground068 | ambientCG | Shattered Aether island ground (env v2) |
| Bricks097 | ambientCG | Stormspire battlements, frost fortress walls (env v2) |
| Marble012 | ambientCG | Sunken Archive dais (env v2) |
| PavingStones138 | ambientCG | Stormspire dais and roads (env v2) |

## Plan (in order)
1. **Env v2:**
   - wire every "(env v2)" input above;
   - Sapling trees, Ivy, Cell Fracture pillars, Archimesh shelves and stairs, Brushstroke Tools on props and the dais;
   - re-render the 6 battlefields, grade, import.
2. **Mannequins:**
   - fix the cast/downed poses and the build macros;
   - render the role set for B04–B07.
3. **VFX flipbooks:** Mantaflow fire, smoke and steam; procedural lightning and splashes, for Unity ParticleSystem.
4. **Crystal shatter:** Cell Fracture + rigid bodies.
