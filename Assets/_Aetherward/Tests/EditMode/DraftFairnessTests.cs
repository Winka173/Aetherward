using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using Aetherward.Sim.Meta;
using Aetherward.Sim.Run;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>Phase 4 probability/fairness validation for drafts, shops, locks and the economy.</summary>
    public class DraftFairnessTests
    {
        private static RunController Shop(ulong seed, int gold = 200)
        {
            ContentDatabase db = TestContent.Db;
            RunController rc = RunController.NewRun(db, seed, new[] { "ignis", "terra" }, 0, RunUnlocks.Everything(db));
            rc.State.Gold = gold;
            rc.State.Wave = 4;
            rc.State.PendingRewards.Add(RewardKind.Shop);
            rc.AdvanceReward();
            return rc;
        }

        [Test]
        public void DraftsAreDistinctActionableAndNotThreeCopiesOfThePlan()
        {
            ContentDatabase db = TestContent.Db;
            int noSynergy = 0, allSynergy = 0;
            for (ulong seed = 1; seed <= 200; seed++)
            {
                RunController rc = RunController.NewRun(db, seed, new[] { "ignis", "terra" }, 0, RunUnlocks.Everything(db));
                rc.State.Wave = 1 + (int)(seed % 18);
                List<CardDef> cards = DraftGenerator.Generate(rc, Pcg32.Derive(seed, "test"), 3, false);
                Assert.AreEqual(cards.Count, new HashSet<CardDef>(cards).Count, "duplicate card in one draft");
                foreach (CardDef c in cards) Assert.IsTrue(DraftGenerator.IsEligible(rc, c, false), c.Id + " is not usable");
                if (!cards.Exists(DraftGenerator.IsSynergy)) noSynergy++;
                if (cards.Count == 3 && cards.TrueForAll(DraftGenerator.IsSynergy)) allSynergy++;
            }
            Assert.AreEqual(0, noSynergy, "every draft has a currently actionable choice");
            Assert.AreEqual(0, allSynergy, "every draft keeps a strategic alternative");
        }

        [Test]
        public void SameSeedAndChoicesGiveTheSameRewardSequence()
        {
            ContentDatabase db = TestContent.Db;
            List<string> Play(ulong seed)
            {
                RunController rc = RunController.NewRun(db, seed, new[] { "ignis", "terra" }, 0, RunUnlocks.Everything(db));
                var log = new List<string>();
                var pilot = new AutoPilot(rc, Strategy.Find("balanced"));
                Assert.IsTrue(pilot.PlayToEnd());
                foreach (string line in rc.State.Log) if (line.StartsWith("offer")) log.Add(line);
                return log;
            }
            CollectionAssert.AreEqual(Play(55), Play(55));
            CollectionAssert.AreNotEqual(Play(55), Play(56));
        }

        [Test]
        public void ShopLockSurvivesRerollsAndTheNextShopAndClearsOnPurchase()
        {
            RunController rc = Shop(9);
            int idx = rc.State.Offers.FindIndex(o => o.Kind == OfferKind.Relic);
            Assert.GreaterOrEqual(idx, 0);
            string id = rc.State.Offers[idx].Id;
            int price = rc.State.Offers[idx].Price;
            Assert.IsTrue(rc.ToggleLock(idx));
            Assert.IsTrue(rc.Reroll());
            Assert.IsTrue(rc.State.Offers.Exists(o => o.Id == id && o.Tag == "locked"), "lock survives a reroll");
            rc.Skip();
            rc.State.PendingRewards.Add(RewardKind.Shop);
            rc.AdvanceReward();
            int again = rc.State.Offers.FindIndex(o => o.Id == id);
            Assert.GreaterOrEqual(again, 0, "lock carries into the next shop");
            Assert.AreEqual(price, rc.State.Offers[again].Price, "locked price is kept");
            Assert.IsTrue(rc.Choose(again));
            Assert.IsNull(rc.State.LockedOffer, "buying the locked offer clears the lock");
            var saves = new SaveService(new MemoryStorage());
            rc.State.LockedOffer = new Offer { Kind = OfferKind.Card, Id = "keen_edge", Price = 7 };
            saves.SaveRun(rc.State);
            Assert.AreEqual("keen_edge", saves.LoadRun(TestContent.Db).LockedOffer.Id);
        }

        [Test]
        public void RerollCostsEscalateAndGoldNeverGoesNegative()
        {
            RunController rc = Shop(10, 30);
            int last = -1, rerolls = 0;
            while (rc.Reroll())
            {
                Assert.GreaterOrEqual(rc.State.Gold, 0);
                Assert.Greater(rc.RerollCost, last == -1 ? -1 : last - 1);
                last = rc.RerollCost;
                if (++rerolls > 100) Assert.Fail("rerolls never get more expensive");
            }
            Assert.GreaterOrEqual(rc.State.Gold, 0);
            Assert.Less(rc.State.Gold, rc.RerollCost, "rerolling stops only when unaffordable");
        }
    }
}
