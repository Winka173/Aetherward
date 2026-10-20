using System.Collections.Generic;
using System.Linq;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using Aetherward.Sim.Presentation;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>P4 + validation scenario 5: boss telegraphs precede harmful effects (also at 2x with the assist mode).</summary>
    public class BossTelegraphTests
    {
        /// <summary>Minimum simulation-seconds between a boss telegraph and its strike (readable at 1x; 2x halves it).</summary>
        public const float MinLead = 0.5f;

        private static IEnumerable<string> Bosses() => TestContent.Db.Enemies.Values.Where(e => e.Boss).Select(e => e.Id).OrderBy(id => id);

        [TestCaseSource(nameof(Bosses))]
        public void EveryBossStrikeIsTelegraphedFirst(string bossId)
        {
            BattleSetup s = TestContent.Setup(1, 5, ("terra", 0), ("marina", 1), ("ignis", 2), ("volt", 3), ("sylph", 5), ("seren", 11));
            foreach (HeroLoadout h in s.Heroes) h.Level = 6;
            s.CrystalMaxHp = s.CrystalHp = 1e9f;   // observe the whole fight
            s.Wave = new WaveDef { Number = 12, Level = 12, Boss = true, TimeLimit = 120f, Lanes = new List<int> { 0 } };
            s.Wave.Groups.Add(new SpawnGroup { Enemy = bossId, Count = 1, Lane = 0 });
            var b = new Battle(s);
            var telegraphs = new List<(float t, string kind, Vec2 pos, float delay)>();
            int strikes = 0;
            float minLead = float.MaxValue;
            var bossUids = new HashSet<int>();
            while (b.Outcome == BattleOutcome.Running && b.Time < 90f)
            {
                b.Tick();
                foreach (EnemyUnit e in b.Enemies) if (e.IsBoss) bossUids.Add(e.Uid);
                foreach (SimEvent ev in b.Journal.Pending)
                {
                    if (!bossUids.Contains(ev.SourceUid)) continue;
                    if (ev.Type == SimEventType.Telegraph) telegraphs.Add((b.Time, ev.Id, ev.Pos, ev.Value));
                    else if (ev.Type == SimEventType.Strike && ev.Id != "summon")
                    {
                        strikes++;
                        int i = telegraphs.FindLastIndex(t => t.kind == ev.Id && Vec2.Distance(t.pos, ev.Pos) < 0.01f);
                        Assert.GreaterOrEqual(i, 0, $"{bossId}: strike '{ev.Id}' at t={b.Time:F2} had no telegraph");
                        float lead = b.Time - telegraphs[i].t;
                        minLead = System.Math.Min(minLead, lead);
                        telegraphs.RemoveAt(i);
                    }
                }
                b.Journal.Clear();
            }
            Assert.IsNotEmpty(bossUids, bossId + " never spawned");
            if (strikes > 0) Assert.GreaterOrEqual(minLead + 1e-4f, MinLead, $"{bossId}: telegraph lead {minLead:F2}s is too short");
            TestContext.WriteLine($"{bossId}: {strikes} telegraphed strikes, min lead {(strikes > 0 ? minLead.ToString("F2") : "-")}s");
        }

        [Test]
        public void AssistModePlaysBossTelegraphsAtNormalSpeed()
        {
            var a = new TelegraphAssist { Enabled = true };
            Assert.AreEqual(2, a.EffectiveSpeed(2, 0f));
            a.OnTelegraph(true, 1.2f, 10f);
            Assert.AreEqual(1, a.EffectiveSpeed(2, 10.5f), "slowed while the telegraph is up");
            Assert.AreEqual(2, a.EffectiveSpeed(2, 11.3f), "back to 2x after the strike");
            a.OnTelegraph(false, 5f, 20f);
            Assert.AreEqual(2, a.EffectiveSpeed(2, 21f), "non-boss telegraphs do not slow");
            var off = new TelegraphAssist { Enabled = false };
            off.OnTelegraph(true, 3f, 0f);
            Assert.AreEqual(2, off.EffectiveSpeed(2, 1f), "assist is opt-in");
        }

        [Test]
        public void TelegraphTimingIsIdenticalRegardlessOfPresentationSpeed()
        {
            // 2x only advances more fixed ticks per frame; the simulation timeline (and thus every lead time) is identical.
            string Run(int ticksPerFrame)
            {
                BattleSetup s = TestContent.Setup(1, 5, ("terra", 0), ("ignis", 2));
                s.CrystalMaxHp = s.CrystalHp = 1e9f;
                s.Wave = new WaveDef { Number = 12, Level = 12, Boss = true, TimeLimit = 60f, Lanes = new List<int> { 0 } };
                s.Wave.Groups.Add(new SpawnGroup { Enemy = "siegebreaker_golem", Count = 1, Lane = 0 });
                var b = new Battle(s);
                var log = new List<string>();
                for (int frame = 0; frame < 900 / ticksPerFrame; frame++)
                {
                    for (int k = 0; k < ticksPerFrame; k++) b.Tick();
                    foreach (SimEvent ev in b.Journal.Pending)
                        if (ev.Type == SimEventType.Telegraph || ev.Type == SimEventType.Strike) log.Add(ev.Type + ev.Id + ev.Pos.X.ToString("F3"));
                    b.Journal.Clear();
                }
                return string.Join("|", log);
            }
            Assert.AreEqual(Run(1), Run(2));
        }
    }
}
