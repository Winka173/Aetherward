using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Run;

namespace Aetherward.Balance
{
    /// <summary>
    /// Simulation cost probe: six late-game heroes against the heaviest waves, timing every tick.
    /// Desktop .NET JIT numbers; IL2CPP on mobile is typically several times slower, so the budget
    /// check uses a 10x safety factor against a 16.6 ms frame at 2x speed (2 ticks per frame).
    /// </summary>
    public static class Perf
    {
        public static void Run(ContentDatabase db, string path)
        {
            var sb = new StringBuilder("# Simulation performance probe\n\n");
            sb.AppendLine("Six level-5 heroes with mixed elements, desktop .NET 8 (JIT), single thread. Not a device measurement.\n");
            sb.AppendLine("| Wave | Ticks | Peak enemies | Avg µs/tick | Max µs/tick | Max reactions/s |");
            sb.AppendLine("|---|---|---|---|---|---|");
            string[] heroes = { "ignis", "volt", "marina", "terra", "zephyr", "freya" };
            int[] nodes = { 4, 8, 6, 0, 10, 2 };
            foreach (int wave in new[] { 11, 14, 18, 19, 20 })
            {
                var setup = new BattleSetup { Content = db, Wave = db.Waves[wave - 1], Seed = 99, CrystalHp = 1e6f, CrystalMaxHp = 1e6f };
                for (int i = 0; i < heroes.Length; i++)
                    setup.Heroes.Add(new HeroLoadout { Def = db.Heroes[heroes[i]], NodeIndex = nodes[i], RosterIndex = i, Level = 5 });
                var b = new Battle(setup);
                // warm-up JIT on a throwaway battle
                var warm = new Battle(setup);
                for (int i = 0; i < 300; i++) { warm.Tick(); warm.Journal.Clear(); }
                var sw = new Stopwatch();
                double max = 0, total = 0;
                int ticks = 0;
                while (b.Outcome == BattleOutcome.Running && b.Time < 300f)
                {
                    sw.Restart();
                    b.Tick();
                    sw.Stop();
                    b.Journal.Clear();
                    double us = sw.Elapsed.TotalMilliseconds * 1000.0;
                    total += us;
                    if (us > max) max = us;
                    ticks++;
                }
                sb.AppendLine($"| {wave} | {ticks} | {b.Stats.PeakEnemies} | {total / Math.Max(1, ticks):0.0} | {max:0} | {b.Stats.PeakReactionsPerSecond} |");
            }
            File.WriteAllText(path, sb.ToString());
            Console.WriteLine(sb.ToString());
        }
    }
}
