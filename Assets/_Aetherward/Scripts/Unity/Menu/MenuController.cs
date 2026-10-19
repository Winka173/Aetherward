using System;
using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using Aetherward.Sim.Meta;
using Aetherward.Sim.Run;
using UnityEngine;

namespace Aetherward.Game
{
    /// <summary>Main menu, starting-team selection, codex, run history and settings.</summary>
    public sealed class MenuController : MonoBehaviour
    {
        private enum Page
        {
            Main,
            Team,
            Codex,
            History,
            Settings
        }

        private Page _page = Page.Main;
        private readonly List<string> _picked = new List<string>();
        private string _focusHero;
        private Element _teamFilter = Element.None;
        private int _teamPage;
        private ulong _seed;
        private int _ascension;
        private int _biomeIndex;
        private GameMode _mode = GameMode.Classic;
        private bool _hasSave;
        private int _codexTab;
        private int _codexPage;
        private string _codexFocus;
        private float _historyScroll;
        private Transform _backdrop;

        private void Start()
        {
            Camera cam = GameRoot.EnsureCamera(new Color(0.12f, 0.2f, 0.18f));
            cam.orthographicSize = 6.2f;
            _backdrop = BuildBackdrop();
            _backdrop.SetParent(transform, false);
            App.Audio.PlayMusic("menu_loop");
            _hasSave = App.HasSavedRun;
            _seed = Pcg32.SeedFromTime(DateTime.UtcNow);
            _ascension = 0;
        }

        private static Transform BuildBackdrop()
        {
            var root = new GameObject("MenuBackdrop").transform;
            Sr(root, "World/arena_background", Vector3.zero, 1f, -100);
            Sr(root, "World/crystal_intact", new Vector3(0, -0.5f, 0), 1.2f, 10);
            string[] show = { "ignis", "marina", "terra", "volt", "freya", "sylph" };
            Vector3[] pos = { new Vector3(-4.2f, -1.4f), new Vector3(4.2f, -1.4f), new Vector3(-2.4f, -2.6f), new Vector3(2.4f, -2.6f), new Vector3(-6f, -0.4f), new Vector3(6f, -0.4f) };
            for (int i = 0; i < show.Length; i++)
            {
                var r = Sr(root, "Heroes/" + show[i] + "_idle", pos[i], 1.05f, 20 - (int)(pos[i].y * 2));
                r.flipX = pos[i].x > 0;
                r.gameObject.AddComponent<IdleBob>().Phase = i * 0.7f;
            }
            return root;
        }

        private static SpriteRenderer Sr(Transform parent, string sprite, Vector3 pos, float scale, int order)
        {
            var go = new GameObject(sprite);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos;
            go.transform.localScale = Vector3.one * scale;
            var r = go.AddComponent<SpriteRenderer>();
            r.sprite = Art.Sprite(sprite);
            r.sortingOrder = order;
            return r;
        }

        private void Update()
        {
            if (_backdrop != null) _backdrop.position = new Vector3(Mathf.Sin(Time.time * 0.07f) * 0.4f, Mathf.Sin(Time.time * 0.05f) * 0.2f, 0);
            if (Input.GetKeyDown(KeyCode.Escape))
            {
                if (_page != Page.Main) _page = Page.Main;
            }
        }

        private void OnGUI()
        {
            Ui.Begin();
            switch (_page)
            {
                case Page.Main: DrawMain(); break;
                case Page.Team: DrawTeam(); break;
                case Page.Codex: DrawCodex(); break;
                case Page.History: DrawHistory(); break;
                case Page.Settings:
                    Ui.DrawRect(0, 0, Ui.W, Ui.H, new Color(0, 0, 0, 0.45f));
                    if (SharedPanels.Settings(Ui.W / 2 - 560, 60, 1120, 960)) _page = Page.Main;
                    break;
            }
        }

        // ------------------------------------------------------------------ main

        private void DrawMain()
        {
            var l = App.Loc;
            Ui.DrawRect(0, 0, Ui.W, Ui.H, new Color(0.04f, 0.05f, 0.12f, 0.35f));
            Ui.Icon(Ui.W / 2 - 420, 40, 840, 262, Art.Tex("UI/title_emblem"));
            Ui.Label(0, 150, Ui.W, 140, l.Get("game.title"), 112, Ui.Gold, TextAnchor.MiddleCenter, true);
            Ui.Label(0, 286, Ui.W, 50, l.Get("game.tagline"), 32, Ui.White, TextAnchor.MiddleCenter);
            float bw = 520, bh = 100, bx = Ui.W / 2 - bw / 2, by = 390;
            if (_hasSave)
            {
                if (Ui.Button(bx, by, bw, bh, l.Get("menu.continue"), Tone.Primary, true, 36)) ContinueRun();
                by += bh + 18;
            }
            if (Ui.Button(bx, by, bw, bh, l.Get("menu.new_run"), _hasSave ? Tone.Secondary : Tone.Primary, true, 36))
            {
                _picked.Clear();
                _focusHero = null;
                _seed = Pcg32.SeedFromTime(DateTime.UtcNow);
                _page = Page.Team;
            }
            by += bh + 18;
            if (Ui.Button(bx, by, bw / 2 - 9, bh, l.Get("menu.codex"), Tone.Ghost, true, 30)) _page = Page.Codex;
            if (Ui.Button(bx + bw / 2 + 9, by, bw / 2 - 9, bh, l.Get("menu.history"), Tone.Ghost, true, 30)) _page = Page.History;
            by += bh + 18;
            if (Ui.Button(bx, by, Application.isMobilePlatform ? bw : bw / 2 - 9, bh, l.Get("menu.settings"), Tone.Ghost, true, 30)) _page = Page.Settings;
            if (!Application.isMobilePlatform && Ui.Button(bx + bw / 2 + 9, by, bw / 2 - 9, bh, l.Get("menu.quit"), Tone.Danger, true, 30)) Application.Quit();
            MetaProfile m = App.Meta;
            Ui.Label(0, Ui.H - 90, Ui.W, 40, l.Format("menu.stats", m.TotalRuns, m.Victories, m.BestWave), 24, Ui.Muted, TextAnchor.MiddleCenter);
            Ui.Label(0, Ui.H - 52, Ui.W - 30, 36, l.Format("menu.version", App.Version), 20, Ui.Muted, TextAnchor.MiddleRight);
            if (App.SaveWasReset) Ui.Label(0, Ui.H - 140, Ui.W, 40, l.Get("menu.save_reset"), 22, Ui.Bad, TextAnchor.MiddleCenter);
        }

        private void ContinueRun()
        {
            if (App.ResumeRun() != null) GameRoot.Instance.GoTo(AppScreen.Battle);
            else _hasSave = false;
        }

        // ------------------------------------------------------------------ team select

        private void DrawTeam()
        {
            var l = App.Loc;
            ContentDatabase db = App.Content;
            Ui.DrawRect(0, 0, Ui.W, Ui.H, new Color(0.04f, 0.05f, 0.12f, 0.7f));
            Ui.Label(60, 30, Ui.W - 120, 70, l.Get("team.title"), 50, Ui.Gold, TextAnchor.UpperLeft, true);
            Ui.Label(60, 96, Ui.W - 120, 40, l.Get("team.subtitle"), 26, Ui.Muted);
            // Element filter chips (All + 12 elements) and a paged grid: scales to the full 36-hero roster.
            float gx = 60, gy = 150, cell = 124;
            int cols = 5;
            float chip = 52;
            if (Ui.Button(gx, gy, 92, chip, l.Get("team.filter_all"), _teamFilter == Element.None ? Tone.Secondary : Tone.Ghost, true, 20))
            {
                _teamFilter = Element.None;
                _teamPage = 0;
            }
            for (int k = 0; k < ElementUtil.All.Length; k++)
            {
                Element el = ElementUtil.All[k];
                float cx = gx + 100 + k * (chip + 4);
                if (_teamFilter == el) Ui.DrawRect(cx - 3, gy - 3, chip + 6, chip + 6, new Color(1f, 0.83f, 0.35f, 0.8f));
                Ui.Icon(cx, gy, chip, chip, Art.ElementIcon(el));
                if (Ui.Hit(cx, gy, chip, chip))
                {
                    _teamFilter = _teamFilter == el ? Element.None : el;
                    _teamPage = 0;
                }
            }
            var shown = new List<HeroDef>();
            foreach (HeroDef h in db.HeroList) if (_teamFilter == Element.None || h.Element == _teamFilter) shown.Add(h);
            float top = gy + chip + 18;
            int rows = Mathf.Max(1, Mathf.FloorToInt((Ui.H - 170 - top) / (cell + 40)));
            int perPage = rows * cols;
            int pages = Mathf.Max(1, (shown.Count + perPage - 1) / perPage);
            _teamPage = Mathf.Clamp(_teamPage, 0, pages - 1);
            for (int n = 0; n < perPage; n++)
            {
                int i = _teamPage * perPage + n;
                if (i >= shown.Count) break;
                HeroDef h = shown[i];
                float x = gx + (n % cols) * (cell + 14), y = top + (n / cols) * (cell + 40);
                bool unlocked = App.Meta.UnlockedHeroes.Contains(h.Id);
                bool picked = _picked.Contains(h.Id);
                if (picked) Ui.DrawRect(x - 6, y - 6, cell + 12, cell + 12, new Color(1f, 0.83f, 0.35f, 0.8f));
                else if (_focusHero == h.Id) Ui.DrawRect(x - 4, y - 4, cell + 8, cell + 8, new Color(0.5f, 0.8f, 1f, 0.45f));
                Ui.Icon(x, y, cell, cell, Art.Portrait(h.Id), unlocked ? (Color?)null : new Color(0.3f, 0.3f, 0.35f, 1f));
                Ui.Icon(x + cell - 40, y + cell - 40, 40, 40, Art.ElementIcon(h.Element));
                Ui.Label(x - 8, y + cell + 2, cell + 16, 36, l.Get(h.NameKey), 22, unlocked ? Ui.White : Ui.Muted, TextAnchor.UpperCenter, true);
                if (!unlocked) Ui.Icon(x + cell / 2 - 26, y + cell / 2 - 26, 52, 52, Art.Icon("lock"));
                if (Ui.Hit(x, y, cell, cell + 36))
                {
                    _focusHero = h.Id;
                    if (unlocked)
                    {
                        if (picked) _picked.Remove(h.Id);
                        else if (_picked.Count < 2) _picked.Add(h.Id);
                        else
                        {
                            _picked.RemoveAt(0);
                            _picked.Add(h.Id);
                        }
                    }
                }
            }
            if (pages > 1)
            {
                float py = top + rows * (cell + 40) - 6;
                if (Ui.Button(gx, py, 90, 56, "<", Tone.Ghost, _teamPage > 0, 26)) _teamPage--;
                Ui.Label(gx + 100, py, 200, 56, (_teamPage + 1) + " / " + pages, 24, Ui.Muted, TextAnchor.MiddleCenter, false, true, true);
                if (Ui.Button(gx + 310, py, 90, 56, ">", Tone.Ghost, _teamPage < pages - 1, 26)) _teamPage++;
            }
            float dx = gx + cols * (cell + 16) + 30, dw = Ui.W - dx - 60;
            string focus = _focusHero ?? (_picked.Count > 0 ? _picked[_picked.Count - 1] : db.HeroList[0].Id);
            HeroDef fd = db.Heroes[focus];
            SharedPanels.HeroDetail(dx, 150, dw, 690, fd);
            if (!App.Meta.UnlockedHeroes.Contains(focus))
                Ui.Label(dx + 30, 150 + 640, dw - 60, 40, SharedPanels.UnlockHint("hero:" + focus), 24, Ui.Bad);

            float by = Ui.H - 140;
            DrawModePicker(dx, by - 176, dw);
            if (_mode != GameMode.Daily) DrawBiomePicker(dx, by - 92, dw);
            if (Ui.Button(60, by, 240, 96, l.Get("common.back"), Tone.Ghost)) _page = Page.Main;
            Ui.Label(330, by, 420, 46, l.Format("common.seed", Pcg32.FormatSeed(_seed)), 26, Ui.Muted, TextAnchor.MiddleLeft, false, true, true);
            if (Ui.Button(330, by + 46, 300, 60, l.Get("team.random_seed"), Tone.Ghost, true, 22)) _seed = Pcg32.SeedFromTime(DateTime.UtcNow.AddTicks(UnityEngine.Random.Range(1, 99999)));
            int maxAsc = App.Meta.MaxAscensionUnlocked;
            if (maxAsc > 0)
            {
                float ax = 680;
                if (Ui.Button(ax, by + 8, 80, 80, "−", Tone.Ghost, _ascension > 0, 34)) _ascension--;
                Ui.Label(ax + 90, by, 300, 50, _ascension == 0 ? l.Get("team.ascension_none") : l.Format("team.ascension", _ascension), 28, Ui.Gold, TextAnchor.MiddleCenter, true);
                Ui.Label(ax + 90, by + 46, 300, 50, l.Get("team.ascension_desc." + Mathf.Min(_ascension, App.Content.Difficulty.MaxLevel)), 18, Ui.Muted, TextAnchor.UpperCenter);
                if (Ui.Button(ax + 400, by + 8, 80, 80, "+", Tone.Ghost, _ascension < maxAsc, 34)) _ascension++;
            }
            bool ready = _picked.Count == 2;
            if (Ui.Button(Ui.W - 480, by, 420, 96, ready ? l.Get("team.start") : l.Get("team.pick_two"), Tone.Primary, ready, 32))
            {
                App.ClearRun();
                App.Run = RunController.NewModeRun(App.Content, ModeUnlocked(_mode) ? _mode : GameMode.Classic, _seed, _picked, _ascension,
                                                   App.Meta.ToRunUnlocks(), SelectedBiome().Id);
                App.SaveRun();
                GameRoot.Instance.GoTo(AppScreen.Battle);
            }
        }

        /// <summary>Endless after a first victory, Boss Rush after beating a wave-10 boss; Daily always.</summary>
        private static bool ModeUnlocked(GameMode m) =>
            m == GameMode.Classic || m == GameMode.Daily || (m == GameMode.Endless ? App.Meta.Victories > 0 : App.Meta.BestWave >= 11);

        private void DrawModePicker(float x, float y, float w)
        {
            Localization l = App.Loc;
            int count = System.Enum.GetValues(typeof(GameMode)).Length;
            if (Ui.Button(x, y, 64, 64, "<", Tone.Ghost, (int)_mode > 0, 28)) _mode--;
            string key = _mode.ToString().ToLowerInvariant();
            bool unlocked = ModeUnlocked(_mode);
            Ui.Label(x + 76, y - 4, w - 160, 36, l.Get("mode.label") + ": " + l.Get("mode." + key + ".name"), 22, unlocked ? Ui.Gold : Ui.Muted, TextAnchor.UpperLeft, true);
            string sub = unlocked ? l.Get("mode." + key + ".desc") : l.Get("mode." + key + ".locked");
            App.Meta.ModeRecords.TryGetValue(_mode == GameMode.Daily ? "daily:" + RunController.DailyKeyFor(DateTime.UtcNow) : key, out int best);
            if (unlocked && best > 0) sub += "  " + l.Format("mode.best", best);
            Ui.Label(x + 76, y + 28, w - 160, 40, sub, 15, unlocked ? Ui.Muted : Ui.Bad, TextAnchor.UpperLeft);
            if (Ui.Button(x + w - 64, y, 64, 64, ">", Tone.Ghost, (int)_mode < count - 1, 28)) _mode++;
        }

        private BiomeDef SelectedBiome()
        {
            List<BiomeDef> list = App.Content.BiomeList;
            _biomeIndex = Mathf.Clamp(_biomeIndex, 0, list.Count - 1);
            BiomeDef b = list[_biomeIndex];
            return App.Meta.UnlockedBiomes.Contains(b.Id) ? b : App.Content.DefaultBiome;
        }

        /// <summary>Battlefield selector: cycles through biomes; locked ones show their unlock condition.</summary>
        private void DrawBiomePicker(float x, float y, float w)
        {
            Localization l = App.Loc;
            List<BiomeDef> list = App.Content.BiomeList;
            if (list.Count < 2) return;
            _biomeIndex = Mathf.Clamp(_biomeIndex, 0, list.Count - 1);
            BiomeDef b = list[_biomeIndex];
            bool unlocked = App.Meta.UnlockedBiomes.Contains(b.Id);
            if (Ui.Button(x, y, 64, 64, "<", Tone.Ghost, _biomeIndex > 0, 28)) _biomeIndex--;
            Ui.Icon(x + 72, y, 112, 64, Art.Tex(b.Background), unlocked ? (Color?)null : new Color(0.3f, 0.3f, 0.35f, 1f));
            string title = l.Get("biome.label") + ": " + l.Get(b.NameKey);
            Ui.Label(x + 196, y - 4, w - 280, 36, title, 22, unlocked ? Ui.Gold : Ui.Muted, TextAnchor.UpperLeft, true);
            string sub = unlocked ? l.Get(b.DescKey) : SharedPanels.UnlockHint("biome:" + b.Id);
            Ui.Label(x + 196, y + 28, w - 280, 40, sub, 15, unlocked ? Ui.Muted : Ui.Bad, TextAnchor.UpperLeft);
            if (Ui.Button(x + w - 64, y, 64, 64, ">", Tone.Ghost, _biomeIndex < list.Count - 1, 28)) _biomeIndex++;
        }

        // ------------------------------------------------------------------ codex

        private void DrawCodex()
        {
            var l = App.Loc;
            ContentDatabase db = App.Content;
            MetaProfile m = App.Meta;
            Ui.DrawRect(0, 0, Ui.W, Ui.H, new Color(0.04f, 0.05f, 0.12f, 0.8f));
            Ui.Label(60, 30, 600, 70, l.Get("codex.title"), 50, Ui.Gold, TextAnchor.UpperLeft, true);
            string[] tabs = { "codex.heroes", "codex.reactions", "codex.relics", "codex.enemies", "codex.matrix" };
            for (int i = 0; i < tabs.Length; i++)
                if (Ui.Button(60 + i * 210, 110, 200, 80, l.Get(tabs[i]), _codexTab == i ? Tone.Secondary : Tone.Ghost, true, 24))
                {
                    _codexTab = i;
                    _codexFocus = null;
                    _codexPage = 0;
                }
            if (_codexTab == 4)
            {
                DrawReactionMatrix();
                if (Ui.Button(60, Ui.H - 130, 240, 96, l.Get("common.back"), Tone.Ghost)) _page = Page.Main;
                return;
            }
            var entries = new List<(string id, string key, Texture tex, bool known)>();
            if (_codexTab == 0)
                foreach (HeroDef h in db.HeroList) entries.Add((h.Id, h.NameKey, Art.Portrait(h.Id), m.Codex.Contains("hero:" + h.Id) || m.UnlockedHeroes.Contains(h.Id)));
            else if (_codexTab == 1)
                foreach (ReactionDef r in db.Reactions.Values) entries.Add((r.Id, r.NameKey, Art.Tex(BattleController.ReactionIcon(r.Id)), m.Codex.Contains("reaction:" + r.Id)));
            else if (_codexTab == 2)
                foreach (RelicDef r in db.RelicList) entries.Add((r.Id, r.NameKey, Art.Tex("Relics/" + r.Id), m.Codex.Contains("relic:" + r.Id)));
            else
                foreach (EnemyDef e in db.Enemies.Values) entries.Add((e.Id, e.NameKey, Art.Tex("Enemies/" + e.Id + "_a"), m.Codex.Contains("enemy:" + e.Id)));
            int known = 0;
            foreach (var e in entries) if (e.known) known++;
            Ui.Label(1100, 120, Ui.W - 1160, 60, l.Format("codex.progress", known, entries.Count), 26, Ui.Muted, TextAnchor.MiddleRight);
            float cell = 120, gx = 60, gy = 220;
            int cols = 7;
            int rows = Mathf.Max(1, Mathf.FloorToInt((Ui.H - 170 - gy) / (cell + 14)));
            int perPage = rows * cols, pages = Mathf.Max(1, (entries.Count + perPage - 1) / perPage);
            _codexPage = Mathf.Clamp(_codexPage, 0, pages - 1);
            if (pages > 1)
            {
                float py = gy + rows * (cell + 14);
                if (Ui.Button(330, py, 90, 56, "<", Tone.Ghost, _codexPage > 0, 26)) _codexPage--;
                Ui.Label(430, py, 160, 56, (_codexPage + 1) + " / " + pages, 24, Ui.Muted, TextAnchor.MiddleCenter, false, true, true);
                if (Ui.Button(600, py, 90, 56, ">", Tone.Ghost, _codexPage < pages - 1, 26)) _codexPage++;
            }
            for (int n = 0; n < perPage; n++)
            {
                int i = _codexPage * perPage + n;
                if (i >= entries.Count) break;
                var e = entries[i];
                float x = gx + (n % cols) * (cell + 14), y = gy + (n / cols) * (cell + 14);
                Ui.DrawRect(x, y, cell, cell, _codexFocus == e.id ? new Color(1f, 0.83f, 0.35f, 0.5f) : new Color(0.15f, 0.17f, 0.3f, 0.85f));
                Ui.Icon(x + 8, y + 8, cell - 16, cell - 16, e.tex, e.known ? (Color?)null : new Color(0, 0, 0, 0.85f));
                if (Ui.Hit(x, y, cell, cell)) _codexFocus = e.id;
            }
            float dx = gx + cols * (cell + 14) + 20, dw = Ui.W - dx - 60;
            if (_codexFocus != null)
            {
                var entry = entries.Find(e => e.id == _codexFocus);
                if (entry.id != null)
                {
                    if (!entry.known)
                    {
                        Ui.Panel(dx, 220, dw, 300);
                        Ui.Label(dx, 300, dw, 80, l.Get("codex.undiscovered"), 36, Ui.Muted, TextAnchor.MiddleCenter, true);
                    }
                    else if (_codexTab == 0) SharedPanels.HeroDetail(dx, 220, dw, 700, db.Heroes[entry.id]);
                    else DrawCodexEntry(dx, 220, dw, entry.id, entry.tex);
                }
            }
            else if (_codexTab == 1)
            {
                Ui.Panel(dx, 220, dw, 360);
                Ui.Label(dx + 30, 250, dw - 60, 320, l.Get("codex.reaction_formula"), 24, Ui.White);
            }
            if (Ui.Button(60, Ui.H - 130, 240, 96, l.Get("common.back"), Tone.Ghost)) _page = Page.Main;
        }

        /// <summary>
        /// 12×12 element matrix: every pair's category (signature / generic / neutral / blocked), the
        /// signature icon once discovered, and details for the focused pair.
        /// </summary>
        private void DrawReactionMatrix()
        {
            var l = App.Loc;
            ContentDatabase db = App.Content;
            Element[] els = ElementUtil.All;
            float cell = Mathf.Min(58f, (Ui.H - 330f) / (els.Length + 1)), gx = 60, gy = 220;
            for (int i = 0; i < els.Length; i++)
            {
                Ui.Icon(gx + (i + 1) * cell + 4, gy + 4, cell - 8, cell - 8, Art.ElementIcon(els[i]));
                Ui.Icon(gx + 4, gy + (i + 1) * cell + 4, cell - 8, cell - 8, Art.ElementIcon(els[i]));
            }
            ReactionDef focus = null;
            for (int r = 0; r < els.Length; r++)
                for (int c = 0; c < els.Length; c++)
                {
                    float x = gx + (c + 1) * cell, y = gy + (r + 1) * cell;
                    if (r == c) { Ui.DrawRect(x + 2, y + 2, cell - 4, cell - 4, new Color(0.08f, 0.08f, 0.12f, 0.9f)); continue; }
                    ReactionDef rd = db.ReactionFor(els[r], els[c]);
                    bool known = rd != null && App.Meta.Codex.Contains("reaction:" + rd.Id);
                    Color col = rd == null ? new Color(0.1f, 0.1f, 0.14f, 0.9f)
                        : rd.Category == ReactionCategory.Signature ? new Color(0.55f, 0.42f, 0.12f, 0.95f)
                        : rd.Category == ReactionCategory.Generic ? new Color(0.25f, 0.27f, 0.36f, 0.95f)
                        : rd.Category == ReactionCategory.Neutral ? new Color(0.14f, 0.16f, 0.2f, 0.95f)
                        : new Color(0.4f, 0.12f, 0.14f, 0.95f);
                    bool hover = _codexFocus == "pair:" + r + ":" + c;
                    Ui.DrawRect(x + 2, y + 2, cell - 4, cell - 4, hover ? new Color(1f, 0.83f, 0.35f, 0.9f) : col);
                    if (rd != null && rd.Category == ReactionCategory.Signature)
                        Ui.Icon(x + 6, y + 6, cell - 12, cell - 12, Art.Tex(BattleController.ReactionIcon(rd.Id)), known ? (Color?)null : new Color(0, 0, 0, 0.75f));
                    if (Ui.Hit(x, y, cell, cell)) _codexFocus = "pair:" + r + ":" + c;
                    if (hover) focus = rd;
                }
            float dx = gx + (els.Length + 1) * cell + 30, dw = Ui.W - dx - 60;
            Ui.Panel(dx, gy, dw, 520);
            if (focus == null)
            {
                Ui.Label(dx + 30, gy + 30, dw - 60, 460, l.Get("codex.matrix_help"), 24, Ui.White);
                return;
            }
            bool seen = App.Meta.Codex.Contains("reaction:" + focus.Id);
            Ui.Label(dx + 30, gy + 30, dw - 60, 50, seen || focus.Category != ReactionCategory.Signature ? l.ReactionName(focus.Id) : l.Get("codex.undiscovered"), 32, Ui.Gold, TextAnchor.UpperLeft, true);
            Ui.Label(dx + 30, gy + 84, dw - 60, 40, l.Element(focus.A) + " + " + l.Element(focus.B) + " · " + l.Get("codex.category." + focus.Category.ToString().ToLowerInvariant()), 22, Ui.Muted);
            if (seen || focus.Category != ReactionCategory.Signature)
                Ui.Label(dx + 30, gy + 134, dw - 60, 360, ContentValidator.ReactionText(l, focus), 22, Ui.White);
        }

        private void DrawCodexEntry(float x, float y, float w, string id, Texture tex)
        {
            var l = App.Loc;
            ContentDatabase db = App.Content;
            Ui.Panel(x, y, w, 640);
            Ui.Icon(x + 30, y + 30, 160, 160, tex);
            string title, body;
            if (_codexTab == 1)
            {
                ReactionDef r = db.Reactions[id];
                title = l.ReactionName(id);
                body = l.Element(r.A) + " + " + l.Element(r.B) + "\n\n" + ContentValidator.ReactionText(l, r);
            }
            else if (_codexTab == 2)
            {
                RelicDef r = db.Relics[id];
                title = l.Get(r.NameKey);
                body = l.Rarity(r.Rarity) + " · " + l.Get("family." + r.Family.ToString().ToLowerInvariant()) + "\n<i>" + l.Get(r.DescKey) + "</i>\n\n" +
                       EffectDescriber.Join(App.Fx.Describe(r.Effects));
            }
            else
            {
                EnemyDef e = db.Enemies[id];
                title = l.Get(e.NameKey);
                body = l.Get(e.DescKey);
            }
            Ui.Label(x + 210, y + 40, w - 240, 60, title, 40, Ui.Gold, TextAnchor.UpperLeft, true);
            Ui.Label(x + 30, y + 220, w - 60, 400, body, 24, Ui.White);
        }

        // ------------------------------------------------------------------ history

        private void DrawHistory()
        {
            var l = App.Loc;
            Ui.DrawRect(0, 0, Ui.W, Ui.H, new Color(0.04f, 0.05f, 0.12f, 0.8f));
            Ui.Label(60, 30, 800, 70, l.Get("history.title"), 50, Ui.Gold, TextAnchor.UpperLeft, true);
            List<RunHistoryEntry> hist = App.Meta.History;
            if (hist.Count == 0) Ui.Label(60, 160, Ui.W - 120, 60, l.Get("history.empty"), 30, Ui.Muted);
            float y = 140 - _historyScroll;
            foreach (RunHistoryEntry h in hist)
            {
                if (y > 120 && y < Ui.H - 220)
                {
                    Ui.Panel(60, y, Ui.W - 120, 110, h.Victory ? "glass" : "dark");
                    Ui.Label(90, y + 14, 260, 40, h.Victory ? l.Get("results.victory") : l.Get("results.defeat"), 30, h.Victory ? Ui.Good : Ui.Bad, TextAnchor.UpperLeft, true);
                    Ui.Label(90, y + 56, 400, 40, l.Format("results.seed", h.Seed, h.Version), 20, Ui.Muted);
                    string mvp = h.Mvp != null ? l.Get("hero." + h.Mvp + ".name") : "-";
                    Ui.Label(380, y + 14, 900, 40, l.Format("history.row", DateTimeOffset.FromUnixTimeSeconds(h.UnixTime).ToLocalTime().ToString("yyyy-MM-dd"), h.Wave, h.Reactions, mvp), 24, Ui.White);
                    float hx = 380;
                    foreach (string hero in h.Heroes)
                    {
                        Ui.Icon(hx, y + 54, 48, 48, Art.Portrait(hero));
                        hx += 52;
                    }
                }
                y += 124;
            }
            float maxScroll = Mathf.Max(0, hist.Count * 124 - (Ui.H - 380));
            if (Ui.Button(Ui.W - 300, Ui.H - 130, 110, 96, "▲", Tone.Ghost, _historyScroll > 0)) _historyScroll = Mathf.Max(0, _historyScroll - 372);
            if (Ui.Button(Ui.W - 180, Ui.H - 130, 110, 96, "▼", Tone.Ghost, _historyScroll < maxScroll)) _historyScroll = Mathf.Min(maxScroll, _historyScroll + 372);
            if (Ui.Button(60, Ui.H - 130, 240, 96, l.Get("common.back"), Tone.Ghost)) _page = Page.Main;
        }
    }

    /// <summary>Gentle idle bob and breathing squash for decorative sprites.</summary>
    public sealed class IdleBob : MonoBehaviour
    {
        public float Phase;
        private Vector3 _basePos;
        private Vector3 _baseScale;

        private void Start()
        {
            _basePos = transform.localPosition;
            _baseScale = transform.localScale;
        }

        private void Update()
        {
            float t = Time.time * 2.2f + Phase;
            transform.localPosition = _basePos + new Vector3(0, Mathf.Abs(Mathf.Sin(t)) * 0.06f, 0);
            float s = Mathf.Sin(t * 2f) * 0.015f;
            transform.localScale = new Vector3(_baseScale.x * (1f - s), _baseScale.y * (1f + s), 1f);
        }
    }
}
