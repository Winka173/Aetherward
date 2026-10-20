using System;
using System.Collections.Generic;
using Aetherward.Sim.Content;

namespace Aetherward.Sim.Run
{
    /// <summary>
    /// Explainable encounter log: what a wave asks of the player, computed from the same data and scaling
    /// rules the battle uses (HP/damage growth by effective level, Ascension, loop scaling, elite multiplier).
    /// Used by the Balance CLI (--encounters) to find budget spikes and by the soak test to sanity-check
    /// generated (Endless / Boss Rush) waves. It never changes a wave.
    /// </summary>
    public sealed class EncounterEntry
    {
        public int Wave;
        public int Level;
        public int Enemies;
        public int Elites;
        public int Bosses;
        public int ThreatPoints;        // Σ EnemyDef.Threat (elite ×2, boss ×4)
        public float EffectiveHp;       // Σ scaled HP the heroes must remove
        public float CrystalPressure;   // Σ scaled Crystal damage if every enemy reached it
        public float Duration;          // seconds from first to last spawn
        public float Density;           // enemies per second of spawning
        public readonly SortedDictionary<string, int> Behaviors = new SortedDictionary<string, int>(StringComparer.Ordinal);
        public readonly List<string> Affixes = new List<string>();
        public string Flag;             // "spike", "dip" or null (vs previous wave)
    }

    public static class EncounterReport
    {
        public const float SpikeRatio = 1.6f;
        public const float DipRatio = 0.6f;

        public static EncounterEntry Analyze(ContentDatabase db, WaveDef w, int ascension)
        {
            EconomyDef eco = db.Economy;
            int lvl = w.EffectiveLevel - 1;
            float asc = 1f + db.Difficulty.HpPerLevel * ascension * db.Difficulty.LevelBonusShare(w.EffectiveLevel);
            float hpScale = (1f + eco.EnemyHpGrowth * lvl + eco.EnemyHpGrowthQuad * lvl * lvl) * asc * (1f + w.ScalePct);
            float dmgScale = (1f + eco.EnemyDamageGrowth * lvl) * asc * (1f + w.ScalePct * 0.5f);
            var e = new EncounterEntry { Wave = w.Number, Level = w.EffectiveLevel };
            float first = float.MaxValue, last = 0f;
            foreach (SpawnGroup g in w.Groups)
            {
                string id = g.Enemy;
                if (db.Enemies.TryGetValue(id, out EnemyDef probe) && probe.Boss && w.BossPool.Count > 0) id = w.BossPool[0];
                if (!db.Enemies.TryGetValue(id, out EnemyDef d) || g.Count <= 0) continue;
                bool elite = g.Elite && !d.Elite && !d.Boss;
                e.Enemies += g.Count;
                if (elite || d.Elite) e.Elites += g.Count;
                if (d.Boss) e.Bosses += g.Count;
                e.ThreatPoints += g.Count * Math.Max(1, d.Threat) * (d.Boss ? 4 : elite ? 2 : 1);
                e.EffectiveHp += g.Count * d.Hp * hpScale * (elite ? 3.5f : 1f);
                e.CrystalPressure += g.Count * d.CrystalDamage * dmgScale;
                string b = d.Behavior.ToString();
                e.Behaviors.TryGetValue(b, out int n);
                e.Behaviors[b] = n + g.Count;
                if (!string.IsNullOrEmpty(g.Affix) && !e.Affixes.Contains(g.Affix)) e.Affixes.Add(g.Affix);
                first = Math.Min(first, g.Start);
                last = Math.Max(last, g.Start + (g.Count - 1) * g.Interval);
            }
            e.Duration = e.Enemies > 0 ? Math.Max(0.5f, last - first) : 0f;
            e.Density = e.Duration > 0f ? e.Enemies / e.Duration : 0f;
            return e;
        }

        /// <summary>Analyzes waves 1..count of a run's mode and flags non-boss budget jumps between neighbours.</summary>
        public static List<EncounterEntry> ForRun(RunController rc, int count)
        {
            var list = new List<EncounterEntry>();
            EncounterEntry prev = null;
            for (int i = 1; i <= count; i++)
            {
                EncounterEntry e = Analyze(rc.Content, rc.WaveAt(i), rc.State.Ascension);
                if (prev != null && prev.EffectiveHp > 0f && e.Bosses == 0 && prev.Bosses == 0)
                {
                    float r = e.EffectiveHp / prev.EffectiveHp;
                    if (r >= SpikeRatio) e.Flag = "spike";
                    else if (r <= DipRatio) e.Flag = "dip";
                }
                list.Add(e);
                prev = e;
            }
            return list;
        }
    }
}
