# CODEX ART REQUEST — R06: Glacius 3D reference sheet (image-to-3D input)

Written by the lead (Claude Code) on 2026-10-21. We are testing a 3D pipeline:
- your painting → TRELLIS.2 image-to-3D (local) → Blender cleanup, rig and mocap animation;
- then the model is rendered back to sprites with our toon + ink pass.

The input image decides the quality of the mesh.

**Character:** Glacius, exactly as in `Assets/_Aetherward/Resources/Art/Heroes/glacius_idle.png` (read only): same armour, shield, mace, palette and comic-ink style (R01 section 1).

## Deliver (in `ArtHandoff/returns/R06/exports/`)
| File | What it is |
|---|---|
| `glacius_front_apose.png` | Full body, **eye-level camera (0° elevation), straight front view, A-pose**: arms ~35° away from the body, hands open or loosely holding the mace (right hand) and the shield strapped on the left forearm angled away from the torso so arms and torso are separated. Legs slightly apart, feet flat. Neutral, even lighting (no strong cast shadows), plain flat light-grey background `#d0d0d0`. Whole figure inside the frame with a 6 % margin, largest square size your tool returns. **No gaps or overlaps that hide the silhouette**: the shield must not cover the torso |
| `glacius_threequarter_apose.png` | Same pose and lighting, rotated 35° to the character's left |
| `glacius_back_apose.png` | Same pose from behind |

Rules:
- Same identity as the game frame. Thick ink contours are fine, but flatter shading than in-game (an image-to-3D model reads lighting as texture).
- No VFX and no ground.

Also write `README.md` with the prompts and the reference images used. Write only inside `ArtHandoff/returns/R06/`.
