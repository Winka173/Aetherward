# Aetherward Art Bible v3 — Dark Arcane Comic-Ink, Premium Stylized 2.5D (Dynamic Party)

Owner decisions, 2026-10-21:
- Drop the dark painterly v2 ("tối không ổn").
- Lead reference: **Ravenswatch**, for mood, silhouette, comic ink and readability. Learn from it; never copy characters, creatures, logos, UI or environments.
- The game becomes a **Dynamic Party Crystal Defense**: up to 6 heroes move, intercept and protect the Crystal on a wider battlefield.
- **Magic must be bigger and louder than the reference**, while the Crystal, heroes, boss and danger zones stay readable.

## 1. Direction in one paragraph
A grim mythic world drawn like a premium inked comic:
- bold brush-pen black-violet contours;
- 2–3 flat cel tones per material, with hard shadow shapes leaning violet-blue;
- saturated jewel colours on mid-to-high values.

Dark fantasy comes from shapes, cracks, runes and the cool shadow colour, not from low values. Heroes are heroic (~6.5 heads, oversized readable props), never chibi or casual. Enemies are muted bone, rust and charcoal bodies with hot rift accents. Magic is hard-edged flat-colour shapes with ink accents, oversized and exaggerated.

## 2. Projection and scale contract (facts)
| Item | Value | Source |
|---|---|---|
| Battlefield | Every arena distance × `ContentDatabase.WorldScale` = **1.3** (bounds ±15.6 × ±9.1, lanes, spawns, start nodes, hazards, covers). The Crystal is unchanged | `Simulation/Content/ContentDatabase.cs` |
| Camera | Orthographic, `orthographicSize = max(9.6, 17.4/aspect)`, so ~34 × 19 units are visible at 16:9. Light tracking leans toward the party centroid (×0.45), clamped to the background margin | `Unity/Battle/BattleController.cs` (`FitCamera`, `UpdateCameraFocus`) |
| Background | 4096×2048 RGB, PPU 102.4, **40 × 20 units**. Power of two, so it gets DXT1 + mips | `sanctum_env.py`, `env_finish.py` |
| Floor projection | Ellipses y = 0.62 × radius (~38° elevation). Ground depth y/0.62 in Blender | unchanged |
| Units | Sprites ×`WorldGfx.UnitScale` = 1.18. Hero 512² at PPU 256 (feet 0.07). Enemy 256² (feet row 236). Boss 512² (feet row 486) | `WorldViews.cs`, COMMON_CONTRACT §4 |
| Animation | Heroes: idle, **walk_a/walk_b (new)**, attack, cast, downed (+ evo idle, cast, attack). Enemies: a/b walk, attack. Bosses also tell. Bob, lunge, recoil, squash, flash, dissolve and shadows are procedural | `WorldViews.cs` |
| Render | Built-in pipeline, Gamma. Light and shadow are painted into sprites. Unit cast shadows are a separate projected sprite | unchanged |

## 3. Palette
| Family | Rule |
|---|---|
| Ink | `#1b1226` black-violet on every contour, environment props included |
| Shadow | Cool violet-blue `#3b2f6b` family. Never grey or brown mud |
| Lit | Warm key `#fff1dc`, from the upper-left front |
| Heroes | Element colour on 25–35 % of the silhouette. Fire `#ff7a1a`/`#c0281a`; Ice `#7fe3ff`; Lightning `#a98bff` + `#fff36a`; Water `#2fb8b0`/`#5fe0ff`; Wind, Earth, Light, Shadow, Nature, Poison, Arcane, Void follow the element colours in `Ui.ElementColor` |
| Enemies (rift faction) | Desaturated bone, rust and charcoal bodies. Rift magenta `#ff3d8b` and violet `#8a2be2` cracks and eyes, ≤ 15 % of the area |
| Battlefield | A biome gradient map (`TOON_RAMPS` in `sanctum_env.py`). View mean luminance ≈ 0.40. Lanes are clearly lighter paths |

## 4. Silhouette by role (dynamic party)
Each role must read from the silhouette alone, at ~110–190 px tall on a 1440p screen.

| Role | Shape language |
|---|---|
| Tank / Guardian | The widest. Heavy plate, a big shield, square shoulders |
| Bruiser | Forward-leaning mass, a big two-handed or paired weapon |
| Mage / Controller | Tall and narrow. Flowing cloth, a staff with a lit focus |
| Ranger | Slim and long-limbed. Bow or long weapon held off-body |
| Assassin | Low and sharp. Blades, a hood, angled stance |
| Support / Healer | Vertical, calm. Crozier or relic, robes, a soft halo accent |
| Elite | Grunt-sized or bigger with spikes, a horn crown and twin weapons. Reads as dangerous next to fodder |
| Boss | 400–450 px on 512. Unique outline, a big prop, a glowing weak point. `_tell` pose held under a telegraph |

## 5. Battlefield
- **Layout:**
  - The Crystal stands on a large ritual dais (the inner ring).
  - An open intercept field surrounds it.
  - Six readable lanes enter from every side.
  - Ruins, pillars, statues, braziers, trees and rocks frame the field and keep away from lanes.
- **Look:** Blender env → toon pass:
  - Cycles passes;
  - three cel light bands, violet shadows and a warm lit tone;
  - Kuwahara-flattened albedo, saturated and gradient-mapped;
  - pass-based ink lines (object-id and depth breaks).
- **Not too busy, not too empty:** props cover at most ~18 % of the view. No prop stands on a lane or on the dais ring.

## 6. Magic and VFX hierarchy (bigger than the reference, still readable)
| Tier | Examples | Rule |
|---|---|---|
| T1 Boss telegraph | Slam rings, lane marks | Always on top. High-contrast red/white edge, never hidden by other fx |
| T2 Ultimates and big reactions | Meteor, chain web, ice bloom, heal dome | Flipbook + additive flash + ground shockwave + sparks + shake (`BattleController.Burst`). 1.2–3.2 units |
| T3 Skills and impacts | Element impacts, crit flash | 0.85–1.35 units, short |
| T4 Ambience | Brazier and crystal glows, mist | Low alpha, never above units |

- **Style:** hard-edged flat colour bands (rank-banded ramps in `vfx_sheets.py`). Ink rims on smoke, steam, rift mist and water. Additive glow and halo on fire and lightning.
- **Readability guards:**
  - Opacity caps on T2/T3 over units.
  - Pool cap (320).
  - Reduced-VFX and battery modes drop T3/T4 first.
  - The Crystal and boss outlines stay visible.

## 7. Crystal
The visual centrepiece:
- glowing core with ink outline;
- ritual pedestal and aura;
- states: intact, cracked, critical, plus path overlays (bastion dome, pulse runes, thorns);
- visible through any fight.

## 8. HUD
Premium dark fantasy in the same ink style: forged metal frames, rune inlays.
- **Top:** wave banner, Crystal HP and shield, gold.
- **Bottom:** hero cards with HP, skill and ultimate rings; stance switcher (Defensive / Balanced / Aggressive).
- **Alerts:** boss bar, "Crystal under attack".

## 9. Evidence rules (never blur these)
| Evidence | What it is not |
|---|---|
| Concept / mockup (Codex `concepts/`) | Not a production sprite, not a screenshot |
| Blender render | Not a Unity screenshot |
| Offline composite (`handoff.py preview`) | Not gameplay |
| Sim benchmark numbers (`Tools/SimHarness`) | Not a visual result |
| Unity capture (`unity_capture.py`, real Battle) | The only gameplay evidence |

Approval of the art direction is the **owner's** decision. A machine checklist is never approval.
