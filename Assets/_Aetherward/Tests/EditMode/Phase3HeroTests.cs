using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>Expansion Phase 3 heroes: one focused test per signature mechanic and its safety bounds.</summary>
    public class Phase3HeroTests
    {
        private static EnemyUnit Dummy(Battle b, Vec2 at, string id = "grunt")
        {
            EnemyUnit e = b.SpawnEnemy(b.Content.Enemies[id], 0, false, null, at);
            e.MaxHp = e.Hp = 1e5f;
            e.Speed = 0f;
            return e;
        }

        private static Battle Make(string evo, params (string, int)[] heroes)
        {
            BattleSetup s = TestContent.Setup(1, 42, heroes);
            s.Wave = new WaveDef { Number = 1, TimeLimit = 999f };
            if (evo != null)
            {
                s.Heroes[0].Level = 5;
                s.Heroes[0].EvolutionId = evo;
            }
            return new Battle(s);
        }

        [Test]
        public void CaelisEchoesTheNextAllySkillOnceAndEchoesNeverChain()
        {
            Battle b = Make(null, ("caelis", 4), ("ignis", 5), ("terra", 0));
            HeroUnit caelis = b.Heroes[0], ignis = b.Heroes[1];
            for (int i = 0; i < 3; i++) Dummy(b, new Vec2(5.5f + i * 0.3f, 1.2f + 0.2f * i));
            b.Tick();
            Assert.IsTrue(b.CastSkill(caelis, 1f, false));
            Assert.Greater(caelis.EchoPrimed, 0f);
            int before = ignis.SkillCasts;
            Assert.IsTrue(b.CastSkill(ignis, 1f, false));
            Assert.AreEqual(before + 2, ignis.SkillCasts, "the ally skill plus exactly one echo");
            Assert.AreEqual(0, caelis.EchoCharges);
            b.CastSkill(ignis, 1f, false);
            Assert.AreEqual(before + 3, ignis.SkillCasts, "no charge left: no further echo");
        }

        [Test]
        public void ArcaneBarrageHitsSeveralTargetsAndLeavesThemResonant()
        {
            Battle b = Make("caelis_arcane_barrage", ("caelis", 4));
            EnemyUnit a = Dummy(b, b.Heroes[0].Pos + new Vec2(2f, 0f));
            EnemyUnit c = Dummy(b, b.Heroes[0].Pos + new Vec2(2.5f, 1.5f));
            b.Tick();
            Assert.IsTrue(b.CastSkill(b.Heroes[0], 1f, false));
            Assert.IsTrue(a.Hp < a.MaxHp && c.Hp < c.MaxHp);
            Assert.IsTrue(a.ResonantTimer > 0f && c.ResonantTimer > 0f);
        }

        [Test]
        public void OrianeCircleAmplifiesReactionsInside()
        {
            Battle b = Make(null, ("oriane", 4));
            EnemyUnit e = Dummy(b, b.Heroes[0].Pos + new Vec2(2.5f, 0f));
            b.Tick();
            Assert.IsTrue(b.CastSkill(b.Heroes[0], 1f, false));
            Zone z = b.Zones.Find(x => x.Field != null && x.Field.Id == "rune_circle");
            Assert.IsNotNull(z);
            b.Tick();
            Assert.Greater(e.FieldReactionAmp, 0.2f);
        }

        [Test]
        public void ZerithPullsStacksUnstableAndNeverDragsOntoTheCrystal()
        {
            Battle b = Make(null, ("zerith", 4));
            EnemyUnit a = Dummy(b, b.Heroes[0].Pos + new Vec2(2f, 0.8f));
            EnemyUnit c = Dummy(b, b.Heroes[0].Pos + new Vec2(2.6f, -0.6f));
            b.Tick();
            Assert.IsTrue(b.CastSkill(b.Heroes[0], 1f, false));
            Assert.IsTrue(a.UnstableStacks > 0 || a.UnstableCooldown > 0f);
            Zone rift = b.Zones.Find(x => x.Field != null && x.Field.Id == "rift");
            Assert.IsNotNull(rift);
            Assert.GreaterOrEqual(Vec2.Distance(rift.Pos, b.Crystal.Pos), b.Crystal.Radius + 1.5f);
            for (int t = 0; t < 30 * 3; t++) { b.Tick(); b.Journal.Clear(); }
            Assert.IsFalse(b.Zones.Contains(rift), "the rift collapses and ends");
        }

        [Test]
        public void MaelisWardSealsAndBlocksBolts()
        {
            Battle b = Make(null, ("maelis", 0), ("sylph", 4));
            HeroUnit m = b.Heroes[0];
            EnemyUnit e = Dummy(b, m.Pos + new Vec2(1.2f, 0f));
            b.Tick();
            Assert.IsTrue(b.CastSkill(m, 1f, false));
            Assert.Greater(e.SealTimer, 0f);
            Zone ward = b.Zones.Find(x => x.Field != null && x.Field.Id == "void_ward");
            Assert.IsNotNull(ward);
            Assert.IsTrue(ward.Field.BlockBolts);
        }

        [Test]
        public void SolenneMarksDetonateAtTheThresholdExactlyOnce()
        {
            Battle b = Make(null, ("solenne", 4));
            HeroUnit h = b.Heroes[0];
            EnemyUnit e = Dummy(b, h.Pos + new Vec2(2.5f, 0f));
            b.Tick();
            b.CastSkill(h, 1f, false);
            Assert.AreEqual(2, e.MarkStacks);
            float hp = e.Hp;
            b.CastSkill(h, 1f, false);
            Assert.AreEqual(0, e.MarkStacks, "4 marks detonate and are consumed");
            Assert.Less(e.Hp, hp);
        }

        [Test]
        public void MirelPushesEnemiesAwayFromTheCrystal()
        {
            Battle b = Make(null, ("mirel", 4));
            EnemyUnit e = Dummy(b, b.Heroes[0].Pos + new Vec2(2f, 0f));
            float d0 = Vec2.Distance(e.Pos, b.Crystal.Pos);
            b.Tick();
            Assert.IsTrue(b.CastSkill(b.Heroes[0], 1f, false));
            for (int t = 0; t < 10; t++) b.Tick();
            Assert.Greater(Vec2.Distance(e.Pos, b.Crystal.Pos), d0 + 0.5f);
            Assert.IsTrue(b.Zones.Exists(x => x.Field != null && x.Field.Id == "river_stream"));
        }

        [Test]
        public void VeyraRampsOnOneTargetAndResetsOnRetarget()
        {
            Battle b = Make(null, ("veyra", 4));
            HeroUnit h = b.Heroes[0];
            EnemyUnit a = Dummy(b, h.Pos + new Vec2(3f, 0f));
            EnemyUnit c = Dummy(b, h.Pos + new Vec2(3f, 1.5f));
            h.RampTargetUid = a.Uid;
            h.RampStacks = 6;
            Assert.AreEqual(0.36f, b.PassiveBonus(h, a), 1e-4f);
            Assert.AreEqual(0f, b.PassiveBonus(h, c), "ramp only applies to its own target");
            b.Tick();
            b.CastSkill(h, 1f, false);
            Assert.AreEqual(0, h.RampStacks, "the charged shot spends the ramp");
        }

        [Test]
        public void IsoldeShattersFrozenTargets()
        {
            Battle b = Make(null, ("isolde", 4));
            HeroUnit h = b.Heroes[0];
            EnemyUnit e = Dummy(b, h.Pos + new Vec2(2.5f, 0f));
            e.Frozen = true;
            e.StunTimer = 3f;
            b.Tick();
            Assert.IsTrue(b.CastSkill(h, 1f, false));
            Assert.IsFalse(e.Frozen, "shattered");
            Assert.Greater(e.BrittleTimer, 0f);
        }

        [Test]
        public void AerisDriftsFieldsButNeverWallsOrOntoTheCrystal()
        {
            Battle b = Make(null, ("aeris", 4));
            HeroUnit h = b.Heroes[0];
            EnemyUnit e = Dummy(b, h.Pos + new Vec2(3f, 1f));
            ContentDatabase db = b.Content;
            Zone pool = b.SpawnField(db.Fields["overgrowth"], h.Pos + new Vec2(1f, -1f), 1.5f, 5f, null, 10f, 0, "test", null);
            Zone wall = b.SpawnField(db.Fields["stone_wall"], h.Pos + new Vec2(1f, 0f), 0.45f, 5f, null, 10f, 0, "test", h.Pos + new Vec2(1f, 1f));
            Vec2 p0 = pool.Pos, w0 = wall.Pos;
            b.Tick();
            Assert.IsTrue(b.CastSkill(h, 1f, false));
            Assert.Less(Vec2.Distance(pool.Pos, e.Pos), Vec2.Distance(p0, e.Pos), "fields drift toward the enemies");
            Assert.AreEqual(w0.X, wall.Pos.X, 1e-5f, "walls never move");
            Assert.GreaterOrEqual(Vec2.Distance(pool.Pos, b.Crystal.Pos), b.Crystal.Radius + 1.2f - 1e-3f);
        }

        [Test]
        public void DoranTurnsDefenseIntoDamageAndCracksArmour()
        {
            Battle b = Make(null, ("doran", 0));
            HeroUnit h = b.Heroes[0];
            EnemyUnit e = Dummy(b, h.Pos + new Vec2(0.7f, 0f));
            Assert.Greater(b.PassiveBonus(h, e), 0.1f);
            Assert.LessOrEqual(b.PassiveBonus(h, e), 0.4f + 1e-4f);
            b.Tick();
            Assert.IsTrue(b.CastSkill(h, 1f, false));
            Assert.Greater(e.ArmorCrackStacks, 0);
        }

        [Test]
        public void ElowenBeamIlluminatesAndHealsAlongIt()
        {
            Battle b = Make(null, ("elowen", 4), ("terra", 0));
            HeroUnit h = b.Heroes[0], ally = b.Heroes[1];
            EnemyUnit e = Dummy(b, h.Pos + new Vec2(2.5f, 0f));
            ally.Hp = ally.MaxHp * 0.5f;
            b.Tick();
            Assert.IsTrue(b.CastSkill(h, 1f, false));
            Assert.IsTrue(e.Illuminated);
            Assert.Greater(ally.Hp, ally.MaxHp * 0.5f);
        }

        [Test]
        public void MorvenGuardsHurtAlliesWithinBounds()
        {
            Battle b = Make(null, ("morven", 0), ("sylph", 3));
            HeroUnit m = b.Heroes[0], ally = b.Heroes[1];
            b.Tick();
            ally.Pos = m.Pos + new Vec2(1.2f, 0f);   // the guard works on live distance: keep the ally beside Morven
            ally.Hp = ally.MaxHp * 0.3f;
            float mHp = m.Hp, aHp = ally.Hp;
            b.DamageHero(ally, 40f, null);
            Assert.Less(m.Hp, mHp, "Morven takes a share");
            m.Hp = m.MaxHp * 0.2f;
            m.RedirectTimer = 0f;
            float before = m.Hp;
            b.DamageHero(ally, 40f, null);
            Assert.AreEqual(before, m.Hp, 1e-3f, "never guards below 25% of his own HP");
        }

        [Test]
        public void AwakeningIsBoundedDeterministicSavedAndUsedInCombat()
        {
            ContentDatabase db = TestContent.Db;
            Aetherward.Sim.Run.RunController rc = Aetherward.Sim.Run.RunController.NewRun(db, 11, new[] { "ignis", "terra" }, 0, Aetherward.Sim.Run.RunUnlocks.Everything(db));
            Assert.IsFalse(rc.CanAwaken(), "level 1 heroes are not eligible");
            foreach (var h in rc.State.Heroes) h.Level = 3;
            var first = rc.Awaken();
            Assert.IsNotNull(first);
            Element el = ElementUtil.TryParse(first.Awakened, out Element e) ? e : Element.None;
            Assert.AreNotEqual(db.Heroes[first.DefId].Element, el);
            Assert.AreEqual(ReactionCategory.Signature, db.ReactionFor(db.Heroes[first.DefId].Element, el).Category);
            Assert.IsNotNull(rc.Awaken());
            Assert.IsFalse(rc.CanAwaken(), "at most two awakenings per run");
            Assert.IsNull(rc.Awaken());

            var rc2 = Aetherward.Sim.Run.RunController.NewRun(db, 11, new[] { "ignis", "terra" }, 0, Aetherward.Sim.Run.RunUnlocks.Everything(db));
            foreach (var h in rc2.State.Heroes) h.Level = 3;
            Assert.AreEqual(first.Awakened, rc2.Awaken().Awakened, "deterministic per seed");

            var saves = new Aetherward.Sim.Meta.SaveService(new Aetherward.Sim.Meta.MemoryStorage());
            saves.SaveRun(rc.State);
            Assert.AreEqual(first.Awakened, saves.LoadRun(db).Heroes.Find(h => h.Uid == first.Uid).Awakened);

            rc.State.Heroes[0].Node = 4;
            rc.State.Heroes[1].Node = 0;
            Battle b = new Battle(rc.BuildBattleSetup());
            HeroUnit hu = b.Heroes.Find(x => x.Def.Id == first.DefId);
            Assert.AreEqual(el, hu.SecondaryElement);
        }
    }
}
