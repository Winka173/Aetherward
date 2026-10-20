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
            // 11 rows must fit the 960-high panel (two settings per row; rh 70 leaves room for Close).
            float row = y + 110, rh = 70, inner = x + 50, iw = w - 100;
            Ui.Label(inner, row, iw * 0.42f, rh, l.Get("settings.language"), 28, Ui.White, TextAnchor.MiddleLeft);
            float bx = inner + iw * 0.44f;
            for (int i = 0; i < Localization.Supported.Length; i++)
            {
                string lang = Localization.Supported[i];
                if (Ui.Button(bx + i * 250, row + 6, 240, 80, l.Get("lang." + lang), s.Language == lang ? Tone.Secondary : Tone.Ghost, true, 26))
                    App.SetLanguage(lang);
            }
            row += rh;
            float hw = iw / 2 - 20;
            float m = Ui.Stepper(inner, row, hw, rh, l.Get("settings.master"), s.MasterVolume);
            float mu = Ui.Stepper(inner + hw + 40, row, hw, rh, l.Get("settings.music"), s.MusicVolume); row += rh;
            float sf = Ui.Stepper(inner, row, hw, rh, l.Get("settings.sfx"), s.SfxVolume);
            float ui = Ui.Stepper(inner + hw + 40, row, hw, rh, l.Get("settings.ui"), s.UiVolume); row += rh;
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
            bool focusPause = Ui.Toggle(inner, row, half, rh, l.Get("settings.focus_pause"), s.PauseOnFocusLoss);
            bool battery = Ui.Toggle(inner + half + 40, row, half, rh, l.Get("settings.battery"), s.BatterySaver); row += rh;
            bool synergy = Ui.Toggle(inner, row, half, rh, l.Get("settings.synergy"), s.SynergyVision);
            bool assist = Ui.Toggle(inner + half + 40, row, half, rh, l.Get("settings.telegraph_assist"), s.TelegraphAssist); row += rh;
            changed |= synergy != s.SynergyVision || assist != s.TelegraphAssist;
            s.TelegraphAssist = assist;
            s.SynergyVision = synergy;
            float flash = Ui.Stepper(inner, row, iw, rh, l.Get("settings.flash"), s.FlashIntensity); row += rh;
            changed |= focusPause != s.PauseOnFocusLoss || battery != s.BatterySaver || flash != s.FlashIntensity;
            bool reapply = battery != s.BatterySaver || flash != s.FlashIntensity || shake != s.ScreenShake || vfx != s.ReducedVfx;
            s.PauseOnFocusLoss = focusPause;
            s.BatterySaver = battery;
            s.FlashIntensity = Mathf.Clamp01(flash);
            changed |= fast != s.DefaultFastSpeed || vfx != s.ReducedVfx || shake != s.ScreenShake || numbers != s.DamageNumbers ||
                       contrast != s.HighContrast || ranges != s.ShowRanges;
            s.DefaultFastSpeed = fast;
            s.ReducedVfx = vfx;
            s.ScreenShake = shake;
            s.DamageNumbers = numbers;
            s.HighContrast = contrast;
            s.ShowRanges = ranges;
            if (reapply) App.ApplySettings();
            // Effects intensity preset (P7); Screen shake / Flash / Reduced VFX above stay hard caps on it.
            Ui.Label(inner, row, iw * 0.42f, rh, l.Get("settings.fx_preset"), 28, Ui.White, TextAnchor.MiddleLeft);
            for (int i = 0; i < 4; i++)
            {
                if (Ui.Button(bx + i * 140, row + 6, 132, 72, l.Get("settings.fx_preset." + i), s.EffectsPreset == i ? Tone.Secondary : Tone.Ghost, true, 22))
                {
                    s.EffectsPreset = i;
                    App.ApplySettings();
                    changed = true;
                }
            }
            row += rh;
            Ui.Label(inner, row, iw * 0.42f, rh, l.Get("settings.fps"), 28, Ui.White, TextAnchor.MiddleLeft);
            for (int i = 0; i < FpsOptions.Length; i++)
            {
                if (Ui.Button(bx + i * 170, row + 6, 160, 72, FpsOptions[i].ToString(), s.TargetFps == FpsOptions[i] ? Tone.Secondary : Tone.Ghost, true, 26))
                {
                    s.TargetFps = FpsOptions[i];
                    changed = true;
                }
            }
            if (changed) App.SaveSettings();
            // Placed below the last row so it never overlaps the FPS buttons.
            return Ui.Button(x + w / 2 - 160, row + rh + 10, 320, 80, l.Get("common.close"), Tone.Primary);
        }

        /// <summary>Hero card: art, identity, stats, skill and passive text generated from data.</summary>
        /// <summary>Trait name + rule text (behaviour template plus generated stat lines).</summary>
        public static string TraitText(string traitId)
        {
            if (string.IsNullOrEmpty(traitId) || !App.Content.Traits.TryGetValue(traitId, out TraitDef t)) return null;
            var l = App.Loc;
            string text = l.PassiveText(t.Behaviour, t.DescKey);
            List<string> fx = App.Fx.Describe(t.Effects);
            if (fx.Count > 0) text += " (" + string.Join(", ", fx) + ")";
            return text;
        }

        public static void HeroDetail(float x, float y, float w, float h, HeroDef def, string evolutionId = null, int level = 1, string traitId = null, string awakened = null)
        {
            var l = App.Loc;
            Ui.Panel(x, y, w, h);
            string sprite = "Heroes/" + def.Id + (evolutionId != null ? "_evo" + (def.Evolutions.IndexOf(evolutionId) == 0 ? "A" : "B") : "_idle");
            Ui.DrawRect(x + 30, y + 30, 260, 300, new Color(0.15f, 0.18f, 0.34f, 0.8f));
            Ui.HeroIcon(x + 30, y + 20, 260, 320, Art.Tex(sprite));
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
            string passiveText = l.PassiveText(passiveParams, passiveKey);
            Ui.Label(x + 30, yy, w - 60, 140, passiveText, 24, Ui.White);
            yy += Ui.TextHeight(passiveText, 24, w - 60) + 14;
            string trait = TraitText(traitId);
            if (trait != null)
            {
                Ui.Icon(x + 30, yy, 40, 40, Art.Tex("Icons/trait_" + traitId));
                Ui.Label(x + 78, yy, w - 110, 40, "<b>" + l.Get("trait.label") + ":</b> " + l.Get("trait." + traitId + ".name"), 26, Ui.Gold, TextAnchor.MiddleLeft, true);
                yy += 44;
                Ui.Label(x + 30, yy, w - 60, 100, trait, 22, Ui.White);
                yy += Ui.TextHeight(trait, 22, w - 60) + 10;
            }
            if (awakened != null && ElementUtil.TryParse(awakened, out Element aw) && aw != Element.None)
            {
                string elName = l.Get("element." + awakened);
                Ui.Icon(x + 30, yy, 40, 40, Art.ElementIcon(aw));
                Ui.Label(x + 78, yy, w - 110, 40, "<b>" + l.Format("hero.awakened", elName) + "</b>", 26, Ui.ElementColor(aw), TextAnchor.MiddleLeft, true);
                yy += 44;
                string ad = l.Format("hero.awakened.desc", elName);
                Ui.Label(x + 30, yy, w - 60, 80, ad, 22, Ui.White);
                yy += Ui.TextHeight(ad, 22, w - 60) + 10;
            }
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
                object arg = rule.Value;
                if (rule.Condition == "defeat_boss" && rule.Param != null) arg = App.Loc.Get("enemy." + rule.Param + ".name");
                return App.Loc.Format("team.locked_hint", App.Loc.Format("unlock." + rule.Condition, arg));
            }
            return App.Loc.Get("common.locked");
        }
    }
}
