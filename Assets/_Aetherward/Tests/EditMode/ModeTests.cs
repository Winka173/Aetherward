using System.Collections.Generic;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Meta;
using Aetherward.Sim.Run;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>Endless, Daily Seed, Boss Rush and Ascension 6–10.</summary>
    public class ModeTests
    {
        private static ContentDatabase Db => TestContent.Db;

        private static RunController Mode(GameMode m, ulong seed = 5, string daily = null) =>
            RunController.NewModeRun(Db, m, seed, new[] { "ignis", "terra" }, 0, RunUnlocks.Everything(Db), null, daily);

        [Test]
        public void EndlessLoopsTheSecondHalfWithRisingScale()
        {
            RunController rc = Mode(GameMode.Endless);
            Assert.AreEqual(0, rc.TotalWaves);
            WaveDef w21 = rc.WaveAt(21), w31 = rc.WaveAt(31), w30 = rc.WaveAt(30);
            Assert.AreEqual(21, w21.Number);
            Assert.Greater(w31.ScalePct, w21.ScalePct);
            Assert.IsTrue(w30.Boss, "every tenth wave is a boss wave");
            Assert.Greater(w30.Rewards.Count, 0, "looped final waves still reward");
            Assert.AreSame(Db.Waves[4], rc.WaveAt(5), "the first 20 waves are the authored ones");
        }

        [Test]
        public void EndlessWave25IsHarderThanWave15()
        {
            RunController rc = Mode(GameMode.Endless);
            BattleSetup a = TestContent.Setup(1, 3, ("terra", 0));
            a.Wave = rc.WaveAt(15);
            BattleSetup b = TestContent.Setup(1, 3, ("terra", 0));
            b.Wave = rc.WaveAt(25);
            EnemyUnit ea = new Battle(a).SpawnEnemy(Db.Enemies["grunt"], 0, false, null, null);
            EnemyUnit eb = new Battle(b).SpawnEnemy(Db.Enemies["grunt"], 0, false, null, null);
            Assert.Greater(eb.MaxHp, ea.MaxHp);
        }

        [Test]
        public void DailyIsTheSameForEveryoneOnADate()
        {
            RunController a = Mode(GameMode.Daily, 1, "20261019"), b = Mode(GameMode.Daily, 999, "20261019"), c = Mode(GameMode.Daily, 1, "20261020");
            Assert.AreEqual(a.State.Seed, b.State.Seed, "seed comes from the date, not the caller");
            Assert.AreEqual(a.State.BiomeId, b.State.BiomeId);
            CollectionAssert.AreEqual(a.State.ModeModifiers, b.State.ModeModifiers);
            Assert.AreEqual(2, a.State.ModeModifiers.Count);
            Assert.AreNotEqual(a.State.Seed, c.State.Seed);
            a.State.Wave = 3;
            foreach (string m in a.State.ModeModifiers) Assert.Contains(m, a.BuildBattleSetup().ExtraWaveModifiers);
        }

        [Test]
        public void BossRushFightsEveryBossInOrderAndEndsAfterTheLast()
        {
            RunController rc = Mode(GameMode.BossRush);
            List<string> bosses = rc.BossRushBosses();
            Assert.AreEqual(bosses.Count, rc.TotalWaves);
            Assert.GreaterOrEqual(bosses.Count, 5);
            Assert.AreEqual(4, rc.State.Heroes.Count, "boss rush starts with a squad of four");
            foreach (HeroRunState h in rc.State.Heroes) { Assert.AreEqual(3, h.Level); Assert.GreaterOrEqual(h.Node, 0); }
            for (int i = 1; i <= bosses.Count; i++)
            {
                WaveDef w = rc.WaveAt(i);
                Assert.AreEqual(bosses[i - 1], rc.BossFor(w));
                Assert.IsTrue(w.Groups.Exists(g => g.Enemy == bosses[i - 1]), "stage " + i + " spawns its boss");
                if (i > 1) Assert.GreaterOrEqual(w.EffectiveLevel, rc.WaveAt(i - 1).EffectiveLevel);
            }
            rc.State.Wave = 1;
            Battle b = new Battle(rc.BuildBattleSetup());
            bool spawned = false;
            for (int t = 0; t < 30 * 10 && !spawned; t++) { b.Tick(); b.Journal.Clear(); spawned = b.Enemies.Exists(e => e.Def.Id == bosses[0]); }
            Assert.IsTrue(spawned);
        }

        [Test]
        public void ModeSurvivesSaveAndRecordsArePerMode()
        {
            RunController rc = Mode(GameMode.Daily, 1, "20261019");
            var saves = new SaveService(new MemoryStorage());
            saves.SaveRun(rc.State);
            RunState loaded = saves.LoadRun(Db);
            Assert.AreEqual(GameMode.Daily, loaded.Mode);
            Assert.AreEqual("20261019", loaded.DailyKey);
            CollectionAssert.AreEqual(rc.State.ModeModifiers, loaded.ModeModifiers);

            MetaProfile m = MetaProfile.CreateDefault(Db);
            RunController br = Mode(GameMode.BossRush);
            br.State.Wave = 4;
            m.RecordRun(br, new RunResults { Victory = false }, 0);
            Assert.AreEqual(4, m.ModeRecords["bossrush"]);
            Assert.AreEqual(0, m.BestWave, "boss rush stages do not count as waves");
            saves.SaveMeta(m);
            Assert.AreEqual(4, saves.LoadMeta(Db).ModeRecords["bossrush"]);
        }

        [Test]
        public void EveryModePlaysToTheEndWithoutGettingStuck()
        {
            foreach (GameMode mode in new[] { GameMode.Classic, GameMode.Daily, GameMode.BossRush })
            {
                RunController rc = Mode(mode, 77, "20261019");
                Assert.IsTrue(new AutoPilot(rc, Strategy.Find("balanced")).PlayToEnd(), mode + " got stuck");
                Assert.IsTrue(rc.State.Phase == RunPhase.Victory || rc.State.Phase == RunPhase.Defeat, mode.ToString());
            }
        }

        [Test]
        public void AscensionSixToTenModulesApply()
        {
            Assert.AreEqual(10, Db.Difficulty.MaxLevel);
            RunController low = RunController.NewRun(Db, 3, new[] { "ignis", "terra" }, 5, RunUnlocks.Everything(Db));
            RunController high = RunController.NewRun(Db, 3, new[] { "ignis", "terra" }, 10, RunUnlocks.Everything(Db));
            Assert.AreEqual(low.RerollCost + 1, high.RerollCost);
            Assert.Less(high.RarityShift(Rarity.Legendary), 1f);
            Assert.AreEqual(1f, high.RarityShift(Rarity.Common));
            Assert.Less(high.CrystalMaxHp, low.CrystalMaxHp);
            high.State.Wave = low.State.Wave = 6;
            BattleSetup hs = high.BuildBattleSetup();
            Assert.AreEqual(8, hs.EliteEvery);
            Assert.Greater(hs.HazardShift, 0f);
            Battle b = new Battle(hs);
            int elites = 0, total = 0;
            for (int t = 0; t < 30 * 60; t++)
            {
                b.Tick();
                foreach (Sim.Combat.SimEvent e in b.Journal.Pending) if (e.Type == SimEventType.EnemySpawn) total++;
                b.Journal.Clear();
            }
            foreach (EnemyUnit e in b.Enemies) if (e.Elite) elites++;
            Assert.Greater(total, 8);
        }

        [Test]
        public void BondsActivateOnlyWithBothHeroesAndChangeStats()
        {
            RunController rc = RunController.NewRun(Db, 4, new[] { "seren", "terra" }, 0, RunUnlocks.Everything(Db));
            Assert.IsEmpty(rc.ActiveBonds());
            Assert.AreEqual("twilight_vow", rc.BondFor("nyxara").Id, "recruit offers know which bond they complete");
            rc.State.Wave = 1;
            float before = new Battle(rc.BuildBattleSetup()).Heroes.Find(h => h.Def.Id == "seren").MaxHp;
            RunController both = RunController.NewRun(Db, 4, new[] { "seren", "terra", "nyxara" }, 0, RunUnlocks.Everything(Db));
            Assert.AreEqual(1, both.ActiveBonds().Count);
            both.State.Wave = 1;
            float after = new Battle(both.BuildBattleSetup()).Heroes.Find(h => h.Def.Id == "seren").MaxHp;
            Assert.AreEqual(before * 1.1f, after, before * 0.01f);
        }

        [Test]
        public void RunPoolsAreSeededSavedAndKeepFusionsAndBondsReachable()
        {
            RunController a = RunController.NewRun(Db, 21, new[] { "seren", "terra" }, 0, RunUnlocks.Everything(Db));
            RunController b = RunController.NewRun(Db, 21, new[] { "seren", "terra" }, 0, RunUnlocks.Everything(Db));
            CollectionAssert.AreEqual(a.State.HeroPool, b.State.HeroPool);
            Assert.LessOrEqual(a.State.HeroPool.Count, RunController.RunHeroPoolSize + 2 + Db.Bonds.Count);
            Assert.Contains("nyxara", a.State.HeroPool, "bond partners of the starters are always in the pool");
            foreach (FusionDef f in Db.Fusions)
                Assert.AreEqual(a.State.RelicPool.Contains(f.A), a.State.RelicPool.Contains(f.B), "fusion halves come together: " + f.Result);
            var saves = new SaveService(new MemoryStorage());
            saves.SaveRun(a.State);
            CollectionAssert.AreEqual(a.State.RelicPool, saves.LoadRun(Db).RelicPool);
            RunController small = RunController.NewRun(Db, 21, new[] { "ignis", "terra" }, 0, MetaProfile.CreateDefault(Db).ToRunUnlocks());
            Assert.IsEmpty(small.State.HeroPool, "small unlock sets are not trimmed");
        }
    }
}
