# Balance spec (design envelopes are PROPOSALS, measured with bots)

Authoritative rules: one C# simulation shared by the game and `Tools/SimHarness/Balance` (no second engine). Seeds, content hash, policies and machine are logged in every report.

## Lab (`--lab`)
- Bots (not players): mono_element=mono_fire, reaction_chain=thunderstorm, tank_healer_stall=stall, boss_burst, summon_proc, area_control=frozen_fortress, naive_random=balanced+random drafting.
- Matrix: 7 bots × 6 biomes × A0/A5/A10 × 30 paired seeds = 3780 runs (~50 s on 4 threads).
- Metrics: clear rate + Wilson 95% CI by bot×Ascension and bot×biome, 20-wave survival curves, defeat waves, relic/card **lift vs runs alive at the same wave** (corrects survivor bias), thin drafts, reaction-budget blocks, proc-cap usage, hard-CC uptime > 60%, knob sensitivity (economy.json).

## Proposed envelopes (not facts)
| Target | Proposal | Current (bots) |
|---|---|---|
| A0 clear rate per viable archetype | 10–35% | 0.6–24.4% (boss_burst 0.6% fails) |
| No near-mandatory pick | no relic lift > 2.5 with n ≥ 100 | max with n ≥ 100: `tidecaller_pearl` 2.17 (n=453); `sanctuary_bell` 2.75 but n=76 (watch) |
| Impossible early seeds | < 10% of runs end by wave 2 at any Ascension | A10: 336/1260 (27%) after ramp, was 843 |
| A5 / A10 clear rate | > 0% for at least two archetypes | **0% for all** (open, needs design review + human playtests) |
| Runaway chains | budget blocks in < 1% of runs | 0.1% (max 45 reactions/s) |
| Proc cap reliance | cap blocks in < 20% of runs | **35%** (procs lean on the safety cap — review) |
| Thin drafts | 0 | 0 / 18528 screens |
| Excessive stuns | 0 runs with > 60% hard-CC wave | 0 |

## Knobs (data, not constants)
- `economy.json`: enemyHpGrowth, crystalHp, … (sensitivity table in `Reports/Balance/lab/summary.md`).
- `difficulty.json`: hpPerLevel, **earlyRampStart / earlyRampFullWave** (new), modules per level.
- `Battle.CrystalPaths` constants (Crystal Evolution) — documented in UX guide; candidate to move to data.

## Changes applied with evidence
1. Auto Arrange covers an empty lane (stall A0 6.1% → 22.8%; even split rejected because it lowered rates).
2. Ascension early ramp (A10 wave-2 deaths 843 → 336 / 1260; A0 unchanged).
No global nerfs were applied.

## Reading the trap-card list
Lowest lifts are mostly signature cards of the weakest bots (`spec_raiden_afterimage`, `spec_veyra_overcharge_ramp` → boss_burst at 0.6%; `toxic_*`, `spec_sable_triage` → poison bots). The lift measures association with weak archetypes, not proof that the card itself is a trap. Next step: per-archetype paired A/B with and without the card (not done).
