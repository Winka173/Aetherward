using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Run;

namespace Aetherward.Balance
{
    /// <summary>
    /// Deterministic balance lab (P9): playstyle bots × biomes × Ascension levels through the real simulation.
    /// Reports clear rates with Wilson CIs, 20-wave survival curves, loss waves, and anomaly detectors (dominant
    /// relics, trap cards, thin drafts, runaway reaction chains, excessive stuns, proc explosions) plus a knob
    /// sensitivity table. Bots are not players; every number states its sample size.
    /// Usage: --lab [--seeds 30] [--lab-asc 0,5,10] [--out DIR] [--no-sensitivity]
    /// </summary>
    public static class Lab
    {
        private static readonly (string label, string strategy, DraftPolicy policy)[] Bots =
        {
            ("mono_element", "mono_fire", DraftPolicy.Scripted),
            ("reaction_chain", "thunderstorm", DraftPolicy.Scripted),
            ("tank_healer_stall", "stall", DraftPolicy.Scripted),
            ("boss_burst", "boss_burst", DraftPolicy.Scripted),
            ("summon_proc", "summon_proc", DraftPolicy.Scripted),
            ("area_control", "frozen_fortress", DraftPolicy.Scripted),
            ("naive_random", "balanced", DraftPolicy.Random),
        };

        private sealed class Rec
        {
            public string Bot, Biome;
            public int Asc;
            public ulong Seed;
            public bool Win;
            public int Wave;
            public float MaxCcUptime;           // worst wave
            public int BudgetBlocked, GenerationBlocked, MaxProcDepth, PeakRps;
            public int DraftScreens, ThinDrafts;
            public readonly Dictionary<string, int> RelicAt = new Dictionary<string, int>();   // relic -> wave acquired
            public readonly Dictionary<string, int> CardAt = new Dictionary<string, int>();
        }

        public static int Run(ContentDatabase db, string root, string contentDir, string[] args)
        {
            int seeds = int.Parse(Arg(args, "--seeds", "30"), CultureInfo.InvariantCulture);
            int[] ascs = Arg(args, "--lab-asc", "0,5,10").Split(',').Select(s => int.Parse(s, CultureInfo.InvariantCulture)).ToArray();
            string outDir = Arg(args, "--out", Path.Combine(root, "Reports", "Balance", "lab"));
            Directory.CreateDirectory(outDir);
            var jobs = new List<(string bot, string strat, DraftPolicy pol, string biome, int asc, ulong seed)>();
            foreach (var b in Bots)
                foreach (BiomeDef bio in db.BiomeList)
                    foreach (int asc in ascs)
                        for (int i = 0; i < seeds; i++)
                            jobs.Add((b.label, b.strategy, b.policy, bio.Id, asc, (ulong)(5000 + i * 7919)));
            var sw = System.Diagnostics.Stopwatch.StartNew();
            var bag = new ConcurrentBag<Rec>();
            Parallel.ForEach(jobs, new ParallelOptions { MaxDegreeOfParallelism = Environment.ProcessorCount }, j =>
                bag.Add(Play(db, j.bot, j.strat, j.pol, j.biome, j.asc, j.seed)));
            var all = bag.OrderBy(r => r.Bot, StringComparer.Ordinal).ThenBy(r => r.Biome, StringComparer.Ordinal).ThenBy(r => r.Asc).ThenBy(r => r.Seed).ToList();
            sw.Stop();
            string sens = Array.IndexOf(args, "--no-sensitivity") >= 0 ? null : Sensitivity(contentDir, Math.Max(20, seeds));
            Write(db, contentDir, outDir, all, seeds, ascs, sw.Elapsed.TotalSeconds, sens);
            Console.WriteLine($"lab: {all.Count} runs in {sw.Elapsed.TotalSeconds:F1}s -> {outDir}");
            return 0;
        }

        private static Rec Play(ContentDatabase db, string bot, string strat, DraftPolicy pol, string biome, int asc, ulong seed)
        {
            Strategy st = Strategy.Find(strat).WithPolicy(pol);
            RunController rc = RunController.NewModeRun(db, GameMode.Classic, seed, st.Starters, asc, RunUnlocks.Everything(db), biome);
            var pilot = new AutoPilot(rc, st);
            var r = new Rec { Bot = bot, Biome = biome, Asc = asc, Seed = seed };
            for (int guard = 0; guard < 4000 && rc.State.Phase != RunPhase.Victory && rc.State.Phase != RunPhase.Defeat; guard++)
            {
                RunState s = rc.State;
                if (s.Phase == RunPhase.Battle)
                {
                    Battle b = rc.Battle;
                    b.RunToEnd();
                    BattleStats bs = b.Stats;
                    if (bs.EnemyAliveSeconds > 5f) r.MaxCcUptime = Math.Max(r.MaxCcUptime, bs.EnemyHardCcSeconds / bs.EnemyAliveSeconds);
                    r.BudgetBlocked += bs.ReactionsBlockedByBudget;
                    r.GenerationBlocked += bs.ReactionsBlockedByGeneration;
                    r.MaxProcDepth = Math.Max(r.MaxProcDepth, bs.MaxProcDepth);
                    r.PeakRps = Math.Max(r.PeakRps, bs.PeakReactionsPerSecond);
                    rc.ResolveBattle();
                    continue;
                }
                if (s.Phase == RunPhase.Reward && s.CurrentReward == RewardKind.Draft)
                {
                    r.DraftScreens++;
                    if (s.Offers.Count < 3) r.ThinDrafts++;
                }
                pilot.Step();
                foreach (string rel in rc.State.Relics) if (!r.RelicAt.ContainsKey(rel)) r.RelicAt[rel] = rc.State.Wave;
                foreach (string c in rc.State.CardOrder) if (!r.CardAt.ContainsKey(c)) r.CardAt[c] = rc.State.Wave;
            }
            r.Win = rc.State.Phase == RunPhase.Victory;
            r.Wave = r.Win ? 20 : rc.State.Wave;
            return r;
        }

        /// <summary>
        /// Lift of owning an item: P(win | acquired by wave w) vs P(win | reached wave w without it), pooled over
        /// acquisition waves. Comparing against runs that reached the same wave removes most survivor bias.
        /// </summary>
        private static List<(string id, int n, double withRate, double baseRate, double lift)> Lifts(List<Rec> all, Func<Rec, Dictionary<string, int>> pick)
        {
            var ids = new SortedSet<string>(StringComparer.Ordinal);
            foreach (Rec r in all) foreach (string k in pick(r).Keys) ids.Add(k);
            var outList = new List<(string, int, double, double, double)>();
            foreach (string id in ids)
            {
                var owners = all.Where(r => pick(r).ContainsKey(id)).ToList();
                if (owners.Count < 30) continue;
                double withRate = owners.Count(r => r.Win) / (double)owners.Count;
                // Baseline: for each owner's acquisition wave, runs alive at that wave without the item.
                double baseSum = 0;
                int baseN = 0;
                foreach (var grp in owners.GroupBy(r => pick(r)[id]))
                {
                    int w = grp.Key;
                    var others = all.Where(r => r.Wave >= w && !(pick(r).TryGetValue(id, out int ow) && ow <= w)).ToList();
                    if (others.Count == 0) continue;
                    baseSum += grp.Count() * (others.Count(r => r.Win) / (double)others.Count);
                    baseN += grp.Count();
                }
                double baseRate = baseN > 0 ? baseSum / baseN : 0;
                outList.Add((id, owners.Count, withRate, baseRate, baseRate > 0 ? withRate / baseRate : double.NaN));
            }
            return outList;
        }

        private static string Sensitivity(string contentDir, int seeds)
        {
            var knobs = new (string label, Action<ContentDatabase> apply)[]
            {
                ("baseline", d => { }),
                ("enemyHpGrowth ×0.9", d => d.Economy.EnemyHpGrowth *= 0.9f),
                ("enemyHpGrowth ×1.1", d => d.Economy.EnemyHpGrowth *= 1.1f),
                ("crystalHp ×0.9", d => d.Economy.CrystalHp = (int)(d.Economy.CrystalHp * 0.9f)),
                ("crystalHp ×1.1", d => d.Economy.CrystalHp = (int)(d.Economy.CrystalHp * 1.1f)),
            };
            var sb = new StringBuilder();
            sb.AppendLine("| Knob (economy.json) | reaction_chain win | tank_healer_stall win | Δ vs baseline (pp, mean of both) |");
            sb.AppendLine("|---|---|---|---|");
            double baseMean = 0;
            foreach (var k in knobs)
            {
                ContentDatabase d = ContentDatabase.Load(n => File.ReadAllText(Path.Combine(contentDir, n + ".json")));
                k.apply(d);
                var res = new ConcurrentBag<(string bot, bool win)>();
                var jobs = new List<(string bot, string strat, ulong seed)>();
                for (int i = 0; i < seeds; i++)
                {
                    jobs.Add(("reaction_chain", "thunderstorm", (ulong)(9000 + i * 7919)));
                    jobs.Add(("tank_healer_stall", "stall", (ulong)(9000 + i * 7919)));
                }
                Parallel.ForEach(jobs, j => res.Add((j.bot, Play(d, j.bot, j.strat, DraftPolicy.Scripted, d.DefaultBiome.Id, 0, j.seed).Win)));
                double a = res.Where(x => x.bot == "reaction_chain").Count(x => x.win) / (double)seeds;
                double b = res.Where(x => x.bot == "tank_healer_stall").Count(x => x.win) / (double)seeds;
                double mean = (a + b) / 2;
                if (k.label == "baseline") baseMean = mean;
                sb.AppendLine($"| {k.label} | {a * 100:F1}% | {b * 100:F1}% | {(k.label == "baseline" ? "—" : ((mean - baseMean) * 100).ToString("+0.0;-0.0", CultureInfo.InvariantCulture))} |");
            }
            sb.AppendLine();
            sb.AppendLine($"{seeds} paired seeds per bot per knob, default biome, Ascension 0. Small samples: treat deltas under ~10 pp as noise.");
            return sb.ToString();
        }

        private static void Write(ContentDatabase db, string contentDir, string outDir, List<Rec> all, int seeds, int[] ascs, double secs, string sens)
        {
            var csv = new StringBuilder("bot,biome,asc,seed,victory,wave,max_cc_uptime,budget_blocked,generation_blocked,max_proc_depth,peak_rps,draft_screens,thin_drafts\n");
            foreach (Rec r in all)
                csv.AppendLine(string.Join(",", r.Bot, r.Biome, r.Asc, r.Seed, r.Win ? 1 : 0, r.Wave, r.MaxCcUptime.ToString("F3", CultureInfo.InvariantCulture),
                    r.BudgetBlocked, r.GenerationBlocked, r.MaxProcDepth, r.PeakRps, r.DraftScreens, r.ThinDrafts));
            File.WriteAllText(Path.Combine(outDir, "runs.csv"), csv.ToString());

            var md = new StringBuilder();
            string[] bots = Bots.Select(b => b.label).ToArray();
            md.AppendLine("# Balance lab (playstyle bots × biomes × Ascension)");
            md.AppendLine();
            md.AppendLine("> Bots, not players. Seeds are paired across bots/biomes/ascensions. Lifts are associations, not causes.");
            md.AppendLine();
            md.AppendLine($"- Runs: **{all.Count}** = {Bots.Length} bots × {db.BiomeList.Count} biomes × {ascs.Length} Ascension levels × {seeds} seeds; {secs:F0}s on {Environment.ProcessorCount} threads ({Batch.CpuName()})");
            md.AppendLine($"- Content hash `{Batch.ContentHash(contentDir)}`; command `dotnet run --project Tools/SimHarness/Balance -c Release -- --lab --seeds {seeds}`");
            md.AppendLine("- Bot mapping: " + string.Join(", ", Bots.Select(b => $"{b.label} = {b.strategy}{(b.policy == DraftPolicy.Random ? " (random drafting)" : "")}")));
            md.AppendLine();
            md.AppendLine("## Clear rate by bot × Ascension (95% Wilson CI)");
            md.AppendLine("| Bot | " + string.Join(" | ", ascs.Select(a => "A" + a)) + " |");
            md.AppendLine("|---|" + string.Join("|", ascs.Select(_ => "---")) + "|");
            foreach (string b in bots)
                md.AppendLine($"| {b} | " + string.Join(" | ", ascs.Select(a => Rate(all.Where(r => r.Bot == b && r.Asc == a).ToList()))) + " |");
            md.AppendLine();
            md.AppendLine("## Clear rate by bot × biome (all Ascensions pooled)");
            md.AppendLine("| Bot | " + string.Join(" | ", db.BiomeList.Select(x => x.Id)) + " |");
            md.AppendLine("|---|" + string.Join("|", db.BiomeList.Select(_ => "---")) + "|");
            foreach (string b in bots)
                md.AppendLine($"| {b} | " + string.Join(" | ", db.BiomeList.Select(x => Rate(all.Where(r => r.Bot == b && r.Biome == x.Id).ToList()))) + " |");
            md.AppendLine();
            md.AppendLine("## 20-wave clear curve (share of runs alive at the start of the wave, A0 / A10)");
            int[] marks = { 5, 10, 14, 15, 18, 20 };
            md.AppendLine("| Bot | Asc | " + string.Join(" | ", marks.Select(w => "w" + w)) + " |");
            md.AppendLine("|---|---|" + string.Join("|", marks.Select(_ => "---")) + "|");
            var curve = new StringBuilder("bot,asc,wave,alive_share\n");
            foreach (string b in bots)
                foreach (int a in new[] { ascs.First(), ascs.Last() }.Distinct())
                {
                    var set = all.Where(r => r.Bot == b && r.Asc == a).ToList();
                    if (set.Count == 0) continue;
                    md.AppendLine($"| {b} | A{a} | " + string.Join(" | ", marks.Select(w => $"{100.0 * set.Count(r => r.Wave >= w) / set.Count:F0}%")) + " |");
                    for (int w = 1; w <= 20; w++) curve.AppendLine($"{b},{a},{w},{(set.Count(r => r.Wave >= w) / (double)set.Count).ToString("F4", CultureInfo.InvariantCulture)}");
                }
            File.WriteAllText(Path.Combine(outDir, "curves.csv"), curve.ToString());
            md.AppendLine();
            md.AppendLine("## Where runs end (defeat wave, all bots)");
            var losses = all.Where(r => !r.Win).GroupBy(r => r.Wave).OrderByDescending(g => g.Count()).Take(6);
            md.AppendLine("| Wave | Defeats | Share of defeats |");
            md.AppendLine("|---|---|---|");
            int nl = all.Count(r => !r.Win);
            foreach (var g in losses) md.AppendLine($"| {g.Key} | {g.Count()} | {100.0 * g.Count() / Math.Max(1, nl):F1}% |");
            md.AppendLine();

            md.AppendLine("## Anomaly detectors");
            var relics = Lifts(all, r => r.RelicAt).OrderByDescending(x => x.lift).ToList();
            var cards = Lifts(all, r => r.CardAt).OrderBy(x => x.lift).ToList();
            md.AppendLine("### Possibly dominant relics (win-rate lift ≥ 1.8 vs runs alive at the same wave without it, n ≥ 30)");
            var dom = relics.Where(x => x.lift >= 1.8).ToList();
            md.AppendLine(dom.Count == 0 ? "- none flagged" : string.Join("\n", dom.Take(10).Select(x => $"- `{x.id}`: n={x.n}, win {x.withRate * 100:F1}% vs {x.baseRate * 100:F1}% → lift {x.lift:F2}")));
            md.AppendLine("### Possible trap cards (lift ≤ 0.6, n ≥ 30)");
            var trap = cards.Where(x => x.lift <= 0.6).ToList();
            md.AppendLine(trap.Count == 0 ? "- none flagged" : string.Join("\n", trap.Take(10).Select(x => $"- `{x.id}`: n={x.n}, win {x.withRate * 100:F1}% vs {x.baseRate * 100:F1}% → lift {x.lift:F2}")));
            int screens = all.Sum(r => r.DraftScreens), thin = all.Sum(r => r.ThinDrafts);
            md.AppendLine($"### Empty/thin draft choices\n- {thin} of {screens} draft screens offered fewer than 3 cards ({100.0 * thin / Math.Max(1, screens):F2}%).");
            int budgetRuns = all.Count(r => r.BudgetBlocked > 0);
            md.AppendLine($"### Runaway reaction chains\n- Runs where the reaction budget had to block reactions: {budgetRuns} / {all.Count} ({100.0 * budgetRuns / all.Count:F1}%); max reactions/s seen: {all.Max(r => r.PeakRps)}; p95 {Percentile(all.Select(r => (double)r.PeakRps), 0.95):F0}.");
            int depthCap = all.Count(r => r.MaxProcDepth >= Battle.MaxProcGeneration);
            int genBlocked = all.Count(r => r.GenerationBlocked > 0);
            md.AppendLine($"### Proc explosions\n- Runs reaching the proc-generation cap ({Battle.MaxProcGeneration}): {depthCap}; runs where the cap blocked a reaction: {genBlocked} ({100.0 * genBlocked / all.Count:F1}%). The cap is the safety net; a high share means procs lean on it.");
            int stunRuns = all.Count(r => r.MaxCcUptime > 0.6f);
            md.AppendLine($"### Excessive stuns\n- Runs with a wave where enemies spent > 60% of their alive time hard-CC'd: {stunRuns} / {all.Count} ({100.0 * stunRuns / all.Count:F1}%). Per bot: " +
                string.Join(", ", bots.Select(b => $"{b} {100.0 * all.Count(r => r.Bot == b && r.MaxCcUptime > 0.6f) / Math.Max(1, all.Count(r => r.Bot == b)):F0}%")));
            md.AppendLine();
            md.AppendLine("Full relic/card lift tables: `relic_lift.csv`, `card_lift.csv`.");
            File.WriteAllText(Path.Combine(outDir, "relic_lift.csv"), "relic,n,win_with,win_baseline,lift\n" + string.Join("\n", relics.Select(x => $"{x.id},{x.n},{x.withRate:F4},{x.baseRate:F4},{x.lift:F3}")) + "\n");
            File.WriteAllText(Path.Combine(outDir, "card_lift.csv"), "card,n,win_with,win_baseline,lift\n" + string.Join("\n", cards.Select(x => $"{x.id},{x.n},{x.withRate:F4},{x.baseRate:F4},{x.lift:F3}")) + "\n");
            if (sens != null)
            {
                md.AppendLine();
                md.AppendLine("## Knob sensitivity (data in economy.json; paired seeds)");
                md.AppendLine(sens);
            }
            File.WriteAllText(Path.Combine(outDir, "summary.md"), md.ToString());
        }

        private static string Rate(List<Rec> set)
        {
            if (set.Count == 0) return "—";
            int w = set.Count(r => r.Win);
            var (lo, hi) = Batch.Wilson(w, set.Count);
            return $"{100.0 * w / set.Count:F1}% [{lo * 100:F0}–{hi * 100:F0}] n={set.Count}";
        }

        private static double Percentile(IEnumerable<double> xs, double p)
        {
            var l = xs.OrderBy(x => x).ToList();
            return l.Count == 0 ? 0 : l[Math.Min(l.Count - 1, (int)Math.Floor(p * l.Count))];
        }

        private static string Arg(string[] a, string k, string d)
        {
            int i = Array.IndexOf(a, k);
            return i >= 0 && i + 1 < a.Length ? a[i + 1] : d;
        }
    }
}
