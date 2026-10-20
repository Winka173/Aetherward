# COMMON CONTRACT — every Aetherward art batch after B01

This file is binding for every `CODEX_ART_REQUEST.md` that references it. The batch file adds the asset list and the per-asset designs. If the two conflict, the batch file wins for its own assets, and you report the conflict.

## 1. Roles
- **Claude Code — lead.**
  - Writes the briefs and accepts or rejects the returns.
  - Integrates the art into Unity.
  - Owns all animation, shaders, particles and code.
- **Codex — art production specialist.**
  - Produces real art assets.
  - Writes only inside `ArtHandoff\returns\<batch>\`.

Repository: `C:\Users\Winka\Projects\Aetherward` (Unity 6000.4.8f1).

## 2. Style (binding)
1. `ArtProduction/ART_BIBLE.md`: read it completely.
2. **Style lock from B01:** `ArtHandoff/returns/B01/README.md` § Style lock, and the prompt template in `ArtHandoff/returns/B01/DELIVERABLE_MANIFEST.json` → `styleLock`.
   - Reuse the palette, the light rig, the edge treatment and the prompt prefix **verbatim**.
3. **Approved reference images:** the batch file lists them under "Style references".
   - Attach them to your image generation calls as references whenever your tool accepts reference images.
4. **Never imitate the old art.** The old art is chibi, pastel and vector. The `references/current/` images are there only for size, framing, pose purpose and orientation.

## 3. Environment (verified on this machine)
| Item | Value |
|---|---|
| Machine | Windows 11, RTX 5070 Ti, 62 GB RAM |
| Image generation | Your `image_generation` tool. This is the primary tool for characters, icons, cards, relics, VFX and portraits |
| Blender | 4.5.14 LTS: `C:\Users\Winka\Tools\blender-4.5.14-windows-x64\blender.exe`. Run it headless; Cycles OPTIX is available. Use it for geometry-locked work: battlefields, crystal |
| Python | 3.11 with Pillow, numpy, scipy and opencv |
| Temp files | Set `TEMP`/`TMP` to `ArtHandoff\returns\<batch>\_work\tmp` |
| Unity | Not for you |
| External services | None beyond your own built-in tools |

## 4. Technical contract (enforced by `Tools/ArtPipeline/handoff.py intake`)
- **Format:** PNG, 8-bit, sRGB, straight RGBA. Battlefield flats are RGB.
- **Size:** use exactly the `size` given in INPUT_MANIFEST. PPU and pivot are fixed by the project.
- **Hero canvas:** the game stores heroes at 512×512 (PPU 256), because Unity compresses sprites only at power-of-two sizes.
  - Deliver either the 512 canvas named in INPUT_MANIFEST, or the 400 contract **plus** the 2× master (800×800, identical framing) in `source/masters/`. The lead resamples the master to 512.
  - The geometry scales with the canvas: feet at 0.07 of the height, the icon box at (0.1, 0.2) with size 0.8, head top 0.59–0.64 of the height above the feet, props ≤ 0.725.
- **Foot row:** for units and the Crystal, the lowest opaque row (alpha > 128) must be within **±6 px** of `footRowFromTop`. `downed` frames are allowed +12 px.
- **Flyers** (`flyer: true`): the lowest opaque row must be at least 10% of the canvas above the foot row.
- **Horizontal anchor:** the torso centre sits on x = width/2 in **every frame of a character**, within ±8 px. Frames must not jitter when the game swaps them.
- **Facing:** every unit faces **screen-right**. Use a three-quarter front view at ~38° elevation, body turned ~25° to the right. The game mirrors the sprite when needed.
- **Hero bounds:** everything stays inside the icon box, columns 40–360 and rows 80–400 of the 400 canvas.
  - The top of the head sits 235–255 px above the foot row.
  - Props may reach at most 290 px above it.
  - Guardians are wider, not taller.
- **Enemy heights on the 256 canvas** (feet on row 236):

  | Size class | Height |
  |---|---|
  | small | 120–160 px |
  | medium | 160–190 px |
  | brute | 190–215 px, ≥ 200 px wide |

  Bosses: 400–450 px tall on the 512 canvas, feet on row 486.
- **Rotated sprites:** `Vfx/arrow`, `Vfx/fireball`, `Vfx/projectile_*` and `World/lane_arrow` are rotated by code. Draw them pointing **+X**, centred.
- **Tinted sprites:** `Vfx/ring`, `Vfx/telegraph`, `Vfx/glow`, `Vfx/spark`, `UI/bar_fill` and `World/node_*` are multiplied by a colour in code, so paint them in **white and neutral greys only**.
- **Ground decals:** `Vfx/field_*`, `Vfx/zone_*`, `Vfx/ring` and `Vfx/telegraph` are painted top-down as a circle, centred. The game squashes them to 0.62.
- **No ground shadow inside units:** `World/shadow` is drawn separately.
- **Defringe:** for every pixel with alpha < 32, set its RGB to the nearest opaque neighbour's RGB. This prevents colour halos.
- **9-slice borders:** use the `border` from INPUT_MANIFEST. Decoration stays inside the border; the centre must stretch cleanly. IMGUI uses 48 on all sides for card frames.
- **Text:** never paint letters or numbers into an asset.
- **Masters:** keep a 2× (or larger) master of every unit, portrait, icon, card and relic in `source/masters/`.
- **Quality target: 2560×1440 (2K).** A hero's 400 px canvas is shown at ~192 px tall on a 1440p screen, an enemy's 256 px canvas at ~154 px, and the boss canvas at ~384 px. Paint at ≥ 2× and judge the result in the 1440p preview.
  - Use crisp, deliberate brushwork with clear material separation: metal, cloth, skin, stone.
  - Avoid mushy edges.
  - Never upscale a smaller generation.
- **Value separation (measured at intake):** the 3 px edge band of every unit frame must average ≥ 0.27 luminance. Battlefields average ~0.16.
  - Achieve this with the shared back-right rim light (`#9fe8ff`, 2–3 px at export) and lit key planes.
  - Do not use a black or uniform outline.

## 5. Animation frames (the lead animates them in Unity)
The game swaps whole pose frames and adds procedural motion: bob, lunge, recoil, squash, flash and dissolve. Each frame is **one clear key pose**:

| Suffix | Pose |
|---|---|
| `_idle` / `_evoA` / `_evoB` | Neutral ready stance, weight centred. This is the identity frame |
| `_attack` / `_evoA_attack` / `_evoB_attack` | The **basic-attack strike moment**. Melee: the weapon at the end of its swing, extended toward +X. Ranged/caster: the release, with the arm, bow or staff extended toward +X |
| `_cast` / `_evoA_cast` / `_evoB_cast` | Skill casting: focus raised, element accent brightest, body lifted ~6% |
| `_downed` | Collapsed or kneeling, desaturated ~40%, still inside the canvas |
| Enemy `_a` / `_b` | Walk contact pose and passing pose. Silhouette IoU between them ≥ 0.6 |
| Enemy `_attack` | Strike pose |
| Boss `_tell` | The anticipation pose held during the ground telegraph: weapon raised high, the body coiled, a glow building on the weapon |
| Boss `_attack` | The impact pose |

**Unit frames contain the character only.**
- Never paint projectiles, beams, explosions or ground effects into a unit frame. VFX are separate sprites.
- A small emissive glow on the weapon or focus is allowed. It may extend at most 10% outside the body's bounding box.

**Identity across frames:**
- Generate the identity frame first.
- Generate every other frame of that character with the identity frame attached as the reference image. A sheet of several poses in one generation is also fine.
- Keep the face, costume, palette and prop identical.
- If drift happens, regenerate. Never ship a frame that reads as a different character.


**Pose and camera references:** `ArtHandoff/requests/pose_refs/<build>_<weapon>_<pose>.png`
- What they are: clay mannequins rendered by the lead in Blender at the exact game camera, on the 2× art canvas (800²). They have correct foot placement on the pivot row and figure height inside the icon box.
- Builds: `slim` for mage, ranger, support, healer, assassin and controller; `heavy` for guardian and bruiser.
- Weapons: `staff`, `sword`, `hammer`, `shield`.
- Poses: `idle`, `attack`, `cast`.
- How to use: attach the closest one to every image generation as a pose/camera reference. Match the view, scale and ground contact; the costume and identity follow the hero design.

**Evolutions** keep the identity of the hero and change at least three of:
- the silhouette outline;
- the costume tier;
- the weapon silhouette;
- the element motif on the body.

## 6. Method
1. Read the batch file, `INPUT_MANIFEST.json`, the guides in `references/guides/`, and the content data it cites (`Assets/_Aetherward/Resources/Content/*.json`, read only).
2. Per character:
   - identity frame;
   - the other frames, using the identity frame as reference;
   - utility cleanup in Python: alpha, defringe, uniform scale, foot alignment, centring. **Never redraw anatomy with code.**
3. Use image generation at ≥ 2× size, then downscale with Lanczos.
4. Self-QA, with the commands run from the repo root:
   ```
   python Tools\ArtPipeline\handoff.py preview --batch <batch> --overlay ArtHandoff\returns\<batch>\exports\Art --out ArtHandoff\returns\<batch>\previews --tag <batch>
   python Tools\ArtPipeline\handoff.py intake  --batch <batch> --stage-dir ArtHandoff\returns\<batch>\_work\stage --qa-dir ArtHandoff\returns\<batch>\qa
   ```
   `preview` is an offline composite. Label it as such; it is not a game screenshot. `intake` must report **0 blocking problems**.
5. Look at the silhouette and grayscale sheets at 720p. If a character does not read as its role at that size, simplify the inner detail and strengthen the rim light, then regenerate.

## 7. Scope and rights
- Write only inside `ArtHandoff\returns\<batch>\`.
- Do not touch `Assets/`, `Tools/`, `ProjectSettings/`, `.meta` files or content JSON.
- No git state changes.
- Do not change gameplay, data or code. If an asset needs a code change, write it in the README; the lead decides.
- **Licensing:**
  - Use only your own generations, your own Blender work and the repo's own files.
  - CC0 inputs only if they are recorded with a URL.
  - No "in the style of <artist or game>".
  - No copying of existing characters.

## 8. Return layout
```
ArtHandoff/returns/<batch>/
  DELIVERABLE_MANIFEST.json      (template: ArtHandoff/requests/B01/DELIVERABLE_MANIFEST.template.json)
  README.md                      method, prompts, drift notes, known issues, blockers
  exports/Art/<Category>/<name>.png
  source/{masters,sheets,blender,scripts,battlefield/layers}/
  previews/  qa/  _work/
```

## 9. Definition of done
1. Every requested asset is exported to the contract, or listed as `blocked`/`skipped` with a concrete reason.
2. Intake reports 0 blocking problems, and its JSON is in `qa/`.
3. The manifest traces every export to its source, generator, prompt and cleanup script.
4. Previews are in `previews/` at 1080p and 720p, with the silhouette and grayscale sheets.
5. The README is honest, including which assets you think are below the bar. Never claim approval.
6. Nothing outside `returns/<batch>/` changed.

## 10. Blockers
- If a tool fails, mark the item `blocked` with the exact error and continue with the rest.
- Never replace painterly art with code-drawn stand-ins presented as final. A labelled `placeholder` is allowed.
- The last message of your run must contain:
  - delivered / blocked counts;
  - the intake result;
  - the top three risks.
