using System.Collections.Generic;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using Aetherward.Sim.Presentation;
using Aetherward.Sim.Run;
using UnityEngine;

namespace Aetherward.Game
{
    /// <summary>
    /// Battle scene controller. Drives the run state machine (prepare -> wave -> rewards), steps the
    /// fixed-tick simulation at 1x/2x, mirrors simulation state into pooled sprite views, and turns
    /// combat events into VFX, audio and floating text. Never owns gameplay rules.
    /// </summary>
    public sealed partial class BattleController : MonoBehaviour
    {
        private RunController _rc;
        private Camera _cam;
        private Transform _world, _unitsRoot, _fxRoot;
        private SpriteRenderer _crystal, _crystalShield;
        private readonly List<SpriteRenderer> _nodes = new List<SpriteRenderer>();
        private readonly List<SpriteRenderer> _laneArrows = new List<SpriteRenderer>();
        private readonly Dictionary<int, UnitView> _units = new Dictionary<int, UnitView>();
        private readonly Dictionary<int, UnitView> _prepViews = new Dictionary<int, UnitView>();
        private readonly Stack<UnitView> _unitPool = new Stack<UnitView>();
        private readonly Dictionary<int, SpriteRenderer> _projectiles = new Dictionary<int, SpriteRenderer>();
        private readonly Dictionary<int, SpriteRenderer> _zones = new Dictionary<int, SpriteRenderer>();
        private readonly Dictionary<DelayedStrike, SpriteRenderer> _strikes = new Dictionary<DelayedStrike, SpriteRenderer>();
        private readonly Dictionary<EnemyBolt, SpriteRenderer> _bolts = new Dictionary<EnemyBolt, SpriteRenderer>();
        private readonly Stack<SpriteRenderer> _srPool = new Stack<SpriteRenderer>();
        private readonly HashSet<int> _seen = new HashSet<int>();
        private readonly HashSet<DelayedStrike> _liveStrikes = new HashSet<DelayedStrike>();
        private readonly List<DelayedStrike> _goneStrikes = new List<DelayedStrike>();
        private readonly HashSet<EnemyBolt> _liveBolts = new HashSet<EnemyBolt>();
        private readonly List<EnemyBolt> _goneBolts = new List<EnemyBolt>();
        private readonly List<int> _remove = new List<int>();
        private FxSystem _fx;
        private readonly FloatingTextSystem _text = new FloatingTextSystem();
        private readonly DamageNumberMerger _merge = new DamageNumberMerger();
        private readonly TelegraphAssist _assist = new TelegraphAssist();
        private DebugOverlay _debug;

        private float _accumulator;
        private int _speed = 1;
        private bool _paused;
        private float _resolveDelay = -1f;
        private float _shake;
        private float _crystalWobble;
        private float _bannerTime;
        private string _bannerText;
        private Color _bannerColor = Color.white;
        private readonly Dictionary<string, float> _calloutCooldown = new Dictionary<string, float>();
        private int _reactionStreak;
        private float _streakTimer;

        // drag & drop
        private int _dragUid = -1;
        private int _selectedUid = -1;
        private Vector3 _dragPos;
        private readonly List<Rect> _uiBlockers = new List<Rect>();
        private readonly List<Rect> _uiBlockersNext = new List<Rect>();

        private ArenaDef Arena => _rc.Arena;

        private void Start()
        {
            _rc = App.Run;
            if (_rc == null)
            {
                // Opened Battle directly (e.g. from the editor): start a quick test run.
                _rc = RunController.NewRun(App.Content, Pcg32.SeedFromTime(System.DateTime.UtcNow), new[] { "ignis", "terra" }, 0, App.Meta.ToRunUnlocks());
                App.Run = _rc;
            }
            _rc.Notice += OnNotice;
            _cam = GameRoot.EnsureCamera(new Color(0.16f, 0.3f, 0.24f));
            FitCamera();
            BuildWorld();
            _fx = new FxSystem(_fxRoot);
            _debug = new GameObject("DebugOverlay").AddComponent<DebugOverlay>();
            _debug.transform.SetParent(transform, false);
            _debug.Init(this);
            App.Audio.PlayMusic(_rc.Biome.Music);
            _speed = App.Settings.DefaultFastSpeed ? 2 : 1;
            if (_rc.State.Phase == RunPhase.Battle) _rc.State.Phase = RunPhase.Prepare; // resumed mid-wave
            ShowPrepareBanner();
        }

        private void OnDestroy()
        {
            if (_rc != null) _rc.Notice -= OnNotice;
            if (_debug != null) Destroy(_debug.gameObject);
        }

        private void FitCamera()
        {
            float aspect = (float)Screen.width / Mathf.Max(1, Screen.height);
            _cam.orthographicSize = Mathf.Max(7.5f, 13.2f / aspect);
        }

        // ------------------------------------------------------------------ world construction

        private void BuildWorld()
        {
            _world = new GameObject("World").transform;
            _world.SetParent(transform, false);
            _unitsRoot = new GameObject("Units").transform;
            _unitsRoot.SetParent(_world, false);
            _fxRoot = new GameObject("Fx").transform;
            _fxRoot.SetParent(_world, false);
            Sprite bgSprite = Art.Sprite(_rc.Biome.Background) ?? Art.Sprite("World/arena_background");
            SpriteRenderer bg = WorldGfx.NewSprite(_world, "Arena", bgSprite, -10000);
            bg.transform.position = Vector3.zero;
            for (int i = 0; i < Arena.Nodes.Count; i++)
            {
                SpriteRenderer n = WorldGfx.NewSprite(_world, "Node" + i, Art.Sprite("World/node_empty"), -9000);
                n.transform.position = WorldGfx.V(Arena.Nodes[i]) + new Vector3(0, -0.05f, 0);
                _nodes.Add(n);
            }
            _crystal = WorldGfx.NewSprite(_world, "Crystal", Art.Sprite("World/crystal_intact"), WorldGfx.OrderFor(-0.6f));
            _crystal.transform.position = new Vector3(0, -0.55f, 0);
            _crystalShield = WorldGfx.NewSprite(_world, "CrystalShield", Art.Sprite("Vfx/ring"), WorldGfx.OrderFor(-0.6f) + 5);
            _crystalShield.transform.position = new Vector3(0, 0.4f, 0);
            _crystalShield.transform.localScale = Vector3.one * 1.3f;
        }

        // ------------------------------------------------------------------ main loop

        /// <summary>Accessibility/mobile: losing focus mid-battle pauses instead of letting the wave run unattended.</summary>
        private void OnApplicationFocus(bool focused)
        {
            if (!focused && App.Settings.PauseOnFocusLoss && _rc != null && _rc.State.Phase == RunPhase.Battle) _paused = true;
        }

        private void Update()
        {
            float dt = Time.unscaledDeltaTime;
            FitCamera();
            HandleKeys();
            RunState s = _rc.State;
            _uiBlockers.Clear();
            _uiBlockers.AddRange(_uiBlockersNext);

            if (s.Phase != RunPhase.Battle) s.MenuSeconds += dt; // decision time outside combat (run breakdown)
            if (s.Phase == RunPhase.Battle && _rc.Battle != null)
            {
                StepBattle(dt);
                if (_rc.Battle != null) SyncBattleViews(dt); // StepBattle may resolve the battle
            }
            else
            {
                SyncPrepViews(dt);
                if (s.Phase == RunPhase.Prepare) HandlePlacementInput();
            }
            UpdateNodes();
            UpdateLaneArrows();
            UpdateCrystal(dt);
            _fx.Update(_paused ? 0f : dt * (s.Phase == RunPhase.Battle ? _speed : 1));
            _text.Update(dt);
            if (_bannerTime > 0f) _bannerTime -= dt;
            if (_streakTimer > 0f)
            {
                _streakTimer -= dt;
                if (_streakTimer <= 0f) _reactionStreak = 0;
            }
            UpdateShake(dt);
            if (s.Finished) FinishRun();
        }

        private void HandleKeys()
        {
            if (Input.GetKeyDown(KeyCode.Escape))
            {
                if (_pauseConfirm) _pauseConfirm = false;
                else if (_showSettings) _showSettings = false;
                else _paused = !_paused;
            }
            if (Input.GetKeyDown(KeyCode.Space) && _rc.State.Phase == RunPhase.Prepare && !OverlayOpen) StartWave();
            if (Input.GetKeyDown(KeyCode.F)) _speed = _speed == 1 ? 2 : 1;
            if (Input.GetKeyDown(KeyCode.F3)) App.Settings.ShowRanges = !App.Settings.ShowRanges;
        }

        private void StepBattle(float dt)
        {
            Battle b = _rc.Battle;
            if (b.Outcome != BattleOutcome.Running)
            {
                if (_resolveDelay < 0f)
                {
                    _resolveDelay = 1.6f;
                    bool cleared = b.Outcome == BattleOutcome.Cleared;
                    if (b.Outcome == BattleOutcome.CrystalDestroyed)
                    {
                        // Drop the wave-start save now so quitting during the defeat banner cannot replay the wave.
                        _runLost = true;
                        App.Saves.Delete("run");
                    }
                    Banner(cleared ? App.Loc.Get("hud.wave_clear") : App.Loc.Get("results.defeat"), cleared ? Ui.Good : Ui.Bad, 1.6f);
                    App.Audio.Play(cleared ? (_rc.TotalWaves > 0 && b.Wave.Number >= _rc.TotalWaves ? "victory" : "wave_clear") : "defeat", 1f, 0f);
                }
                _resolveDelay -= dt;
                if (_resolveDelay <= 0f)
                {
                    _resolveDelay = -1f;
                    ClearBattleViews();
                    _rc.ResolveBattle();
                    if (!_rc.State.Finished)
                    {
                        App.SaveRun();
                        App.SaveMeta();
                        if (_rc.State.Phase == RunPhase.Prepare) ShowPrepareBanner();
                    }
                }
                return;
            }
            if (_paused || _modalOpen) return;
            _accumulator += dt * _assist.EffectiveSpeed(_speed, Time.unscaledTime);
            int steps = 0;
            while (_accumulator >= Battle.TickSeconds && steps < 10)
            {
                _accumulator -= Battle.TickSeconds;
                b.Tick();
                ProcessEvents(b);
                b.Journal.Clear();
                steps++;
            }
            if (steps == 10) _accumulator = 0f; // never spiral on slow frames
        }

        public void StartWave()
        {
            if (_rc.State.Phase != RunPhase.Prepare) return;
            if (_rc.StartWave() == null) return;
            ClearPrepViews();
            _accumulator = 0f;
            WaveDef w = _rc.Battle.Wave;
            Banner(App.Loc.Format("hud.wave_start", w.Number, App.Loc.Get(w.NameKey)), Ui.Gold, 2.2f);
            App.Audio.Play("wave_start", 0.9f, 0f);
            App.Audio.PlayMusic(w.Boss ? "boss_loop" : "battle_loop");
            if (w.Boss) App.Audio.Play("boss_roar", 1f, 0f);
        }

        private void FinishRun()
        {
            if (_finishing) return;
            _finishing = true;
            RunResults results = RunResults.Build(_rc);
            App.LastResults = results;
            App.LastUnlocks = App.Meta.RecordRun(_rc, results, System.DateTimeOffset.UtcNow.ToUnixTimeSeconds());
            App.Meta.TutorialDone = true;
            App.SaveMeta();
            App.ClearRun();
            App.Run = _rc; // keep for the results screen; save already deleted
            GameRoot.Instance.GoTo(AppScreen.Results);
        }

        private bool _finishing;
        private bool _runLost;

        // ------------------------------------------------------------------ event -> presentation

        private static bool IsBossUid(Battle b, int uid)
        {
            if (uid == 0) return false;
            foreach (EnemyUnit en in b.Enemies) if (en.Uid == uid) return en.IsBoss;
            return false;
        }

        private void ProcessEvents(Battle b)
        {
            bool reduced = App.Settings.ReducedVfx || App.Settings.BatterySaver;
            _merge.Prune(Time.unscaledTime);
            bool numbers = App.Settings.DamageNumbers;
            foreach (SimEvent e in b.Journal.Pending)
            {
                Vector3 p = WorldGfx.V(e.Pos);
                switch (e.Type)
                {
                    case SimEventType.Hit:
                    {
                        if (e.Id == "hero")
                        {
                            if (_units.TryGetValue(e.TargetUid, out UnitView hv)) hv.Flash(0.8f);
                            break;
                        }
                        if (_units.TryGetValue(e.TargetUid, out UnitView v)) v.Flash(1f);
                        if (numbers && (e.Crit || e.Value >= 8f) && e.Generation <= 1)
                        {
                            Color c = e.Crit ? Ui.Gold : (e.Id != null ? Ui.ElementColor(e.Element) : Color.white);
                            DamageNumberMerger.Result m = _merge.Add(e.TargetUid, e.Value, e.Crit, Time.unscaledTime);
                            _text.Upsert(m.Slot, p + new Vector3(Random.Range(-0.25f, 0.25f), 0.9f, 0), Mathf.RoundToInt(m.Total) + (e.Crit ? "!" : ""), c, e.Crit ? 34 : 24, 0.75f);
                        }
                        if (!reduced && e.Generation == 0 && Random.value < 0.6f)
                            _fx.Spawn("Vfx/impact_" + (e.Element == Element.None ? "earth" : ElementUtil.Key(e.Element)), p + new Vector3(0, 0.45f, 0), 0.25f, 0.55f, 0.22f, Color.white, Random.Range(0, 360));
                        App.Audio.Play("hit_" + (e.Element == Element.None ? "physical" : ElementUtil.Key(e.Element)), 0.35f, 0.08f, SoundCategory.Sfx, 0.06f);
                        break;
                    }
                    case SimEventType.Reaction:
                        OnReaction(e, p, reduced);
                        break;
                    case SimEventType.Strike:
                        OnStrike(e, p, reduced);
                        break;
                    case SimEventType.SkillCast:
                    {
                        if (_units.TryGetValue(e.SourceUid, out UnitView v)) v.Cast();
                        if (e.Element != Element.None) App.Audio.Play("cast_" + ElementUtil.Key(e.Element), 0.55f, 0.04f, SoundCategory.Sfx, 0.08f);
                        if (!reduced) _fx.Spawn("Vfx/glow", p + new Vector3(0, 0.4f, 0), 0.5f, 2.2f, 0.4f, Ui.ElementColor(e.Element) * new Color(1, 1, 1, 0.55f));
                        break;
                    }
                    case SimEventType.BasicAttack:
                    {
                        if (e.Id == "melee" && _units.TryGetValue(e.SourceUid, out UnitView v) && _units.TryGetValue(e.TargetUid, out UnitView t))
                        {
                            v.Lunge(t.transform.position);
                            if (!reduced)
                            {
                                Vector3 d = (t.transform.position - v.transform.position);
                                float ang = Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg;
                                _fx.Spawn("Vfx/slash", v.transform.position + d.normalized * 0.5f + new Vector3(0, 0.5f, 0), 0.5f, 0.7f, 0.18f,
                                    Ui.ElementColor(e.Element), ang);
                            }
                        }
                        break;
                    }
                    case SimEventType.EnemyDeath:
                        App.Audio.Play("enemy_death", 0.45f, 0.1f, SoundCategory.Sfx, 0.05f);
                        _fx.Spawn("Vfx/impact_earth", p + new Vector3(0, 0.3f, 0), 0.3f, 0.9f, 0.3f, new Color(0.8f, 0.6f, 1f, 0.9f), Random.Range(0, 360));
                        if (e.Value >= 1f)
                        {
                            _fx.Spawn("Vfx/coin", p + new Vector3(0, 0.6f, 0), 0.35f, 0.25f, 0.6f, Color.white, 0, 0, new Vector3(0, 1.4f, 0));
                            App.Audio.Play("coin", 0.25f, 0.1f, SoundCategory.Sfx, 0.08f);
                        }
                        break;
                    case SimEventType.HeroDowned:
                        App.Audio.Play("hero_down", 0.9f, 0f);
                        _text.Add(p + new Vector3(0, 1.4f, 0), App.Loc.Get("hud.downed"), Ui.Bad, 32, 1.2f);
                        break;
                    case SimEventType.HeroRevived:
                        App.Audio.Play("hero_revive", 0.9f, 0f);
                        _fx.Spawn("Vfx/glow", p + new Vector3(0, 0.6f, 0), 0.5f, 3f, 0.7f, new Color(1f, 0.9f, 0.5f, 0.8f));
                        break;
                    case SimEventType.CrystalHit:
                        _crystalWobble = 0.25f;
                        Shake(e.Value > 60f ? 0.35f : 0.12f);
                        App.Audio.Play("crystal_hit", 0.6f, 0.05f, SoundCategory.Sfx, 0.12f);
                        if (numbers) _text.Add(new Vector3(Random.Range(-0.4f, 0.4f), 2.2f, 0), "-" + Mathf.RoundToInt(e.Value), Ui.Bad, 30, 0.9f);
                        break;
                    case SimEventType.Heal:
                        if (numbers && e.Value >= 10f) _text.Add(p + new Vector3(0, 1.1f, 0), "+" + Mathf.RoundToInt(e.Value), Ui.Good, 24, 0.8f);
                        break;
                    case SimEventType.Telegraph:
                        if (e.Id == "lane_mark")
                        {
                            LaneDef lane = Arena.Lanes[Mathf.Clamp(e.TargetUid, 0, Arena.Lanes.Count - 1)];
                            Banner(App.Loc.Format("hud.lane_marked", App.Loc.Get(lane.NameKey)), Ui.Bad, 1.8f);
                        }
                        if (e.Id == "BossSlam" || e.Id == "Meteor" || e.Id == "lane_mark") App.Audio.Play("telegraph", 0.6f, 0f, SoundCategory.Sfx, 0.3f);
                        _assist.Enabled = App.Settings.TelegraphAssist;
                        _assist.OnTelegraph(IsBossUid(b, e.SourceUid), e.Value, Time.unscaledTime);
                        break;
                    case SimEventType.BossPhase:
                        OnBossPhase(e);
                        break;
                    case SimEventType.EnemySpawn:
                        if (!reduced && Random.value < 0.35f) _fx.Spawn("Vfx/glow", p + new Vector3(0, 0.4f, 0), 0.6f, 1.6f, 0.35f, new Color(0.7f, 0.5f, 1f, 0.6f));
                        break;
                    case SimEventType.RelicProc:
                        if (!reduced && e.Id != null && App.Content.Relics.ContainsKey(e.Id) && Random.value < 0.5f)
                            _fx.Spawn("Relics/" + e.Id, p + new Vector3(0, 1.2f, 0), 0.25f, 0.3f, 0.7f, new Color(1, 1, 1, 0.9f), 0, 0, new Vector3(0, 0.8f, 0));
                        break;
                    case SimEventType.Taunt:
                        if (!reduced) _fx.Spawn("Vfx/ring", p + new Vector3(0, 0.1f, 0), 0.3f, e.Radius, 0.5f, new Color(1f, 0.5f, 0.3f, 0.7f), 0, 0, default, -20);
                        break;
                    case SimEventType.Miss:
                        if (numbers) _text.Add(p + new Vector3(0, 1f, 0), e.Id == "immune" ? "✦" : "miss", Ui.Muted, 20, 0.6f);
                        break;
                }
            }
        }

        private static string ReactionSound(string id)
        {
            if (App.Content.Reactions.TryGetValue(id, out ReactionDef def) && !string.IsNullOrEmpty(def.Sound)) return def.Sound;
            switch (id)
            {
                case "vaporize": case "melt": return "react_steam";
                case "overload": case "firestorm": return "react_explosion";
                case "electrocharge": case "magnetize": return "react_chain";
                case "freeze": case "superconduct": case "ice_spikes": return "react_freeze";
                case "rainstorm": case "thunderstorm": case "blizzard": case "sandstorm": return "react_storm";
                case "magma": case "mudfield": return "react_rumble";
                default: return "react_generic";
            }
        }

        private void OnReaction(SimEvent e, Vector3 p, bool reduced)
        {
            App.Audio.Play(ReactionSound(e.Id), 0.6f, 0.05f, SoundCategory.Sfx, 0.07f);
            _reactionStreak++;
            _streakTimer = 1.2f;
            if (_reactionStreak > 0 && _reactionStreak % 10 == 0) Banner(App.Loc.Format("hud.combo", _reactionStreak), Ui.Teal, 0.9f);
            float rad = Mathf.Max(0.8f, e.Radius);
            Color c = Ui.ElementColor(e.Element);
            if (!reduced || e.Generation <= 1)
                _fx.Spawn(ReactionIcon(e.Id), p + new Vector3(0, 0.9f, 0), 0.25f, 0.45f, 0.5f, new Color(1, 1, 1, 0.95f));
            if (!reduced) _fx.Spawn("Vfx/ring", p + new Vector3(0, 0.1f, 0), 0.3f, rad, 0.35f, c * new Color(1, 1, 1, 0.8f), 0, 0, default, -20);
            if (e.Id == "overload" || e.Id == "vaporize" || e.Id == "melt")
                _fx.Spawn("Vfx/impact_" + (e.Id == "vaporize" ? "water" : "fire"), p + new Vector3(0, 0.4f, 0), 0.4f, rad * 0.9f, 0.3f, Color.white, Random.Range(0, 360));
            // Callout text only for significant events, throttled per reaction type.
            _calloutCooldown.TryGetValue(e.Id, out float until);
            if (Time.unscaledTime >= until && e.Generation <= 1)
            {
                _calloutCooldown[e.Id] = Time.unscaledTime + 0.6f;
                _text.Add(p + new Vector3(0, 1.4f, 0), App.Loc.ReactionName(e.Id), Color.Lerp(c, Color.white, 0.35f), 26, 0.9f,
                    Art.Tex(ReactionIcon(e.Id)));
            }
        }

        /// <summary>Generated generic interactions share one icon; their name carries both elements.</summary>
        public static string ReactionIcon(string id)
        {
            return App.Content.Reactions.TryGetValue(id, out ReactionDef r) && r.AutoNamed ? "Icons/reaction_generic" : "Icons/reaction_" + id;
        }

        private void OnStrike(SimEvent e, Vector3 p, bool reduced)
        {
            switch (e.Id)
            {
                case "chain":
                case "storm_bolt":
                {
                    Vector3 from = e.Id == "chain" ? WorldGfx.V(e.From) + new Vector3(0, 0.5f, 0) : p + new Vector3(0, 3f, 0);
                    Vector3 to = p + new Vector3(0, 0.5f, 0);
                    Vector3 d = to - from;
                    float ang = Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg;
                    // projectile_lightning is 0.556 units long at PPU 230: scale it to span the arc
                    float len = Mathf.Max(0.3f, d.magnitude / 0.556f);
                    _fx.Spawn("Vfx/projectile_lightning", (from + to) / 2, len, len, 0.16f, Color.white, ang, 0, default, 40, true, 1.2f / len);
                    _fx.Spawn("Vfx/impact_lightning", to, 0.3f, 0.5f, 0.2f, Color.white);
                    break;
                }
                case "Meteor":
                    _fx.Spawn("Vfx/impact_fire", p + new Vector3(0, 0.3f, 0), e.Radius * 0.4f, e.Radius * 1.1f, 0.45f, Color.white, Random.Range(0, 360));
                    _fx.Spawn("Vfx/ring", p, 0.2f, e.Radius, 0.4f, new Color(1f, 0.6f, 0.2f, 0.8f), 0, 0, default, -20);
                    Shake(0.3f);
                    App.Audio.Play("react_explosion", 0.9f, 0.05f);
                    break;
                case "IceSpike":
                    _fx.Spawn("Vfx/impact_ice", p + new Vector3(0, 0.3f, 0), 0.3f, e.Radius * 1.2f, 0.3f, Color.white, Random.Range(0, 360));
                    break;
                case "Aftershock":
                case "shatter":
                    _fx.Spawn("Vfx/ring", p, 0.3f, Mathf.Max(1f, e.Radius), 0.4f, Ui.ElementColor(e.Element), 0, 0, default, -20);
                    _fx.Spawn("Vfx/impact_" + (e.Id == "shatter" ? "ice" : "earth"), p + new Vector3(0, 0.3f, 0), 0.4f, e.Radius, 0.3f, Color.white);
                    App.Audio.Play(e.Id == "shatter" ? "react_freeze" : "react_rumble", 0.6f);
                    break;
                case "BossSlam":
                case "BossLaneMark":
                    _fx.Spawn("Vfx/impact_earth", p + new Vector3(0, 0.3f, 0), e.Radius * 0.5f, e.Radius * 1.3f, 0.4f, new Color(1f, 0.6f, 0.8f), Random.Range(0, 360));
                    Shake(0.4f);
                    App.Audio.Play("react_rumble", 0.9f);
                    break;
                case "relic_burst":
                    _fx.Spawn("Vfx/ring", p, 0.3f, e.Radius, 0.35f, Ui.ElementColor(e.Element), 0, 0, default, -20);
                    _fx.Spawn("Vfx/impact_" + (e.Element == Element.None ? "earth" : ElementUtil.Key(e.Element)), p + new Vector3(0, 0.3f, 0), 0.4f, e.Radius * 0.8f, 0.3f, Color.white);
                    break;
                default:
                    if (e.Radius > 0f)
                    {
                        string el = e.Element == Element.None ? "earth" : ElementUtil.Key(e.Element);
                        _fx.Spawn("Vfx/impact_" + el, p + new Vector3(0, 0.3f, 0), 0.4f, e.Radius, 0.3f, Color.white, Random.Range(0, 360));
                    }
                    break;
            }
        }

        private void OnBossPhase(SimEvent e)
        {
            var l = App.Loc;
            switch (e.Id)
            {
                case "golem_armor": Banner(l.Get("hud.armor_up"), Ui.Gold, 1.6f); break;
                case "golem_exposed": Banner(l.Get("hud.armor_down"), Ui.Good, 1.6f); break;
                case "warden_exposed": Banner(l.Get("hud.exposed"), Ui.Good, 1.8f); break;
                default:
                    if (e.Id != null && e.Id.StartsWith("warden_phase_"))
                    {
                        Banner(l.Format("hud.boss_phase", e.Id.Substring("warden_phase_".Length)), Ui.Bad, 2f);
                        App.Audio.Play("boss_roar", 1f, 0f);
                        Shake(0.5f);
                    }
                    else if (e.Id != null && l.Has("hud." + e.Id))
                    {
                        // Data-named boss phases: "*_vent"/"*_exposed" are counter windows (green), others threats (red).
                        bool window = e.Id.EndsWith("_vent") || e.Id.EndsWith("_exposed");
                        Banner(l.Get("hud." + e.Id), window ? Ui.Good : Ui.Bad, 2f);
                        if (!window)
                        {
                            App.Audio.Play("boss_roar", 1f, 0f);
                            Shake(0.45f);
                        }
                    }
                    break;
            }
        }

        private void OnNotice(string key)
        {
            App.Audio.Play(key == "notice.evolved" ? "evolution" : "level_up", 0.8f, 0f, SoundCategory.Ui);
            Banner(App.Loc.Get(key), Ui.Gold, 1.4f);
        }

        public void Banner(string text, Color color, float time)
        {
            _bannerText = text;
            _bannerColor = color;
            _bannerTime = time;
        }

        private void ShowPrepareBanner()
        {
            if (_rc.State.Phase != RunPhase.Prepare) return;
            WaveDef w = _rc.CurrentWave;
            Banner(App.Loc.Format("prep.title", w.Number), Ui.Gold, 1.6f);
            App.Audio.PlayMusic(_rc.Biome.Music);
        }

        private void Shake(float amount)
        {
            if (!App.Settings.ScreenShake) return;
            _shake = Mathf.Min(0.6f, Mathf.Max(_shake, amount * (Application.isMobilePlatform ? 0.5f : 1f)));
        }

        private void UpdateShake(float dt)
        {
            _shake = Mathf.Max(0f, _shake - dt * 1.8f);
            Vector2 o = _shake > 0f ? Random.insideUnitCircle * _shake * 0.35f : Vector2.zero;
            _cam.transform.position = new Vector3(o.x, o.y, -10f);
        }

        // ------------------------------------------------------------------ view sync: battle

        private UnitView RentUnit()
        {
            UnitView v = _unitPool.Count > 0 ? _unitPool.Pop() : UnitView.Create(_unitsRoot);
            return v;
        }

        private void ReturnUnit(UnitView v)
        {
            v.Release();
            _unitPool.Push(v);
        }

        private SpriteRenderer RentSr(string sprite)
        {
            SpriteRenderer r = _srPool.Count > 0 ? _srPool.Pop() : WorldGfx.NewSprite(_fxRoot, "Sr", null, 0);
            r.gameObject.SetActive(true);
            r.sprite = Art.Sprite(sprite);
            r.color = Color.white;
            r.transform.rotation = Quaternion.identity;
            r.transform.localScale = Vector3.one;
            return r;
        }

        private void ReturnSr(SpriteRenderer r)
        {
            r.gameObject.SetActive(false);
            _srPool.Push(r);
        }

        private void SyncBattleViews(float dt)
        {
            Battle b = _rc.Battle;
            float viewDt = _paused || _modalOpen ? 0f : dt * _assist.EffectiveSpeed(_speed, Time.unscaledTime);
            _seen.Clear();
            foreach (HeroUnit h in b.Heroes)
            {
                if (!_units.TryGetValue(h.Uid, out UnitView v))
                {
                    v = RentUnit();
                    v.SetupHero(h.Def, h.EvolutionId);
                    v.Uid = h.Uid;
                    _units[h.Uid] = v;
                }
                _seen.Add(h.Uid);
                v.Sync(WorldGfx.V(h.Pos), h.Facing.X, h.HpFraction, h.MaxHp > 0 ? h.Shield / h.MaxHp : 0f, h.Alive, true, h.StunTimer > 0f,
                    Element.None, Element.None, viewDt);
            }
            foreach (EnemyUnit e in b.Enemies)
            {
                if (!e.Alive) continue;
                if (!_units.TryGetValue(e.Uid, out UnitView v))
                {
                    v = RentUnit();
                    v.SetupEnemy(e.Def, e.Elite, e.Affix);
                    v.Uid = e.Uid;
                    _units[e.Uid] = v;
                }
                _seen.Add(e.Uid);
                e.DominantStatuses(out Element s1, out Element s2);
                v.Sync(WorldGfx.V(e.Pos), e.Facing.X, e.HpFraction, e.MaxHp > 0 ? e.Shield / e.MaxHp : 0f, true, e.Elite || e.IsBoss, e.Stunned, s1, s2, viewDt);
            }
            _remove.Clear();
            foreach (var kv in _units) if (!_seen.Contains(kv.Key)) _remove.Add(kv.Key);
            foreach (int id in _remove)
            {
                ReturnUnit(_units[id]);
                _units.Remove(id);
            }

            // projectiles
            _seen.Clear();
            foreach (Projectile p in b.Projectiles)
            {
                if (!p.Alive) continue;
                if (!_projectiles.TryGetValue(p.Uid, out SpriteRenderer r))
                {
                    string sprite = p.Visual == "fireball" ? "Vfx/fireball" : (p.Visual == "pierce_arrow" ? "Vfx/arrow" :
                        "Vfx/projectile_" + (p.Damage.Element == Element.None ? "earth" : ElementUtil.Key(p.Damage.Element)));
                    r = RentSr(sprite);
                    float scale = p.Visual == "fireball" ? 1.1f : (p.Kind == ProjectileKind.Pierce ? 1.1f : 0.9f);
                    r.transform.localScale = Vector3.one * scale;
                    _projectiles[p.Uid] = r;
                }
                _seen.Add(p.Uid);
                r.transform.position = WorldGfx.V(p.Pos) + new Vector3(0, 0.55f, 0);
                r.transform.rotation = Quaternion.Euler(0, 0, Mathf.Atan2(p.Dir.Y, p.Dir.X) * Mathf.Rad2Deg);
                r.sortingOrder = WorldGfx.OrderFor(p.Pos.Y) + 8;
            }
            ReleaseUnseen(_projectiles);

            // zones (ground effects)
            _seen.Clear();
            foreach (Zone z in b.Zones)
            {
                if (!_zones.TryGetValue(z.Uid, out SpriteRenderer r))
                {
                    r = RentSr(z.Kind == ZoneKind.Field ? "Vfx/field_" + z.Field.Id : "Vfx/zone_" + ZoneSprite(z.Kind));
                    _zones[z.Uid] = r;
                }
                _seen.Add(z.Uid);
                float k = z.Duration > 0 ? z.Remaining / z.Duration : 1f;
                float grow = Mathf.Clamp01((z.Duration - z.Remaining) / 0.2f);
                if (z.Line)
                {
                    // Line fields (river channels, walls): stretched along the segment.
                    Vector3 a = WorldGfx.V(z.Pos), c = WorldGfx.V(z.End);
                    r.transform.position = (a + c) * 0.5f;
                    r.transform.rotation = Quaternion.Euler(0, 0, Mathf.Atan2(c.y - a.y, c.x - a.x) * Mathf.Rad2Deg);
                    r.transform.localScale = new Vector3((Vector3.Distance(a, c) * 0.5f + z.Radius) * grow, z.Radius * grow, 1f);
                }
                else
                {
                    r.transform.position = WorldGfx.V(z.Pos);
                    r.transform.localScale = new Vector3(z.Radius * grow, z.Radius * 0.62f * grow, 1f);
                }
                if (z.Kind == ZoneKind.Vortex) r.transform.Rotate(0, 0, -240f * viewDt);
                r.color = new Color(1, 1, 1, Mathf.Clamp01(k * 3f) * (App.Settings.ReducedVfx ? 0.55f : 0.9f));
                r.sortingOrder = -8000;
            }
            ReleaseUnseen(_zones);

            // telegraphs for delayed strikes (meteors, spikes, boss slams)
            _liveStrikes.Clear();
            foreach (DelayedStrike ds in b.Strikes) _liveStrikes.Add(ds);
            _goneStrikes.Clear();
            foreach (var kv in _strikes) if (!_liveStrikes.Contains(kv.Key)) _goneStrikes.Add(kv.Key);
            foreach (DelayedStrike s in _goneStrikes)
            {
                ReturnSr(_strikes[s]);
                _strikes.Remove(s);
            }
            foreach (DelayedStrike s in b.Strikes)
            {
                if (!_strikes.TryGetValue(s, out SpriteRenderer r))
                {
                    r = RentSr("Vfx/telegraph");
                    _strikes[s] = r;
                }
                bool danger = s.Kind == StrikeKind.BossSlam || s.Kind == StrikeKind.BossLaneMark || s.Kind == StrikeKind.Hazard;
                float k = s.Total > 0 ? 1f - s.Delay / s.Total : 1f;
                r.transform.position = WorldGfx.V(s.Pos);
                r.transform.localScale = new Vector3(s.Radius, s.Radius * 0.62f, 1f) * (0.85f + 0.15f * k);
                r.color = danger ? new Color(1f, 0.25f, 0.3f, 0.45f + 0.4f * k) : new Color(1f, 0.75f, 0.3f, 0.35f + 0.35f * k);
                r.sortingOrder = -7900;
            }

            // enemy bolts
            _liveBolts.Clear();
            foreach (EnemyBolt eb in b.Bolts) _liveBolts.Add(eb);
            _goneBolts.Clear();
            foreach (var kv in _bolts) if (!_liveBolts.Contains(kv.Key)) _goneBolts.Add(kv.Key);
            foreach (EnemyBolt bolt in _goneBolts)
            {
                ReturnSr(_bolts[bolt]);
                _bolts.Remove(bolt);
            }
            foreach (EnemyBolt bolt in b.Bolts)
            {
                if (!_bolts.TryGetValue(bolt, out SpriteRenderer r))
                {
                    r = RentSr("Vfx/spark");
                    r.color = new Color(0.55f, 1f, 0.45f);
                    r.transform.localScale = Vector3.one * 0.9f;
                    _bolts[bolt] = r;
                }
                r.transform.position = WorldGfx.V(bolt.Pos) + new Vector3(0, 0.6f, 0);
                r.sortingOrder = WorldGfx.OrderFor(bolt.Pos.Y) + 8;
            }
        }

        private void ReleaseUnseen(Dictionary<int, SpriteRenderer> map)
        {
            _remove.Clear();
            foreach (var kv in map) if (!_seen.Contains(kv.Key)) _remove.Add(kv.Key);
            foreach (int id in _remove)
            {
                ReturnSr(map[id]);
                map.Remove(id);
            }
        }

        private static string ZoneSprite(ZoneKind k)
        {
            switch (k)
            {
                case ZoneKind.Magma: return "magma";
                case ZoneKind.Mud: return "mud";
                case ZoneKind.Thunderstorm: return "thunderstorm";
                case ZoneKind.Blizzard: return "blizzard";
                case ZoneKind.HealingRain: return "healing_rain";
                case ZoneKind.Vortex: return "vortex";
                case ZoneKind.BurningGround: return "burning_ground";
                case ZoneKind.StormTrail: return "storm_trail";
                default: return "tempest_link";
            }
        }

        private void ClearBattleViews()
        {
            foreach (UnitView v in _units.Values) ReturnUnit(v);
            _units.Clear();
            foreach (SpriteRenderer r in _projectiles.Values) ReturnSr(r);
            _projectiles.Clear();
            foreach (SpriteRenderer r in _zones.Values) ReturnSr(r);
            _zones.Clear();
            foreach (SpriteRenderer r in _strikes.Values) ReturnSr(r);
            _strikes.Clear();
            foreach (SpriteRenderer r in _bolts.Values) ReturnSr(r);
            _bolts.Clear();
            _fx.Clear();
            _text.Entries.Clear();
        }

        // ------------------------------------------------------------------ view sync: preparation

        private void SyncPrepViews(float dt)
        {
            _seen.Clear();
            foreach (HeroRunState h in _rc.State.Heroes)
            {
                if (h.Node < 0) continue;
                if (!_prepViews.TryGetValue(h.Uid, out UnitView v))
                {
                    v = RentUnit();
                    v.SetupHero(App.Content.Heroes[h.DefId], h.EvolutionId);
                    v.Uid = h.Uid;
                    _prepViews[h.Uid] = v;
                }
                else if (_prepEvo.TryGetValue(h.Uid, out string evo) && evo != h.EvolutionId)
                {
                    v.SetupHero(App.Content.Heroes[h.DefId], h.EvolutionId);
                }
                _prepEvo[h.Uid] = h.EvolutionId;
                _seen.Add(h.Uid);
                Vector3 pos = h.Uid == _dragUid ? _dragPos : WorldGfx.V(Arena.Nodes[h.Node]);
                v.Sync(pos, pos.x >= 0 ? -1f : 1f, h.Downed ? 0f : h.HpFraction, 0f, !h.Downed, true, false, Element.None, Element.None, dt);
                if (h.Uid == _selectedUid) v.Body.color = new Color(1f, 1f, 0.75f);
            }
            _remove.Clear();
            foreach (var kv in _prepViews) if (!_seen.Contains(kv.Key)) _remove.Add(kv.Key);
            foreach (int id in _remove)
            {
                ReturnUnit(_prepViews[id]);
                _prepViews.Remove(id);
            }
        }

        private readonly Dictionary<int, string> _prepEvo = new Dictionary<int, string>();

        private void ClearPrepViews()
        {
            foreach (UnitView v in _prepViews.Values) ReturnUnit(v);
            _prepViews.Clear();
            _dragUid = -1;
            _selectedUid = -1;
        }

        private void UpdateNodes()
        {
            bool prep = _rc.State.Phase == RunPhase.Prepare;
            for (int i = 0; i < _nodes.Count; i++)
            {
                HeroRunState occ = _rc.State.HeroOnNode(i);
                string sprite = occ != null ? "World/node_occupied" : "World/node_empty";
                if (prep && (_dragUid >= 0 || _selectedUid >= 0) && NearestNode(_dragUid >= 0 ? _dragPos : Vector3.one * 999f) == i) sprite = "World/node_highlight";
                else if (prep && _selectedUid >= 0 && occ == null) sprite = "World/node_highlight";
                if (i == _rc.State.BlockedNode)
                {
                    // Ascension blocked node: dark red, no highlight, cannot be used this wave.
                    _nodes[i].sprite = Art.Sprite("World/node_empty");
                    _nodes[i].color = new Color(0.9f, 0.2f, 0.25f, prep ? 0.85f : 0.4f);
                    continue;
                }
                _nodes[i].sprite = Art.Sprite(sprite);
                float pulse = prep && occ == null ? 0.75f + 0.25f * Mathf.Sin(Time.time * 3f + i) : 0.45f;
                Color tint = NodeTraitTint(i);
                tint.a = prep ? pulse : 0.35f;
                _nodes[i].color = tint;
            }
        }

        /// <summary>Biome node traits read at a glance: warm for heated bridges, icy for frozen tiles.</summary>
        private Color NodeTraitTint(int node)
        {
            if (!_rc.Biome.NodeTraitIds.TryGetValue(node, out string trait)) return Color.white;
            switch (trait)
            {
                case "heated_bridge": return new Color(1f, 0.62f, 0.35f);
                case "frozen_tile": return new Color(0.6f, 0.88f, 1f);
                case "aether_node": return new Color(1f, 0.55f, 0.95f);
                case "lightning_rod": return new Color(1f, 0.95f, 0.45f);
                case "archive_tome": return new Color(0.55f, 0.85f, 1f);
                default: return new Color(1f, 0.95f, 0.6f);
            }
        }

        private void UpdateLaneArrows()
        {
            bool prep = _rc.State.Phase == RunPhase.Prepare;
            int needed = 0;
            if (prep)
            {
                WaveDef w = _rc.CurrentWave;
                foreach (int laneIndex in Battle.LanesForWave(w, _rc.Biome))
                {
                    LaneDef lane = Arena.Lanes[laneIndex % Arena.Lanes.Count];
                    for (int k = 0; k < 3; k++)
                    {
                        float t = (k + (Time.time * 0.8f % 1f)) / 3f;
                        Vector3 a = WorldGfx.V(lane.Points[0]), b = WorldGfx.V(lane.Points[1]), c = WorldGfx.V(lane.Points[2]);
                        Vector3 pos = t < 0.5f ? Vector3.Lerp(a, b, t * 2f) : Vector3.Lerp(b, c, (t - 0.5f) * 2f);
                        Vector3 dir = t < 0.5f ? b - a : c - b;
                        // keep arrows on screen even when spawns are off-camera
                        float halfH = _cam.orthographicSize - 0.6f, halfW = halfH * _cam.aspect - 0.6f;
                        pos.x = Mathf.Clamp(pos.x, -halfW, halfW);
                        pos.y = Mathf.Clamp(pos.y, -halfH, halfH);
                        SpriteRenderer r;
                        if (needed < _laneArrows.Count) r = _laneArrows[needed];
                        else
                        {
                            r = WorldGfx.NewSprite(_world, "LaneArrow", Art.Sprite("World/lane_arrow"), 9000);
                            _laneArrows.Add(r);
                        }
                        r.gameObject.SetActive(true);
                        r.transform.position = pos;
                        r.transform.rotation = Quaternion.Euler(0, 0, Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg);
                        r.color = new Color(1, 1, 1, Mathf.Sin(t * Mathf.PI) * 0.9f);
                        needed++;
                    }
                }
            }
            for (int i = needed; i < _laneArrows.Count; i++) _laneArrows[i].gameObject.SetActive(false);
        }

        private void UpdateCrystal(float dt)
        {
            float frac = _rc.State.Phase == RunPhase.Battle && _rc.Battle != null ? _rc.Battle.Crystal.HpFraction : _rc.State.CrystalHp / Mathf.Max(1f, _rc.CrystalMaxHp);
            _crystal.sprite = Art.Sprite(frac > 0.6f ? "World/crystal_intact" : (frac > 0.25f ? "World/crystal_cracked" : "World/crystal_critical"));
            _crystalWobble = Mathf.Max(0f, _crystalWobble - dt);
            float hover = Mathf.Sin(Time.time * 1.6f) * 0.04f;
            _crystal.transform.position = new Vector3(Mathf.Sin(_crystalWobble * 60f) * _crystalWobble * 0.3f, -0.55f + hover, 0);
            WorldGfx.SetFlash(_crystal, _crystalWobble > 0f ? _crystalWobble * 2.5f : 0f, new Color(1f, 0.6f, 0.6f));
            bool shield = _rc.Battle != null && _rc.State.Phase == RunPhase.Battle && _rc.Battle.Crystal.Shield > 1f;
            _crystalShield.enabled = shield;
            if (shield)
            {
                _crystalShield.color = new Color(0.55f, 0.9f, 1f, 0.5f + 0.2f * Mathf.Sin(Time.time * 5f));
                _crystalShield.transform.localScale = new Vector3(1.6f, 1.6f, 1f);
            }
        }

        // ------------------------------------------------------------------ placement input

        private Vector3 PointerWorld()
        {
            Vector3 m = Input.mousePosition;
            Vector3 w = _cam.ScreenToWorldPoint(new Vector3(m.x, m.y, 10f));
            w.z = 0f;
            return w;
        }

        private bool PointerOverUi()
        {
            Vector2 gui = new Vector2(Input.mousePosition.x, Screen.height - Input.mousePosition.y);
            foreach (Rect r in _uiBlockers) if (r.Contains(gui)) return true;
            return false;
        }

        public int NearestNode(Vector3 world, float maxDist = 1.1f)
        {
            int best = -1;
            float bestD = maxDist;
            for (int i = 0; i < Arena.Nodes.Count; i++)
            {
                float d = Vector2.Distance(world, WorldGfx.V(Arena.Nodes[i]));
                if (d < bestD) { bestD = d; best = i; }
            }
            return best;
        }

        private int HeroAt(Vector3 world)
        {
            foreach (HeroRunState h in _rc.State.Heroes)
            {
                if (h.Node < 0) continue;
                Vector3 p = WorldGfx.V(Arena.Nodes[h.Node]) + new Vector3(0, 0.6f, 0);
                if (Vector2.Distance(world, p) < 0.8f) return h.Uid;
            }
            return -1;
        }

        private void HandlePlacementInput()
        {
            if (_modalOpen || OverlayOpen) return;
            Vector3 w = PointerWorld();
            if (Input.GetMouseButtonDown(0) && !PointerOverUi())
            {
                int hero = HeroAt(w);
                if (hero >= 0)
                {
                    _dragUid = hero;
                    _dragPos = w;
                    _dragMoved = false;
                }
                else if (_selectedUid >= 0)
                {
                    int node = NearestNode(w);
                    if (node >= 0 && _rc.PlaceHero(_selectedUid, node)) App.Audio.Ui("ui_card");
                    _selectedUid = -1;
                }
            }
            if (_dragUid >= 0 && Input.GetMouseButton(0))
            {
                if (Vector2.Distance(_dragPos, w) > 0.15f) _dragMoved = true;
                _dragPos = w;
            }
            if (_dragUid >= 0 && Input.GetMouseButtonUp(0))
            {
                if (_dragMoved)
                {
                    int node = NearestNode(w);
                    if (node >= 0 && _rc.PlaceHero(_dragUid, node)) App.Audio.Ui("ui_card");
                    _selectedUid = -1;
                }
                else
                {
                    // tap-to-select alternative (accessibility): tap hero, then tap a node
                    _selectedUid = _selectedUid == _dragUid ? -1 : _dragUid;
                }
                _dragUid = -1;
            }
        }

        private bool _dragMoved;

        // ------------------------------------------------------------------ accessors for overlay/UI

        public RunController Run => _rc;
        public Camera Cam => _cam;
        public bool Paused => _paused;
    }
}
