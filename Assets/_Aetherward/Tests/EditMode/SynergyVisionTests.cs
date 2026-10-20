using System.Collections.Generic;
using System.Linq;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>P1 Synergy Vision + validation scenarios 1 and 2 (coverage by placement; reaction counted once).</summary>
    public class SynergyVisionTests
    {
        private static readonly string[] Six = { "marina", "volt", "zephyr", "terra", "ignis", "freya" };

        private static Battle Place(params int[] nodes)
        {
            var heroes = new (string, int)[Six.Length];
            for (int i = 0; i < Six.Length; i++) heroes[i] = (Six[i], nodes[i]);
            BattleSetup s = TestContent.Setup(1, 77, heroes);
            s.Wave = new WaveDef { Number = 6, TimeLimit = 999f, Lanes = new List<int> { 0, 1, 2, 3 } };
            s.Wave.Groups.Add(new SpawnGroup { Enemy = "grunt", Count = 1, Lane = -1 });
            return new Battle(s);
        }

        private static string Fingerprint(SynergyReport r) =>
            string.Join("|", r.Links.Select(l => $"{l.Kind}:{l.A}-{l.B}:{l.RuleId}:{l.Active}:{l.Condition}")) + "#" +
            string.Join(",", r.LaneCoverage.OrderBy(kv => kv.Key).Select(kv => kv.Key + "=" + kv.Value.ToString("F4"))) + "#" + r.CrystalCoverage.ToString("F4") +
            "#" + string.Join(",", r.Missing);

        [Test]
        public void SixHeroPlacementsGivePredictablyDifferentCoverageAndAreDeterministic()
        {
            // East cluster vs spread formation (same seed, same heroes).
            SynergyReport east = SynergyReport.Analyze(Place(0, 3, 4, 5, 11, 6));
            SynergyReport spread = SynergyReport.Analyze(Place(4, 8, 6, 10, 0, 2));
            Assert.AreEqual(Fingerprint(east), Fingerprint(SynergyReport.Analyze(Place(0, 3, 4, 5, 11, 6))), "same formation, same report");
            Assert.AreNotEqual(Fingerprint(east), Fingerprint(spread));
            // Lane 0 = east, lane 1 = west (arena.json): coverage follows where the heroes stand.
            Assert.Greater(east.LaneCoverage[0], east.LaneCoverage[1], "east cluster covers the east lane better");
            Assert.Greater(spread.LaneCoverage[1], east.LaneCoverage[1], "spreading out covers the west lane");
            Assert.That(east.Missing.Any(m => m.StartsWith("lane_uncovered:")) || east.LaneCoverage[1] < spread.LaneCoverage[1]);
        }

        [Test]
        public void ReactionLinksExplainRuleIdsAndRangeConditions()
        {
            Battle near = Place(0, 3, 6, 10, 5, 11);
            SynergyReport r = SynergyReport.Analyze(near);
            ContentDatabase db = near.Content;
            string waterLightning = "reaction:" + db.ReactionFor(Element.Water, Element.Lightning).Id;
            SynergyLink l = r.Links.Single(x => x.Kind == SynergyKind.Reaction && x.A == 0 && x.B == 1);
            Assert.AreEqual(waterLightning, l.RuleId);
            Assert.IsTrue(l.Active, "adjacent marina + volt overlap");
            // Every link's state must agree with the reach rule it reports.
            foreach (SynergyLink x in r.Links.Where(x => x.Kind == SynergyKind.Reaction))
            {
                bool overlap = x.Distance < SynergyReport.Reach(near.Heroes[x.A]) + SynergyReport.Reach(near.Heroes[x.B]);
                Assert.AreEqual(overlap, x.Active, x.RuleId);
                Assert.AreEqual(overlap ? null : "ranges_apart", x.Condition);
            }
        }

        [Test]
        public void SupportAuraLinksDependOnDistance()
        {
            // terra (bulwark r=2.8) on node 4 (4.5,0): node 5 (3.2,2.45) is 2.77 away, node 8 (-4.5,0) is 9 away.
            SynergyReport r = SynergyReport.Analyze(Place(5, 8, 2, 4, 9, 10));
            Assert.IsTrue(r.Links.Any(x => x.Kind == SynergyKind.Buff && x.RuleId == "buff:bulwark" && x.A == 3 && x.B == 0 && x.Active));
            Assert.IsFalse(r.Links.Any(x => x.RuleId == "buff:bulwark" && x.A == 3 && x.B == 1), "far ally: no aura link");
        }

        [Test]
        public void WaterLightningWindReactionsAreCountedExactlyOnce()
        {
            BattleSetup s = TestContent.Setup(6, 9, ("marina", 0), ("volt", 1), ("zephyr", 3));
            foreach (HeroLoadout h in s.Heroes) h.Level = 4;
            var b = new Battle(s);
            int events = 0;
            var byId = new Dictionary<string, int>();
            while (b.Outcome == BattleOutcome.Running && b.Time < 300f)
            {
                b.Tick();
                foreach (SimEvent e in b.Journal.Pending)
                {
                    if (e.Type != SimEventType.Reaction) continue;
                    events++;
                    byId.TryGetValue(e.Id, out int c);
                    byId[e.Id] = c + 1;
                }
                b.Journal.Clear();
            }
            int counted = b.Stats.ReactionCounts.Values.Sum();
            Assert.Greater(counted, 0, "water/lightning/wind team triggers reactions");
            Assert.AreEqual(counted, events, "one presentation event per counted reaction (no double counting)");
            foreach (var kv in b.Stats.ReactionCounts) Assert.AreEqual(kv.Value, byId[kv.Key], kv.Key);
            Assert.AreEqual(0, b.Journal.Dropped, "journal never dropped reaction events");
        }
    }
}
