using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    /// <summary>Team tactic presets: soft weights on hero targeting, never hard rules.</summary>
    public enum TeamTactic
    {
        Balanced,
        ProtectCrystal,
        FocusBoss,
        ElementalChain,
        CrowdControl
    }

    /// <summary>Inspectable record of a hero's last targeting decision (AI inspector / debug overlay).</summary>
    public sealed class TargetDecision
    {
        public const int Components = 7;
        public static readonly string[] Names = { "profile", "threat", "kill", "reaction", "priority", "cluster", "reach" };
        public int TargetUid;
        public float Total;
        public readonly float[] Parts = new float[Components];   // weighted contributions of the chosen target
        public int Candidates;
        public int RunnerUpUid;
        public float RunnerUpTotal;
        public bool KeptByHysteresis;
        public string Reason;                                     // "no target in reach" etc.
    }

    /// <summary>
    /// Utility targeting for basic attacks: every candidate in reach gets normalized components
    /// (role profile rank, crystal threat, killability, reaction opportunity, boss/elite priority,
    /// cluster value, reach) weighted by role and the team tactic. Hysteresis keeps the current target
    /// unless a candidate beats it by a margin; ties break by enemy uid (deterministic). Out-of-reach
    /// targets are never considered (no "cheating" AI). Skills keep their own targeting profiles.
    /// </summary>
    public sealed partial class Battle
    {
        public const float TargetHysteresis = 0.15f;

        private static readonly float[] BaseWeights = { 1.0f, 0.6f, 0.3f, 0.3f, 0.2f, 0.1f, 0.3f };

        private float[] WeightsFor(HeroUnit h)
        {
            var w = (float[])BaseWeights.Clone();
            if (h.Role == HeroRole.Guardian) w[1] += 0.4f;
            if (h.Role == HeroRole.Assassin || h.Role == HeroRole.Ranger) w[4] += 0.2f;
            switch (Setup.Tactic)
            {
                case TeamTactic.ProtectCrystal: w[1] += 0.8f; break;
                case TeamTactic.FocusBoss: w[4] += 1.0f; break;
                case TeamTactic.ElementalChain: w[3] += 0.8f; break;
                case TeamTactic.CrowdControl: w[5] += 0.8f; break;
            }
            return w;
        }

        private EnemyUnit SelectTargetUtility(HeroUnit h)
        {
            TargetDecision d = h.Decision ?? (h.Decision = new TargetDecision());
            float range = h.Stat(StatId.Range) + h.Stat(StatId.LeashRadius);
            List<EnemyUnit> c = RentList();
            QueryEnemies(h.Anchor, range, c);
            // Deterministic candidate order: by uid (grid query order depends on cell layout).
            c.Sort((a, b) => a.Uid.CompareTo(b.Uid));
            float[] w = WeightsFor(h);
            int n = 0;
            float bestProfile = float.MinValue, worstProfile = float.MaxValue;
            var profileScores = _profileScratch;
            profileScores.Clear();
            for (int i = 0; i < c.Count && n < 40; i++)
            {
                EnemyUnit e = c[i];
                if (!e.Alive || e.Burrowed) { profileScores.Add(float.NaN); continue; }
                n++;
                float p = ProfileScore(h, h.Targeting, e);
                profileScores.Add(p);
                if (p > bestProfile) bestProfile = p;
                if (p < worstProfile) worstProfile = p;
            }
            EnemyUnit best = null, second = null;
            float bestTotal = float.MinValue, secondTotal = float.MinValue, currentTotal = float.MinValue;
            var parts = _partsScratch;
            for (int i = 0; i < profileScores.Count; i++)
            {
                if (float.IsNaN(profileScores[i])) continue;
                EnemyUnit e = c[i];
                float span = bestProfile - worstProfile;
                parts[0] = w[0] * (span > 1e-4f ? (profileScores[i] - worstProfile) / span : 1f);
                parts[1] = w[1] * SimMath.Clamp(1f - RemainingPath(e) / 20f, 0f, 1f) * (e.Def.Behavior == EnemyBehavior.Sapper || e.Def.Params.Has("siegeRange") ? 1.3f : 1f);
                float hit = h.Stat(StatId.Attack) * h.Basic.Multiplier;
                parts[2] = w[2] * (e.Hp <= hit * 2f ? 1f : SimMath.Clamp(1f - e.HpFraction, 0f, 1f) * 0.6f);
                parts[3] = w[3] * ReactionOpportunity(h.Def.Element, e);
                parts[4] = w[4] * (e.IsBoss ? 1f : e.Elite ? 0.7f : 0f);
                parts[5] = w[5] * SimMath.Min(1f, ClusterScore(e, 1.5f) / 6f);
                parts[6] = w[6] * SimMath.Clamp(1f - Vec2.Distance(h.Pos, e.Pos) / SimMath.Max(1f, range), 0f, 1f);
                float total = 0f;
                for (int k = 0; k < TargetDecision.Components; k++) total += parts[k];
                if (e == h.Target) currentTotal = total;
                if (total > bestTotal)
                {
                    second = best;
                    secondTotal = bestTotal;
                    best = e;
                    bestTotal = total;
                    System.Array.Copy(parts, d.Parts, TargetDecision.Components);
                }
                else if (total > secondTotal)
                {
                    second = e;
                    secondTotal = total;
                }
            }
            ReturnList(c);
            d.Candidates = n;
            d.KeptByHysteresis = false;
            if (best == null)
            {
                d.TargetUid = 0;
                d.Total = 0f;
                d.Reason = "no target in reach";
                return null;
            }
            // Hysteresis: stay on a still-valid current target unless the best is clearly better.
            if (h.Target != null && h.Target.Alive && h.Target != best && currentTotal > float.MinValue && bestTotal < currentTotal + TargetHysteresis)
            {
                d.KeptByHysteresis = true;
                d.RunnerUpUid = best.Uid;
                d.RunnerUpTotal = bestTotal;
                d.TargetUid = h.Target.Uid;
                d.Total = currentTotal;
                d.Reason = "kept current target (hysteresis)";
                return h.Target;
            }
            d.TargetUid = best.Uid;
            d.Total = bestTotal;
            d.RunnerUpUid = second?.Uid ?? 0;
            d.RunnerUpTotal = second != null ? secondTotal : 0f;
            d.Reason = null;
            return best;
        }

        private readonly List<float> _profileScratch = new List<float>(48);
        private readonly float[] _partsScratch = new float[TargetDecision.Components];
    }
}
