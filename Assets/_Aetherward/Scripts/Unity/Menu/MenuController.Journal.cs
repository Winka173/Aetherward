using Aetherward.Sim.Meta;
using UnityEngine;

namespace Aetherward.Game
{
    /// <summary>Discovery Codex journal (P5): milestones (unearned ones stay hidden), best chain, winning formations.</summary>
    public sealed partial class MenuController
    {
        private static readonly string[] JournalMilestones =
            { "first_evolution", "first_fusion", "ten_reactions_in_run", "reactions_100_in_run", "first_victory", "victory_ascension_5" };

        private void DrawJournal()
        {
            var l = App.Loc;
            MetaProfile m = App.Meta;
            float x = 60, y = 210, w = Ui.W / 2 - 90;
            Ui.Panel(x, y, w, 640);
            Ui.Label(x + 24, y + 16, w - 48, 40, l.Get("codex.milestones"), 28, Ui.Gold, TextAnchor.UpperLeft, true);
            float yy = y + 66;
            foreach (string id in JournalMilestones)
            {
                bool got = m.Milestones.Contains(id);
                Ui.Label(x + 24, yy, w - 48, 34, (got ? "★ " : "☆ ") + (got ? l.Get("milestone." + id) : l.Get("codex.undiscovered")), 22, got ? Ui.White : Ui.Muted);
                yy += 40;
            }
            Ui.Label(x + 24, yy + 10, w - 48, 34, l.Format("codex.best_chain", m.BestReactionsPerSecond), 22, Ui.White);
            Ui.Label(x + 24, yy + 50, w - 48, 34, l.Format("codex.discovered", m.Codex.Count), 22, Ui.Muted);

            float fx = Ui.W / 2 + 30, fw = Ui.W / 2 - 90;
            Ui.Panel(fx, y, fw, 640);
            Ui.Label(fx + 24, y + 16, fw - 48, 40, l.Get("codex.formations"), 28, Ui.Gold, TextAnchor.UpperLeft, true);
            if (m.WinningFormations.Count == 0) Ui.Label(fx + 24, y + 66, fw - 48, 60, l.Get("codex.no_formations"), 22, Ui.Muted);
            for (int i = 0; i < m.WinningFormations.Count && i < 8; i++)
            {
                FormationSnapshot f = m.WinningFormations[i];
                float ry = y + 66 + i * 68;
                string heroes = string.Join(" ", f.Heroes.ConvertAll(h => h.Split('@')[0]));
                Ui.Label(fx + 24, ry, fw - 220, 30, f.Mode + " · A" + f.Ascension + " · " + f.Seed, 18, Ui.Muted);
                Ui.Label(fx + 24, ry + 28, fw - 220, 30, heroes, 20, Ui.White);
                if (Ui.Button(fx + fw - 190, ry + 6, 166, 54, l.Get("results.copy_build"), Tone.Ghost, true, 16)) GUIUtility.systemCopyBuffer = f.ShareCode;
            }
        }
    }
}
