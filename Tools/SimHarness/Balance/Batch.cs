using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using Aetherward.Sim.Run;

namespace Aetherward.Balance
{
    /// <summary>
    /// Phase 10 batch simulator: thousands of seeded runs through the game's own simulation, several
    /// draft policies, Wilson confidence intervals, outlier detection and run invariants. Writes
    /// Reports/Balance/{summary.md, runs.csv, heroes.csv, relics.csv, config.json}.
    /// Usage: --batch N [--policies scripted,synergy,random,greedy] [--strategy name] [--asc n] [--biome id] [--mode m] [--out dir]
    /// </summary>
    public static class Batch
    {
        private sealed class Rec
        {
            public string Strategy, Policy, Defeat;
            public ulong Seed;
            public bool Win, InvariantsOk;
            public int Wave, Reactions;
            public float Seconds, Gold;
            public string[] Heroes, Relics;
        }

        public static int Run(ContentDatabase db, string root, string contentDir, string[] args)
        {
            int n = int.Parse(Arg(args, "--batch", "1000"), CultureInfo.InvariantCulture);
            var policies = Arg(args, "--policies", "scripted,synergy,random,greedy").Split(',').Select(p => (DraftPolicy)Enum.Parse(typeof(DraftPolicy), p, true)).ToList();
            string only = Arg(args, "--strategy", null);
            int asc = int.Parse(Arg(args, "--asc", "0"), CultureInfo.InvariantCulture);
            string biome = Arg(args, "--biome", null);
            GameMode mode = (GameMode)Enum.Parse(typeof(GameMode), Arg(args, "--mode", "Classic"), true);
            string outDir = Arg(args, "--out", Path.Combine(root, "Reports", "Balance"));
            Directory.CreateDirectory(outDir);

            var strategies = Strategy.Archetypes.Where(s => only == null || s.Name == only).ToList();
            var jobs = new List<(Strategy st, int i)>();
            foreach (Strategy s in strategies)
                foreach (DraftPolicy p in policies)
                    for (int i = 0; i < n; i++) jobs.Add((s.WithPolicy(p), i));

            var recs = new ConcurrentBag<Rec>();
            var sw = Stopwatch.StartNew();
            int stuck = 0;
            Parallel.ForEach(jobs, new ParallelOptions { MaxDegreeOfParallelism = Environment.ProcessorCount }, job =>
            {
                ulong seed = 1000UL + (ulong)job.i * 7919UL;
                RunController rc = RunController.NewModeRun(db, mode, seed, job.st.Starters, asc, RunUnlocks.Everything(db), biome, "20261019");
                bool ok = new AutoPilot(rc, job.st).PlayToEnd();
                if (!ok) System.Threading.Interlocked.Increment(ref stuck);
                RunResults res = RunResults.Build(rc);
                RunState s = rc.State;
                recs.Add(new Rec
                {
                    Strategy = job.st.Name.Split('/')[0], Policy = job.st.Policy.ToString().ToLowerInvariant(), Seed = seed,
                    Win = res.Victory, Wave = res.Victory ? rc.TotalWaves : s.Wave, Reactions = res.TotalReactions, Seconds = s.ActiveSeconds,
                    Gold = s.GoldEarnedTotal, Defeat = res.DefeatSource ?? "",
                    Heroes = s.Heroes.Select(h => h.DefId).ToArray(), Relics = s.Relics.ToArray(),
                    InvariantsOk = ok && s.Gold >= 0 && !float.IsNaN(s.CrystalHp) && !float.IsInfinity(s.CrystalHp)
                                   && (s.Phase == RunPhase.Victory || s.Phase == RunPhase.Defeat)
                                   && s.Heroes.All(h => !float.IsNaN(h.HpFraction))
                });
            });
            sw.Stop();
            List<Rec> all = recs.OrderBy(r => r.Strategy).ThenBy(r => r.Policy).ThenBy(r => r.Seed).ToList();
            Write(db, contentDir, outDir, all, n, policies, asc, biome, mode, sw.Elapsed, stuck);
            Console.WriteLine("batch: " + all.Count + " runs in " + sw.Elapsed.TotalSeconds.ToString("F1", CultureInfo.InvariantCulture) + "s -> " + outDir);
            return all.Any(r => !r.InvariantsOk) ? 2 : 0;
        }

        // ------------------------------------------------------------------ report

        /// <summary>Wilson score interval (95%) for a binomial rate.</summary>
        public static (double lo, double hi) Wilson(int wins, int total)
        {
            if (total == 0) return (0, 0);
            const double z = 1.96;
            double p = (double)wins / total, d = 1 + z * z / total;
            double c = (p + z * z / (2 * total)) / d, m = z * Math.Sqrt(p * (1 - p) / total + z * z / (4.0 * total * total)) / d;
            return (Math.Max(0, c - m), Math.Min(1, c + m));
        }

        private static string Pct(int w, int t)
        {
            var (lo, hi) = Wilson(w, t);
            return string.Format(CultureInfo.InvariantCulture, "{0:F1}% [{1:F1}–{2:F1}]", t == 0 ? 0 : 100.0 * w / t, lo * 100, hi * 100);
        }

        private static void Write(ContentDatabase db, string contentDir, string outDir, List<Rec> all, int n, List<DraftPolicy> policies, int asc, string biome,
                                  GameMode mode, TimeSpan elapsed, int stuck)
        {
            var md = new StringBuilder();
            md.AppendLine("# Batch balance report (headless, authoritative simulation)");
            md.AppendLine();
            md.AppendLine("> AutoPilot policies are **bots, not players**: rates describe scripted/heuristic drafting, not human win rates.");
            md.AppendLine();
            string hash = ContentHash(contentDir);
            md.AppendLine($"- Runs: **{all.Count}** ({n} seeds × {all.Select(r => r.Strategy).Distinct().Count()} starting lineups × {policies.Count} policies), mode {mode}, Ascension {asc}, biome {biome ?? "default"}");
            md.AppendLine($"- Wall clock: {elapsed.TotalSeconds:F1}s on {Environment.ProcessorCount} threads ({CpuName()}), .NET {Environment.Version}");
            md.AppendLine($"- Content hash: `{hash}` · Unity editor not involved (pure C# simulation shared with the game)");
            int bad = all.Count(r => !r.InvariantsOk);
            md.AppendLine($"- Invariants (finished, no NaN, gold ≥ 0, exactly one outcome): **{(bad == 0 ? "all passed" : bad + " FAILED")}**; stuck runs: {stuck}");
            md.AppendLine();

            md.AppendLine("## Win rate by policy (95% Wilson CI)");
            md.AppendLine("| Policy | Runs | Win rate | Avg wave |");
            md.AppendLine("|---|---|---|---|");
            foreach (var g in all.GroupBy(r => r.Policy))
                md.AppendLine($"| {g.Key} | {g.Count()} | {Pct(g.Count(r => r.Win), g.Count())} | {g.Average(r => r.Wave):F1} |");
            md.AppendLine();
            md.AppendLine("## Win rate by starting lineup × policy");
            md.Append("| Lineup |");
            foreach (DraftPolicy p in policies) md.Append(" " + p.ToString().ToLowerInvariant() + " |");
            md.AppendLine();
            md.AppendLine("|---|" + string.Concat(policies.Select(_ => "---|")));
            foreach (var g in all.GroupBy(r => r.Strategy))
            {
                md.Append("| " + g.Key + " |");
                foreach (DraftPolicy p in policies)
                {
                    var pr = g.Where(r => r.Policy == p.ToString().ToLowerInvariant()).ToList();
                    md.Append(" " + Pct(pr.Count(r => r.Win), pr.Count) + " |");
                }
                md.AppendLine();
            }

            md.AppendLine();
            md.AppendLine("## Failure waves (share of all defeats)");
            var defeats = all.Where(r => !r.Win).ToList();
            md.AppendLine("| Wave | Defeats | Share | Top killers |");
            md.AppendLine("|---|---|---|---|");
            foreach (var g in defeats.GroupBy(r => r.Wave).OrderByDescending(g => g.Count()).Take(8))
                md.AppendLine($"| {g.Key} | {g.Count()} | {100.0 * g.Count() / Math.Max(1, defeats.Count):F1}% | {string.Join(", ", g.GroupBy(r => r.Defeat).OrderByDescending(x => x.Count()).Take(3).Select(x => x.Key + " " + x.Count()))} |");

            // Heroes and relics: presence vs win rate; outliers flagged with non-overlapping CIs.
            var heroRows = new StringBuilder("hero,runs,pick_rate,win_rate,win_lo,win_hi,win_without\n");
            var relicRows = new StringBuilder("relic,runs,pick_rate,win_rate,win_lo,win_hi,win_without\n");
            var flags = new List<string>();
            int total = all.Count, wins = all.Count(r => r.Win);
            foreach (HeroDef h in db.HeroList) Presence(h.Id, all.Where(r => r.Heroes.Contains(h.Id)).ToList(), total, wins, heroRows, flags, "hero");
            foreach (RelicDef rl in db.RelicList) Presence(rl.Id, all.Where(r => r.Relics.Contains(rl.Id)).ToList(), total, wins, relicRows, flags, "relic");
            foreach (var g in defeats.GroupBy(r => r.Wave))
                if (defeats.Count >= 50 && g.Count() > defeats.Count * 0.25) flags.Add($"spike: wave {g.Key} causes {100.0 * g.Count() / defeats.Count:F0}% of defeats");

            md.AppendLine();
            md.AppendLine("## Outlier flags (automatic; investigate, do not auto-nerf)");
            md.AppendLine("Rules: *must-pick candidate* = owned in ≥5% of runs and its win-rate CI lies entirely above the without-CI by ≥10 pp; *never viable* = in ≥30 runs with 0 wins; *spike* = one wave causes >25% of defeats. Presence correlates with drafting skill and run length (relics picked late appear in longer runs) — treat as leads, not verdicts.");
            md.AppendLine();
            if (flags.Count == 0) md.AppendLine("- none");
            foreach (string f in flags) md.AppendLine("- " + f);

            File.WriteAllText(Path.Combine(outDir, "summary.md"), md.ToString());
            File.WriteAllText(Path.Combine(outDir, "heroes.csv"), heroRows.ToString());
            File.WriteAllText(Path.Combine(outDir, "relics.csv"), relicRows.ToString());
            var runs = new StringBuilder("strategy,policy,seed,victory,wave,reactions,active_seconds,gold_earned,defeat_source,invariants_ok,heroes,relics\n");
            foreach (Rec r in all)
                runs.AppendLine(string.Join(",", r.Strategy, r.Policy, r.Seed, r.Win ? 1 : 0, r.Wave, r.Reactions, r.Seconds.ToString("F1", CultureInfo.InvariantCulture),
                    r.Gold.ToString("F0", CultureInfo.InvariantCulture), r.Defeat, r.InvariantsOk ? 1 : 0, string.Join(" ", r.Heroes), string.Join(" ", r.Relics)));
            File.WriteAllText(Path.Combine(outDir, "runs.csv"), runs.ToString());
            File.WriteAllText(Path.Combine(outDir, "config.json"), "{\n  \"seeds\": " + n + ",\n  \"policies\": \"" + string.Join(",", policies) + "\",\n  \"mode\": \"" + mode +
                "\",\n  \"ascension\": " + asc + ",\n  \"biome\": \"" + (biome ?? "default") + "\",\n  \"crystalEvolution\": " + (Aetherward.Sim.Run.FeatureFlags.CrystalEvolution ? "true" : "false") + ",\n  \"utilityTargeting\": " + (Aetherward.Sim.Run.FeatureFlags.UtilityTargeting ? "true" : "false") + ",\n  \"contentHash\": \"" + hash + "\",\n  \"runs\": " + all.Count +
                ",\n  \"seconds\": " + elapsed.TotalSeconds.ToString("F1", CultureInfo.InvariantCulture) + ",\n  \"threads\": " + Environment.ProcessorCount + "\n}\n");
        }

        private static void Presence(string id, List<Rec> with, int total, int wins, StringBuilder rows, List<string> flags, string kind)
        {
            int ww = with.Count(r => r.Win), wn = with.Count, ow = wins - ww, on = total - wn;
            var (lo, hi) = Wilson(ww, wn);
            var (olo, ohi) = Wilson(ow, on);
            rows.AppendLine(string.Join(",", id, wn, (100.0 * wn / Math.Max(1, total)).ToString("F1", CultureInfo.InvariantCulture),
                (wn == 0 ? 0 : 100.0 * ww / wn).ToString("F1", CultureInfo.InvariantCulture), (lo * 100).ToString("F1", CultureInfo.InvariantCulture),
                (hi * 100).ToString("F1", CultureInfo.InvariantCulture), (on == 0 ? 0 : 100.0 * ow / on).ToString("F1", CultureInfo.InvariantCulture)));
            if (wn >= total * 0.05 && lo > ohi && (double)ww / wn - (double)ow / Math.Max(1, on) >= 0.10)
                flags.Add($"must-pick candidate ({kind}): {id} — {Pct(ww, wn)} with vs {Pct(ow, on)} without");
            if (wn >= 30 && ww == 0) flags.Add($"never viable ({kind}): {id} — 0 wins in {wn} runs");
        }

        private static string ContentHash(string dir)
        {
            var sb = new StringBuilder();
            foreach (string f in Directory.GetFiles(dir, "*.json").OrderBy(f => f, StringComparer.Ordinal)) sb.Append(File.ReadAllText(f));
            return Pcg32.Hash64(sb.ToString()).ToString("x16");
        }

        private static string CpuName()
        {
            try
            {
                foreach (string l in File.ReadLines("/proc/cpuinfo")) if (l.StartsWith("model name")) return l.Split(':')[1].Trim();
            }
            catch (Exception) { }
            return "unknown CPU";
        }

        private static string Arg(string[] args, string key, string def)
        {
            int i = Array.IndexOf(args, key);
            return i >= 0 && i + 1 < args.Length ? args[i + 1] : def;
        }
    }
}
