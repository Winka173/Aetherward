using System;
using System.Collections.Generic;
using System.Linq;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using Aetherward.Sim.Meta;
using Aetherward.Sim.Run;
using NUnit.Framework;

namespace Aetherward.Tests
{
    public class HavenTests
    {
        private static Battle Empty(string biome, bool dynamicParty = true, params string[] heroes)
        {
            BattleSetup setup = TestContent.Setup(1, 71);
            setup.Wave = new WaveDef { Number = 8, TimeLimit = 999f };
            setup.Biome = TestContent.Db.Biomes[biome];
            setup.CrystalHp = setup.CrystalMaxHp = 100000f;
            setup.DynamicParty = dynamicParty;
            for (int i = 0; i < heroes.Length; i++)
                setup.Heroes.Add(new HeroLoadout { Def = TestContent.Db.Heroes[heroes[i]], RosterIndex = i, NodeIndex = i });
            return new Battle(setup);
        }

        [Test]
        public void AllBiomesHaveConnectedWalkableGatesAndSafeHazards()
        {
            foreach (BiomeDef biome in TestContent.Db.BiomeList)
            {
                ArenaDef arena = biome.Arena;
                Assert.IsTrue(arena.IsHaven, biome.Id);
                Assert.IsNotEmpty(arena.Walls);
                HavenNavigation nav = HavenNavigation.For(arena);
                foreach (LaneDef lane in arena.Lanes)
                {
                    Assert.IsTrue(lane.Gate.HasValue, biome.Id + lane.Id);
                    Assert.IsTrue(lane.Points.Any(p => Vec2.Distance(p, lane.Gate.Value) < 0.01f));
                    var path = new List<Vec2>();
                    Vec2 from = new Vec2(2, 2), to = nav.Project(lane.Gate.Value + lane.Gate.Value.Normalized * 2f, 0.4f);
                    nav.FindPath(from, to, path);
                    Assert.IsNotEmpty(path, biome.Id + " gate " + lane.Id);
                    foreach (Vec2 point in path)
                    {
                        Assert.IsTrue(nav.CanTravel(from, point, 0.4f), biome.Id + " path crosses a wall");
                        from = point;
                    }
                    Assert.Less(Vec2.Distance(from, to), 0.6f);
                }
                foreach (HazardDef hazard in biome.Hazards)
                    foreach (Vec2 point in hazard.Points) Assert.IsTrue(nav.CanStand(point, 0.1f), biome.Id + " hazard outside play area");
            }
        }

        [Test]
        public void NavigationGoesThroughGateInsteadOfCuttingThroughWall()
        {
            var nav = HavenNavigation.For(TestContent.Db.DefaultBiome.Arena);
            Vec2 start = new Vec2(4, -3), end = new Vec2(3, -8);
            Assert.IsFalse(nav.CanTravel(start, end, 0.4f));
            var path = new List<Vec2>();
            nav.FindPath(start, end, path);
            Assert.IsNotEmpty(path);
            Assert.IsTrue(path.Any(p => Math.Abs(p.X) < 1.2f && p.Y < -5));
            foreach (Vec2 point in path)
            {
                Assert.IsTrue(nav.CanTravel(start, point, 0.4f));
                start = point;
            }
            Assert.Less(Vec2.Distance(start, end), 0.01f);
        }

        [Test]
        public void MovingPartyAndDashesNeverCrossHavenWalls()
        {
            foreach (BiomeDef biome in TestContent.Db.BiomeList)
            {
                var setup = TestContent.Setup(12, 41, ("terra", 0), ("cinder", 1), ("raiden", 2), ("kael", 3), ("ignis", 4), ("marina", 5));
                setup.Biome = biome; setup.DynamicParty = true; setup.Stance = PartyStance.Aggressive;
                setup.CrystalHp = setup.CrystalMaxHp = 1e6f;
                var b = new Battle(setup);
                var nav = HavenNavigation.For(b.Arena);
                for (int tick = 0; tick < 900 && b.Outcome == BattleOutcome.Running; tick++)
                {
                    Vec2[] before = b.Heroes.Select(h => h.Pos).ToArray();
                    b.Tick(); b.Journal.Clear();
                    for (int i = 0; i < b.Heroes.Count; i++)
                        Assert.IsTrue(nav.CanTravel(before[i], b.Heroes[i].Pos, b.Heroes[i].Radius), biome.Id + " hero " + b.Heroes[i].Def.Id + " crossed wall at " + tick);
                }
            }
        }

        [Test]
        public void GroundEnemiesSlowAtGateAndFlyersKeepTheirSpeed()
        {
            foreach (string enemy in new[] { "grunt", "storm_harpy" })
            {
                Battle haven = Empty("verdant_sanctuary"), legacy = Empty("verdant_sanctuary", false);
                Vec2 point = haven.Arena.Lanes[0].Gate.Value + new Vec2(0.5f, 0);
                EnemyUnit a = haven.SpawnEnemy(haven.Content.Enemies[enemy], 0, false, null, point);
                EnemyUnit b = legacy.SpawnEnemy(legacy.Content.Enemies[enemy], 0, false, null, point);
                a.Waypoint = b.Waypoint = 3;
                haven.Tick(); legacy.Tick();
                float ratio = Vec2.Distance(a.Pos, point) / Vec2.Distance(b.Pos, point);
                Assert.AreEqual(enemy == "grunt" ? Battle.GateSlow : 1f, ratio, 0.02f, enemy);
            }
        }

        [Test]
        public void PillageDamagesCrystalFromInsideKeepAndRecordsItsSource()
        {
            Battle b = Empty("verdant_sanctuary");
            EnemyUnit e = b.SpawnEnemy(b.Content.Enemies["grunt"], 0, false, null, new Vec2(4, 0.3f));
            e.Speed = 0f; e.CrystalDamage = 1000f;
            float hp = b.Crystal.Hp;
            for (int i = 0; i < 15; i++) b.Tick();
            Assert.AreEqual(1, b.Pillagers);
            Assert.Less(b.Crystal.Hp, hp);
            Assert.Greater(b.Stats.CrystalDamageByEnemy["grunt"], 0f);
            Assert.Greater(b.Stats.CrystalDamageByLane[0], 0f);
            e.Pos = new Vec2(10, 0.3f);
            hp = b.Crystal.Hp;
            for (int i = 0; i < 15; i++) b.Tick();
            Assert.AreEqual(0, b.Pillagers);
            Assert.AreEqual(hp, b.Crystal.Hp);
        }

        [Test]
        public void PhysicalSouthGateIsReportedOnceForItsFourApproachLanes()
        {
            var setup = TestContent.Setup(12, 42, ("terra", 0), ("magnus", 1), ("glacius", 2));
            setup.DynamicParty = true;
            var b = new Battle(setup);
            var report = SynergyReport.Analyze(b);
            Assert.LessOrEqual(report.GateCoverage.Count, 3);
            Assert.AreEqual(Battle.GateLane(b.Arena, 2), Battle.GateLane(b.Arena, 5));
            Assert.AreEqual(PartyStance.Balanced, report.Stance);
            Assert.Greater(b.Heroes.Average(h => h.Anchor.Length), 3.5f, "balanced holders leave the crystal");
        }

        [Test]
        public void DynamicDeploymentIgnoresLegacySavedSlots()
        {
            RunController rc = RunController.NewRun(TestContent.Db, 7, new[] { "terra", "ignis" }, 0, RunUnlocks.Everything(TestContent.Db));
            foreach (HeroRunState hero in rc.State.Heroes) hero.Node = -1;
            Battle battle = rc.StartWave();
            Assert.IsNotNull(battle);
            Assert.AreEqual(2, battle.Heroes.Count);
            Assert.IsTrue(battle.Heroes.All(h => h.Pos.Length > battle.Crystal.Radius));
        }

        [Test]
        public void FormationsSplitOrConcentrateTheFrontline()
        {
            Battle Make(PartyFormation formation)
            {
                var setup = TestContent.Setup(12, 42, ("terra", 0), ("magnus", 1), ("glacius", 2));
                setup.DynamicParty = true; setup.Formation = formation;
                return new Battle(setup);
            }
            Battle split = Make(PartyFormation.Split), swarm = Make(PartyFormation.Swarm);
            Assert.Greater(split.Heroes.Select(h => h.PostLane).Distinct().Count(), 1);
            Assert.AreEqual(1, swarm.Heroes.Select(h => h.PostLane).Distinct().Count());
            Battle boss = Make(PartyFormation.BossFocus);
            EnemyUnit target = boss.SpawnEnemy(boss.Content.Enemies["rift_warden"], 1, false, null, new Vec2(-12, 0.3f));
            target.Hp = target.MaxHp = 1e7f; target.Speed = 0;
            for (int i = 0; i < 20; i++) { boss.Tick(); boss.Journal.Clear(); }
            Assert.IsTrue(boss.Heroes.All(h => h.PostLane == 1));
        }

        [Test]
        public void EveryHeroHasValidatedSignatureAndCanCastIt()
        {
            foreach (HeroDef def in TestContent.Db.HeroList)
            {
                Assert.IsNotNull(def.Ultimate, def.Id);
                Battle b = Empty("verdant_sanctuary", true, def.Id);
                HeroUnit hero = b.Heroes[0];
                hero.Ult = 1f; hero.SkillTimer = 999f;
                for (int i = 0; i < 3; i++)
                {
                    EnemyUnit enemy = b.SpawnEnemy(b.Content.Enemies["grunt"], 0, false, null, hero.Pos + new Vec2(1.5f, 0.2f * i));
                    enemy.Speed = 0; enemy.MaxHp = enemy.Hp = 1e6f;
                }
                b.Tick();
                Assert.AreEqual(1, b.Stats.Ultimates, def.Id);
                Assert.AreEqual(0f, hero.Ult, def.Id);
                Assert.IsTrue(b.Strikes.Any(s => s.Kind == StrikeKind.Ultimate), def.Id);
            }
        }
    }
}
