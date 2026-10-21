# CODEX ART REQUEST — R05: real animation key poses (Aetherward, Art Bible v3)

Written by the lead (Claude Code) on 2026-10-21.

The R01 cast looks right as stills, but in motion it is stiff:
- walks have 2 frames;
- attacks are one strike pose;
- idle is one frame.

This batch adds the missing key poses. The lead sequences them in Unity:
- walk cycle: a → b → c → d;
- attack: windup → strike (`_attack`) → follow → idle;
- idle breathing: idle ↔ idle_b.

On top of those the lead adds procedural squash, lean, bob and smear.

Read with this file:
- `ArtHandoff/requests/R01/CODEX_ART_REQUEST.md`, sections 1–2 (style, camera, frames).
- `ArtHandoff/requests/COMMON_CONTRACT.md`, sections 4–10.
- `ArtHandoff/requests/R05/INPUT_MANIFEST.json`: 37 new frames. Each copies the canvas, foot row and pivot of its character's identity frame (`"like"`).

The current frames of every character are in `Assets/_Aetherward/Resources/Art/Heroes|Enemies/` (read only): `_idle`, `_walk_a`, `_walk_b`, `_attack`, `_cast` for heroes; `_a`, `_b`, `_attack` for enemies.

## 1. Poses
| Frame | Pose |
|---|---|
| Hero `_walk_c` | Contact pose, **opposite leg** to `_walk_a`: the other foot forward, arms counter-swung the other way |
| Hero `_walk_d` | Passing pose, opposite to `_walk_b`. The body is highest here |
| Hero `_windup` | Anticipation before `_attack`. Melee: weapon drawn back and up behind the body, weight on the back foot, torso twisted away from +X. Ranged/caster: bow drawn to full or staff pulled back, the focus charging |
| Hero `_follow` | Follow-through after `_attack`. Melee: weapon past the target, low and across the body, weight fully forward. Ranged/caster: arm still extended, recoiling, cloth swinging forward |
| Hero `_idle_b` | Breathing variant of `_idle`: chest and shoulders up 2–3 px, cloth and hair shifted a little. Everything else identical. Swapping the two must look like breathing, not a jump |
| Enemy `_c` / `_d` | Opposite-leg contact and passing poses, continuing `_a` → `_b` into a 4-frame cycle |
| Enemy `_windup` | Anticipation before `_attack`: the weapon raised or claws pulled back, body coiled |
| Boss `rift_warden_c` / `_d` | As for enemies (its `_tell` and `_attack` stay) |

## 2. Rules
- **Same character, scale, foot row and torso x** as the identity frame, within ±6 px and ±8 px. Same costume, palette and prop. Use the identity frame plus the neighbouring pose as references in every generation, at most 5 images.
- **Exaggerate.** These are key poses for a premium action game: strong lines of action, clear silhouettes, about 15 % more stretch than realistic. Never tiny changes that read as the same pose.
- No VFX painted in, except the allowed small weapon or focus glow.
- Cleanup is utility only: alpha, defringe, Lanczos downscale, foot alignment.

## 3. QA and return
- Self-QA per COMMON_CONTRACT section 6 with `--batch R05`. Intake must report 0 blocking problems.
- Add `previews/cycles_1440.png`: for each character, its full walk cycle and attack sequence in a row at game size, over the battlefield reference.
- Add an animated GIF per character in `previews/`, at 8 fps for the walk and 12 fps for the attack. Label them **offline previews**.
- The final message must give counts, the intake result and the top three risks.
