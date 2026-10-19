using System.Linq;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Meta;
using Aetherward.Sim.Run;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>Phase 8 run breakdown: provenance without double counting, turning points, share code, persistence.</summary>
    public class RunBreakdownTests
    {
        [Test]
        public void ProvenanceMatchesHeroTotalsAndBreakdownIsFilled()
        {
            ContentDatabase db = TestContent.Db;
            RunController rc = RunController.NewRun(db, 31, new[] { "ignis", "terra" }, 0, RunUnlocks.Everything(db));
            Assert.IsTrue(new AutoPilot(rc, Strategy.Find("balanced")).PlayToEnd());
            RunResults r = RunResults.Build(rc);
            float provenance = 0f;
            for (int k = 0; k < r.DamageByKind.Length; k++) if (k != (int)DamageKind.Enemy) provenance += r.DamageByKind[k];
            float heroes = r.Heroes.Sum(h => h.DamageDealt);
            Assert.Greater(provenance, 0f);
            // Every hero-sourced hit is in both totals; the provenance total may only exceed it by sourceless damage (hazards, collapses).
            Assert.GreaterOrEqual(provenance + 1f, heroes, "a hero hit is missing from provenance");
            Assert.Less(provenance, heroes * 1.25f + 1f, "provenance double-counts hits");
            Assert.IsNotNull(r.MostDamagingThreat);
            Assert.Greater(r.ClosestSaveWave, 0);
            Assert.LessOrEqual(r.ClosestSaveHpFraction, 1f);
            StringAssert.StartsWith("AW1 seed=", rc.ShareCode());
            StringAssert.Contains("heroes=ignis", rc.ShareCode());
        }

        [Test]
        public void BreakdownFieldsSurviveSave()
        {
            ContentDatabase db = TestContent.Db;
            RunController rc = RunController.NewRun(db, 32, new[] { "ignis", "terra" }, 0, RunUnlocks.Everything(db));
            rc.State.DamageByKind[(int)DamageKind.Basic] = 1234f;
            rc.State.MaxProcDepth = 3;
            rc.State.CrystalDamageByEnemy["grunt"] = 55f;
            var saves = new SaveService(new MemoryStorage());
            saves.SaveRun(rc.State);
            RunState loaded = saves.LoadRun(db);
            Assert.AreEqual(rc.State.DamageByKind[(int)DamageKind.Basic], loaded.DamageByKind[(int)DamageKind.Basic], 1f);
            Assert.AreEqual(3, loaded.MaxProcDepth);
            Assert.AreEqual(55f, loaded.CrystalDamageByEnemy["grunt"], 0.01f);
        }
    }
}
