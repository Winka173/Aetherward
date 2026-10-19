using System.Collections.Generic;
using Aetherward.Sim.Content;

namespace Aetherward.Sim.Run
{
    public enum RunPhase
    {
        Prepare,
        Battle,
        Reward,
        Victory,
        Defeat
    }

    /// <summary>A hero owned in the current run (run-local level/XP/evolution; reset at run end).</summary>
    public sealed class HeroRunState
    {
        public int Uid;
        public string DefId;
        public int Level = 1;
        public int Xp;
        public string EvolutionId;
        public float HpFraction = 1f;
        public bool Downed;
        public int Node = -1;
        public int JoinedWave = 1;
        public string TraitId;            // rolled on recruitment; null for starters
        public string Awakened;           // Elemental Awakening: secondary element key (run-only), null if none
        // Lifetime totals for the results screen.
        public float DamageDealt;
        public float HealingDone;
        public float DamageTaken;
        public int Kills;
        public int Reactions;
        public int SkillCasts;
        public int TimesDowned;
    }

    public enum OfferKind
    {
        Card,
        Hero,
        Relic,
        Repair,
        Revive,
        Evolution,
        EventOption,
        Pact,
        CrystalPath
    }

    /// <summary>One selectable item on a reward/shop screen.</summary>
    public sealed class Offer
    {
        public OfferKind Kind;
        public string Id;          // card/hero/relic/evolution/event id
        public int Price;          // 0 = free choice
        public int HeroUid;        // for revive/evolution
        public int OptionIndex;    // for events
        public bool Sold;
        public string Tag;         // "synergy", "pivot", "new", ... for UI hints
        public string TraitId;     // hero offers: the trait this recruit comes with
    }

    /// <summary>Per-wave record for the post-run report.</summary>
    public sealed class WaveRecord
    {
        public int Wave;
        public float Duration;
        public float CrystalDamage;
        public float CrystalHpAfter;
        public int Kills;
        public int Leaks;
        public int Reactions;
        public int HeroDowns;
        public int GoldEarned;
        public int PeakEnemies;
        public int PeakReactionsPerSecond;
        public bool Cleared;
    }

    /// <summary>
    /// Complete state of a run. Plain data so it can be saved between waves and restored exactly
    /// (resume never restores mid-combat projectiles; it restarts at the wave boundary).
    /// </summary>
    /// <summary>Run modes. Classic = 20 authored waves; Endless loops 11–20 with rising scale; Daily = a
    /// date-seeded Classic run with daily modifiers; Boss Rush = every boss in sequence.</summary>
    public enum GameMode
    {
        Classic,
        Endless,
        Daily,
        BossRush
    }

    public sealed class RunState
    {
        public const int SaveVersion = 2;

        public ulong Seed;
        public string GameVersion = "0.1.0";
        public int Ascension;
        public int Wave = 1;               // next wave to fight (or the one being fought)
        public RunPhase Phase = RunPhase.Prepare;
        public int Gold;
        public int Essence;
        public float CrystalHp;
        public float CrystalBaseMaxHp;
        public float CrystalKnownMax;      // max HP when last adjusted (for relic/pact deltas)
        public int NextHeroUid = 1;
        public readonly List<HeroRunState> Heroes = new List<HeroRunState>();
        public readonly List<string> Relics = new List<string>();
        public readonly Dictionary<string, int> Cards = new Dictionary<string, int>();
        public readonly List<string> CardOrder = new List<string>();
        public readonly List<string> Pacts = new List<string>();
        public readonly List<string> NextWaveModifiers = new List<string>();
        public readonly List<RewardKind> PendingRewards = new List<RewardKind>();
        public RewardKind CurrentReward;
        public readonly List<Offer> Offers = new List<Offer>();
        public string CurrentEventId;
        public int RerollsThisScreen;
        public int TotalRerolls;
        public int FreeRerollsLeft;
        public float ActiveSeconds;
        public float GoldEarnedTotal;
        public float GoldSpentTotal;
        public readonly List<WaveRecord> WaveLog = new List<WaveRecord>();
        public readonly Dictionary<string, int> ReactionCounts = new Dictionary<string, int>();
        public readonly Dictionary<string, float> ReactionDamage = new Dictionary<string, float>();
        public readonly Dictionary<string, int> SourceActivations = new Dictionary<string, int>();
        public readonly Dictionary<string, float> SourceDamage = new Dictionary<string, float>();
        public readonly float[] ElementDamage = new float[ElementUtil.Count];
        public readonly float[] DamageByKind = new float[6];
        public float ShieldAbsorbed;
        public int MaxProcDepth;
        public readonly Dictionary<string, float> CrystalDamageByEnemy = new Dictionary<string, float>();
        public readonly List<string> SeenEnemies = new List<string>();
        /// <summary>Boss chosen for each wave that has a boss pool (deterministic per seed, saved).</summary>
        public readonly Dictionary<int, string> BossChoices = new Dictionary<int, string>();
        /// <summary>Ascension "blocked_node": a defense node unusable for the current wave (-1 = none).</summary>
        public int BlockedNode = -1;
        /// <summary>Battlefield of this run (null = default biome; unknown ids degrade to default).</summary>
        public string BiomeId;
        public GameMode Mode;
        public Combat.TeamTactic Tactic;
        public string CrystalPath;                                    // Crystal Evolution choice (null = not chosen)
        public bool CrystalEvolutionEnabled = FeatureFlags.CrystalEvolution;
        /// <summary>Optional shop lock: one hero/relic/card offer carried into the next shop at its price.</summary>
        public Offer LockedOffer;
        /// <summary>Real seconds spent outside combat (prepare/reward screens), measured by the client.</summary>
        public float MenuSeconds;
        /// <summary>Per-run offer pools (empty = everything unlocked). Drawn once at run start, saved.</summary>
        public readonly List<string> HeroPool = new List<string>();
        public readonly List<string> RelicPool = new List<string>();
        public string DailyKey;                 // yyyymmdd for Daily runs
        public readonly List<string> ModeModifiers = new List<string>(); // applied to every wave (Daily)
        public string DefeatSource;
        public int DraftsTaken;
        public readonly List<string> Log = new List<string>(); // selection trace (debug, bounded)

        public bool Finished => Phase == RunPhase.Victory || Phase == RunPhase.Defeat;

        public HeroRunState Hero(int uid)
        {
            for (int i = 0; i < Heroes.Count; i++) if (Heroes[i].Uid == uid) return Heroes[i];
            return null;
        }

        public HeroRunState HeroOnNode(int node)
        {
            for (int i = 0; i < Heroes.Count; i++) if (Heroes[i].Node == node) return Heroes[i];
            return null;
        }

        public bool HasHero(string defId)
        {
            for (int i = 0; i < Heroes.Count; i++) if (Heroes[i].DefId == defId) return true;
            return false;
        }

        public int CardStacks(string id) => Cards.TryGetValue(id, out int n) ? n : 0;

        public void Trace(string line)
        {
            Log.Add(line);
            if (Log.Count > 400) Log.RemoveAt(0);
        }
    }
}
