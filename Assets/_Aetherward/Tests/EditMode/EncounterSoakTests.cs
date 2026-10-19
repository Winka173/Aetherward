using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Run;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>Phase 6/10: encounter budgets are sane and a long Endless soak keeps the simulation bounded.</summary>
    public class EncounterSoakTests
    {
        [Test]
        public void EveryWaveOfEveryModeHasAPositiveBoundedBudget()
        {
            ContentDatabase db = TestContent.Db;
            foreach (GameMode mode in new[] { GameMode.Classic, GameMode.Endless, GameMode.BossRush })
            {
                RunController rc = RunController.NewModeRun(db, mode, 1, new[] { "ignis", "terra" }, 0, RunUnlocks.Everything(db));
                int count = mode == GameMode.Endless ? 40 : rc.TotalWaves;
                foreach (EncounterEntry e in EncounterReport.ForRun(rc, count))
                {
                    Assert.Greater(e.Enemies, 0, mode + " wave " + e.Wave + " is empty");
                    Assert.Greater(e.EffectiveHp, 0f);
                    Assert.Less(e.Density, 12f, mode + " wave " + e.Wave + " spawns faster than the arena can read");
                    Assert.IsFalse(float.IsNaN(e.CrystalPressure));
                }
            }
        }

        [Test]
        public void EndlessSoakStaysBoundedForThirtyWaves()
        {
            ContentDatabase db = TestContent.Db;
            Strategy st = Strategy.Find("balanced");
            RunController rc = RunController.NewModeRun(db, GameMode.Endless, 777, st.Starters, 0, RunUnlocks.Everything(db));
            var pilot = new AutoPilot(rc, st);
            for (int guard = 0; guard < 20000 && rc.State.Wave <= 30; guard++)
            {
                if (rc.State.Phase == RunPhase.Prepare)
                {
                    pilot.Prepare();
                    Battle b = rc.StartWave();
                    Assert.IsNotNull(b);
                    b.Crystal.MaxHp = b.Crystal.Hp = 1e9f; // stress mode: reach late waves
                    int ticks = 0;
                    while (b.Outcome == BattleOutcome.Running && ticks++ < 30 * 600)
                    {
                        b.Tick();
                        Assert.LessOrEqual(b.Enemies.Count, b.Setup.MaxActiveEnemies);
                        Assert.Less(b.Zones.Count + b.Projectiles.Count, 400, "effects pile up");
                        b.Journal.Clear();
                    }
                    Assert.AreNotEqual(BattleOutcome.Running, b.Outcome, "wave " + rc.State.Wave + " never ended");
                    rc.ResolveBattle();
                }
                else Assert.IsTrue(pilot.Step());
                Assert.AreNotEqual(RunPhase.Defeat, rc.State.Phase);
            }
            Assert.Greater(rc.State.Wave, 30);
            Assert.GreaterOrEqual(rc.State.Gold, 0);
        }
    }
}
