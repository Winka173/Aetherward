# Batch balance report (headless, authoritative simulation)

> AutoPilot policies are **bots, not players**: rates describe scripted/heuristic drafting, not human win rates.

- Runs: **3600** (150 seeds × 12 starting lineups × 2 policies), mode Classic, Ascension 0, biome default
- Wall clock: 169.3s on 4 threads (Intel(R) Xeon(R) Processor @ 2.10GHz), .NET 8.0.31
- Content hash: `292ebec7f47819b3` · Unity editor not involved (pure C# simulation shared with the game)
- Invariants (finished, no NaN, gold ≥ 0, exactly one outcome): **all passed**; stuck runs: 0

## Win rate by policy (95% Wilson CI)
| Policy | Runs | Win rate | Avg wave |
|---|---|---|---|
| greedy | 1800 | 12.4% [11.0–14.0] | 15.6 |
| scripted | 1800 | 15.1% [13.5–16.8] | 15.8 |

## Win rate by starting lineup × policy
| Lineup | scripted | greedy |
|---|---|---|
| arcane_void | 0.0% [0.0–2.5] | 0.0% [0.0–2.5] |
| balanced | 27.3% [20.8–35.0] | 14.0% [9.3–20.5] |
| eclipse | 6.0% [3.2–11.0] | 8.0% [4.6–13.5] |
| engineers | 3.3% [1.4–7.6] | 5.3% [2.7–10.2] |
| frozen_fortress | 30.7% [23.8–38.5] | 10.7% [6.7–16.6] |
| glass_cannon | 11.3% [7.2–17.4] | 13.3% [8.8–19.7] |
| magma_engine | 24.0% [17.9–31.4] | 17.3% [12.1–24.2] |
| mixed_burst | 27.3% [20.8–35.0] | 39.3% [31.9–47.3] |
| phoenix_gale | 10.7% [6.7–16.6] | 4.7% [2.3–9.3] |
| thorn_doctor | 0.0% [0.0–2.5] | 4.7% [2.3–9.3] |
| thunderstorm | 36.7% [29.4–44.6] | 28.7% [22.0–36.4] |
| verdant_plague | 3.3% [1.4–7.6] | 3.3% [1.4–7.6] |

## Failure waves (share of all defeats)
| Wave | Defeats | Share | Top killers |
|---|---|---|---|
| 18 | 694 | 22.4% | sapper 609, juggernaut 36, hexcaster 24 |
| 14 | 685 | 22.1% | sapper 558, shieldbearer 72, hexcaster 25 |
| 17 | 366 | 11.8% | mimic 187, siege_colossus 119, warded 40 |
| 19 | 270 | 8.7% | shieldbearer 76, hexcaster 55, mimic 53 |
| 9 | 241 | 7.8% | warded 188, grunt 51, void_priest 2 |
| 12 | 218 | 7.0% | shieldbearer 134, hexcaster 44, mirror_knight 20 |
| 10 | 131 | 4.2% | ignaroth 44, thornmother 36, ashen_matriarch 21 |
| 15 | 121 | 3.9% | juggernaut 53, ravager 36, banner 17 |

## Outlier flags (automatic; investigate, do not auto-nerf)
Rules: *must-pick candidate* = owned in ≥5% of runs and its win-rate CI lies entirely above the without-CI by ≥10 pp; *never viable* = in ≥30 runs with 0 wins; *spike* = one wave causes >25% of defeats. Presence correlates with drafting skill and run length (relics picked late appear in longer runs) — treat as leads, not verdicts.

- must-pick candidate (hero): ignis — 20.3% [18.3–22.5] with vs 9.4% [8.2–10.7] without
- must-pick candidate (hero): marina — 27.3% [24.8–30.0] with vs 7.4% [6.4–8.5] without
- must-pick candidate (hero): zephyr — 22.4% [19.0–26.1] with vs 12.3% [11.2–13.5] without
- must-pick candidate (relic): mana_battery — 25.4% [20.6–30.8] with vs 12.8% [11.7–13.9] without
- must-pick candidate (relic): overgrowth — 23.9% [19.7–28.7] with vs 12.7% [11.6–13.9] without
- must-pick candidate (relic): frozen_heart — 23.3% [18.0–29.5] with vs 13.2% [12.1–14.3] without
- must-pick candidate (relic): crystal_growth — 24.2% [18.6–30.8] with vs 13.2% [12.1–14.4] without
- must-pick candidate (relic): iron_bulwark — 23.0% [18.9–27.7] with vs 12.7% [11.6–13.9] without
- must-pick candidate (relic): spark_of_genesis — 23.3% [18.6–28.8] with vs 13.0% [11.9–14.2] without
- must-pick candidate (relic): sanctuary_bell — 33.7% [27.5–40.4] with vs 12.6% [11.5–13.7] without
- must-pick candidate (relic): zephyr_sash — 24.2% [19.8–29.1] with vs 12.7% [11.6–13.9] without
- must-pick candidate (relic): kite_banner — 24.3% [20.1–29.2] with vs 12.6% [11.5–13.8] without
- must-pick candidate (relic): twilight_hourglass — 24.9% [19.2–31.6] with vs 13.1% [12.1–14.3] without
- must-pick candidate (relic): ember_codex — 24.3% [21.5–27.4] with vs 10.7% [9.6–11.9] without
- must-pick candidate (relic): tidal_engine — 27.5% [24.1–31.1] with vs 10.8% [9.8–12.0] without
- must-pick candidate (relic): ember_testament — 27.9% [24.9–31.3] with vs 10.0% [8.9–11.1] without
- must-pick candidate (relic): ocean_heart — 42.6% [38.7–46.7] with vs 8.1% [7.2–9.1] without
