using System.Collections.Generic;
using Aetherward.Sim.Run;

namespace Aetherward.Sim.Meta
{
    /// <summary>Snapshot of a winning team, kept in the Discovery Codex (P5) with its replayable share code.</summary>
    public sealed class FormationSnapshot
    {
        public string Seed;
        public string Mode;
        public int Ascension;
        public string ShareCode;
        public long UnixTime;
        public readonly List<string> Heroes = new List<string>();   // "heroId@node:evolutionId"
        public readonly List<string> Relics = new List<string>();
    }

    /// <summary>
    /// Lightweight, non-pausing milestone detection for the battle view (P5). It only reports "this is new";
    /// persistence happens in MetaProfile.RecordRun at run end, so quitting mid-run never half-records progress.
    /// Each milestone is announced at most once per run.
    /// </summary>
    public sealed class DiscoveryTracker
    {
        private readonly MetaProfile _meta;
        private readonly HashSet<string> _announced = new HashSet<string>();

        public DiscoveryTracker(MetaProfile meta) => _meta = meta;

        private string Once(string key) => _announced.Add(key) ? key : null;

        /// <returns>"reaction:&lt;id&gt;" the first time a reaction never seen in any run fires, else null.</returns>
        public string OnReaction(string id) => _meta == null || _meta.Codex.Contains("reaction:" + id) ? null : Once("reaction:" + id);

        public string OnEvolution(string evolutionId) => _meta == null || _meta.Codex.Contains("evolution:" + evolutionId) ? null : Once("evolution:" + evolutionId);

        public string OnFusion(string relicId) => _meta == null || _meta.Codex.Contains("fusion:" + relicId) ? null : Once("fusion:" + relicId);

        /// <summary>New personal best for reactions in one second (announced once per run, the first time it is beaten).</summary>
        public string OnPeakChain(int reactionsPerSecond) =>
            _meta != null && reactionsPerSecond > _meta.BestReactionsPerSecond && reactionsPerSecond >= 3 ? Once("best_chain") : null;
    }

    public static class Milestones
    {
        public const int MaxFormations = 20;

        /// <summary>Milestone ids earned by a finished run (also written into MetaProfile.Milestones).</summary>
        public static List<string> Evaluate(MetaProfile m, RunController rc, RunResults r)
        {
            var earned = new List<string>();
            void Earn(string id)
            {
                if (m.Milestones.Add(id)) earned.Add(id);
            }
            RunState s = rc.State;
            foreach (HeroRunState h in s.Heroes) if (!string.IsNullOrEmpty(h.EvolutionId)) Earn("first_evolution");
            foreach (string relic in s.Relics)
                if (rc.Content.Relics.TryGetValue(relic, out var def) && def.Fusion) Earn("first_fusion");
            if (r.TotalReactions >= 100) Earn("reactions_100_in_run");
            if (s.ReactionCounts.Count >= 10) Earn("ten_reactions_in_run");
            if (r.Victory) Earn("first_victory");
            if (r.Victory && s.Ascension >= 5) Earn("victory_ascension_5");
            int peak = 0;
            foreach (WaveRecord w in s.WaveLog) if (w.PeakReactionsPerSecond > peak) peak = w.PeakReactionsPerSecond;
            if (peak > m.BestReactionsPerSecond)
            {
                m.BestReactionsPerSecond = peak;
                if (peak >= 3) earned.Add("best_chain:" + peak);
            }
            return earned;
        }

        public static FormationSnapshot Snapshot(RunController rc, RunResults r, long unixTime)
        {
            var f = new FormationSnapshot { Seed = r.Seed, Mode = rc.State.Mode.ToString(), Ascension = rc.State.Ascension, ShareCode = r.ShareCode, UnixTime = unixTime };
            foreach (HeroRunState h in rc.State.Heroes) f.Heroes.Add(h.DefId + "@" + h.Node + (string.IsNullOrEmpty(h.EvolutionId) ? "" : ":" + h.EvolutionId));
            f.Relics.AddRange(rc.State.Relics);
            return f;
        }
    }
}
