using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Run;
using UnityEngine;

namespace Aetherward.Game
{
    /// <summary>
    /// Training Chamber page (P2): pick up to 6 unlocked heroes, a dummy profile and a duration, run the real
    /// simulation headlessly (deterministic, instant) and read sourced metrics. No rewards, no save changes.
    /// </summary>
    public sealed partial class MenuController
    {
        private readonly List<string> _trainHeroes = new List<string>();
        private DummyProfile _trainProfile = DummyProfile.Swarm;
        private float _trainSeconds = 20f;
        private bool _trainSandbox;
        private TrainingReport _trainReport;
        private string _trainError;
        private Vector2 _trainScroll;

        private void DrawTraining()
        {
            var l = App.Loc;
            Ui.DrawRect(0, 0, Ui.W, Ui.H, new Color(0.04f, 0.05f, 0.12f, 0.85f));
            Ui.Label(0, 30, Ui.W, 70, l.Get("training.title"), 54, Ui.Gold, TextAnchor.MiddleCenter, true);
            Ui.Label(0, 96, Ui.W, 36, l.Get("training.subtitle"), 22, Ui.Muted, TextAnchor.MiddleCenter);

            // Hero picker (unlocked heroes; sandbox exposes the rest, clearly marked).
            float gx = 60, gy = 150, cell = 118;
            int col = 0, row = 0;
            foreach (HeroDef h in App.Content.HeroList)
            {
                bool unlocked = App.Meta.UnlockedHeroes.Contains(h.Id);
                if (!unlocked && !_trainSandbox) continue;
                float x = gx + col * (cell + 8), y = gy + row * (cell + 8);
                bool on = _trainHeroes.Contains(h.Id);
                Ui.DrawRect(x, y, cell, cell, on ? new Color(0.35f, 0.3f, 0.1f, 0.9f) : new Color(0.12f, 0.14f, 0.26f, 0.85f));
                Ui.HeroIcon(x + 4, y + 4, cell - 8, cell - 8, Art.Tex("Heroes/" + h.Id + "_idle"), unlocked ? (Color?)null : new Color(1, 1, 1, 0.5f));
                if (Ui.Hit(x, y, cell, cell))
                {
                    if (on) _trainHeroes.Remove(h.Id);
                    else if (_trainHeroes.Count < 6) _trainHeroes.Add(h.Id);
                    _trainReport = null;
                }
                if (++col == 7) { col = 0; row++; }
            }

            // Options column.
            float ox = Ui.W - 700, oy = 150;
            Ui.Label(ox, oy, 640, 34, l.Get("training.profile"), 24, Ui.White, TextAnchor.UpperLeft, true);
            var profiles = (DummyProfile[])System.Enum.GetValues(typeof(DummyProfile));
            for (int i = 0; i < profiles.Length; i++)
                if (Ui.Button(ox + (i % 3) * 214, oy + 40 + (i / 3) * 66, 206, 58, l.Get("training.profile." + profiles[i].ToString().ToLowerInvariant()),
                        _trainProfile == profiles[i] ? Tone.Secondary : Tone.Ghost, true, 18)) { _trainProfile = profiles[i]; _trainReport = null; }
            oy += 190;
            Ui.Label(ox, oy, 640, 34, l.Get("training.duration"), 24, Ui.White, TextAnchor.UpperLeft, true);
            for (int i = 0; i < TrainingChamber.AllowedSeconds.Length; i++)
            {
                float sec = TrainingChamber.AllowedSeconds[i];
                if (Ui.Button(ox + i * 150, oy + 40, 140, 58, sec + " s", Mathf.Approximately(_trainSeconds, sec) ? Tone.Secondary : Tone.Ghost, true, 20)) { _trainSeconds = sec; _trainReport = null; }
            }
            oy += 120;
            bool sb = Ui.Toggle(ox, oy, 640, 60, l.Get("training.sandbox"), _trainSandbox);
            if (sb != _trainSandbox) { _trainSandbox = sb; _trainReport = null; if (!sb) _trainHeroes.RemoveAll(id => !App.Meta.UnlockedHeroes.Contains(id)); }
            oy += 80;
            if (Ui.Button(ox, oy, 310, 96, l.Get(_trainReport == null ? "training.run" : "training.restart"), Tone.Primary, _trainHeroes.Count > 0, 30))
                RunTraining();
            if (Ui.Button(ox + 330, oy, 310, 96, l.Get("common.back"), Tone.Ghost, true, 30)) _page = Page.Main;
            if (_trainError != null) Ui.Label(ox, oy + 104, 640, 40, l.Get("training.error." + _trainError.Split(':')[0]), 20, Ui.Bad);

            if (_trainReport != null) DrawTrainingReport(60, 560, Ui.W - 120, Ui.H - 600);
        }

        private void RunTraining()
        {
            var cfg = new TrainingConfig { Profile = _trainProfile, Seconds = _trainSeconds, Seed = 1, Sandbox = _trainSandbox };
            // Fixed node layout: inner ring first, then the outer ring (same layout every run -> reproducible).
            for (int i = 0; i < _trainHeroes.Count; i++) cfg.Heroes.Add(new TrainingHero { HeroId = _trainHeroes[i], Node = i < 4 ? i : 4 + (i - 4) * 4 });
            if (!TrainingChamber.CanUse(App.Content, cfg, App.Meta.UnlockedHeroes, out _trainError)) { _trainReport = null; return; }
            _trainError = null;
            _trainReport = TrainingChamber.Run(App.Content, cfg);
        }

        private void DrawTrainingReport(float x, float y, float w, float h)
        {
            var l = App.Loc;
            TrainingReport r = _trainReport;
            Ui.Panel(x, y, w, h);
            string head = l.Format("training.summary", r.Seconds, l.Get("training.profile." + r.Profile.ToString().ToLowerInvariant())) + (r.Sandbox ? "  [SANDBOX]" : "");
            Ui.Label(x + 24, y + 16, w - 48, 34, head, 24, Ui.Gold, TextAnchor.UpperLeft, true);
            string[] rows =
            {
                l.Format("training.m.raw", r.RawDps.ToString("F1")), l.Format("training.m.reaction", r.ReactionDps.ToString("F1")),
                l.Format("training.m.dot", r.DotDps.ToString("F1")), l.Format("training.m.trigger", r.TriggerDps.ToString("F1")),
                l.Format("training.m.heal", r.HealPerSecond.ToString("F1")), l.Format("training.m.shield", r.ShieldAbsorbed.ToString("F0")),
                l.Format("training.m.cc", Mathf.RoundToInt(r.HardCcUptime * 100f), Mathf.RoundToInt(r.SlowUptime * 100f)),
                l.Format("training.m.ttk", r.AvgTimeToKill.ToString("F1"), r.Kills), l.Format("training.m.reactions", r.Reactions),
                l.Format("training.m.idle", Mathf.RoundToInt(r.HeroIdleShare * 100f)),
                l.Format("training.m.survive", r.HeroDowns, Mathf.RoundToInt(r.MinHeroHpFraction * 100f), r.DamageTakenByHeroes.ToString("F0"))
            };
            for (int i = 0; i < rows.Length; i++)
                Ui.Label(x + 24 + (i % 2) * (w / 2), y + 60 + (i / 2) * 34, w / 2 - 40, 32, rows[i], 20, Ui.White);
            float ny = y + 60 + ((rows.Length + 1) / 2) * 34 + 10;
            foreach (string n in r.Notes)
            {
                Ui.Label(x + 24, ny, w - 48, 28, "• " + l.Get(n), 18, Ui.Muted);
                ny += 28;
            }
        }
    }
}
