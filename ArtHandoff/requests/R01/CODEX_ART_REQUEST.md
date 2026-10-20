# CODEX ART REQUEST — R01: Ravenswatch-direction benchmark (Aetherward)

Written by the lead (Claude Code) on 2026-10-21. You are the art specialist (Codex 6.1 Sol, built-in image_gen).

The game is pivoting:
- **Gameplay:** "a party of up to 6 heroes that moves around a wide battlefield and defends a Crystal". It replaces "heroes as towers on fixed slots".
- **Art:** a new direction replaces the old dark painterly style.

This batch is the **style benchmark**. It is small on purpose. Nothing is mass-produced until the owner approves it.

Read with this file:
- `ArtHandoff/requests/COMMON_CONTRACT.md`. Its sections 4 (technical), 5 (frames), 6 (method), 7 (scope and rights), 8 (layout), 9 (done) and 10 (blockers) still apply. **Section 2 (style), the rim-light and value-separation rules in section 4, and the B01 style lock are REPLACED by section 1 below.**
- `ArtHandoff/requests/R01/INPUT_MANIFEST.json`: the 47 exact assets with size, foot row and guides. 14 of them are new frames (`"new": true`) that copy their sibling's contract.
- `ArtProduction/designs/heroes.json` and `enemies.json` (read only). Use them for **costume, prop and silhouette identity** only. Their palette notes belong to the old style; use the palettes in section 3 instead.
- `ArtHandoff/requests/R01/references/battlefield_toon_verdant.png` (and `_crop_1to1.png`): the lead's new battlefield, the ground every unit stands on.

## 1. Style (binding)
**Dark arcane fantasy, comic-ink, premium stylized 2.5D.**

Characters must look like premium hand-inked comic art:

| Element | Rule |
|---|---|
| Ink | Bold, confident black-violet ink contours (`#1b1226`). 4–6 px on the 800 master, giving ~3 px in game. Thicker on the outer silhouette, thinner inside. Lines taper as if drawn with a brush pen. |
| Shading | 2–3 flat cel tones per material with hard-edged shadow shapes. Sparse ink hatching only inside the deepest shadows. No airbrushed gradients, no soft painterly blending. |
| Light | One warm key light from the upper-left front. Shadow tones lean cool violet-blue (`#3b2f6b` family), never grey or brown mud. |
| Colour | Saturated jewel tones. Mid-to-high values on the lit planes. Each hero carries their element colour on 25–35 % of the silhouette, so a player reads the element at a glance. |
| Proportions | Heroic, slightly stylised: about 6.5 heads tall. Big readable props (shields, staffs, bows). Hands and props are oversized ~15 % for readability. Never chibi or cute, never mobile-casual, never flat vector. |
| Mood | Grim, mythic, arcane. Torn cloth, runes, worn metal, glowing sigils. Dark fantasy comes from the shapes and the shadow colour, **not** from making everything dark. |

**Readability test:** the units must read on the bright-ish green and sand battlefield reference (mean luminance about 0.4). The ink contour plus saturated colour does the separation; no rim light is needed.

Intake checks the outer 3 px edge band: its mean luminance must be ≤ 0.22, which means a dark ink contour is present.

**Licensing:**
- Never write "in the style of <game/artist>" in a prompt, and never copy any existing game's characters, logos or UI.
- Describe the look with the words above.

## 2. Camera and frames
- **Camera:** the camera, facing and canvas rules from COMMON_CONTRACT section 4 are unchanged.
  - Three-quarter front view at about 38° elevation, facing screen-right.
  - Heroes on the 400 contract plus an 800 master in `source/masters/`.
  - Enemies on 256, the boss on 512.
  - Feet on the foot row given in each guide.
- **Walk frames (new, because heroes now move):**
  - `_walk_a` is the contact pose: the leading foot forward toward +X, the rear foot back, arms counter-swinging.
  - `_walk_b` is the passing pose: legs crossing under the body, the body slightly higher.
  - Same character, same scale, same foot row and same torso x as `_idle`. Silhouette IoU with `_idle` is at least 0.55.
  - Enemies already use `_a`/`_b` the same way.
- **Other frame poses:** attack, cast, downed and tell are defined in COMMON_CONTRACT section 5.
  - Unit frames hold the character only. No projectiles, beams or ground effects.
  - A small emissive glow on the focus or weapon is allowed.
- **Portraits:** `Portraits/<id>` uses the same contract as the live portrait (see the manifest). Show the head and shoulders in the same ink style, on a flat dark violet background with an element-colour accent.

## 3. Roster and direction
Each hero must read as their **role** from the silhouette alone.

| Asset | Role | Direction |
|---|---|---|
| **glacius** | Tank (guardian), ice | The widest silhouette in the game. Frost-steel full plate, closed helm with an ice crest, a huge tower shield of glacier ice on the left arm, a short frost mace. Palette: steel blue, ice cyan `#7fe3ff`, a white-blue glow in the shield runes. |
| **ignis** | Mage, fire | Lean battle-mage in layered ember robes with burnt hems. A tall staff with a caged flame focus. Flowing cloth and a casting posture. Palette: crimson `#c0281a`, orange `#ff7a1a`, gold trim, charcoal undercloth. |
| **veyra** | Ranger, lightning | Slim and precise. Hooded storm-scout with light leather and a long recurve bow strung with crackling light. Palette: deep indigo, electric violet `#a98bff`, white-yellow sparks `#fff36a`. Her attack frame is the release, bow arm extended toward +X. |
| **marina** | Healer, water | Robed tide-priestess with a shell-and-coral crozier and a flowing veil. Calm and protective. Palette: sea teal `#2fb8b0`, aqua `#5fe0ff`, pearl white, a hint of coral. |
| **grunt** | Melee fodder (rift husk) | Hunched rift-born husk with a fused broken helm and a notched blade. |
| **runner** | Fast melee | Lanky, low, sprinting rift hound-man with claws forward. Reads as speed. |
| **hexcaster** | Ranged caster | Hooded cultist with a hex lantern or bone wand. Tall thin silhouette that reads as a caster from far away. |
| **juggernaut** | Brute | Massive armoured brute with a slab hammer, at least 200 px wide on the 256 canvas. |
| **ravager** | Elite | A clearly superior rift warrior: twin blades, spiked pauldrons, crown of rift-horns. It must read as dangerous next to the grunt. |
| **rift_warden** | Mini-boss | Towering rift knight on the 512 canvas, 400–450 px tall, with a glaive and a cracked halo of rift crystal. `_tell` holds the glaive high with glow building. `_attack` is the slam impact. |

**Enemy faction palette (all rift enemies):**
- Desaturated bone, rust and charcoal bodies.
- Rift magenta `#ff3d8b` and violet `#8a2be2` cracks and eyes, at most 15 % of the area.
- The enemies must never be confused with the heroes. Heroes are saturated jewel tones; the faction is muted bodies with hot rift accents.

## 4. Extra deliverables (concepts, not game assets)
Put these in `concepts/` and label them **MOCKUP / concept** in the README. They are direction targets, not screenshots.
1. `concepts/hud_concept.png` at 2560×1440: the battle HUD over the battlefield reference.
   - Top: wave banner, Crystal HP and shield bar, gold.
   - Bottom: 6 hero portrait cards with HP, skill and ultimate rings.
   - A stance switcher with three icons (Defensive / Balanced / Aggressive), a boss bar, and a "Crystal under attack" alert.
   - Premium dark fantasy frames: forged metal, rune inlays, ink outlines, the same comic style. Not mobile-casual.
2. `concepts/combat_scene_concept.png` at 2560×1440: the 4 heroes in action around a glowing Crystal on its ritual dais, fighting a rift wave with the ravager and the rift warden.
   - Show **huge, exaggerated, comic-styled magic**: a fire meteor burst, a chain-lightning web, an ice bloom and a water heal dome.
   - Hard-edged flat-colour flames and shards with ink accents, bigger and louder than typical ARPG effects, yet the Crystal, heroes and boss stay readable.
   - This becomes the VFX target the lead builds against.

## 5. Order and method
1. **glacius_idle first.** Iterate it until it nails section 1, then use it as the identity and style reference for everything else.
2. Then do:
   - every other glacius frame and its portrait;
   - the other heroes, each with its identity frame first;
   - the enemies, grunt first;
   - the boss;
   - the two concepts.
3. Attach at most 5 reference images per generation. Use the glacius identity frame plus the unit's own identity frame plus a pose reference from `ArtHandoff/requests/pose_refs/` where one fits.
4. Cleanup is utility only: alpha, defringe, Lanczos downscale, foot alignment, centring. Never redraw anatomy with code.
5. Run the self-QA commands in COMMON_CONTRACT section 6 with `--batch R01`. Intake must report 0 blocking problems.
6. Update `DELIVERABLE_MANIFEST.json` after each character, so partial work survives a usage limit.

## 6. Acceptance (judged by the lead in Unity at 1440p)
- Every unit reads its role and element at game size (about 190 px tall heroes, about 150 px enemies) on the toon battlefield.
- A consistent ink weight and cel style across all 10 characters. Nothing soft or airbrushed, nothing chibi.
- Walk frames animate without popping: same scale, foot row and torso x.
- Rift enemies are unmistakably the enemy faction. The elite and the boss read as threats at a glance.
- Honest README: which assets you think are below the bar, plus the top three risks.
