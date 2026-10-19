using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using Aetherward.Sim.Meta;
using Aetherward.Sim.Run;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>Crystal Evolution: offered once after wave 6, exclusive, persisted, effective, and switchable off.</summary>
    public class CrystalEvolutionTests
    {
        private static RunController AfterWave(ulong seed, bool enabled)
        {
            ContentDatabase db = TestContent.Db;
            RunController rc = RunController.NewRun(db, seed, new[] { "ignis", "terra" }, 0, RunUnlocks.Everything(db));
            rc.State.CrystalEvolutionEnabled = enabled;
            var pilot = new AutoPilot(rc, Strategy.Find("balanced"));
            for (int guard = 0; guard < 5000 && rc.State.Phase != RunPhase.Victory && rc.State.Phase != RunPhase.Defeat; guard++)
            {
                if (rc.State.Phase == RunPhase.Reward && rc.State.CurrentReward == RewardKind.CrystalEvolution) return rc;
                pilot.Step();
            }
            return rc;
        }

        [Test]
        public void OfferedOnceAfterWaveSixAndExclusive()
        {
            RunController rc = AfterWave(41, true);
            Assert.AreEqual(RewardKind.CrystalEvolution, rc.State.CurrentReward);
            Assert.GreaterOrEqual(rc.State.Wave, CrystalPaths.OfferAfterWave);
            Assert.AreEqual(3, rc.State.Offers.Count);
            Assert.IsTrue(rc.Choose(rc.State.Offers.FindIndex(o => o.Id == CrystalPaths.Thorn)));
            Assert.AreEqual(CrystalPaths.Thorn, rc.State.CrystalPath);
            var pilot = new AutoPilot(rc, Strategy.Find("balanced"));
            Assert.IsTrue(pilot.PlayToEnd());
            int offered = 0;
            foreach (string line in rc.State.Log) if (line.Contains("CrystalPath:")) offered++;
            Assert.AreEqual(3 + 1, offered, "three offers and one choice, never again");
            Assert.AreEqual(CrystalPaths.Thorn, rc.State.CrystalPath);
        }

        [Test]
        public void FeatureFlagOffNeverOffers()
        {
            RunController rc = AfterWave(41, false);
            Assert.AreNotEqual(RewardKind.CrystalEvolution, rc.State.CurrentReward);
            Assert.IsNull(rc.State.CrystalPath);
        }

        [Test]
        public void ChoicePersistsInSaves()
        {
            ContentDatabase db = TestContent.Db;
            RunController rc = RunController.NewRun(db, 5, new[] { "ignis", "terra" }, 0, RunUnlocks.Everything(db));
            rc.State.CrystalPath = CrystalPaths.Pulse;
            rc.State.CrystalEvolutionEnabled = false;
            var saves = new SaveService(new MemoryStorage());
            saves.SaveRun(rc.State);
            RunState loaded = saves.LoadRun(db);
            Assert.AreEqual(CrystalPaths.Pulse, loaded.CrystalPath);
            Assert.IsFalse(loaded.CrystalEvolutionEnabled);
        }

        private static Battle Make(string path)
        {
            BattleSetup s = TestContent.Setup(1, 3, ("terra", 0));
            s.Wave = new WaveDef { Number = 6, TimeLimit = 999f };
            s.CrystalPath = path;
            return new Battle(s);
        }

        [Test]
        public void BastionHardensThornRetaliatesPulseHitsNearbyEnemies()
        {
            Battle none = Make(null), bastion = Make(CrystalPaths.Bastion), thorn = Make(CrystalPaths.Thorn);
            Assert.AreEqual(none.Crystal.DamageReduction + CrystalPaths.BastionReduction, bastion.Crystal.DamageReduction, 1e-4f);
            Assert.Greater(bastion.Crystal.Regen, none.Crystal.Regen);
            Assert.Greater(thorn.Crystal.Thorns, none.Crystal.Thorns);

            Battle pulse = Make(CrystalPaths.Pulse);
            EnemyUnit near = pulse.SpawnEnemy(pulse.Content.Enemies["grunt"], 0, false, null, pulse.Crystal.Pos + new Vec2(1.5f, 0f));
            EnemyUnit far = pulse.SpawnEnemy(pulse.Content.Enemies["grunt"], 0, false, null, pulse.Crystal.Pos + new Vec2(9f, 0f));
            near.Speed = far.Speed = 0f;
            near.MaxHp = near.Hp = far.MaxHp = far.Hp = 100000f;
            pulse.Heroes[0].Pos = new Vec2(-30f, -30f); // keep the hero out of the test
            for (int i = 0; i < (int)(CrystalPaths.PulseInterval * 30f) + 2; i++) pulse.Tick();
            Assert.Less(near.Hp, near.MaxHp, "nova hits enemies in radius");
            Assert.AreEqual(far.MaxHp, far.Hp, 1e-3f, "nova does not reach far enemies");
        }
    }
}
