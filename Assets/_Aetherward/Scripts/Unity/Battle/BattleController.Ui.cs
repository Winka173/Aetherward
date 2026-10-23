using System.Collections.Generic;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Run;
using UnityEngine;

namespace Aetherward.Game
{
    public sealed partial class BattleController
    {
        private bool _modalOpen;
        private bool _pauseConfirm;
        private bool _showSettings;
        private bool _showBuild;
        private int _focusOffer = -1;
        private int _pactPending = -1;
        private int _heroInfoUid = -1;
        private string _buildFocus;

        private Localization L => App.Loc;

        private void Block(float x, float y, float w, float h)
        {
            if (Event.current.type == EventType.Repaint) _uiBlockersNext.Add(Ui.R(x, y, w, h));
        }

        private void OnGUI()
        {
            if (_rc == null) return;
            if (Event.current.type == EventType.Repaint) _uiBlockersNext.Clear();
            Ui.Begin();
            GUI.depth = 0;
            RunState s = _rc.State;
            _offersChanged = false;
            bool evolveOpen = s.Phase == RunPhase.Prepare && _evolveHero >= 0;
            bool prevEnabled = GUI.enabled;
            // Everything under an open overlay is drawn but not clickable.
            GUI.enabled = prevEnabled && !(evolveOpen || _showBuild || _paused || _showSettings);
            _text.Draw(_cam);
            DrawTopBar();
            if (s.Phase == RunPhase.Battle && _rc.Battle != null)
            {
                DrawBossBar();
                DrawHeroDock(true);
                if (_rc.Battle.Pillagers > 0)
                    Ui.Label(0, 140, Ui.W, 64, L.Format("hud.pillage", _rc.Battle.Pillagers), 36, Ui.Bad, TextAnchor.MiddleCenter, true);
                DrawBattleControls();
                DrawTutorial();
            }
            else if (s.Phase == RunPhase.Prepare)
            {
                DrawPrepare();
            }
            _modalOpen = s.Phase == RunPhase.Reward;
            if (s.Phase == RunPhase.Reward) DrawReward();
            DrawBanner();
            DrawToasts();
            GUI.enabled = prevEnabled && !(_showBuild || _paused || _showSettings);
            if (evolveOpen) DrawEvolveModal(_evolveHero, false);
            GUI.enabled = prevEnabled && !(_paused || _showSettings);
            if (_showBuild) DrawBuild();
            GUI.enabled = prevEnabled;
            if (_paused && !_showSettings) DrawPause();
            if (_showSettings)
            {
                Ui.DrawRect(0, 0, Ui.W, Ui.H, new Color(0, 0, 0, 0.5f));
                Block(0, 0, Ui.W, Ui.H);
                if (SharedPanels.Settings(Ui.W / 2 - 560, 60, 1120, 960)) _showSettings = false;
            }
        }

        // ------------------------------------------------------------------ HUD

        private void DrawTopBar()
        {
            RunState s = _rc.State;
            bool battle = s.Phase == RunPhase.Battle && _rc.Battle != null;
            float crystalHp = battle ? _rc.Battle.Crystal.Hp : s.CrystalHp;
            float crystalMax = battle ? _rc.Battle.Crystal.MaxHp : _rc.CrystalMaxHp;
            float shield = battle ? _rc.Battle.Crystal.Shield : 0f;
            Ui.Panel(16, 12, 640, 128, "glass");
            Block(16, 12, 640, 128);
            Ui.Icon(30, 22, 64, 64, Art.Icon("crystal"));
            Ui.Label(104, 20, 300, 36, L.Get("hud.crystal"), 22, Ui.Muted, TextAnchor.UpperLeft, true);
            Ui.Bar(104, 52, 520, 34, crystalHp / Mathf.Max(1f, crystalMax), Color.Lerp(Ui.Bad, new Color(0.45f, 0.9f, 1f), crystalHp / Mathf.Max(1f, crystalMax)),
                Mathf.CeilToInt(crystalHp) + " / " + Mathf.CeilToInt(crystalMax) + (shield > 1f ? "  +" + Mathf.CeilToInt(shield) : ""), 22);
            Ui.Icon(30, 92, 40, 40, Art.Icon("gold"));
            Ui.Label(76, 92, 140, 40, s.Gold.ToString(), 30, Ui.Gold, TextAnchor.MiddleLeft, true, true, true);
            Ui.Icon(200, 92, 40, 40, Art.Icon("essence"));
            Ui.Label(246, 92, 120, 40, s.Essence.ToString(), 30, new Color(0.8f, 0.65f, 1f), TextAnchor.MiddleLeft, true, true, true);
            Ui.Label(360, 92, 280, 40, L.Format("common.seed", Sim.Core.Pcg32.FormatSeed(s.Seed)), 18, Ui.Muted, TextAnchor.MiddleRight);

            int total = _rc.TotalWaves;
            int wave = total > 0 ? Mathf.Min(s.Wave, total) : s.Wave;
            WaveDef w = _rc.WaveAt(wave);
            string totalText = total > 0 ? total.ToString() : "∞";
            Ui.Panel(Ui.W / 2 - 300, 12, 600, battle ? 118 : 96, "glass");
            Block(Ui.W / 2 - 300, 12, 600, 96);
            Ui.Label(Ui.W / 2 - 300, 20, 600, 46, L.Format("hud.wave", wave) + "  <size=" + Ui.Px(24) + "><color=#c0c8e8>/ " + total + "</color></size>", 38, Ui.Gold, TextAnchor.UpperCenter, true);
            Ui.Label(Ui.W / 2 - 300, 62, 600, 34, L.Get(w.NameKey), 24, Ui.White, TextAnchor.UpperCenter);
            if (battle)
            {
                Battle b = _rc.Battle;
                float left = Mathf.Max(0f, w.TimeLimit - b.Time);
                int remaining = b.Enemies.Count + b.RemainingSpawns;
                Ui.Label(Ui.W / 2 - 280, 92, 260, 32, L.Format("hud.enemies", remaining), 20, Ui.Muted, TextAnchor.UpperLeft);
                Ui.Label(Ui.W / 2 + 20, 92, 260, 32, Mathf.CeilToInt(left) + "s", 20, left < 15f ? Ui.Bad : Ui.Muted, TextAnchor.UpperRight, false, true, true);
            }
        }

        private void DrawBattleControls()
        {
            float x = Ui.W - 16 - 3 * 112;
            Block(x - 8, 12, 3 * 112 + 8, 108);
            if (Ui.Button(x, 14, 100, 96, "II", Tone.Ghost, true, 30)) _paused = true;
            if (Ui.Button(x + 112, 14, 100, 96, _speed + "×", _speed == 2 ? Tone.Secondary : Tone.Ghost, true, 32)) _speed = _speed == 1 ? 2 : 1;
            bool vfx = App.Settings.ReducedVfx;
            if (Ui.Button(x + 224, 14, 100, 96, vfx ? "FX-" : "FX", vfx ? Tone.Secondary : Tone.Ghost, true, 24))
            {
                App.Settings.ReducedVfx = !vfx;
                App.SaveSettings();
            }
        }

        private void DrawBossBar()
        {
            foreach (EnemyUnit e in _rc.Battle.Enemies)
            {
                if (!e.IsBoss || !e.Alive) continue;
                float w = Mathf.Min(900, Ui.W - 1400);
                w = Mathf.Max(w, 600);
                float x = Ui.W / 2 - w / 2;
                Ui.Label(x, 136, w, 34, L.Get(e.Def.NameKey) + (e.VulnerableTimer > 0f ? "  · " + L.Get("hud.exposed") : ""), 26,
                    e.VulnerableTimer > 0f ? Ui.Good : Ui.Bad, TextAnchor.UpperCenter, true);
                Ui.Bar(x, 172, w, 30, e.HpFraction, new Color(0.9f, 0.3f, 0.5f), Mathf.CeilToInt(e.Hp) + "", 20);
                break;
            }
        }

        /// <summary>Six portrait slots with HP, skill readiness and level; tap for details.</summary>
        private void DrawHeroDock(bool battle)
        {
            RunState s = _rc.State;
            HeroDef ultimateTip = null;
            int n = Mathf.Max(1, s.Heroes.Count);
            float slot = battle ? 80 : 150, gap = battle ? 8 : 14;
            float total = n * slot + (n - 1) * gap;
            float x0 = Ui.W / 2 - total / 2, y = Ui.H - (battle ? 126 : 196);
            Ui.Panel(x0 - 20, y - 12, total + 40, battle ? 134 : 204, "glass");
            Block(x0 - 20, y - 12, total + 40, battle ? 134 : 204);
            for (int i = 0; i < s.Heroes.Count; i++)
            {
                HeroRunState h = s.Heroes[i];
                HeroDef def = App.Content.Heroes[h.DefId];
                float x = x0 + i * (slot + gap);
                HeroUnit unit = null;
                if (battle && _rc.Battle != null)
                    foreach (HeroUnit u in _rc.Battle.Heroes) if (u.RosterIndex == i) unit = u;
                bool down = unit != null ? !unit.Alive : h.Downed;
                if (_heroInfoUid == h.Uid || _selectedUid == h.Uid) Ui.DrawRect(x - 4, y - 4, slot + 8, slot + 8, new Color(1f, 0.85f, 0.4f, 0.7f));
                Ui.Icon(x, y, slot, slot, Art.Portrait(def.Id), down ? new Color(0.35f, 0.35f, 0.4f) : (Color?)null);
                Ui.Label(x + 6, y + 4, 80, 34, L.Format("common.level", h.Level), 20, Ui.White, TextAnchor.UpperLeft, true);
                if (!string.IsNullOrEmpty(h.EvolutionId)) Ui.Icon(x + slot - 40, y + 4, 36, 36, Art.Icon("evolve"));
                float hp = unit != null ? unit.HpFraction : (h.Downed ? 0f : h.HpFraction);
                Ui.Bar(x, y + slot + 4, slot, 20, hp, Color.Lerp(Ui.Bad, Ui.Good, hp));
                if (unit != null && unit.Alive)
                {
                    float cd = unit.Skill.Cooldown * unit.Stat(StatId.SkillCooldown);
                    float ready = cd > 0 ? 1f - Mathf.Clamp01(unit.SkillTimer / cd) : 1f;
                    Ui.Bar(x, y + slot + 26, slot, 14, ready, ready >= 1f ? Ui.Gold : Ui.ElementColor(def.Element));
                    // ultimate charge: a gold band across the portrait top, pulsing when ready
                    float ult = unit.Ult;
                    Color uc = ult >= 1f ? Color.Lerp(Ui.Gold, Color.white, 0.5f + 0.5f * Mathf.Sin(Time.unscaledTime * 8f)) : new Color(1f, 0.78f, 0.3f, 0.9f);
                    Ui.Bar(x + 4, y + 4, slot - 8, 10, ult, uc);
                }
                if (down) Ui.Label(x, y + slot / 2 - 24, slot, 48, L.Get("hud.downed"), 30, Ui.Bad, TextAnchor.MiddleCenter, true);
                if (def.Ultimate != null && Ui.Hover(x, y, slot, slot)) ultimateTip = def;
                if (Ui.Hit(x, y, slot, slot))
                {
                    if (!battle && s.Phase == RunPhase.Prepare) _selectedUid = _selectedUid == h.Uid ? -1 : h.Uid;
                    _heroInfoUid = _heroInfoUid == h.Uid ? -1 : h.Uid;
                }
            }
            if (ultimateTip != null)
            {
                string title = L.Get("hero." + ultimateTip.Id + ".ultimate.name");
                string body = L.Get("hero." + ultimateTip.Id + ".ultimate.desc");
                float width = 760, height = Ui.TextHeight(body, 21, width - 36) + 65;
                float left = Ui.W / 2 - width / 2, top = y - height - 20;
                Ui.Tooltip(left, top, width, height);
                Ui.Label(left + 18, top + 10, width - 36, 32, title, 24, Ui.Gold, TextAnchor.UpperLeft, true);
                Ui.Label(left + 18, top + 45, width - 36, height - 50, body, 21, Ui.White);
            }
            if (_heroInfoUid >= 0)
            {
                HeroRunState h = s.Hero(_heroInfoUid);
                if (h != null)
                {
                    float pw = 900, ph = 640;
                    float px = Ui.W - pw - 20, py = Ui.H - 220 - ph;
                    Block(px, py, pw, ph);
                    SharedPanels.HeroDetail(px, py, pw, ph, App.Content.Heroes[h.DefId], h.EvolutionId, h.Level, h.TraitId, h.Awakened);
                    int next = h.Level < App.Content.Economy.LevelCap ? App.Content.Economy.XpToLevel[h.Level] : -1;
                    Ui.Label(px + 30, py + ph - 56, 500, 40, next > 0 ? L.Format("prep.xp", h.Xp, next) : L.Get("prep.max_level"), 22, Ui.Muted);
                    if (Ui.Button(px + pw - 200, py + ph - 100, 170, 80, L.Get("common.close"), Tone.Ghost, true, 24)) _heroInfoUid = -1;
                }
            }
        }

        private void DrawTutorial()
        {
            if (App.Meta.TutorialDone || _rc.State.Wave > 3) return;
            int step = _rc.State.Wave == 1 ? 1 : (_rc.State.Wave == 2 ? 3 : 4);
            float w = 900;
            Ui.Tooltip(Ui.W / 2 - w / 2, 220, w, 90);
            Ui.Label(Ui.W / 2 - w / 2 + 20, 220, w - 40, 90, L.Get("tutorial." + step), 26, Ui.White, TextAnchor.MiddleCenter);
        }

        private void DrawBanner()
        {
            if (_bannerTime <= 0f || string.IsNullOrEmpty(_bannerText)) return;
            float a = Mathf.Clamp01(_bannerTime * 2f);
            float y = Ui.H * 0.3f;
            Ui.DrawRect(0, y, Ui.W, 110, new Color(0.04f, 0.04f, 0.1f, 0.55f * a));
            Ui.Label(0, y, Ui.W, 110, _bannerText, 60, new Color(_bannerColor.r, _bannerColor.g, _bannerColor.b, a), TextAnchor.MiddleCenter, true);
        }

        // ------------------------------------------------------------------ preparation

        /// <summary>Explain the current biome's positional bonuses.</summary>
        private string AreaTraitSummary()
        {
            var seen = new HashSet<string>();
            var sb = new System.Text.StringBuilder();
            foreach (AreaTraitDef t in _rc.Biome.AreaTraits)
                if (seen.Add(t.Id)) sb.Append(App.Loc.Get("nodetrait." + t.Id)).Append(". ");
            return sb.ToString();
        }

        /// <summary>Team tactic chips (soft targeting weights); shown on the prepare screen, persisted in the run.</summary>
        /// <summary>Party stance (dynamic party): how far from the Crystal the heroes fight this wave.</summary>
        private void DrawStancePicker(float x, float y)
        {
            RunState s = _rc.State;
            Ui.Label(x, y, 740, 30, L.Get("stance.label") + ": " + L.Get("stance." + s.Stance.ToString().ToLowerInvariant() + ".desc"), 18, Ui.Muted, TextAnchor.UpperLeft);
            var values = (PartyStance[])System.Enum.GetValues(typeof(PartyStance));
            for (int i = 0; i < values.Length; i++)
            {
                PartyStance t = values[i];
                string key = t.ToString().ToLowerInvariant();
                if (Ui.Button(x + i * 190, y + 32, 180, 56, "     " + L.Get("stance." + key), s.Stance == t ? Tone.Primary : Tone.Ghost, true, 17))
                    s.Stance = t;
                Texture2D icon = Art.Icon("stance_" + key);
                if (icon != null) Ui.Icon(x + i * 190 + 10, y + 40, 40, 40, icon);
            }
            Block(x, y, values.Length * 190, 90);
        }

        private void DrawFormationPicker(float x, float y)
        {
            Ui.Label(x, y, 740, 28, L.Get("formation.label"), 18, Ui.Muted);
            foreach (PartyFormation f in System.Enum.GetValues(typeof(PartyFormation)))
                if (Ui.Button(x + (int)f * 190, y + 30, 180, 50, L.Get("formation." + f.ToString().ToLowerInvariant()),
                    _rc.State.Formation == f ? Tone.Primary : Tone.Ghost, true, 17)) _rc.State.Formation = f;
            Block(x, y, 570, 86);
        }

        private void DrawTacticPicker(float x, float y)
        {
            RunState s = _rc.State;
            Ui.Label(x, y, 600, 30, L.Get("tactic.label") + ": " + L.Get("tactic." + s.Tactic.ToString().ToLowerInvariant() + ".desc"), 18, Ui.Muted, TextAnchor.UpperLeft);
            var values = (TeamTactic[])System.Enum.GetValues(typeof(TeamTactic));
            for (int i = 0; i < values.Length; i++)
            {
                TeamTactic t = values[i];
                if (Ui.Button(x + i * 150, y + 32, 140, 56, L.Get("tactic." + t.ToString().ToLowerInvariant()), s.Tactic == t ? Tone.Secondary : Tone.Ghost, true, 16))
                    s.Tactic = t;
            }
            Block(x, y, values.Length * 150, 90);
        }

        // ------------------------------------------------------------------ synergy vision (P1)

        private SynergyReport _synergy;
        private Battle _synergyBattle;
        private string _synergyKey;
        private int _synergyFocus = -1;

        private string FormationKey()
        {
            var sb = new System.Text.StringBuilder();
            foreach (HeroRunState h in _rc.State.Heroes) sb.Append(h.DefId).Append(':').Append(h.Node).Append(':').Append(h.EvolutionId).Append(':').Append(h.Level).Append(':').Append(h.Downed).Append(';');
            foreach (string relic in _rc.State.Relics) sb.Append(relic).Append(';');
            foreach (string card in _rc.State.CardOrder) sb.Append(card).Append(':').Append(_rc.State.CardStacks(card)).Append(';');
            return sb.Append(_rc.State.Wave).Append(_rc.State.Stance).Append(_rc.State.Formation).Append(_rc.State.Tactic).Append(_rc.State.SealedGate).Append(_rc.State.CrystalPath).ToString();
        }

        /// <summary>
        /// Pre-wave overlay: lines between heroes for reaction rules (element colour), support auras (green), bonds (gold)
        /// and conflicts (red). Dashed = conditional, with the reason. Explains, never recommends a formation.
        /// </summary>
        private void EnsureFormationPreview()
        {
            string key = FormationKey();
            if (key != _synergyKey)
            {
                _synergyKey = key;
                _synergyBattle = new Battle(_rc.BuildBattleSetup());
                _synergy = SynergyReport.Analyze(_synergyBattle, _rc.ActiveBonds());
            }
        }

        private void DrawSynergyVision()
        {
            EnsureFormationPreview();
            Battle b = _synergyBattle;
            if (b == null || _synergy == null) return;
            var pos = new Vector2[b.Heroes.Count];
            for (int i = 0; i < pos.Length; i++) pos[i] = Ui.FromScreen(_cam.WorldToScreenPoint(WorldGfx.V(b.Heroes[i].Anchor)));
            // Hover (PC) / last touch (mobile) focuses one hero's links; no input is captured, so dragging heroes still works.
            _synergyFocus = -1;
            for (int i = 0; i < pos.Length; i++)
                if (Ui.Hover(pos[i].x - 50, pos[i].y - 120, 100, 130)) _synergyFocus = i;
            int labelled = 0;
            foreach (SynergyLink l in _synergy.Links)
            {
                if (_synergyFocus >= 0 && l.A != _synergyFocus && l.B != _synergyFocus) continue;
                Color c = l.Kind == SynergyKind.Reaction ? Color.Lerp(Ui.ElementColor(b.Heroes[l.A].Def.Element), Ui.ElementColor(b.Heroes[l.B].Def.Element), 0.5f)
                        : l.Kind == SynergyKind.Buff ? new Color(0.45f, 0.95f, 0.55f) : l.Kind == SynergyKind.Bond ? Ui.Gold : Ui.Bad;
                c.a = l.Active ? 0.85f : 0.45f;
                float off = l.Kind == SynergyKind.Reaction ? 0f : l.Kind == SynergyKind.Buff ? 6f : l.Kind == SynergyKind.Bond ? -6f : 10f;
                Vector2 a = pos[l.A] + new Vector2(0, off - 40), z = pos[l.B] + new Vector2(0, off - 40);
                Ui.Line(a.x, a.y, z.x, z.y, l.Active ? 5f : 3f, c, l.Active ? 0f : 10f);
                if (_synergyFocus >= 0 || labelled < 8)
                {
                    labelled++;
                    Vector2 mid = (a + z) / 2f + new Vector2(0, off * 3f);
                    string id = l.RuleId.Substring(l.RuleId.IndexOf(':') + 1);
                    string name = l.Kind == SynergyKind.Reaction ? L.ReactionName(id) : L.Get("synergy." + l.Kind.ToString().ToLowerInvariant()) + " · " + id;
                    if (!l.Active || l.Condition != null) name += " — " + L.Get("synergy.cond." + l.Condition);
                    Ui.Label(mid.x - 160, mid.y - 14, 320, 28, name, 16, c, TextAnchor.MiddleCenter, true, true, true);
                }
            }
            // Coverage & missing pieces panel (bottom-left, above the tactic picker).
            float px = 16, py = Ui.H - 420, pw = 520;
            var lines = new List<string> { L.Format("synergy.crystal", Mathf.RoundToInt(_synergy.CrystalCoverage * 100f)) };
            foreach (var kv in (_synergy.GateCoverage.Count > 0 ? _synergy.GateCoverage : _synergy.LaneCoverage))
                lines.Add(L.Format("synergy.lane", L.Get(Arena.Lanes[kv.Key].NameKey), Mathf.RoundToInt(kv.Value * 100f)));
            foreach (string m in _synergy.Missing)
            {
                int c = m.IndexOf(':');
                string arg = m.Substring(c + 1);
                if (m.StartsWith("isolated_element")) arg = L.Get("element." + arg);
                else if ((m.StartsWith("lane_uncovered") || m.StartsWith("gate_uncovered")) && int.TryParse(arg, out int li) && li < Arena.Lanes.Count) arg = L.Get(Arena.Lanes[li].NameKey);
                lines.Add("• " + L.Format("synergy.missing." + m.Substring(0, c), arg));
            }
            float ph = 50 + lines.Count * 26;
            Ui.Panel(px, py - ph, pw, ph);
            Block(px, py - ph, pw, ph);
            Ui.Label(px + 16, py - ph + 10, pw - 32, 30, L.Get("synergy.title"), 20, Ui.Gold, TextAnchor.UpperLeft, true);
            for (int i = 0; i < lines.Count; i++) Ui.Label(px + 16, py - ph + 40 + i * 26, pw - 32, 26, lines[i], 17, Ui.White);
        }

        private void DrawPrepare()
        {
            RunState s = _rc.State;
            DrawFormationPicker(Ui.W / 2 - 370, Ui.H - 510);
            DrawStancePicker(Ui.W / 2 - 370, Ui.H - 410);
            DrawTacticPicker(Ui.W / 2 - 370, Ui.H - 310);
            if (Ui.Button(Ui.W / 2 + 400, Ui.H - 228, 190, 56, L.Get("synergy.toggle"), App.Settings.SynergyVision ? Tone.Secondary : Tone.Ghost, true, 16))
            {
                App.Settings.SynergyVision = !App.Settings.SynergyVision;
                App.SaveSettings();
            }
            if (App.Settings.SynergyVision) DrawSynergyVision();
            WaveDef w = _rc.CurrentWave;
            // incoming panel (left)
            float px = 16, py = 156, pw = 560;
            List<KeyValuePair<string, int>> counts = _rc.PreviewEnemies(w);
            string hint = L.Get(w.HintKey);
            if (s.SealedGate >= 0 && s.SealedGate < Arena.Lanes.Count) hint = L.Format("prep.sealed_gate", L.Get(Arena.Lanes[s.SealedGate].NameKey)) + "\n" + hint;
            if (!_rc.Biome.Default) hint = L.Get(_rc.Biome.NameKey) + " — " + AreaTraitSummary() + hint;
            // Boss threat preview (P4): mechanics only once the boss is in the codex; first encounters get a generic,
            // non-spoiler reading guide.
            string bossId = _rc.BossFor(w);
            if (bossId != null && App.Content.Enemies.TryGetValue(bossId, out EnemyDef bossDef))
                hint += "\n" + (App.Meta.Codex.Contains("enemy:" + bossId)
                    ? L.Format("prep.boss_known", L.Get(bossDef.NameKey), L.Get(bossDef.DescKey))
                    : L.Get("prep.boss_first"));
            float hintH = Ui.TextHeight(hint, 22, pw - 40);
            float ph = 110 + hintH + 20 + ((counts.Count + 3) / 4) * 130;
            Ui.Panel(px, py, pw, ph);
            Block(px, py, pw, ph);
            Ui.Label(px + 20, py + 18, pw - 40, 40, L.Get("prep.incoming"), 26, Ui.Gold, TextAnchor.UpperLeft, true);
            var laneNames = new List<string>();
            EnsureFormationPreview();
            foreach (int l in Battle.LanesForWave(w, _rc.Biome))
            {
                int gate = Battle.GateLane(Arena, _synergyBattle.EffectiveLane(l));
                string name = L.Get(Arena.Lanes[gate].NameKey);
                if (!laneNames.Contains(name)) laneNames.Add(name);
            }
            Ui.Label(px + 20, py + 56, pw - 40, 34, L.Format("prep.lanes", string.Join(", ", laneNames)), 22, Ui.Bad);
            Ui.Label(px + 20, py + 92, pw - 40, hintH + 10, hint, 22, Ui.White);
            float ey = py + 110 + hintH;
            for (int i = 0; i < counts.Count; i++)
            {
                float ex = px + 20 + (i % 4) * 132, eyy = ey + (i / 4) * 130;
                Ui.DrawRect(ex, eyy, 120, 120, new Color(0.15f, 0.17f, 0.3f, 0.8f));
                Ui.Icon(ex + 6, eyy + 2, 108, 108, Art.Tex("Enemies/" + counts[i].Key + "_a"));
                Ui.Label(ex, eyy + 86, 116, 34, "×" + counts[i].Value, 24, Ui.White, TextAnchor.LowerRight, true, true, true);
                if (Ui.Hit(ex, eyy, 120, 120)) _buildFocus = "enemy:" + counts[i].Key;
            }
            if (_buildFocus != null && _buildFocus.StartsWith("enemy:"))
            {
                string id = _buildFocus.Substring(6);
                EnemyDef def = App.Content.Enemies[id];
                float tw = 560, th = 60 + Ui.TextHeight(L.Get(def.DescKey), 22, tw - 40);
                float ty = py + ph + 10;
                Ui.Tooltip(px, ty, tw, th);
                Block(px, ty, tw, th);
                Ui.Label(px + 20, ty + 10, tw - 40, 40, L.Get(def.NameKey), 26, Ui.Gold, TextAnchor.UpperLeft, true);
                Ui.Label(px + 20, ty + 46, tw - 40, th, L.Get(def.DescKey), 22, Ui.White);
                if (Ui.Hit(px, ty, tw, th)) _buildFocus = null;
            }

            // action column (right)
            float bx = Ui.W - 420, by = 156, bw = 400;
            Block(bx, by, bw, 720);
            if (Ui.Button(bx, by, bw, 120, L.Get("prep.start"), Tone.Primary, true, 40)) StartWave();
            by += 136;
            if (Ui.Button(bx, by, bw, 92, L.Get("prep.auto"), Tone.Secondary, true, 28)) { s.Formation = PartyFormation.Split; s.Stance = PartyStance.Balanced; Formation.AutoArrange(_rc); }
            by += 104;
            bool damaged = s.CrystalHp < _rc.CrystalMaxHp - 0.5f;
            if (Ui.Button(bx, by, bw, 92, L.Format("prep.repair", _rc.RepairCost), Tone.Ghost, damaged && s.Gold >= _rc.RepairCost, 26))
                if (_rc.RepairCrystal()) App.Audio.Play("coin", 0.6f, 0f, SoundCategory.Ui);
            by += 104;
            foreach (HeroRunState h in s.Heroes)
            {
                if (h.Downed)
                {
                    string name = L.Get(App.Content.Heroes[h.DefId].NameKey);
                    if (Ui.Button(bx, by, bw, 92, L.Format("prep.revive", _rc.ReviveCost) + " · " + name, Tone.Danger, s.Gold >= _rc.ReviveCost, 24))
                        _rc.Revive(h.Uid);
                    by += 104;
                }
            }
            foreach (HeroRunState h in s.Heroes)
            {
                if (!_rc.CanEvolve(h)) continue;
                string name = L.Get(App.Content.Heroes[h.DefId].NameKey);
                if (Ui.Button(bx, by, bw, 92, L.Get("prep.evolve") + " · " + name, Tone.Primary, true, 26)) _evolveHero = h.Uid;
                by += 104;
            }
            if (Ui.Button(bx, by, bw / 2 - 6, 88, L.Get("prep.build"), Tone.Ghost, true, 26)) _showBuild = true;
            if (Ui.Button(bx + bw / 2 + 6, by, bw / 2 - 6, 88, L.Get("hud.pause"), Tone.Ghost, true, 26)) _paused = true;
            by += 100;
            Ui.Label(bx, by, bw, 120, L.Get("prep.drag_hint"), 20, Ui.Muted);
            if (!App.Meta.TutorialDone && s.Wave <= 2)
            {
                Ui.Tooltip(Ui.W / 2 - 450, 140, 900, 80);
                Ui.Label(Ui.W / 2 - 430, 140, 860, 80, L.Get("tutorial.2"), 24, Ui.White, TextAnchor.MiddleCenter);
            }
            DrawHeroDock(false);
        }

        private int _evolveHero = -1;
        /// <summary>Set when a choice/reroll/skip replaced the offer list this frame; offer loops stop drawing stale entries.</summary>
        private bool _offersChanged;

        /// <summary>True while a modal overlay owns input (keyboard shortcuts must not act beneath it).</summary>
        private bool OverlayOpen => _paused || _showBuild || _showSettings || _evolveHero >= 0 || _pactPending >= 0;

        // ------------------------------------------------------------------ rewards

        private void DrawReward()
        {
            RunState s = _rc.State;
            Ui.DrawRect(0, 0, Ui.W, Ui.H, new Color(0.03f, 0.03f, 0.09f, 0.72f));
            Block(0, 0, Ui.W, Ui.H);
            string titleKey = "reward." + s.CurrentReward.ToString().ToLowerInvariant();
            Ui.Label(0, 150, Ui.W, 80, L.Get(titleKey), 56, Ui.Gold, TextAnchor.UpperCenter, true);
            // After-wave Battle Insights (P6): only when the wave actually hurt the Crystal.
            if (s.WaveLog.Count > 0)
            {
                WaveRecord last = s.WaveLog[s.WaveLog.Count - 1];
                for (int i = 0; i < last.Insights.Count && i < 2; i++)
                    Ui.Label(0, 214 + i * 24, Ui.W, 24, InsightText.Describe(L, App.Content, last.Insights[i]), 17, Ui.Muted, TextAnchor.UpperCenter);
            }
            switch (s.CurrentReward)
            {
                case RewardKind.Draft: DrawCardChoice(false); break;
                case RewardKind.Pact: DrawCardChoice(true); break;
                case RewardKind.Recruit: DrawRecruit(); break;
                case RewardKind.Relic: DrawRelicChoice(); break;
                case RewardKind.Shop: DrawShop(); break;
                case RewardKind.Evolution: DrawEvolutionReward(); break;
                case RewardKind.Event: DrawEvent(); break;
                case RewardKind.CrystalEvolution: DrawCrystalPaths(); break;
            }
        }

        /// <summary>Crystal Evolution: three permanent, exclusive Crystal paths (one pick per run).</summary>
        private void DrawCrystalPaths()
        {
            RunState s = _rc.State;
            int n = s.Offers.Count;
            float cw = 440, ch = 460, gap = 40;
            float x0 = Ui.W / 2 - (n * cw + (n - 1) * gap) / 2, y = 280;
            Ui.Label(0, 220, Ui.W, 40, L.Get("crystal.permanent"), 24, Ui.Muted, TextAnchor.UpperCenter);
            for (int i = 0; i < n && !_offersChanged; i++)
            {
                Offer o = s.Offers[i];
                float x = x0 + i * (cw + gap);
                Ui.CardFrame(x, y, cw, ch, "epic", _focusOffer == i);
                Ui.Label(x + 30, y + 30, cw - 60, 50, L.Get("crystal." + o.Id), 32, Ui.Gold, TextAnchor.UpperCenter, true);
                Ui.Label(x + 30, y + 110, cw - 60, ch - 140, L.Get("crystal." + o.Id + ".desc"), 23, Ui.White);
                if (Ui.Hit(x, y, cw, ch)) _focusOffer = i;
                if (Ui.Button(x + 30, y + ch + 14, cw - 60, 96, L.Get("reward.take"), Tone.Primary, true, 26)) Choose(i);
            }
            if (!_offersChanged) RewardFooter(false, "common.skip");
        }

        private void RewardFooter(bool canReroll, string skipKey, bool skipDanger = false)
        {
            RunState s = _rc.State;
            float y = Ui.H - 130;
            if (canReroll)
            {
                int cost = _rc.RerollCost;
                string label = cost == 0 ? L.Get("reward.reroll_free") : L.Format("reward.reroll", cost);
                if (Ui.Button(Ui.W / 2 - 420, y, 400, 100, label, Tone.Secondary, s.Gold >= cost, 28))
                {
                    if (_rc.Reroll()) App.Audio.Ui("ui_reroll");
                    _focusOffer = -1;
                    _offersChanged = true;
                }
            }
            if (skipKey != null && Ui.Button(canReroll ? Ui.W / 2 + 20 : Ui.W / 2 - 200, y, 400, 100, L.Get(skipKey), skipDanger ? Tone.Danger : Tone.Ghost, true, 28))
            {
                _rc.Skip();
                _focusOffer = -1;
                _offersChanged = true;
                AfterReward();
            }
            Ui.Label(40, y + 20, 600, 60, L.Format("reward.save_gold", App.Content.Economy.InterestCap), 20, Ui.Muted, TextAnchor.MiddleLeft);
        }

        private void AfterReward()
        {
            _evolveHero = -1;
            if (_rc.State.Phase != RunPhase.Reward)
            {
                App.SaveRun();
                ShowPrepareBanner();
            }
        }

        private void Choose(int index)
        {
            if (_rc.Choose(index))
            {
                App.Audio.Ui("ui_confirm");
                _focusOffer = -1;
                _offersChanged = true;
                AfterReward();
            }
            else App.Audio.Ui("ui_error");
        }

        private float CardDetail(CardDef c, float x, float y, float w, out string drawback)
        {
            List<string> lines = App.Fx.Describe(c.Effects);
            drawback = c.DrawbackKey != null ? L.Get(c.DrawbackKey) : null;
            string flavor = L.Get(c.DescKey);
            string text = (string.IsNullOrEmpty(flavor) ? "" : "<i>" + flavor + "</i>\n") + "• " + string.Join("\n• ", lines);
            Ui.Label(x, y, w, 400, text, 23, Ui.White);
            return Ui.TextHeight(text, 23, w);
        }

        private void DrawCardChoice(bool pact)
        {
            RunState s = _rc.State;
            int n = s.Offers.Count;
            float cw = 440, ch = 600, gap = 40;
            float x0 = Ui.W / 2 - (n * cw + (n - 1) * gap) / 2, y = 250;
            bool prevEnabled = GUI.enabled;
            if (_pactPending >= 0) GUI.enabled = false; // the confirm dialog owns input
            for (int i = 0; i < n && !_offersChanged; i++)
            {
                Offer o = s.Offers[i];
                CardDef c = App.Content.Cards[o.Id];
                float x = x0 + i * (cw + gap);
                bool focus = _focusOffer == i;
                Ui.CardFrame(x, y, cw, ch, Ui.RarityKey(c.Rarity), focus);
                Ui.Label(x + 30, y + 30, cw - 60, 46, L.Get(c.NameKey), 30, Ui.White, TextAnchor.UpperCenter, true);
                Ui.Icon(x + cw / 2 - 80, y + 92, 160, 160, Art.Tex("Cards/" + c.Id));
                string typeLine = L.Get("cardtype." + Sim.Content.EnumParse.ToSnake(c.Type.ToString())) + " · " + L.Rarity(c.Rarity);
                Ui.Label(x + 20, y + 258, cw - 40, 30, typeLine, 20, Ui.RarityColor(c.Rarity), TextAnchor.UpperCenter, true);
                if (o.Tag != null && o.Tag != "cursed") Ui.Label(x + 20, y + 286, cw - 40, 30, L.Get("reward." + o.Tag), 20, Ui.Teal, TextAnchor.UpperCenter, true);
                float h = CardDetail(c, x + 30, y + 322, cw - 60, out string drawback);
                if (drawback != null) Ui.Label(x + 30, y + 330 + h, cw - 60, 120, "<b>" + L.Get("label.drawback") + ":</b> " + drawback, 22, Ui.Bad);
                if (c.MaxStacks > 1) Ui.Label(x + 20, y + ch - 50, cw - 40, 30, L.Format("reward.stacks", s.CardStacks(c.Id), c.MaxStacks), 18, Ui.Muted, TextAnchor.UpperCenter);
                if (Ui.Hit(x, y, cw, ch)) _focusOffer = i;
                if (focus && Ui.Button(x + cw / 2 - 150, y + ch + 16, 300, 96, pact ? L.Get("reward.accept") : L.Get("reward.take"), pact ? Tone.Danger : Tone.Primary))
                {
                    if (pact) _pactPending = i;
                    else Choose(i);
                }
            }
            GUI.enabled = prevEnabled;
            if (_offersChanged) return;
            if (_pactPending >= 0)
            {
                Block(0, 0, Ui.W, Ui.H);
                Ui.DrawRect(0, 0, Ui.W, Ui.H, new Color(0, 0, 0, 0.6f));
                Ui.Panel(Ui.W / 2 - 500, Ui.H / 2 - 190, 1000, 380, "danger");
                Ui.Label(Ui.W / 2 - 460, Ui.H / 2 - 160, 920, 160, L.Get("reward.pact_confirm"), 30, Ui.White, TextAnchor.MiddleCenter, true);
                if (Ui.Button(Ui.W / 2 - 440, Ui.H / 2 + 50, 400, 100, L.Get("common.confirm"), Tone.Danger))
                {
                    int i = _pactPending;
                    _pactPending = -1;
                    Choose(i);
                }
                if (Ui.Button(Ui.W / 2 + 40, Ui.H / 2 + 50, 400, 100, L.Get("common.cancel"), Tone.Ghost)) _pactPending = -1;
                return;
            }
            RewardFooter(!pact, pact ? "reward.decline" : "common.skip");
        }

        private void DrawRecruit()
        {
            RunState s = _rc.State;
            int n = s.Offers.Count;
            float gap = 36, ch = 620;
            float cw = Mathf.Min(460f, (Ui.W - 120f - gap * (n - 1)) / Mathf.Max(1, n));
            float x0 = Ui.W / 2 - (n * cw + (n - 1) * gap) / 2, y = 250;
            for (int i = 0; i < n && !_offersChanged; i++)
            {
                Offer o = s.Offers[i];
                float x = x0 + i * (cw + gap);
                DrawHeroOffer(o, x, y, cw, ch, i, "reward.recruit_btn");
            }
            if (!_offersChanged) RewardFooter(true, "common.skip");
        }

        private void DrawHeroOffer(Offer o, float x, float y, float cw, float ch, int index, string buttonKey)
        {
            RunState s = _rc.State;
            HeroDef def = App.Content.Heroes[o.Id];
            bool full = s.Heroes.Count >= App.Content.Economy.MaxHeroes;
            Ui.CardFrame(x, y, cw, ch, "rare", _focusOffer == index);
            Ui.HeroIcon(x + cw / 2 - 110, y + 70, 220, 220, Art.Tex("Heroes/" + def.Id + "_idle"));
            Ui.Label(x + 30, y + 28, cw - 60, 46, L.Get(def.NameKey), 32, Ui.White, TextAnchor.UpperCenter, true);
            Ui.Icon(x + 40, y + 292, 44, 44, Art.ElementIcon(def.Element));
            Ui.Icon(x + 90, y + 292, 44, 44, Art.Tex("Icons/role_" + def.Role.ToString().ToLowerInvariant()));
            Ui.Label(x + 144, y + 292, cw - 170, 44, L.Format("label.element_role", L.Element(def.Element), L.Role(def.Role)), 22, Ui.ElementColor(def.Element), TextAnchor.MiddleLeft, true);
            Ui.Label(x + 30, y + 346, cw - 60, 36, L.Get(def.Skill.NameKey), 24, Ui.Gold, TextAnchor.UpperLeft, true);
            Ui.Label(x + 30, y + 380, cw - 60, 200, L.SkillText(def.Skill, def.Skill.DescKey), 20, Ui.White);
            BondDef bond = _rc.BondFor(def.Id);
            if (bond != null)
            {
                // Bond banner over the portrait: recruiting this hero completes a bond with the roster.
                Ui.DrawRect(x + 18, y + 252, cw - 36, 36, new Color(0.35f, 0.12f, 0.3f, 0.85f));
                Ui.Label(x + 24, y + 252, cw - 48, 36, L.Format("bond.forms", L.Get(bond.NameKey)), 18, Ui.Gold, TextAnchor.MiddleCenter, true);
            }
            if (o.TraitId != null)
            {
                // Recruit trait strip: icon, name and the rule (traits are rolled per offer, run-only).
                float ty = y + ch - 100;
                Ui.DrawRect(x + 18, ty - 4, cw - 36, 92, new Color(0.1f, 0.08f, 0.22f, 0.8f));
                Ui.Icon(x + 24, ty, 40, 40, Art.Tex("Icons/trait_" + o.TraitId));
                Ui.Label(x + 70, ty, cw - 96, 40, L.Get("trait." + o.TraitId + ".name"), 22, Ui.Gold, TextAnchor.MiddleLeft, true);
                Ui.Label(x + 24, ty + 40, cw - 48, 48, SharedPanels.TraitText(o.TraitId), 16, Ui.White);
            }
            if (o.Sold)
            {
                Ui.Label(x, y + ch - 80, cw, 60, L.Get("common.sold"), 30, Ui.Muted, TextAnchor.MiddleCenter, true);
                return;
            }
            if (Ui.Hit(x, y, cw, ch)) _focusOffer = index;
            string label = (o.Price > 0 ? L.Format("common.cost", o.Price) + " · " : "") + L.Get(buttonKey);
            bool ok = !full && s.Gold >= o.Price;
            if (Ui.Button(x + 30, y + ch + 14, cw - 60, 96, ok ? label : (full ? L.Get("reward.roster_full") : L.Get("reward.not_enough")), Tone.Primary, ok, 26)) Choose(index);
        }

        private void DrawRelicChoice()
        {
            RunState s = _rc.State;
            int n = s.Offers.Count;
            float cw = 440, ch = 560, gap = 40;
            float x0 = Ui.W / 2 - (n * cw + (n - 1) * gap) / 2, y = 260;
            for (int i = 0; i < n && !_offersChanged; i++) DrawRelicOffer(s.Offers[i], x0 + i * (cw + gap), y, cw, ch, i, "reward.take");
            if (!_offersChanged) RewardFooter(false, "common.skip");
        }

        private void DrawRelicOffer(Offer o, float x, float y, float cw, float ch, int index, string buttonKey)
        {
            RunState s = _rc.State;
            RelicDef r = App.Content.Relics[o.Id];
            Ui.CardFrame(x, y, cw, ch, Ui.RarityKey(r.Rarity), _focusOffer == index);
            Ui.Label(x + 30, y + 28, cw - 60, 46, L.Get(r.NameKey), 28, Ui.White, TextAnchor.UpperCenter, true);
            Ui.Icon(x + cw / 2 - 72, y + 88, 144, 144, Art.Tex("Relics/" + r.Id));
            Ui.Label(x + 20, y + 236, cw - 40, 30, L.Rarity(r.Rarity) + " · " + L.Get("family." + r.Family.ToString().ToLowerInvariant()), 20, Ui.RarityColor(r.Rarity), TextAnchor.UpperCenter, true);
            if (_rc.CompletesFusion(r.Id)) Ui.Label(x + 20, y + 266, cw - 40, 30, L.Get("reward.fusion_hint"), 22, Ui.Gold, TextAnchor.UpperCenter, true);
            string text = "<i>" + L.Get(r.DescKey) + "</i>\n• " + string.Join("\n• ", App.Fx.Describe(r.Effects));
            Ui.Label(x + 30, y + 300, cw - 60, ch - 320, text, 21, Ui.White);
            if (o.Sold)
            {
                Ui.Label(x, y + ch + 20, cw, 60, L.Get("common.sold"), 30, Ui.Muted, TextAnchor.MiddleCenter, true);
                return;
            }
            if (Ui.Hit(x, y, cw, ch)) _focusOffer = index;
            bool ok = s.Gold >= o.Price;
            string label = (o.Price > 0 ? L.Format("common.cost", o.Price) + " · " : "") + L.Get(buttonKey);
            if (Ui.Button(x + 30, y + ch + 14, cw - 60, 96, ok ? label : L.Get("reward.not_enough"), Tone.Primary, ok, 26)) Choose(index);
        }

        private void DrawShop()
        {
            RunState s = _rc.State;
            float cw = 340, ch = 470, gap = 22;
            int perRow = Mathf.Max(3, Mathf.FloorToInt((Ui.W - 80) / (cw + gap)));
            var items = new List<int>();
            for (int i = 0; i < s.Offers.Count; i++) items.Add(i);
            int rows = (items.Count + perRow - 1) / perRow;
            float scale = rows > 1 ? 0.78f : 1f;
            cw *= scale;
            ch *= scale;
            float rowW = Mathf.Min(items.Count, perRow) * (cw + gap) - gap;
            float x0 = Ui.W / 2 - rowW / 2, y0 = 240;
            for (int k = 0; k < items.Count && !_offersChanged; k++)
            {
                int i = items[k];
                Offer o = s.Offers[i];
                float x = x0 + (k % perRow) * (cw + gap), y = y0 + (k / perRow) * (ch + 130 * scale);
                if (!o.Sold && (o.Kind == OfferKind.Hero || o.Kind == OfferKind.Relic || o.Kind == OfferKind.Card))
                {
                    // Shop lock: keep one offer for the next shop (survives rerolls).
                    bool locked = _rc.IsLocked(o);
                    if (locked) Ui.DrawRect(x - 4, y - 4, cw + 8, ch + 8, new Color(0.45f, 0.75f, 1f, 0.45f));
                    if (Ui.Button(x + cw - 64, y - 30, 64, 52, locked ? L.Get("shop.unlock") : L.Get("shop.lock"), locked ? Tone.Secondary : Tone.Ghost, true, 16))
                        _rc.ToggleLock(i);
                }
                switch (o.Kind)
                {
                    case OfferKind.Hero: DrawHeroOffer(o, x, y, cw, ch, i, "reward.buy"); break;
                    case OfferKind.Relic: DrawRelicOffer(o, x, y, cw, ch, i, "reward.buy"); break;
                    case OfferKind.Card:
                    {
                        CardDef c = App.Content.Cards[o.Id];
                        Ui.CardFrame(x, y, cw, ch, Ui.RarityKey(c.Rarity), _focusOffer == i);
                        Ui.Label(x + 20, y + 22, cw - 40, 40, L.Get(c.NameKey), 26, Ui.White, TextAnchor.UpperCenter, true);
                        Ui.Icon(x + cw / 2 - 60, y + 70, 120, 120, Art.Tex("Cards/" + c.Id));
                        CardDetail(c, x + 24, y + 200, cw - 48, out string drawback);
                        if (o.Sold) Ui.Label(x, y + ch + 16, cw, 60, L.Get("common.sold"), 28, Ui.Muted, TextAnchor.MiddleCenter, true);
                        else
                        {
                            if (Ui.Hit(x, y, cw, ch)) _focusOffer = i;
                            bool ok = s.Gold >= o.Price;
                            if (Ui.Button(x + 20, y + ch + 12, cw - 40, 92, ok ? L.Format("common.cost", o.Price) + " · " + L.Get("reward.buy") : L.Get("reward.not_enough"), Tone.Primary, ok, 24)) Choose(i);
                        }
                        break;
                    }
                    case OfferKind.Repair:
                    case OfferKind.Revive:
                    {
                        Ui.Panel(x, y, cw, ch * 0.62f);
                        bool repair = o.Kind == OfferKind.Repair;
                        Ui.Icon(x + cw / 2 - 60, y + 30, 120, 120, repair ? Art.Icon("crystal") : Art.Portrait(o.Id));
                        string title = repair ? L.Format("reward.repair", Mathf.RoundToInt(App.Content.Economy.RepairPct * 100)) : L.Format("reward.revive", L.Get("hero." + o.Id + ".name"));
                        Ui.Label(x + 20, y + 160, cw - 40, 80, title, 26, Ui.White, TextAnchor.UpperCenter, true);
                        bool ok = s.Gold >= o.Price && (!o.Sold || repair) && (!repair || s.CrystalHp < _rc.CrystalMaxHp - 0.5f);
                        if (Ui.Button(x + 20, y + ch * 0.62f + 12, cw - 40, 92, L.Format("common.cost", o.Price), Tone.Secondary, ok, 26)) Choose(i);
                        break;
                    }
                }
            }
            if (!_offersChanged) RewardFooter(true, "reward.leave");
        }

        private void DrawEvolutionReward()
        {
            RunState s = _rc.State;
            var heroes = new List<int>();
            foreach (Offer o in s.Offers) if (!heroes.Contains(o.HeroUid)) heroes.Add(o.HeroUid);
            if (heroes.Count == 0)
            {
                Ui.Label(0, 400, Ui.W, 60, L.Get("reward.evo_none"), 30, Ui.Muted, TextAnchor.MiddleCenter);
            }
            else
            {
                if (_evolveHero < 0 || !heroes.Contains(_evolveHero)) _evolveHero = heroes[0];
                float x = Ui.W / 2 - heroes.Count * 90;
                for (int i = 0; i < heroes.Count; i++)
                {
                    HeroRunState h = s.Hero(heroes[i]);
                    if (_evolveHero == h.Uid) Ui.DrawRect(x + i * 180 - 4, 236, 168, 168, new Color(1f, 0.85f, 0.4f, 0.8f));
                    Ui.Icon(x + i * 180, 240, 160, 160, Art.Portrait(h.DefId));
                    if (Ui.Hit(x + i * 180, 240, 160, 160)) _evolveHero = h.Uid;
                }
                DrawEvolveModal(_evolveHero, true);
            }
            Ui.Label(0, Ui.H - 220, Ui.W, 40, L.Format("reward.evolve_cost", App.Content.Economy.EvolutionEssence) + " · " + L.Get("common.essence") + " " + s.Essence, 24, new Color(0.8f, 0.65f, 1f), TextAnchor.MiddleCenter, true);
            if (!_offersChanged) RewardFooter(false, "common.done");
        }

        /// <summary>Two evolution branches side by side with full mechanical descriptions.</summary>
        private void DrawEvolveModal(int heroUid, bool inReward)
        {
            RunState s = _rc.State;
            HeroRunState h = s.Hero(heroUid);
            if (h == null) { _evolveHero = -1; return; }
            HeroDef def = App.Content.Heroes[h.DefId];
            if (!inReward)
            {
                Ui.DrawRect(0, 0, Ui.W, Ui.H, new Color(0.03f, 0.03f, 0.09f, 0.75f));
                Block(0, 0, Ui.W, Ui.H);
            }
            Ui.Label(0, inReward ? 410 : 160, Ui.W, 50, L.Format("reward.evo_choose", L.Get(def.NameKey)), 34, Ui.White, TextAnchor.UpperCenter, true);
            float cw = 700, ch = 520, y = inReward ? 470 : 230;
            for (int i = 0; i < def.Evolutions.Count; i++)
            {
                EvolutionDef evo = App.Content.Evolutions[def.Evolutions[i]];
                float x = Ui.W / 2 - cw - 20 + i * (cw + 40);
                Ui.CardFrame(x, y, cw, ch, i == 0 ? "legendary" : "epic");
                Ui.HeroIcon(x + 20, y + 30, 200, 240, Art.Tex("Heroes/" + def.Id + "_evo" + (i == 0 ? "A" : "B")));
                Ui.Label(x + 230, y + 34, cw - 260, 50, L.Get(evo.NameKey), 34, Ui.Gold, TextAnchor.UpperLeft, true);
                Ui.Label(x + 230, y + 86, cw - 260, 120, "<i>" + L.Get(evo.DescKey) + "</i>", 22, Ui.White);
                SkillDef skill = def.Skill.With(evo.Skill);
                string text = "<b>" + L.Get(skill.NameKey) + "</b>\n" + L.SkillText(skill, skill.DescKey);
                List<string> fx = App.Fx.Describe(evo.Effects);
                if (fx.Count > 0) text += "\n• " + string.Join("\n• ", fx);
                if (evo.RoleOverride.HasValue) text += "\n" + L.Get("label.passive") + ": " + L.Role(evo.RoleOverride.Value);
                Ui.Label(x + 30, y + 280, cw - 60, ch - 290, text, 21, Ui.White);
                bool ok = _rc.CanEvolve(h);
                if (Ui.Button(x + cw / 2 - 200, y + ch + 14, 400, 96, L.Get("prep.evolve") + " · " + L.Format("reward.evolve_cost", App.Content.Economy.EvolutionEssence), Tone.Primary, ok, 26))
                {
                    if (_rc.Evolve(h.Uid, evo.Id))
                    {
                        App.Audio.Play("evolution", 1f, 0f, SoundCategory.Ui);
                        _evolveHero = -1;
                        _offersChanged = true;
                        App.SaveRun();
                        return;
                    }
                }
            }
            if (!inReward && Ui.Button(Ui.W / 2 - 200, Ui.H - 130, 400, 100, L.Get("common.cancel"), Tone.Ghost)) _evolveHero = -1;
        }

        private void DrawEvent()
        {
            RunState s = _rc.State;
            if (s.CurrentEventId == null || !App.Content.Events.TryGetValue(s.CurrentEventId, out EventDef ev)) return;
            float w = 1100, x = Ui.W / 2 - w / 2;
            Ui.Panel(x, 250, w, 180);
            Ui.Label(x + 40, 270, w - 80, 50, L.Get(ev.NameKey), 36, Ui.Gold, TextAnchor.UpperLeft, true);
            Ui.Label(x + 40, 324, w - 80, 90, L.Get(ev.DescKey), 24, Ui.White);
            float y = 460;
            for (int i = 0; i < s.Offers.Count && !_offersChanged; i++)
            {
                EventOption o = ev.Options[s.Offers[i].OptionIndex];
                string text = L.Get(o.TextKey);
                bool affordable = o.Gold >= 0 || s.Gold >= -o.Gold;
                if (Ui.Button(x, y, w, 100, text, i == s.Offers.Count - 1 ? Tone.Ghost : Tone.Secondary, affordable, 26)) Choose(i);
                if (o.DrawbackKey != null)
                {
                    Ui.Label(x + 20, y + 104, w - 40, 36, "<b>" + L.Get("label.drawback") + ":</b> " + L.Get(o.DrawbackKey), 22, Ui.Bad);
                    y += 40;
                }
                y += 124;
            }
        }

        // ------------------------------------------------------------------ build view & pause

        private void DrawBuild()
        {
            RunState s = _rc.State;
            Ui.DrawRect(0, 0, Ui.W, Ui.H, new Color(0.03f, 0.03f, 0.09f, 0.8f));
            Block(0, 0, Ui.W, Ui.H);
            Ui.Label(60, 40, 800, 60, L.Get("prep.relics"), 40, Ui.Gold, TextAnchor.UpperLeft, true);
            float x = 60, y = 110;
            if (s.Relics.Count == 0) Ui.Label(60, y, 600, 40, L.Get("prep.none"), 24, Ui.Muted);
            foreach (string id in s.Relics)
            {
                Ui.Icon(x, y, 110, 110, Art.Tex("Relics/" + id));
                if (Ui.Hit(x, y, 110, 110)) _buildFocus = "relic:" + id;
                x += 120;
                if (x > Ui.W / 2 - 120) { x = 60; y += 120; }
            }
            y += 140;
            Ui.Label(60, y, 800, 60, L.Get("prep.cards"), 40, Ui.Gold, TextAnchor.UpperLeft, true);
            y += 70;
            x = 60;
            if (s.CardOrder.Count == 0) Ui.Label(60, y, 600, 40, L.Get("prep.none"), 24, Ui.Muted);
            foreach (string id in s.CardOrder)
            {
                Ui.Icon(x, y, 100, 100, Art.Tex("Cards/" + id));
                int st = s.CardStacks(id);
                if (st > 1) Ui.Label(x, y + 70, 96, 30, "×" + st, 24, Ui.White, TextAnchor.LowerRight, true, true, true);
                if (Ui.Hit(x, y, 100, 100)) _buildFocus = "card:" + id;
                x += 110;
                if (x > Ui.W / 2 - 110) { x = 60; y += 110; }
            }
            if (_buildFocus != null && !_buildFocus.StartsWith("enemy:"))
            {
                float px = Ui.W / 2 + 20, pw = Ui.W / 2 - 80;
                Ui.Panel(px, 110, pw, 640);
                string body, title;
                if (_buildFocus.StartsWith("relic:"))
                {
                    RelicDef r = App.Content.Relics[_buildFocus.Substring(6)];
                    title = L.Get(r.NameKey);
                    body = "<i>" + L.Get(r.DescKey) + "</i>\n• " + string.Join("\n• ", App.Fx.Describe(r.Effects));
                    int count = s.SourceActivations.TryGetValue(r.Id, out int c) ? c : 0;
                    body += "\n\n" + L.Get("results.relics") + ": " + count;
                }
                else
                {
                    CardDef c = App.Content.Cards[_buildFocus.Substring(5)];
                    title = L.Get(c.NameKey) + (s.CardStacks(c.Id) > 1 ? " ×" + s.CardStacks(c.Id) : "");
                    body = "• " + string.Join("\n• ", App.Fx.Describe(c.Effects, s.CardStacks(c.Id)));
                    if (c.DrawbackKey != null) body += "\n<color=#ff7080>" + L.Get(c.DrawbackKey) + "</color>";
                }
                Ui.Label(px + 30, 140, pw - 60, 50, title, 34, Ui.Gold, TextAnchor.UpperLeft, true);
                Ui.Label(px + 30, 200, pw - 60, 540, body, 24, Ui.White);
            }
            Ui.Label(60, Ui.H - 260, Ui.W - 120, 120, L.Get("help.application") + "\n" + L.Get("help.reaction") + "\n" + L.Get("help.proc"), 20, Ui.Muted);
            if (Ui.Button(Ui.W / 2 - 200, Ui.H - 130, 400, 100, L.Get("common.close"), Tone.Ghost))
            {
                _showBuild = false;
                _buildFocus = null;
            }
        }

        private void DrawPause()
        {
            Ui.DrawRect(0, 0, Ui.W, Ui.H, new Color(0, 0, 0, 0.6f));
            Block(0, 0, Ui.W, Ui.H);
            float w = 640, h = 640, x = Ui.W / 2 - w / 2, y = Ui.H / 2 - h / 2;
            Ui.Panel(x, y, w, h);
            Ui.Label(x, y + 30, w, 60, L.Get("pause.title"), 48, Ui.Gold, TextAnchor.UpperCenter, true);
            if (_pauseConfirm)
            {
                Ui.Label(x + 40, y + 140, w - 80, 160, L.Get("pause.abandon_confirm"), 28, Ui.White, TextAnchor.MiddleCenter);
                if (Ui.Button(x + 60, y + 340, w - 120, 100, L.Get("common.confirm"), Tone.Danger))
                {
                    _pauseConfirm = false;
                    _paused = false;
                    ClearBattleViews();
                    _rc.Abandon();
                }
                if (Ui.Button(x + 60, y + 460, w - 120, 100, L.Get("common.cancel"), Tone.Ghost)) _pauseConfirm = false;
                return;
            }
            float by = y + 130;
            if (Ui.Button(x + 60, by, w - 120, 100, L.Get("pause.resume"), Tone.Primary)) _paused = false;
            by += 116;
            if (Ui.Button(x + 60, by, w - 120, 100, L.Get("menu.settings"), Tone.Ghost)) _showSettings = true;
            by += 116;
            if (Ui.Button(x + 60, by, w - 120, 100, L.Get("pause.to_menu"), Tone.Secondary))
            {
                _paused = false;
                if (!_runLost) App.SaveRun();
                App.SaveMeta();
                App.Run = null;
                GameRoot.Instance.GoTo(AppScreen.MainMenu);
            }
            by += 116;
            if (Ui.Button(x + 60, by, w - 120, 100, L.Get("pause.abandon"), Tone.Danger)) _pauseConfirm = true;
            Ui.Label(x + 30, y + h - 70, w - 60, 60, L.Get("pause.save_note"), 18, Ui.Muted, TextAnchor.MiddleCenter);
        }
    }
}
