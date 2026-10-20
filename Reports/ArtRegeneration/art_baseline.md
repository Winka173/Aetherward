# Art baseline (real state, audited)

- Runtime sprites: **795** PNGs under `Assets/_Aetherward/Resources/Art`; loaded through `Resources.Load` by path (`Art.Tex/Art.Sprite`). Scenes/prefabs found: 4 (Battle.unity, Boot.unity, MainMenu.unity, Results.unity); GUIDs they reference: 2 (art GUIDs among them: 0). No Animator controllers, AnimationClips, SpriteAtlases or Addressables exist; frames are animated procedurally in `UnitView`.
- Provenance: 795 / 795 assets map to a generator script in the manifest (reproducible); non-reproducible: 0.
- Baseline commit `f19ac35` (before the new pipeline): 300 assets differ from it today (re-generated and imported through `ap.py import`); the rest are byte-identical to what the pipeline produces (`ap.py generate` + `ap.py diff` → 0 changes).
- Unreferenced by code/content (orphan candidates, reviewed manually before any removal): 1: UI/vignette

| Category | Assets | Changed since baseline |
|---|---|---|
| Cards | 80 | 39 |
| Enemies | 104 | 6 |
| Heroes | 252 | 252 |
| Icons | 122 | 3 |
| Portraits | 36 | 0 |
| Relics | 81 | 0 |
| UI | 30 | 0 |
| Vfx | 76 | 0 |
| World | 14 | 0 |

Baseline quality (validator at the baseline commit): `Reports/ArtQuality/baseline/summary.md` — 62 blocking, 22 weak evolutions.
Unity import/compile, scene screenshots, FPS/memory: **NOT RUN** (no Unity editor; see toolchain_capabilities.md).
