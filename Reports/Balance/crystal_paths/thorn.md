# Batch balance report (headless, authoritative simulation)

> AutoPilot policies are **bots, not players**: rates describe scripted/heuristic drafting, not human win rates.

- Runs: **3600** (150 seeds × 12 starting lineups × 2 policies), mode Classic, Ascension 0, biome default
- Wall clock: 153.6s on 4 threads (Intel(R) Xeon(R) Processor @ 2.10GHz), .NET 8.0.31
- Content hash: `292ebec7f47819b3` · Unity editor not involved (pure C# simulation shared with the game)
- Invariants (finished, no NaN, gold ≥ 0, exactly one outcome): **all passed**; stuck runs: 0

## Win rate by policy (95% Wilson CI)
| Policy | Runs | Win rate | Avg wave |
|---|---|---|---|
| greedy | 1800 | 12.6% [11.2–14.2] | 15.9 |
| scripted | 1800 | 14.6% [13.0–16.3] | 16.0 |

## Win rate by starting lineup × policy
| Lineup | scripted | greedy |
|---|---|---|
| arcane_void | 0.0% [0.0–2.5] | 0.0% [0.0–2.5] |
| balanced | 26.7% [20.2–34.3] | 14.0% [9.3–20.5] |
| eclipse | 6.7% [3.7–11.8] | 7.3% [4.1–12.7] |
| engineers | 4.0% [1.8–8.5] | 5.3% [2.7–10.2] |
| frozen_fortress | 33.3% [26.3–41.2] | 13.3% [8.8–19.7] |
| glass_cannon | 9.3% [5.6–15.1] | 12.7% [8.3–18.9] |
| magma_engine | 20.7% [15.0–27.8] | 16.7% [11.6–23.4] |
| mixed_burst | 28.0% [21.4–35.7] | 38.7% [31.2–46.7] |
| phoenix_gale | 10.7% [6.7–16.6] | 5.3% [2.7–10.2] |
| thorn_doctor | 0.0% [0.0–2.5] | 2.7% [1.0–6.7] |
| thunderstorm | 32.7% [25.7–40.5] | 33.3% [26.3–41.2] |
| verdant_plague | 2.7% [1.0–6.7] | 2.0% [0.7–5.7] |

## Failure waves (share of all defeats)
| Wave | Defeats | Share | Top killers |
|---|---|---|---|
| 18 | 837 | 26.9% | sapper 750, juggernaut 48, hexcaster 15 |
| 14 | 688 | 22.1% | sapper 551, shieldbearer 75, hexcaster 25 |
| 17 | 359 | 11.5% | mimic 176, siege_colossus 105, warded 58 |
| 13 | 196 | 6.3% | sapper 176, juggernaut 10, stone_burrower 4 |
| 19 | 189 | 6.1% | mimic 68, shieldbearer 59, hexcaster 24 |
| 15 | 153 | 4.9% | ravager 64, juggernaut 58, banner 16 |
| 12 | 147 | 4.7% | shieldbearer 112, mirror_knight 13, hexcaster 12 |
| 10 | 137 | 4.4% | thornmother 39, ignaroth 39, ashen_matriarch 26 |

## Outlier flags (automatic; investigate, do not auto-nerf)
Rules: *must-pick candidate* = owned in ≥5% of runs and its win-rate CI lies entirely above the without-CI by ≥10 pp; *never viable* = in ≥30 runs with 0 wins; *spike* = one wave causes >25% of defeats. Presence correlates with drafting skill and run length (relics picked late appear in longer runs) — treat as leads, not verdicts.

- must-pick candidate (hero): marina — 27.1% [24.6–29.7] with vs 7.2% [6.2–8.3] without
- must-pick candidate (hero): zephyr — 22.6% [19.2–26.3] with vs 12.0% [10.9–13.2] without
- must-pick candidate (hero): nerissa — 22.3% [18.8–26.4] with vs 12.3% [11.2–13.5] without
- must-pick candidate (relic): mana_battery — 23.8% [19.2–29.2] with vs 12.7% [11.6–13.9] without
- must-pick candidate (relic): overgrowth — 24.5% [20.3–29.2] with vs 12.4% [11.3–13.6] without
- must-pick candidate (relic): thunder_relay — 23.0% [18.2–28.6] with vs 12.9% [11.8–14.1] without
- must-pick candidate (relic): eternal_ember — 22.8% [18.4–28.0] with vs 12.8% [11.7–14.0] without
- must-pick candidate (relic): crystal_growth — 29.3% [23.2–36.1] with vs 12.7% [11.6–13.9] without
- must-pick candidate (relic): sanctuary_bell — 35.3% [29.0–42.2] with vs 12.3% [11.2–13.4] without
- must-pick candidate (relic): kite_banner — 25.3% [21.0–30.1] with vs 12.3% [11.3–13.5] without
- must-pick candidate (relic): ember_codex — 23.4% [20.7–26.5] with vs 10.7% [9.6–11.9] without
- must-pick candidate (relic): tidal_engine — 28.7% [25.3–32.3] with vs 10.3% [9.3–11.5] without
- must-pick candidate (relic): ember_testament — 27.7% [24.6–30.9] with vs 9.8% [8.7–10.9] without
- must-pick candidate (relic): ocean_heart — 39.2% [35.4–43.2] with vs 8.4% [7.5–9.5] without
- spike: wave 18 causes 27% of defeats
