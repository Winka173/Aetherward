# Aetherward Art Bible v2 — Dark Mythic, Painterly Stylized 2.5D

Status: **DRAFT for benchmark B01**. It becomes binding only after the owner approves the B01 benchmark.
It replaces the "storybook chibi" direction in `Docs/ART_DIRECTION.md` and `Docs/Enhancement/ART_BIBLE.md`.
The technical gates in those files (validator, budgets, pivots) still apply.

Facts are taken from code and data, with the source given. Everything else is a direction decision.

---

## 1. What the game is, and what the art has to do
Aetherward is a 2D crystal-defense roguelike auto-battler:
- up to 6 heroes on 12 nodes around a central Crystal;
- 20 waves arriving along 6 lanes;
- 12 elements, 40 reactions, 72 evolutions and 12 bosses (`Resources/Content/*.json`).

Combat runs automatically, so the player **watches**. The art therefore has to make four things readable at a glance, even when 40 enemies and a dozen spells are on screen:
1. where the Crystal is and how hurt it is;
2. who each hero is and what they are doing;
3. what is dangerous: boss tells and elites;
4. where enemies are coming from.

**Read priority (fixed):**
1. Crystal
2. Heroes and their important casts
3. Boss tells and elites
4. Common enemies
5. Ground (decals, terrain)

The ground must never compete with tiers 1–4.

## 2. Direction in one paragraph
An ancient, half-ruined sanctum built around a holy crystal relic, slowly being corrupted by the rift.
- **Ground:** basalt, ash and aged stone, with desaturated teal moss; deep blue night ambient; muted wine and crimson for corruption.
- **Heroes:** adult and heroic, stylized but not cute. Painted with visible but controlled brushwork, with structured costumes in leather, rune-etched metal and heavy cloth.
- **Light:** one coherent light. A dim ambient, a ritual rim light, and the Crystal as the main emissive source.
- **Mood:** mythic and solemn, but bright enough to read on a phone in daylight.

**Explicitly rejected (do not drift back to these):**
- pastel colours, candy saturation, chibi proportions (big head, short body);
- flat vector fills, uniform thick black outlines, round "blob" monsters, toy-plastic shading;
- grass-and-flowers prototype ground, racetrack-like glowing lanes;
- any 1:1 copy of another game's characters or style.

## 3. Projection & scale contract (facts — do not change)
| Item | Value | Source |
|---|---|---|
| Camera | Orthographic, no tilt. `orthographicSize = max(7.5, 13.2/aspect)` → 15 units tall on 16:9 | `Unity/Battle/BattleController.cs:144-148` |
| Pixel density | 72 px/unit at 1080p, 48 at 720p | derived |
| Floor projection | Ground ellipses use y = 0.62 × radius (telegraphs, zones, rings, shadows). The floor plane reads as seen from **~38° elevation** | `BattleController.cs:737,765`, `WorldViews.cs:119-140` |
| Unit view | Billboard sprites, one facing (authored facing screen-right); mirrored by negative `localScale.x` | `WorldViews.cs:260-261` |
| Hero sprite | 400×400, PPU 200 (2×2 units), pivot (0.5, 0.07) → feet on pixel row 372 from top. The figure lives in the 320×320 box at (40,80); the UI crops that box for icons | `Tools/AssetGen/import_settings.json`, `UI/Ui.cs:231-240` |
| Hero on screen | The 2-unit canvas is 144 px at 1080p. Head top is 235–255 px above the feet on the 400 canvas (≈ 90 px at 1080p, 60 px at 720p). Props may rise to ≤ 290 px (inside the icon box) | derived; current sprites measure 250–300 px including props |
| Enemy sprite | 256×256, PPU 160, pivot y 0.078 → feet row 236. Elite ×1.3, swarmling ×0.8 | import settings, `WorldViews.cs:132` |
| Boss sprite | 512×512, PPU 160, pivot y 0.0508 → feet row 486, ×1.25 in game (4 units) | same |
| Crystal | 320×400, PPU 160, pivot y 0.07 → feet row 372. Drawn at (0, −0.55) | `BattleController.cs:169` |
| Background | 2400×1360 RGB, PPU 80 (30×17 units), centred, behind everything | `BattleController.cs:160-162` |
| Ground shadow | Separate sprite `World/shadow` under every unit — **never bake a ground shadow into a unit sprite** | `WorldViews.cs:95-96` |
| Sorting | By y (lower = in front). Units cannot be occluded by the background | `WorldViews.cs:43` |
| Animation | No frame animation for attack or hit. Heroes have idle / cast / downed (+ evo A/B idle and cast). Enemies have a 2-frame walk a/b at 2 Hz. Lunge, recoil, squash, bob and hit flash are procedural | `WorldViews.cs:108-130,247-263`, `UnitPose.cs` |
| Render | Built-in pipeline, Gamma colour space, no Light2D, no URP. Lighting must be **painted into the sprites** | `ProjectSettings/GraphicsSettings.asset:40` |

**Implications for art:**
- Every unit is drawn at the same ~38° view, three-quarter front, body turned about 25° toward screen-right.
- Feet sit exactly on the pivot row. Nothing in the sprite casts onto a painted floor.
- There are no directional sheets. Do not invent 4- or 8-direction art.
- Because lighting is painted into the sprites, one light rig must be shared by all of them: key light upper-left-front, cool rim light from back-right. A mirrored sprite flips its light; this is accepted, so keep the key light near frontal (≈30° left) so the flip is not jarring.

## 4. Proportion & silhouette
- **Heroes:** adult, about **5.5–6 heads tall**.
  - Heads are slightly enlarged (~110%) only so that faces and helmets read at 77 px.
  - Weapons and signature props are **oversized by 15–25%** and must break the body outline.
- **Silhouette first:** every hero must be identifiable as a solid black shape at 64 px tall. Class reads through mass, not colour:

| Role (8 in data) | Shape language |
|---|---|
| guardian | wide trapezoid, ≥1.35× the width of a mage; a large shield or slab mass; low centre of gravity; heavy pauldrons |
| bruiser | inverted triangle; huge arms or weapon; forward-leaning stance |
| mage | tall triangle (robe flares to the floor); staff or focus rising above the head |
| healer / support | vertical, calm; a halo, orbiting ring or aura element above or behind the shoulders |
| ranger | narrow body with a long diagonal bow line or long weapon; light cloak; stance turned sideways |
| assassin | compact, crouched and low; angled blades; scarf or sash tails showing speed |
| controller | asymmetric; floating objects, ribbons or chains around the body |

- **Evolutions** keep the face, base palette anchor and signature prop of the hero. They change at least three of:
  - silhouette outline (new mass above the shoulders or behind the back);
  - costume tier (more armour or regalia);
  - weapon silhouette;
  - element VFX layered on the body (embers, runes, water halo).

  They must pass the validator's `weak_evolution` gate: silhouette IoU ≤ 0.90, **or** hue distance ≥ 0.25, **or** value distance ≥ 0.15.
- **Enemies** follow a size ladder:
  - **small** (grunt, runner, swarmling): compact, hunched, readable as a mob;
  - **medium caster:** elongated robes, tall headdress or hood;
  - **brute:** shoulders ≥2× the head width, armour slabs;
  - **flyer:** wing span wider than tall, body lifted ≥15% of the canvas above the foot row, with a thin tether/shadow anchor to the feet row;
  - **elite:** a distinct crown or horn read plus an accent rim;
  - **bosses:** break the rhythm with a non-humanoid or giant anatomy and a threat silhouette (raised weapon, open maw, spread limbs).

## 5. Palette
**Environment** (keep desaturated: saturation ≤ 35%, value 15–45%):

| Use | Colours |
|---|---|
| Basalt / ash | `#1d1f24`, `#2a2c31`, `#3b3a3d` |
| Aged stone | `#4d4a47`, `#625c55` |
| Desaturated teal moss | `#2e4a47`, `#3f5f5a` |
| Night ambient | `#16233a` |
| Corruption (wine / crimson) | `#4a1f2b`, `#6b2734` |

**Gameplay element colours are identity colours.** Keep the hue from `Resources/Content/elements.json`; value and saturation may be painted around it:

| Element | Hex |
|---|---|
| fire | `#ff6a2b` |
| water | `#2f8cff` |
| lightning | `#b06cff` |
| ice | `#8fe3ff` |
| wind | `#5fe8c8` |
| earth | `#c98a3e` |
| light | `#ffe066` |
| shadow | `#a3306b` |
| nature | `#3fa34d` |
| poison | `#c8f03a` |
| arcane | `#ff5fd2` |
| void | `#5146d9` |

The owner's brief names "fire amber/red, frost cyan, lightning gold, nature emerald". The data defines lightning as violet `#b06cff` with a gold secondary `#ffe14a` (`Docs/Enhancement/ART_BIBLE.md` §3). **Data wins; use gold as the spark accent of lightning.** Do not change gameplay colours in art tasks.

**Crystal:** cold white core → cyan `#8fe3ff` → deep aether blue `#2b5cff` edges. It is the highest-value object on screen.

**Hierarchy rule:**
- Nothing on the ground may be brighter than value 55%, except the Crystal glow pool and gameplay decals.
- Spell colours appear only in VFX and in hero element accents (≤ 20% of a hero's area).

## 6. Light, material, edge
- **Light rig (shared by every asset):**
  - key light upper-left-front, warm neutral `#ffe9d0`;
  - fill is the ambient night blue;
  - rim light from back-right, cool `#9fe8ff`, 1–3 px at the export size;
  - ambient occlusion is soft and present under the chin, arms and the hem.
- **No uniform black outline.** Edges come from value contrast plus the rim light. Where a dark unit meets the dark ground, use a thin coloured edge — a darkened local hue, never pure black — 1.5–2.5 px at the export size, plus the rim light.

  Every unit must pass `minEdgeContrast` 1.6 against the battlefield (`Tools/ArtPipeline/art_spec.json`).
- **Materials:**
  - stone: chipped, worn and carved, with soft AO in the carvings;
  - metal: rune-etched, with a specular highlight on top facets only;
  - leather and cloth: painted roughness, folds that follow the body;
  - crystal: sharp cut facets, internal refraction gradients, a hot core.
- **Brushwork:**
  - visible at full resolution;
  - must stay clean and not noisy at game scale;
  - no high-frequency texture inside silhouettes smaller than 8 px.
- **No reliance on post-processing:**
  - glow is painted into the sprite (Vfx/glow sprites exist for additive accents);
  - bloom is not available at runtime (built-in pipeline, no post stack).

## 7. Asset-family rules
### Heroes
- **States to paint:** idle, cast and downed, plus evoA, evoA_cast, evoB and evoB_cast where the hero has evolutions. Attack and hit are procedural; do not paint them.
- **Cast pose:**
  - the weapon or focus is raised;
  - the element accent is lit, with emissive brightening on the focus;
  - the body shifts 5–10% upward in the frame.
- **Downed:**
  - the figure is collapsed or kneeling, still inside the canvas;
  - colours desaturated about 40%;
  - the feet or knees stay on the foot row.
- **Portraits** (192×192): head and shoulders cut from the same character design, with the same light rig and a dark vignette background inside the square.
- The 320×320 icon crop box must contain the full figure.

### Crystal and platform
- **Concept:** an ancient holy relic, not a generic rhombus.
  - a tall faceted crystal with an asymmetric crown of shards;
  - set in a carved stone collar or pedestal with glyphs;
  - 2–4 suspended shards or a restrained orbital ring;
  - a luminous fracture network that grows with damage.
- **States:**

| State | Look |
|---|---|
| intact | clean facets; glyphs lit |
| cracked | bright fracture lines through 2–3 facets; one shard drifts lower |
| critical | half the shards dim or fallen; core flickers red-violet `#ff4a7a` inside; glyphs broken |

- All states are **pixel-registered**: same pedestal, same pivot, same overall bounds.
- **Separate from AoE:** the Crystal's own glow must not look like a zone decal. Keep its glow vertical (upward) and the ground pool small.

### Enemies / factions / bosses
- **Launch enemies** (grunt, runner, hexcaster, juggernaut …; no faction tag) are **Rift-born**:
  - ash-grey husk flesh or stone;
  - wine-red rift cracks glowing faintly;
  - fragments of broken armour from the sanctum's fallen guard.
- **Faction tags** (`enemies.json`) get one icon motif and one accent each:

| Faction | Motif | Accent |
|---|---|---|
| iron_legion | riveted plate, gears | rust orange |
| voidborn | star-holes, violet void | `#5146d9` |
| ashen_horde | cinders, charred bone | ember |
| frozen_covenant | rime, ice crowns | pale cyan |
| corrupted_wilds | bark, spores | sick green |
| arcane_fractures | floating runes, mirror shards | magenta |
| stormspire | copper, feathers, sparks | violet-gold |

- **Walk frames a/b:** contact pose and passing pose, with feet on the foot row. The silhouette IoU between a and b must be ≥ 0.6 (validator `enemyFrameIoU`).
- **Boss tells** are VFX (`Vfx/telegraph`) on the ground. The boss sprite itself must leave visual space around its feet and must not paint red ground glow that could be confused with a telegraph.

### Battlefield (biome)
The background is one flattened sprite at runtime. Production keeps **separate layers** in the source, composited in this order:

| # | Layer | Content |
|---|---|---|
| 1 | base terrain | basalt, ash and stone ground, with material variation in large shapes |
| 2 | path / traffic wear | enemies' lanes as **worn processional paths**: flattened, slightly lighter, value +8–12% vs. terrain, with edge stones. Not glowing, not uniform-width racetracks |
| 3 | ruins / structure | the sanctum floor: a carved stone dais around the Crystal that contains all 12 nodes (a ~5-unit radius ellipse at ratio 0.62); broken pillars, arches and stairs **outside** the lanes |
| 4 | cliffs / height planes | the outer ring drops away or rises in cliffs; vertical faces are visible because of the 38° view |
| 5 | cracks / decals | rift cracks (wine glow, low intensity), glyph rings on the dais |
| 6 | ambient particles / fog | low ground fog in the outer ring only, never over lanes near the dais |
| 7 | static props | braziers, statues, dead trees: only in the outer ring and never on a lane |
| 8 | occlusion / shadows | AO and long soft shadows consistent with the key light; a soft Crystal light pool at the centre |

- Units walk **over** the background: no tall object may stand on a lane or node, because it would look like units pass through it.
- **Coverage:** 16:9 sees 26.7×15 of the 30×17 image. 20:9 and 4:3 see beyond the image (known issue, logged for a later batch), so fade the image edge to the battle clear colour.
- **Clear colour:** the current clear colour is green (0.16, 0.30, 0.24), set in `BattleController.cs:125`. The lead will change it to match the new edge colour.

### VFX tiers (readability under density)
| Tier | What | Size / intensity |
|---|---|---|
| 1 | Boss tell (`telegraph`) | Strongest edge contrast; an arcane etched ring with an inner fill ≤ 35% alpha; crimson `#ff3a4a` danger tint (the code tints it) |
| 2 | Reaction (`ring`, reaction icons, fields) | Medium; element colour; carved-rune ring language |
| 3 | Skill / ultimate (`fireball`, zones) | Hero-centred; painterly flame, water or wind forms |
| 4 | Basic hit (`impact_*`, `slash`, `arrow`, `projectile_*`) | Small and quick; must not hide the unit; ≤ 60% alpha over its centre |

- The range circles are a debug or "show ranges" overlay only; never paint range rings into art.
- Ground decals (telegraph, ring, zone, field) are drawn as **flat circles**: the game squashes them to 0.62. Paint them top-down, not pre-squashed.

### HUD & icons
- **Style:** premium fantasy but compact. Dark slate and bronze surfaces, thin engraved borders, and one gem or rune accent. No tiny gothic filigree: at 1080p a border line must be ≥ 2 px.
- **9-slice borders are fixed by code:**
  - panels 40 px; tooltip 24; bars 18; buttons 36;
  - card frames 48 uniform (IMGUI ignores the 80 bottom border in .meta).

  The decorated edge must stay inside that border and the centre must tile cleanly.
- **Icons:**
  - one engraved medallion language: a dark disc or shield;
  - a bright symbol occupying 60–70% of the frame;
  - shape first, then colour (CVD: 8 element pairs are below ΔE 12, so shapes carry the meaning);
  - the symbols match the element shape cues in `Docs/Enhancement/ART_BIBLE.md` §3.

## 8. Evidence rules (never blur these)
| Evidence | What it is not |
|---|---|
| Concept art | not a production sprite |
| Blender render | not a Unity screenshot |
| Offline composite (`compose_frame.py`) | not gameplay |
| A pipeline written | not a regeneration run |
| A validator pass on format | not beauty |

- Pillow and numpy are utilities only: masks, packing, crop, alignment, guides. They are not final art.
- Before/after pairs use the same size, camera and gameplay state, and the source of each is labelled.
- Approval of art direction is the **owner's** decision. A machine checklist is never approval.
