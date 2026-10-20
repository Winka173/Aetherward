# Enhancement changelog (Final Quality / Art / Balance prompt)

- Art Quality Validator (`Tools/ArtPipeline/validate.py`) with waivers, CI job, 8 self-tests.
- Art pipeline CLI `ap.py`: generate, render (Blender), validate, preview (720p/1080p, battlefields, spell density, CVD), pack (atlas plan), diff (before/after), import (transactional), rollback, lock.
- Regenerated 258 sprites: 400² hero frames with headroom (no cropped props), grounded downed poses, 3 enemy fits, evolution kits for 22 weak branches; `gen_meta --refresh-textures` keeps GUIDs while updating pivots; `Ui.HeroIcon` keeps UI framing.
- Blender crystal benchmark (REWORK, 2D stays default).
- P1 Synergy Vision overlay; P2 Training Chamber; P4 boss telegraph audit + assist + non-spoiler preview; P5 Discovery Codex + milestone toasts + journal; P6 Battle Insights.
- P9 balance lab; Auto Arrange lane fix; Ascension early ramp (data); counterexample tests.
- Fix: enemy delayed strikes now report their source uid.
