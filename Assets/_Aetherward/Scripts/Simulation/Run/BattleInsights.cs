using System;
using System.Collections.Generic;
using System.Globalization;
using Aetherward.Sim.Combat;

namespace Aetherward.Sim.Run
{
    /// <summary>
    /// Battle Insights (P6): explains what hurt the Crystal using only logged combat data. Each code carries its
    /// evidence (ids and percentages) and a confidence level; when the evidence is thin the code says so
    /// ("low") instead of guessing. Format: "kind|arg1|arg2|...|confidence". Deterministic for a given battle.
    /// </summary>
    public static class BattleInsights
    {
        public const float MinCrystalShare = 0.02f;   // below 2% of max HP the wave is not explained at all

        public static List<string> ForWave(Battle b)
        {
            var codes = new List<string>();
            BattleStats st = b.Stats;
            float total = 0f;
            foreach (float v in st.CrystalDamageByEnemy.Values) total += v;
            bool defeat = b.Outcome == BattleOutcome.CrystalDestroyed;
            if (total < b.Crystal.MaxHp * MinCrystalShare && !defeat) return codes;

            // 1) Which enemy type did the damage.
            string topId = null;
            float topDmg = 0f;
            foreach (var kv in Sorted(st.CrystalDamageByEnemy))
                if (kv.Value > topDmg) { topId = kv.Key; topDmg = kv.Value; }
            if (topId != null && total > 0f)
            {
                int pct = Pct(topDmg, total);
                codes.Add(Join("threat", topId, I(pct), pct >= 50 ? "high" : pct >= 30 ? "medium" : "low"));
            }

            // 2) Which lane was breached, and whether it was covered at the start of the wave.
            int lane = -1;
            float laneDmg = 0f;
            var gateDamage = new Dictionary<int, float>();
            foreach (var kv in st.CrystalDamageByLane)
            {
                int gate = Battle.GateLane(b.Arena, kv.Key);
                gateDamage.TryGetValue(gate, out float damage);
                gateDamage[gate] = damage + kv.Value;
            }
            foreach (var kv in gateDamage)
                if (kv.Value > laneDmg || (Math.Abs(kv.Value - laneDmg) < 1e-3f && kv.Key < lane)) { lane = kv.Key; laneDmg = kv.Value; }
            if (lane >= 0 && total > 0f && laneDmg / total >= 0.5f)
            {
                SynergyReport cov = SynergyReport.Analyze(new Battle(b.Setup), null, includeDowned: true);
                int covPct = (b.Arena.IsHaven ? cov.GateCoverage : cov.LaneCoverage).TryGetValue(lane, out float c) ? Pct(c, 1f) : -1;
                // Low coverage is direct evidence of a positional gap; high coverage points elsewhere (damage, CC).
                codes.Add(Join(b.Arena.IsHaven ? "gate" : "lane", I(lane), I(Pct(laneDmg, total)), I(covPct), covPct >= 0 && covPct < 35 ? "high" : "low"));
            }

            // 3) Did the defensive line collapse first?
            if (st.FirstGuardianDown != null && total > 0f)
            {
                int after = Pct(st.CrystalDamageAfterGuardianDown, total);
                if (after >= 35)
                    codes.Add(Join("tank", st.FirstGuardianDown, st.FirstGuardianDownTime.ToString("F0", CultureInfo.InvariantCulture), I(after), after >= 60 ? "high" : "medium"));
            }

            // 4) Ran out of time (leftover enemies forced through).
            if (st.TimeoutBreaches > 0) codes.Add(Join("timeout", I(st.TimeoutBreaches), "high"));

            if (defeat && codes.Count == 0) codes.Add(Join("no_evidence", "low"));
            return codes;
        }

        private static IEnumerable<KeyValuePair<string, float>> Sorted(Dictionary<string, float> d)
        {
            var list = new List<KeyValuePair<string, float>>(d);
            list.Sort((a, c) => string.CompareOrdinal(a.Key, c.Key));
            return list;
        }

        private static int Pct(float part, float whole) => whole > 0f ? (int)Math.Round(100.0 * part / whole) : 0;
        private static string I(int v) => v.ToString(CultureInfo.InvariantCulture);
        private static string Join(params string[] parts) => string.Join("|", parts);

        /// <summary>Parses a code into kind, args and confidence (for the view and tests).</summary>
        public static (string kind, string[] args, string confidence) Parse(string code)
        {
            string[] p = code.Split('|');
            var args = new string[Math.Max(0, p.Length - 2)];
            Array.Copy(p, 1, args, 0, args.Length);
            return (p[0], args, p[p.Length - 1]);
        }
    }
}
