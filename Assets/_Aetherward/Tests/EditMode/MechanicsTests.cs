using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using Aetherward.Sim.Run;
using NUnit.Framework;

namespace Aetherward.Tests
{
    public class MechanicsTests
    {
        [Test]
        public void DeadTargetsAreReleasedByHeroes()
        {
            Battle b = new Battle(TestContent.Setup(2, 21, ("sylph", 4)));
            for (int i = 0; i < 30 * 20 && b.Heroes[0].Target == null; i++) { b.Tick(); b.Journal.Clear(); }
            EnemyUnit t = b.Heroes[0].Target;
            Assert.IsNotNull(t, "hero should acquire a target");
            b.DealDamage(t, new DamageRequest { Attack = 1e6f, Multiplier = 1f, Kind = DamageKind.Trigger, IgnoreDefense = true });
            b.Tick();
            Assert.AreNotSame(t, b.Heroes[0].Target, "dead target must be cleared");
        }

        [Test]
        public void StuckEnemiesAreNudgedForward()
        {
            Battle b = TestContent.EmptyBattle(("terra", 0));
            EnemyUnit e = b.SpawnEnemy(b.Content.Enemies["grunt"], 0, false, null, new Vec2(10f, 1f));
            // Simulate a jam: the enemy keeps trying to walk but something pins it in place.
            var pinned = new Vec2(10f, 1f);
            for (int i = 0; i < 30 * 8; i++)
            {
                b.Tick();
                b.Journal.Clear();
                if (b.Stats.StuckRecoveries == 0) e.Pos = pinned;
            }
            Assert.Greater(b.Stats.StuckRecoveries, 0);
        }

        [Test]
        public void PhoenixFeatherRevivesOncePerWave()
        {
            BattleSetup s = TestContent.Setup(1, 3, ("ignis", 4));
            s.Modifiers.Add(TestContent.Db.Relics["phoenix_feather"].Effects[0], "phoenix_feather");
            Battle b = new Battle(s);
            HeroUnit h = b.Heroes[0];
            b.DamageHero(h, 1e6f, null);
            Assert.IsTrue(h.Alive, "first fall is prevented");
            Assert.Greater(h.Hp, 0f);
            b.DamageHero(h, 1e6f, null);
            Assert.IsFalse(h.Alive, "only once per wave");
            Assert.AreEqual(1, b.Stats.SourceActivations["phoenix_feather"]);
        }

        [Test]
        public void ElementalMirrorStaysBoundedInDenseCrowds()
        {
            BattleSetup s = TestContent.Setup(1, 4);
            s.Wave = new WaveDef { Number = 15, TimeLimit = 999f };
            s.Modifiers.Add(TestContent.Db.Relics["elemental_mirror"].Effects[0], "elemental_mirror");
            s.Modifiers.Add(TestContent.Db.Cards["elemental_overflow"].Effects[0], "elemental_overflow");
            Battle b = new Battle(s);
            Element[] cycle = ElementUtil.All;
            for (int i = 0; i < 60; i++)
            {
                EnemyUnit e = b.SpawnEnemy(b.Content.Enemies["grunt"], 0, false, null, new Vec2(5f + (i % 8) * 0.3f, (i / 8) * 0.3f));
                e.MaxHp = e.Hp = 1e7f;
                b.ApplyElement(e, cycle[i % cycle.Length], 1f, null, 0);
            }
            b.Grid.Rebuild(b.Enemies);
            int before = b.Stats.TotalReactions;
            foreach (EnemyUnit e in b.Enemies.ToArray()) b.ApplyElement(e, Element.Wind, 1f, null, 0);
            int produced = b.Stats.TotalReactions - before;
            Assert.LessOrEqual(produced, 60 * (Battle.MaxProcGeneration + 2), "reaction count must stay bounded");
            Assert.Greater(b.Stats.ReactionsBlockedByGeneration + b.Stats.ReactionsBlockedByBudget, 0);
        }

        [Test]
        public void AdaptiveEnemiesGainPartialResistanceOnly()
        {
            Battle b = TestContent.EmptyBattle(("terra", 0));
            EnemyUnit m = b.SpawnEnemy(b.Content.Enemies["mimic"], 0, false, null, new Vec2(11f, 6f));
            m.Speed = 0f;
            m.MaxHp = m.Hp = 1e7f;
            for (int i = 0; i < 30 * 4; i++)
            {
                if (i % 10 == 0) b.DealDamage(m, new DamageRequest { Attack = 50f, Multiplier = 1f, Element = Element.Fire, Kind = DamageKind.Skill });
                b.Tick();
                b.Journal.Clear();
            }
            Assert.AreEqual((int)Element.Fire, m.AdaptedElement);
            Assert.Greater(m.Resist[(int)Element.Fire], 0.3f);
            Assert.Less(m.Resist[(int)Element.Fire], 0.76f, "never full immunity");
        }

        [Test]
        public void InterestRewardsSavingGoldUpToCap()
        {
            RunController rc = RunController.NewRun(TestContent.Db, 9, new[] { "ignis", "terra" }, 0, RunUnlocks.Everything(TestContent.Db));
            rc.State.Gold = 100;
            rc.StartWave();
            rc.Battle.RunToEnd();
            int before = rc.State.Gold;
            rc.ResolveBattle();
            WaveRecord rec = rc.State.WaveLog[0];
            int interest = rec.GoldEarned - (int)System.Math.Round(rc.Content.Waves[0].Gold + rc.State.WaveLog[0].Kills * 1f);
            Assert.AreEqual(rc.Content.Economy.InterestCap, interest, "100 gold => capped interest");
            Assert.Greater(rc.State.Gold, before);
        }

        [Test]
        public void TwoTimesSpeedIsJustMoreTicks()
        {
            // The view runs 2 ticks per frame-step at 2x; outcome must equal 1x (fixed-tick determinism).
            Battle a = new Battle(TestContent.Setup(3, 77, ("ignis", 4), ("terra", 0)));
            Battle b = new Battle(TestContent.Setup(3, 77, ("ignis", 4), ("terra", 0)));
            while (a.Outcome == BattleOutcome.Running && a.Time < 300) { a.Tick(); a.Journal.Clear(); }
            while (b.Outcome == BattleOutcome.Running && b.Time < 300) { b.Tick(); b.Tick(); b.Journal.Clear(); }
            Assert.AreEqual(a.Outcome, b.Outcome);
            Assert.AreEqual(a.Crystal.Hp, b.Crystal.Hp, 0.001f);
            Assert.AreEqual(a.Stats.Kills, b.Stats.Kills);
        }

        [Test]
        public void JournalNeverGrowsUnbounded()
        {
            Battle b = new Battle(TestContent.Setup(19, 5, ("ignis", 4), ("volt", 8), ("marina", 6), ("terra", 0), ("zephyr", 10), ("sylph", 2)));
            int peak = 0;
            while (b.Outcome == BattleOutcome.Running && b.Time < 200)
            {
                b.Tick();
                if (b.Journal.Pending.Count > peak) peak = b.Journal.Pending.Count;
                b.Journal.Clear();
            }
            Assert.LessOrEqual(peak, CombatJournal.MaxEventsPerFrame);
        }
    }
}
