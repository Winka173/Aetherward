# CODEX ART REQUEST — R03: HUD / UI benchmark (Aetherward, Art Bible v3)

Written by the lead (Claude Code) on 2026-10-21. R01 (units) and R02 (VFX) are integrated and look right in Unity. The HUD still uses the old flat-blue panels.

Your `ArtHandoff/returns/R01/concepts/hud_concept_LOW_RES_DRAFT.png` is the target: forged dark-metal frames, rune inlays, ink outlines and gem accents, in the same comic-ink style.

Read with this file:
- `ArtHandoff/requests/R01/CODEX_ART_REQUEST.md`, section 1 (style).
- `ArtHandoff/requests/COMMON_CONTRACT.md`, sections 4 and 6–10.
- `ArtHandoff/requests/R03/INPUT_MANIFEST.json`: 56 assets with exact size, PPU and **9-slice border** per asset. Every guide is under `references/guides/`.

## 1. How the game uses these (IMGUI, 1920×1080 virtual, scaled to the screen)
| Group | What it is |
|---|---|
| **9-slice frames** | `panel_*` (border 40), `tooltip` (24), `bar_bg` / `bar_fill` (18), `button_*` (36), `card_*` (48). Corners and edges inside the border are kept; the centre and edges stretch. Put all ornament (corner caps, rivets, gems) **inside the border band**. Keep the centre area plain and low-contrast, because text and icons are drawn over it |
| `bar_fill` | **Tinted by code** (HP red/green, shield blue, skill gold). Draw it neutral light grey/white with a subtle bevel and an ink edge. No hue |
| `bar_bg` | The empty track behind the fill: dark recessed metal |
| `button_<tone>_<state>` | 4 tones × 4 states. The label is drawn on top in white. **primary** is gold/ember accent, **secondary** arcane teal, **danger** crimson, **ghost** a dark frame with a faint fill. **hover** is a little brighter with rim glow, **pressed** darker and inset, **disabled** desaturated |
| `panel_dark` | The main HUD frame (top bar, hero dock, tooltips, shop): the hud_concept frame |
| `panel_glass` | Translucent: the frame at ~70 % alpha, the centre at ~55 % |
| `panel_light` | Lighter parchment-metal |
| `panel_danger` | Crimson-trimmed alert, for "Crystal under attack" and boss warnings |
| `card_<rarity>` | Draft cards, 256×360, one per rarity: common iron, rare blue steel, epic violet, legendary gold, cursed sick green-black with cracks. Leave the art window and text area plain |
| `title_emblem` | The game logo plate, 1024×320, transparent. Use a forged sigil and crystal emblem with an empty band for the title text. **No letters**: the game renders "AETHERWARD" itself |
| `vignette` | Keep it a soft dark edge vignette, 512×288. A plain technical asset, no ornament |
| `Icons/ui_*` | 96×96 UI icons in the same ink style: bold silhouette and 2–3 tones on transparent. Gold, crystal, heart, shield, sword, wave, speed, pause, play and the rest keep the meaning their names say. They must read at 32 px |
| `Icons/ui_stance_defensive / balanced / aggressive` (new) | The party stance switcher: a tower shield, a balance scale, crossed swords, as in the hud_concept |

## 2. Rules
- Same ink colour (`#1b1226`) and cel style as R01. Metal is dark gunmetal and violet-black with worn gold or bronze trim; gems in the element colours.
- Premium dark fantasy. Not mobile-casual: no candy gradients, no bubbly shapes.
- 9-slice safety: nothing important in the stretch zones. Test each frame stretched 3× wide and 2× tall in your preview, so stretching does not smear ornaments.
- Text contrast: white text must read on every button and panel centre (contrast ≥ 4.5:1 against the centre colour).

## 3. Order and QA
1. Do `panel_dark` first, matched to the hud_concept frame.
2. Then the buttons, bars, the other panels, tooltip, cards, emblem, icons and stance icons.
3. Self-QA per COMMON_CONTRACT section 6 with `--batch R03`. Intake must report 0 blocking problems.
4. Add `previews/hud_mock_1440.png`. It is an **offline composite**, labelled as such: the stretched frames assembled into the HUD layout over `ArtHandoff/requests/R01/references/battlefield_toon_verdant.png`.
5. The final message must give counts, the intake result and the top three risks.
