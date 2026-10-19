# Batch balance report (headless, authoritative simulation)

> AutoPilot policies are **bots, not players**: rates describe scripted/heuristic drafting, not human win rates.

- Runs: **24000** (500 seeds × 12 starting lineups × 4 policies), mode Classic, Ascension 0, biome default
- Wall clock: 426.2s on 4 threads (Intel(R) Xeon(R) Processor @ 2.10GHz), .NET 8.0.31
- Content hash: `292ebec7f47819b3` · Unity editor not involved (pure C# simulation shared with the game)
- Invariants (finished, no NaN, gold ≥ 0, exactly one outcome): **all passed**; stuck runs: 0

## Win rate by policy (95% Wilson CI)
| Policy | Runs | Win rate | Avg wave |
|---|---|---|---|
| greedy | 6000 | 9.3% [8.6–10.0] | 14.5 |
| random | 6000 | 8.1% [7.4–8.8] | 14.6 |
| scripted | 6000 | 9.4% [8.7–10.2] | 14.7 |
| synergy | 6000 | 6.2% [5.7–6.9] | 14.1 |

## Win rate by starting lineup × policy
| Lineup | scripted | synergy | random | greedy |
|---|---|---|---|---|
| arcane_void | 0.0% [0.0–0.8] | 0.0% [0.0–0.8] | 0.6% [0.2–1.7] | 0.2% [0.0–1.1] |
| balanced | 20.6% [17.3–24.4] | 10.2% [7.8–13.2] | 9.6% [7.3–12.5] | 14.6% [11.8–18.0] |
| eclipse | 2.2% [1.2–3.9] | 1.4% [0.7–2.9] | 3.2% [2.0–5.1] | 5.0% [3.4–7.3] |
| engineers | 2.2% [1.2–3.9] | 3.2% [2.0–5.1] | 3.4% [2.1–5.4] | 3.4% [2.1–5.4] |
| frozen_fortress | 21.6% [18.2–25.4] | 9.4% [7.1–12.3] | 8.6% [6.4–11.4] | 9.2% [7.0–12.1] |
| glass_cannon | 6.4% [4.6–8.9] | 10.4% [8.0–13.4] | 11.8% [9.3–14.9] | 12.2% [9.6–15.4] |
| magma_engine | 18.0% [14.9–21.6] | 6.8% [4.9–9.4] | 10.2% [7.8–13.2] | 9.2% [7.0–12.1] |
| mixed_burst | 9.6% [7.3–12.5] | 18.8% [15.6–22.5] | 27.0% [23.3–31.1] | 28.2% [24.4–32.3] |
| phoenix_gale | 8.6% [6.4–11.4] | 3.2% [2.0–5.1] | 3.6% [2.3–5.6] | 3.6% [2.3–5.6] |
| thorn_doctor | 0.0% [0.0–0.8] | 1.0% [0.4–2.3] | 0.6% [0.2–1.7] | 1.4% [0.7–2.9] |
| thunderstorm | 23.4% [19.9–27.3] | 10.6% [8.2–13.6] | 17.6% [14.5–21.2] | 23.4% [19.9–27.3] |
| verdant_plague | 0.6% [0.2–1.7] | 0.0% [0.0–0.8] | 0.6% [0.2–1.7] | 0.8% [0.3–2.0] |

## Failure waves (share of all defeats)
| Wave | Defeats | Share | Top killers |
|---|---|---|---|
| 14 | 5343 | 24.3% | sapper 4406, shieldbearer 413, runner 240 |
| 18 | 3962 | 18.0% | sapper 3605, juggernaut 132, hexcaster 99 |
| 9 | 2872 | 13.0% | warded 2031, grunt 727, void_priest 114 |
| 12 | 1970 | 8.9% | shieldbearer 1187, hexcaster 317, mirror_knight 157 |
| 17 | 1835 | 8.3% | mimic 909, siege_colossus 592, warded 205 |
| 13 | 1591 | 7.2% | sapper 1491, flame_devourer 32, grunt 28 |
| 19 | 1011 | 4.6% | mimic 229, shieldbearer 216, hexcaster 200 |
| 10 | 772 | 3.5% | ignaroth 275, ashen_matriarch 175, thornmother 170 |

## Outlier flags (automatic; investigate, do not auto-nerf)
Rules: *must-pick candidate* = owned in ≥5% of runs and its win-rate CI lies entirely above the without-CI by ≥10 pp; *never viable* = in ≥30 runs with 0 wins; *spike* = one wave causes >25% of defeats. Presence correlates with drafting skill and run length (relics picked late appear in longer runs) — treat as leads, not verdicts.

- must-pick candidate (hero): marina — 16.1% [15.3–17.0] with vs 4.7% [4.4–5.1] without
- must-pick candidate (relic): mana_battery — 20.5% [18.6–22.5] with vs 7.4% [7.0–7.7] without
- must-pick candidate (relic): sanctuary_bell — 25.0% [22.8–27.3] with vs 7.2% [6.9–7.5] without
- must-pick candidate (relic): tidal_engine — 18.1% [16.9–19.4] with vs 6.4% [6.0–6.7] without
- must-pick candidate (relic): ember_testament — 20.4% [19.2–21.6] with vs 5.7% [5.4–6.0] without
- must-pick candidate (relic): ocean_heart — 27.6% [26.1–29.1] with vs 5.2% [4.9–5.5] without
