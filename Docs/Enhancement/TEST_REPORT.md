# Test report

| Suite | Command | Result |
|---|---|---|
| C# EditMode (compiled with .NET 8) | `dotnet test Tools/SimHarness/Tests` | **PASS 221/221** |
| Unity scripts type-check | `dotnet build Tools/SimHarness/UnityCheck` | **PASS 0 errors** |
| Art validator self-tests (broken fixtures) | `python3 -m unittest discover -s Tools/ArtPipeline/tests` | **PASS 8/8** |
| Art Quality Validator (live) | `python3 Tools/ArtPipeline/validate.py` | **PASS 0 blocking**, 206 warnings |
| Content validation | `dotnet run --project Tools/SimHarness/Balance -c Release -- --validate` | PASS 0 errors, 2 warnings |
| Unity PlayMode / scene load / builds | — | **NOT RUN** (no Unity) |
| CI workflow (`.github/workflows/simulation.yml`) | — | **NOT RUN** on GitHub |

## Minimum validation scenarios
| # | Scenario | Test | Status |
|---|---|---|---|
| 1 | Placements → predictably different coverage, one seed | `SynergyVisionTests.SixHeroPlacements…` | PASS |
| 2 | Water+Lightning+Wind reactions counted once | `SynergyVisionTests.WaterLightningWind…` | PASS (visual readability NOT VERIFIED) |
| 3 | Every evolution branch differs mechanically and visually | content rule (mechanical) + validator `weak_evolution` = 0 | PASS (numeric); human review PENDING |
| 4 | Training reproducible, no rewards, saves untouched | `TrainingChamberTests` | PASS |
| 5 | Boss telegraphs precede harm, also at 2×; assist works | `BossTelegraphTests` (12 bosses, min lead 1.17 s) | PASS (on-screen contrast NOT VERIFIED) |
| 6 | Codex survives content additions + migration | `DiscoveryCodexTests` | PASS |
| 7 | Smart draft with 150+ upgrades: no impossible cards, off-build options | `DraftFairnessTests` + lab: 0/15053 thin drafts | PASS |
| 8 | Loss explanation from logged threats; replay agrees | `BattleInsightsTests` | PASS |

## Thresholds tuned on the current set (proposals)
`art_spec.json` thresholds were set once against the baseline and are unchanged afterwards; the weak-evolution rule gained a value-distance term (still flags all 22 baseline branches).
