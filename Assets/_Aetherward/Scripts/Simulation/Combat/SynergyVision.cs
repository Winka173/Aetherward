using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    public enum SynergyKind
    {
        Reaction,   // primer element + trigger element of two heroes form a reaction rule
        Buff,       // a hero's support passive reaches an ally
        Bond,       // authored hero bond is active
        Conflict    // the two heroes work against each other under a stated condition
    }

    /// <summary>One explained connection between two deployed heroes (indices into Battle.Heroes).</summary>
    public sealed class SynergyLink
    {
        public SynergyKind Kind;
        public int A, B;
        public string RuleId;        // "reaction:vaporize", "buff:bulwark", "bond:steam_engine", "conflict:knock_vs_melee"
        public bool Active;          // false = conditional (see Condition)
        public string Condition;     // null, or why it does not apply yet: "ranges_apart", "outside_aura"
        public float Distance;       // between the two anchors (world units)
    }

    /// <summary>
    /// Pre-wave team synergy visualisation data (P1). Built from a real Battle constructed for the current
    /// formation, so ranges, passives and element auras are the authoritative values. It explains connections and
    /// gaps; it never ranks teams or recommends a "best" formation. The arena has no line-of-sight blockers,
    /// so coverage is a pure distance test (documented; a future blocker system must extend Covers()).
    /// </summary>
    public sealed class SynergyReport
    {
        public readonly List<SynergyLink> Links = new List<SynergyLink>();
        public readonly List<string> Missing = new List<string>();     // "isolated_element:fire", "lane_uncovered:2"
        public readonly Dictionary<int, float> LaneCoverage = new Dictionary<int, float>();
        public float CrystalCoverage;                                   // share of the approach ring (r=3) in reach

        public static readonly HashSet<string> SupportPassives = new HashSet<string>
        {
            "tailwind", "bulwark", "radiant_guard", "plague_doctor", "backline_ward", "tempest_oracle", "radiant_hymn", "gloom_guard"
        };

        public static SynergyReport Analyze(Battle b, IList<BondDef> activeBonds = null, bool includeDowned = false)
        {
            var r = new SynergyReport();
            List<HeroUnit> hs = b.Heroes;
            ContentDatabase db = b.Content;
            for (int i = 0; i < hs.Count; i++)
            {
                for (int j = i + 1; j < hs.Count; j++)
                {
                    HeroUnit x = hs[i], y = hs[j];
                    float d = Battle.FormationDistance(x, y);
                    bool overlap = d < Reach(x) + Reach(y);
                    foreach (Element ex in Elements(x))
                    {
                        foreach (Element ey in Elements(y))
                        {
                            ReactionDef rd = ex != ey ? db.ReactionFor(ex, ey) : null;
                            if (rd == null || r.Links.Exists(l => l.Kind == SynergyKind.Reaction && l.A == i && l.B == j && l.RuleId == "reaction:" + rd.Id)) continue;
                            r.Links.Add(new SynergyLink { Kind = SynergyKind.Reaction, A = i, B = j, RuleId = "reaction:" + rd.Id, Active = overlap, Condition = overlap ? null : "ranges_apart", Distance = d });
                            if (rd.Params.Get("knock") > 0f && (x.Def.Melee || y.Def.Melee) && overlap)
                                r.Links.Add(new SynergyLink { Kind = SynergyKind.Conflict, A = i, B = j, RuleId = "conflict:knock_vs_melee", Active = true, Condition = "knock_scatters_melee", Distance = d });
                        }
                    }
                    if (activeBonds != null)
                        foreach (BondDef bd in activeBonds)
                            if ((bd.A == x.Def.Id && bd.B == y.Def.Id) || (bd.A == y.Def.Id && bd.B == x.Def.Id))
                                r.Links.Add(new SynergyLink { Kind = SynergyKind.Bond, A = i, B = j, RuleId = "bond:" + bd.Id, Active = true, Distance = d });
                }
            }
            for (int i = 0; i < hs.Count; i++)
            {
                HeroUnit s = hs[i];
                if (s.PassiveKind == null || !SupportPassives.Contains(s.PassiveKind)) continue;
                float radius = s.PassiveParams.Get("radius", 0f);
                if (radius <= 0f) continue;
                for (int j = 0; j < hs.Count; j++)
                {
                    if (j == i) continue;
                    float d = Battle.FormationDistance(s, hs[j]);
                    if (d <= radius)
                        r.Links.Add(new SynergyLink { Kind = SynergyKind.Buff, A = i, B = j, RuleId = "buff:" + s.PassiveKind, Active = true, Distance = d });
                    else if (d <= radius * 1.5f)
                        r.Links.Add(new SynergyLink { Kind = SynergyKind.Buff, A = i, B = j, RuleId = "buff:" + s.PassiveKind, Active = false, Condition = "outside_aura", Distance = d });
                }
            }
            // Missing pieces: an element nobody else can react with.
            for (int i = 0; i < hs.Count; i++)
            {
                bool partner = r.Links.Exists(l => l.Kind == SynergyKind.Reaction && (l.A == i || l.B == i));
                string tag = "isolated_element:" + ElementUtil.Key(hs[i].Def.Element);
                if (!partner && hs.Count > 1 && !r.Missing.Contains(tag)) r.Missing.Add(tag);
            }
            // Coverage: share of each active lane's last 10 world units (approach to the Crystal) inside some hero's reach.
            foreach (int lane in Battle.LanesForWave(b.Wave, b.Biome))
            {
                if (lane < 0 || lane >= b.Arena.Lanes.Count) continue;
                List<Vec2> pts = Sample(b.Arena.Lanes[lane].Points, 0.5f, 10f);
                int hit = 0;
                foreach (Vec2 p in pts) if (Covers(hs, p, includeDowned)) hit++;
                float cov = pts.Count > 0 ? (float)hit / pts.Count : 0f;
                r.LaneCoverage[lane] = cov;
                if (cov < 0.35f) r.Missing.Add("lane_uncovered:" + lane);
            }
            int ring = 0;
            for (int k = 0; k < 36; k++)
            {
                double a = k * 2.0 * System.Math.PI / 36.0;   // analysis only (never feeds the simulation)
                if (Covers(hs, b.Crystal.Pos + new Vec2((float)System.Math.Cos(a), (float)System.Math.Sin(a)) * 3f, includeDowned)) ring++;
            }
            r.CrystalCoverage = ring / 36f;
            return r;
        }

        public static float Reach(HeroUnit h) => h.Stat(StatId.Range) + h.Stat(StatId.LeashRadius);

        private static IEnumerable<Element> Elements(HeroUnit h)
        {
            yield return h.Def.Element;
            if (h.SecondaryElement != Element.None && h.SecondaryElement != h.Def.Element) yield return h.SecondaryElement;
        }

        private static bool Covers(List<HeroUnit> hs, Vec2 p, bool includeDowned)
        {
            foreach (HeroUnit h in hs) if ((includeDowned || !h.Downed) && Vec2.Distance(h.Anchor, p) <= Reach(h)) return true;
            return false;
        }

        /// <summary>Points every <paramref name="step"/> along the last <paramref name="tail"/> units of a polyline (spawn → crystal).</summary>
        private static List<Vec2> Sample(List<Vec2> pts, float step, float tail)
        {
            var outPts = new List<Vec2>();
            float remaining = tail;
            for (int i = pts.Count - 1; i > 0 && remaining > 0f; i--)
            {
                Vec2 a = pts[i], c = pts[i - 1];
                float len = Vec2.Distance(a, c);
                for (float t = 0f; t < len && remaining > 0f; t += step, remaining -= step)
                    outPts.Add(a + (c - a) * (t / SimMath.Max(1e-4f, len)));
            }
            return outPts;
        }
    }
}
