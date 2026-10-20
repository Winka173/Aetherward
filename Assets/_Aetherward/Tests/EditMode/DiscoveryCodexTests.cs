using System.IO;
using System.Linq;
using Aetherward.Sim.Content;
using Aetherward.Sim.Meta;
using Aetherward.Sim.Run;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>P5 Discovery Codex + validation scenario 6 (codex survives content additions and save migration).</summary>
    public class DiscoveryCodexTests
    {
        private static string Fixture(string name) =>
            File.ReadAllText(Path.Combine(TestContent.ContentDirectory, "..", "..", "Tests", "EditMode", "Fixtures", "mvp_0dde0cd", name + ".json"));

        [Test]
        public void MvpCodexSurvivesMigrationAndUnknownIdsArePreserved()
        {
            ContentDatabase db = TestContent.Db;
            var mem = new MemoryStorage();
            mem.Files["meta"] = Fixture("meta");
            var saves = new SaveService(mem);
            MetaProfile old = saves.LoadMeta(db);
            int codexBefore = old.Codex.Count;
            Assert.Greater(codexBefore, 0, "fixture has codex progress");
            Assert.IsEmpty(old.Milestones, "new fields default to nothing yet");
            Assert.IsEmpty(old.WinningFormations);
            // Content added later (or removed temporarily) must not erase discoveries.
            old.Codex.Add("hero:future_hero_from_a_content_update");
            old.Milestones.Add("first_fusion");
            saves.SaveMeta(old);
            MetaProfile again = saves.LoadMeta(db);
            Assert.AreEqual(codexBefore + 1, again.Codex.Count);
            Assert.IsTrue(again.Codex.Contains("hero:future_hero_from_a_content_update"));
            Assert.IsTrue(again.Milestones.Contains("first_fusion"));
            CollectionAssert.IsSubsetOf(old.Codex.ToList(), again.Codex.ToList());
        }

        [Test]
        public void VictoryRecordsMilestonesAndAWinningFormationOnce()
        {
            ContentDatabase db = TestContent.Db;
            RunController rc = null;
            for (ulong seed = 1; seed < 400; seed++)
            {
                rc = RunController.NewRun(db, seed, new[] { "ignis", "terra" }, 0, RunUnlocks.Everything(db));
                new AutoPilot(rc, Strategy.Find("thunderstorm")).PlayToEnd();
                if (rc.State.Phase == RunPhase.Victory) break;
            }
            Assert.AreEqual(RunPhase.Victory, rc.State.Phase, "found a winning seed");
            RunResults r = RunResults.Build(rc);
            var meta = MetaProfile.CreateDefault(db);
            meta.RecordRun(rc, r, 1_760_000_000L);
            Assert.Contains("first_victory", meta.LastMilestones);
            Assert.AreEqual(1, meta.WinningFormations.Count);
            FormationSnapshot f = meta.WinningFormations[0];
            Assert.AreEqual(rc.State.Heroes.Count, f.Heroes.Count);
            StringAssert.StartsWith("AW1 seed=", f.ShareCode);
            meta.RecordRun(rc, r, 1_760_000_100L);
            Assert.IsFalse(meta.LastMilestones.Contains("first_victory"), "a milestone is earned once");
            var saves = new SaveService(new MemoryStorage());
            saves.SaveMeta(meta);
            MetaProfile loaded = saves.LoadMeta(db);
            Assert.AreEqual(2, loaded.WinningFormations.Count);
            Assert.AreEqual(1_760_000_000L, loaded.WinningFormations[1].UnixTime, "unix time keeps full precision");
            Assert.AreEqual(meta.BestReactionsPerSecond, loaded.BestReactionsPerSecond);
            CollectionAssert.AreEquivalent(meta.Milestones, loaded.Milestones);
        }

        [Test]
        public void InBattleDiscoveriesAreAnnouncedOncePerRunAndOnlyWhenNew()
        {
            var meta = new MetaProfile();
            meta.Codex.Add("reaction:vaporize");
            meta.BestReactionsPerSecond = 5;
            var t = new DiscoveryTracker(meta);
            Assert.IsNull(t.OnReaction("vaporize"), "already discovered");
            Assert.AreEqual("reaction:melt", t.OnReaction("melt"));
            Assert.IsNull(t.OnReaction("melt"), "announced once");
            Assert.IsNull(t.OnPeakChain(5), "ties are not a new best");
            Assert.AreEqual("best_chain", t.OnPeakChain(6));
            Assert.IsNull(t.OnPeakChain(9), "best chain toast once per run");
            Assert.IsFalse(meta.Codex.Contains("reaction:melt"), "persisted only at run end (RecordRun)");
        }
    }
}
