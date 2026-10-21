# CODEX ART REQUEST — R04: hand-painted battlefield (Aetherward, Art Bible v3)

Written by the lead (Claude Code) on 2026-10-21.

The owner judges the in-game graphics at about 20–30 % of the reference quality. The biggest single cause is the battlefield. Today it is a Blender render of photo scans run through a toon filter: muddy, speckled, nothing designed.

Your R01 `hud_concept` repainted almost exactly this layout, and it looked far better. This batch makes that the real game background.

## 1. Inputs (in `ArtHandoff/requests/R04/references/`)
| File | Use |
|---|---|
| `verdant_layout.png` (3344×1882) | The current composition: every lane, the dais, props and cliffs. Repaint it |
| `verdant_guide.png` | The same image with the **simulation geometry** on top: lane centre lines and widths (red), spawn points, the inner dais ring (yellow ellipse), the Crystal socket (cyan), the open intercept field (white circle) and hazards (orange, if any). **These must stay exactly where they are** |
| `style_ref_hud_concept.png`, `style_ref_combat_concept.png` | Your own R01 concepts: the target look and detail density |

## 2. What to paint
One finished battlefield illustration of the **Verdant Sanctuary**, the full 16:9 view (36 × 20.25 game units), at the largest 16:9 size your tool returns.

The lead upscales it 4× with Real-ESRGAN (anime model), so clean ink and flat cel shapes upscale best. Avoid fine noise and grain.

**Hard rules:**
- **Layout lock.** Keep the lane paths exactly on the guide's red bands: same centre lines and widths, lighter worn paths that read clearly. Keep the dais ring centre and size, and the Crystal socket position. No prop may stand on a lane or inside the white circle.
- **Do not paint the Crystal itself.** Leave an empty glowing socket and pedestal ring at the cyan mark; the game draws the Crystal there.
- **Nothing alive or temporary:** no characters, enemies, VFX or UI.
- **Shadows:** cast toward the screen **upper-right** (direction x +0.82, y up +0.57), length about 0.9 × object height. The game projects unit shadows the same way.
- **Camera:** the same three-quarter top-down view, ~38° elevation, as the layout.

**Look (Art Bible v3):**
- Premium dark arcane comic-ink: bold `#1b1226` contours on every prop, 2–3 flat cel tones, violet-blue shadows, a warm key light.
- Saturated but mid-value ground, so units stay the brightest, most saturated things on screen.
- Detail density like your HUD concept, all of it designed:
  - grass tufts, moss, flowers and leaf litter on the ground;
  - worn flagstones on the dais;
  - cracked rune stones, ivy on the pillars, roots, small ruin debris;
  - glowing aether crystals in clusters;
  - cliffs with layered strata;
  - braziers with lit fire bowls.
- Keep the ground under the lanes and the intercept field calm (low detail contrast), so combat reads on top. Push detail toward the edges.

## 3. Deliver
- `exports/World/verdant_paint.png`: the painting, untouched, at the native size.
- `exports/World/verdant_paint_on_guide.png`: the painting with the guide's red, yellow and white lines overlaid at 50 %, to prove the layout lock.
- `README.md`: the prompts, the references attached, your honest opinion of where it is weaker than the HUD concept, and the top three risks.

Iterate until the layout-lock overlay matches: a lane offset by more than about a quarter of a lane width is a fail. Regenerate rather than warp.

Scope: write only inside `ArtHandoff/returns/R04/`. No git, no Assets.
