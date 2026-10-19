# Phase reports (1–13): summary

Status:
- **Done** — has code and tests/evidence.
- **Partial** — some of it done, the rest is listed.
- **Blocked** — needs Unity, a device or a person; nothing was faked.

Unity 6000.4.8f1 was never opened in this environment. Everything on the Unity side has only been type-checked (UnityCheck), never run.

| # | Phase | Status | Done (evidence) | Not done / blocked |
|---|---|---|---|---|
| 1 | Combat feel / juice | Partial | Damage-number merging (`DamageNumberMerger`, tests), global flash scale, Crystal Pulse event | New VFX/SFX not checked by eye; hit-stop/camera not retuned |
| 2 | Smart hero AI + inspector | Done (sim), Partial (UI) | Utility targeting + 5 tactics + hysteresis + `TargetDecision` (TargetAITests); A/B batch | Inspector in the debug overlay not seen on screen |
| 3 | Build transformation & upgrade UX | Partial | Bond banner, "decisive upgrade" on the results screen | No new evolution-preview screen |
| 4 | Smart draft, shop, fair RNG | Done | Shop lock, strategic-alternative slot, escalating reroll, offer log tied to the seed (DraftFairnessTests) | — |
| 5 | Formation & Crystal decisions | Partial | Crystal Evolution: 3 exclusive paths, feature flag (CrystalEvolutionTests) | Emergency Swap and formation slots not built |
| 6 | Wave pacing & encounters | Partial | `EncounterReport`, `--encounters` (spike/dip flags), budget tests | No dynamic director (waves stay authored + scaled) |
| 7 | Clarity, UI/UX, accessibility | Partial | Flash intensity, pause when unfocused, battery saver, settings persistence (tests) | No colour-blind/contrast audit by a real person |
| 8 | Run breakdown, replay, share | Done | Provenance by `DamageKind`, turning points, `ShareCode`, `--breakdown` (RunBreakdownTests) | Share code is text only (no image) |
| 9 | Content authoring tools | Partial | `--validate` (ContentValidator + warnings), CI workflow | No Unity Editor window (needs Unity to verify) |
| 10 | Headless balance simulator | Done | `--batch` (4 policies, Wilson CI, CSV, content hash, parallel, byte-identical rerun) | — |
| 11 | Unity performance & stability | Blocked (partial) | Headless soak (`Reports/Performance/headless_soak.md`): ~0.02 ms/tick, retained memory stable | Unity profiler, FPS, draw calls, devices, builds |
| 12 | Save, update, release ops | Done (sim) | 2-level backup, quarantine, `File.Replace`, MVP fixture, feature flags in the save, release checklist | Crash mid-write not tested on a real device |
| 13 | Player feedback | Partial | Optional local feedback (5 stars + reason chips) in the meta save | **No real playtests** — no feedback has been collected |

## Gates
- **A (Foundation):** passed — audit, baseline, tests, save fixture.
- **B (Feel):** passes on the AI/tests side; on the "readable VFX/SFX" side it is **not checked** (no Unity).
- **C (Roguelike choices):** fair draft/shop measured; formation impact not measured (no formation).
- **D (Operations):** passed — seeded sim, validator, breakdown, save tests, headless profiling harness.
- **E (Release candidate):** **not passed** — no playtests, builds or device profiling.
