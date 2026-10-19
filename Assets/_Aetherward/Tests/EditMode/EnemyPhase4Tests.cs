using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>Phase 4 enemies (reflect, chaos, mimic, regen) and the generic-module bosses.</summary>
    public class EnemyPhase4Tests
    {
        private static EnemyUnit Dummy(Battle b, string id, Vec2 at, float hp = 1e5f)
        {
            EnemyUnit e = b.SpawnEnemy(b.Content.Enemies[id], 0, false, null, at);
            e.MaxHp = e.Hp = hp;
            e.Speed = 0f;
            return e;
        }

        [Test]
        public void MirrorKnightReflectsSkillsButNeverKills()
        {
            Battle b = TestContent.EmptyBattle(("ignis", 4));
            HeroUnit h = b.Heroes[0];
            EnemyUnit k = Dummy(b, "mirror_knight", h.Pos + new Vec2(2f, 0f));
            float hp = h.Hp;
            b.DealDamage(k, new DamageRequest { Source = h, Attack = 200f, Multiplier = 1f, Kind = DamageKind.Skill, IgnoreDefense = true });
            Assert.Less(h.Hp, hp, "skills are reflected");
            hp = h.Hp;
            b.DealDamage(k, new DamageRequest { Source = h, Attack = 200f, Multiplier = 1f, Kind = DamageKind.Basic, IgnoreDefense = true });
            Assert.AreEqual(hp, h.Hp, "basic attacks are not");
            h.Hp = 5f;
            b.DealDamage(k, new DamageRequest { Source = h, Attack = 1e5f, Multiplier = 1f, Kind = DamageKind.Skill, IgnoreDefense = true });
            Assert.IsTrue(h.Alive, "reflection is never lethal");
        }

        [Test]
        public void ChaosElementalCyclesItsResistedElement()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit c = Dummy(b, "chaos_elemental", new Vec2(8f, 0f));
            Element first = c.ChaosElement;
            Assert.AreNotEqual(Element.None, first);
            float resisted = b.DealDamage(c, new DamageRequest { Attack = 100f, Multiplier = 1f, Kind = DamageKind.Trigger, IgnoreDefense = true, Element = first });
            Element other = first == Element.Fire ? Element.Water : Element.Fire;
            float hit = b.DealDamage(c, new DamageRequest { Attack = 100f, Multiplier = 1f, Kind = DamageKind.Trigger, IgnoreDefense = true, Element = other });
            Assert.Less(resisted, hit * 0.5f);
            for (int t = 0; t < 30 * 5; t++) { b.Tick(); b.Journal.Clear(); }
            Assert.AreNotEqual(first, c.ChaosElement, "the element cycles");
        }

        [Test]
        public void ArcaneMimicCopiesNearbyCastsAsACappedShield()
        {
            Battle b = TestContent.EmptyBattle(("ignis", 4));
            HeroUnit h = b.Heroes[0];
            EnemyUnit m = Dummy(b, "arcane_mimic", h.Pos + new Vec2(2f, 0f), 1000f);
            Dummy(b, "grunt", h.Pos + new Vec2(2.4f, 0.3f));
            b.Tick();
            for (int i = 0; i < 10; i++) b.CastSkill(h, 1f, false);
            Assert.Greater(m.Shield, 0f);
            Assert.LessOrEqual(m.Shield, m.MaxHp * 0.08f * 3f + 1e-3f);
        }

        [Test]
        public void BlightShamblerRegeneratesUnlessBurningOrPoisoned()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit s = Dummy(b, "blight_shambler", new Vec2(8f, 0f), 1000f);
            s.Hp = 500f;
            for (int t = 0; t < 30; t++) { b.Tick(); b.Journal.Clear(); }
            Assert.Greater(s.Hp, 515f);
            float hp = s.Hp;
            b.AddPoison(s, 1, 10f, null);
            for (int t = 0; t < 30; t++) { b.Tick(); b.Journal.Clear(); }
            Assert.LessOrEqual(s.Hp, hp, "poison stops the regeneration");
        }

        [Test]
        public void GenericBossModulesFireAndEveryNewBossResolves()
        {
            ContentDatabase db = TestContent.Db;
            foreach (string id in new[] { "vaelith", "mirrath", "aetherion", "thornmother", "ironclad_warlord", "ashen_matriarch", "nyxhollow" })
            {
                EnemyDef def = db.Enemies[id];
                bool twenty = def.Hp > 2500f;
                BattleSetup s = TestContent.Setup(twenty ? 20 : 10, 9, ("terra", 0), ("marina", 4), ("ignis", 8), ("volt", 6), ("seren", 2), ("kael", 5));
                s.Substitutions[twenty ? "rift_warden" : "siegebreaker_golem"] = id;
                foreach (HeroLoadout l in s.Heroes) l.Level = 6;
                s.CrystalHp = s.CrystalMaxHp = 1e6f;
                Battle b = new Battle(s);
                bool telegraph = false, exposed = false, sawBoss = false;
                for (int t = 0; t < 30 * 400 && b.Outcome == BattleOutcome.Running; t++)
                {
                    b.Tick();
                    foreach (SimEvent e in b.Journal.Pending)
                        if (e.Type == SimEventType.BossPhase && e.Id == "boss_exposed") exposed = true;
                    b.Journal.Clear();
                    foreach (DelayedStrike d in b.Strikes) if (d.EnemySource != null && d.EnemySource.Def.Id == id && d.Delay > 0.5f) telegraph = true;
                    EnemyUnit boss = b.Enemies.Find(x => x.Alive && x.Def.Id == id);
                    if (boss != null) sawBoss = true;
                    if (boss != null && b.Time > 60f && boss.HpFraction > 0.3f) boss.Hp = boss.MaxHp * 0.3f; // reach the late phases
                }
                Assert.IsTrue(sawBoss, id);
                Assert.IsTrue(telegraph || !def.Params.Has("markInterval") && !def.Params.Has("volleyInterval"), id + ": heavy hits are telegraphed");
                Assert.IsTrue(exposed, id + ": an exposed window exists");
                Assert.AreNotEqual(BattleOutcome.Running, b.Outcome, id + " softlocked");
            }
        }

        [Test]
        public void MirrathIsGuardedWhileHerKnightsStand()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit q = Dummy(b, "mirrath", new Vec2(8f, 0f), 1e6f);
            float open = b.DealDamage(q, new DamageRequest { Attack = 100f, Multiplier = 1f, Kind = DamageKind.Trigger, IgnoreDefense = true });
            q.Hp = q.MaxHp * 0.69f;
            b.Tick();
            b.Journal.Clear();
            Assert.IsTrue(b.Enemies.Exists(e => e.Alive && e.Def.Id == "mirror_knight"));
            float guarded = b.DealDamage(q, new DamageRequest { Attack = 100f, Multiplier = 1f, Kind = DamageKind.Trigger, IgnoreDefense = true });
            Assert.AreEqual(open * 0.6f, guarded, open * 0.05f);
        }
    }
}
