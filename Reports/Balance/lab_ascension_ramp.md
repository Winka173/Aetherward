# A/B — Ascension early ramp + Auto Arrange lane fix (balance lab, paired seeds)

Command: `dotnet run --project Tools/SimHarness/Balance -c Release -- --lab --seeds 30` (7 bots × 6 biomes × A0/A5/A10 × 30 seeds = 3780 runs per arm).

## 1. Auto Arrange: cover a lane left empty (Reports/Balance/lab_before_autoarrange_fix → lab)
Found by Battle Insights on seed 5000 ("100% of the Crystal damage came through the West lane, 0% in reach"). Wave 2 attacks East + West and both starters stood East.

| Bot (A0) | Before | Even split (rejected) | Minimal fix (kept) |
|---|---|---|---|
| tank_healer_stall | 6.1% | 12.2% | **22.8%** |
| area_control | 19.4% | 5.0% | **23.9%** |
| reaction_chain | 21.7% | 7.2% | 21.7% |
| naive_random | 24.4% | 10.6% | 24.4% |
| mono_element | 11.7% | 2.2% | 10.0% |

Spreading every hero evenly lowered clear rates, so the fix only moves the longest-reach hero to a lane that carries ≥25% of the wave and has nobody in reach. This function is also the player's "Auto arrange" button.

## 2. Ascension early ramp (difficulty.json: earlyRampStart 0.35 → 100% at wave 7)
| | Before | After |
|---|---|---|
| A10: runs dead by wave 2 | 843 / 1260 | 336 / 1260 |
| A10: median wave reached | 2 | 4 |
| A5: runs dead by wave 2 | 9 / 1260 | 4 / 1260 |
| A0: any change | — | none (ramp only scales the Ascension bonus) |

**Still open (not fixed):** every bot clears **0%** at A5 and A10. A5 runs mostly end at waves 6–9. We did not retune this: the brief forbids large nerfs without regression review. Bots are also weaker than players, so it needs human playtests and a design decision on the intended A5/A10 clear rate.
