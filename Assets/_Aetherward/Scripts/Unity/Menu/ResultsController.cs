using System;
using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using Aetherward.Sim.Meta;
using Aetherward.Sim.Run;
using UnityEngine;

namespace Aetherward.Game
{
    /// <summary>
    /// Post-run analytics: outcome, per-hero contribution, reaction chart, relic activations, crystal
    /// timeline, insights explaining why the run went this way, unlocks, and one-tap replay.
    /// </summary>
    public sealed class ResultsController : MonoBehaviour
    {
        private RunResults _r;
        private float _t;

        private void Start()
        {
            GameRoot.EnsureCamera(new Color(0.06f, 0.07f, 0.15f));
            _r = App.LastResults;
            App.Audio.PlayMusic("menu_loop");
            if (_r != null) App.Audio.Play(_r.Victory ? "victory" : "defeat", 1f, 0f, SoundCategory.Ui);
        }

        private void Update() => _t += Time.unscaledDeltaTime;

        private void OnGUI()
        {
            Ui.Begin();
            var l = App.Loc;
            Ui.DrawRect(0, 0, Ui.W, Ui.H, new Color(0.06f, 0.07f, 0.15f));
            if (_r == null)
            {
                if (Ui.Button(Ui.W / 2 - 200, Ui.H / 2 - 50, 400, 100, l.Get("results.menu"))) GameRoot.Instance.GoTo(AppScreen.MainMenu);
                return;
            }
            float pop = Mathf.Clamp01(_t * 2f);
            Ui.Label(0, 30, Ui.W, 110, _r.Victory ? l.Get("results.victory") : l.Get("results.defeat"), 90 * (0.7f + 0.3f * pop),
                _r.Victory ? Ui.Gold : Ui.Bad, TextAnchor.UpperCenter, true);
            TimeSpan active = TimeSpan.FromSeconds(_r.ActiveSeconds);
            Ui.Label(0, 140, Ui.W, 44, l.Format("results.reached", _r.WaveReached, active.Minutes + ":" + active.Seconds.ToString("00")), 28, Ui.White, TextAnchor.UpperCenter);
            Ui.Label(0, 182, Ui.W, 34, l.Format("results.seed", _r.Seed, _r.GameVersion), 20, Ui.Muted, TextAnchor.UpperCenter);
            string turning = l.Format("results.turning", _r.ClosestSaveWave, Mathf.RoundToInt(_r.ClosestSaveHpFraction * 100f),
                _r.MostDamagingThreat != null ? l.Get("enemy." + _r.MostDamagingThreat + ".name") : "—",
                Mathf.RoundToInt(_r.MenuSeconds / 60f));
            Ui.Label(0, 210, Ui.W, 30, turning, 18, Ui.Muted, TextAnchor.UpperCenter);
            if (Ui.Button(Ui.W - 300, 140, 260, 60, l.Get("results.copy_build"), Tone.Ghost, true, 20)) GUIUtility.systemCopyBuffer = _r.ShareCode;
            if (App.Meta.LastMilestones.Count > 0)
            {
                var names = new List<string>();
                foreach (string ms in App.Meta.LastMilestones) names.Add(MilestoneName(ms));
                Ui.Label(40, 140, 520, 80, l.Get("milestone.earned") + " " + string.Join(", ", names), 18, Ui.Gold, TextAnchor.UpperLeft, true);
            }

            float colW = (Ui.W - 120) / 3f;
            DrawHeroes(40, 240, colW, 560);
            DrawReactions(60 + colW, 240, colW, 560);
            DrawRight(80 + colW * 2, 240, colW, 560);

            float by = Ui.H - 140;
            DrawFeedback(by - 84);
            if (Ui.Button(Ui.W / 2 - 520, by, 500, 104, l.Get("results.replay"), Tone.Primary, true, 30))
            {
                List<string> starters = new List<string>();
                foreach (HeroResult h in _r.Heroes) if (starters.Count < 2) starters.Add(h.HeroId);
                App.ClearRun();
                App.Run = RunController.NewRun(App.Content, Pcg32.SeedFromTime(DateTime.UtcNow), starters, _r.Ascension, App.Meta.ToRunUnlocks());
                App.SaveRun();
                GameRoot.Instance.GoTo(AppScreen.Battle);
            }
            if (Ui.Button(Ui.W / 2 + 20, by, 500, 104, l.Get("results.menu"), Tone.Ghost, true, 30))
            {
                App.Run = null;
                GameRoot.Instance.GoTo(AppScreen.MainMenu);
            }
        }

        private void DrawHeroes(float x, float y, float w, float h)
        {
            var l = App.Loc;
            Ui.Panel(x, y, w, h);
            Ui.Label(x + 24, y + 18, w - 48, 40, l.Get("results.heroes"), 30, Ui.Gold, TextAnchor.UpperLeft, true);
            float max = 1f;
            foreach (HeroResult hr in _r.Heroes) max = Mathf.Max(max, hr.DamageDealt + hr.HealingDone);
            float yy = y + 70;
            foreach (HeroResult hr in _r.Heroes)
            {
                Ui.Icon(x + 24, yy, 72, 72, Art.Portrait(hr.HeroId));
                string name = l.Get("hero." + hr.HeroId + ".name") + (hr.EvolutionId != null ? " · " + l.Get("evo." + hr.EvolutionId + ".name") : "");
                Ui.Label(x + 108, yy, w - 130, 30, name + (hr.HeroId == _r.MvpHero ? "  <color=#ffd35a>★ " + l.Get("results.mvp") + "</color>" : ""), 20, Ui.White, TextAnchor.UpperLeft, true);
                float dmgW = (w - 140) * hr.DamageDealt / max, healW = (w - 140) * hr.HealingDone / max;
                Ui.DrawRect(x + 108, yy + 34, Mathf.Max(2, dmgW), 16, new Color(1f, 0.5f, 0.35f));
                Ui.DrawRect(x + 108 + dmgW, yy + 34, healW, 16, Ui.Good);
                Ui.Label(x + 108, yy + 50, w - 130, 26, l.Get("results.damage") + " " + Mathf.RoundToInt(hr.DamageDealt) + " · " + l.Get("results.kills") + " " + hr.Kills +
                                                     (hr.HealingDone > 1 ? " · " + l.Get("results.healing") + " " + Mathf.RoundToInt(hr.HealingDone) : ""), 17, Ui.Muted);
                yy += 82;
            }
        }

        private void DrawReactions(float x, float y, float w, float h)
        {
            var l = App.Loc;
            Ui.Panel(x, y, w, h);
            Ui.Label(x + 24, y + 18, w - 48, 40, l.Get("results.reactions") + " (" + _r.TotalReactions + ")", 30, Ui.Gold, TextAnchor.UpperLeft, true);
            float max = 1f;
            foreach (RankedEntry e in _r.Reactions) max = Mathf.Max(max, e.Value);
            float yy = y + 70;
            int shown = 0;
            foreach (RankedEntry e in _r.Reactions)
            {
                if (shown++ >= 8) break;
                Ui.Icon(x + 24, yy, 48, 48, Art.Tex("Icons/reaction_" + e.Id));
                Ui.Label(x + 82, yy, w - 110, 26, l.ReactionName(e.Id) + " ×" + e.Count, 20, Ui.White, TextAnchor.UpperLeft, true);
                Ui.DrawRect(x + 82, yy + 28, Mathf.Max(2, (w - 120) * e.Value / max), 14, new Color(0.6f, 0.75f, 1f));
                yy += 58;
            }
            yy = y + h - 120;
            Ui.Label(x + 24, yy, w - 48, 30, l.Get("results.elements"), 20, Ui.Muted, TextAnchor.UpperLeft, true);
            float total = 0f;
            for (int i = 1; i < _r.ElementDamage.Length; i++) total += _r.ElementDamage[i];
            float bx = x + 24, bw = w - 48;
            for (int i = 1; i < _r.ElementDamage.Length; i++)
            {
                float share = total > 0 ? _r.ElementDamage[i] / total : 0f;
                Ui.DrawRect(bx, yy + 36, bw * share, 28, Ui.ElementColor((Element)i));
                bx += bw * share;
            }
        }

        private void DrawRight(float x, float y, float w, float h)
        {
            var l = App.Loc;
            Ui.Panel(x, y, w, h);
            Ui.Label(x + 24, y + 18, w - 48, 40, l.Get("results.crystal"), 26, Ui.Gold, TextAnchor.UpperLeft, true);
            // crystal HP timeline
            float gx = x + 24, gy = y + 66, gw = w - 48, gh = 110;
            Ui.DrawRect(gx, gy, gw, gh, new Color(0.1f, 0.12f, 0.24f));
            float maxHp = 1f;
            foreach (WaveRecord wr in _r.Waves) maxHp = Mathf.Max(maxHp, wr.CrystalHpAfter + wr.CrystalDamage);
            int n = Mathf.Max(1, _r.Waves.Count);
            for (int i = 0; i < _r.Waves.Count; i++)
            {
                WaveRecord wr = _r.Waves[i];
                float bh = gh * wr.CrystalHpAfter / maxHp;
                Ui.DrawRect(gx + i * gw / n + 1, gy + gh - bh, gw / n - 2, bh, Color.Lerp(Ui.Bad, new Color(0.45f, 0.9f, 1f), wr.CrystalHpAfter / maxHp));
            }
            float yy = gy + gh + 20;
            Ui.Label(x + 24, yy, w - 48, 36, l.Get("results.insights"), 24, Ui.Gold, TextAnchor.UpperLeft, true);
            yy += 40;
            foreach (string ins in _r.Insights)
            {
                string[] parts = ins.Split('|');
                string arg = parts.Length > 1 ? parts[1] : "";
                if (parts[0] == "insight.strongest_reaction") arg = l.ReactionName(arg);
                if (parts[0] == "insight.defeated_by") arg = arg == "abandoned" || arg == "breach" ? arg : l.Get("enemy." + arg + ".name");
                string text = "• " + l.Format(parts[0], arg);
                Ui.Label(x + 24, yy, w - 48, 80, text, 19, Ui.White);
                yy += Ui.TextHeight(text, 19, w - 48) + 6;
            }
            if (App.LastUnlocks != null && App.LastUnlocks.Count > 0)
            {
                yy += 8;
                Ui.Label(x + 24, yy, w - 48, 36, l.Get("results.unlocked"), 24, Ui.Good, TextAnchor.UpperLeft, true);
                yy += 40;
                float ix = x + 24;
                foreach (string u in App.LastUnlocks)
                {
                    Texture tex = u.StartsWith("hero:") ? Art.Portrait(u.Substring(5))
                        : u.StartsWith("biome:") ? Art.Tex(App.Content.BiomeOrDefault(u.Substring(6)).Background)
                        : Art.Tex("Relics/" + u.Substring(6));
                    Ui.Icon(ix, yy, 72, 72, tex);
                    ix += 80;
                }
            }
        }

        /// <summary>Optional local feedback (Phase 13): 1–5 rating + reason chips, stored only in the meta save.</summary>
        private void DrawFeedback(float y)
        {
            var l = App.Loc;
            RunFeedback f = App.Meta.Feedback.Find(x => x.Seed == _r.Seed);
            float x = Ui.W / 2 - 640;
            Ui.Label(x, y, 220, 64, l.Get("feedback.prompt"), 20, Ui.Muted, TextAnchor.MiddleLeft);
            x += 230;
            for (int i = 1; i <= 5; i++, x += 66)
            {
                bool on = f != null && f.Rating >= i;
                if (Ui.Button(x, y + 4, 60, 56, "★", on ? Tone.Secondary : Tone.Ghost, true, 26)) Record(i, null);
            }
            x += 20;
            foreach (string tag in RunFeedback.TagIds)
            {
                bool on = f != null && f.Tags.Contains(tag);
                if (Ui.Button(x, y + 4, 150, 56, l.Get("feedback." + tag), on ? Tone.Secondary : Tone.Ghost, true, 16)) Record(0, tag);
                x += 158;
            }
        }

        private void Record(int rating, string tag)
        {
            App.Meta.RecordFeedback(_r.Seed, _r.WaveReached, _r.Victory, rating, tag);
            App.SaveMeta();
        }

        public static string MilestoneName(string id)
        {
            var l = App.Loc;
            int c = id.IndexOf(':');
            return c < 0 ? l.Get("milestone." + id) : l.Format("milestone." + id.Substring(0, c), id.Substring(c + 1));
        }
    }
}
