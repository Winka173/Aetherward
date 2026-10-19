# Batch balance report (headless, authoritative simulation)

> AutoPilot policies are **bots, not players**: rates describe scripted/heuristic drafting, not human win rates.

- Runs: **24000** (500 seeds × 12 starting lineups × 4 policies), mode Classic, Ascension 0, biome default
- Wall clock: 1039.9s on 4 threads (Intel(R) Xeon(R) Processor @ 2.10GHz), .NET 8.0.31
- Content hash: `292ebec7f47819b3` · Unity editor not involved (pure C# simulation shared with the game)
- Invariants (finished, no NaN, gold ≥ 0, exactly one outcome): **all passed**; stuck runs: 0

## Win rate by policy (95% Wilson CI)
| Policy | Runs | Win rate | Avg wave |
|---|---|---|---|
| greedy | 6000 | 13.3% [12.4–14.1] | 14.9 |
| random | 6000 | 12.2% [11.3–13.0] | 15.1 |
| scripted | 6000 | 14.1% [13.2–15.0] | 15.3 |
| synergy | 6000 | 9.4% [8.7–10.2] | 14.6 |

## Win rate by starting lineup × policy
| Lineup | scripted | synergy | random | greedy |
|---|---|---|---|---|
| arcane_void | 0.2% [0.0–1.1] | 0.0% [0.0–0.8] | 1.2% [0.6–2.6] | 1.6% [0.8–3.1] |
| balanced | 28.2% [24.4–32.3] | 15.2% [12.3–18.6] | 15.2% [12.3–18.6] | 17.6% [14.5–21.2] |
| eclipse | 4.6% [3.1–6.8] | 3.6% [2.3–5.6] | 6.4% [4.6–8.9] | 5.4% [3.7–7.7] |
| engineers | 5.4% [3.7–7.7] | 4.0% [2.6–6.1] | 5.6% [3.9–8.0] | 6.2% [4.4–8.7] |
| frozen_fortress | 22.4% [19.0–26.3] | 10.6% [8.2–13.6] | 14.4% [11.6–17.7] | 8.0% [5.9–10.7] |
| glass_cannon | 11.0% [8.5–14.0] | 10.8% [8.4–13.8] | 14.2% [11.4–17.5] | 16.2% [13.2–19.7] |
| magma_engine | 27.0% [23.3–31.1] | 11.0% [8.5–14.0] | 15.0% [12.1–18.4] | 15.2% [12.3–18.6] |
| mixed_burst | 23.2% [19.7–27.1] | 31.6% [27.7–35.8] | 36.8% [32.7–41.1] | 46.6% [42.3–51.0] |
| phoenix_gale | 11.2% [8.7–14.3] | 5.0% [3.4–7.3] | 6.2% [4.4–8.7] | 5.4% [3.7–7.7] |
| thorn_doctor | 0.2% [0.0–1.1] | 0.6% [0.2–1.7] | 1.6% [0.8–3.1] | 3.0% [1.8–4.9] |
| thunderstorm | 34.0% [30.0–38.3] | 20.0% [16.7–23.7] | 27.4% [23.7–31.5] | 32.8% [28.8–37.0] |
| verdant_plague | 1.2% [0.6–2.6] | 0.8% [0.3–2.0] | 1.8% [0.9–3.4] | 1.2% [0.6–2.6] |

## Failure waves (share of all defeats)
| Wave | Defeats | Share | Top killers |
|---|---|---|---|
| 14 | 4564 | 21.7% | sapper 3480, shieldbearer 439, runner 238 |
| 18 | 3520 | 16.7% | sapper 2830, juggernaut 264, hexcaster 178 |
| 9 | 2901 | 13.8% | warded 2083, grunt 706, void_priest 112 |
| 17 | 2226 | 10.6% | mimic 1102, siege_colossus 724, warded 260 |
| 19 | 1843 | 8.7% | storm_harpy 401, shieldbearer 342, mimic 323 |
| 12 | 1818 | 8.6% | shieldbearer 1195, hexcaster 269, mirror_knight 118 |
| 15 | 836 | 4.0% | juggernaut 359, ravager 251, grunt 100 |
| 7 | 656 | 3.1% | shieldbearer 291, juggernaut 245, ironback_golem 119 |

## Outlier flags (automatic; investigate, do not auto-nerf)
Rules: *must-pick candidate* = owned in ≥5% of runs and its win-rate CI lies entirely above the without-CI by ≥10 pp; *never viable* = in ≥30 runs with 0 wins; *spike* = one wave causes >25% of defeats. Presence correlates with drafting skill and run length (relics picked late appear in longer runs) — treat as leads, not verdicts.

- must-pick candidate (hero): ignis — 20.3% [19.5–21.2] with vs 7.5% [7.1–8.0] without
- must-pick candidate (hero): marina — 24.5% [23.5–25.5] with vs 6.7% [6.3–7.1] without
- must-pick candidate (hero): zephyr — 21.6% [20.2–23.1] with vs 10.8% [10.4–11.2] without
- must-pick candidate (relic): mana_battery — 27.6% [25.6–29.8] with vs 11.0% [10.6–11.4] without
- must-pick candidate (relic): overgrowth — 25.2% [23.4–27.0] with vs 10.9% [10.5–11.3] without
- must-pick candidate (relic): storm_caller — 24.5% [22.5–26.6] with vs 11.3% [10.9–11.7] without
- must-pick candidate (relic): sanctuary_bell — 35.2% [32.8–37.7] with vs 10.7% [10.3–11.1] without
- must-pick candidate (relic): zephyr_sash — 23.6% [21.9–25.3] with vs 11.0% [10.6–11.4] without
- must-pick candidate (relic): ember_codex — 22.8% [21.7–24.0] with vs 9.4% [9.0–9.8] without
- must-pick candidate (relic): tidal_engine — 26.2% [24.9–27.6] with vs 9.3% [8.9–9.8] without
- must-pick candidate (relic): ember_testament — 28.4% [27.1–29.7] with vs 8.5% [8.1–8.9] without
- must-pick candidate (relic): ocean_heart — 38.0% [36.5–39.6] with vs 7.5% [7.2–7.9] without
