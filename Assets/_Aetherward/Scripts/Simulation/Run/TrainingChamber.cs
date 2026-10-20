using System;
using System.Collections.Generic;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Run
{
    public enum DummyProfile
    {
        Swarm,          // many weak melee units (grunt + swarmling)
        ArmoredElite,   // elite juggernauts (high defense, CC resistant)
        Boss,           // one real boss (siegebreaker_golem) with its full rule set
        HighResistance, // warded units (+20% resist to the six base elements)
        HighMobility    // runners / goblin sprinters
    }

    public sealed class TrainingHero
    {
        public string HeroId;
        public int Level = 4;
        public string EvolutionId;
        public int Node;
    }

    public sealed class TrainingConfig
    {
        public readonly List<TrainingHero> Heroes = new List<TrainingHero>();
        public DummyProfile Profile = DummyProfile.Swarm;
        public float Seconds = 20f;
        public ulong Seed = 1;
        public int WaveLevel = 8;
        /// <summary>Sandbox exception: allows heroes that are not unlocked; the report is marked SANDBOX.</summary>
        public bool Sandbox;
    }

    /// <summary>Every number comes from the real combat rules (Battle + BattleStats); nothing is estimated.</summary>
    public sealed class TrainingReport
    {
        public float Seconds;
        public bool Sandbox;
        public DummyProfile Profile;
        public float RawDps;            // Basic + Skill damage per second
        public float ReactionDps;       // Reaction damage per second
        public float DotDps;            // damage over time per second
        public float TriggerDps;        // relic/passive procs per second
        public float HealPerSecond;
        public float ShieldAbsorbed;
        public float HardCcUptime;      // share of enemy-alive time spent stunned / frozen / rooted
        public float SlowUptime;
        public float AvgTimeToKill;     // seconds from spawn to death, killed enemies only
        public int Kills;
        public int Reactions;
        public float HeroIdleShare;     // share of hero-time with enemies alive but no target in reach
        public int HeroDowns;
        public float MinHeroHpFraction = 1f;
        public float DamageTakenByHeroes;
        public readonly Dictionary<string, float> HeroDamage = new Dictionary<string, float>();
        public readonly List<string> Notes = new List<string>();   // how dummies differ from real waves
        public string Fingerprint;      // reproducibility check (identical config -> identical fingerprint)
    }

    /// <summary>
    /// Training Chamber (P2): fast deterministic out-of-run arena. Runs the real Battle simulation against
    /// dummy profiles built from real enemy definitions. It never touches RunState, MetaProfile or saves, so it
    /// cannot grant rewards or alter campaign progress (enforced by API shape and tests).
    /// </summary>
    public static class TrainingChamber
    {
        public static readonly float[] AllowedSeconds = { 15f, 20f, 30f };

        public static bool CanUse(ContentDatabase db, TrainingConfig cfg, ICollection<string> unlockedHeroes, out string reason)
        {
            reason = null;
            if (cfg.Heroes.Count == 0 || cfg.Heroes.Count > 6) { reason = "team_size"; return false; }
            foreach (TrainingHero h in cfg.Heroes)
            {
                if (!db.Heroes.ContainsKey(h.HeroId)) { reason = "unknown_hero"; return false; }
                if (!cfg.Sandbox && unlockedHeroes != null && !unlockedHeroes.Contains(h.HeroId)) { reason = "locked:" + h.HeroId; return false; }
                if (h.EvolutionId != null && (!db.Evolutions.TryGetValue(h.EvolutionId, out EvolutionDef e) || e.HeroId != h.HeroId)) { reason = "bad_evolution"; return false; }
            }
            return true;
        }

        public static WaveDef DummyWave(DummyProfile p, int level, float seconds)
        {
            var w = new WaveDef { Number = level, Level = level, TimeLimit = seconds + 5f, Lanes = new List<int> { 0, 1, 2, 3 } };
            void G(string id, int count, float start, float interval, bool elite = false, int lane = -1) =>
                w.Groups.Add(new SpawnGroup { Enemy = id, Count = count, Start = start, Interval = interval, Elite = elite, Lane = lane });
            int reps = (int)Math.Ceiling(seconds / 10f);
            switch (p)
            {
                case DummyProfile.Swarm:
                    for (int r = 0; r < reps; r++) { G("grunt", 8, r * 10f, 0.5f); G("swarmling", 10, r * 10f + 1f, 0.35f); }
                    break;
                case DummyProfile.ArmoredElite:
                    for (int r = 0; r < reps; r++) G("juggernaut", 2, r * 10f, 3f, true);
                    break;
                case DummyProfile.Boss:
                    G("siegebreaker_golem", 1, 0f, 1f, false, 0);
                    w.Boss = true;
                    break;
                case DummyProfile.HighResistance:
                    for (int r = 0; r < reps; r++) G("warded", 6, r * 10f, 1f);
                    break;
                case DummyProfile.HighMobility:
                    for (int r = 0; r < reps; r++) { G("runner", 8, r * 10f, 0.6f); G("goblin_sprinter", 4, r * 10f + 2f, 0.8f); }
                    break;
            }
            return w;
        }

        public static TrainingReport Run(ContentDatabase db, TrainingConfig cfg)
        {
            if (!AllowedSecondsContains(cfg.Seconds)) cfg.Seconds = SimMath.Clamp(cfg.Seconds, 15f, 30f);
            var setup = new BattleSetup
            {
                Content = db,
                Wave = DummyWave(cfg.Profile, cfg.WaveLevel, cfg.Seconds),
                Seed = cfg.Seed,
                CrystalMaxHp = 1e9f,      // dummies: the Crystal cannot fall, so every test runs its full duration
                CrystalHp = 1e9f,
                Biome = db.DefaultBiome
            };
            for (int i = 0; i < cfg.Heroes.Count; i++)
            {
                TrainingHero h = cfg.Heroes[i];
                setup.Heroes.Add(new HeroLoadout { Def = db.Heroes[h.HeroId], Level = h.Level, EvolutionId = h.EvolutionId, NodeIndex = h.Node, RosterIndex = i });
            }
            var b = new Battle(setup);
            var rep = new TrainingReport { Seconds = cfg.Seconds, Sandbox = cfg.Sandbox, Profile = cfg.Profile };
            var born = new Dictionary<int, float>();
            var dead = new HashSet<int>();
            float enemyTime = 0f, ccTime = 0f, slowTime = 0f, heroTime = 0f, idleTime = 0f, ttkSum = 0f;
            int ttkN = 0;
            int ticks = (int)Math.Round(cfg.Seconds / Battle.TickSeconds);
            for (int t = 0; t < ticks && b.Outcome == BattleOutcome.Running; t++)
            {
                b.Tick();
                b.Journal.Clear();
                int alive = 0;
                foreach (EnemyUnit e in b.Enemies)
                {
                    if (!born.ContainsKey(e.Uid)) born[e.Uid] = b.Time;
                    if (e.Alive)
                    {
                        alive++;
                        enemyTime += Battle.TickSeconds;
                        if (e.StunTimer > 0f || e.Frozen || e.RootTimer > 0f) ccTime += Battle.TickSeconds;
                        else if (e.SlowTimer > 0f) slowTime += Battle.TickSeconds;
                    }
                    else if (dead.Add(e.Uid))
                    {
                        ttkSum += b.Time - born[e.Uid];
                        ttkN++;
                    }
                }
                foreach (HeroUnit h in b.Heroes)
                {
                    if (!h.Alive) continue;
                    rep.MinHeroHpFraction = Math.Min(rep.MinHeroHpFraction, h.Hp / Math.Max(1f, h.MaxHp));
                    if (alive == 0) continue;
                    heroTime += Battle.TickSeconds;
                    if (h.Target == null) idleTime += Battle.TickSeconds;
                }
            }
            float secs = Math.Max(Battle.TickSeconds, b.Time);
            float[] k = b.Stats.DamageByKind;
            rep.RawDps = (k[(int)DamageKind.Basic] + k[(int)DamageKind.Skill]) / secs;
            rep.ReactionDps = k[(int)DamageKind.Reaction] / secs;
            rep.DotDps = k[(int)DamageKind.Dot] / secs;
            rep.TriggerDps = k[(int)DamageKind.Trigger] / secs;
            rep.ShieldAbsorbed = b.Stats.HeroShieldAbsorbed;
            rep.Kills = b.Stats.Kills;
            rep.HeroDowns = b.Stats.HeroDowns;
            foreach (int c in b.Stats.ReactionCounts.Values) rep.Reactions += c;
            float heal = 0f;
            foreach (HeroUnit h in b.Heroes)
            {
                heal += h.HealingDone;
                rep.DamageTakenByHeroes += h.DamageTaken;
                rep.HeroDamage[h.Def.Id] = h.DamageDealt;
            }
            rep.HealPerSecond = heal / secs;
            rep.HardCcUptime = enemyTime > 0f ? ccTime / enemyTime : 0f;
            rep.SlowUptime = enemyTime > 0f ? slowTime / enemyTime : 0f;
            rep.AvgTimeToKill = ttkN > 0 ? ttkSum / ttkN : 0f;
            rep.HeroIdleShare = heroTime > 0f ? idleTime / heroTime : 0f;
            rep.Notes.Add("training.note.crystal_immortal");
            rep.Notes.Add("training.note.fixed_spawns");
            rep.Notes.Add("training.note.no_rewards");
            if (cfg.Profile == DummyProfile.Boss) rep.Notes.Add("training.note.boss_alone");
            if (cfg.Sandbox) rep.Notes.Add("training.note.sandbox");
            rep.Fingerprint = string.Join(",", rep.RawDps.ToString("F3"), rep.ReactionDps.ToString("F3"), rep.DotDps.ToString("F3"),
                rep.HealPerSecond.ToString("F3"), rep.Kills, rep.Reactions, rep.HardCcUptime.ToString("F4"), rep.AvgTimeToKill.ToString("F3"));
            return rep;
        }

        private static bool AllowedSecondsContains(float s)
        {
            foreach (float a in AllowedSeconds) if (Math.Abs(a - s) < 0.01f) return true;
            return false;
        }
    }
}
