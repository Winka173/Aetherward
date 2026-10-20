# Balance lab (playstyle bots × biomes × Ascension)

> Bots, not players. Seeds are paired across bots/biomes/ascensions. Lifts are associations, not causes.

- Runs: **3780** = 7 bots × 6 biomes × 3 Ascension levels × 30 seeds; 44s on 4 threads (Intel(R) Xeon(R) Processor @ 2.10GHz)
- Content hash `b898c5023e8c67cd`; command `dotnet run --project Tools/SimHarness/Balance -c Release -- --lab --seeds 30`
- Bot mapping: mono_element = mono_fire, reaction_chain = thunderstorm, tank_healer_stall = stall, boss_burst = boss_burst, summon_proc = summon_proc, area_control = frozen_fortress, naive_random = balanced (random drafting)

## Clear rate by bot × Ascension (95% Wilson CI)
| Bot | A0 | A5 | A10 |
|---|---|---|---|
| mono_element | 11.7% [8–17] n=180 | 0.0% [0–2] n=180 | 0.0% [0–2] n=180 |
| reaction_chain | 21.7% [16–28] n=180 | 0.0% [0–2] n=180 | 0.0% [0–2] n=180 |
| tank_healer_stall | 6.1% [3–11] n=180 | 0.0% [0–2] n=180 | 0.0% [0–2] n=180 |
| boss_burst | 0.6% [0–3] n=180 | 0.0% [0–2] n=180 | 0.0% [0–2] n=180 |
| summon_proc | 6.7% [4–11] n=180 | 0.0% [0–2] n=180 | 0.0% [0–2] n=180 |
| area_control | 19.4% [14–26] n=180 | 0.0% [0–2] n=180 | 0.0% [0–2] n=180 |
| naive_random | 24.4% [19–31] n=180 | 0.0% [0–2] n=180 | 0.0% [0–2] n=180 |

## Clear rate by bot × biome (all Ascensions pooled)
| Bot | verdant_sanctuary | molten_crater | frostfall_bastion | shattered_aether | stormspire_citadel | sunken_archive |
|---|---|---|---|---|---|---|
| mono_element | 4.4% [2–11] n=90 | 3.3% [1–9] n=90 | 3.3% [1–9] n=90 | 4.4% [2–11] n=90 | 3.3% [1–9] n=90 | 4.4% [2–11] n=90 |
| reaction_chain | 6.7% [3–14] n=90 | 7.8% [4–15] n=90 | 3.3% [1–9] n=90 | 10.0% [5–18] n=90 | 6.7% [3–14] n=90 | 8.9% [5–17] n=90 |
| tank_healer_stall | 0.0% [0–4] n=90 | 8.9% [5–17] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 1.1% [0–6] n=90 | 2.2% [1–8] n=90 |
| boss_burst | 1.1% [0–6] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 |
| summon_proc | 2.2% [1–8] n=90 | 4.4% [2–11] n=90 | 1.1% [0–6] n=90 | 2.2% [1–8] n=90 | 2.2% [1–8] n=90 | 1.1% [0–6] n=90 |
| area_control | 5.6% [2–12] n=90 | 10.0% [5–18] n=90 | 5.6% [2–12] n=90 | 7.8% [4–15] n=90 | 5.6% [2–12] n=90 | 4.4% [2–11] n=90 |
| naive_random | 7.8% [4–15] n=90 | 7.8% [4–15] n=90 | 8.9% [5–17] n=90 | 8.9% [5–17] n=90 | 5.6% [2–12] n=90 | 10.0% [5–18] n=90 |

## 20-wave clear curve (share of runs alive at the start of the wave, A0 / A10)
| Bot | Asc | w5 | w10 | w14 | w15 | w18 | w20 |
|---|---|---|---|---|---|---|---|
| mono_element | A0 | 100% | 93% | 78% | 51% | 34% | 12% |
| mono_element | A10 | 7% | 0% | 0% | 0% | 0% | 0% |
| reaction_chain | A0 | 100% | 97% | 88% | 76% | 67% | 23% |
| reaction_chain | A10 | 1% | 0% | 0% | 0% | 0% | 0% |
| tank_healer_stall | A0 | 26% | 24% | 24% | 19% | 14% | 7% |
| tank_healer_stall | A10 | 0% | 0% | 0% | 0% | 0% | 0% |
| boss_burst | A0 | 100% | 73% | 50% | 23% | 13% | 1% |
| boss_burst | A10 | 0% | 0% | 0% | 0% | 0% | 0% |
| summon_proc | A0 | 100% | 94% | 74% | 49% | 27% | 7% |
| summon_proc | A10 | 17% | 0% | 0% | 0% | 0% | 0% |
| area_control | A0 | 100% | 77% | 63% | 58% | 46% | 21% |
| area_control | A10 | 0% | 0% | 0% | 0% | 0% | 0% |
| naive_random | A0 | 100% | 92% | 86% | 72% | 54% | 31% |
| naive_random | A10 | 2% | 0% | 0% | 0% | 0% | 0% |

## Where runs end (defeat wave, all bots)
| Wave | Defeats | Share of defeats |
|---|---|---|
| 2 | 1478 | 40.9% |
| 6 | 395 | 10.9% |
| 9 | 237 | 6.6% |
| 7 | 227 | 6.3% |
| 14 | 219 | 6.1% |
| 18 | 198 | 5.5% |

## Anomaly detectors
### Possibly dominant relics (win-rate lift ≥ 1.8 vs runs alive at the same wave without it, n ≥ 30)
- `sanctuary_bell`: n=67, win 34.3% vs 12.7% → lift 2.70
- `tidecaller_pearl`: n=310, win 23.5% vs 9.4% → lift 2.51
- `stoneheart`: n=140, win 25.7% vs 11.1% → lift 2.31
- `overgrowth`: n=112, win 26.8% vs 13.3% → lift 2.02
- `frostbreaker_hammer`: n=208, win 24.0% vs 12.2% → lift 1.97
- `twilight_hourglass`: n=56, win 51.8% vs 26.9% → lift 1.92
- `ocean_heart`: n=312, win 29.8% vs 15.9% → lift 1.87
### Possible trap cards (lift ≤ 0.6, n ≥ 30)
- `spec_vesper_potency`: n=35, win 0.0% vs 16.5% → lift 0.00
- `spec_raiden_afterimage`: n=280, win 1.1% vs 8.7% → lift 0.12
- `spec_veyra_overcharge_ramp`: n=277, win 1.4% vs 9.9% → lift 0.15
- `toxic_shock_theory`: n=121, win 5.0% vs 19.7% → lift 0.25
- `toxic_pact`: n=132, win 4.5% vs 17.7% → lift 0.26
- `spec_sable_triage`: n=105, win 5.7% vs 20.5% → lift 0.28
- `spec_caelis_resonant_echo`: n=404, win 3.7% vs 9.3% → lift 0.40
- `void_covenant`: n=53, win 7.5% vs 14.8% → lift 0.51
- `dawn_vigil`: n=98, win 10.2% vs 19.4% → lift 0.53
- `arcane_accord`: n=552, win 4.7% vs 8.5% → lift 0.55
### Empty/thin draft choices
- 0 of 15053 draft screens offered fewer than 3 cards (0.00%).
### Runaway reaction chains
- Runs where the reaction budget had to block reactions: 5 / 3780 (0.1%); max reactions/s seen: 56; p95 18.
### Proc explosions
- Runs reaching the proc-generation cap (2): 2591; runs where the cap blocked a reaction: 1019 (27.0%). The cap is the safety net; a high share means procs lean on it.
### Excessive stuns
- Runs with a wave where enemies spent > 60% of their alive time hard-CC'd: 0 / 3780 (0.0%). Per bot: mono_element 0%, reaction_chain 0%, tank_healer_stall 0%, boss_burst 0%, summon_proc 0%, area_control 0%, naive_random 0%

Full relic/card lift tables: `relic_lift.csv`, `card_lift.csv`.

## Knob sensitivity (data in economy.json; paired seeds)
| Knob (economy.json) | reaction_chain win | tank_healer_stall win | Δ vs baseline (pp, mean of both) |
|---|---|---|---|
| baseline | 33.3% | 3.3% | — |
| enemyHpGrowth ×0.9 | 46.7% | 0.0% | +5.0 |
| enemyHpGrowth ×1.1 | 26.7% | 0.0% | -5.0 |
| crystalHp ×0.9 | 26.7% | 0.0% | -5.0 |
| crystalHp ×1.1 | 43.3% | 40.0% | +23.3 |

30 paired seeds per bot per knob, default biome, Ascension 0. Small samples: treat deltas under ~10 pp as noise.

