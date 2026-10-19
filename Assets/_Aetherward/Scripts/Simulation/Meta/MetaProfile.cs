using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Run;

namespace Aetherward.Sim.Meta
{
    public sealed class RunHistoryEntry
    {
        public string Seed;
        public string Version;
        public bool Victory;
        public int Wave;
        public int Ascension;
        public float Seconds;
        public int Reactions;
        public string StrongestReaction;
        public string DefeatSource;
        public string Mvp;
        public readonly List<string> Heroes = new List<string>();
        public readonly List<string> Relics = new List<string>();
        public readonly List<float> CrystalTimeline = new List<float>();
        public long UnixTime;
    }

    public sealed class UnlockRule
    {
        public string Id;          // content id unlocked (hero:x / relic:y / biome:z)
        public string Condition;   // reach_wave | total_reactions | distinct_reactions | defeat_boss | victory | hero_runs
        public int Value;
        public string Param;
    }

    /// <summary>
    /// Persistent profile. Unlocks variety only (heroes, relics, ascension, codex, cosmetics);
    /// never permanent combat stats.
    /// </summary>
    public sealed class MetaProfile
    {
        public const int MaxHistory = 30;

        public readonly HashSet<string> UnlockedHeroes = new HashSet<string>();
        public readonly HashSet<string> UnlockedRelics = new HashSet<string>();
        public readonly HashSet<string> UnlockedBiomes = new HashSet<string>();
        public readonly HashSet<string> Codex = new HashSet<string>();   // "reaction:x", "hero:y", "enemy:z", "relic:r", "fusion:f"
        public readonly Dictionary<string, int> HeroRuns = new Dictionary<string, int>();
        public readonly Dictionary<string, int> HeroWins = new Dictionary<string, int>();
        public readonly List<RunHistoryEntry> History = new List<RunHistoryEntry>();
        public int TotalRuns;
        public int Victories;
        public int BestWave;
        public int TotalReactions;
        public int MaxAscensionUnlocked;
        public bool TutorialDone;

        public static readonly UnlockRule[] Rules =
        {
            new UnlockRule { Id = "hero:raiden", Condition = "reach_wave", Value = 6 },
            new UnlockRule { Id = "hero:tidal", Condition = "total_reactions", Value = 60 },
            new UnlockRule { Id = "hero:glacius", Condition = "reach_wave", Value = 10 },
            new UnlockRule { Id = "hero:zephyr", Condition = "distinct_reactions", Value = 8 },
            new UnlockRule { Id = "hero:magnus", Condition = "defeat_boss", Param = "siegebreaker_golem" },
            new UnlockRule { Id = "relic:arcane_echo", Condition = "reach_wave", Value = 8 },
            new UnlockRule { Id = "relic:glass_cannon", Condition = "hero_runs", Value = 3 },
            new UnlockRule { Id = "relic:phoenix_feather", Condition = "reach_wave", Value = 15 },
            new UnlockRule { Id = "relic:elemental_mirror", Condition = "distinct_reactions", Value = 12 },
            // Expansion Phase 1
            new UnlockRule { Id = "hero:seren", Condition = "reach_wave", Value = 4 },
            new UnlockRule { Id = "hero:nyxara", Condition = "distinct_reactions", Value = 5 },
            new UnlockRule { Id = "hero:ashara", Condition = "hero_runs", Value = 2 },
            new UnlockRule { Id = "hero:nerissa", Condition = "total_reactions", Value = 120 },
            new UnlockRule { Id = "hero:voltrix", Condition = "reach_wave", Value = 8 },
            new UnlockRule { Id = "hero:eirwen", Condition = "reach_wave", Value = 12 },
            new UnlockRule { Id = "hero:kael", Condition = "distinct_reactions", Value = 10 },
            new UnlockRule { Id = "hero:borun", Condition = "reach_wave", Value = 14 },
            new UnlockRule { Id = "relic:verdict_scale", Condition = "distinct_reactions", Value = 15 },
            new UnlockRule { Id = "relic:radiant_lens", Condition = "reach_wave", Value = 18 },
            new UnlockRule { Id = "relic:shadow_contract", Condition = "defeat_boss", Param = "ignaroth" },
            new UnlockRule { Id = "relic:eclipse_engine", Condition = "victory", Value = 1 },
            // Expansion Phase 2: battlefields
            new UnlockRule { Id = "biome:molten_crater", Condition = "reach_wave", Value = 7 },
            new UnlockRule { Id = "biome:frostfall_bastion", Condition = "reach_wave", Value = 11 }
        };

        /// <summary>Highest Ascension that can be unlocked (data: difficulty.json).</summary>
        public static int MaxAscension = 5;

        public static MetaProfile CreateDefault(ContentDatabase db)
        {
            var m = new MetaProfile();
            foreach (HeroDef h in db.HeroList) if (h.StarterUnlocked) m.UnlockedHeroes.Add(h.Id);
            foreach (RelicDef r in db.RelicList) if (r.StarterUnlocked && !r.Fusion) m.UnlockedRelics.Add(r.Id);
            m.UnlockedBiomes.Add(db.DefaultBiome.Id);
            return m;
        }

        public RunUnlocks ToRunUnlocks()
        {
            var u = new RunUnlocks();
            foreach (string h in UnlockedHeroes) u.Heroes.Add(h);
            foreach (string r in UnlockedRelics) u.Relics.Add(r);
            return u;
        }

        public int DistinctReactionsSeen
        {
            get
            {
                int n = 0;
                foreach (string c in Codex) if (c.StartsWith("reaction:")) n++;
                return n;
            }
        }

        /// <summary>Records a finished run; returns newly unlocked content ids for the results screen.</summary>
        public List<string> RecordRun(RunController rc, RunResults results, long unixTime)
        {
            RunState s = rc.State;
            TotalRuns++;
            if (results.Victory)
            {
                Victories++;
                int cap = System.Math.Max(MaxAscension, rc.Content.Difficulty.MaxLevel);
                if (MaxAscensionUnlocked <= s.Ascension && s.Ascension < cap) MaxAscensionUnlocked = s.Ascension + 1;
            }
            int reached = results.Victory ? rc.Content.Waves.Count : s.Wave;
            if (reached > BestWave) BestWave = reached;
            TotalReactions += results.TotalReactions;
            foreach (var kv in s.ReactionCounts) Codex.Add("reaction:" + kv.Key);
            foreach (HeroRunState h in s.Heroes)
            {
                Codex.Add("hero:" + h.DefId);
                if (!string.IsNullOrEmpty(h.EvolutionId)) Codex.Add("evolution:" + h.EvolutionId);
                HeroRuns.TryGetValue(h.DefId, out int runs);
                HeroRuns[h.DefId] = runs + 1;
                if (results.Victory)
                {
                    HeroWins.TryGetValue(h.DefId, out int wins);
                    HeroWins[h.DefId] = wins + 1;
                }
            }
            foreach (string r in s.Relics)
            {
                Codex.Add("relic:" + r);
                if (rc.Content.Relics.TryGetValue(r, out RelicDef def) && def.Fusion) Codex.Add("fusion:" + r);
            }
            foreach (string e in s.SeenEnemies) if (!e.StartsWith("hero:")) Codex.Add("enemy:" + e);

            var entry = new RunHistoryEntry
            {
                Seed = results.Seed,
                Version = results.GameVersion,
                Victory = results.Victory,
                Wave = reached,
                Ascension = s.Ascension,
                Seconds = results.ActiveSeconds,
                Reactions = results.TotalReactions,
                StrongestReaction = results.StrongestReaction,
                DefeatSource = results.DefeatSource,
                Mvp = results.MvpHero,
                UnixTime = unixTime
            };
            foreach (HeroRunState h in s.Heroes) entry.Heroes.Add(h.DefId);
            entry.Relics.AddRange(s.Relics);
            foreach (WaveRecord w in s.WaveLog) entry.CrystalTimeline.Add(w.CrystalHpAfter);
            History.Insert(0, entry);
            while (History.Count > MaxHistory) History.RemoveAt(History.Count - 1);

            // Every boss actually fought and beaten this run (boss pools resolved per seed).
            foreach (WaveRecord w in s.WaveLog)
            {
                if (!w.Cleared || w.Wave < 1 || w.Wave > rc.Content.Waves.Count) continue;
                WaveDef wd = rc.Content.Waves[w.Wave - 1];
                if (!wd.Boss) continue;
                foreach (SpawnGroup g in wd.Groups)
                {
                    string id = rc.EnemyFor(wd, g.Enemy);
                    if (rc.Content.Enemies.TryGetValue(id, out EnemyDef ed) && ed.Boss) Codex.Add("defeated:" + id);
                }
            }

            var unlocked = new List<string>();
            foreach (UnlockRule rule in Rules)
            {
                if (SetFor(rule.Id, out string key).Contains(key)) continue;
                bool met;
                switch (rule.Condition)
                {
                    case "reach_wave": met = BestWave >= rule.Value; break;
                    case "total_reactions": met = TotalReactions >= rule.Value; break;
                    case "distinct_reactions": met = DistinctReactionsSeen >= rule.Value; break;
                    case "defeat_boss": met = Codex.Contains("defeated:" + rule.Param); break;
                    case "hero_runs": met = TotalRuns >= rule.Value; break;
                    case "victory": met = Victories > 0; break;
                    default: met = false; break;
                }
                if (!met) continue;
                SetFor(rule.Id, out key).Add(key);
                unlocked.Add(rule.Id);
            }
            return unlocked;
        }

        /// <summary>Unlock set for a rule id ("hero:x", "relic:y", "biome:z") and the bare content id.</summary>
        private HashSet<string> SetFor(string ruleId, out string key)
        {
            int colon = ruleId.IndexOf(':');
            key = ruleId.Substring(colon + 1);
            switch (ruleId.Substring(0, colon))
            {
                case "hero": return UnlockedHeroes;
                case "biome": return UnlockedBiomes;
                default: return UnlockedRelics;
            }
        }
    }
}
