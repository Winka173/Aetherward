# Batch balance report (headless, authoritative simulation)

> AutoPilot policies are **bots, not players**: rates describe scripted/heuristic drafting, not human win rates.

- Runs: **3600** (150 seeds × 12 starting lineups × 2 policies), mode Classic, Ascension 0, biome default
- Wall clock: 177.0s on 4 threads (Intel(R) Xeon(R) Processor @ 2.10GHz), .NET 8.0.31
- Content hash: `292ebec7f47819b3` · Unity editor not involved (pure C# simulation shared with the game)
- Invariants (finished, no NaN, gold ≥ 0, exactly one outcome): **all passed**; stuck runs: 0

## Win rate by policy (95% Wilson CI)
| Policy | Runs | Win rate | Avg wave |
|---|---|---|---|
| greedy | 1800 | 13.8% [12.3–15.4] | 15.4 |
| scripted | 1800 | 16.8% [15.2–18.6] | 15.8 |

## Win rate by starting lineup × policy
| Lineup | scripted | greedy |
|---|---|---|
| arcane_void | 0.0% [0.0–2.5] | 0.0% [0.0–2.5] |
| balanced | 32.7% [25.7–40.5] | 17.3% [12.1–24.2] |
| eclipse | 7.3% [4.1–12.7] | 8.0% [4.6–13.5] |
| engineers | 4.0% [1.8–8.5] | 6.0% [3.2–11.0] |
| frozen_fortress | 28.7% [22.0–36.4] | 12.0% [7.7–18.2] |
| glass_cannon | 10.0% [6.2–15.8] | 15.3% [10.4–22.0] |
| magma_engine | 34.7% [27.5–42.6] | 18.7% [13.2–25.7] |
| mixed_burst | 28.7% [22.0–36.4] | 42.0% [34.4–50.0] |
| phoenix_gale | 14.0% [9.3–20.5] | 7.3% [4.1–12.7] |
| thorn_doctor | 0.0% [0.0–2.5] | 5.3% [2.7–10.2] |
| thunderstorm | 38.7% [31.2–46.7] | 32.7% [25.7–40.5] |
| verdant_plague | 3.3% [1.4–7.6] | 0.7% [0.1–3.7] |

## Failure waves (share of all defeats)
| Wave | Defeats | Share | Top killers |
|---|---|---|---|
| 14 | 617 | 20.2% | sapper 445, shieldbearer 77, runner 27 |
| 18 | 590 | 19.4% | sapper 481, juggernaut 47, hexcaster 37 |
| 17 | 358 | 11.7% | mimic 197, siege_colossus 96, warded 43 |
| 19 | 333 | 10.9% | mimic 72, shieldbearer 69, hexcaster 66 |
| 9 | 300 | 9.8% | warded 212, grunt 79, void_priest 9 |
| 12 | 213 | 7.0% | shieldbearer 133, hexcaster 35, hex_binder 18 |
| 15 | 143 | 4.7% | juggernaut 62, ravager 37, grunt 19 |
| 10 | 123 | 4.0% | ignaroth 44, thornmother 33, ashen_matriarch 19 |

## Outlier flags (automatic; investigate, do not auto-nerf)
Rules: *must-pick candidate* = owned in ≥5% of runs and its win-rate CI lies entirely above the without-CI by ≥10 pp; *never viable* = in ≥30 runs with 0 wins; *spike* = one wave causes >25% of defeats. Presence correlates with drafting skill and run length (relics picked late appear in longer runs) — treat as leads, not verdicts.

- must-pick candidate (hero): ignis — 23.0% [20.9–25.3] with vs 10.2% [9.0–11.6] without
- must-pick candidate (hero): marina — 30.5% [27.9–33.2] with vs 8.2% [7.2–9.4] without
- must-pick candidate (hero): zephyr — 26.6% [23.0–30.6] with vs 13.4% [12.2–14.6] without
- must-pick candidate (hero): nerissa — 24.2% [20.5–28.3] with vs 14.0% [12.9–15.3] without
- must-pick candidate (relic): mana_battery — 27.4% [22.5–33.0] with vs 14.3% [13.1–15.5] without
- must-pick candidate (relic): stoneheart — 27.4% [22.9–32.4] with vs 14.1% [12.9–15.3] without
- must-pick candidate (relic): overgrowth — 25.1% [20.8–29.9] with vs 14.3% [13.1–15.5] without
- must-pick candidate (relic): eternal_ember — 24.7% [20.1–29.8] with vs 14.5% [13.3–15.7] without
- must-pick candidate (relic): crystal_growth — 28.1% [22.1–35.0] with vs 14.6% [13.5–15.8] without
- must-pick candidate (relic): spark_of_genesis — 25.6% [20.6–31.2] with vs 14.5% [13.4–15.7] without
- must-pick candidate (relic): sanctuary_bell — 37.3% [30.9–44.2] with vs 14.0% [12.9–15.2] without
- must-pick candidate (relic): overclock_coil — 23.8% [20.9–27.1] with vs 13.1% [11.9–14.4] without
- must-pick candidate (relic): zephyr_sash — 28.3% [23.7–33.4] with vs 14.0% [12.8–15.2] without
- must-pick candidate (relic): kite_banner — 26.5% [22.1–31.4] with vs 14.1% [13.0–15.4] without
- must-pick candidate (relic): ember_codex — 27.3% [24.3–30.4] with vs 11.8% [10.6–13.0] without
- must-pick candidate (relic): tidal_engine — 30.6% [27.1–34.3] with vs 12.1% [11.0–13.3] without
- must-pick candidate (relic): ember_testament — 32.1% [28.9–35.5] with vs 10.7% [9.6–11.9] without
- must-pick candidate (relic): ocean_heart — 44.8% [40.9–48.8] with vs 9.4% [8.4–10.5] without
