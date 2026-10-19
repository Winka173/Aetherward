# Architecture delta — Gameplay Operations Enhancement

The architecture is unchanged: a pure C# simulation (netstandard2.1, fixed 1/30 s tick, PCG32 streams), with the Unity layer only presenting it (IMGUI, built-in renderer). Every addition below lives on the side it belongs to.

## Simulation (`Assets/_Aetherward/Scripts/Simulation`)
| Area | New / changed | Notes |
|---|---|---|
| Combat AI | `Combat/Battle.TargetAI.cs`: `TeamTactic`, `TargetDecision`, `SelectTargetUtility` | 7 normalized components × weights (role + tactic). Hysteresis 0.15. Tie-break by uid. Only considers enemies in range. `BattleSetup.UtilityTargeting` is the flag. |
| Combat AI | `Battle.Heroes.cs`: `ProfileScore` split out of `SelectTarget` | The legacy profile is kept as one of the components. |
| Crystal | `Combat/Battle.CrystalPath.cs`: `CrystalPaths` (bastion/pulse/thorn) | Values are constants shared by sim/UI/test. Pulse emits a `Strike` event with id `crystal_pulse`. |
| Provenance | `BattleStats.DamageByKind[6]`, `HeroShieldAbsorbed`, `MaxProcDepth`; `RunState.CrystalDamageByEnemy` | Each hit is counted once per `DamageKind`. |
| Concurrency | `HitSetPool` is `[ThreadStatic]` | Lets the batch run in parallel. Determinism unchanged (each run is still single-threaded). |
| Run | `RunController`: `ToggleLock/IsLocked`, `ShareCode()`, `RewardKind.CrystalEvolution`, `OfferKind.CrystalPath` | The shop lock survives rerolls and carries into the next shop at its old price. |
| Run | `DraftGenerator`: "strategic alternative" slot | A draft of 3 cards always has at least 1 non-synergy card. |
| Run | `AutoPilot`: `DraftPolicy {Scripted, Random, Synergy, Greedy}`, `Step()` | `Step()` lets tests and the soak run step by step. |
| Run | `RunResults`: MostDamagingThreat, ClosestSave, DecisiveUpgrade, ShareCode, MenuSeconds | The results screen reads these instead of inferring anything. |
| Run | `EncounterReport` / `EncounterEntry` | Wave budgets use the same scaling formula as `Battle`. |
| Run | `FeatureFlags` (CrystalEvolution, UtilityTargeting) | Each run copies the flag into `RunState` (and the save). |
| Presentation (pure) | `Presentation/DamageNumberMerger` | Merges damage numbers on the same target within 0.3 s; crits get their own number. |
| Save | `SaveSystem`: `.bak` → `.bak2` rotation, `.corrupt` quarantine; new fields (tactic, lock, crystalPath, crystalEvo, breakdown, settings flash/focusPause/battery) | Old saves load with defaults. MVP fixture `mvp_0dde0cd`. |

## Unity (`Assets/_Aetherward/Scripts/Unity`)
- `Services.cs`: writes go through a temp file, then `File.Replace` (atomic). `ApplySettings` caps FPS in battery-saver mode and sets `WorldGfx.FlashScale`.
- `BattleController`: tactic picker, shop lock button, bond banner, Crystal Evolution screen (`DrawCrystalPaths`), damage-number merging, `OnApplicationFocus` → auto pause, `MenuSeconds`.
- `DebugOverlay`: AI inspector (components / runner-up / hysteresis) when ShowRanges is on.
- `ResultsController`: turning-points line and a "Copy build" button (`ShareCode`).
- `SharedPanels`: settings for flash intensity, pause when unfocused, battery saver.

## Tools
- `Tools/SimHarness/Balance`: `--batch` (Wilson CI, CSV, content hash, invariants), `--validate`, `--breakdown`, `--encounters`, `--soak`, and the A/B flags `--no-crystal-evo` / `--legacy-targeting`.
- `.github/workflows/simulation.yml`: test + validate + a 25-seed batch. **It has never been run on GitHub.**

## Not changed
Scenes, the render pipeline, the input system, the asmdef layout, and the content JSON format (only optional fields were added).
