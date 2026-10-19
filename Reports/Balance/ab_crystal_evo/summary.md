# Batch balance report (headless, authoritative simulation)

> AutoPilot policies are **bots, not players**: rates describe scripted/heuristic drafting, not human win rates.

- Runs: **24000** (500 seeds × 12 starting lineups × 4 policies), mode Classic, Ascension 0, biome default
- Wall clock: 592.5s on 4 threads (Intel(R) Xeon(R) Processor @ 2.10GHz), .NET 8.0.31
- Content hash: `292ebec7f47819b3` · Unity editor not involved (pure C# simulation shared with the game)
- Invariants (finished, no NaN, gold ≥ 0, exactly one outcome): **all passed**; stuck runs: 0

## Win rate by policy (95% Wilson CI)
| Policy | Runs | Win rate | Avg wave |
|---|---|---|---|
| greedy | 6000 | 13.5% [12.7–14.4] | 15.5 |
| random | 6000 | 12.6% [11.7–13.4] | 15.6 |
| scripted | 6000 | 15.0% [14.2–16.0] | 15.8 |
| synergy | 6000 | 10.8% [10.0–11.6] | 15.3 |

## Win rate by starting lineup × policy
| Lineup | scripted | synergy | random | greedy |
|---|---|---|---|---|
| arcane_void | 0.2% [0.0–1.1] | 0.6% [0.2–1.7] | 0.8% [0.3–2.0] | 0.6% [0.2–1.7] |
| balanced | 34.6% [30.6–38.9] | 19.6% [16.4–23.3] | 17.8% [14.7–21.4] | 20.8% [17.5–24.6] |
| eclipse | 5.6% [3.9–8.0] | 4.8% [3.2–7.0] | 6.2% [4.4–8.7] | 7.8% [5.8–10.5] |
| engineers | 4.6% [3.1–6.8] | 3.4% [2.1–5.4] | 5.2% [3.6–7.5] | 6.6% [4.7–9.1] |
| frozen_fortress | 31.6% [27.7–35.8] | 18.0% [14.9–21.6] | 14.0% [11.2–17.3] | 15.6% [12.7–19.0] |
| glass_cannon | 11.2% [8.7–14.3] | 12.8% [10.2–16.0] | 12.2% [9.6–15.4] | 12.4% [9.8–15.6] |
| magma_engine | 27.6% [23.9–31.7] | 11.8% [9.3–14.9] | 17.0% [14.0–20.5] | 19.0% [15.8–22.7] |
| mixed_burst | 22.0% [18.6–25.8] | 32.8% [28.8–37.0] | 39.8% [35.6–44.2] | 38.2% [34.0–42.5] |
| phoenix_gale | 11.0% [8.5–14.0] | 3.2% [2.0–5.1] | 5.8% [4.1–8.2] | 6.6% [4.7–9.1] |
| thorn_doctor | 1.0% [0.4–2.3] | 2.6% [1.5–4.4] | 3.8% [2.4–5.9] | 5.8% [4.1–8.2] |
| thunderstorm | 29.8% [26.0–34.0] | 19.0% [15.8–22.7] | 25.8% [22.2–29.8] | 26.8% [23.1–30.8] |
| verdant_plague | 1.2% [0.6–2.6] | 0.8% [0.3–2.0] | 2.2% [1.2–3.9] | 2.2% [1.2–3.9] |

## Failure waves (share of all defeats)
| Wave | Defeats | Share | Top killers |
|---|---|---|---|
| 14 | 4791 | 22.9% | sapper 3845, shieldbearer 466, hexcaster 212 |
| 18 | 4550 | 21.8% | sapper 3961, juggernaut 209, hexcaster 187 |
| 17 | 2322 | 11.1% | mimic 1188, siege_colossus 738, warded 240 |
| 12 | 1662 | 8.0% | shieldbearer 1038, hexcaster 308, hex_binder 128 |
| 19 | 1646 | 7.9% | mimic 380, shieldbearer 353, hexcaster 318 |
| 9 | 1566 | 7.5% | warded 1186, grunt 325, void_priest 55 |
| 15 | 867 | 4.2% | juggernaut 394, ravager 257, grunt 92 |
| 10 | 837 | 4.0% | ignaroth 272, thornmother 211, ashen_matriarch 189 |

## Outlier flags (automatic; investigate, do not auto-nerf)
Rules: *must-pick candidate* = owned in ≥5% of runs and its win-rate CI lies entirely above the without-CI by ≥10 pp; *never viable* = in ≥30 runs with 0 wins; *spike* = one wave causes >25% of defeats. Presence correlates with drafting skill and run length (relics picked late appear in longer runs) — treat as leads, not verdicts.

- must-pick candidate (hero): ignis — 21.3% [20.4–22.1] with vs 8.1% [7.7–8.6] without
- must-pick candidate (hero): marina — 24.1% [23.1–25.1] with vs 7.9% [7.5–8.3] without
- must-pick candidate (relic): mana_battery — 26.4% [24.5–28.5] with vs 11.9% [11.4–12.3] without
- must-pick candidate (relic): overgrowth — 24.9% [23.2–26.7] with vs 11.7% [11.3–12.1] without
- must-pick candidate (relic): storm_caller — 22.5% [20.7–24.5] with vs 12.2% [11.8–12.6] without
- must-pick candidate (relic): sanctuary_bell — 34.0% [31.7–36.3] with vs 11.4% [11.0–11.9] without
- must-pick candidate (relic): zephyr_sash — 22.3% [20.7–24.0] with vs 11.9% [11.5–12.3] without
- must-pick candidate (relic): ember_codex — 23.8% [22.7–25.0] with vs 9.9% [9.5–10.3] without
- must-pick candidate (relic): tidal_engine — 24.4% [23.2–25.8] with vs 10.5% [10.1–10.9] without
- must-pick candidate (relic): ember_testament — 29.4% [28.1–30.7] with vs 8.9% [8.5–9.3] without
- must-pick candidate (relic): ocean_heart — 35.7% [34.2–37.3] with vs 8.6% [8.2–9.0] without
