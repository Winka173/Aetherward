using System.Collections.Generic;
using UnityEngine;

namespace Aetherward.Game
{
    public enum Tone
    {
        Primary,
        Secondary,
        Danger,
        Ghost
    }

    /// <summary>
    /// Immediate-mode UI kit on top of IMGUI. Layout uses a virtual canvas 1080 units tall (width
    /// varies with aspect) inside the device safe area. Fonts are sized in real pixels each frame so
    /// text stays crisp at any resolution. All interactive elements are tap-sized (>= 88 virtual px
    /// tall at 1080p ≈ 44dp) and nothing relies on hover.
    /// </summary>
    public static class Ui
    {
        public const float RefHeight = 1080f;
        public const float MinWidth = 1600f;

        public static float Scale { get; private set; } = 1f;
        public static float W { get; private set; } = 1920f;
        public static float H { get; private set; } = 1080f;
        private static Rect _safe;
        private static float _builtScale = -1f;
        private static bool _builtContrast;

        public static Font Heading, Body, Numbers;
        private static readonly Dictionary<string, GUIStyle> Styles = new Dictionary<string, GUIStyle>();
        private static GUIStyle _panelDark, _panelLight, _panelGlass, _panelDanger, _tooltip, _barBg, _barFill;
        private static readonly Dictionary<Tone, GUIStyle> Buttons = new Dictionary<Tone, GUIStyle>();
        private static readonly Dictionary<string, GUIStyle> CardFrames = new Dictionary<string, GUIStyle>();

        public static readonly Color Gold = new Color(1f, 0.83f, 0.35f);
        public static readonly Color Teal = new Color(0.37f, 0.88f, 0.82f);
        public static readonly Color Ink = new Color(0.07f, 0.06f, 0.14f, 0.9f);
        public static readonly Color Muted = new Color(0.75f, 0.78f, 0.9f);
        public static readonly Color Good = new Color(0.49f, 1f, 0.6f);
        public static readonly Color Bad = new Color(1f, 0.42f, 0.48f);
        public static readonly Color White = Color.white;

        /// <summary>Call at the top of every OnGUI.</summary>
        public static void Begin()
        {
            _safe = Screen.safeArea;
            if (_safe.width <= 0 || _safe.height <= 0) _safe = new Rect(0, 0, Screen.width, Screen.height);
            float s = _safe.height / RefHeight;
            if (_safe.width / s < MinWidth) s = _safe.width / MinWidth;
            Scale = Mathf.Max(0.2f, s);
            W = _safe.width / Scale;
            H = _safe.height / Scale;
            bool contrast = App.Settings != null && App.Settings.HighContrast;
            if (Mathf.Abs(_builtScale - Scale) > 0.001f || _builtContrast != contrast) Build(contrast);
        }

        public static Rect R(float x, float y, float w, float h)
        {
            float top = Screen.height - _safe.yMax;
            return new Rect(_safe.x + x * Scale, top + y * Scale, w * Scale, h * Scale);
        }

        public static Vector2 ToVirtual(Vector2 guiPoint)
        {
            float top = Screen.height - _safe.yMax;
            return new Vector2((guiPoint.x - _safe.x) / Scale, (guiPoint.y - top) / Scale);
        }

        /// <summary>World position (Unity screen space, y up) to virtual UI coordinates.</summary>
        public static Vector2 FromScreen(Vector3 screen)
        {
            return ToVirtual(new Vector2(screen.x, Screen.height - screen.y));
        }

        // ------------------------------------------------------------------ styles

        private static void Build(bool contrast)
        {
            _builtScale = Scale;
            _builtContrast = contrast;
            if (Heading == null)
            {
                Heading = Resources.Load<Font>("Fonts/BeVietnamPro-Black");
                Body = Resources.Load<Font>("Fonts/BeVietnamPro-SemiBold");
                Numbers = Resources.Load<Font>("Fonts/LilitaOne-Regular");
                if (Body == null) Body = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
                if (Heading == null) Heading = Body;
                if (Numbers == null) Numbers = Heading;
            }
            Styles.Clear();
            _panelDark = Slice("UI/panel_dark", 40);
            _panelLight = Slice("UI/panel_light", 40);
            _panelGlass = Slice("UI/panel_glass", 40);
            _panelDanger = Slice("UI/panel_danger", 40);
            _tooltip = Slice("UI/tooltip", 24);
            _barBg = Slice("UI/bar_bg", 18);
            _barFill = Slice("UI/bar_fill", 18);
            Buttons.Clear();
            foreach (Tone t in new[] { Tone.Primary, Tone.Secondary, Tone.Danger, Tone.Ghost })
            {
                string k = t.ToString().ToLowerInvariant();
                var st = Slice("UI/button_" + k + "_normal", 36);
                st.hover.background = Art.Tex("UI/button_" + k + "_hover");
                st.active.background = Art.Tex("UI/button_" + k + "_pressed");
                st.onNormal.background = st.active.background;
                st.font = Heading;
                st.alignment = TextAnchor.MiddleCenter;
                st.fontSize = Px(30);
                st.wordWrap = true;
                st.padding = new RectOffset(Px(18), Px(18), Px(6), Px(12));
                Color text = t == Tone.Primary ? new Color(0.2f, 0.1f, 0.05f) : Color.white;
                st.normal.textColor = st.hover.textColor = st.active.textColor = st.onNormal.textColor = text;
                Buttons[t] = st;
            }
            CardFrames.Clear();
            foreach (string r in new[] { "common", "rare", "epic", "legendary", "cursed" })
                CardFrames[r] = Slice("UI/card_" + r, 48);
        }

        private static GUIStyle Slice(string path, int border)
        {
            var st = new GUIStyle();
            st.normal.background = Art.Tex(path);
            st.border = new RectOffset(border, border, border, border);
            return st;
        }

        public static int Px(float virtualSize) => Mathf.Max(1, Mathf.RoundToInt(virtualSize * Scale));

        public static GUIStyle Text(float size, Color color, TextAnchor align = TextAnchor.UpperLeft, bool heading = false, bool numbers = false, bool wrap = true)
        {
            string key = size + "|" + color + "|" + align + "|" + heading + "|" + numbers + "|" + wrap;
            if (Styles.TryGetValue(key, out GUIStyle st)) return st;
            st = new GUIStyle
            {
                font = numbers ? Numbers : (heading ? Heading : Body),
                fontSize = Px(size),
                alignment = align,
                wordWrap = wrap,
                richText = true,
                clipping = TextClipping.Overflow
            };
            st.normal.textColor = color;
            Styles[key] = st;
            return st;
        }

        // ------------------------------------------------------------------ primitives

        public static void Label(float x, float y, float w, float h, string text, float size = 26, Color? color = null,
            TextAnchor align = TextAnchor.UpperLeft, bool heading = false, bool shadow = true, bool numbers = false)
        {
            Color c = color ?? White;
            if (shadow)
            {
                GUIStyle sh = Text(size, new Color(0.04f, 0.03f, 0.1f, 0.85f * c.a), align, heading, numbers);
                float o = Mathf.Max(1.5f, size * 0.07f);
                GUI.Label(R(x + o * 0.6f, y + o, w, h), text, sh);
            }
            GUI.Label(R(x, y, w, h), text, Text(size, c, align, heading, numbers));
        }

        public static float TextHeight(string text, float size, float width, bool heading = false)
        {
            GUIStyle st = Text(size, White, TextAnchor.UpperLeft, heading);
            return st.CalcHeight(new GUIContent(text), width * Scale) / Scale;
        }

        public static void Panel(float x, float y, float w, float h, string kind = "dark")
        {
            GUIStyle st = kind == "light" ? _panelLight : kind == "glass" ? _panelGlass : kind == "danger" ? _panelDanger : _panelDark;
            if (st != null && st.normal.background != null) GUI.Box(R(x, y, w, h), GUIContent.none, st);
            else DrawRect(x, y, w, h, new Color(0.11f, 0.13f, 0.25f, 0.95f));
        }

        public static void Tooltip(float x, float y, float w, float h)
        {
            if (_tooltip != null && _tooltip.normal.background != null) GUI.Box(R(x, y, w, h), GUIContent.none, _tooltip);
        }

        public static void CardFrame(float x, float y, float w, float h, string rarity, bool selected = false)
        {
            if (selected) DrawRect(x - 6, y - 6, w + 12, h + 12, new Color(1f, 0.86f, 0.4f, 0.55f));
            if (CardFrames.TryGetValue(rarity, out GUIStyle st) && st.normal.background != null) GUI.Box(R(x, y, w, h), GUIContent.none, st);
        }

        public static bool Button(float x, float y, float w, float h, string text, Tone tone = Tone.Primary, bool enabled = true, float size = 30)
        {
            GUIStyle st = Buttons.TryGetValue(tone, out GUIStyle b) ? b : GUI.skin.button;
            bool prevEnabled = GUI.enabled;
            GUI.enabled = enabled;
            if (!enabled)
            {
                st = new GUIStyle(st);
                string k = tone.ToString().ToLowerInvariant();
                st.normal.background = st.hover.background = st.active.background = Art.Tex("UI/button_" + k + "_disabled");
                st.normal.textColor = st.hover.textColor = new Color(0.85f, 0.85f, 0.9f);
            }
            st.fontSize = Px(size);
            bool clicked = GUI.Button(R(x, y, w, h), text, st);
            GUI.enabled = prevEnabled;
            if (clicked && App.Audio != null) App.Audio.Ui("ui_click");
            return clicked;
        }

        /// <summary>Invisible full-rect hit area (for tapping cards, portraits, list rows).</summary>
        public static bool Hit(float x, float y, float w, float h)
        {
            bool clicked = GUI.Button(R(x, y, w, h), GUIContent.none, GUIStyle.none);
            if (clicked && App.Audio != null) App.Audio.Ui("ui_card");
            return clicked;
        }

        public static void Icon(float x, float y, float w, float h, Texture tex, Color? tint = null)
        {
            if (tex == null) return;
            Color prev = GUI.color;
            if (tint.HasValue) GUI.color = tint.Value;
            GUI.DrawTexture(R(x, y, w, h), tex, ScaleMode.ScaleToFit, true);
            GUI.color = prev;
        }

        public static void DrawRect(float x, float y, float w, float h, Color c)
        {
            Color prev = GUI.color;
            GUI.color = c;
            GUI.DrawTexture(R(x, y, w, h), Texture2D.whiteTexture);
            GUI.color = prev;
        }

        public static void Bar(float x, float y, float w, float h, float fraction, Color fill, string text = null, float textSize = 20)
        {
            fraction = Mathf.Clamp01(fraction);
            if (_barBg != null && _barBg.normal.background != null) GUI.Box(R(x, y, w, h), GUIContent.none, _barBg);
            else DrawRect(x, y, w, h, new Color(0.08f, 0.08f, 0.16f));
            if (fraction > 0.001f)
            {
                Color prev = GUI.color;
                GUI.color = fill;
                float fw = Mathf.Max(h, w * fraction);
                if (_barFill != null && _barFill.normal.background != null) GUI.Box(R(x, y, fw, h), GUIContent.none, _barFill);
                else GUI.DrawTexture(R(x, y, w * fraction, h), Texture2D.whiteTexture);
                GUI.color = prev;
            }
            if (text != null) Label(x, y, w, h, text, textSize, White, TextAnchor.MiddleCenter, true, true, true);
        }

        public static bool Toggle(float x, float y, float w, float h, string label, bool value)
        {
            Label(x, y, w - 170, h, label, 28, White, TextAnchor.MiddleLeft);
            string text = value ? App.Loc.Get("settings.on") : App.Loc.Get("settings.off");
            if (Button(x + w - 160, y + (h - 80) / 2, 160, 80, text, value ? Tone.Secondary : Tone.Ghost, true, 26)) return !value;
            return value;
        }

        /// <summary>Stepper slider: big -/+ buttons (touch-friendly) around a bar.</summary>
        public static float Stepper(float x, float y, float w, float h, string label, float value, float step = 0.1f)
        {
            Label(x, y, w * 0.42f, h, label, 28, White, TextAnchor.MiddleLeft);
            float bx = x + w * 0.44f, bw = w * 0.56f;
            if (Button(bx, y + (h - 80) / 2, 90, 80, "−", Tone.Ghost, true, 36)) value -= step;
            Bar(bx + 100, y + h / 2 - 18, bw - 200, 36, value, Teal, Mathf.RoundToInt(value * 100) + "%", 22);
            if (Button(bx + bw - 90, y + (h - 80) / 2, 90, 80, "+", Tone.Ghost, true, 36)) value += step;
            return Mathf.Clamp01(Mathf.Round(value * 20f) / 20f);
        }

        public static Color ElementColor(Sim.Content.Element e)
        {
            switch (e)
            {
                case Sim.Content.Element.Fire: return new Color(1f, 0.42f, 0.22f);
                case Sim.Content.Element.Water: return new Color(0.25f, 0.62f, 1f);
                case Sim.Content.Element.Lightning: return new Color(0.78f, 0.5f, 1f);
                case Sim.Content.Element.Ice: return new Color(0.6f, 0.9f, 1f);
                case Sim.Content.Element.Wind: return new Color(0.35f, 0.9f, 0.65f);
                case Sim.Content.Element.Earth: return new Color(0.85f, 0.62f, 0.32f);
                default: return new Color(0.92f, 0.92f, 0.95f);
            }
        }

        public static string RarityKey(Sim.Content.Rarity r) => r.ToString().ToLowerInvariant();

        public static Color RarityColor(Sim.Content.Rarity r)
        {
            switch (r)
            {
                case Sim.Content.Rarity.Rare: return new Color(0.4f, 0.68f, 1f);
                case Sim.Content.Rarity.Epic: return new Color(0.75f, 0.55f, 1f);
                case Sim.Content.Rarity.Legendary: return new Color(1f, 0.78f, 0.25f);
                case Sim.Content.Rarity.Cursed: return new Color(1f, 0.35f, 0.42f);
                default: return new Color(0.78f, 0.8f, 0.86f);
            }
        }
    }
}
