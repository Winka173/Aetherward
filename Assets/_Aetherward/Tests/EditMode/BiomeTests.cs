using System.Collections.Generic;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using Aetherward.Sim.Meta;
using Aetherward.Sim.Run;
using NUnit.Framework;

namespace Aetherward.Tests
{
    public class BiomeTests
    {
        private static Battle BiomeBattle(string biome, int wave, params (string hero, int node)[] heroes)
        {
            BattleSetup s = TestContent.Setup(1, 42, heroes);
            s.Wave = new WaveDef { Number = wave, TimeLimit = 999f };
            s.Biome = TestContent.Db.Biomes[biome];
            s.CrystalHp = s.CrystalMaxHp = 1e6f;
            return new Battle(s);
        }

        /// <summary>Runs until the enemy reaches and damages the crystal; false if it never gets there.</summary>
        private static bool ReachesCrystal(Battle b, EnemyUnit e, float seconds)
        {
            float hp = b.Crystal.Hp;
            for (int t = 0; t < seconds * 30 && e.Alive; t++)
            {
                b.Tick();
                b.Journal.Clear();
                if (b.Crystal.Hp < hp) return true;
            }
            return false;
        }

        [Test]
        public void EveryBiomeLaneReachesTheCrystal()
        {
            ContentDatabase db = TestContent.Db;
            foreach (BiomeDef biome in db.BiomeList)
                for (int lane = 0; lane < biome.Arena.Lanes.Count; lane++)
                {
                    Battle b = BiomeBattle(biome.Id, 1);
                    EnemyUnit e = b.SpawnEnemy(db.Enemies["grunt"], lane, false, null, null);
                    e.MaxHp = e.Hp = 1e6f;
                    Assert.IsTrue(ReachesCrystal(b, e, 60f), biome.Id + " lane " + lane + " must reach the crystal");
                }
        }

        [Test]
        public void WallsOnEveryLaneSlowButNeverBlockThePath()
        {
            ContentDatabase db = TestContent.Db;
            FieldDef wall = db.Fields["stone_wall"];
            foreach (BiomeDef biome in db.BiomeList)
                for (int lane = 0; lane < biome.Arena.Lanes.Count; lane++)
                {
                    Battle b = BiomeBattle(biome.Id, 1);
                    LaneDef l = biome.Arena.Lanes[lane];
                    // A wall straight across the lane at every interior waypoint.
                    for (int i = 1; i < l.Points.Count - 1; i++)
                    {
                        Vec2 dir = (l.Points[i + 1] - l.Points[i]).Normalized;
                        Vec2 side = new Vec2(-dir.Y, dir.X) * 1.2f;
                        b.SpawnField(wall, l.Points[i], 0.45f, 999f, null, 0f, 0, "test", l.Points[i] + side).Pos = l.Points[i] - side;
                    }
                    EnemyUnit e = b.SpawnEnemy(db.Enemies["grunt"], lane, false, null, null);
                    e.MaxHp = e.Hp = 1e6f;
                    Assert.IsTrue(ReachesCrystal(b, e, 120f), biome.Id + " lane " + lane + " is blocked by walls");
                }
        }

        [Test]
        public void LavaVentsAreTelegraphedAndHurtEnemiesStandingOnThem()
        {
            Battle b = BiomeBattle("molten_crater", 3, ("terra", 0));
            HazardDef hz = b.Biome.Hazards[0];
            var dummies = new List<EnemyUnit>();
            foreach (Vec2 p in hz.Points)
            {
                EnemyUnit e = b.SpawnEnemy(b.Content.Enemies["grunt"], 0, false, null, p);
                e.Speed = 0f;
                e.MaxHp = e.Hp = 1e5f;
                dummies.Add(e);
            }
            bool telegraphed = false;
            for (int t = 0; t < 30 * 20; t++)
            {
                b.Tick();
                b.Journal.Clear();
                foreach (DelayedStrike s in b.Strikes)
                    if (s.Kind == StrikeKind.Hazard && s.Delay > 0.5f) telegraphed = true;
                foreach (EnemyUnit e in dummies) e.Pos = hz.Points[dummies.IndexOf(e)];
            }
            Assert.IsTrue(telegraphed, "vents warn before erupting");
            Assert.IsTrue(dummies.Exists(e => e.Hp < e.MaxHp), "eruptions damage enemies too");
        }

        [Test]
        public void HazardsHitHeroesForABoundedShareOfMaxHp()
        {
            Battle b = BiomeBattle("molten_crater", 3, ("terra", 4));
            HeroUnit h = b.Heroes[0];
            HazardDef hz = b.Biome.Hazards[0];
            h.Pos = h.Anchor = hz.Points[0];
            EnemyUnit keepAlive = b.SpawnEnemy(b.Content.Enemies["grunt"], 0, false, null, new Vec2(11f, 6f));
            keepAlive.Speed = 0f;
            keepAlive.MaxHp = keepAlive.Hp = 1e6f;
            float lowest = h.Hp;
            for (int t = 0; t < 30 * 40; t++)
            {
                h.Pos = hz.Points[0];
                float before = h.Hp;
                b.Tick();
                b.Journal.Clear();
                if (before - h.Hp > 0f) Assert.LessOrEqual(before - h.Hp, h.MaxHp * hz.HeroDamagePct + 1f, "one eruption is capped");
                if (h.Hp < lowest) lowest = h.Hp;
            }
            Assert.Less(lowest, h.MaxHp, "a hero standing in a vent gets hit at some point");
        }

        [Test]
        public void IceCoversSpawnAndBreakAfterTheirHits()
        {
            Battle b = BiomeBattle("frostfall_bastion", 5, ("terra", 0));
            List<Zone> covers = b.Zones.FindAll(z => z.Field != null && z.Field.Id == "ice_cover");
            Assert.AreEqual(b.Biome.Covers.Count, covers.Count);
            foreach (Zone z in covers) Assert.AreEqual(8, z.HitsLeft);
        }

        [Test]
        public void FrostfallDiagonalGatesOpenOnWaveEight()
        {
            ContentDatabase db = TestContent.Db;
            BiomeDef frost = db.Biomes["frostfall_bastion"];
            Assert.AreEqual(0, frost.MapLane(4, 5));
            Assert.AreEqual(1, frost.MapLane(5, 7));
            Assert.AreEqual(4, frost.MapLane(4, 8));
            Assert.AreEqual(5, frost.MapLane(5, 12));
            foreach (WaveDef w in db.Waves)
                foreach (int lane in Battle.LanesForWave(w, frost))
                    if (w.Number < 8) Assert.IsTrue(lane != 4 && lane != 5, "wave " + w.Number + " uses a closed gate");
        }

        [Test]
        public void AreaTraitsFollowPositionAndExpireWhenLeaving()
        {
            Battle b = BiomeBattle("molten_crater", 1, ("terra", 0));
            HeroUnit h = b.Heroes[0];
            float attack = h.Stat(StatId.Attack);
            EnemyUnit dummy = b.SpawnEnemy(b.Content.Enemies["grunt"], 0, false, null, new Vec2(18, 0));
            dummy.Speed = 0f;
            h.Pos = h.Anchor = b.Biome.AreaTraits[0].Pos;
            b.Tick();
            Assert.AreEqual(attack * 1.15f, h.Stat(StatId.Attack), 0.01f);
            h.Pos = h.Anchor = new Vec2(1.6f, 1.3f);
            b.Tick();
            Assert.AreEqual(attack, h.Stat(StatId.Attack), 0.01f, "leaving a region removes its bonus");
        }

        [Test]
        public void BiomeIsSavedAndDrivesBossAndExtraSpawns()
        {
            ContentDatabase db = TestContent.Db;
            RunController rc = RunController.NewRun(db, 7, new[] { "terra", "ignis" }, 0, RunUnlocks.Everything(db), "frostfall_bastion");
            var saves = new SaveService(new MemoryStorage());
            saves.SaveRun(rc.State);
            RunState loaded = saves.LoadRun(db);
            Assert.AreEqual("frostfall_bastion", loaded.BiomeId);
            Assert.AreEqual("seraphyne", rc.BossFor(db.Waves[9]));
            rc.State.Wave = 8;
            Assert.AreEqual("frostfall_bastion", rc.BuildBattleSetup().Biome.Id);
            Assert.IsTrue(rc.PreviewEnemies(db.Waves[7]).Exists(k => k.Key == "frost_wraith"), "biome extras show up in the preview");
            RunController plain = RunController.NewRun(db, 7, new[] { "terra", "ignis" }, 0, RunUnlocks.Everything(db));
            Assert.IsTrue(plain.Biome.Default);
            Assert.IsFalse(plain.PreviewEnemies(db.Waves[7]).Exists(k => k.Key == "frost_wraith"));
        }

        [Test]
        public void BiomesUnlockThroughProgressAndPersist()
        {
            ContentDatabase db = TestContent.Db;
            MetaProfile m = MetaProfile.CreateDefault(db);
            Assert.IsTrue(m.UnlockedBiomes.Contains(db.DefaultBiome.Id));
            Assert.IsFalse(m.UnlockedBiomes.Contains("molten_crater"));
            RunController rc = RunController.NewRun(db, 3, new[] { "terra", "ignis" }, 0, m.ToRunUnlocks());
            rc.State.Wave = 8;
            List<string> unlocked = m.RecordRun(rc, new RunResults { Victory = false }, 0);
            Assert.Contains("biome:molten_crater", unlocked);
            var saves = new SaveService(new MemoryStorage());
            saves.SaveMeta(m);
            Assert.IsTrue(saves.LoadMeta(db).UnlockedBiomes.Contains("molten_crater"));
        }

        [Test]
        public void FullBiomeWavesResolveWithoutSoftlock()
        {
            ContentDatabase db = TestContent.Db;
            foreach (string biome in new[] { "molten_crater", "frostfall_bastion" })
                foreach (int wave in new[] { 6, 9, 15 })
                {
                    BattleSetup s = TestContent.Setup(wave, 11, ("terra", 0), ("marina", 4), ("ignis", 8), ("volt", 6));
                    s.Biome = db.Biomes[biome];
                    foreach (HeroLoadout l in s.Heroes) l.Level = 6;
                    Battle b = new Battle(s);
                    for (int t = 0; t < 30 * 400 && b.Outcome == BattleOutcome.Running; t++)
                    {
                        b.Tick();
                        b.Journal.Clear();
                    }
                    Assert.AreNotEqual(BattleOutcome.Running, b.Outcome, biome + " wave " + wave);
                }
        }
    }
}
