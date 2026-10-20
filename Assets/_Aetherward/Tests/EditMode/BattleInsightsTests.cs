using System.Collections.Generic;
using System.Linq;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Meta;
using Aetherward.Sim.Run;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>P6 + validation scenario 8: loss explanations point at logged threats, and a replay agrees.</summary>
    public class BattleInsightsTests
    {
        private static (List<string> insights, Dictionary<string, float> byEnemy, Dictionary<int, float> byLane, BattleStats stats, int wave) PlayToDefeat(ulong seed)
        {
            ContentDatabase db = TestContent.Db;
            RunController rc = RunController.NewRun(db, seed, new[] { "ignis", "terra" }, 0, RunUnlocks.Everything(db));
            var pilot = new AutoPilot(rc, Strategy.Find("arcane_void"));
            Dictionary<string, float> byEnemy = null;
            Dictionary<int, float> byLane = null;
            BattleStats stats = null;
            for (int guard = 0; guard < 3000 && rc.State.Phase != RunPhase.Defeat && rc.State.Phase != RunPhase.Victory; guard++)
            {
                if (rc.State.Phase == RunPhase.Battle)
                {
                    rc.Battle.RunToEnd();
                    byEnemy = new Dictionary<string, float>(rc.Battle.Stats.CrystalDamageByEnemy);
                    byLane = new Dictionary<int, float>(rc.Battle.Stats.CrystalDamageByLane);
                    stats = rc.Battle.Stats;
                    rc.ResolveBattle();
                }
                else pilot.Step();
            }
            WaveRecord last = rc.State.WaveLog.Last();
            return (new List<string>(last.Insights), byEnemy, byLane, stats, last.Wave);
        }

        [Test]
        public void DefeatInsightsQuoteLoggedEvidenceAndReplayAgrees()
        {
            ulong seed = 0;
            (List<string> insights, Dictionary<string, float> byEnemy, Dictionary<int, float> byLane, BattleStats stats, int wave) r = default;
            for (ulong s = 1; s < 60; s++)
            {
                r = PlayToDefeat(s);
                if (r.byEnemy != null && r.byEnemy.Count > 0 && r.insights.Count > 0) { seed = s; break; }
            }
            Assert.Greater(seed, 0UL, "found a defeat to explain");
            float total = r.byEnemy.Values.Sum();
            foreach (string code in r.insights)
            {
                var (kind, args, conf) = BattleInsights.Parse(code);
                Assert.That(conf, Is.AnyOf("high", "medium", "low"), code);
                switch (kind)
                {
                    case "threat":
                        string top = r.byEnemy.OrderByDescending(kv => kv.Value).ThenBy(kv => kv.Key, System.StringComparer.Ordinal).First().Key;
                        Assert.AreEqual(top, args[0], "names the enemy that actually did the most Crystal damage");
                        Assert.AreEqual((int)System.Math.Round(100.0 * r.byEnemy[top] / total), int.Parse(args[1]));
                        break;
                    case "lane":
                        int lane = int.Parse(args[0]);
                        Assert.IsTrue(r.byLane.ContainsKey(lane), "lane is from the damage log");
                        Assert.GreaterOrEqual(r.byLane[lane] / total, 0.5f - 1e-3f);
                        break;
                    case "tank":
                        Assert.AreEqual(r.stats.FirstGuardianDown, args[0]);
                        break;
                    case "timeout":
                        Assert.Greater(r.stats.TimeoutBreaches, 0);
                        break;
                }
            }
            // Deterministic replay: the same seed yields the same explanation.
            CollectionAssert.AreEqual(r.insights, PlayToDefeat(seed).insights);
        }

        [Test]
        public void QuietWavesAreNotExplainedAndInsightsSurviveSaves()
        {
            Battle b = TestContent.EmptyBattle(("terra", 0));
            b.RunToEnd();
            Assert.IsEmpty(BattleInsights.ForWave(b), "no Crystal damage -> nothing to explain (no invented causes)");
            ContentDatabase db = TestContent.Db;
            RunController rc = RunController.NewRun(db, 4, new[] { "ignis", "terra" }, 0, RunUnlocks.Everything(db));
            var rec = new WaveRecord { Wave = 3 };
            rec.Insights.Add("threat|sapper|62|high");
            rec.Insights.Add("lane|0|80|20|high");
            rc.State.WaveLog.Add(rec);
            var saves = new SaveService(new MemoryStorage());
            saves.SaveRun(rc.State);
            CollectionAssert.AreEqual(rec.Insights, saves.LoadRun(db).WaveLog.Last().Insights, "order preserved");
        }
    }
}
