using System.Collections.Generic;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using Aetherward.Sim.Meta;
using Aetherward.Sim.Run;
using NUnit.Framework;

namespace Aetherward.Tests
{
    public class TraitTests
    {
        [Test]
        public void RolledTraitsAreAlwaysEligibleAndRarityWeighted()
        {
            ContentDatabase db = TestContent.Db;
            var counts = new Dictionary<string, int>();
            for (ulong seed = 1; seed <= 150; seed++)
            {
                RunController rc = RunController.NewRun(db, seed, new[] { "terra", "ignis" }, 0, RunUnlocks.Everything(db));
                foreach (HeroDef h in db.HeroList)
                {
                    string t = rc.RollTrait(h.Id);
                    Assert.IsNotNull(t);
                    Assert.IsTrue(db.Traits[t].EligibleFor(h), t + " is not eligible for " + h.Id);
                    counts.TryGetValue(t, out int c);
                    counts[t] = c + 1;
                }
            }
            Assert.Greater(counts.Count, 8, "most traits should appear across many rolls");
            Assert.Greater(counts["quick_channel"], counts["tactician"], "common traits roll more often than epic ones");
        }

        [Test]
        public void TraitStatsApplyOnlyToTheirHero()
        {
            BattleSetup s = TestContent.Setup(1, 3, ("volt", 4), ("ignis", 8));
            float plainHp = new Battle(s).Heroes[0].MaxHp;
            s.Heroes[0].TraitId = "fragile_genius";
            Battle b = new Battle(s);
            Assert.AreEqual(plainHp * 0.8f, b.Heroes[0].MaxHp, 0.5f);
            Assert.AreEqual(1.25f, b.Heroes[0].Stat(StatId.SkillPower), 1e-3f);
            Assert.AreEqual(1f, b.Heroes[1].Stat(StatId.SkillPower), 1e-3f, "other heroes unaffected");
        }

        [Test]
        public void ExecutionerAddsDamageOnlyBelowThreshold()
        {
            BattleSetup s = TestContent.Setup(1, 3, ("raiden", 4));
            s.Heroes[0].TraitId = "executioner";
            s.Wave = new WaveDef { Number = 1, TimeLimit = 999f };
            Battle b = new Battle(s);
            EnemyUnit e = b.SpawnEnemy(b.Content.Enemies["grunt"], 0, false, null, new Vec2(6f, 0f));
            e.MaxHp = 1000f;
            e.Defense = 0f;
            e.Hp = 900f;
            float high = b.DealDamage(e, new DamageRequest { Source = b.Heroes[0], Attack = 100f, Multiplier = 1f, Kind = DamageKind.Trigger, IgnoreDefense = true });
            e.Hp = 200f;
            float low = b.DealDamage(e, new DamageRequest { Source = b.Heroes[0], Attack = 100f, Multiplier = 1f, Kind = DamageKind.Trigger, IgnoreDefense = true });
            Assert.AreEqual(high * 1.4f, low, 0.5f);
        }

        [Test]
        public void TwinCasterEchoesWithACooldown()
        {
            BattleSetup s = TestContent.Setup(6, 11, ("ignis", 4), ("terra", 0));
            Battle plain = new Battle(s);
            plain.RunToEnd();
            s.Heroes[0].TraitId = "twin_caster";
            Battle twin = new Battle(s);
            twin.RunToEnd();
            Assert.Greater(twin.Heroes[0].SkillCasts, plain.Heroes[0].SkillCasts, "echoes add casts");
            Assert.LessOrEqual(twin.Heroes[0].SkillCasts, plain.Heroes[0].SkillCasts * 2, "echo cooldown bounds extra casts");
        }

        [Test]
        public void TraitSurvivesSaveAndDoesNotLeakIntoANewRun()
        {
            ContentDatabase db = TestContent.Db;
            RunController rc = RunController.NewRun(db, 77, new[] { "terra", "ignis" }, 0, RunUnlocks.Everything(db));
            rc.State.Heroes[0].TraitId = "steadfast";
            var saves = new SaveService(new MemoryStorage());
            saves.SaveRun(rc.State);
            RunState loaded = saves.LoadRun(db);
            Assert.AreEqual("steadfast", loaded.Heroes[0].TraitId);
            RunController fresh = RunController.NewRun(db, 78, new[] { "terra", "ignis" }, 0, RunUnlocks.Everything(db));
            foreach (HeroRunState h in fresh.State.Heroes) Assert.IsNull(h.TraitId, "starters never carry traits");
        }

        [Test]
        public void RecruitOffersCarryAnEligibleTrait()
        {
            ContentDatabase db = TestContent.Db;
            RunController rc = RunController.NewRun(db, 5, new[] { "terra", "ignis" }, 0, RunUnlocks.Everything(db));
            rc.State.PendingRewards.Add(RewardKind.Recruit);
            rc.AdvanceReward();
            Assert.AreEqual(RewardKind.Recruit, rc.State.CurrentReward);
            foreach (Offer o in rc.State.Offers)
            {
                Assert.IsNotNull(o.TraitId);
                Assert.IsTrue(db.Traits[o.TraitId].EligibleFor(db.Heroes[o.Id]));
            }
            rc.State.Gold = 999;
            Offer pick = rc.State.Offers[0];
            Assert.IsTrue(rc.Choose(0));
            Assert.AreEqual(pick.TraitId, rc.State.Heroes[rc.State.Heroes.Count - 1].TraitId);
        }
    }
}
