using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using Aetherward.Sim.Meta;
using Aetherward.Sim.Run;
using NUnit.Framework;

namespace Aetherward.Tests
{
    public class DifficultyTests
    {
        private static RunController Run(int asc, ulong seed = 9) =>
            RunController.NewRun(TestContent.Db, seed, new[] { "terra", "ignis" }, asc, RunUnlocks.Everything(TestContent.Db));

        [Test]
        public void LaunchAscensionEffectsArePreservedAsModules()
        {
            DifficultyDef d = TestContent.Db.Difficulty;
            Assert.GreaterOrEqual(d.MaxLevel, 5);
            Assert.IsFalse(d.Has("frenzy", 0));
            Assert.IsTrue(d.Has("frenzy", 1));
            Assert.AreEqual(0.04f, d.Value("enemy_speed", 2), 1e-4f);    // retuned 0.08 -> 0.04 (lab_ascension_retune.md)
            Assert.AreEqual(1000f * 0.92f, Run(3).State.CrystalBaseMaxHp, 0.01f);
            Assert.AreEqual(1000f, Run(2).State.CrystalBaseMaxHp, 0.01f);
            Assert.AreEqual(0.05f, Run(4).BuildModifiers().EnemyDamagePct, 1e-4f);
            Assert.AreEqual(0f, Run(3).BuildModifiers().EnemyDamagePct, 1e-4f);
        }

        [Test]
        public void ShopPricesRiseFromLevelTwo()
        {
            Assert.AreEqual(Run(1).PriceScale * 1.15f, Run(2).PriceScale, 1e-4f);
        }

        [Test]
        public void BlockedNodeIsTelegraphedRespectedAndSaved()
        {
            Assert.AreEqual(-1, Run(2).State.BlockedNode);
            RunController rc = Run(3);
            int blocked = rc.State.BlockedNode;
            Assert.That(blocked, Is.InRange(0, 11));
            foreach (HeroRunState h in rc.State.Heroes) Assert.AreNotEqual(blocked, h.Node);
            Assert.IsFalse(rc.PlaceHero(rc.State.Heroes[0].Uid, blocked));
            Formation.AutoArrange(rc);
            foreach (HeroRunState h in rc.State.Heroes) Assert.AreNotEqual(blocked, h.Node);
            var saves = new SaveService(new MemoryStorage());
            saves.SaveRun(rc.State);
            Assert.AreEqual(blocked, saves.LoadRun(TestContent.Db).BlockedNode);
        }

        [Test]
        public void ElitesGetAnAffixAtLevelFour()
        {
            BattleSetup s = TestContent.Setup(1, 3, ("terra", 0));
            s.Wave = new WaveDef { Number = 1, TimeLimit = 999f };
            s.EliteExtraAffix = true;
            Battle b = new Battle(s);
            EnemyUnit e = b.SpawnEnemy(b.Content.Enemies["grunt"], 0, true, null, new Vec2(6f, 0f));
            Assert.IsNotNull(e.Affix);
            EnemyUnit boss = b.SpawnEnemy(b.Content.Enemies["rift_warden"], 0, false, null, new Vec2(6f, 3f));
            Assert.IsNull(boss.Affix, "bosses never roll extra affixes");
        }

        [Test]
        public void BossEnrageTriggersOnceBelowAQuarter()
        {
            BattleSetup s = TestContent.Setup(1, 3, ("terra", 0));
            s.Wave = new WaveDef { Number = 1, TimeLimit = 999f };
            s.BossEnrage = 0.25f;
            Battle b = new Battle(s);
            EnemyUnit boss = b.SpawnEnemy(b.Content.Enemies["siegebreaker_golem"], 0, false, null, new Vec2(9f, 0f));
            float atk = boss.Attack;
            boss.Hp = boss.MaxHp * 0.2f;
            b.Tick();
            b.Tick();
            Assert.IsTrue(boss.Enraged);
            Assert.AreEqual(atk * 1.25f, boss.Attack, 0.01f, "enrage applies exactly once");
        }
    }
}
