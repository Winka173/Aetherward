# CODEX ART REQUEST — Batch B01: Dark Mythic benchmark

| Field | Value |
|---|---|
| batch_id | `B01` |
| From | Claude Code — project lead. Owns architecture, Unity integration, QA and final acceptance |
| To | Codex (GPT‑6.1 Sol) — art production specialist |
| Repository | `C:\Users\Winka\Projects\Aetherward` (Unity 6000.4.8f1, branch `main`) |
| Your writable folder | `C:\Users\Winka\Projects\Aetherward\ArtHandoff\returns\B01\` — **only this folder** |
| Priority | Highest. This benchmark decides the art direction for the whole game |
| Goal | Produce **real, production-format art** for a representative slice of the game in the new direction. The owner will judge it at real game scale, in Unity, before anything else is regenerated |

This file is self-contained. You do not need any earlier conversation. If something here conflicts with another document, this file wins, and you report the conflict.

---

## 1. The game and why the art is changing
Aetherward is a 2D fantasy crystal-defense roguelike auto-battler:
- The player places up to 6 heroes on 12 nodes around a central Crystal.
- Enemies arrive along 6 lanes for 20 waves.
- The game has 12 elements, 40 reactions, hero evolutions, relics and 12 bosses.
- Combat is automatic, so the player mostly **watches**. Art must read instantly in a crowded fight.

**Current art:** all 795 sprites were drawn by Python/pycairo code. The style is chibi, pastel and flat vector with thick black outlines. **The owner rejected it.** You can see it in `ArtHandoff/requests/B01/references/current/` and `ArtProduction/reviews/B01/baseline/scene_current_1080p.png`.
- Use these files **only** for size, framing, pose purpose and orientation.
- **Do not imitate their style.**

**New direction: "Dark Mythic Fantasy — Painterly Stylized 2.5D".**
- Mature, ancient, corrupted and mysterious.
- Not too dark to play on a phone.
- The full rules are in `ArtProduction/ART_BIBLE.md`. **Read it completely before starting**; it is part of this request.

A previous attempt built characters out of Blender primitives. It proved the lighting and composition, but the figures looked like faceless figurines, and that is **not acceptable as final character art**. See `Reports/ArtDirection/benchmarks/mythic_720p.png`: use it for mood, light and value only.

## 2. Your environment (verified by the lead on this machine, 2026‑10‑20)
| Tool | Status |
|---|---|
| OS / hardware | Windows 11 Pro, Ryzen 7 9700X, 62 GB RAM, **RTX 5070 Ti** |
| Your image generation tool | Feature `image_generation` is enabled in your Codex install, and it returns transparent RGBA PNGs. **This is the primary tool for characters, portraits, icons and painterly finish** |
| Blender | **4.5.14 LTS**: `C:\Users\Winka\Tools\blender-4.5.14-windows-x64\blender.exe`. Headless works (`-b --factory-startup --python script.py`). Cycles has **OPTIX/CUDA on the RTX 5070 Ti**. Use it for hard-surface and geometry-locked work (Crystal states, battlefield layout) |
| Python | 3.11 with Pillow, numpy, scipy and opencv (`cv2`). No pycairo, no torch |
| Unity | **Not for you.** The lead imports and captures in Unity |
| Not available | Krita, GIMP, Inkscape, ImageMagick. **No paid or cloud services beyond your own tools** |

**Temp files:** set `TEMP`/`TMP` to `ArtHandoff\returns\B01\_work\tmp` for Blender and Python, because your sandbox may block the system temp folder.

If a tool you need is missing or fails, **stop that item and report it** (§10). Do not substitute geometric code drawings and present them as art.

## 3. Read first (all paths are relative to the repo root)
1. `ArtProduction/ART_BIBLE.md` — the binding style and technical rules.
2. `ArtHandoff/requests/B01/INPUT_MANIFEST.json` — the exact list of the **77 assets**, with facts read from the live project for each one:
   - size, PPU, pivot, 9-slice border, Unity GUID;
   - the code lines that use it;
   - `footRowFromTop` (the pixel row where the feet must touch), and `flyer` for flying enemies;
   - the current reference image and guide image paths.

   Do not invent asset IDs, and do not rename anything.
3. `ArtHandoff/requests/B01/references/guides/`:
   - `layout__World__arena_background.png`: the battlefield at its exact 2400×1360 pixel grid, with lanes (red bands), the 12 hero nodes (green), the Crystal footprint and the camera views.
   - `unit__*.png`: one per unit sprite. Each shows the canvas, the foot row (red), the centre line, the hero icon crop box (green, 40,80 → 360,400) and the ground-shadow footprint.
4. `ArtHandoff/requests/B01/benchmark_layout.json` — the fixed benchmark frame (which units stand where). It is used for every comparison.
5. `Assets/_Aetherward/Resources/Content/` (JSONC, with `//` comments): `heroes.json`, `evolutions.json`, `enemies.json`, `elements.json`, `arena.json`, `biomes.json` and `loc_en.json` for names and descriptions.

   **Read only.**

## 4. Hard technical contract (the lead's intake script rejects violations)
The game is Unity built-in 2D. Sprites are drawn by `SpriteRenderer` with one shared shader. There is **no runtime lighting, no post-processing and no animation clips**, so everything you paint is exactly what the player sees.

| Rule | Value |
|---|---|
| Format | PNG, 8-bit, sRGB, **straight (non‑premultiplied) RGBA**. `World/arena_background` is RGB with no alpha |
| Size | **Exactly** the `size` in INPUT_MANIFEST. Never change the canvas size. PPU and pivot are fixed by the project |
| Feet | For units and the Crystal, the lowest opaque pixel row (alpha > 128) must be within **±6 px** of `footRowFromTop`. `downed` frames are allowed +12 px |
| Flyers | `flyer: true` (storm_harpy): the lowest opaque row must be **at least 10% of the canvas above** the foot row. The body hovers; the separate shadow sprite marks the ground |
| Horizontal anchor | The body's centre of mass sits on the canvas centre line (x = width/2) |
| Facing | Every unit faces **screen-right** (the game mirrors it). 3/4 front view at ~38° elevation, body turned ~25° toward the right |
| Rotated sprites | `Vfx/arrow`, `Vfx/fireball`, `Vfx/projectile_*` and `World/lane_arrow` are rotated by code with `atan2(dir)`. Draw them **pointing +X (to the right)**, centred |
| Tinted sprites (the code multiplies a colour) | `Vfx/ring`, `Vfx/telegraph`, `Vfx/glow`, `UI/bar_fill` and the three `World/node_*`. Paint them **in white and neutral greys only** (saturation ≈ 0); the value and alpha structure carry the design |
| Ground decals | `Vfx/ring`, `Vfx/telegraph`, `Vfx/zone_*`: paint them **top-down as a circle**. The game squashes them to 0.62 itself |
| No baked ground shadow in units | `World/shadow` is drawn separately under every unit. A little contact AO **on the body** is fine; a shadow on a floor is not |
| Alpha edges | No colour halo. For every pixel with alpha < 32, set its RGB to the nearest opaque neighbour's RGB (defringe). The validator flags halos (`haloFringeRatio` 0.12) |
| 9-slice | `UI/panel_dark` border 40, `UI/tooltip` 24, `UI/bar_bg`/`UI/bar_fill` 18, `UI/button_primary_*` 36, `UI/card_rare` **48 on all sides** (the runtime ignores the 80 in the .meta). Decorated edges stay inside the border. The centre must stretch cleanly (flat or very low-frequency) |
| Text | Never paint letters or numbers into any asset |
| Masters | Also keep a 2× (or larger) master of every unit, portrait and icon in `source/masters/`. Downscale with Lanczos. Optionally add a light unsharp mask after downscaling |

**Game scale** (what the owner judges):
- A hero's 400 px canvas is 2 units = 144 px at 1080p, so a standing hero is about **90 px to the top of the head at 1080p and 60 px at 720p**.
- An enemy's 256 px canvas is 1.6 units = 115 px at 1080p.
- The boss canvas ×1.25 = 4 units = 288 px at 1080p.

Design for those sizes first: big shapes, clear value groups, strong rim light. Detail is a bonus at 2×.

## 5. How to produce it (method)
Order of work: **P0 → P1 → P2 → P3**.
- Update `DELIVERABLE_MANIFEST.json` after each priority tier, so partial results are usable.
- Do not stop after P0: continue through all tiers in this run. Stop only when blocked, and report.

### 5.1 P0 — style lock (deliver first)
`Heroes/ignis_idle`, `Enemies/grunt_a`, `World/crystal_intact`, plus a **style frame**: `previews/style_frame_1080p.png`.

The style frame is a painted concept of the benchmark scene. Use the layout guide as composition reference, show the new battlefield, Crystal, heroes and enemies, and label it as concept.

These three assets set the line, brush, light, palette and level of detail for everything after. Write the exact choices (palette hexes, light direction, edge treatment, prompt template) into `README.md` § Style lock, and reuse them verbatim for every later asset.

### 5.2 Characters (heroes, portraits, enemies, boss): image generation + utility cleanup
**Identity consistency is the main risk.** Use this order and stop at the first approach that keeps identity across frames:

1. **One sheet per character.** Generate idle, cast and downed for one hero **in a single image** (side by side, same scale, plain flat background or transparent), using the style-lock image as reference. Then slice it.
2. **Evolutions.** Generate them as a separate sheet that takes the approved base sheet as the reference image. Keep the face, hair, base palette anchor and signature prop. Change the silhouette as specified.
3. If your tool can edit from a reference image, use the base idle as the reference for each state.

**Cleanup — Python utility, allowed:**
- background removal to true alpha (or keep the tool's own transparency);
- defringe;
- uniform scaling so every hero has the same figure height on the 400 canvas:
  - the standing idle top of the head is **235–255 px above the foot row** (feet on row 372);
  - hoods, crests, staffs and weapons may rise to at most **290 px above the foot row** (row 82), so everything stays inside the 320 icon box (rows 80–400, columns 40–360);
  - guardians are wider, not taller;
- foot alignment to the foot row, and centring.

Do **not** redraw anatomy with code.

**Enemy walk frames a/b:** frame a is the contact pose, frame b is the passing pose. Same character, same scale. The silhouette IoU between a and b must be ≥ 0.6.

**Portraits:** generate them from the same character reference: head and shoulders, three-quarter view facing right, same light, dark vignette background filling the square.

### 5.3 Crystal: geometry-locked
The three states must be **pixel-registered**: same pedestal, same outline extents, same pivot.

**Recommended:** build the crystal and pedestal in Blender 4.5:
- Cycles on OPTIX; use the denoiser;
- orthographic camera at **38.3° elevation** (sin = 0.62), looking at the object from the front;
- the shared light rig: key upper-left-front `#ffe9d0`, rim back-right `#9fe8ff`, ambient night blue `#16233a`;
- an emissive core;
- render each state from **one scene** with damage toggled: fracture emission, shard positions, core colour.

Then do a painterly finish pass that does not move edges, for example a light brush-stroke texture in the shader or a controlled paint-over of the identical render.

You may use image generation instead **only if** the three states stay registered: the lead's intake measures their bounding boxes.

### 5.4 Battlefield (`World/arena_background` and its layers): geometry-locked to the gameplay
Enemies walk the lanes in `arena.json` and heroes stand on its 12 nodes. **The art must line up with those coordinates.**

**Recommended:** a Blender scene with lane and node geometry placed from `arena.json`.

The game maps world (x, y) straight to the screen. A floor seen at elevation θ projects ground depth by sin θ. So:
- place the floor geometry at **ground X = x, ground depth = y / 0.62**;
- use an orthographic camera at 38.3° elevation, `ortho_scale` = 30 units across 2400 px (PPU 80);
- centre the image on world (0, 0).

Overlay your render on `layout__World__arena_background.png` to check alignment. Put that overlay in `qa/`.

**Layers:** export the eight layers listed in ART_BIBLE §7 "Battlefield" as separate 2400×1360 RGBA PNGs into `source/battlefield/layers/NN_name.png`, plus the flattened RGB export.

**Painterly finish:** you may paint over the render with image generation or editing, but the lane and node positions must not move. The lead overlays the guide at intake.

### 5.5 VFX, icons, HUD
- Use image generation at 4× size, then downscale.
- VFX must look painterly-energetic, not vector circles.
- Respect the tint rules in §4 (white-only sprites) and the tiers in ART_BIBLE §7.
- For the HUD, test each 9-slice by stretching it to 3× width in a preview (`qa/nineslice_*.png`) to prove that it tiles.

### 5.6 Self-QA tools you may run (they write only where you point them)
```
cd C:\Users\Winka\Projects\Aetherward
python Tools\ArtPipeline\handoff.py preview --batch B01 --overlay ArtHandoff\returns\B01\exports\Art --out ArtHandoff\returns\B01\previews --tag b01
python Tools\ArtPipeline\handoff.py intake  --batch B01 --stage-dir ArtHandoff\returns\B01\_work\stage --qa-dir ArtHandoff\returns\B01\qa
```
- **`preview`** renders the benchmark frame at 1080p and 720p with the same camera, PPU and pivots as the game, plus colour, silhouette and grayscale unit sheets at game scale.
  - It is an **offline composite**. Label it as such, never as a game screenshot.
  - Compare your result with `ArtProduction/reviews/B01/baseline/scene_current_1080p.png`.
- **`intake`** is the lead's acceptance gate (size, alpha, foot row, flyer lift, manifest, write scope). **Run it before you finish.** Zero blocking problems is required.

## 6. Asset specifications
Names and roles come from the game data. The look is defined here. "Accent" means the element identity colour from `elements.json`. Accents cover ≤ 20% of a hero; the rest is the costume's own muted palette.

### 6.1 Heroes — 4 heroes of 4 different roles, Ignis with both evolutions
Common to all heroes:
- adult, heroic stylized, **5.5–6 heads tall**, head ~110%;
- oversized signature prop, +15–25%;
- painterly rendering with the shared light rig;
- coloured dark edge plus cool rim light, no black outline;
- faces readable: eyes and a lit nose/cheek plane at 2×.

**Ignis — "Ember Magus"** (fire, mage, starter). Shape: tall triangle.
- **`ignis_idle`:**
  - lean adult mage in layered charcoal and oxblood robes that flare to the floor;
  - an ash-grey mantle over the shoulders;
  - a **tall pointed hood** with a stiff peak bending backward;
  - the face half in shadow, lit from below by the staff orb;
  - a staff of blackened iron with an **ember orb caged in claw prongs**; the staff top rises above the hood tip;
  - faint ember seams glow at the hem and cuffs (`#ff6a2b`).
- **`ignis_cast`:**
  - the staff is thrust forward and up toward screen-right, and the orb flares bright;
  - the free hand is open with a spiral of embers;
  - the hood is pushed back slightly by heat; the body rises ~6%.
- **`ignis_downed`:**
  - kneeling on one knee, the staff planted diagonally, the head bowed;
  - the orb is dim ash-red; colours desaturated ~40%.
- **`ignis_evoA` — "Meteor Archmage"** (huge telegraphed meteors, slower casts). The silhouette gains mass **above the head and shoulders**:
  - a stiff high collar of basalt plates;
  - **three molten rock fragments orbiting above the hood**;
  - a longer staff crowned with a cracked magma stone;
  - robes deepen to crimson with magma-crack trims.
- **`ignis_evoA_cast`:**
  - the staff raised overhead with both hands;
  - the fragments fused into one glowing meteor above;
  - the mantle blown outward.
- **`ignis_evoB` — "Ember Weaver"** (spreads Burn, empowers reactions). Lighter and sinuous:
  - the hood opens into a draped veil;
  - **burning threads woven between the fingers** form looping arcs outside the body outline;
  - a shorter spindle-staff topped with a spiral;
  - the palette shifts to amber-gold and ash-white.
- **`ignis_evoB_cast`:** both arms spread, a burning thread web stretched between the hands.

Both evolutions must stay recognisable as Ignis (face, staff orb motif, oxblood anchor). They must also differ clearly from the base and from each other in silhouette.

**Terra — "Stone Warden"** (earth, guardian, starter). Shape: wide trapezoid, the heaviest silhouette, ≥1.35× Ignis's width.
- **`terra_idle`:**
  - a broad armoured warden in dark bronze-steel plate;
  - **carved stone slab pauldrons**, moss-flecked, with glyphs;
  - a closed helm with a visor slit and two short stone-horn crests;
  - an ochre tabard (`#c98a3e` accent);
  - a **huge two-handed maul** with a glyph-carved stone head, resting head-down at the right side;
  - the stance is wide and low.
- **`terra_cast`:**
  - the maul lifted overhead, about to slam;
  - the glyphs on the maul head glow amber;
  - small rock fragments rising around the feet. These are on the body layer, not ground decals.
- **`terra_downed`:** down on one knee, leaning on the upright maul, the head lowered.

**Sylph — "Gale Ranger"** (wind, ranger, starter). Shape: narrow body, long diagonal bow line.
- **`sylph_idle`:**
  - lean adult ranger;
  - a short hooded cloak with wind-torn edges, a teal lining (`#5fe8c8` accent), a leather jerkin and bracers;
  - a **longbow as tall as the body**, held diagonally;
  - a quiver of pale-fletched arrows;
  - the stance is turned sideways toward the right.
- **`sylph_cast`:**
  - full draw toward screen-right, the nocked arrow glowing teal;
  - the cloak streaming backward;
  - wind ribbons spiralling around the bow arm.
- **`sylph_downed`:** sitting slumped against nothing (no props on the ground), the bow across the lap, the hood fallen.

**Marina — "Tide Healer"** (water, healer, starter). Shape: calm vertical with a ring aura (the support read).
- **`marina_idle`:**
  - flowing layered robes of deep sea-blue and slate with pale sea-foam trim;
  - a **suspended halo-ring of water droplets** behind the head and shoulders;
  - a staff crowned with a **curling wave crest** of pale shell and coral;
  - the accent is `#2f8cff`;
  - serene posture.
- **`marina_cast`:**
  - the staff lifted high;
  - the droplet ring expanding and brightening;
  - droplets rising upward from the hands.
- **`marina_downed`:**
  - kneeling, the head bowed;
  - the droplet ring fallen into a loose arc around the shoulders and dim;
  - desaturated.

**Portraits** (`Portraits/ignis|terra|sylph|marina`, 192×192, full-bleed square, no transparency needed but allowed):
- head and shoulders from the base idle design, three-quarter view facing right;
- same light;
- a dark vignette background tinted faintly with the hero's accent;
- the face fills ~45% of the height.

### 6.2 Enemies — 4 archetypes
**Rift-born** look (launch enemies have no faction): ash-grey husk flesh or stone; faint wine-red rift cracks (`#6b2734` to `#a8324a`); fragments of the fallen sanctum guard's armour. **Never cute: no big round eyes, no blob bodies.**

Figure heights on the 256 canvas, with feet on row 236:
- grunt **140–160 px** (on screen ≈ 80% of a hero);
- hexcaster 170–190 px;
- juggernaut 195–215 px tall and ≥ 200 px wide;
- harpy wing span ≥ 200 px.

- **`grunt_a` / `grunt_b` — "Rift Grunt"** (basic melee, the most common unit). Compact and hunched:
  - a broken guard helmet fused into the skull;
  - glowing rift cracks across the chest and forearms;
  - a jagged notched blade in the right hand and a torn tabard;
  - reads as a mob unit;
  - a: contact stride; b: passing stride.
- **`juggernaut_a` / `_b` — "Juggernaut"** (huge, crowd-control resistant). Brute:
  - shoulders ≥ 2× the head width; a tiny head sunk between slab pauldrons;
  - armour slabs of rift-fused stone and iron;
  - deep crimson glow in the seams;
  - fists like boulders;
  - fills ~85% of the canvas width;
  - a heavy, slow stride.
- **`hexcaster_a` / `_b` — "Hexcaster"** (ranged, targets heroes from 3.6 m). Caster:
  - **elongated tattered robes** and a tall horned hood;
  - emaciated grey arms;
  - a floating hex sigil (wine-violet with a magenta core) above the raised left hand;
  - a gliding walk with small robe changes between a and b.
- **`storm_harpy_a` / `_b` — "Storm Harpy"** (faction **stormspire**: copper, feathers, sparks, violet-gold; a **flyer**):
  - **wing span wider than tall**, copper-feathered wings;
  - a lean predatory body with talons;
  - violet (`#b06cff`) lightning crackling between the primaries, with gold sparks;
  - **lifted ≥ 10% of the canvas above the foot row**;
  - a: wings up; b: wings down.

### 6.3 Boss
**`rift_warden_a` / `_b` — "The Rift Warden"** (final boss). The 512×512 canvas is shown ×1.25. Make the figure **400–450 px tall** with feet on row 486, which is about 230–250 px on screen at 1080p. Data: phase 1 summons riftlings; phase 2 marks a lane and assaults down it; phase 3 casts three slams, then is Exposed.

Design: the sanctum's **ancient guardian statue, animated and corrupted by the rift** — a dark mirror of the Crystal.
- Towering, with broad basalt and obsidian plate.
- A broken halo of **floating rift-crystal shards** above the head.
- A **massive glaive** held diagonally across the body (the threat silhouette).
- A chest core of crimson-violet rift light behind cracked plates.
- A tattered stone-grey cloak below the waist.
- Must read as "boss" at a glance: breaks the human rhythm with long arms, a hunched mass and the halo.
- Keep clear space at the feet. **No red ground glow**: the game's telegraph owns that.
- a: weight on the front foot; b: weight on the back foot, glaive shifted.

Optional (preview only, not wired in code): `previews/rift_warden_exposed_concept.png`, the phase‑3 Exposed look with the plates fallen and the core blazing.

### 6.4 Crystal (`World/crystal_intact | cracked | critical`, 320×400, feet row 372)
Read ART_BIBLE §7 "Crystal and platform". Summary:
- an **ancient holy relic**: a tall faceted crystal with an asymmetric crown of shards;
- seated in a **carved stone collar with glyphs**;
- 2–4 restrained suspended shards;
- refractive gradients from a white core to cyan `#8fe3ff` to aether blue `#2b5cff`;
- the brightest object in the game;
- its glow is vertical, with only a small ground pool.

| State | Look |
|---|---|
| intact | clean facets, glyphs lit |
| cracked | bright fracture lines through 2–3 facets; one shard drifts lower |
| critical | half the shards dim or fallen onto the collar; the core flickers red-violet `#ff4a7a`; glyphs broken |

All three states are pixel-registered. The game flashes the sprite pink on hits; do not paint a hit flash.

### 6.5 Battlefield — biome `verdant_sanctuary` (the default; `World/arena_background`)
The id stays. The look becomes **"the Warded Sanctum"**: an ancient basalt sanctum on a plateau at night, where desaturated teal moss and dark ivy are the only "verdant" left.
- **Centre:** a carved stone dais containing all 12 nodes (an ellipse of ~5 units radius, ratio 0.62), with concentric glyph rings, worn steps at the lane mouths, and the soft cyan light pool of the Crystal.
- **Lanes:**
  - **worn processional roads** of flagstones and packed ash, value +8–12% vs. the terrain;
  - edge stones, broken in places;
  - they must merge into the dais naturally. Heroes stand at the lane mouths; see the guide;
  - lanes are **never glowing** and never a uniform racetrack.
- **Outer ring:**
  - cliffs and height drops at the image edges, visible because of the 38° view;
  - broken pillars, a fallen arch, two cold braziers with faint teal fire, dead trees with ivy;
  - **everything tall stays off the lanes and nodes**;
  - low fog only in the outer ring;
  - faint wine-red rift cracks approach from the lane entrances (corruption), at low intensity.
- **Value budget:** the ground stays at value 15–45%. Only the Crystal pool and gameplay decals are brighter.
- **Edges:** fade toward the dark basalt colour. The 20:9 and 4:3 views see past the image; report the edge colour you used in the README.

Also in this group:

| Asset | Size / PPU | Spec |
|---|---|---|
| `World/node_empty` | 192×128 / 150 | Engraved stone socket ring with glyph ticks, drawn already in perspective (ellipse ratio ~0.62–0.67). **Neutral light greys only** (the code tints and pulses it). Centre mostly transparent |
| `World/node_occupied` | same | Same ring plus an inner engraved disc, slightly brighter |
| `World/node_highlight` | same | Same ring with brighter glyphs and a soft inner glow (still neutral; tinted at runtime) |
| `World/lane_arrow` | 128×128 / 160 | Carved arcane chevron **pointing +X (right)**, pale bronze-white with a soft glow. The code fades it in and out along the lane |
| `World/shadow` | 128×48 / 128 | Soft contact shadow ellipse, pure black, alpha ~0.75 in the centre falling off to 0, with no colour. Feet sit on it |

### 6.6 VFX — 12 representative sprites (tiers per ART_BIBLE §7)
| Asset | Size / PPU | Tier | Spec |
|---|---|---|---|
| `Vfx/telegraph` | 256 / 128 | 1 boss tell | **WHITE only** (tinted crimson by code). A top-down circular **etched arcane warning ring**: a thick bright outer rim with notched rune segments, a thin inner ring, and an inner fill ≤ 35% alpha with radial hatch. It must read on dark ground after tinting |
| `Vfx/ring` | 256 / 128 | 2 reaction / shield | **WHITE only**. A thin carved rune circle with a soft glow edge, transparent centre. Used for reaction bursts and the Crystal shield, tinted by element |
| `Vfx/zone_burning_ground` | 256 / 128 | 3 skill zone | Top-down circle of burning ground: ember cracks, licking low flames at the rim, soft edge fade |
| `Vfx/fireball` | 192 / 200 | 3 skill | Painterly fireball **flying +X**: a hot core, a trailing flame tongue to the left, ember sparks |
| `Vfx/glow` | 128 / 64 | cast burst | **WHITE only**. A soft radial glow with a faint 4-point flare. Additive-looking with alpha only |
| `Vfx/impact_fire` | 192 / 192 | 4 hit | Small flame burst with sparks; ≤ 60% alpha over the centre |
| `Vfx/impact_water` | 192 / 192 | 4 hit | Splash crown and droplets |
| `Vfx/impact_wind` | 192 / 192 | 4 hit | Crescent gust slashes |
| `Vfx/impact_earth` | 192 / 192 | 4 hit | Stone chips and a dust puff (also used as the enemy death puff) |
| `Vfx/projectile_water` | 128 / 230 | 4 | Water bolt **flying +X** with a spiral tail |
| `Vfx/arrow` | 192×96 / 220 | 4 | Wind-fletched arrow **pointing +X**, faint teal streak |
| `Vfx/slash` | 256 / 160 | 4 melee | Crescent slash arc, pale with an element-neutral warm edge |

### 6.7 Icons — 17 (one engraved medallion language)
- A dark engraved bronze or slate medallion, with a bright symbol filling 60–70%.
- Shape carries the meaning; colour supports it.
- Readable at 32 px.
- No text.

| Asset | Size / PPU | Symbol |
|---|---|---|
| `Icons/element_fire` | 128 / 256 | Flame tongues, spiky |
| `Icons/element_water` | 128 / 256 | Droplet with a wave curl |
| `Icons/element_wind` | 128 / 256 | Triple swirl ribbon |
| `Icons/element_earth` | 128 / 256 | Stacked angular boulders |
| `Icons/role_guardian` | 96 / 240 | Tower shield |
| `Icons/role_mage` | 96 / 240 | Staff with an orb |
| `Icons/role_ranger` | 96 / 240 | Drawn bow |
| `Icons/role_healer` | 96 / 240 | Open hand with a droplet halo |
| `Icons/status_burn` | 96 / 240 | Small flame on a cracked ring |
| `Icons/status_wet` | 96 / 240 | Three falling drops |
| `Icons/status_stun` | 96 / 240 | Orbiting stars over a jagged ring |
| `Icons/status_shield` | 96 / 240 | Faceted crystal shield |
| `Icons/reaction_vaporize` | 128 / 200 | Flame and droplet merging into steam |
| `Icons/reaction_firestorm` | 128 / 200 | Flame caught in a swirl |
| `Icons/ui_crystal` | 96 / 240 | The new Crystal's silhouette |
| `Icons/ui_gold` | 96 / 240 | Stacked ancient coins with a rune |
| `Icons/ui_wave` | 96 / 240 | Banner with chevrons |

The element and status icons sit next to icons from the old set that are not being replaced in B01. That is expected.

### 6.8 HUD — 9 sprites (IMGUI 9-slice, borders in §4)
Common style: dark basalt or slate surface, a thin engraved bronze border (≥ 2 px at 1080p), one small rune or gem accent in the corners. Compact; not gothic filigree.

| Asset | Size | Spec |
|---|---|---|
| `UI/panel_dark` | 128×128 | Main panel. Border 40 holds the corners; the centre is flat dark slate with a very subtle texture |
| `UI/tooltip` | 96×96 | Lighter-edged, thinner border, border 24 |
| `UI/bar_bg` | 128×40 | Recessed dark track with a bronze rim (border 18) |
| `UI/bar_fill` | 128×40 | **WHITE/neutral only** (tinted by code): a glossy painted fill with a top highlight band (border 18) |
| `UI/button_primary_normal`, `_hover`, `_pressed`, `_disabled` | 192×96 | Engraved bronze-framed slab with a warm amber inner plate (border 36). **Hover:** brighter rim. **Pressed:** inset, darker, 2 px lower. **Disabled:** desaturated, low contrast |
| `UI/card_rare` | 256×360 | Card frame. Rare tier = cool blue-silver metal with a sapphire gem at the top centre. Border **48 on all sides**. The **centre is transparent or near-flat dark**: the art and text are drawn inside by code |

## 7. What you may and may not touch
- **Write only inside `ArtHandoff\returns\B01\`.** Do not create, modify, move or delete anything else in the repository: no `Assets/`, no `Tools/`, no `ProjectSettings/`, no `.meta` files, no content JSON.
- No git commands that change state: no commit, add, checkout, reset or stash. Read-only git is fine.
- Do not change gameplay, data, scenes, prefabs or code. If an asset needs a code change to look right (for example a new frame type), **describe it in the README** and the lead will decide.
- **Licensing:**
  - Use only your own generations, your own Blender work and the repo's own files.
  - No third-party textures, models, fonts or brushes unless they are CC0 and recorded with a URL in the manifest.
  - Do not prompt "in the style of <artist or game>", and do not copy any existing game's characters.
- No paid or cloud services beyond your own built-in tools.

## 8. Return layout
```
ArtHandoff/returns/B01/
  DELIVERABLE_MANIFEST.json      (template: ArtHandoff/requests/B01/DELIVERABLE_MANIFEST.template.json)
  README.md                      style lock, method per group, tools and versions, prompts used, known issues, blockers
  exports/Art/<Category>/<name>.png   final files, exact contract; the path mirrors Assets/_Aetherward/Resources/Art
  source/
    masters/                     2x+ masters of units, portraits and icons
    sheets/                      raw generated sheets before slicing (as generated)
    blender/                     .blend files + the .py scripts that build and render them (re-runnable headless)
    battlefield/layers/          the 8 layers, 2400x1360 RGBA
    scripts/                     every Python cleanup/slice/align script you used (re-runnable)
  previews/                      style_frame_1080p.png (concept), handoff.py preview outputs, optional boss concept
  qa/                            intake output, layout overlay, 9-slice stretch tests, before/after crops
  _work/                         scratch (may be deleted by the lead)
```

## 9. Definition of done (the lead verifies every point)
1. All 77 assets are in `exports/Art/...` with the exact contract, **or** listed as `blocked`/`skipped` with a concrete reason.
2. `handoff.py intake` reports **0 blocking problems**. Its JSON is in `qa/`.
3. Every export is traceable in `DELIVERABLE_MANIFEST.json` to:
   - its source (sheet, master, .blend);
   - its generator (image generation or Blender script and version);
   - the cleanup script.

   Generation prompts are recorded.
4. Re-runnability: the Blender scripts re-render headless, and the cleanup scripts re-produce the exports from `source/`. Image generation itself is not deterministic, so its raw outputs are kept in `source/sheets/`.
5. `handoff.py preview` outputs are in `previews/`, at 1080p and 720p, plus the silhouette and grayscale sheets.
6. `README.md` is honest:
   - what worked and what did not;
   - where identity consistency drifted;
   - which assets you think are below the bar, and why.

   **Do not claim "premium" or "approved"**: approval belongs to the owner.
7. Nothing outside `ArtHandoff/returns/B01/` was changed.

## 10. Blockers and honesty
- If your image generation tool is unavailable or refuses, or Blender fails:
  - stop that group;
  - write `status: "blocked"` with the exact error in the manifest;
  - continue with the groups you can do.
- **Never** replace a blocked painterly asset with a geometric or code-drawn stand-in presented as final. A clearly labelled placeholder is allowed only if it is marked `status: "placeholder"`.
- Report every limitation that affects quality: resolution, consistency drift, alpha problems, alignment.
- When finished, the last message of your run must be a short summary:
  - delivered / blocked counts;
  - intake result;
  - the top three risks you see.
