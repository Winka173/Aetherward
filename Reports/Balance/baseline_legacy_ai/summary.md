# Batch balance report (headless, authoritative simulation)

> AutoPilot policies are **bots, not players**: rates describe scripted/heuristic drafting, not human win rates.

- Runs: **48000** (1000 seeds × 12 starting lineups × 4 policies), mode Classic, Ascension 0, biome default
- Wall clock: 909.7s on 4 threads (Intel(R) Xeon(R) Processor @ 2.10GHz), .NET 8.0.31
- Content hash: `cc591f02dd5044be` · Unity editor not involved (pure C# simulation shared with the game)
- Invariants (finished, no NaN, gold ≥ 0, exactly one outcome): **all passed**; stuck runs: 0

## Win rate by policy (95% Wilson CI)
| Policy | Runs | Win rate | Avg wave |
|---|---|---|---|
| greedy | 12000 | 9.4% [8.9–9.9] | 14.5 |
| random | 12000 | 7.8% [7.4–8.3] | 14.6 |
| scripted | 12000 | 9.7% [9.2–10.2] | 14.7 |
| synergy | 12000 | 6.7% [6.2–7.1] | 14.1 |

## Win rate by starting lineup × policy
| Lineup | scripted | synergy | random | greedy |
|---|---|---|---|---|
| arcane_void | 0.0% [0.0–0.4] | 0.1% [0.0–0.6] | 0.1% [0.0–0.6] | 0.7% [0.3–1.4] |
| balanced | 19.7% [17.4–22.3] | 10.0% [8.3–12.0] | 9.4% [7.7–11.4] | 11.9% [10.0–14.1] |
| eclipse | 2.6% [1.8–3.8] | 1.7% [1.1–2.7] | 3.6% [2.6–4.9] | 4.3% [3.2–5.7] |
| engineers | 2.9% [2.0–4.1] | 3.0% [2.1–4.3] | 2.7% [1.9–3.9] | 4.1% [3.0–5.5] |
| frozen_fortress | 19.9% [17.5–22.5] | 9.6% [7.9–11.6] | 10.1% [8.4–12.1] | 10.2% [8.5–12.2] |
| glass_cannon | 7.9% [6.4–9.7] | 9.7% [8.0–11.7] | 10.8% [9.0–12.9] | 12.5% [10.6–14.7] |
| magma_engine | 18.4% [16.1–20.9] | 7.9% [6.4–9.7] | 9.0% [7.4–10.9] | 9.2% [7.6–11.2] |
| mixed_burst | 11.8% [9.9–13.9] | 21.2% [18.8–23.8] | 26.0% [23.4–28.8] | 31.5% [28.7–34.4] |
| phoenix_gale | 9.3% [7.7–11.3] | 3.9% [2.9–5.3] | 2.9% [2.0–4.1] | 3.6% [2.6–4.9] |
| thorn_doctor | 0.1% [0.0–0.6] | 0.7% [0.3–1.4] | 1.1% [0.6–2.0] | 1.3% [0.8–2.2] |
| thunderstorm | 23.2% [20.7–25.9] | 12.0% [10.1–14.2] | 18.0% [15.7–20.5] | 22.0% [19.5–24.7] |
| verdant_plague | 0.5% [0.2–1.2] | 0.0% [0.0–0.4] | 0.5% [0.2–1.2] | 1.3% [0.8–2.2] |

## Failure waves (share of all defeats)
| Wave | Defeats | Share | Top killers |
|---|---|---|---|
| 14 | 10595 | 24.1% | sapper 8770, shieldbearer 765, runner 484 |
| 18 | 7836 | 17.8% | sapper 7164, juggernaut 247, hexcaster 194 |
| 9 | 5811 | 13.2% | warded 4083, grunt 1490, void_priest 238 |
| 12 | 3773 | 8.6% | shieldbearer 2319, hexcaster 595, mirror_knight 304 |
| 17 | 3585 | 8.2% | mimic 1752, siege_colossus 1164, warded 418 |
| 13 | 3206 | 7.3% | sapper 3015, grunt 64, stone_burrower 45 |
| 19 | 2111 | 4.8% | mimic 476, hexcaster 433, shieldbearer 406 |
| 10 | 1551 | 3.5% | ignaroth 548, thornmother 390, ashen_matriarch 298 |

## Outlier flags (automatic; investigate, do not auto-nerf)
Rules: *must-pick candidate* = owned in ≥5% of runs and its win-rate CI lies entirely above the without-CI by ≥10 pp; *never viable* = in ≥30 runs with 0 wins; *spike* = one wave causes >25% of defeats. Presence correlates with drafting skill and run length (relics picked late appear in longer runs) — treat as leads, not verdicts.

- must-pick candidate (hero): marina — 16.8% [16.3–17.5] with vs 4.6% [4.4–4.9] without
- must-pick candidate (relic): mana_battery — 21.4% [19.9–22.9] with vs 7.5% [7.3–7.8] without
- must-pick candidate (relic): overgrowth — 17.6% [16.4–18.8] with vs 7.5% [7.3–7.8] without
- must-pick candidate (relic): sanctuary_bell — 24.3% [22.8–26.0] with vs 7.4% [7.1–7.6] without
- must-pick candidate (relic): ember_codex — 16.6% [15.9–17.4] with vs 6.4% [6.1–6.6] without
- must-pick candidate (relic): tidal_engine — 18.9% [18.1–19.8] with vs 6.5% [6.2–6.7] without
- must-pick candidate (relic): ember_testament — 21.0% [20.2–21.9] with vs 5.7% [5.5–5.9] without
- must-pick candidate (relic): ocean_heart — 29.0% [27.9–30.1] with vs 5.1% [4.9–5.3] without
