using System.IO;
using Aetherward.Sim.Content;
using Aetherward.Sim.Meta;
using Aetherward.Sim.Run;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>Phase 12: historical save fixtures (written by the MVP-era code at commit 0dde0cd) and failure recovery.</summary>
    public class SaveCompatTests
    {
        private static string Fixture(string name) =>
            File.ReadAllText(Path.Combine(TestContent.ContentDirectory, "..", "..", "Tests", "EditMode", "Fixtures", "mvp_0dde0cd", name + ".json"));

        [Test]
        public void MvpEraSavesLoadIntoTheCurrentBuild()
        {
            ContentDatabase db = TestContent.Db;
            var mem = new MemoryStorage();
            mem.Files["run"] = Fixture("run");
            mem.Files["meta"] = Fixture("meta");
            mem.Files["settings"] = Fixture("settings");
            var saves = new SaveService(mem);
            RunState run = saves.LoadRun(db);
            Assert.IsNotNull(run, saves.LastError);
            Assert.AreEqual(2, run.Heroes.Count);
            Assert.AreEqual("ignis", run.Heroes[0].DefId);
            Assert.AreEqual(GameMode.Classic, run.Mode, "new fields default sensibly");
            Assert.IsEmpty(run.HeroPool, "old runs keep the full offer pool");
            RunController rc = new RunController(db, run, RunUnlocks.Everything(db));
            Assert.IsTrue(new AutoPilot(rc, Strategy.Find("balanced")).PlayToEnd(), "an MVP-era run can be finished");
            MetaProfile meta = saves.LoadMeta(db);
            Assert.Greater(meta.TotalRuns, 0);
            Assert.IsTrue(meta.UnlockedBiomes.Contains(db.DefaultBiome.Id));
            Assert.IsNotNull(saves.LoadSettings());
        }

        [Test]
        public void CorruptSavesFallBackThroughTwoBackupsAndAreQuarantined()
        {
            ContentDatabase db = TestContent.Db;
            var mem = new MemoryStorage();
            var saves = new SaveService(mem);
            MetaProfile m = MetaProfile.CreateDefault(db);
            for (int i = 1; i <= 3; i++)
            {
                m.TotalRuns = i;
                saves.SaveMeta(m);
            }
            Assert.IsTrue(mem.Files.ContainsKey("meta.bak") && mem.Files.ContainsKey("meta.bak2"));
            mem.Files["meta"] = "{ broken";
            Assert.AreEqual(2, saves.LoadMeta(db).TotalRuns, "falls back to .bak");
            Assert.AreEqual("{ broken", mem.Files["meta.corrupt"], "the unreadable file is kept, not wiped");
            mem.Files["meta.bak"] = mem.Files["meta.bak"].Replace("\"totalRuns\": 2", "\"totalRuns\": 9");
            Assert.AreEqual(1, saves.LoadMeta(db).TotalRuns, "checksum mismatch falls back to .bak2");
            mem.Files["meta.bak2"] = "";
            Assert.AreEqual(0, saves.LoadMeta(db).TotalRuns, "all broken: a clean profile, never a crash");
        }

        [Test]
        public void SavesFromANewerBuildAreRefusedNotOverwritten()
        {
            var mem = new MemoryStorage();
            mem.Files["meta"] = Fixture("meta").Replace("\"version\": 2", "\"version\": 99");
            var saves = new SaveService(mem);
            MetaProfile m = saves.LoadMeta(TestContent.Db);
            Assert.AreEqual(0, m.TotalRuns);
            StringAssert.Contains("newer version", saves.LastError);
            Assert.IsTrue(mem.Files.ContainsKey("meta.corrupt"), "the newer save is preserved for a later update");
        }
    }
}
