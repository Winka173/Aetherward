# Batch balance report (headless, authoritative simulation)

> AutoPilot policies are **bots, not players**: rates describe scripted/heuristic drafting, not human win rates.

- Runs: **24000** (500 seeds × 12 starting lineups × 4 policies), mode Classic, Ascension 0, biome default
- Wall clock: 557.4s on 4 threads (Intel(R) Xeon(R) Processor @ 2.10GHz), .NET 8.0.31
- Content hash: `292ebec7f47819b3` · Unity editor not involved (pure C# simulation shared with the game)
- Invariants (finished, no NaN, gold ≥ 0, exactly one outcome): **all passed**; stuck runs: 0

## Win rate by policy (95% Wilson CI)
| Policy | Runs | Win rate | Avg wave |
|---|---|---|---|
| greedy | 6000 | 10.8% [10.1–11.6] | 14.7 |
| random | 6000 | 9.2% [8.5–10.0] | 14.8 |
| scripted | 6000 | 10.9% [10.1–11.7] | 15.0 |
| synergy | 6000 | 6.9% [6.3–7.6] | 14.3 |

## Win rate by starting lineup × policy
| Lineup | scripted | synergy | random | greedy |
|---|---|---|---|---|
| arcane_void | 0.0% [0.0–0.8] | 0.0% [0.0–0.8] | 0.4% [0.1–1.4] | 0.6% [0.2–1.7] |
| balanced | 22.8% [19.3–26.7] | 11.2% [8.7–14.3] | 10.8% [8.4–13.8] | 16.0% [13.0–19.5] |
| eclipse | 3.2% [2.0–5.1] | 1.2% [0.6–2.6] | 4.0% [2.6–6.1] | 4.2% [2.8–6.3] |
| engineers | 3.4% [2.1–5.4] | 3.6% [2.3–5.6] | 3.8% [2.4–5.9] | 4.0% [2.6–6.1] |
| frozen_fortress | 21.2% [17.8–25.0] | 8.2% [6.1–10.9] | 10.0% [7.7–12.9] | 7.0% [5.1–9.6] |
| glass_cannon | 9.2% [7.0–12.1] | 11.0% [8.5–14.0] | 12.0% [9.4–15.1] | 16.0% [13.0–19.5] |
| magma_engine | 21.8% [18.4–25.6] | 6.2% [4.4–8.7] | 12.8% [10.2–16.0] | 11.8% [9.3–14.9] |
| mixed_burst | 14.0% [11.2–17.3] | 23.8% [20.3–27.7] | 28.8% [25.0–32.9] | 33.2% [29.2–37.4] |
| phoenix_gale | 7.0% [5.1–9.6] | 4.2% [2.8–6.3] | 4.4% [2.9–6.6] | 4.8% [3.2–7.0] |
| thorn_doctor | 0.0% [0.0–0.8] | 0.6% [0.2–1.7] | 0.8% [0.3–2.0] | 2.2% [1.2–3.9] |
| thunderstorm | 27.0% [23.3–31.1] | 12.0% [9.4–15.1] | 22.2% [18.8–26.0] | 29.2% [25.4–33.3] |
| verdant_plague | 1.0% [0.4–2.3] | 0.6% [0.2–1.7] | 1.0% [0.4–2.3] | 0.8% [0.3–2.0] |

## Failure waves (share of all defeats)
| Wave | Defeats | Share | Top killers |
|---|---|---|---|
| 14 | 5080 | 23.4% | sapper 4056, shieldbearer 476, runner 220 |
| 18 | 3896 | 17.9% | sapper 3407, juggernaut 168, hexcaster 148 |
| 9 | 2901 | 13.4% | warded 2083, grunt 706, void_priest 112 |
| 17 | 1961 | 9.0% | mimic 946, siege_colossus 688, warded 212 |
| 12 | 1811 | 8.3% | shieldbearer 1185, hexcaster 270, mirror_knight 128 |
| 19 | 1404 | 6.5% | shieldbearer 280, mimic 264, storm_harpy 263 |
| 13 | 1116 | 5.1% | sapper 1020, juggernaut 29, grunt 27 |
| 15 | 738 | 3.4% | juggernaut 322, ravager 220, grunt 83 |

## Outlier flags (automatic; investigate, do not auto-nerf)
Rules: *must-pick candidate* = owned in ≥5% of runs and its win-rate CI lies entirely above the without-CI by ≥10 pp; *never viable* = in ≥30 runs with 0 wins; *spike* = one wave causes >25% of defeats. Presence correlates with drafting skill and run length (relics picked late appear in longer runs) — treat as leads, not verdicts.

- must-pick candidate (hero): marina — 18.8% [18.0–19.8] with vs 5.2% [4.9–5.6] without
- must-pick candidate (relic): mana_battery — 22.2% [20.3–24.3] with vs 8.5% [8.1–8.9] without
- must-pick candidate (relic): overgrowth — 19.7% [18.1–21.5] with vs 8.4% [8.1–8.8] without
- must-pick candidate (relic): sanctuary_bell — 26.9% [24.7–29.3] with vs 8.3% [8.0–8.7] without
- must-pick candidate (relic): ember_codex — 18.0% [16.9–19.1] with vs 7.3% [6.9–7.6] without
- must-pick candidate (relic): tidal_engine — 20.2% [19.0–21.5] with vs 7.3% [7.0–7.7] without
- must-pick candidate (relic): ember_testament — 23.4% [22.1–24.7] with vs 6.4% [6.1–6.8] without
- must-pick candidate (relic): ocean_heart — 30.3% [28.8–31.9] with vs 5.9% [5.6–6.3] without
