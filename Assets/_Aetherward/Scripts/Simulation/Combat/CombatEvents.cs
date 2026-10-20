using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    public enum SimEventType
    {
        Hit,
        Heal,
        ShieldGain,
        Reaction,
        EnemyDeath,
        HeroDowned,
        HeroRevived,
        SkillCast,
        BasicAttack,
        CrystalHit,
        EnemySpawn,
        Telegraph,
        BossPhase,
        ZoneSpawn,
        Strike,        // delayed impact (meteor, spike, aftershock)
        StatusApplied,
        RelicProc,
        Taunt,
        Leak,
        Miss
    }

    public enum DamageKind
    {
        Basic,
        Skill,
        Reaction,
        Dot,
        Trigger,
        Enemy
    }

    /// <summary>
    /// One presentation-facing combat event. Plain struct in a reusable list, consumed each frame by
    /// the Unity view (VFX, floating text, audio) and by the results aggregator.
    /// </summary>
    public struct SimEvent
    {
        public SimEventType Type;
        public Vec2 Pos;
        public Vec2 From;
        public Element Element;
        public float Value;
        public float Radius;
        public bool Crit;
        public int SourceUid;
        public int TargetUid;
        public string Id;          // reaction id, skill kind, enemy id, relic id...
        public int Generation;
        public float Tick;
    }

    /// <summary>
    /// Bounded combat journal. Holds the events of the current frame for presentation plus rolling
    /// counters; never grows without bound in long waves.
    /// </summary>
    public sealed class CombatJournal
    {
        public const int MaxEventsPerFrame = 2048;
        public readonly List<SimEvent> Pending = new List<SimEvent>(256);
        public int Dropped;
        public bool Enabled = true;

        public void Emit(SimEvent e)
        {
            if (!Enabled) return;
            if (Pending.Count >= MaxEventsPerFrame)
            {
                Dropped++;
                return;
            }
            Pending.Add(e);
        }

        public void Clear() => Pending.Clear();
    }

    /// <summary>Per-battle aggregated statistics consumed by the run results.</summary>
    public sealed class BattleStats
    {
        /// <summary>Total distance walked by heroes (party liveliness benchmark).</summary>
        public float HeroTravel;
        /// <summary>Enemy hits on the Crystal and the damage they did.</summary>
        public int CrystalHits;
        public readonly Dictionary<string, int> ReactionCounts = new Dictionary<string, int>();
        public readonly Dictionary<string, float> ReactionDamage = new Dictionary<string, float>();
        public readonly Dictionary<string, int> SourceActivations = new Dictionary<string, int>();
        public readonly Dictionary<string, float> SourceDamage = new Dictionary<string, float>();
        public readonly float[] ElementDamage = new float[ElementUtil.Count];
        public readonly Dictionary<string, float> CrystalDamageByEnemy = new Dictionary<string, float>();
        /// <summary>Effective damage by kind (Basic/Skill/Reaction/Dot/Trigger/Enemy) — each hit counted once.</summary>
        public readonly float[] DamageByKind = new float[6];
        public float HeroShieldAbsorbed;
        /// <summary>Battle Insights evidence (P6): Crystal damage per lane, guardian collapse timing.</summary>
        public readonly Dictionary<int, float> CrystalDamageByLane = new Dictionary<int, float>();
        public string FirstGuardianDown;
        public float FirstGuardianDownTime = -1f;
        public float CrystalDamageAfterGuardianDown;
        public float EnemyAliveSeconds;
        public float EnemyHardCcSeconds;
        public int MaxProcDepth;
        public int Kills;
        public int Leaks;
        public int HeroDowns;
        public int PeakEnemies;
        public int PeakReactionsPerSecond;
        public int ReactionsBlockedByBudget;
        public int ReactionsBlockedByGeneration;
        public int StuckRecoveries;
        public int TimeoutBreaches;
        public float GoldFromKills;
        public int EssenceFromKills;
        public float Duration;

        public void AddReaction(string id, float damage)
        {
            ReactionCounts.TryGetValue(id, out int c);
            ReactionCounts[id] = c + 1;
            ReactionDamage.TryGetValue(id, out float d);
            ReactionDamage[id] = d + damage;
        }

        public void AddReactionDamage(string id, float damage)
        {
            ReactionDamage.TryGetValue(id, out float d);
            ReactionDamage[id] = d + damage;
        }

        public void AddSource(string sourceId, float damage)
        {
            if (string.IsNullOrEmpty(sourceId)) return;
            SourceActivations.TryGetValue(sourceId, out int c);
            SourceActivations[sourceId] = c + 1;
            if (damage > 0f)
            {
                SourceDamage.TryGetValue(sourceId, out float d);
                SourceDamage[sourceId] = d + damage;
            }
        }

        public void AddSourceDamage(string sourceId, float damage)
        {
            if (string.IsNullOrEmpty(sourceId) || damage <= 0f) return;
            SourceDamage.TryGetValue(sourceId, out float d);
            SourceDamage[sourceId] = d + damage;
        }

        public int TotalReactions
        {
            get
            {
                int t = 0;
                foreach (var kv in ReactionCounts) t += kv.Value;
                return t;
            }
        }
    }
}
