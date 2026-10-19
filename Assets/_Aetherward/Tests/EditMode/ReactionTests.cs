using System.Collections.Generic;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using NUnit.Framework;

namespace Aetherward.Tests
{
    public class ReactionTests
    {
        private static EnemyUnit Dummy(Battle b, float hp = 100000f, Vec2? at = null)
        {
            EnemyUnit e = b.SpawnEnemy(b.Content.Enemies["grunt"], 0, false, null, at ?? new Vec2(6f, 0f));
            e.MaxHp = e.Hp = hp;
            e.Defense = 0f;
            return e;
        }

        [Test]
        public void LaunchFifteenPairsKeepTheirLegacyReactions()
        {
            ContentDatabase db = TestContent.Db;
            var seen = new HashSet<string>();
            Element[] launch = { Element.Fire, Element.Water, Element.Lightning, Element.Ice, Element.Wind, Element.Earth };
            for (int i = 0; i < launch.Length; i++)
            {
                for (int j = i + 1; j < launch.Length; j++)
                {
                    ReactionDef r = db.ReactionFor(launch[i], launch[j]);
                    Assert.IsNotNull(r, launch[i] + "+" + launch[j] + " has no reaction");
                    Assert.AreSame(r, db.ReactionFor(launch[j], launch[i]), "reaction lookup must be commutative");
                    Assert.IsTrue(r.Legacy, r.Id + " must keep its launch resolution");
                    Assert.IsTrue(seen.Add(r.Id), "duplicate reaction " + r.Id);
                }
            }
            Assert.AreEqual(15, seen.Count);
        }

        [TestCase(Element.Fire, Element.Water, "vaporize")]
        [TestCase(Element.Water, Element.Fire, "vaporize")]
        [TestCase(Element.Lightning, Element.Water, "electrocharge")]
        [TestCase(Element.Ice, Element.Water, "freeze")]
        [TestCase(Element.Earth, Element.Wind, "sandstorm")]
        [TestCase(Element.Ice, Element.Lightning, "superconduct")]
        public void ApplyingSecondElementTriggersReactionInEitherOrder(Element first, Element second, string expected)
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit e = Dummy(b);
            b.ApplyElement(e, first, 1f, null, 0);
            Assert.IsTrue(e.HasAura(first));
            b.ApplyElement(e, second, 1f, null, 0);
            Assert.IsTrue(b.Stats.ReactionCounts.ContainsKey(expected), "expected " + expected);
            Assert.AreEqual(1, b.Stats.TotalReactions);
        }

        [Test]
        public void ReactionConsumesExistingGauge()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit e = Dummy(b);
            b.ApplyElement(e, Element.Fire, 1f, null, 0);
            float before = e.Aura[(int)Element.Fire];
            b.ApplyElement(e, Element.Water, 0.5f, null, 0);
            Assert.Less(e.Aura[(int)Element.Fire], before);
            Assert.AreEqual(0f, e.Aura[(int)Element.Water], 1e-4f, "incoming gauge is consumed by the reaction");
        }

        [Test]
        public void GaugeDecaysOverTime()
        {
            Battle b = TestContent.EmptyBattle(("terra", 0)); // keep battle alive with an enemy far away
            EnemyUnit e = Dummy(b, 1e6f, new Vec2(11f, 6f));
            e.Speed = 0f;
            b.ApplyElement(e, Element.Ice, 1f, null, 0);
            for (int i = 0; i < 30 * 3; i++) b.Tick();
            Assert.IsFalse(e.HasAura(Element.Ice), "1 gauge unit should expire within 3 seconds");
        }

        [Test]
        public void SamePairHasAntiRepeatCooldown()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit e = Dummy(b);
            b.ApplyElement(e, Element.Fire, 2f, null, 0);
            b.ApplyElement(e, Element.Water, 0.2f, null, 0);
            b.ApplyElement(e, Element.Water, 0.2f, null, 0);
            Assert.AreEqual(1, b.Stats.ReactionCounts["vaporize"], "second vaporize within cooldown must not fire");
        }

        [Test]
        public void GenerationCapBlocksSecondaryChains()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit e = Dummy(b);
            b.ApplyElement(e, Element.Fire, 1f, null, Battle.MaxProcGeneration);
            b.ApplyElement(e, Element.Water, 1f, null, Battle.MaxProcGeneration);
            Assert.AreEqual(0, b.Stats.TotalReactions);
            Assert.Greater(b.Stats.ReactionsBlockedByGeneration, 0);
        }

        [Test]
        public void PerTargetBudgetCapsReactionsPerSecond()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit e = Dummy(b);
            Element[] cycle = { Element.Fire, Element.Water, Element.Lightning, Element.Ice, Element.Wind, Element.Earth };
            for (int i = 0; i < 60; i++) b.ApplyElement(e, cycle[i % cycle.Length], 1f, null, 0);
            Assert.LessOrEqual(b.Stats.TotalReactions, Battle.TargetReactionBudgetPerSecond + 1);
        }

        [Test]
        public void RainstormSpreadsWetButSecondaryChainsStayBounded()
        {
            // Many enemies pre-charged with lightning: rainstorm applies Wet (gen 1) which may trigger
            // electrocharge (gen 2) whose bounces must not create further reactions.
            Battle b = TestContent.EmptyBattle();
            var list = new List<EnemyUnit>();
            for (int i = 0; i < 12; i++)
            {
                EnemyUnit e = Dummy(b, 1e6f, new Vec2(6f + (i % 4) * 0.4f, (i / 4) * 0.4f));
                list.Add(e);
            }
            for (int i = 1; i < list.Count; i++) b.ApplyElement(list[i], Element.Lightning, 1f, null, 0);
            b.Grid.Rebuild(b.Enemies);
            b.ApplyElement(list[0], Element.Wind, 1f, null, 0);
            b.ApplyElement(list[0], Element.Water, 1f, null, 0);
            Assert.IsTrue(b.Stats.ReactionCounts.ContainsKey("rainstorm"), "water onto wind => rainstorm");
            Assert.IsTrue(b.Stats.ReactionCounts.ContainsKey("electrocharge"), "spread Wet reacts with neighbours' lightning");
            Assert.Less(b.Stats.TotalReactions, 40, "chain must stay bounded");
        }

        [Test]
        public void FreezeStunsNormalEnemiesButBossesBuildResistance()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit grunt = Dummy(b);
            b.ApplyElement(grunt, Element.Water, 1f, null, 0);
            b.ApplyElement(grunt, Element.Ice, 1f, null, 0);
            Assert.IsTrue(grunt.Frozen);
            Assert.Greater(grunt.StunTimer, 1f);

            EnemyUnit boss = b.SpawnEnemy(b.Content.Enemies["rift_warden"], 0, false, null, new Vec2(5f, 3f));
            b.ApplyElement(boss, Element.Water, 1f, null, 0);
            b.ApplyElement(boss, Element.Ice, 1f, null, 0);
            Assert.Less(boss.StunTimer, grunt.StunTimer);
            Assert.Greater(boss.FreezeResist, 0f, "bosses resist repeated freeze but are never immune");
        }

        [Test]
        public void BurnTickCanTriggerVaporizeOnWetTarget()
        {
            Battle b = TestContent.EmptyBattle(("terra", 0));
            EnemyUnit e = Dummy(b, 1e6f, new Vec2(11f, 6f));
            e.Speed = 0f;
            b.ApplyBurn(e, null, 4f);
            for (int i = 0; i < 30; i++) b.Tick();
            b.ApplyElement(e, Element.Water, 1f, null, 0);
            for (int i = 0; i < 60; i++) b.Tick();
            Assert.IsTrue(b.Stats.ReactionCounts.ContainsKey("vaporize"), "DoT fire gauge should react with Wet");
        }
    }
}
