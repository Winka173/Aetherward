using Aetherward.Sim.Content;
using Aetherward.Sim.Run;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>P9 counterexample regressions found by the balance lab (Reports/Balance/lab_ascension_ramp.md).</summary>
    public class BalanceLabRegressionTests
    {
        private static int PlayWave(string strategy, ulong seed, int asc)
        {
            ContentDatabase db = TestContent.Db;
            Strategy st = Strategy.Find(strategy);
            RunController rc = RunController.NewModeRun(db, GameMode.Classic, seed, st.Starters, asc, RunUnlocks.Everything(db), null);
            new AutoPilot(rc, st).PlayToEnd();
            return rc.State.Phase == RunPhase.Victory ? 21 : rc.State.Wave;
        }

        [Test]
        public void AutoArrangeNoLongerLeavesTheWestLaneEmptyOnWaveTwo()
        {
            // Seed 5000 / stall: both starters stood East while wave 2 also attacked West -> defeat at wave 2.
            Assert.Greater(PlayWave("stall", 5000, 0), 2);
        }

        [Test]
        public void HighAscensionRunsAreNotDecidedAtWaveTwo()
        {
            int early = 0;
            for (ulong i = 0; i < 8; i++) if (PlayWave("thunderstorm", 5000 + i * 7919, 10) <= 2) early++;
            Assert.LessOrEqual(early, 4, "at most half of A10 runs may end by wave 2 (was nearly all before the early ramp)");
        }

        [Test]
        public void EarlyRampOnlyScalesTheAscensionBonus()
        {
            DifficultyDef d = TestContent.Db.Difficulty;
            Assert.AreEqual(d.EarlyRampStart, d.LevelBonusShare(1), 1e-5f);
            Assert.AreEqual(1f, d.LevelBonusShare(d.EarlyRampFullWave), 1e-5f);
            Assert.AreEqual(1f, d.LevelBonusShare(20), 1e-5f);
        }
    }
}
