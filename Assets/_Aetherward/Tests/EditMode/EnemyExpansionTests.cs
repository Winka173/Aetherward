using System.Collections.Generic;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using Aetherward.Sim.Meta;
using Aetherward.Sim.Run;
using NUnit.Framework;

namespace Aetherward.Tests
{
    public class EnemyExpansionTests
    {
        [Test]
        public void ManaLeechSlowsNearbyCooldownsButNotSteadfastHeroes()
        {
            BattleSetup s = TestContent.Setup(1, 3, ("terra", 0), ("ignis", 3));
            s.Heroes[1].TraitId = "steadfast";
            s.Wave = new WaveDef { Number = 1, TimeLimit = 999f };
            Battle b = new Battle(s);
            EnemyUnit leech = b.SpawnEnemy(b.Content.Enemies["mana_leech"], 0, false, null, new Vec2(1.75f, 0f));
            leech.Speed = 0f;
            for (int i = 0; i < 20; i++) b.Tick();
            Assert.Greater(b.Heroes[0].LeechTimer, 0f, "Terra stands inside the leech aura");
            Assert.AreEqual(0f, b.Heroes[1].LeechTimer, "Steadfast is immune");
            float before = b.Heroes[0].SkillTimer = 5f;
            b.Tick();
            Assert.AreEqual(before - Battle.TickSeconds * 0.65f, b.Heroes[0].SkillTimer, 1e-3f, "cooldown recovers 35% slower");
        }

        [Test]
        public void CrystalParasiteLatchesResistsAndIsRippedOffByLight()
        {
            Battle b = TestContent.EmptyBattle(("sylph", 8));
            EnemyUnit p = b.SpawnEnemy(b.Content.Enemies["crystal_parasite"], 0, false, null, new Vec2(1.5f, 0.2f));
            p.MaxHp = p.Hp = 10000f;
            for (int i = 0; i < 30 && !p.Latched; i++) b.Tick();
            Assert.IsTrue(p.Latched);
            float hpBefore = b.Crystal.Hp;
            for (int i = 0; i < 30; i++) b.Tick();
            Assert.Less(b.Crystal.Hp, hpBefore, "latched parasites gnaw the crystal");
            float resisted = b.DealDamage(p, new DamageRequest { Attack = 100f, Multiplier = 1f, Kind = DamageKind.Trigger, IgnoreDefense = true, Element = Element.Fire });
            float lit = b.DealDamage(p, new DamageRequest { Attack = 100f, Multiplier = 1f, Kind = DamageKind.Trigger, IgnoreDefense = true, Element = Element.Light });
            Assert.Less(resisted, lit * 0.6f, "unguarded latch resists everything but Light");
            b.Illuminate(p, 3f, 0.15f, 0.5f);
            Assert.IsFalse(p.Latched, "Light detaches the parasite");
            Assert.Greater(p.StunTimer, 0.5f);
        }

        [Test]
        public void GuardingTheCoreRemovesTheParasiteResistance()
        {
            Battle b = TestContent.EmptyBattle(("terra", 0));
            EnemyUnit p = b.SpawnEnemy(b.Content.Enemies["crystal_parasite"], 0, false, null, new Vec2(0f, -1.3f));
            p.MaxHp = p.Hp = 10000f;
            p.Latched = true;
            Assert.IsTrue(b.CoreGuarded, "a hero on an inner node guards the core");
            float dmg = b.DealDamage(p, new DamageRequest { Attack = 100f, Multiplier = 1f, Kind = DamageKind.Trigger, IgnoreDefense = true, Element = Element.Fire });
            Assert.Greater(dmg, 90f);
        }

        [Test]
        public void AshImpBurstsOnDeathNearHeroes()
        {
            Battle b = TestContent.EmptyBattle(("terra", 4));
            HeroUnit h = b.Heroes[0];
            EnemyUnit imp = b.SpawnEnemy(b.Content.Enemies["ash_imp"], 0, false, null, h.Pos + new Vec2(0.5f, 0f));
            float hp = h.Hp;
            b.DealDamage(imp, new DamageRequest { Attack = 9999f, Multiplier = 1f, Kind = DamageKind.Trigger, IgnoreDefense = true });
            Assert.Less(h.Hp, hp);
        }

        [Test]
        public void IgnarothOverheatsWithACounterWindowAndNeverSoftlocks()
        {
            BattleSetup s = TestContent.Setup(10, 21, ("terra", 0), ("marina", 4), ("freya", 8), ("volt", 6));
            s.Substitutions["siegebreaker_golem"] = "ignaroth";
            foreach (HeroLoadout l in s.Heroes) l.Level = 5;
            s.CrystalHp = s.CrystalMaxHp = 1e6f; // mechanics test: keep the crystal out of the picture
            Battle b = new Battle(s);
            bool heat = false, vent = false, lava = false;
            for (int t = 0; t < 30 * 200 && b.Outcome == BattleOutcome.Running; t++)
            {
                b.Tick();
                foreach (SimEvent e in b.Journal.Pending)
                {
                    if (e.Type == SimEventType.BossPhase && e.Id == "ignaroth_heat") heat = true;
                    if (e.Type == SimEventType.BossPhase && e.Id == "ignaroth_vent") vent = true;
                    if (e.Type == SimEventType.Telegraph && e.Id == "BossSlam") lava = true;
                }
                b.Journal.Clear();
                EnemyUnit boss = b.Enemies.Find(x => x.Def.Id == "ignaroth");
                if (boss != null && boss.Phase == 0 && b.Time > 30f) boss.Hp = boss.MaxHp * 0.45f; // reach the heat phase quickly
                if (boss != null && boss.Phase == 1 && !vent) boss.Hp = SimMath.Max(boss.Hp, boss.MaxHp * 0.3f); // survive until the first vent
            }
            TestContext.WriteLine("t=" + b.Time + " outcome=" + b.Outcome + " lava=" + lava + " heat=" + heat + " vent=" + vent + " bossSeen=" + b.Stats.Kills);
            Assert.IsTrue(lava, "lava eruptions are telegraphed");
            Assert.IsTrue(heat, "boss enters the Overheat phase");
            Assert.IsTrue(vent, "Overheat has a vent (Exposed) window");
            Assert.AreNotEqual(BattleOutcome.Running, b.Outcome, "wave resolves (no softlock)");
        }

        [Test]
        public void BossPoolChoiceIsDeterministicSavedAndUsed()
        {
            ContentDatabase db = TestContent.Db;
            var seen = new HashSet<string>();
            for (ulong seed = 1; seed <= 20; seed++)
            {
                RunController rc = RunController.NewRun(db, seed, new[] { "terra", "ignis" }, 0, RunUnlocks.Everything(db));
                WaveDef w10 = db.Waves[9];
                string a = rc.BossFor(w10);
                Assert.AreEqual(a, RunController.NewRun(db, seed, new[] { "terra", "ignis" }, 0, RunUnlocks.Everything(db)).BossFor(w10));
                seen.Add(a);
                var saves = new SaveService(new MemoryStorage());
                saves.SaveRun(rc.State);
                Assert.AreEqual(a, saves.LoadRun(db).BossChoices[10]);
                rc.State.Wave = 10;
                BattleSetup setup = rc.BuildBattleSetup();
                Battle b = new Battle(setup);
                bool spawned = false;
                for (int t = 0; t < 30 * 8; t++)
                {
                    b.Tick();
                    b.Journal.Clear();
                    if (b.Enemies.Exists(e => e.Def.Id == a)) { spawned = true; break; }
                }
                Assert.IsTrue(spawned, a + " should be the wave-10 boss for seed " + seed);
            }
            Assert.AreEqual(2, seen.Count, "both bosses appear across seeds");
        }
    }
}
