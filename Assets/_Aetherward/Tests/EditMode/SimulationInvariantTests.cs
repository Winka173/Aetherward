using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using Aetherward.Sim.Run;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>Deterministic replay and per-tick invariants over real waves (Phase 10 golden checks).</summary>
    public class SimulationInvariantTests
    {
        private static ulong StateHash(Battle b)
        {
            ulong h = 1469598103934665603UL;
            void Mix(float v) { h ^= (ulong)System.BitConverter.SingleToInt32Bits(v); h *= 1099511628211UL; }
            Mix(b.Time);
            Mix(b.Crystal.Hp);
            foreach (HeroUnit u in b.Heroes) { Mix(u.Hp); Mix(u.Pos.X); Mix(u.Pos.Y); Mix(u.SkillTimer); }
            foreach (EnemyUnit e in b.Enemies) { Mix(e.Hp); Mix(e.Pos.X); Mix(e.Pos.Y); }
            return h;
        }

        private static void CheckInvariants(Battle b, string where)
        {
            Assert.IsFalse(float.IsNaN(b.Crystal.Hp) || float.IsInfinity(b.Crystal.Hp), where + ": crystal HP");
            Assert.GreaterOrEqual(b.Crystal.Hp, 0f, where);
            foreach (HeroUnit h in b.Heroes)
            {
                Assert.IsFalse(float.IsNaN(h.Hp) || float.IsNaN(h.Pos.X) || float.IsNaN(h.Pos.Y), where + ": hero " + h.Def.Id);
                Assert.LessOrEqual(h.Hp, h.MaxHp + 1e-3f, where + ": overheal " + h.Def.Id);
                Assert.IsTrue(h.Target == null || h.Target.Alive, where + ": " + h.Def.Id + " targets a dead enemy");
            }
            foreach (EnemyUnit e in b.Enemies)
            {
                Assert.IsFalse(float.IsNaN(e.Hp) || float.IsNaN(e.Pos.X), where + ": enemy " + e.Def.Id);
                foreach (float r in e.Resist) Assert.LessOrEqual(r, Battle.MaxResist + 1e-4f, where + ": resist cap " + e.Def.Id);
                Assert.LessOrEqual(Vec2.Distance(e.Pos, b.Crystal.Pos), 40f, where + ": enemy escaped the arena");
            }
            Assert.LessOrEqual(b.Enemies.Count, 400, where + ": horde runaway");
        }

        [Test]
        public void ReplayingTheSameSetupIsTickForTickIdentical()
        {
            foreach (int wave in new[] { 4, 10, 15, 20 })
            {
                BattleSetup a = TestContent.Setup(wave, 99, ("terra", 0), ("ignis", 4), ("marina", 8), ("volt", 6), ("seren", 2), ("zerith", 5));
                BattleSetup b = TestContent.Setup(wave, 99, ("terra", 0), ("ignis", 4), ("marina", 8), ("volt", 6), ("seren", 2), ("zerith", 5));
                foreach (HeroLoadout l in a.Heroes) l.Level = 4;
                foreach (HeroLoadout l in b.Heroes) l.Level = 4;
                Battle x = new Battle(a), y = new Battle(b);
                for (int t = 0; t < 30 * 240 && (x.Outcome == BattleOutcome.Running || y.Outcome == BattleOutcome.Running); t++)
                {
                    x.Tick(); y.Tick();
                    x.Journal.Clear(); y.Journal.Clear();
                    if (t % 15 == 0) Assert.AreEqual(StateHash(x), StateHash(y), "wave " + wave + " diverged at tick " + t);
                }
                Assert.AreEqual(x.Outcome, y.Outcome);
            }
        }

        [Test]
        public void InvariantsHoldEveryTickAcrossWavesBiomesAndAscension()
        {
            ContentDatabase db = TestContent.Db;
            int checkedTicks = 0;
            foreach (BiomeDef biome in db.BiomeList)
                foreach (int wave in new[] { 6, 13, 20 })
                {
                    BattleSetup s = TestContent.Setup(wave, 7, ("terra", 0), ("vesper", 4), ("isolde", 8), ("caelis", 6), ("morven", 2), ("aeris", 5));
                    s.Biome = biome;
                    s.Ascension = 10;
                    s.EliteExtraAffix = true;
                    s.EliteEvery = 8;
                    foreach (HeroLoadout l in s.Heroes) l.Level = 5;
                    Battle b = new Battle(s);
                    for (int t = 0; t < 30 * 300 && b.Outcome == BattleOutcome.Running; t++)
                    {
                        b.Tick();
                        b.Journal.Clear();
                        if (t % 10 == 0) { CheckInvariants(b, biome.Id + " w" + wave + " t" + t); checkedTicks++; }
                    }
                    Assert.AreNotEqual(BattleOutcome.Running, b.Outcome, biome.Id + " wave " + wave + " never resolved");
                }
            Assert.Greater(checkedTicks, 1000);
        }

        [Test]
        public void FullRunsNeverProduceNegativeGoldOrDoubleOutcomes()
        {
            ContentDatabase db = TestContent.Db;
            for (ulong seed = 1; seed <= 6; seed++)
            {
                RunController rc = RunController.NewRun(db, seed, new[] { "ignis", "terra" }, (int)(seed % 3) * 4, RunUnlocks.Everything(db));
                Assert.IsTrue(new AutoPilot(rc, Strategy.Find("balanced")).PlayToEnd());
                Assert.GreaterOrEqual(rc.State.Gold, 0);
                Assert.IsTrue(rc.State.Phase == RunPhase.Victory ^ rc.State.Phase == RunPhase.Defeat);
            }
        }
    }
}
