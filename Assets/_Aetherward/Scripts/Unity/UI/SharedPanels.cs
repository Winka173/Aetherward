using System.Collections.Generic;
using Aetherward.Sim.Content;
using UnityEngine;

namespace Aetherward.Game
{
    /// <summary>Settings and hero detail panels shared by the menu and the in-battle pause screen.</summary>
    public static class SharedPanels
    {
        private static readonly int[] FpsOptions = { 30, 60, 120 };

        /// <summary>Returns true when the panel should close.</summary>
        public static bool Settings(float x, float y, float w, float h)
        {
            var l = App.Loc;
            var s = App.Settings;
            Ui.Panel(x, y, w, h);
            Ui.Label(x, y + 26, w, 60, l.Get("settings.title"), 46, Ui.Gold, TextAnchor.MiddleCenter, true);
            float row = y + 110, rh = 92, inner = x + 50, iw = w - 100;
            Ui.Label(inner, row, iw * 0.42f, rh, l.Get("settings.language"), 28, Ui.White, TextAnchor.MiddleLeft);
            float bx = inner + iw * 0.44f;
            for (int i = 0; i < Localization.Supported.Length; i++)
            {
                string lang = Localization.Supported[i];
                if (Ui.Button(bx + i * 250, row + 6, 240, 80, l.Get("lang." + lang), s.Language == lang ? Tone.Secondary : Tone.Ghost, true, 26))
                    App.SetLanguage(lang);
            }
            row += rh;
            float m = Ui.Stepper(inner, row, iw, rh, l.Get("settings.master"), s.MasterVolume); row += rh;
            float mu = Ui.Stepper(inner, row, iw, rh, l.Get("settings.music"), s.MusicVolume); row += rh;
            float sf = Ui.Stepper(inner, row, iw, rh, l.Get("settings.sfx"), s.SfxVolume); row += rh;
            float ui = Ui.Stepper(inner, row, iw, rh, l.Get("settings.ui"), s.UiVolume); row += rh;
            bool changed = m != s.MasterVolume || mu != s.MusicVolume || sf != s.SfxVolume || ui != s.UiVolume;
            s.MasterVolume = m;
            s.MusicVolume = mu;
            s.SfxVolume = sf;
            s.UiVolume = ui;
            float half = iw / 2 - 20;
            bool fast = Ui.Toggle(inner, row, half, rh, l.Get("settings.fast"), s.DefaultFastSpeed);
            bool vfx = Ui.Toggle(inner + half + 40, row, half, rh, l.Get("settings.reduced_vfx"), s.ReducedVfx); row += rh;
            bool shake = Ui.Toggle(inner, row, half, rh, l.Get("settings.shake"), s.ScreenShake);
            bool numbers = Ui.Toggle(inner + half + 40, row, half, rh, l.Get("settings.numbers"), s.DamageNumbers); row += rh;
            bool contrast = Ui.Toggle(inner, row, half, rh, l.Get("settings.contrast"), s.HighContrast);
            bool ranges = Ui.Toggle(inner + half + 40, row, half, rh, l.Get("settings.ranges"), s.ShowRanges); row += rh;
            changed |= fast != s.DefaultFastSpeed || vfx != s.ReducedVfx || shake != s.ScreenShake || numbers != s.DamageNumbers ||
                       contrast != s.HighContrast || ranges != s.ShowRanges;
            s.DefaultFastSpeed = fast;
            s.ReducedVfx = vfx;
            s.ScreenShake = shake;
            s.DamageNumbers = numbers;
            s.HighContrast = contrast;
            s.ShowRanges = ranges;
            Ui.Label(inner, row, iw * 0.42f, rh, l.Get("settings.fps"), 28, Ui.White, TextAnchor.MiddleLeft);
            for (int i = 0; i < FpsOptions.Length; i++)
            {
                if (Ui.Button(bx + i * 170, row + 6, 160, 80, FpsOptions[i].ToString(), s.TargetFps == FpsOptions[i] ? Tone.Secondary : Tone.Ghost, true, 26))
                {
                    s.TargetFps = FpsOptions[i];
                    changed = true;
                }
            }
            if (changed) App.SaveSettings();
            return Ui.Button(x + w / 2 - 160, y + h - 120, 320, 92, l.Get("common.close"), Tone.Primary);
        }

        /// <summary>Hero card: art, identity, stats, skill and passive text generated from data.</summary>
        public static void HeroDetail(float x, float y, float w, float h, HeroDef def, string evolutionId = null, int level = 1)
        {
            var l = App.Loc;
            Ui.Panel(x, y, w, h);
            string sprite = "Heroes/" + def.Id + (evolutionId != null ? "_evo" + (def.Evolutions.IndexOf(evolutionId) == 0 ? "A" : "B") : "_idle");
            Ui.DrawRect(x + 30, y + 30, 260, 300, new Color(0.15f, 0.18f, 0.34f, 0.8f));
            Ui.Icon(x + 30, y + 20, 260, 320, Art.Tex(sprite));
            float tx = x + 320, tw = w - 350;
            Ui.Label(tx, y + 30, tw, 60, l.Get(def.NameKey), 48, Ui.White, TextAnchor.UpperLeft, true);
            Ui.Label(tx, y + 88, tw, 40, l.Get(def.TitleKey), 26, Ui.Muted);
            Ui.Icon(tx, y + 136, 52, 52, Art.ElementIcon(def.Element));
            Ui.Icon(tx + 60, y + 136, 52, 52, Art.Tex("Icons/role_" + def.Role.ToString().ToLowerInvariant()));
            Ui.Label(tx + 124, y + 136, tw - 130, 52, l.Format("label.element_role", l.Element(def.Element), l.Role(def.Role)), 26, Ui.ElementColor(def.Element), TextAnchor.MiddleLeft, true);
            float growth = Mathf.Pow(1f + def.GrowthPerLevel, level - 1);
            string stats = l.Format("label.stats", Mathf.RoundToInt(def.BaseStats[(int)StatId.MaxHp] * growth), Mathf.RoundToInt(def.BaseStats[(int)StatId.Attack] * growth),
                Mathf.RoundToInt(def.BaseStats[(int)StatId.Defense]), def.BaseStats[(int)StatId.Range].ToString("0.#"));
            Ui.Label(tx, y + 200, tw, 40, stats, 24, Ui.Muted);

            SkillDef skill = def.Skill;
            ParamBag passiveParams = def.PassiveParams;
            string passiveKey = def.PassiveDescKey, passiveName = l.Get(def.PassiveNameKey);
            if (evolutionId != null && App.Content.Evolutions.TryGetValue(evolutionId, out EvolutionDef evo))
            {
                skill = def.Skill.With(evo.Skill);
                if (evo.PassiveKind != null)
                {
                    passiveKey = "passive." + evo.PassiveKind + ".desc";
                    passiveParams = evo.PassiveParams;
                }
            }
            float yy = y + 350;
            Ui.Label(x + 30, yy, w - 60, 40, "<b>" + l.Get("label.skill") + ":</b> " + l.Get(skill.NameKey), 28, Ui.Gold, TextAnchor.UpperLeft, true);
            yy += 42;
            string sd = l.SkillText(skill, skill.DescKey);
            Ui.Label(x + 30, yy, w - 60, 200, sd, 24, Ui.White);
            yy += Ui.TextHeight(sd, 24, w - 60) + 14;
            Ui.Label(x + 30, yy, w - 60, 40, "<b>" + l.Get("label.passive") + ":</b> " + passiveName, 28, Ui.Teal, TextAnchor.UpperLeft, true);
            yy += 42;
            Ui.Label(x + 30, yy, w - 60, 140, l.PassiveText(passiveParams, passiveKey), 24, Ui.White);
            yy += 70;
            if (evolutionId == null && yy < y + h - 90)
            {
                Ui.Label(x + 30, yy, w - 60, 40, l.Get("codex.evolutions"), 24, Ui.Muted, TextAnchor.UpperLeft, true);
                string evos = string.Join("  ·  ", new List<string>(def.Evolutions).ConvertAll(e => l.Get("evo." + e + ".name")));
                Ui.Label(x + 30, yy + 34, w - 60, 40, evos, 24, Ui.White);
            }
        }

        public static string UnlockHint(string contentId)
        {
            foreach (var rule in Sim.Meta.MetaProfile.Rules)
            {
                if (rule.Id != contentId) continue;
                return App.Loc.Format("team.locked_hint", App.Loc.Format("unlock." + rule.Condition, rule.Value));
            }
            return App.Loc.Get("common.locked");
        }
    }
}
