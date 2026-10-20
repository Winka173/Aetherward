using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Meta;
using Aetherward.Sim.Run;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>P2 Training Chamber + validation scenario 4 (reproducible, no rewards, campaign saves untouched).</summary>
    public class TrainingChamberTests
    {
        private static TrainingConfig Team(DummyProfile p, float seconds = 20f)
        {
            var c = new TrainingConfig { Profile = p, Seconds = seconds, Seed = 3 };
            c.Heroes.Add(new TrainingHero { HeroId = "marina", Node = 0 });
            c.Heroes.Add(new TrainingHero { HeroId = "volt", Node = 1 });
            c.Heroes.Add(new TrainingHero { HeroId = "terra", Node = 4 });
            return c;
        }

        [Test]
        public void ResultsAreReproducibleAndSourced()
        {
            ContentDatabase db = TestContent.Db;
            TrainingReport a = TrainingChamber.Run(db, Team(DummyProfile.Swarm));
            TrainingReport b = TrainingChamber.Run(db, Team(DummyProfile.Swarm));
            Assert.AreEqual(a.Fingerprint, b.Fingerprint);
            Assert.Greater(a.RawDps, 0f);
            Assert.Greater(a.Kills, 0);
            Assert.That(a.HardCcUptime, Is.InRange(0f, 1f));
            Assert.That(a.HeroIdleShare, Is.InRange(0f, 1f));
            float sum = 0f;
            foreach (float d in a.HeroDamage.Values) sum += d;
            Assert.Greater(sum, 0f);
            Assert.Contains("training.note.crystal_immortal", a.Notes, "dummy differences are disclosed");
        }

        [Test]
        public void ProfilesStressDifferentThings()
        {
            ContentDatabase db = TestContent.Db;
            TrainingReport swarm = TrainingChamber.Run(db, Team(DummyProfile.Swarm));
            TrainingReport boss = TrainingChamber.Run(db, Team(DummyProfile.Boss, 30f));
            TrainingReport armored = TrainingChamber.Run(db, Team(DummyProfile.ArmoredElite));
            Assert.Greater(swarm.Kills, boss.Kills);
            Assert.Greater(armored.AvgTimeToKill + 0.001f, swarm.AvgTimeToKill, "elite armour takes longer to kill");
            Assert.Contains("training.note.boss_alone", boss.Notes);
            foreach (DummyProfile p in System.Enum.GetValues(typeof(DummyProfile)))
                Assert.DoesNotThrow(() => TrainingChamber.Run(db, Team(p, 15f)), p.ToString());
        }

        [Test]
        public void TrainingNeverTouchesSavesOrMetaAndRespectsUnlocks()
        {
            ContentDatabase db = TestContent.Db;
            var storage = new MemoryStorage();
            var saves = new SaveService(storage);
            var meta = new MetaProfile();
            meta.UnlockedHeroes.Add("marina");
            meta.UnlockedHeroes.Add("volt");
            meta.UnlockedHeroes.Add("terra");
            saves.SaveMeta(meta);
            string before = storage.Read("meta");
            int runsBefore = meta.TotalRuns;
            TrainingChamber.Run(db, Team(DummyProfile.HighMobility));
            Assert.AreEqual(before, storage.Read("meta"), "meta save unchanged");
            Assert.IsNull(storage.Read("run"), "no campaign run created");
            Assert.AreEqual(runsBefore, meta.TotalRuns);
            TrainingConfig locked = Team(DummyProfile.Swarm);
            locked.Heroes.Add(new TrainingHero { HeroId = "zerith", Node = 6 });
            Assert.IsFalse(TrainingChamber.CanUse(db, locked, meta.UnlockedHeroes, out string why));
            Assert.AreEqual("locked:zerith", why);
            locked.Sandbox = true;
            Assert.IsTrue(TrainingChamber.CanUse(db, locked, meta.UnlockedHeroes, out _), "sandbox exception is explicit");
            Assert.Contains("training.note.sandbox", TrainingChamber.Run(db, locked).Notes);
        }
    }
}
