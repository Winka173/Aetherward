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
        Pact
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
        public readonly List<string> SeenEnemies = new List<string>();
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
