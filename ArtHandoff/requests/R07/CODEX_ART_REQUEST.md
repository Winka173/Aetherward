# CODEX ART REQUEST — R07: the Haven keep battlefield (Aetherward, Art Bible v3)

Written by the lead (Claude Code) on 2026-10-21.

The owner changed the map style:
- **Before:** an open field around the Crystal.
- **Now:** a **walled keep (the Haven) that the party defends while the wave breaks in through its gates**, like a "defend your haven" game. The owner's reference showed:
  - a top-down stone keep with thick walls;
  - an inner courtyard with braziers and banners;
  - a main gate in the south wall that the horde floods into;
  - heroes holding inside;
  - grass fields outside.

The simulation is already built for this layout. Your painting must match it exactly.

## 1. Inputs (in `ArtHandoff/requests/R07/references/`)
| File | Use |
|---|---|
| `haven_guide.png` (3344×1882 = the full 36 × 20.25-unit view) | The locked layout, colour-coded below. Everything outside the walls is open grass field with the approach roads |
| `style_ref_r04_verdant_paint.png` | Your R04 Verdant painting: the target style, palette and detail density. Keep the comic-ink look and the same grass, path and prop language |

`haven_guide.png` colour code:
- **Dark blocks with white outline:** the **wall footprints**, where each wall meets the ground. Paint each wall as a thick stone rampart rising up on screen from that footprint (~38° three-quarter top-down view). The south wall shows its outer face and battlements; the side walls show their tops.
- **Gaps in the walls (green circles):**
  - the **main south gate**, an arched gatehouse with an open, broken or raised portcullis;
  - two **side gates**, west and east.
  - They are open passages, and the floor in each must be clear.
- **Faint white rectangles:** where heroes stand and walk: the courtyard, the gate passages, and the aprons in front of each gate. Keep them clear of tall props; small floor detail is fine.
- **Red bands:** the enemy approach roads. Paint them as trampled dirt roads outside, turning into the gate passages, then flagstones inside.
- **Yellow ellipse:** the Crystal's ritual platform in the courtyard centre, a raised round stone dais with runes.
- **Cyan ring:** the Crystal socket. **Do not paint the Crystal** (the game draws it). Leave an empty glowing socket.

## 2. Look
- **Inside the keep:** worn flagstone courtyard, braziers with fire bowls, hanging banners in deep blue and gold, weapon racks, crates, a few arcane crystal clusters along the walls. Ivy on the stones.
- **Outside:** grass fields, scattered rocks, dead trees and ruins at the edges. Keep the approach roads readable.
- **Lighting and shadows:**
  - Warm braziers inside, a slightly cooler night-dusk tone outside. The courtyard is the brightest area.
  - Cast shadows toward the upper-right (x +0.82, y +0.57).
- Same comic-ink style as R01/R04: bold `#1b1226` contours, 2–3 cel tones, violet-blue shadows.
- No characters, no enemies, no VFX, no UI, no Crystal.

## 3. Deliver
- `exports/World/haven_paint.png`: native 16:9 size, untouched.
- `exports/World/haven_paint_on_guide.png`: the guide overlaid at 50 %, to prove the lock.
  - Walls must sit on their footprints, within about ¼ of a wall thickness.
  - Gates must sit at the green circles.
  - Roads must sit on the red bands.
- `README.md`: the prompts, your honest weak points, and the top three risks.

Iterate until the lock overlay matches. Regenerate rather than warp. Write only inside `ArtHandoff/returns/R07/`.
