# Aetherward Art Bible (gameplay readability first)

The numbers below are facts taken from the pipeline and runtime code, unless marked **(proposal)**. Gates are enforced by `Tools/ArtPipeline/validate.py` using `Tools/ArtPipeline/art_spec.json`.

## 1. Identity
- Original "storybook chibi" vector style:
  - thick deep-violet ink outline (`#1C1730`, ~6 px at the 320-unit hero grid);
  - flat base colour + one cel shade (lower-right) + one soft highlight (upper-left).
- Big head and small body: the head carries identity (hair, hood, helm). The prop carries the role (staff, shield, bow, blades).
- Each hero is generated from a parametric spec in `Tools/AssetGen/art/heroes.py` (build, outfit, head, prop, palette). No third-party art.

## 2. Camera, scale, ground contact
- Orthographic 2D camera. `orthographicSize = max(7.5, 13.2/aspect)` → 15 world units tall on 16:9.
- Heroes:
  - frame **400×400**, PPU 200 (2 world units);
  - the figure occupies the 320-unit region at (40, 80): headroom for raised props;
  - pivot (0.5, 0.07) = the ground point.
- Enemies: 256² (bosses 512²), PPU 160, pivot at the foot line. Crystal: 320×400, PPU 160, pivot 0.07.
- On screen, a hero is ~115 px tall at 1080p and ~77 px at 720p. All previews are made at those sizes (`ap.py preview`).
- The ground contact shadow is a separate sprite (`World/shadow`), never baked into the character.

## 3. Element signalling (colour + shape, never colour alone)
| Element | Primary / secondary | Shape cue |
|---|---|---|
| Fire | #ff5a2c / #ffb230 | flame tongues, spikes |
| Water | #2f8cff / #5fe0ff | waves, droplets |
| Lightning | #8c4dff / #ffe14a | zig-zags |
| Ice | #7fd8ff / #e8fbff | crystals, hexagons |
| Wind | #2fd39a / #c4ffd9 | swirls, ribbons |
| Earth | #b9773a / #8fc24a | blocks, boulders |
| Light | #ffd84a / #fff7cc | rays, halos |
| Shadow | #a3306b / #3a0f2c | crescents, thorns |
| Nature | #3fa34d / #b6ec6a | leaves, blossoms |
| Poison | #a8e030 / #6a2a9a | bubbles, drips |
| Arcane | #ff5fd2 / #ffd6f6 | runes, sigils |
| Void | #5146d9 / #140c38 | rings, singularities |

- Colour-vision check: the validator simulates protan/deutan/tritan vision. 8 element pairs fall below ΔE 12, and each of those has a distinct glyph icon (`Icons/element_*`).
- Time and Crystal are disciplines, not elements.

## 4. Evolution identity (P3)
- Each branch must change the **silhouette** and the **palette**, not only add trim.
- Validator rule `weak_evolution` flags a branch when all three hold: silhouette IoU > 0.90, hue distance < 0.25, and value distance < 0.15.
- Branch kits (`EVO_KITS` in `heroes.py`) match the mechanics:
  - **aegis**: tower shield, spiked pauldrons, crystal crest.
  - **archmage**: tall mantle, floating crystal crown, orbiting runes.
  - **champion**: horned helm, massive pauldrons, belt plate.
  - **blade**: crossed back blades, streaming scarf, headband tails.
  - **saint**: sunburst disk, stole.
- On top of the kit, the outfit shifts toward the element colour.
- Result: 22 weak branches → 0 (`Reports/ArtQuality/before_after/evolution_*.jpg`).

## 5. VFX hierarchy (readability under density)
1. Boss telegraph:
   - ground marker shown ≥ 1.17 s before the strike (measured on all 12 bosses);
   - optional 1× assist while 2× speed is on.
2. Reaction bursts: medium size, element colour, one sound per reaction.
3. Skills / ultimates: hero-centred, shorter.
4. Basic hits: small impacts, plus merged damage numbers.

Rules:
- No full-screen splash and no "combo showcase".
- Milestones appear as small top-right toasts only.
- Flash intensity can be scaled from 0 to 100%. Battery saver and Reduced VFX lower the particle density.

## 6. Quality gates (blocking = CI failure)
- **Blocking checks:**
  - missing frame, manifest entry, licence or .meta;
  - duplicate GUID or path;
  - .meta pivot/PPU differing from the import settings;
  - empty image, missing alpha, wrong size;
  - cropped silhouette;
  - missing runtime reference;
  - expired waiver.
- **Warnings (review):**
  - white halo, foot/pivot drift, scale outlier, frame jump (IoU);
  - weak evolution, element signal;
  - battlefield and spell-density contrast, lighting direction;
  - overdraw (info when the mesh is Tight);
  - texture budget, CVD.
- Every asset also gets `humanReview: PENDING`. Numbers do not judge beauty.

## 7. Production paths
- **Default:** deterministic 2D vector generation (pycairo).
  - `ap.py generate` → staging → `validate` → `diff` (before/after) → `import` (backup + journal, all-or-nothing) → `rollback`.
- **3D→2D (Blender 4.0.2 headless, Cycles CPU):**
  - available, but the crystal benchmark was **REWORK — not adopted** (`Reports/ArtQuality/blender_benchmark/DECISION.md`);
  - EEVEE is blocked (no libEGL).
- **Directional animation:**
  - the game uses one facing that is mirrored by the view (`flipX`), plus pose frames (idle/cast/downed) animated procedurally in `UnitView` (lunge, squash, flash);
  - 4/8-direction sheets were **not produced**: the current camera and gameplay do not use them. **(proposal)** Only add them if the camera ever gets an azimuth.

## 8. Budgets
- RGBA32 upper bounds per category are in `art_spec.json`.
- A battle loads only the 6 deployed heroes: ~25.6 MB RGBA32 for all their frames (validator `heroWorkingSetMB_RGBA32`).
- Device size with compression (`textureCompression 1`): **not measured** (needs the Unity editor).
