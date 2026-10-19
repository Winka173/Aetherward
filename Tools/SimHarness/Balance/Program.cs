using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using Aetherward.Sim.Content;
using Aetherward.Sim.Run;

namespace Aetherward.Balance
{
    /// <summary>
    /// Headless balance simulator. Plays complete 20-wave runs with each archetype strategy across
    /// seeds and writes per-run CSV, per-wave CSV and a markdown summary.
    /// Usage: dotnet run --project Balance -- [--runs 20] [--strategy name|all] [--out dir] [--asc 0]
    /// </summary>
    public static class Program
    {
        public static int Main(string[] args)
        {
            int runs = 20;
            string strategyName = "all";
            string outDir = null;
            int ascension = 0;
            string biome = null;
            GameMode mode = GameMode.Classic;
            for (int i = 0; i < args.Length - 1; i++)
            {
                if (args[i] == "--runs") runs = int.Parse(args[i + 1]);
                if (args[i] == "--strategy") strategyName = args[i + 1];
                if (args[i] == "--out") outDir = args[i + 1];
                if (args[i] == "--asc") ascension = int.Parse(args[i + 1]);
                if (args[i] == "--biome") biome = args[i + 1];
                if (args[i] == "--mode") mode = (GameMode)Enum.Parse(typeof(GameMode), args[i + 1], true);
            }
            string root = FindRepoRoot();
            outDir ??= Path.Combine(root, "Docs", "Balance");
            Directory.CreateDirectory(outDir);
            string contentDir = Path.Combine(root, "Assets", "_Aetherward", "Resources", "Content");
            ContentDatabase db = ContentDatabase.Load(n => File.ReadAllText(Path.Combine(contentDir, n + ".json")));

            int snapWave = 0;
            float snapTime = 20f;
            for (int i = 0; i < args.Length - 1; i++)
            {
                if (args[i] == "--snapshot") snapWave = int.Parse(args[i + 1]);
                if (args[i] == "--time") snapTime = float.Parse(args[i + 1], CultureInfo.InvariantCulture);
            }
            if (Array.IndexOf(args, "--catalog") >= 0)
            {
                Catalog.Write(db, Path.Combine(root, "Docs", "CONTENT_CATALOG.md"));
                ReactionMatrix.Write(db, Path.Combine(root, "Docs", "Expansion", "ELEMENT_REACTION_MATRIX.md"));
                ExpansionDocs.Write(db, root);
                return 0;
            }
            if (Array.IndexOf(args, "--perf") >= 0)
            {
                Perf.Run(db, Path.Combine(outDir, "PERF.md"));
                return 0;
            }
            if (snapWave > 0)
            {
                Snapshot.Write(db, Strategy.Find(strategyName == "all" ? "thunderstorm" : strategyName), snapWave, snapTime,
                    Path.Combine(outDir, "snapshot_w" + snapWave + ".json"));
                return 0;
            }

            Strategy[] strategies = strategyName == "all" ? Strategy.Archetypes : new[] { Strategy.Find(strategyName) };
            var runCsv = new StringBuilder("strategy,seed,victory,wave,active_seconds,crystal_hp_pct,heroes,hero_downs,reactions,peak_enemies,peak_rps,gold_earned,gold_spent,relics,top_reaction,defeat_source,stuck_recoveries,ms,team\n");
            var waveCsv = new StringBuilder("strategy,seed,wave,duration,crystal_damage,crystal_hp_after,kills,leaks,reactions,hero_downs,gold,peak_enemies,peak_rps\n");
            var summary = new List<(string name, int wins, int n, double avgWave, double avgMinutes, double avgReactions, int peakEnemies, int peakRps, double avgMs, Dictionary<int, int> deaths)>();

            foreach (Strategy st in strategies)
            {
                int wins = 0;
                double waveSum = 0, secSum = 0, reactSum = 0, msSum = 0;
                int peakEnemies = 0, peakRps = 0;
                var deathWaves = new Dictionary<int, int>();
                for (int r = 0; r < runs; r++)
                {
                    ulong seed = 1000UL + (ulong)r * 7919UL;
                    var sw = Stopwatch.StartNew();
                    RunController rc = RunController.NewModeRun(db, mode, seed, st.Starters, ascension, Unlocks(db, args), biome, "20261019");
                    var pilot = new AutoPilot(rc, st);
                    bool ok = pilot.PlayToEnd();
                    sw.Stop();
                    if (!ok) Console.Error.WriteLine("STUCK: " + st.Name + " seed " + seed);
                    RunResults res = RunResults.Build(rc);
                    RunState s = rc.State;
                    int wave = res.Victory ? 20 : s.Wave;
                    if (res.Victory) wins++;
                    else { deathWaves.TryGetValue(wave, out int c); deathWaves[wave] = c + 1; }
                    waveSum += wave;
                    secSum += s.ActiveSeconds;
                    reactSum += res.TotalReactions;
                    msSum += sw.Elapsed.TotalMilliseconds;
                    int pe = s.WaveLog.Count > 0 ? s.WaveLog.Max(w => w.PeakEnemies) : 0;
                    int pr = s.WaveLog.Count > 0 ? s.WaveLog.Max(w => w.PeakReactionsPerSecond) : 0;
                    peakEnemies = Math.Max(peakEnemies, pe);
                    peakRps = Math.Max(peakRps, pr);
                    runCsv.AppendLine(string.Join(",", st.Name, seed, res.Victory ? 1 : 0, wave, F(s.ActiveSeconds), F(res.CrystalHpFraction * 100),
                        s.Heroes.Count, s.Heroes.Sum(h => h.TimesDowned), res.TotalReactions, pe, pr, F(s.GoldEarnedTotal), F(s.GoldSpentTotal),
                        "\"" + string.Join(" ", s.Relics) + "\"", res.StrongestReaction ?? "", res.DefeatSource ?? "", 0, F(sw.Elapsed.TotalMilliseconds),
                        "\"" + string.Join(" ", s.Heroes.Select(h => h.DefId + ":" + h.Level)) + "\""));
                    foreach (WaveRecord w in s.WaveLog)
                        waveCsv.AppendLine(string.Join(",", st.Name, seed, w.Wave, F(w.Duration), F(w.CrystalDamage), F(w.CrystalHpAfter), w.Kills, w.Leaks,
                            w.Reactions, w.HeroDowns, w.GoldEarned, w.PeakEnemies, w.PeakReactionsPerSecond));
                }
                summary.Add((st.Name, wins, runs, waveSum / runs, secSum / runs / 60.0, reactSum / runs, peakEnemies, peakRps, msSum / runs, deathWaves));
                Console.WriteLine($"{st.Name,-16} wins {wins}/{runs}  avgWave {waveSum / runs:0.0}  active {secSum / runs / 60.0:0.0} min  reactions {reactSum / runs:0}  peakEnemies {peakEnemies}  sim {msSum / runs:0} ms/run");
            }

            File.WriteAllText(Path.Combine(outDir, "runs.csv"), runCsv.ToString());
            File.WriteAllText(Path.Combine(outDir, "waves.csv"), waveCsv.ToString());
            var md = new StringBuilder();
            md.AppendLine("# Balance simulation summary");
            md.AppendLine();
            md.AppendLine($"Generated by `Tools/SimHarness/Balance` ({runs} seeded runs per strategy, ascension {ascension}, all content unlocked). Auto-pilot decisions are scripted heuristics, not human play.");
            md.AppendLine();
            md.AppendLine("| Strategy | Wins | Avg wave reached | Avg active combat (min) | Avg reactions/run | Peak enemies | Peak reactions/s | Deaths by wave |");
            md.AppendLine("|---|---|---|---|---|---|---|---|");
            foreach (var s in summary)
            {
                string deaths = string.Join(", ", s.deaths.OrderBy(k => k.Key).Select(k => "W" + k.Key + "×" + k.Value));
                md.AppendLine($"| {s.name} | {s.wins}/{s.n} | {s.avgWave:0.0} | {s.avgMinutes:0.0} | {s.avgReactions:0} | {s.peakEnemies} | {s.peakRps} | {deaths} |");
            }
            File.WriteAllText(Path.Combine(outDir, "SUMMARY.md"), md.ToString());
            Console.WriteLine("Wrote " + outDir);
            return 0;
        }

        private static string F(double v) => v.ToString("0.##", CultureInfo.InvariantCulture);

        private static string FindRepoRoot()
        {
            string dir = Directory.GetCurrentDirectory();
            while (dir != null && !Directory.Exists(Path.Combine(dir, "Assets", "_Aetherward"))) dir = Path.GetDirectoryName(dir);
            return dir ?? throw new DirectoryNotFoundException("repo root not found");
        }

        /// <summary>--launch-pool restricts offers to launch heroes/relics (diagnostic: isolates content dilution).</summary>
        private static RunUnlocks Unlocks(ContentDatabase db, string[] args)
        {
            RunUnlocks all = RunUnlocks.Everything(db);
            bool pool = Array.IndexOf(args, "--launch-pool") >= 0;
            if (pool || Array.IndexOf(args, "--launch-heroes") >= 0)
            {
                var launchHeroes = new[] { "ignis", "cinder", "marina", "tidal", "volt", "raiden", "freya", "glacius", "zephyr", "sylph", "terra", "magnus" };
                all.Heroes.Clear();
                foreach (string h in launchHeroes) all.Heroes.Add(h);
            }
            if (pool || Array.IndexOf(args, "--launch-relics") >= 0)
            {
                all.Relics.Clear();
                for (int i = 0; i < db.RelicList.Count && i < 28; i++) all.Relics.Add(db.RelicList[i].Id);
            }
            int ex = Array.IndexOf(args, "--exclude");
            if (ex >= 0 && ex + 1 < args.Length)
                foreach (string id in args[ex + 1].Split(','))
                {
                    all.Heroes.Remove(id);
                    all.Relics.Remove(id);
                }
            return all;
        }
    }
}
