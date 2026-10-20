# Implementation plan (executed in this order)

| Step | Scope | Gate before next step |
|---|---|---|
| 1 | Art Quality Validator + broken-fixture self-tests + CI job | validator catches every planted defect |
| 2 | `ap.py` pipeline (generate/render/validate/preview/pack/diff/import/rollback/lock) | regenerate = 0 diffs (idempotent); rollback restores byte-identical |
| 3 | Fix blocking art (headroom frames, downed placement, enemy fit) + evolution kits | staging 0 blocking, 0 weak evolutions; before/after sheets |
| 4 | Blender 3D→2D benchmark (Crystal) | ACCEPT/REWORK decision with evidence |
| 5 | P1 Synergy Vision → P2 Training Chamber → P4 boss audit → P5 Discovery Codex → P6 Battle Insights | each with tests, UnityCheck 0 errors |
| 6 | P9 balance lab + anomaly detectors; fix only evidence-backed issues with paired A/B | regression tests for counterexamples |
| 7 | Docs, final Vietnamese report | — |

Scope revisions (recorded, not silent):
- 4/8-direction sprite sheets: not produced — the game uses one mirrored facing (see ART_BIBLE §7).
- URP 2D lights / Shader Graph: not enabled — built-in renderer project, no editor to verify cost.
- Unity SpriteAtlas assets: planned only (`Reports/ArtQuality/atlas_plan.md`); creating them needs the editor.
- P7 (feel/audio polish): milestone toasts + telegraph assist; effects-intensity preset, phased cast/hit poses, hitstop, priority voice allocation + ducking, 4 new SFX (logic unit tested; on-screen feel needs a Unity review).
