using System.Collections.Generic;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Meta;
using Aetherward.Sim.Run;
using NUnit.Framework;

namespace Aetherward.Tests
{
    public class RunTests
    {
        private static RunController NewRun(ulong seed = 77, params string[] starters)
        {
            if (starters.Length == 0) starters = new[] { "ignis", "terra" };
            return RunController.NewRun(TestContent.Db, seed, starters, 0, RunUnlocks.Everything(TestContent.Db));
        }

        [Test]
        public void ContentCatalogMeetsMvpCounts()
        {
            ContentDatabase db = TestContent.Db;
            int baseRelics = 0, fusions = 0;
            foreach (RelicDef r in db.RelicList) if (r.Fusion) fusions++; else baseRelics++;
            Assert.GreaterOrEqual(baseRelics, 25);
            Assert.AreEqual(fusions, db.Fusions.Count, "every fusion-only relic has exactly one recipe");
            foreach (string launch in new[] { "arcane_echo", "phoenix_feather", "tempest_engine", "absolute_zero", "living_monolith" })
                Assert.IsTrue(db.Relics.ContainsKey(launch), "launch relic id must be preserved: " + launch);
            Assert.GreaterOrEqual(db.Cards.Count, 40);
            Assert.GreaterOrEqual(db.Events.Count, 3);
            foreach (FusionDef f in db.Fusions)
            {
                Assert.IsTrue(db.Relics.ContainsKey(f.A) && db.Relics.ContainsKey(f.B) && db.Relics.ContainsKey(f.Result));
                Assert.IsTrue(db.Relics[f.Result].Fusion);
            }
            foreach (RelicDef r in db.RelicList) Assert.Greater(r.Effects.Count, 0, r.Id + " has no effect");
            foreach (CardDef c in db.CardList) Assert.Greater(c.Effects.Count, 0, c.Id + " has no effect");
        }

        [Test]
        public void NewRunStartsInPrepareWithTwoPlacedHeroes()
        {
            RunController rc = NewRun();
            Assert.AreEqual(RunPhase.Prepare, rc.State.Phase);
            Assert.AreEqual(2, rc.State.Heroes.Count);
            Assert.AreNotEqual(rc.State.Heroes[0].Node, rc.State.Heroes[1].Node);
            foreach (HeroRunState h in rc.State.Heroes) Assert.GreaterOrEqual(h.Node, 0);
        }

        [Test]
        public void PlacingOnOccupiedNodeSwaps()
        {
            RunController rc = NewRun();
            HeroRunState a = rc.State.Heroes[0], b = rc.State.Heroes[1];
            int na = a.Node, nb = b.Node;
            Assert.IsTrue(rc.PlaceHero(a.Uid, nb));
            Assert.AreEqual(nb, a.Node);
            Assert.AreEqual(na, b.Node);
        }

        [Test]
        public void WaveOneGivesGoldXpAndADraft()
        {
            RunController rc = NewRun();
            int gold = rc.State.Gold;
            rc.StartWave();
            rc.Battle.RunToEnd();
            rc.ResolveBattle();
            Assert.AreEqual(RunPhase.Reward, rc.State.Phase);
            Assert.AreEqual(RewardKind.Draft, rc.State.CurrentReward);
            Assert.AreEqual(3, rc.State.Offers.Count);
            Assert.Greater(rc.State.Gold, gold);
            foreach (HeroRunState h in rc.State.Heroes) Assert.AreEqual(1, h.Xp);
        }

        [Test]
        public void DraftNeverOffersDuplicatesOrIneligibleCards()
        {
            for (ulong seed = 1; seed < 40; seed++)
            {
                RunController rc = NewRun(seed);
                var rng = Sim.Core.Pcg32.Derive(seed, "test");
                List<CardDef> cards = DraftGenerator.Generate(rc, rng, 3, false);
                Assert.AreEqual(3, cards.Count);
                var ids = new HashSet<string>();
                foreach (CardDef c in cards)
                {
                    Assert.IsTrue(ids.Add(c.Id), "duplicate " + c.Id);
                    Assert.IsTrue(DraftGenerator.IsEligible(rc, c, false), c.Id);
                    Assert.AreNotEqual(CardType.CursedPact, c.Type);
                    if (!string.IsNullOrEmpty(c.Requires.Hero)) Assert.IsTrue(rc.State.HasHero(c.Requires.Hero));
                }
            }
        }

        [Test]
        public void DraftGuaranteesAnActionableSynergyWhenAvailable()
        {
            for (ulong seed = 1; seed < 30; seed++)
            {
                RunController rc = NewRun(seed, "ignis", "cinder");
                List<CardDef> cards = DraftGenerator.Generate(rc, Sim.Core.Pcg32.Derive(seed, "x"), 3, false);
                bool synergy = false;
                foreach (CardDef c in cards) synergy |= DraftGenerator.IsSynergy(c);
                Assert.IsTrue(synergy, "seed " + seed);
            }
        }

        [Test]
        public void MaxStacksAreRespected()
        {
            RunController rc = NewRun();
            CardDef c = rc.Content.Cards["keen_edge"];
            for (int i = 0; i < 5; i++) rc.AddCard(c.Id);
            Assert.AreEqual(c.MaxStacks, rc.State.CardStacks(c.Id));
            Assert.IsFalse(DraftGenerator.IsEligible(rc, c, false));
        }

        [Test]
        public void ShopPurchaseRequiresGoldAndScalesPrice()
        {
            RunController rc = NewRun();
            rc.State.Wave = 4;
            int p4 = rc.RelicPrice("war_drum");
            rc.State.Wave = 19;
            int p19 = rc.RelicPrice("war_drum");
            Assert.Greater(p19, p4);
            rc.State.Wave = 4;
            rc.State.Phase = RunPhase.Battle; // simulate end of a shop wave
            rc.State.PendingRewards.Clear();
            rc.State.PendingRewards.Add(RewardKind.Shop);
            rc.State.Phase = RunPhase.Reward;
            rc.AdvanceReward();
            Assert.AreEqual(RewardKind.Shop, rc.State.CurrentReward);
            rc.State.Gold = 0;
            for (int i = 0; i < rc.State.Offers.Count; i++)
                if (rc.State.Offers[i].Price > 0) Assert.IsFalse(rc.Choose(i), "should not afford " + rc.State.Offers[i].Id);
            rc.State.Gold = 999;
            int relicIndex = rc.State.Offers.FindIndex(o => o.Kind == OfferKind.Relic);
            Assert.IsTrue(rc.Choose(relicIndex));
            Assert.Less(rc.State.Gold, 999);
            Assert.IsFalse(rc.Choose(relicIndex), "sold items cannot be bought twice");
        }

        [Test]
        public void EvolutionRequiresLevelCapAndEssence()
        {
            RunController rc = NewRun();
            HeroRunState h = rc.State.Heroes[0];
            Assert.IsFalse(rc.Evolve(h.Uid, "ignis_meteor_archmage"));
            h.Level = rc.Content.Economy.LevelCap;
            rc.State.Essence = 0;
            Assert.IsFalse(rc.Evolve(h.Uid, "ignis_meteor_archmage"));
            rc.State.Essence = 10;
            Assert.IsFalse(rc.Evolve(h.Uid, "terra_bedrock_warden"), "foreign branch rejected");
            Assert.IsTrue(rc.Evolve(h.Uid, "ignis_meteor_archmage"));
            Assert.AreEqual(10 - rc.Content.Economy.EvolutionEssence, rc.State.Essence);
            Assert.IsFalse(rc.Evolve(h.Uid, "ignis_ember_weaver"), "only one evolution per run");
        }

        [Test]
        public void EvolvedHeroChangesMechanicsInBattle()
        {
            RunController rc = NewRun();
            HeroRunState h = rc.State.Heroes[0];
            h.Level = 5;
            rc.State.Essence = 5;
            rc.Evolve(h.Uid, "ignis_meteor_archmage");
            Battle b = new Battle(rc.BuildBattleSetup());
            Assert.AreEqual("meteor", b.Heroes[0].Skill.Kind);
        }

        [Test]
        public void FusionReplacesBothComponents()
        {
            RunController rc = NewRun();
            rc.AddRelic("chain_conductor");
            rc.AddRelic("storm_caller");
            CollectionAssert.Contains(rc.State.Relics, "tempest_engine");
            CollectionAssert.DoesNotContain(rc.State.Relics, "chain_conductor");
            CollectionAssert.DoesNotContain(rc.State.Relics, "storm_caller");
        }

        [Test]
        public void PactShowsAndAppliesExactDrawback()
        {
            RunController rc = NewRun();
            float before = rc.CrystalMaxHp;
            CardDef pact = rc.Content.Cards["pact_of_cinders"];
            Assert.IsNotNull(pact.DrawbackKey);
            rc.AddCard(pact.Id);
            Assert.AreEqual(before * 0.75f, rc.CrystalMaxHp, 0.5f);
            Assert.LessOrEqual(rc.State.CrystalHp, rc.CrystalMaxHp);
            CollectionAssert.Contains(rc.State.Pacts, pact.Id);
        }

        [Test]
        public void RelicModifiersDoNotLeakIntoNextRun()
        {
            RunController a = NewRun(5);
            a.AddRelic("war_drum");
            a.AddCard("sharpened_focus");
            float boosted = new Battle(a.BuildBattleSetup()).Heroes[0].Stat(StatId.Attack);
            RunController b = NewRun(5);
            float clean = new Battle(b.BuildBattleSetup()).Heroes[0].Stat(StatId.Attack);
            Assert.Greater(boosted, clean);
            Assert.AreEqual(TestContent.Db.Heroes["ignis"].BaseStats[(int)StatId.Attack], clean, 0.001f, "shared definition untouched");
        }

        [Test]
        public void RevivalCostsGoldAndRestoresHero()
        {
            RunController rc = NewRun();
            HeroRunState h = rc.State.Heroes[0];
            h.Downed = true;
            h.HpFraction = 0f;
            rc.State.Gold = 0;
            Assert.IsFalse(rc.Revive(h.Uid));
            rc.State.Gold = 50;
            Assert.IsTrue(rc.Revive(h.Uid));
            Assert.IsFalse(h.Downed);
            Assert.Less(rc.State.Gold, 50);
        }

        [Test]
        public void SaveRoundTripRestoresRunAndMeta()
        {
            var storage = new MemoryStorage();
            var saves = new SaveService(storage);
            RunController rc = NewRun(99);
            rc.StartWave();
            rc.Battle.RunToEnd();
            rc.ResolveBattle();
            rc.AddRelic("stoneheart");
            saves.SaveRun(rc.State);
            RunState loaded = saves.LoadRun(TestContent.Db);
            Assert.IsNotNull(loaded, saves.LastError);
            Assert.AreEqual(rc.State.Seed, loaded.Seed);
            Assert.AreEqual(rc.State.Gold, loaded.Gold);
            Assert.AreEqual(rc.State.Wave, loaded.Wave);
            Assert.AreEqual(rc.State.Phase, loaded.Phase);
            Assert.AreEqual(rc.State.Offers.Count, loaded.Offers.Count);
            CollectionAssert.AreEqual(rc.State.Relics, loaded.Relics);
            Assert.AreEqual(rc.State.Heroes.Count, loaded.Heroes.Count);

            MetaProfile meta = MetaProfile.CreateDefault(TestContent.Db);
            meta.Codex.Add("reaction:vaporize");
            meta.TotalRuns = 3;
            saves.SaveMeta(meta);
            MetaProfile m2 = saves.LoadMeta(TestContent.Db);
            Assert.AreEqual(3, m2.TotalRuns);
            Assert.IsTrue(m2.Codex.Contains("reaction:vaporize"));
        }

        [Test]
        public void CorruptSaveFallsBackToBackupThenDefault()
        {
            var storage = new MemoryStorage();
            var saves = new SaveService(storage);
            MetaProfile meta = MetaProfile.CreateDefault(TestContent.Db);
            meta.TotalRuns = 1;
            saves.SaveMeta(meta);
            meta.TotalRuns = 2;
            saves.SaveMeta(meta);
            storage.Files["meta"] = storage.Files["meta"].Replace("\"totalRuns\": 2", "\"totalRuns\": 9");
            MetaProfile fromBackup = saves.LoadMeta(TestContent.Db);
            Assert.AreEqual(1, fromBackup.TotalRuns, "checksum mismatch -> backup used");
            storage.Files["meta"] = "{ broken";
            storage.Files["meta.bak"] = "also broken";
            MetaProfile fresh = saves.LoadMeta(TestContent.Db);
            Assert.AreEqual(0, fresh.TotalRuns);
            Assert.Greater(fresh.UnlockedHeroes.Count, 0);
        }

        [Test]
        public void VersionOneRunSaveMigrates()
        {
            var storage = new MemoryStorage();
            var saves = new SaveService(storage);
            RunController rc = NewRun(3);
            saves.SaveRun(rc.State);
            string text = storage.Files["run"].Replace("\"version\": 2", "\"version\": 1");
            storage.Files["run"] = text;
            RunState loaded = saves.LoadRun(TestContent.Db);
            Assert.IsNotNull(loaded, saves.LastError);
            Assert.AreEqual(loaded.CrystalBaseMaxHp, loaded.CrystalKnownMax);
        }

        [Test]
        public void MetaUnlocksVarietyNotStats()
        {
            MetaProfile meta = MetaProfile.CreateDefault(TestContent.Db);
            Assert.IsFalse(meta.UnlockedHeroes.Contains("raiden"));
            RunController rc = NewRun(8);
            new AutoPilot(rc, Strategy.Find("balanced")).PlayToEnd();
            List<string> unlocked = meta.RecordRun(rc, RunResults.Build(rc), 0);
            if (rc.State.Wave >= 6 || rc.State.Phase == RunPhase.Victory) CollectionAssert.Contains(unlocked, "hero:raiden");
            Assert.AreEqual(1, meta.History.Count);
        }

        [TestCase("thunderstorm", 11UL)]
        [TestCase("frozen_fortress", 12UL)]
        [TestCase("magma_engine", 13UL)]
        [TestCase("mixed_burst", 14UL)]
        [TestCase("glass_cannon", 15UL)]
        [TestCase("balanced", 16UL)]
        public void FullRunEndsInVictoryOrDefeatWithoutSoftlock(string strategy, ulong seed)
        {
            RunController rc = RunController.NewRun(TestContent.Db, seed, Strategy.Find(strategy).Starters, 0, RunUnlocks.Everything(TestContent.Db));
            bool finished = new AutoPilot(rc, Strategy.Find(strategy)).PlayToEnd();
            Assert.IsTrue(finished, "run softlocked");
            Assert.IsTrue(rc.State.Finished);
            RunResults res = RunResults.Build(rc);
            Assert.Greater(res.TotalKills, 0);
            Assert.Greater(res.Heroes.Count, 1);
            Assert.LessOrEqual(rc.State.Heroes.Count, 6);
        }

        [Test]
        public void ConsecutiveRunsAreIndependent()
        {
            RunController a = RunController.NewRun(TestContent.Db, 500, new[] { "ignis", "terra" }, 0, RunUnlocks.Everything(TestContent.Db));
            new AutoPilot(a, Strategy.Find("balanced")).PlayToEnd();
            RunController b = RunController.NewRun(TestContent.Db, 500, new[] { "ignis", "terra" }, 0, RunUnlocks.Everything(TestContent.Db));
            new AutoPilot(b, Strategy.Find("balanced")).PlayToEnd();
            Assert.AreEqual(a.State.Wave, b.State.Wave);
            Assert.AreEqual(a.State.Gold, b.State.Gold);
            Assert.AreEqual(a.State.CrystalHp, b.State.CrystalHp, 0.001f);
        }
    }
}
