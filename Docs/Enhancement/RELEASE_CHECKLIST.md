# Release Checklist

Legend: ✅ done, with evidence in this repo · ⏳ needs Unity, a device or a person · ❌ not done

## Automated (run in this environment)
- ✅ `dotnet test Tools/SimHarness/Tests`: 191/191 EditMode tests (compiled with .NET 8)
- ✅ `dotnet build Tools/SimHarness/UnityCheck`: 0 errors when type-checking the Unity scripts against reference DLLs
- ✅ `--validate`: 0 errors, 2 warnings (wind/earth have only 1 relic each) → `Reports/ContentValidation/`
- ✅ `--batch`: invariants (run ends, no NaN, gold ≥ 0, exactly one outcome) hold across 48,000 runs → `Reports/Balance/`
- ✅ Determinism: same seed gives the same tick hash; a batch run twice gives byte-identical `runs.csv`
- ✅ Old saves: the MVP fixture (`mvp_0dde0cd`) loads and plays to the end; the backup chain and quarantine work
- ✅ Headless soak of 40 Endless waves: retained memory stable at ~1.5 MB, no unbounded growth → `Reports/Performance/headless_soak.md`

## Needs Unity / devices (not done — unverified)
- ⏳ Open the project in Unity 6000.4.8f1: import with no errors or missing references
- ⏳ Play each screen: tactic picker, shop lock, Crystal Evolution, results "Copy build", the 3 new settings
- ⏳ Check by eye: damage-number merging, flash intensity, AI inspector in the debug overlay
- ⏳ Profiling on target devices: FPS, GC spikes, draw calls (only headless numbers exist so far)
- ⏳ Platform builds (Android/iOS/Standalone) with `Tools/Build` scripts
- ⏳ Focus loss / app pause on mobile → auto pause + save
- ⏳ Run CI `.github/workflows/simulation.yml` on GitHub for the first time

## Needs people (not done)
- ⏳ Real playtests: the win rates in the reports come from bots, not players
- ⏳ Accessibility review (photosensitivity, colour contrast) by a real user
- ⏳ Proofread the EN/VI localization in game context

## Before tagging
- ⏳ Update the version in ProjectSettings / `Docs/CHANGELOG.md`
- ⏳ Decide the default for the `FeatureFlags` (see the A/B result in `FINAL_IMPLEMENTATION_REPORT.md`)
