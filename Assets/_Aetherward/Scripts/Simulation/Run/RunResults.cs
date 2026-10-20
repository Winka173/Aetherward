using System.Collections.Generic;
using Aetherward.Sim.Content;

namespace Aetherward.Sim.Run
{
    public sealed class HeroResult
    {
        public string HeroId;
        public string EvolutionId;
        public int Level;
        public float DamageDealt;
        public float HealingDone;
        public int Kills;
        public int Reactions;
        public int TimesDowned;
    }

    public sealed class RankedEntry
    {
        public string Id;
        public float Value;
        public int Count;
    }

    /// <summary>Post-run report: what the build was and why it worked or failed.</summary>
    public sealed class RunResults
    {
        public bool Victory;
        public int WaveReached;
        public string Seed;
        public string GameVersion;
        public int Ascension;
        public float ActiveSeconds;
        public float CrystalHpFraction;
        public string DefeatSource;
        public int TotalReactions;
        public int TotalKills;
        public float GoldEarned;
        public float GoldSpent;
        public readonly List<HeroResult> Heroes = new List<HeroResult>();
        public readonly List<RankedEntry> Reactions = new List<RankedEntry>();
        public readonly List<RankedEntry> Sources = new List<RankedEntry>();
        public readonly float[] ElementDamage = new float[ElementUtil.Count];
        public readonly List<string> Relics = new List<string>();
        public readonly List<string> Cards = new List<string>();
        public readonly List<WaveRecord> Waves = new List<WaveRecord>();
        public string StrongestReaction;
        public string MvpHero;
        // Run breakdown (Phase 8): provenance split, prevention and the run's turning points.
        public readonly float[] DamageByKind = new float[6];
        public float ShieldAbsorbed;
        public int MaxProcDepth;
        public string MostDamagingThreat;
        public float MostDamagingThreatDamage;
        public int ClosestSaveWave;
        public float ClosestSaveHpFraction = 1f;
        public string DecisiveUpgrade;
        public readonly List<string> FinalInsights = new List<string>();   // Battle Insights of the last wave played
        public string ShareCode;
        public float MenuSeconds;
        public float DecisiveUpgradeDamage;
        public readonly List<string> Insights = new List<string>(); // localization keys with {0} args encoded as key|arg

        public static RunResults Build(RunController rc)
        {
            RunState s = rc.State;
            var r = new RunResults
            {
                Victory = s.Phase == RunPhase.Victory,
                WaveReached = s.Wave,
                Seed = Core.Pcg32.FormatSeed(s.Seed),
                GameVersion = s.GameVersion,
                Ascension = s.Ascension,
                ActiveSeconds = s.ActiveSeconds,
                CrystalHpFraction = rc.CrystalMaxHp > 0 ? s.CrystalHp / rc.CrystalMaxHp : 0f,
                DefeatSource = s.DefeatSource,
                GoldEarned = s.GoldEarnedTotal,
                GoldSpent = s.GoldSpentTotal
            };
            float best = -1f;
            foreach (HeroRunState h in s.Heroes)
            {
                r.Heroes.Add(new HeroResult
                {
                    HeroId = h.DefId,
                    EvolutionId = h.EvolutionId,
                    Level = h.Level,
                    DamageDealt = h.DamageDealt,
                    HealingDone = h.HealingDone,
                    Kills = h.Kills,
                    Reactions = h.Reactions,
                    TimesDowned = h.TimesDowned
                });
                float score = h.DamageDealt + h.HealingDone * 1.5f;
                if (score > best) { best = score; r.MvpHero = h.DefId; }
                r.TotalKills += h.Kills;
            }
            float bestReaction = -1f;
            foreach (var kv in s.ReactionCounts)
            {
                s.ReactionDamage.TryGetValue(kv.Key, out float dmg);
                r.Reactions.Add(new RankedEntry { Id = kv.Key, Count = kv.Value, Value = dmg });
                r.TotalReactions += kv.Value;
                if (dmg > bestReaction) { bestReaction = dmg; r.StrongestReaction = kv.Key; }
            }
            r.Reactions.Sort((a, b) => b.Value.CompareTo(a.Value));
            foreach (var kv in s.SourceActivations)
            {
                s.SourceDamage.TryGetValue(kv.Key, out float dmg);
                r.Sources.Add(new RankedEntry { Id = kv.Key, Count = kv.Value, Value = dmg });
            }
            r.Sources.Sort((a, b) => b.Count.CompareTo(a.Count));
            for (int i = 0; i < s.ElementDamage.Length; i++) r.ElementDamage[i] = s.ElementDamage[i];
            for (int i = 0; i < s.DamageByKind.Length; i++) r.DamageByKind[i] = s.DamageByKind[i];
            r.ShieldAbsorbed = s.ShieldAbsorbed;
            r.MaxProcDepth = s.MaxProcDepth;
            foreach (var kv in s.CrystalDamageByEnemy)
                if (kv.Value > r.MostDamagingThreatDamage) { r.MostDamagingThreatDamage = kv.Value; r.MostDamagingThreat = kv.Key; }
            float max = rc.CrystalMaxHp;
            foreach (WaveRecord w in s.WaveLog)
                if (w.Cleared && max > 0f && w.CrystalHpAfter / max < r.ClosestSaveHpFraction) { r.ClosestSaveHpFraction = w.CrystalHpAfter / max; r.ClosestSaveWave = w.Wave; }
            // Decisive upgrade: the relic/card/bond whose own effects dealt the most damage (attributed via SourceTag).
            foreach (var kv in s.SourceDamage)
                if (kv.Value > r.DecisiveUpgradeDamage) { r.DecisiveUpgradeDamage = kv.Value; r.DecisiveUpgrade = kv.Key; }
            r.ShareCode = rc.ShareCode();
            if (s.WaveLog.Count > 0) r.FinalInsights.AddRange(s.WaveLog[s.WaveLog.Count - 1].Insights);
            r.MenuSeconds = s.MenuSeconds;
            r.Relics.AddRange(s.Relics);
            r.Cards.AddRange(s.CardOrder);
            r.Waves.AddRange(s.WaveLog);
            r.BuildInsights(rc);
            return r;
        }

        private void BuildInsights(RunController rc)
        {
            RunState s = rc.State;
            float total = 0f, reactionTotal = 0f;
            for (int i = 0; i < ElementDamage.Length; i++) total += ElementDamage[i];
            foreach (RankedEntry e in Reactions) reactionTotal += e.Value;
            if (total > 0f && reactionTotal / total > 0.3f) Insights.Add("insight.reaction_engine|" + (int)(reactionTotal / total * 100f));
            if (StrongestReaction != null) Insights.Add("insight.strongest_reaction|" + StrongestReaction);
            int leaks = 0, downs = 0;
            float worst = 0f;
            int worstWave = 0;
            foreach (WaveRecord w in Waves)
            {
                leaks += w.Leaks;
                downs += w.HeroDowns;
                if (w.CrystalDamage > worst) { worst = w.CrystalDamage; worstWave = w.Wave; }
            }
            if (worstWave > 0) Insights.Add("insight.worst_wave|" + worstWave);
            if (leaks > 15) Insights.Add("insight.many_leaks|" + leaks);
            if (downs > 6) Insights.Add("insight.fragile_team|" + downs);
            if (!Victory && DefeatSource != null) Insights.Add("insight.defeated_by|" + DefeatSource);
            if (s.Heroes.Count < 4) Insights.Add("insight.small_roster|" + s.Heroes.Count);
        }
    }
}
