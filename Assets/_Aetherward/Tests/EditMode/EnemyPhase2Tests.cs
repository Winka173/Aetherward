using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>One test per Phase 2 enemy mechanic and boss, each also checking the intended counter.</summary>
    public class EnemyPhase2Tests
    {
        private static EnemyUnit Dummy(Battle b, string id, Vec2 at, float hp = 1e5f)
        {
            EnemyUnit e = b.SpawnEnemy(b.Content.Enemies[id], 0, false, null, at);
            e.MaxHp = e.Hp = hp;
            return e;
        }

        private static float Hit(Battle b, EnemyUnit e, DamageKind kind, Element el = Element.None, HeroUnit src = null) =>
            b.DealDamage(e, new DamageRequest { Source = src, Attack = 100f, Multiplier = 1f, Kind = kind, IgnoreDefense = true, Element = el });

        private static void Run(Battle b, float seconds)
        {
            for (int t = 0; t < seconds * 30; t++)
            {
                b.Tick();
                b.Journal.Clear();
            }
        }

        [Test]
        public void GoblinSprinterBurstsOfSpeedAndRootStopsThem()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit g = Dummy(b, "goblin_sprinter", new Vec2(11f, 0f));
            float maxStep = 0f;
            Vec2 last = g.Pos;
            for (int t = 0; t < 30 * 6; t++)
            {
                b.Tick();
                b.Journal.Clear();
                maxStep = SimMath.Max(maxStep, Vec2.Distance(last, g.Pos));
                last = g.Pos;
            }
            Assert.Greater(maxStep, g.Speed * Battle.TickSeconds * 1.5f, "a sprint is clearly faster than walking");
        }

        [Test]
        public void IronbackPlatesHalveBasicsUntilCorroded()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit g = Dummy(b, "ironback_golem", new Vec2(9f, 0f));
            float basic = Hit(b, g, DamageKind.Basic);
            float skill = Hit(b, g, DamageKind.Skill);
            Assert.AreEqual(skill * 0.5f, basic, skill * 0.05f);
            b.AddPoison(g, 5, 5f, null);
            Assert.IsTrue(g.Corroded);
            Assert.Greater(Hit(b, g, DamageKind.Basic), basic * 1.5f, "Corrode strips the plates");
        }

        [Test]
        public void SpiritSplitterSplitsOnceIntoWisps()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit s = Dummy(b, "spirit_splitter", new Vec2(8f, 0f), 50f);
            Hit(b, s, DamageKind.Skill);
            b.Tick();
            var wisps = b.Enemies.FindAll(e => e.Alive && e.Def.Id == "spirit_wisp");
            Assert.AreEqual(2, wisps.Count);
            foreach (EnemyUnit w in wisps) Hit(b, w, DamageKind.Skill);
            b.Tick();
            Assert.AreEqual(0, b.Enemies.FindAll(e => e.Alive).Count, "wisps never split again");
        }

        [Test]
        public void FlameDevourerIsStokedByFireAndWeakToWater()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit d = Dummy(b, "flame_devourer", new Vec2(9f, 0f));
            float fire = Hit(b, d, DamageKind.Skill, Element.Fire);
            float water = Hit(b, d, DamageKind.Skill, Element.Water);
            Assert.Greater(water, fire * 2f);
            for (int i = 0; i < 20; i++) Hit(b, d, DamageKind.Skill, Element.Fire);
            Assert.AreEqual(d.Def.Params.Get("stokeMax"), d.Stoke, 1e-4f, "stoking is capped");
        }

        [Test]
        public void FrostWraithPhasesUntilIlluminated()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit w = Dummy(b, "frost_wraith", new Vec2(9f, 0f));
            float phased = Hit(b, w, DamageKind.Skill, Element.Fire);
            b.Illuminate(w, 3f, 0f, 0f);
            float lit = Hit(b, w, DamageKind.Skill, Element.Fire);
            Assert.AreEqual(phased / (1f - w.Def.Params.Get("phasing")), lit, lit * 0.1f);
        }

        [Test]
        public void StormHarpyFliesOverFieldsAndShrugsOffMeleeBasics()
        {
            Battle b = TestContent.EmptyBattle(("terra", 0), ("sylph", 4));
            EnemyUnit h = Dummy(b, "storm_harpy", new Vec2(9f, 0f));
            HeroUnit melee = b.Heroes.Find(x => x.Melee);
            HeroUnit ranged = b.Heroes.Find(x => !x.Melee);
            Assume.That(melee != null && ranged != null);
            float m = Hit(b, h, DamageKind.Basic, Element.None, melee);
            float r = Hit(b, h, DamageKind.Basic, Element.None, ranged);
            Assert.AreEqual(r * 0.5f, m, r * 0.05f);
            Assert.IsTrue(b.IsFlying(h));
        }

        [Test]
        public void StoneBurrowerIsUntouchableUntilItSurfacesNearTheCore()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit s = b.SpawnEnemy(b.Content.Enemies["stone_burrower"], 0, false, null, null);
            Assert.IsTrue(s.Burrowed);
            b.ApplyElement(s, Element.Fire, 1f, null, 0);
            Assert.AreEqual(0f, s.Aura[(int)Element.Fire], "cannot be tagged underground");
            bool telegraph = false;
            for (int t = 0; t < 30 * 30 && s.Burrowed; t++)
            {
                b.Tick();
                foreach (SimEvent e in b.Journal.Pending) if (e.Type == SimEventType.Telegraph && e.Id == "surface") telegraph = true;
                b.Journal.Clear();
            }
            Assert.IsFalse(s.Burrowed);
            Assert.IsTrue(telegraph, "surfacing is telegraphed");
            // surfaces once its remaining lane path (which ends ~2 m from the core) is within surfaceDist
            Assert.LessOrEqual(Vec2.Distance(s.Pos, b.Crystal.Pos), s.Def.Params.Get("surfaceDist") + 2.5f);
        }

        [Test]
        public void VoidPriestHealsAndStunsInterruptTheChannel()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit p = Dummy(b, "void_priest", new Vec2(9f, 0f));
            EnemyUnit ally = Dummy(b, "grunt", new Vec2(9.5f, 0f));
            p.Speed = ally.Speed = 0f;
            ally.Hp = ally.MaxHp * 0.5f;
            Run(b, 5f);
            Assert.Greater(ally.Hp, ally.MaxHp * 0.5f, "channelled heal lands");

            Battle b2 = TestContent.EmptyBattle();
            EnemyUnit p2 = Dummy(b2, "void_priest", new Vec2(9f, 0f));
            EnemyUnit a2 = Dummy(b2, "grunt", new Vec2(9.5f, 0f));
            p2.Speed = a2.Speed = 0f;
            a2.Hp = a2.MaxHp * 0.5f;
            for (int t = 0; t < 30 * 5; t++)
            {
                if (p2.ChannelTimer > 0f) p2.StunTimer = 0.2f;
                b2.Tick();
                b2.Journal.Clear();
            }
            Assert.AreEqual(a2.MaxHp * 0.5f, a2.Hp, 1f, "every channel interrupted -> no heal");
        }

        [Test]
        public void HexBinderSilencesButNotSteadfast()
        {
            BattleSetup s = TestContent.Setup(1, 3, ("sylph", 4));
            s.Wave = new WaveDef { Number = 1, TimeLimit = 999f };
            Battle b = new Battle(s);
            HeroUnit h = b.Heroes[0];
            EnemyUnit hex = Dummy(b, "hex_binder", h.Pos + new Vec2(2.5f, 0f));
            hex.Speed = 0f;
            Run(b, 7f);
            Assert.IsTrue(h.SilenceTimer > 0f || b.Stats.Kills > 0 || h.Hp < h.MaxHp, "silence lands on the nearest hero");

            s = TestContent.Setup(1, 3, ("sylph", 4));
            s.Heroes[0].TraitId = "steadfast";
            s.Wave = new WaveDef { Number = 1, TimeLimit = 999f };
            b = new Battle(s);
            hex = Dummy(b, "hex_binder", b.Heroes[0].Pos + new Vec2(2.5f, 0f));
            hex.Speed = 0f;
            for (int t = 0; t < 30 * 7; t++)
            {
                b.Tick();
                b.Journal.Clear();
                Assert.AreEqual(0f, b.Heroes[0].SilenceTimer, "Steadfast is immune");
            }
        }

        [Test]
        public void SiegeColossusStopsAtRangeAndShellsTheCrystal()
        {
            BattleSetup s = TestContent.Setup(1, 3);
            s.Wave = new WaveDef { Number = 1, TimeLimit = 999f };
            Battle b = new Battle(s);
            EnemyUnit c = b.SpawnEnemy(b.Content.Enemies["siege_colossus"], 0, false, null, null);
            c.MaxHp = c.Hp = 1e6f;
            bool shelled = false;
            float hp = b.Crystal.Hp;
            for (int t = 0; t < 30 * 40; t++)
            {
                b.Tick();
                foreach (DelayedStrike ds in b.Strikes) if (ds.EnemySource == c && ds.Delay > 0.5f) shelled = true;
                b.Journal.Clear();
            }
            Assert.IsTrue(shelled, "shells are telegraphed");
            Assert.Less(b.Crystal.Hp, hp);
            Assert.Greater(Vec2.Distance(c.Pos, b.Crystal.Pos), 4f, "it never walks into melee range of the core");
        }

        [Test]
        public void SoulBinderTakesTheLinkedShareAndLinksBreakOnDeath()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit binder = Dummy(b, "soul_binder", new Vec2(9f, 0f));
            EnemyUnit ally = Dummy(b, "grunt", new Vec2(9.6f, 0f));
            binder.Speed = ally.Speed = 0f;
            b.Tick();
            Assert.AreSame(binder, ally.LinkedTo);
            float binderHp = binder.Hp;
            float dealt = Hit(b, ally, DamageKind.Skill);
            Assert.Less(binder.Hp, binderHp, "binder absorbs a share");
            Assert.AreEqual(binderHp - binder.Hp, dealt * binder.Def.Params.Get("linkShare") / (1f - binder.Def.Params.Get("linkShare")), dealt * 0.1f);
            binder.Hp = 1f;
            Hit(b, binder, DamageKind.Skill);
            Assert.IsNull(ally.LinkedTo);
        }

        [Test]
        public void SporeCarrierLeavesARegeneratingCloud()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit carrier = Dummy(b, "spore_carrier", new Vec2(9f, 0f), 10f);
            EnemyUnit ally = Dummy(b, "grunt", new Vec2(9.3f, 0f));
            ally.Speed = 0f;
            ally.Hp = ally.MaxHp * 0.5f;
            Hit(b, carrier, DamageKind.Skill);
            Assert.IsTrue(b.Zones.Exists(z => z.Field != null && z.Field.Id == "spore_cloud"));
            Run(b, 2f);
            Assert.Greater(ally.Hp, ally.MaxHp * 0.5f);
        }

        private static Battle BossBattle(string boss, ulong seed)
        {
            BattleSetup s = TestContent.Setup(10, seed, ("terra", 0), ("marina", 4), ("ignis", 8), ("volt", 6));
            s.Substitutions["siegebreaker_golem"] = boss;
            foreach (HeroLoadout l in s.Heroes) l.Level = 5;
            s.CrystalHp = s.CrystalMaxHp = 1e6f;
            return new Battle(s);
        }

        [Test]
        public void SeraphyneRaisesStatuesAndBlizzardAndNeverSoftlocks()
        {
            Battle b = BossBattle("seraphyne", 21);
            bool statues = false, blizzard = false, marks = false;
            for (int t = 0; t < 30 * 240 && b.Outcome == BattleOutcome.Running; t++)
            {
                b.Tick();
                foreach (SimEvent e in b.Journal.Pending)
                {
                    if (e.Type == SimEventType.BossPhase && e.Id == "seraphyne_statues") statues = true;
                    if (e.Type == SimEventType.BossPhase && e.Id == "seraphyne_blizzard") blizzard = true;
                }
                b.Journal.Clear();
                foreach (DelayedStrike ds in b.Strikes) if (ds.HeroStun > 0f) marks = true;
                EnemyUnit boss = b.Enemies.Find(x => x.Alive && x.Def.Id == "seraphyne");
                if (boss == null) continue;
                if (boss.Phase == 0 && b.Time > 20f) boss.Hp = boss.MaxHp * 0.55f;
                if (boss.Phase == 1 && b.Time > 40f) boss.Hp = SimMath.Min(boss.Hp, boss.MaxHp * 0.4f);
            }
            Assert.IsTrue(marks, "frost marks are telegraphed and freeze");
            Assert.IsTrue(statues);
            Assert.IsTrue(blizzard);
            Assert.AreNotEqual(BattleOutcome.Running, b.Outcome);
            Assert.IsFalse(b.Enemies.Exists(x => x.Alive && x.Def.Id == "ice_statue") && b.Outcome == BattleOutcome.Cleared);
        }

        [Test]
        public void StatuesGuardSeraphyneAndShatterWithHer()
        {
            Battle b = TestContent.EmptyBattle();
            EnemyUnit q = Dummy(b, "seraphyne", new Vec2(8f, 0f), 1e6f);
            q.Speed = 0f;
            float open = Hit(b, q, DamageKind.Trigger, Element.Fire);
            q.Hp = q.MaxHp * 0.59f;
            b.Tick();
            b.Journal.Clear();
            Assert.AreEqual(2, b.Enemies.FindAll(x => x.Alive && x.Def.Id == "ice_statue").Count);
            float guardedHit = Hit(b, q, DamageKind.Trigger, Element.Fire);
            Assert.AreEqual(open * (1f - q.Def.Params.Get("statueGuard")), guardedHit, open * 0.05f);
            q.Hp = 1f;
            Hit(b, q, DamageKind.Trigger, Element.Fire);
            Assert.AreEqual(0, b.Enemies.FindAll(x => x.Alive && x.Def.Id == "ice_statue").Count, "statues shatter with the queen");
        }

        [Test]
        public void GravemawVentsArmourBreachesAndNeverSoftlocks()
        {
            Battle b = BossBattle("gravemaw", 5);
            bool exposed = false, breach = false;
            float minDefense = float.MaxValue;
            for (int t = 0; t < 30 * 300 && b.Outcome == BattleOutcome.Running; t++)
            {
                b.Tick();
                foreach (SimEvent e in b.Journal.Pending)
                {
                    if (e.Type == SimEventType.BossPhase && e.Id == "gravemaw_exposed") exposed = true;
                    if (e.Type == SimEventType.BossPhase && e.Id == "gravemaw_breach") breach = true;
                }
                b.Journal.Clear();
                EnemyUnit boss = b.Enemies.Find(x => x.Alive && x.Def.Id == "gravemaw");
                if (boss == null) continue;
                minDefense = SimMath.Min(minDefense, boss.Defense);
                if (boss.Phase == 0 && exposed && b.Time > 30f) boss.Hp = boss.MaxHp * 0.45f;
            }
            Assert.IsTrue(exposed, "armour vent opens a counter window");
            Assert.IsTrue(breach);
            Assert.Less(minDefense, b.Content.Enemies["gravemaw"].Defense, "defense drops while exposed");
            Assert.AreNotEqual(BattleOutcome.Running, b.Outcome);
        }
    }
}
