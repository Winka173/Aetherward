# Balance lab (playstyle bots × biomes × Ascension)

> Bots, not players. Seeds are paired across bots/biomes/ascensions. Lifts are associations, not causes.

- Runs: **3780** = 7 bots × 6 biomes × 3 Ascension levels × 30 seeds; 78s on 4 threads (Intel(R) Xeon(R) Processor @ 2.10GHz)
- Content hash `8277f76cb260854e`; command `dotnet run --project Tools/SimHarness/Balance -c Release -- --lab --seeds 30`
- Bot mapping: mono_element = mono_fire, reaction_chain = thunderstorm, tank_healer_stall = stall, boss_burst = boss_burst, summon_proc = summon_proc, area_control = frozen_fortress, naive_random = balanced (random drafting)

## Clear rate by bot × Ascension (95% Wilson CI)
| Bot | A0 | A5 | A10 |
|---|---|---|---|
| mono_element | 10.0% [6–15] n=180 | 2.8% [1–6] n=180 | 0.0% [0–2] n=180 |
| reaction_chain | 21.7% [16–28] n=180 | 2.2% [1–6] n=180 | 0.0% [0–2] n=180 |
| tank_healer_stall | 22.8% [17–29] n=180 | 2.8% [1–6] n=180 | 0.6% [0–3] n=180 |
| boss_burst | 0.6% [0–3] n=180 | 0.0% [0–2] n=180 | 0.0% [0–2] n=180 |
| summon_proc | 6.7% [4–11] n=180 | 0.6% [0–3] n=180 | 0.0% [0–2] n=180 |
| area_control | 23.9% [18–31] n=180 | 6.1% [3–11] n=180 | 0.6% [0–3] n=180 |
| naive_random | 24.4% [19–31] n=180 | 5.0% [3–9] n=180 | 2.8% [1–6] n=180 |

## Clear rate by bot × biome (all Ascensions pooled)
| Bot | verdant_sanctuary | molten_crater | frostfall_bastion | shattered_aether | stormspire_citadel | sunken_archive |
|---|---|---|---|---|---|---|
| mono_element | 5.6% [2–12] n=90 | 4.4% [2–11] n=90 | 3.3% [1–9] n=90 | 4.4% [2–11] n=90 | 3.3% [1–9] n=90 | 4.4% [2–11] n=90 |
| reaction_chain | 6.7% [3–14] n=90 | 12.2% [7–21] n=90 | 3.3% [1–9] n=90 | 10.0% [5–18] n=90 | 6.7% [3–14] n=90 | 8.9% [5–17] n=90 |
| tank_healer_stall | 12.2% [7–21] n=90 | 11.1% [6–19] n=90 | 6.7% [3–14] n=90 | 8.9% [5–17] n=90 | 6.7% [3–14] n=90 | 6.7% [3–14] n=90 |
| boss_burst | 1.1% [0–6] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 |
| summon_proc | 2.2% [1–8] n=90 | 4.4% [2–11] n=90 | 2.2% [1–8] n=90 | 2.2% [1–8] n=90 | 2.2% [1–8] n=90 | 1.1% [0–6] n=90 |
| area_control | 8.9% [5–17] n=90 | 17.8% [11–27] n=90 | 8.9% [5–17] n=90 | 10.0% [5–18] n=90 | 5.6% [2–12] n=90 | 10.0% [5–18] n=90 |
| naive_random | 11.1% [6–19] n=90 | 13.3% [8–22] n=90 | 8.9% [5–17] n=90 | 10.0% [5–18] n=90 | 6.7% [3–14] n=90 | 14.4% [9–23] n=90 |

## 20-wave clear curve (share of runs alive at the start of the wave, A0 / A10)
| Bot | Asc | w5 | w10 | w14 | w15 | w18 | w20 |
|---|---|---|---|---|---|---|---|
| mono_element | A0 | 100% | 96% | 78% | 54% | 31% | 10% |
| mono_element | A10 | 100% | 32% | 12% | 6% | 2% | 0% |
| reaction_chain | A0 | 100% | 97% | 88% | 76% | 67% | 23% |
| reaction_chain | A10 | 100% | 44% | 26% | 14% | 8% | 0% |
| tank_healer_stall | A0 | 100% | 84% | 77% | 57% | 44% | 26% |
| tank_healer_stall | A10 | 97% | 22% | 14% | 9% | 5% | 1% |
| boss_burst | A0 | 100% | 74% | 53% | 24% | 13% | 1% |
| boss_burst | A10 | 99% | 9% | 0% | 0% | 0% | 0% |
| summon_proc | A0 | 100% | 94% | 74% | 49% | 27% | 7% |
| summon_proc | A10 | 100% | 17% | 5% | 2% | 1% | 0% |
| area_control | A0 | 100% | 84% | 67% | 63% | 44% | 25% |
| area_control | A10 | 100% | 27% | 11% | 8% | 4% | 1% |
| naive_random | A0 | 100% | 93% | 87% | 73% | 54% | 29% |
| naive_random | A10 | 100% | 38% | 11% | 7% | 5% | 3% |

## Where runs end (defeat wave, all bots)
| Wave | Defeats | Share of defeats |
|---|---|---|
| 9 | 619 | 17.5% |
| 14 | 530 | 15.0% |
| 12 | 502 | 14.2% |
| 18 | 334 | 9.4% |
| 6 | 320 | 9.0% |
| 7 | 277 | 7.8% |

## Anomaly detectors
### Possibly dominant relics (win-rate lift ≥ 1.8 vs runs alive at the same wave without it, n ≥ 30)
- `sanctuary_bell`: n=124, win 25.8% vs 9.1% → lift 2.85
- `living_monolith`: n=53, win 75.5% vs 27.7% → lift 2.72
- `tidecaller_pearl`: n=628, win 16.9% vs 7.9% → lift 2.15
- `stoneheart`: n=289, win 18.3% vs 9.0% → lift 2.04
- `crystal_growth`: n=150, win 24.7% vs 12.3% → lift 2.00
- `frostbreaker_hammer`: n=432, win 20.4% vs 10.7% → lift 1.91
- `mana_battery`: n=315, win 23.8% vs 12.9% → lift 1.84
### Possible trap cards (lift ≤ 0.6, n ≥ 30)
- `spec_vesper_potency`: n=66, win 0.0% vs 10.8% → lift 0.00
- `spec_raiden_afterimage`: n=445, win 1.8% vs 8.6% → lift 0.21
- `toxic_shock_theory`: n=216, win 3.2% vs 14.5% → lift 0.22
- `toxic_pact`: n=234, win 3.0% vs 12.6% → lift 0.24
- `spec_sable_triage`: n=197, win 3.6% vs 14.9% → lift 0.24
- `spec_veyra_overcharge_ramp`: n=454, win 2.9% vs 9.2% → lift 0.31
- `spec_caelis_resonant_echo`: n=557, win 3.1% vs 9.0% → lift 0.34
- `void_covenant`: n=98, win 4.1% vs 10.2% → lift 0.40
- `spec_isolde_deep_cold`: n=66, win 7.6% vs 15.1% → lift 0.50
- `arcane_accord`: n=744, win 4.7% vs 8.9% → lift 0.53
### Empty/thin draft choices
- 0 of 25344 draft screens offered fewer than 3 cards (0.00%).
### Runaway reaction chains
- Runs where the reaction budget had to block reactions: 7 / 3780 (0.2%); max reactions/s seen: 52; p95 22.
### Proc explosions
- Runs reaching the proc-generation cap (2): 3680; runs where the cap blocked a reaction: 1852 (49.0%). The cap is the safety net; a high share means procs lean on it.
### Excessive stuns
- Runs with a wave where enemies spent > 60% of their alive time hard-CC'd: 2 / 3780 (0.1%). Per bot: mono_element 0%, reaction_chain 0%, tank_healer_stall 0%, boss_burst 0%, summon_proc 0%, area_control 0%, naive_random 0%

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

