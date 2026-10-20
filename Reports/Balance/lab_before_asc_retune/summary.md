# Balance lab (playstyle bots × biomes × Ascension)

> Bots, not players. Seeds are paired across bots/biomes/ascensions. Lifts are associations, not causes.

- Runs: **3780** = 7 bots × 6 biomes × 3 Ascension levels × 30 seeds; 51s on 4 threads (Intel(R) Xeon(R) Processor @ 2.10GHz)
- Content hash `82127e62bbda5f78`; command `dotnet run --project Tools/SimHarness/Balance -c Release -- --lab --seeds 30`
- Bot mapping: mono_element = mono_fire, reaction_chain = thunderstorm, tank_healer_stall = stall, boss_burst = boss_burst, summon_proc = summon_proc, area_control = frozen_fortress, naive_random = balanced (random drafting)

## Clear rate by bot × Ascension (95% Wilson CI)
| Bot | A0 | A5 | A10 |
|---|---|---|---|
| mono_element | 10.0% [6–15] n=180 | 0.0% [0–2] n=180 | 0.0% [0–2] n=180 |
| reaction_chain | 21.7% [16–28] n=180 | 0.0% [0–2] n=180 | 0.0% [0–2] n=180 |
| tank_healer_stall | 22.8% [17–29] n=180 | 0.0% [0–2] n=180 | 0.0% [0–2] n=180 |
| boss_burst | 0.6% [0–3] n=180 | 0.0% [0–2] n=180 | 0.0% [0–2] n=180 |
| summon_proc | 6.7% [4–11] n=180 | 0.0% [0–2] n=180 | 0.0% [0–2] n=180 |
| area_control | 23.9% [18–31] n=180 | 0.0% [0–2] n=180 | 0.0% [0–2] n=180 |
| naive_random | 24.4% [19–31] n=180 | 0.0% [0–2] n=180 | 0.0% [0–2] n=180 |

## Clear rate by bot × biome (all Ascensions pooled)
| Bot | verdant_sanctuary | molten_crater | frostfall_bastion | shattered_aether | stormspire_citadel | sunken_archive |
|---|---|---|---|---|---|---|
| mono_element | 4.4% [2–11] n=90 | 3.3% [1–9] n=90 | 2.2% [1–8] n=90 | 4.4% [2–11] n=90 | 2.2% [1–8] n=90 | 3.3% [1–9] n=90 |
| reaction_chain | 6.7% [3–14] n=90 | 7.8% [4–15] n=90 | 3.3% [1–9] n=90 | 10.0% [5–18] n=90 | 6.7% [3–14] n=90 | 8.9% [5–17] n=90 |
| tank_healer_stall | 11.1% [6–19] n=90 | 7.8% [4–15] n=90 | 6.7% [3–14] n=90 | 6.7% [3–14] n=90 | 6.7% [3–14] n=90 | 6.7% [3–14] n=90 |
| boss_burst | 1.1% [0–6] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 |
| summon_proc | 2.2% [1–8] n=90 | 4.4% [2–11] n=90 | 1.1% [0–6] n=90 | 2.2% [1–8] n=90 | 2.2% [1–8] n=90 | 1.1% [0–6] n=90 |
| area_control | 6.7% [3–14] n=90 | 12.2% [7–21] n=90 | 6.7% [3–14] n=90 | 8.9% [5–17] n=90 | 5.6% [2–12] n=90 | 7.8% [4–15] n=90 |
| naive_random | 8.9% [5–17] n=90 | 7.8% [4–15] n=90 | 7.8% [4–15] n=90 | 8.9% [5–17] n=90 | 6.7% [3–14] n=90 | 8.9% [5–17] n=90 |

## 20-wave clear curve (share of runs alive at the start of the wave, A0 / A10)
| Bot | Asc | w5 | w10 | w14 | w15 | w18 | w20 |
|---|---|---|---|---|---|---|---|
| mono_element | A0 | 100% | 96% | 78% | 54% | 31% | 10% |
| mono_element | A10 | 78% | 0% | 0% | 0% | 0% | 0% |
| reaction_chain | A0 | 100% | 97% | 88% | 76% | 67% | 23% |
| reaction_chain | A10 | 24% | 0% | 0% | 0% | 0% | 0% |
| tank_healer_stall | A0 | 100% | 84% | 77% | 57% | 44% | 26% |
| tank_healer_stall | A10 | 0% | 0% | 0% | 0% | 0% | 0% |
| boss_burst | A0 | 100% | 74% | 53% | 24% | 13% | 1% |
| boss_burst | A10 | 17% | 0% | 0% | 0% | 0% | 0% |
| summon_proc | A0 | 100% | 94% | 74% | 49% | 27% | 7% |
| summon_proc | A10 | 62% | 0% | 0% | 0% | 0% | 0% |
| area_control | A0 | 100% | 84% | 67% | 63% | 44% | 25% |
| area_control | A10 | 21% | 0% | 0% | 0% | 0% | 0% |
| naive_random | A0 | 100% | 93% | 87% | 73% | 54% | 29% |
| naive_random | A10 | 78% | 0% | 0% | 0% | 0% | 0% |

## Where runs end (defeat wave, all bots)
| Wave | Defeats | Share of defeats |
|---|---|---|
| 6 | 612 | 17.1% |
| 5 | 363 | 10.1% |
| 9 | 354 | 9.9% |
| 2 | 340 | 9.5% |
| 4 | 322 | 9.0% |
| 7 | 320 | 8.9% |

## Anomaly detectors
### Possibly dominant relics (win-rate lift ≥ 1.8 vs runs alive at the same wave without it, n ≥ 30)
- `sanctuary_bell`: n=76, win 32.9% vs 12.0% → lift 2.75
- `living_monolith`: n=39, win 79.5% vs 33.9% → lift 2.34
- `tidecaller_pearl`: n=453, win 19.6% vs 9.1% → lift 2.17
- `ocean_heart`: n=422, win 28.0% vs 14.4% → lift 1.95
- `overgrowth`: n=128, win 25.0% vs 13.3% → lift 1.88
- `twilight_hourglass`: n=71, win 47.9% vs 25.7% → lift 1.86
- `frostbreaker_hammer`: n=294, win 23.1% vs 12.5% → lift 1.86
### Possible trap cards (lift ≤ 0.6, n ≥ 30)
- `spec_vesper_potency`: n=35, win 0.0% vs 17.0% → lift 0.00
- `toxic_shock_theory`: n=131, win 4.6% vs 20.0% → lift 0.23
- `toxic_pact`: n=152, win 3.9% vs 17.1% → lift 0.23
- `spec_raiden_afterimage`: n=353, win 2.3% vs 8.8% → lift 0.26
- `spec_sable_triage`: n=109, win 5.5% vs 21.1% → lift 0.26
- `spec_veyra_overcharge_ramp`: n=353, win 2.5% vs 9.3% → lift 0.27
- `spec_caelis_resonant_echo`: n=471, win 3.4% vs 9.5% → lift 0.36
- `void_covenant`: n=59, win 6.8% vs 14.6% → lift 0.46
- `spec_tidal_riptide`: n=90, win 10.0% vs 17.7% → lift 0.56
### Empty/thin draft choices
- 0 of 18528 draft screens offered fewer than 3 cards (0.00%).
### Runaway reaction chains
- Runs where the reaction budget had to block reactions: 5 / 3780 (0.1%); max reactions/s seen: 45; p95 20.
### Proc explosions
- Runs reaching the proc-generation cap (2): 3219; runs where the cap blocked a reaction: 1324 (35.0%). The cap is the safety net; a high share means procs lean on it.
### Excessive stuns
- Runs with a wave where enemies spent > 60% of their alive time hard-CC'd: 0 / 3780 (0.0%). Per bot: mono_element 0%, reaction_chain 0%, tank_healer_stall 0%, boss_burst 0%, summon_proc 0%, area_control 0%, naive_random 0%

Full relic/card lift tables: `relic_lift.csv`, `card_lift.csv`.

## Knob sensitivity (data in economy.json; paired seeds)
| Knob (economy.json) | reaction_chain win | tank_healer_stall win | Δ vs baseline (pp, mean of both) |
|---|---|---|---|
| baseline | 33.3% | 43.3% | — |
| enemyHpGrowth ×0.9 | 46.7% | 43.3% | +6.7 |
| enemyHpGrowth ×1.1 | 26.7% | 26.7% | -11.7 |
| crystalHp ×0.9 | 26.7% | 20.0% | -15.0 |
| crystalHp ×1.1 | 43.3% | 53.3% | +10.0 |

30 paired seeds per bot per knob, default biome, Ascension 0. Small samples: treat deltas under ~10 pp as noise.

