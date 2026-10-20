# A/B — Ascension retune (A5/A10 were 0% for every bot)

Bots, not players. Seeds are paired. Before = `Reports/Balance/lab_before_asc_retune/`, after = `Reports/Balance/lab/`.
Command: `dotnet run --project Tools/SimHarness/Balance -c Release -- --lab --seeds 30` (7 bots × 6 biomes × 30 seeds per level).

## 1. Result (official lab, 1260 runs per level)
| Level | Before: all bots | Before: best bot | Before: mean wave | After: all bots | After: best bot | After: mean wave |
|---|---|---|---|---|---|---|
| A0 | 15.7% | 24.4% | 15.4 | 15.7% | 24.4% | 15.4 (unchanged: the retune touches Ascension data only) |
| A5 | **0.0%** | 0.0% | 7.7 | **2.8%** | 6.1% | 12.8 |
| A10 | **0.0%** | 0.0% | 3.9 | **0.6%** | 2.8% | 9.2 |

Full curve A0..A10 (15 seeds, `ascension_retune/5_curve_A0_to_A10.txt`): the mean wave reached falls at every level
(15.3 → 14.5 → 14.1 → 13.3 → 12.8 → 12.6 → 11.9 → 10.4 → 10.0 → 9.4 → 8.9). Each level is harder than the one below it.
Clear rate falls from 13.8% to 0.3% (best bot 28.9% → 2.2%). The A5/A6 best-bot values (8.9% / 13.3%) overlap within their 95% CI.

## 2. Diagnosis (ablation, `Reports/Balance/ascension_retune/`)
Tool: `--lab --ablation` (new), which removes one difficulty knob per row.
1. **No single module is the culprit** (`1_ablation_old_difficulty.md`). Removing any one module leaves A5 at ≤0.2%.
2. **The sim is very sensitive to enemy strength** (`2_candidates_A0_A5_A10.md`):
   - +40% HP/damage alone (A5 × 8%/level, no modules) takes A5 from 13.8% to 1.1%.
   - The modules alone (hpPerLevel 0) take it to 2.2%.
   - At A0, bots only reach a median of wave 16, so the run is close to a "power check" and small multipliers have a large effect.
3. **On a softened base, A10 depends mostly on** (`4_ablation_on_soft_base_A10.md`):
   - `double_elite`: median wave 7 → 12 when removed;
   - `blocked_node`;
   - `enemy_damage`;
   - `crystal_max`.

## 3. Change (`difficulty.json`, data only; no code or rules changed)
| Knob | Before | After |
|---|---|---|
| hpPerLevel (HP and damage per level) | 0.08 | **0.01** |
| A2 enemy_speed | +8% | +4% |
| A3 crystal_max | −15% | −8% |
| A4 enemy_damage | +10% | +5% |
| A6 enemy_hp | +10% | +5% |
| A7 double_elite | every 8th | every 14th |
| A8 crystal_max | −10% | −5% |
| A9 enemy_damage | +10% | +5% |
| A10 enemy_hp | +10% | +5% |

Unchanged:
- **Rule modules:** frenzy, shop prices, blocked node, elite affix, boss enrage, reroll cost, rarity shift, hazard shift.
- **Early ramp.**

Ascension descriptions are updated in EN and VI (`team.ascension_desc.*`). Two tests that pinned the old values are updated to the new ones.

## 4. Limits
- Bots are weaker than players, so human A10 clear rates will be higher. Targets need human playtests.
- Relic and card anomaly lists are unchanged by this retune and still need a separate review: dominant `living_monolith` and `sanctuary_bell`; trap cards `spec_vesper_potency` and `toxic_pact`.
