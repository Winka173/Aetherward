using System.Collections.Generic;
using Aetherward.Sim.Content;

namespace Aetherward.Sim.Combat
{
    public sealed class SourcedOp
    {
        public EffectOp Op;
        public string Source;     // content id of the relic/card/evolution/pact (for stats only)
        public int Stacks = 1;
    }

    public sealed class ReactionMod
    {
        public float DamagePct;
        public float RadiusPct;
        public float DurationPct;
        public float Bounces;     // electrocharge / chain extras
        public float StatusPct;   // control strength (freeze/slow/pull)
    }

    /// <summary>Runtime state for a trigger op inside one battle (counters, internal cooldowns).</summary>
    public sealed class TriggerInstance
    {
        public SourcedOp Source;
        public int Counter;
        public float Cooldown;
        public int UsesThisWave;
    }

    /// <summary>
    /// Flattened view of every active effect op for one battle. Rebuilt from the run state before each
    /// wave, so nothing leaks between waves or runs (spec: no ghost buffs).
    /// </summary>
    public sealed class BattleModifiers
    {
        public readonly List<SourcedOp> StatOps = new List<SourcedOp>();
        public readonly Dictionary<string, ReactionMod> Reactions = new Dictionary<string, ReactionMod>();
        public readonly List<SourcedOp> Triggers = new List<SourcedOp>();
        public readonly Dictionary<string, float> Rules = new Dictionary<string, float>();
        public readonly float[] GaugeMult = { 1f, 1f, 1f, 1f, 1f, 1f, 1f };
        public float CrystalMaxHpPct;
        public float CrystalMaxHpFlat;
        public float CrystalRegen;
        public float CrystalReduction;
        public float CrystalThorns;
        public float EnemyHpPct;
        public float EnemySpeedPct;
        public float EnemyDamagePct;
        public float EnemyGoldPct;
        public float HealingPct;
        public float ReactionDamageAll;

        public float Rule(string key) => Rules.TryGetValue(key, out float v) ? v : 0f;
        public bool HasRule(string key) => Rules.ContainsKey(key);

        public ReactionMod ModFor(string reactionId)
        {
            Reactions.TryGetValue(reactionId, out ReactionMod m);
            return m;
        }

        public void Add(EffectOp op, string source, int stacks = 1)
        {
            var s = new SourcedOp { Op = op, Source = source, Stacks = stacks };
            switch (op.Op)
            {
                case "stat":
                    StatOps.Add(s);
                    break;
                case "reaction":
                {
                    string key = string.IsNullOrEmpty(op.Reaction) ? "*" : op.Reaction;
                    if (!Reactions.TryGetValue(key, out ReactionMod m)) Reactions[key] = m = new ReactionMod();
                    m.DamagePct += op.Params.Get("damagePct") * stacks;
                    m.RadiusPct += op.Params.Get("radiusPct") * stacks;
                    m.DurationPct += op.Params.Get("durationPct") * stacks;
                    m.Bounces += op.Params.Get("bounces") * stacks;
                    m.StatusPct += op.Params.Get("statusPct") * stacks;
                    break;
                }
                case "trigger":
                    Triggers.Add(s);
                    break;
                case "rule":
                    Rules.TryGetValue(op.Rule, out float existing);
                    Rules[op.Rule] = existing + (op.Value != 0f ? op.Value : 1f) * stacks;
                    // Rules may carry named extra parameters ("rule.param").
                    foreach (string k in op.Params.NumberKeys)
                    {
                        string rk = op.Rule + "." + k;
                        Rules.TryGetValue(rk, out float e2);
                        Rules[rk] = e2 + op.Params.Get(k) * stacks;
                    }
                    break;
                case "crystal":
                    CrystalMaxHpPct += op.Params.Get("maxHpPct") * stacks;
                    CrystalMaxHpFlat += op.Params.Get("maxHp") * stacks;
                    CrystalRegen += op.Params.Get("regen") * stacks;
                    CrystalReduction += op.Params.Get("reduction") * stacks;
                    CrystalThorns += op.Params.Get("thorns") * stacks;
                    break;
                case "enemy":
                    EnemyHpPct += op.Params.Get("hpPct") * stacks;
                    EnemySpeedPct += op.Params.Get("speedPct") * stacks;
                    EnemyDamagePct += op.Params.Get("damagePct") * stacks;
                    EnemyGoldPct += op.Params.Get("goldPct") * stacks;
                    break;
                case "gauge":
                {
                    string el = op.Params.GetString("element");
                    float v = op.Params.Get("pct") * stacks;
                    if (string.IsNullOrEmpty(el) || el == "all")
                        for (int i = 1; i < GaugeMult.Length; i++) GaugeMult[i] += v;
                    else
                        GaugeMult[(int)ContentDatabase.ParseElement(el)] += v;
                    break;
                }
                case "healing":
                    HealingPct += op.Params.Get("pct") * stacks;
                    break;
                case "economy":
                    // Economy ops are consumed by the run layer, not the battle.
                    break;
            }
        }
    }
}
