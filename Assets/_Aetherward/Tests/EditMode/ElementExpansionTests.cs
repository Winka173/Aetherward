using System.Collections.Generic;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>Twelve-element model: pair coverage, new statuses, declarative reactions and their caps.</summary>
    public class ElementExpansionTests
    {
        private static EnemyUnit Dummy(Battle b, float hp = 100000f, Vec2? at = null, string id = "grunt")
        {
            EnemyUnit e = b.SpawnEnemy(b.Content.Enemies[id], 0, false, null, at ?? new Vec2(6f, 0f));
            e.MaxHp = e.Hp = hp;
            e.Defense = 0f;
            e.Speed = 0f;
            return e;
        }

        [Test]
        public void EverySixtySixPairHasAnExplicitCategory()
        {
            ContentDatabase db = TestContent.Db;
            Element[] all = ElementUtil.All;
            Assert.AreEqual(12, all.Length);
            int pairs = 0, signature = 0, generic = 0, neutral = 0;
            for (int i = 0; i < all.Length; i++)
            {
                for (int j = i + 1; j < all.Length; j++)
                {
                    pairs++;
                    ReactionCategory c = db.CategoryFor(all[i], all[j]);
                    Assert.AreEqual(c, db.CategoryFor(all[j], all[i]));
                    ReactionDef r = db.ReactionFor(all[i], all[j]);
                    if (c == ReactionCategory.Neutral || c == ReactionCategory.BlockedByDesign)
                    {
                        Assert.IsNull(r);
                        neutral++;
                    }
                    else
                    {
                        Assert.IsNotNull(r, all[i] + "+" + all[j]);
                        Assert.AreSame(r, db.ReactionFor(all[j], all[i]));
                        if (c == ReactionCategory.Signature) signature++;
                        else generic++;
                    }
                }
            }
            Assert.AreEqual(66, pairs);
            Assert.AreEqual(35, signature, "15 launch + 20 expansion signature reactions");
            Assert.That(signature, Is.InRange(ContentValidator.MinSignature, ContentValidator.MaxSignature));
            Assert.AreEqual(66, signature + generic + neutral);
            Assert.Greater(neutral, 0);
        }

        [Test]
        public void GenericInteractionsHaveDistinctReadableNames()
        {
            ContentDatabase db = TestContent.Db;
            var loc = new Localization(db, "en");
            var names = new HashSet<string>();
            foreach (ReactionDef r in db.Reactions.Values)
            {
                string n = loc.ReactionName(r.Id);
                Assert.IsFalse(n.StartsWith("reaction."), r.Id + " has no display name");
                Assert.IsFalse(n.Contains("{"), r.Id + " name not formatted: " + n);
                Assert.IsTrue(names.Add(n), "two reactions share the popup name " + n);
            }
            Assert.AreEqual("Lightning·Light Burst", loc.ReactionName("generic_lightning_light"));
        }

        [Test]
        public void SpecifiedPairsProduceTheirNamedReactions()
        {
            ContentDatabase db = TestContent.Db;
            Assert.AreEqual("eclipse", db.ReactionFor(Element.Light, Element.Shadow).Id);
            Assert.AreEqual("wildfire", db.ReactionFor(Element.Nature, Element.Fire).Id);
            Assert.AreEqual("blight_garden", db.ReactionFor(Element.Poison, Element.Nature).Id);
            Assert.AreEqual("singularity", db.ReactionFor(Element.Void, Element.Wind).Id);
            foreach (var (a, b) in new[] { (Element.Light, Element.Fire), (Element.Light, Element.Water), (Element.Shadow, Element.Fire),
                                           (Element.Shadow, Element.Water), (Element.Arcane, Element.Void) })
            {
                ReactionDef r = db.ReactionFor(a, b);
                Assert.IsNotNull(r, a + "+" + b + " must be supported");
                Assert.IsFalse(r.AutoNamed, a + "+" + b + " uses an authored interaction");
            }
        }

        [Test]
        public void NeutralPairCoexistsWithoutReacting()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit e = Dummy(b);
            b.ApplyElement(e, Element.Light, 1f, null, 0);
            b.ApplyElement(e, Element.Poison, 1f, null, 0);
            Assert.AreEqual(0, b.Stats.TotalReactions);
            Assert.IsTrue(e.HasAura(Element.Light) && e.HasAura(Element.Poison));
            Assert.Greater(e.PoisonStacks, 0);
            Assert.IsTrue(e.Illuminated);
        }

        [Test]
        public void NeutralAuraIsSkippedForAReactingAura()
        {
            // Earth (neutral with Poison) is stronger, but Poison still finds the Fire aura.
            Battle b = TestContent.EmptyBattle();
            EnemyUnit e = Dummy(b);
            e.Aura[(int)Element.Earth] = 2f;
            e.Aura[(int)Element.Fire] = 1f;
            b.ApplyElement(e, Element.Poison, 1f, null, 0);
            Assert.IsTrue(b.Stats.ReactionCounts.ContainsKey("toxic_combustion"));
        }

        [Test]
        public void IlluminatePurgesShieldsAndWeakensEnemyDamage()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit e = Dummy(b);
            e.Shield = 100f;
            e.SpeedBuff = 0.25f;
            b.ApplyElement(e, Element.Light, 1f, null, 0);
            Assert.AreEqual(50f, e.Shield, 0.01f);
            Assert.AreEqual(0f, e.SpeedBuff);
            float before = b.Crystal.Hp;
            b.DamageCrystal(100f, e);
            Assert.AreEqual(85f, before - b.Crystal.Hp, 0.5f, "Illuminated enemies deal 15% less");
        }

        [Test]
        public void DoomExecutesNonBossesAndAmplifiesBosses()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit grunt = Dummy(b, 1000f);
            b.AddDoom(grunt, 5, null);
            Assert.AreEqual(0.2f, b.DoomThreshold(grunt), 1e-4f);
            grunt.Hp = 250f;
            b.DealDamage(grunt, new DamageRequest { Attack = 60f, Multiplier = 1f, Kind = DamageKind.Trigger, IgnoreDefense = true });
            Assert.IsFalse(grunt.Alive, "190/1000 HP with 5 Doom (20%) is executed");

            EnemyUnit boss = Dummy(b, 1e6f, new Vec2(4f, 3f), "rift_warden");
            b.AddDoom(boss, 5, null);
            Assert.AreEqual(0f, b.DoomThreshold(boss), "bosses are never executed by Doom");
            boss.Hp = 1000f;
            b.DealDamage(boss, new DamageRequest { Attack = 100f, Multiplier = 1f, Kind = DamageKind.Trigger, IgnoreDefense = true });
            Assert.IsTrue(boss.Alive);
            Assert.Greater(1000f - boss.Hp, 100f, "Doom stacks amplify boss damage");

            EnemyUnit cap = Dummy(b, 1000f, new Vec2(3f, -3f));
            b.AddDoom(cap, 50, null);
            Assert.AreEqual(Battle.DoomMaxStacks, cap.DoomStacks);
        }

        [Test]
        public void PoisonStacksAreCappedCorrodeAndSpreadBoundedOnDeath()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit a = Dummy(b, 100f, new Vec2(6f, 0f));
            EnemyUnit n1 = Dummy(b, 1e6f, new Vec2(6.8f, 0f));
            b.AddPoison(a, 30, 5f, null);
            Assert.AreEqual(Battle.PoisonMaxStacks, a.PoisonStacks);
            Assert.IsTrue(a.Corroded);
            a.Defense = 100f;
            Assert.AreEqual(70f, b.EffectiveDefense(a), 0.01f);
            b.Grid.Rebuild(b.Enemies);
            b.DealDamage(a, new DamageRequest { Attack = 1000f, Multiplier = 1f, Kind = DamageKind.Trigger, IgnoreDefense = true });
            Assert.IsFalse(a.Alive);
            Assert.AreEqual(5, n1.PoisonStacks, "half the stacks jump to the nearest enemy");
            Assert.AreEqual(1, n1.ContagionDepth);

            n1.ContagionDepth = Battle.MaxContagionDepth;
            EnemyUnit n2 = Dummy(b, 1e6f, new Vec2(7.4f, 0f));
            n1.MaxHp = n1.Hp = 10f;
            b.Grid.Rebuild(b.Enemies);
            b.DealDamage(n1, new DamageRequest { Attack = 1000f, Multiplier = 1f, Kind = DamageKind.Trigger, IgnoreDefense = true });
            Assert.AreEqual(0, n2.PoisonStacks, "contagion stops at the maximum depth");
        }

        [Test]
        public void PoisonTicksDealDamageOverTime()
        {
            Battle b = TestContent.EmptyBattle(("terra", 0));
            EnemyUnit e = Dummy(b, 1e6f, new Vec2(11f, 6f));
            b.AddPoison(e, 6, 5f, null);
            for (int i = 0; i < 60; i++) b.Tick();
            Assert.Less(e.Hp, 1e6f);
            Assert.Greater(b.Stats.ElementDamage[(int)Element.Poison], 0f);
        }

        [Test]
        public void RootHoldsPositionWithImmunityAndNeverRootsBosses()
        {
            Battle b = TestContent.EmptyBattle(("terra", 0));
            EnemyUnit e = b.SpawnEnemy(b.Content.Enemies["grunt"], 0, false, null, new Vec2(9f, 1.2f));
            b.ApplyElement(e, Element.Nature, 1f, null, 0);
            Assert.IsTrue(e.Rooted);
            Vec2 at = e.Pos;
            for (int i = 0; i < 10; i++) b.Tick();
            Assert.AreEqual(at.X, e.Pos.X, 0.05f, "rooted enemies hold position");
            for (int i = 0; i < 30; i++) b.Tick();
            Assert.IsFalse(e.Rooted);
            Assert.Greater(e.RootImmune, 0f);
            b.Root(e, 1f);
            Assert.IsFalse(e.Rooted, "immunity window prevents permanent root");

            EnemyUnit boss = b.SpawnEnemy(b.Content.Enemies["siegebreaker_golem"], 1, false, null, null);
            b.Root(boss, 1f);
            Assert.IsFalse(boss.Rooted);
            Assert.Greater(boss.SlowTimer, 0f, "bosses are slowed instead");
        }

        [Test]
        public void ResonantAmplifiesTheNextReactionOnce()
        {
            float Melt(bool resonant)
            {
                Battle b = TestContent.EmptyBattle();
                EnemyUnit e = Dummy(b);
                if (resonant) e.ResonantTimer = 5f;
                b.ApplyElement(e, Element.Ice, 1f, null, 0);
                b.ApplyElement(e, Element.Fire, 1f, null, 0);
                Assert.AreEqual(0f, e.ResonantTimer, 1e-4f);
                return 100000f - e.Hp;
            }
            float plain = Melt(false), amped = Melt(true);
            Assert.Greater(amped, plain * 1.2f);
        }

        [Test]
        public void UnstableCollapsesAtThresholdWithCooldown()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit e = Dummy(b);
            EnemyUnit near = Dummy(b, 100000f, new Vec2(7f, 0f));
            b.Grid.Rebuild(b.Enemies);
            b.AddUnstable(e, 2, null, 0);
            Assert.AreEqual(100000f, near.Hp);
            b.AddUnstable(e, 1, null, 0);
            Assert.Less(near.Hp, 100000f, "collapse damages neighbours");
            Assert.Greater(near.PullTimer, 0f);
            float hp = near.Hp;
            b.AddUnstable(e, 3, null, 0);
            Assert.AreEqual(hp, near.Hp, "2s cooldown between collapses");
        }

        [Test]
        public void EclipseLeavesADebuffFieldThatAddsDoom()
        {
            Battle b = TestContent.EmptyBattle(("terra", 0));
            EnemyUnit e = Dummy(b, 1e6f, new Vec2(10f, 5f));
            EnemyUnit other = Dummy(b, 1e6f, new Vec2(10.6f, 5f));
            b.Grid.Rebuild(b.Enemies);
            b.ApplyElement(e, Element.Light, 1f, null, 0);
            b.ApplyElement(e, Element.Shadow, 1f, null, 0);
            Assert.IsTrue(b.Stats.ReactionCounts.ContainsKey("eclipse"));
            Assert.IsTrue(b.Zones.Exists(z => z.Field != null && z.Field.Id == "eclipse"));
            for (int i = 0; i < 70; i++) b.Tick();
            Assert.Greater(other.DoomStacks, 0, "eclipse pulses add Doom to enemies inside");
        }

        [Test]
        public void WorldCooldownLimitsTeamBuffReactions()
        {
            Battle b = TestContent.EmptyBattle(("terra", 0));
            EnemyUnit a = Dummy(b, 1e6f, new Vec2(5f, 0f));
            EnemyUnit c = Dummy(b, 1e6f, new Vec2(-5f, 0f));
            b.ApplyElement(a, Element.Water, 1f, null, 0);
            b.ApplyElement(a, Element.Arcane, 1f, null, 0);
            b.ApplyElement(c, Element.Water, 1f, null, 0);
            b.ApplyElement(c, Element.Arcane, 1f, null, 0);
            Assert.AreEqual(1, b.Stats.ReactionCounts["mana_tide"], "mana tide is limited to once per 1.5s battle-wide");
        }

        [Test]
        public void EveryReactionResolvesWithinCaps()
        {
            ContentDatabase db = TestContent.Db;
            foreach (ReactionDef r in db.Reactions.Values)
            {
                Battle b = TestContent.EmptyBattle(("terra", 0), ("ignis", 4));
                var cluster = new List<EnemyUnit>();
                for (int i = 0; i < 9; i++) cluster.Add(Dummy(b, 1e6f, new Vec2(7f + (i % 3) * 0.5f, 2f + (i / 3) * 0.5f)));
                b.Grid.Rebuild(b.Enemies);
                foreach (EnemyUnit e in cluster) b.ApplyElement(e, r.A, 1f, null, 0);
                b.ApplyElement(cluster[4], r.B, 1f, b.Heroes[0], 0);
                Assert.IsTrue(b.Stats.ReactionCounts.ContainsKey(r.Id), r.Id + " did not trigger from " + r.A + "+" + r.B);
                for (int t = 0; t < 120; t++)
                {
                    b.Tick();
                    b.Journal.Clear();
                    foreach (EnemyUnit e in b.Enemies)
                        Assert.IsFalse(float.IsNaN(e.Hp) || float.IsNaN(e.Pos.X), r.Id + " produced NaN");
                }
                Assert.LessOrEqual(b.Zones.Count, 12, r.Id + " left too many zones");
            }
        }

        [Test]
        public void RandomTwelveElementStormStaysBounded()
        {
            Battle b = TestContent.EmptyBattle(("terra", 0), ("marina", 4), ("volt", 8));
            var rng = new Pcg32(7);
            var list = new List<EnemyUnit>();
            for (int i = 0; i < 60; i++) list.Add(Dummy(b, 1e7f, new Vec2(4f + (i % 10) * 0.45f, -2f + (i / 10) * 0.45f)));
            int peakZones = 0;
            for (int t = 0; t < 600; t++)
            {
                for (int k = 0; k < 6; k++)
                {
                    EnemyUnit e = list[rng.Range(0, list.Count)];
                    if (e.Alive) b.ApplyElement(e, ElementUtil.All[rng.Range(0, 12)], 1f, b.Heroes[k % 3], 0);
                }
                b.Tick();
                b.Journal.Clear();
                if (b.Zones.Count > peakZones) peakZones = b.Zones.Count;
            }
            Assert.LessOrEqual(b.Stats.PeakReactionsPerSecond, Battle.WorldReactionBudgetPerTick * 30);
            Assert.LessOrEqual(peakZones, 40, "field caps keep zone count bounded");
            foreach (EnemyUnit e in b.Enemies)
            {
                Assert.LessOrEqual(e.PoisonStacks, Battle.PoisonMaxStacks);
                Assert.LessOrEqual(e.DoomStacks, Battle.DoomMaxStacks);
                Assert.IsFalse(float.IsNaN(e.Hp));
            }
        }
    }
}
