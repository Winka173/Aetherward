using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using NUnit.Framework;

namespace Aetherward.Tests
{
    public class CombatTests
    {
        [Test]
        public void ContentLoadsWithExpectedCounts()
        {
            ContentDatabase db = TestContent.Db;
            Assert.AreEqual(12, db.Heroes.Count);
            Assert.AreEqual(24, db.Evolutions.Count);
            Assert.AreEqual(20, db.Waves.Count);
            Assert.AreEqual(12, db.Arena.Nodes.Count);
            Assert.GreaterOrEqual(db.Enemies.Count, 10);
            foreach (HeroDef h in db.HeroList)
            {
                Assert.AreEqual(2, h.Evolutions.Count, h.Id);
                foreach (string evo in h.Evolutions)
                {
                    Assert.IsTrue(db.Evolutions.ContainsKey(evo), evo);
                    Assert.AreEqual(h.Id, db.Evolutions[evo].HeroId);
                }
            }
        }

        [Test]
        public void DefenseFormulaReducesPhysicalDamage()
        {
            Battle b = TestContent.EmptyBattle(("ignis", 4));
            HeroUnit h = b.Heroes[0];
            h.Stats[(int)StatId.CritChance] = 0f;
            EnemyUnit e = b.SpawnEnemy(b.Content.Enemies["grunt"], 0, false, null, new Vec2(6f, 0f));
            e.MaxHp = e.Hp = 10000f;
            e.Defense = 100f;
            for (int i = 0; i < e.Resist.Length; i++) e.Resist[i] = 0f;
            float dealt = b.DealDamage(e, new DamageRequest { Source = h, Attack = 100f, Multiplier = 1f, Element = Element.None, Kind = DamageKind.Basic });
            Assert.AreEqual(50f, dealt, 0.01f, "100 attack vs 100 defense => 50% damage");
        }

        [Test]
        public void ReactionDamageIgnoresDefenseButNotResistance()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit e = b.SpawnEnemy(b.Content.Enemies["grunt"], 0, false, null, new Vec2(6f, 0f));
            e.MaxHp = e.Hp = 10000f;
            e.Defense = 1000f;
            e.Resist[(int)Element.Fire] = 0.5f;
            float dealt = b.DealDamage(e, new DamageRequest { Attack = 100f, Multiplier = 1f, Element = Element.Fire, Kind = DamageKind.Reaction, ReactionId = "melt" });
            Assert.AreEqual(50f, dealt, 0.01f);
        }

        [Test]
        public void CritChanceIsCappedAndMultiplierBounded()
        {
            Battle b = TestContent.EmptyBattle(("sylph", 4));
            HeroUnit h = b.Heroes[0];
            h.Stats[(int)StatId.CritChance] = 5f;
            h.Stats[(int)StatId.CritMultiplier] = 10f;
            h.Stats[(int)StatId.DamageBonus] = 0f;
            EnemyUnit e = b.SpawnEnemy(b.Content.Enemies["grunt"], 0, false, null, new Vec2(6f, 0f));
            e.Defense = 0f;
            int crits = 0;
            for (int i = 0; i < 400; i++)
            {
                e.MaxHp = e.Hp = 1e6f;
                float d = b.DealDamage(e, new DamageRequest { Source = h, Attack = 10f, Multiplier = 1f, Kind = DamageKind.Basic, CanCrit = true });
                Assert.LessOrEqual(d, 40.001f, "crit multiplier capped at 4x");
                if (d > 10.5f) crits++;
            }
            Assert.Less(crits, 360, "crit chance capped at 75%");
            Assert.Greater(crits, 240);
        }

        [Test]
        public void ShieldAbsorbsBeforeHpAndHealingDoesNotOverflow()
        {
            Battle b = TestContent.EmptyBattle(("terra", 4), ("marina", 6));
            HeroUnit terra = b.Heroes[0];
            terra.Stats[(int)StatId.Defense] = 0f;
            terra.Stats[(int)StatId.DamageReduction] = 0f;
            b.AddHeroShield(terra, 50f, null);
            float hp = terra.Hp;
            b.DamageHero(terra, 30f, null);
            Assert.AreEqual(hp, terra.Hp, 0.001f);
            Assert.AreEqual(20f, terra.Shield, 0.001f);
            b.AddHeroShield(terra, 1e6f, null);
            Assert.LessOrEqual(terra.Shield, terra.MaxHp * 0.6f + 0.01f, "shield bounded");
            terra.Hp = terra.MaxHp - 10f;
            float healed = b.HealHero(terra, 1000f, null);
            Assert.AreEqual(10f, healed, 0.01f);
            Assert.AreEqual(terra.MaxHp, terra.Hp, 0.01f);
        }

        [Test]
        public void DownedHeroStopsActingAndReleasesEngagedEnemies()
        {
            Battle b = TestContent.EmptyBattle(("ignis", 4));
            HeroUnit h = b.Heroes[0];
            EnemyUnit e = b.SpawnEnemy(b.Content.Enemies["grunt"], 0, false, null, new Vec2(5f, 0f));
            e.Engaged = h;
            b.DamageHero(h, 1e6f, e);
            Assert.IsFalse(h.Alive);
            Assert.AreEqual(HeroState.Downed, h.State);
            Assert.IsNull(e.Engaged);
        }

        [Test]
        public void TwoHeroesClearWaveOne()
        {
            Battle b = new Battle(TestContent.Setup(1, 7, ("ignis", 4), ("terra", 0)));
            BattleOutcome o = b.RunToEnd();
            Assert.AreEqual(BattleOutcome.Cleared, o);
            Assert.AreEqual(7, b.Stats.Kills);
            Assert.Greater(b.Crystal.Hp, 0f);
            Assert.Less(b.Time, 70f);
        }

        [Test]
        public void NoHeroesMeansEnemiesDamageCrystalAndWaveStillResolves()
        {
            BattleSetup s = TestContent.Setup(6, 11);
            s.CrystalHp = 100f;
            Battle b = new Battle(s);
            BattleOutcome o = b.RunToEnd();
            Assert.AreEqual(BattleOutcome.CrystalDestroyed, o, "undefended crystal must fall, never softlock");
            Assert.IsNotNull(b.DefeatSource);
        }

        [Test]
        public void TimeoutBreachResolvesWave()
        {
            BattleSetup s = TestContent.Setup(2, 3, ("terra", 0));
            Battle b = new Battle(s);
            // Freeze every enemy in place forever: the wave must still end via the timeout breach.
            for (int i = 0; i < 30 * 200 && b.Outcome == BattleOutcome.Running; i++)
            {
                foreach (EnemyUnit e in b.Enemies) { e.Speed = 0f; e.Pos = new Vec2(11.5f, 6.5f); }
                b.Heroes[0].Stats[(int)StatId.Attack] = 0f;
                b.Tick();
                b.Journal.Clear();
            }
            Assert.AreNotEqual(BattleOutcome.Running, b.Outcome);
            Assert.Greater(b.Stats.TimeoutBreaches, 0);
        }

        [Test]
        public void SameSeedReplaysIdentically()
        {
            float RunOnce()
            {
                Battle b = new Battle(TestContent.Setup(6, 1234, ("ignis", 4), ("volt", 8), ("terra", 0), ("marina", 6)));
                b.RunToEnd();
                return b.Crystal.Hp * 1000f + b.Time + b.Stats.TotalReactions;
            }
            Assert.AreEqual(RunOnce(), RunOnce());
        }

        [Test]
        public void EveryHeroSkillCastsInARealWave()
        {
            foreach (HeroDef def in TestContent.Db.HeroList)
            {
                Battle b = new Battle(TestContent.Setup(6, 5, (def.Id, 4), ("terra", 0)));
                b.RunToEnd();
                Assert.Greater(b.Heroes[0].SkillCasts, 0, def.Id + " never cast its skill");
            }
        }

        [Test]
        public void EveryEvolutionBuildsAndCasts()
        {
            ContentDatabase db = TestContent.Db;
            foreach (EvolutionDef evo in db.Evolutions.Values)
            {
                BattleSetup s = TestContent.Setup(6, 9, (evo.HeroId, 4), ("terra", 0), ("marina", 6));
                s.Heroes[0].Level = 5;
                s.Heroes[0].EvolutionId = evo.Id;
                Battle b = new Battle(s);
                Assert.AreNotSame(db.Heroes[evo.HeroId].Skill, b.Heroes[0].Skill, evo.Id + " must change the skill");
                b.RunToEnd();
                Assert.Greater(b.Heroes[0].SkillCasts, 0, evo.Id + " never cast");
            }
        }

        [Test]
        public void ShieldbearerBlocksFrontalHits()
        {
            Battle b = TestContent.EmptyBattle(("sylph", 4));
            HeroUnit h = b.Heroes[0];
            EnemyUnit e = b.SpawnEnemy(b.Content.Enemies["shieldbearer"], 0, false, null, new Vec2(7f, 0f));
            e.Facing = new Vec2(-1f, 0f); // walking toward the hero at x=4.5
            e.MaxHp = e.Hp = 1e5f;
            float front = b.DealDamage(e, new DamageRequest { Source = h, Attack = 100f, Multiplier = 1f, Kind = DamageKind.Skill });
            e.Facing = new Vec2(1f, 0f);
            float back = b.DealDamage(e, new DamageRequest { Source = h, Attack = 100f, Multiplier = 1f, Kind = DamageKind.Skill });
            Assert.Less(front, back * 0.6f);
        }
    }
}
