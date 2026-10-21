using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>Nature/Poison heroes (Expansion Phase 2): each skill, passive and evolution twist.</summary>
    public class NatureHeroTests
    {
        private static EnemyUnit Dummy(Battle b, Vec2 at, string id = "grunt")
        {
            EnemyUnit e = b.SpawnEnemy(b.Content.Enemies[id], 0, false, null, at);
            e.MaxHp = e.Hp = 1e5f;
            e.Speed = 0f;
            return e;
        }

        private static Battle WithEvolution(string hero, string evo, int node, params (string, int)[] others)
        {
            var all = new (string, int)[others.Length + 1];
            all[0] = (hero, node);
            others.CopyTo(all, 1);
            BattleSetup s = TestContent.Setup(1, 42, all);
            s.Wave = new WaveDef { Number = 1, TimeLimit = 999f };
            if (evo != null)
            {
                s.Heroes[0].Level = 5;
                s.Heroes[0].EvolutionId = evo;
            }
            return new Battle(s);
        }

        [Test]
        public void LioraRootsTheClusterAndDeepRootsRewardsIt()
        {
            Battle b = TestContent.EmptyBattle(("liora", 4));
            HeroUnit h = b.Heroes[0];
            EnemyUnit a = Dummy(b, h.Pos + new Vec2(2.5f, 0f));
            EnemyUnit c = Dummy(b, h.Pos + new Vec2(2.9f, 0.3f));
            b.Tick();
            Assert.IsTrue(b.CastSkill(h, 1f, false));
            Assert.IsTrue(a.Rooted && c.Rooted, "the bloom roots the whole cluster");
            Assert.AreEqual(0.3f, b.PassiveBonus(h, a), 1e-4f, "Deep Roots: +30% to Rooted enemies");
            a.RootTimer = 0f;
            Assert.AreEqual(0f, b.PassiveBonus(h, a));
        }

        [Test]
        public void BossesAreSlowedNotRooted()
        {
            Battle b = TestContent.EmptyBattle(("liora", 4));
            EnemyUnit boss = Dummy(b, b.Heroes[0].Pos + new Vec2(2.5f, 0f), "siegebreaker_golem");
            b.Root(boss, 2f);
            Assert.IsFalse(boss.Rooted);
            Assert.Greater(boss.SlowTimer, 0f);
        }

        [Test]
        public void SporeGardenLeavesAHealingRootingField()
        {
            Battle b = WithEvolution("liora", "liora_spore_garden", 4);
            HeroUnit h = b.Heroes[0];
            Dummy(b, h.Pos + new Vec2(2.5f, 0f));
            b.Tick();
            Assert.IsTrue(b.CastSkill(h, 1f, false));
            Assert.IsTrue(b.Zones.Exists(z => z.Field != null && z.Field.Id == "spore_garden"));
        }

        [Test]
        public void ThalenThornsReflectAndBarkskinScalesWithMissingHealth()
        {
            Battle b = TestContent.EmptyBattle(("thalen", 0));
            HeroUnit h = b.Heroes[0];
            EnemyUnit e = Dummy(b, h.Pos + new Vec2(0.6f, 0f));
            b.Tick();
            Assert.IsTrue(b.CastSkill(h, 1f, false));
            Assert.Greater(h.Shield, 0f);
            Assert.Greater(h.ThornTimer, 0f);
            Assert.AreSame(h, e.Taunter, "thorn wall taunts");
            float hp = e.Hp;
            b.DamageHero(h, 10f, e);
            Assert.Less(e.Hp, hp, "attackers take thorn damage");

            h.Shield = 0f;
            h.Hp = h.MaxHp;
            float full = h.Hp;
            b.DamageHero(h, 100f, null);
            float tookFull = full - h.Hp;
            h.Hp = h.MaxHp * 0.4f;
            float low = h.Hp;
            b.DamageHero(h, 100f, null);
            Assert.Less(low - h.Hp, tookFull * 0.85f, "Barkskin: up to 20% less damage when hurt");
        }

        [Test]
        public void BrambleFortressRootsAttackers()
        {
            Battle b = WithEvolution("thalen", "thalen_bramble_fortress", 0);
            HeroUnit h = b.Heroes[0];
            EnemyUnit e = Dummy(b, h.Pos + new Vec2(0.6f, 0f));
            b.Tick();
            Assert.IsTrue(b.CastSkill(h, 1f, false));
            b.DamageHero(h, 10f, e);
            Assert.IsTrue(e.Rooted);
        }

        [Test]
        public void OvergrowthChargeLashesAtRange()
        {
            Battle b = WithEvolution("thalen", "thalen_overgrowth_charge", 4);
            HeroUnit h = b.Heroes[0];
            EnemyUnit far = Dummy(b, h.Pos + new Vec2(2.6f, 0f));
            b.Tick();
            Assert.IsTrue(b.CastSkill(h, 1f, false));
            Assert.Less(far.Hp, far.MaxHp);
            Assert.IsTrue(far.Rooted);
        }

        [Test]
        public void VesperPoisonsLeavesAPatchAndCatalysisScales()
        {
            Battle b = TestContent.EmptyBattle(("vesper", 4));
            HeroUnit h = b.Heroes[0];
            EnemyUnit e = Dummy(b, h.Pos + new Vec2(2.5f, 0f));
            b.Tick();
            Assert.IsTrue(b.CastSkill(h, 1f, false));
            Assert.GreaterOrEqual(e.PoisonStacks, 2);
            Assert.IsTrue(b.Zones.Exists(z => z.Field != null && z.Field.Id == "toxic_patch"));
            e.PoisonStacks = 5;
            Assert.AreEqual(0.2f, b.PassiveBonus(h, e), 1e-4f, "Catalysis: +4% per stack");
            e.PoisonStacks = 10;
            Assert.AreEqual(0.3f, b.PassiveBonus(h, e), 1e-4f, "capped at +30%");
        }

        [Test]
        public void VolatileMixtureDetonatesExistingPoisonWithoutLooping()
        {
            Battle plain = WithEvolution("vesper", "vesper_volatile_mixture", 4);
            EnemyUnit a = Dummy(plain, plain.Heroes[0].Pos + new Vec2(2.5f, 0f));
            plain.Tick();
            plain.CastSkill(plain.Heroes[0], 1f, false);
            float cleanHit = a.MaxHp - a.Hp;

            Battle b = WithEvolution("vesper", "vesper_volatile_mixture", 4);
            EnemyUnit e = Dummy(b, b.Heroes[0].Pos + new Vec2(2.5f, 0f));
            b.Tick();
            b.AddPoison(e, 8, 6f, null);
            b.CastSkill(b.Heroes[0], 1f, false);
            Assert.Greater(e.MaxHp - e.Hp, cleanHit * 1.5f, "existing poison detonates");
            Assert.Less(e.PoisonStacks, 8 + 2, "half of the stacks were consumed");
            Assert.IsFalse(b.Zones.Exists(z => z.Field != null && z.Field.Id == "toxic_patch"), "no patch on this branch");
        }

        [Test]
        public void SableInfectsHealsAndGivesFever()
        {
            Battle b = TestContent.EmptyBattle(("sable", 4), ("terra", 0));
            HeroUnit doc = b.Heroes[0], ally = b.Heroes[1];
            for (int i = 0; i < 3; i++) Dummy(b, doc.Pos + new Vec2(2.4f + i * 0.3f, 0.2f * i));
            b.Tick();
            ally.Pos = doc.Pos + new Vec2(-1.2f, 0f);   // heal range is live distance: keep the ally beside Sable
            ally.Hp = ally.MaxHp * 0.4f;
            float before = ally.Hp;
            Assert.IsTrue(b.CastSkill(doc, 1f, false));
            Assert.Greater(ally.Hp - before, ally.MaxHp * 0.08f, "base heal plus a bonus per poisoned enemy");
            Assert.Greater(ally.FeverTimer, 0f, "tradeoff: Fever");
            Assert.IsTrue(b.Enemies.TrueForAll(e => e.PoisonStacks >= 2));
            b.CleanseHero(ally);
            Assert.AreEqual(0f, ally.FeverTimer, "cleanse removes Fever");
        }

        [Test]
        public void RemedyHasNoFeverAndPlagueDoctorHealsOnPoisonedDeaths()
        {
            Battle b = WithEvolution("sable", "sable_remedy", 4, ("terra", 0));
            HeroUnit doc = b.Heroes[0], ally = b.Heroes[1];
            EnemyUnit e = Dummy(b, doc.Pos + new Vec2(2.4f, 0f));
            b.Tick();
            ally.Hp = ally.MaxHp * 0.4f;
            Assert.IsTrue(b.CastSkill(doc, 1f, false));
            Assert.AreEqual(0f, ally.FeverTimer, "Remedy cures without Fever");

            Battle p = TestContent.EmptyBattle(("sable", 4), ("terra", 0));
            HeroUnit pa = p.Heroes[1];
            EnemyUnit victim = Dummy(p, p.Heroes[0].Pos + new Vec2(2f, 0f));
            p.Tick();
            pa.Pos = p.Heroes[0].Pos + new Vec2(-1.2f, 0f);
            pa.Hp = pa.MaxHp * 0.5f;
            p.AddPoison(victim, 3, 5f, null);
            float hp = pa.Hp;
            p.DealDamage(victim, new DamageRequest { Attack = 1e6f, Multiplier = 1f, Kind = DamageKind.Trigger, IgnoreDefense = true });
            Assert.Greater(pa.Hp, hp, "a poisoned death near Sable mends the most hurt ally");
        }

        [Test]
        public void NaturePoisonRelicsChangeTheRules()
        {
            Battle b = TestContent.EmptyBattle(("liora", 4));
            EnemyUnit e = Dummy(b, b.Heroes[0].Pos + new Vec2(2.5f, 0f));
            b.Root(e, 1f);
            float plain = e.RootTimer;

            BattleSetup s = TestContent.Setup(1, 42, ("liora", 4));
            s.Wave = new WaveDef { Number = 1, TimeLimit = 999f };
            s.Modifiers.Rules["root_duration"] = 0.3f; // what Verdant Seed grants
            Battle r = new Battle(s);
            EnemyUnit e2 = Dummy(r, r.Heroes[0].Pos + new Vec2(2.5f, 0f));
            r.Root(e2, 1f);
            Assert.AreEqual(plain * 1.3f, e2.RootTimer, 1e-3f);
        }
    }
}
