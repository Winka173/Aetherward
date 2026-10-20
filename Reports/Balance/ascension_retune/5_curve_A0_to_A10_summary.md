# Balance lab (playstyle bots × biomes × Ascension)

> Bots, not players. Seeds are paired across bots/biomes/ascensions. Lifts are associations, not causes.

- Runs: **6930** = 7 bots × 6 biomes × 11 Ascension levels × 15 seeds; 127s on 4 threads (Intel(R) Xeon(R) Processor @ 2.10GHz)
- Content hash `24626885b09af150`; command `dotnet run --project Tools/SimHarness/Balance -c Release -- --lab --seeds 15`
- Bot mapping: mono_element = mono_fire, reaction_chain = thunderstorm, tank_healer_stall = stall, boss_burst = boss_burst, summon_proc = summon_proc, area_control = frozen_fortress, naive_random = balanced (random drafting)

## Clear rate by bot × Ascension (95% Wilson CI)
| Bot | A0 | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mono_element | 11.1% [6–19] n=90 | 10.0% [5–18] n=90 | 4.4% [2–11] n=90 | 5.6% [2–12] n=90 | 4.4% [2–11] n=90 | 4.4% [2–11] n=90 | 1.1% [0–6] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 |
| reaction_chain | 12.2% [7–21] n=90 | 7.8% [4–15] n=90 | 4.4% [2–11] n=90 | 2.2% [1–8] n=90 | 0.0% [0–4] n=90 | 1.1% [0–6] n=90 | 1.1% [0–6] n=90 | 1.1% [0–6] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 |
| tank_healer_stall | 16.7% [10–26] n=90 | 15.6% [9–24] n=90 | 12.2% [7–21] n=90 | 3.3% [1–9] n=90 | 0.0% [0–4] n=90 | 1.1% [0–6] n=90 | 0.0% [0–4] n=90 | 2.2% [1–8] n=90 | 1.1% [0–6] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 |
| boss_burst | 1.1% [0–6] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 |
| summon_proc | 11.1% [6–19] n=90 | 8.9% [5–17] n=90 | 4.4% [2–11] n=90 | 0.0% [0–4] n=90 | 1.1% [0–6] n=90 | 1.1% [0–6] n=90 | 1.1% [0–6] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 |
| area_control | 28.9% [21–39] n=90 | 21.1% [14–31] n=90 | 17.8% [11–27] n=90 | 14.4% [9–23] n=90 | 12.2% [7–21] n=90 | 8.9% [5–17] n=90 | 13.3% [8–22] n=90 | 10.0% [5–18] n=90 | 2.2% [1–8] n=90 | 0.0% [0–4] n=90 | 0.0% [0–4] n=90 |
| naive_random | 15.6% [9–24] n=90 | 11.1% [6–19] n=90 | 12.2% [7–21] n=90 | 5.6% [2–12] n=90 | 3.3% [1–9] n=90 | 2.2% [1–8] n=90 | 1.1% [0–6] n=90 | 3.3% [1–9] n=90 | 5.6% [2–12] n=90 | 3.3% [1–9] n=90 | 2.2% [1–8] n=90 |

## Clear rate by bot × biome (all Ascensions pooled)
| Bot | verdant_sanctuary | molten_crater | frostfall_bastion | shattered_aether | stormspire_citadel | sunken_archive |
|---|---|---|---|---|---|---|
| mono_element | 4.8% [2–9] n=165 | 1.8% [1–5] n=165 | 3.6% [2–8] n=165 | 4.2% [2–8] n=165 | 3.6% [2–8] n=165 | 4.2% [2–8] n=165 |
| reaction_chain | 2.4% [1–6] n=165 | 6.7% [4–12] n=165 | 0.0% [0–2] n=165 | 3.0% [1–7] n=165 | 2.4% [1–6] n=165 | 1.8% [1–5] n=165 |
| tank_healer_stall | 6.1% [3–11] n=165 | 7.3% [4–12] n=165 | 4.8% [2–9] n=165 | 3.0% [1–7] n=165 | 3.0% [1–7] n=165 | 4.2% [2–8] n=165 |
| boss_burst | 0.6% [0–3] n=165 | 0.0% [0–2] n=165 | 0.0% [0–2] n=165 | 0.0% [0–2] n=165 | 0.0% [0–2] n=165 | 0.0% [0–2] n=165 |
| summon_proc | 2.4% [1–6] n=165 | 3.6% [2–8] n=165 | 1.8% [1–5] n=165 | 2.4% [1–6] n=165 | 2.4% [1–6] n=165 | 2.4% [1–6] n=165 |
| area_control | 10.9% [7–17] n=165 | 18.2% [13–25] n=165 | 10.9% [7–17] n=165 | 10.9% [7–17] n=165 | 7.9% [5–13] n=165 | 11.5% [7–17] n=165 |
| naive_random | 4.8% [2–9] n=165 | 10.9% [7–17] n=165 | 4.2% [2–8] n=165 | 4.8% [2–9] n=165 | 4.2% [2–8] n=165 | 6.7% [4–12] n=165 |

## 20-wave clear curve (share of runs alive at the start of the wave, A0 / A10)
| Bot | Asc | w5 | w10 | w14 | w15 | w18 | w20 |
|---|---|---|---|---|---|---|---|
| mono_element | A0 | 100% | 91% | 66% | 46% | 24% | 11% |
| mono_element | A10 | 100% | 29% | 9% | 6% | 0% | 0% |
| reaction_chain | A0 | 100% | 97% | 89% | 76% | 62% | 14% |
| reaction_chain | A10 | 100% | 23% | 12% | 6% | 3% | 0% |
| tank_healer_stall | A0 | 100% | 81% | 77% | 48% | 33% | 17% |
| tank_healer_stall | A10 | 100% | 19% | 16% | 11% | 4% | 0% |
| boss_burst | A0 | 100% | 74% | 60% | 20% | 11% | 1% |
| boss_burst | A10 | 99% | 7% | 0% | 0% | 0% | 0% |
| summon_proc | A0 | 100% | 94% | 76% | 57% | 34% | 11% |
| summon_proc | A10 | 100% | 12% | 1% | 1% | 1% | 0% |
| area_control | A0 | 100% | 86% | 73% | 69% | 56% | 31% |
| area_control | A10 | 100% | 33% | 14% | 9% | 4% | 0% |
| naive_random | A0 | 100% | 89% | 81% | 67% | 47% | 19% |
| naive_random | A10 | 100% | 33% | 12% | 10% | 6% | 2% |

## Where runs end (defeat wave, all bots)
| Wave | Defeats | Share of defeats |
|---|---|---|
| 9 | 1295 | 19.6% |
| 14 | 971 | 14.7% |
| 12 | 927 | 14.0% |
| 6 | 586 | 8.9% |
| 18 | 579 | 8.7% |
| 7 | 548 | 8.3% |

## Anomaly detectors
### Possibly dominant relics (win-rate lift ≥ 1.8 vs runs alive at the same wave without it, n ≥ 30)
- `living_monolith`: n=118, win 69.5% vs 11.4% → lift 6.11
- `stoneheart`: n=484, win 20.0% vs 3.4% → lift 5.94
- `sun_hymnal`: n=85, win 18.8% vs 5.7% → lift 3.29
- `sanctuary_bell`: n=279, win 18.3% vs 6.2% → lift 2.95
- `frostbreaker_hammer`: n=822, win 18.7% vs 6.7% → lift 2.81
- `crystal_growth`: n=354, win 22.0% vs 8.0% → lift 2.74
- `infinite_codex`: n=195, win 20.0% vs 7.8% → lift 2.55
- `antidote_flask`: n=289, win 13.1% vs 5.6% → lift 2.35
- `mana_battery`: n=265, win 21.1% vs 9.5% → lift 2.23
- `last_stand`: n=80, win 15.0% vs 6.7% → lift 2.22
### Possible trap cards (lift ≤ 0.6, n ≥ 30)
- `dawn_vigil`: n=226, win 0.0% vs 8.9% → lift 0.00
- `eclipse_theory`: n=92, win 0.0% vs 12.4% → lift 0.00
- `night_oath`: n=56, win 0.0% vs 8.5% → lift 0.00
- `spec_elowen_bright_choir`: n=106, win 0.0% vs 9.9% → lift 0.00
- `spec_sable_triage`: n=533, win 0.0% vs 8.5% → lift 0.00
- `spec_vesper_potency`: n=69, win 0.0% vs 7.9% → lift 0.00
- `spec_zerith_event_pull`: n=83, win 0.0% vs 6.4% → lift 0.00
- `toxic_shock_theory`: n=432, win 0.0% vs 10.1% → lift 0.00
- `toxic_pact`: n=511, win 0.2% vs 9.0% → lift 0.02
- `spec_tidal_riptide`: n=256, win 0.8% vs 8.1% → lift 0.10
### Empty/thin draft choices
- 0 of 44846 draft screens offered fewer than 3 cards (0.00%).
### Runaway reaction chains
- Runs where the reaction budget had to block reactions: 7 / 6930 (0.1%); max reactions/s seen: 61; p95 22.
### Proc explosions
- Runs reaching the proc-generation cap (2): 6718; runs where the cap blocked a reaction: 3239 (46.7%). The cap is the safety net; a high share means procs lean on it.
### Excessive stuns
- Runs with a wave where enemies spent > 60% of their alive time hard-CC'd: 2 / 6930 (0.0%). Per bot: mono_element 0%, reaction_chain 0%, tank_healer_stall 0%, boss_burst 0%, summon_proc 0%, area_control 0%, naive_random 0%

Full relic/card lift tables: `relic_lift.csv`, `card_lift.csv`.
