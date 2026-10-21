using System.Collections.Generic;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Presentation;
using UnityEngine;

namespace Aetherward.Game
{
    /// <summary>Shared sprite material (flash-capable) and sorting helpers.</summary>
    public static class WorldGfx
    {
        /// <summary>Unit sprite scale: the dynamic-party camera sees a wider field, so units are drawn a bit larger.</summary>
        public const float UnitScale = 1.5f;

        private static Material _mat;
        private static MaterialPropertyBlock _mpb;
        public static readonly int FlashId = Shader.PropertyToID("_Flash");
        public static readonly int FlashColorId = Shader.PropertyToID("_FlashColor");
        public static readonly int DissolveId = Shader.PropertyToID("_Dissolve");

        public static Material SpriteMaterial
        {
            get
            {
                if (_mat == null)
                {
                    Shader s = Resources.Load<Shader>("Shaders/SpriteFlash");
                    if (s == null) s = Shader.Find("Sprites/Default");
                    _mat = new Material(s);
                }
                return _mat;
            }
        }

        private static Material _unitMat, _shadowMat, _additiveMat;

        /// <summary>Additive glow/flame material (SpriteAdditive); falls back to the shared sprite material.</summary>
        public static Material AdditiveMaterial
        {
            get
            {
                if (_additiveMat == null)
                {
                    Shader s = Resources.Load<Shader>("Shaders/SpriteAdditive");
                    _additiveMat = s != null ? new Material(s) : SpriteMaterial;
                }
                return _additiveMat;
            }
        }

        /// <summary>Directional cast shadows of units (SpriteCastShadow); null when the shader is missing.</summary>
        public static Material ShadowMaterial
        {
            get
            {
                if (_shadowMat == null)
                {
                    Shader s = Resources.Load<Shader>("Shaders/SpriteCastShadow");
                    if (s != null) _shadowMat = new Material(s);
                }
                return _shadowMat;
            }
        }

        /// <summary>
        /// Light of the current battlefield (from its env_meta: the Blender sun the background was rendered with), so unit
        /// shadows fall the same way as the painted props. screenLengthPerHeight is per unit of on-screen sprite height.
        /// </summary>
        public static void ApplyEnvironmentLight(Vector2 shadowDir, float screenLengthPerHeight, float strength)
        {
            Shader.SetGlobalVector("_AwShadowDir", shadowDir.sqrMagnitude > 1e-4f ? shadowDir.normalized : new Vector2(0.8f, 0.6f));
            Shader.SetGlobalFloat("_AwShadowLength", screenLengthPerHeight);
            Shader.SetGlobalFloat("_AwShadowStrength", strength);
            Shader.SetGlobalFloat("_AwShadowHeight", 1.6f);
        }

        /// <summary>Hero/enemy bodies: SpriteLive (flash + readability rim + dissolve). Falls back to the shared material.</summary>
        public static Material UnitMaterial
        {
            get
            {
                if (_unitMat == null)
                {
                    Shader s = Resources.Load<Shader>("Shaders/SpriteLive");
                    _unitMat = s != null ? new Material(s) : SpriteMaterial;
                }
                return _unitMat;
            }
        }

        /// <summary>Readability rim on unit sprites (global so units keep batching). High contrast doubles it.</summary>
        public static void ApplyRim(bool highContrast)
        {
            Shader.SetGlobalColor("_AwRimColor", new Color(0.62f, 0.91f, 1f, 1f));
            Shader.SetGlobalFloat("_AwRimStrength", highContrast ? 1.2f : 0.7f);
            Shader.SetGlobalFloat("_AwRimWidthPx", 6f);   // texels; a 400 px hero is ~144 px on a 1080p screen
            Shader.SetGlobalVector("_AwRimDir", new Vector4(1f, 0.55f, 0f, 0f));
        }

        public static SpriteRenderer NewSprite(Transform parent, string name, Sprite sprite, int order)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            var r = go.AddComponent<SpriteRenderer>();
            r.sharedMaterial = SpriteMaterial;
            r.sprite = sprite;
            r.sortingOrder = order;
            return r;
        }

        /// <summary>Lower on screen = drawn in front. Each unit reserves 10 sorting slots.</summary>
        public static int OrderFor(float y) => 5000 - Mathf.RoundToInt(y * 100f) * 10;

        /// <summary>Accessibility: global multiplier on sprite flashes (Settings.FlashIntensity × effects preset).</summary>
        public static float FlashScale = 1f;

        /// <summary>Effects preset in force (Settings → Effects intensity, capped by the accessibility toggles).</summary>
        public static FeelProfile Feel = FeelProfile.For(EffectsPreset.Standard, true, 1f, false, false);

        public static void SetFlash(SpriteRenderer r, float amount, Color color)
        {
            amount *= FlashScale;
            if (_mpb == null) _mpb = new MaterialPropertyBlock();
            if (amount <= 0.001f)
            {
                if (r.HasPropertyBlock()) r.SetPropertyBlock(null);
                return;
            }
            _mpb.SetFloat(FlashId, amount);
            _mpb.SetColor(FlashColorId, color);
            r.SetPropertyBlock(_mpb);
        }

        public static Vector3 V(Sim.Core.Vec2 v, float z = 0f) => new Vector3(v.X, v.Y, z);
    }

    /// <summary>
    /// Visual for one hero or enemy: shadow, body (2-frame walk or pose swap), HP bar, up to two
    /// status icons, elite/affix ring. Animation is procedural (bob, squash, lunge, hit flash).
    /// </summary>
    public sealed class UnitView : MonoBehaviour
    {
        public SpriteRenderer Body;
        private SpriteRenderer _castShadow;
        private SpriteRenderer _shadow, _hpBg, _hpFill, _status1, _status2, _ring, _shieldFx;
        private Sprite _idle, _alt, _cast, _down, _attack, _tell, _walkA, _walkB, _windup, _follow, _idleB;
        private Sprite[] _cycle;          // walk cycle (2 or 4 key poses; R05 adds c/d)
        /// <summary>Set by the battle view each frame: the unit's next attack is about to land (shows the windup pose).</summary>
        public bool Windup;
        private bool _isHero;
        private float _baseScale = 1f;
        private float _phase;
        private float _castTimer, _lungeTimer, _flash, _hpShowTimer, _attackTimer;
        private float _spawnT = -1f, _dieT = -1f;   // dissolve in on spawn / out on death; < 0 = not playing
        private MaterialPropertyBlock _mpb;
        /// <summary>Set each frame by the battle view while a telegraphed strike from this unit is pending (boss tell pose).</summary>
        public bool Telegraphing;
        public const float AttackHold = 0.3f, SpawnTime = 0.35f, DeathTime = 0.4f;
        private const float ShadowBlobAlpha = 0.6f;   // contact occlusion under the feet; the cast shadow carries the light
        public bool Dying => _dieT >= 0f;
        private float _castT = -1f, _hitT = -1f;   // seconds into the cast / hit pose (UnitPose); < 0 = idle
        private bool _hitHeavy;
        private Vector3 _lungeDir, _hitDir;
        private float _walk;
        private Vector3 _lastPos;
        private Element _s1 = Element.None, _s2 = Element.None;
        public int Uid;
        private Vector3 _smoothPos;
        private float _speed;
        private bool _hasPos;
        public bool IsHero => _isHero;
        public bool InUse;

        public static UnitView Create(Transform parent)
        {
            var go = new GameObject("Unit");
            go.transform.SetParent(parent, false);
            var v = go.AddComponent<UnitView>();
            v._shadow = WorldGfx.NewSprite(go.transform, "Shadow", Art.Sprite("World/shadow"), 0);
            v._shadow.color = new Color(1, 1, 1, ShadowBlobAlpha);
            if (WorldGfx.ShadowMaterial != null)
            {
                v._castShadow = WorldGfx.NewSprite(go.transform, "CastShadow", null, 0);
                v._castShadow.sharedMaterial = WorldGfx.ShadowMaterial;
            }
            v._ring = WorldGfx.NewSprite(go.transform, "Ring", Art.Sprite("Vfx/ring"), 0);
            v.Body = WorldGfx.NewSprite(go.transform, "Body", null, 0);
            v.Body.sharedMaterial = WorldGfx.UnitMaterial;
            v._shieldFx = WorldGfx.NewSprite(go.transform, "Shield", Art.Sprite("Vfx/glow"), 0);
            v._hpBg = WorldGfx.NewSprite(go.transform, "HpBg", Art.Sprite("UI/bar_bg"), 0);
            v._hpFill = WorldGfx.NewSprite(go.transform, "HpFill", Art.Sprite("UI/bar_fill"), 0);
            v._status1 = WorldGfx.NewSprite(go.transform, "Status1", null, 0);
            v._status2 = WorldGfx.NewSprite(go.transform, "Status2", null, 0);
            v._status1.transform.localScale = v._status2.transform.localScale = Vector3.one * 0.75f;
            return v;
        }

        public void SetupHero(HeroDef def, string evolutionId)
        {
            _isHero = true;
            string evo = evolutionId == null ? null : (def.Evolutions.IndexOf(evolutionId) == 0 ? "A" : "B");
            _idle = Art.Sprite("Heroes/" + def.Id + (evo == null ? "_idle" : "_evo" + evo));
            _cast = Art.Sprite("Heroes/" + def.Id + (evo == null ? "_cast" : "_evo" + evo + "_cast"));
            _down = Art.Sprite("Heroes/" + def.Id + "_downed");
            _attack = Art.Optional("Heroes/" + def.Id + (evo == null ? "_attack" : "_evo" + evo + "_attack")) ?? _idle;
            _tell = null;
            _alt = _idle;
            // walk cycle (new with the dynamic party; arrives batch by batch, idle bob when absent)
            _walkA = evo == null ? Art.Optional("Heroes/" + def.Id + "_walk_a") : null;
            _walkB = _walkA != null ? Art.Optional("Heroes/" + def.Id + "_walk_b") ?? _idle : null;
            _cycle = Cycle(_walkA, _walkB, Art.Optional("Heroes/" + def.Id + "_walk_c"), Art.Optional("Heroes/" + def.Id + "_walk_d"));
            string pre = "Heroes/" + def.Id + (evo == null ? "" : "_evo" + evo);
            _windup = Art.Optional(pre + "_windup");
            _follow = Art.Optional(pre + "_follow");
            _idleB = Art.Optional(pre + "_idle_b");
            _baseScale = WorldGfx.UnitScale;
            _ring.enabled = true;
            _ring.color = Ui.ElementColor(def.Element) * new Color(1, 1, 1, 0.55f);
            _ring.transform.localScale = new Vector3(0.42f, 0.2f, 1);
            _shadow.transform.localScale = new Vector3(0.95f, 0.9f, 1);
            Init();
        }

        public void SetupEnemy(EnemyDef def, bool elite, string affix)
        {
            _isHero = false;
            _idle = Art.Sprite("Enemies/" + def.Id + "_a");
            _alt = Art.Sprite("Enemies/" + def.Id + "_b");
            _cast = _idle;
            _down = _idle;
            _attack = Art.Optional("Enemies/" + def.Id + "_attack") ?? _idle;
            _tell = def.Boss ? Art.Optional("Enemies/" + def.Id + "_tell") : null;
            bool big = def.Boss;
            _walkA = _walkB = null;
            _cycle = Cycle(_idle, _alt, Art.Optional("Enemies/" + def.Id + "_c"), Art.Optional("Enemies/" + def.Id + "_d"));
            _windup = Art.Optional("Enemies/" + def.Id + "_windup");
            _follow = null;
            _idleB = null;
            _baseScale = WorldGfx.UnitScale * (elite && !def.Elite && !def.Boss ? 1.3f : 1f) * (def.Id == "swarmling" ? 0.8f : 1f) * (big ? 1.25f : 1f);
            float shadowW = big ? 2.6f : (def.Radius * 2.4f) * _baseScale;
            _shadow.transform.localScale = new Vector3(shadowW, shadowW * 0.9f, 1);
            _ring.enabled = elite || !string.IsNullOrEmpty(affix);
            if (_ring.enabled)
            {
                _ring.color = AffixColor(affix, elite);
                float rw = (big ? 1.4f : def.Radius * 1.6f) * _baseScale;
                _ring.transform.localScale = new Vector3(rw, rw * 0.5f, 1);
            }
            Init();
            _spawnT = 0f;
        }

        private static Color AffixColor(string affix, bool elite)
        {
            switch (affix)
            {
                case "fireproof": return new Color(1f, 0.4f, 0.2f, 0.85f);
                case "tideproof": return new Color(0.3f, 0.6f, 1f, 0.85f);
                case "stormproof": return new Color(0.75f, 0.45f, 1f, 0.85f);
                case "frostproof": return new Color(0.6f, 0.9f, 1f, 0.85f);
                case "windproof": return new Color(0.4f, 1f, 0.7f, 0.85f);
                case "earthbound": return new Color(0.9f, 0.65f, 0.3f, 0.85f);
                default: return elite ? new Color(1f, 0.8f, 0.3f, 0.9f) : new Color(1, 1, 1, 0.6f);
            }
        }

        private void Init()
        {
            Body.sprite = _idle;
            Body.color = Color.white;
            _shadow.color = new Color(1, 1, 1, ShadowBlobAlpha);   // a death fade may have cleared it on a pooled view
            if (_castShadow != null) _castShadow.color = Color.white;
            _phase = Random.value * 6f;
            _castTimer = _lungeTimer = _flash = _hpShowTimer = _attackTimer = 0f;
            _hasPos = false;
            _speed = 0f;
            _castT = _hitT = _spawnT = _dieT = -1f;
            Telegraphing = false;
            _s1 = _s2 = Element.None;
            _status1.enabled = _status2.enabled = false;
            _shieldFx.enabled = false;
            gameObject.SetActive(true);
            InUse = true;
            _lastPos = transform.position;
            SetBodyProps(0f, 0f);
        }

        /// <summary>The cast shadow uses the body's current pose sprite, grounded at the feet (no bob/lunge), same facing.</summary>
        private void SyncCastShadow(float flip)
        {
            if (_castShadow == null) return;
            _castShadow.enabled = Body.sprite != null;
            _castShadow.sprite = Body.sprite;
            _castShadow.transform.localPosition = Vector3.zero;
            _castShadow.transform.localScale = new Vector3(flip * _baseScale, _baseScale, 1f);
        }

        /// <summary>Flash and dissolve share one property block; none at all while idle so bodies keep batching.</summary>
        private void SetBodyProps(float flash, float dissolve)
        {
            flash *= WorldGfx.FlashScale;
            if (flash <= 0.001f && dissolve <= 0.001f)
            {
                if (Body.HasPropertyBlock()) Body.SetPropertyBlock(null);
                return;
            }
            if (_mpb == null) _mpb = new MaterialPropertyBlock();
            _mpb.SetFloat(WorldGfx.FlashId, flash);
            _mpb.SetColor(WorldGfx.FlashColorId, Color.white);
            _mpb.SetFloat(WorldGfx.DissolveId, dissolve);
            Body.SetPropertyBlock(_mpb);
        }

        /// <summary>The basic-attack strike pose (heroes: BasicAttack; enemies: the moment their hit lands).</summary>
        public void Attack() => _attackTimer = AttackHold;

        private static Sprite[] Cycle(Sprite a, Sprite b, Sprite c, Sprite d)
        {
            if (a == null) return null;
            if (c != null && d != null) return new[] { a, b ?? a, c, d };
            return b != null && b != a ? new[] { a, b } : null;
        }

        /// <summary>Enemy killed: plays the dissolve-out; <see cref="TickDeath"/> returns false when it is finished.</summary>
        public void BeginDeath()
        {
            if (_dieT < 0f) _dieT = 0f;
            _hpBg.enabled = _hpFill.enabled = _status1.enabled = _status2.enabled = _shieldFx.enabled = _ring.enabled = false;
        }

        public bool TickDeath(float dt)
        {
            _dieT += dt;
            float k = Mathf.Clamp01(_dieT / DeathTime);
            _shadow.color = new Color(1, 1, 1, ShadowBlobAlpha * (1f - k));
            if (_castShadow != null) _castShadow.color = new Color(1, 1, 1, 1f - k);
            Body.transform.localPosition += new Vector3(0, -dt * 0.15f, 0);
            SetBodyProps(0f, WorldGfx.Feel.AnimAmplitude > 0f ? k : 1f);
            return _dieT < DeathTime;
        }

        public void Release()
        {
            InUse = false;
            gameObject.SetActive(false);
        }

        public void Cast(float duration = UnitPose.CastDuration)
        {
            _castTimer = duration;
            _castT = 0f;
        }

        /// <summary>Recoil away from <paramref name="from"/> (attacker or impact centre); heavy = crit or big hit.</summary>
        public void Hit(Vector3 from, bool heavy)
        {
            if (_hitT >= 0f && !heavy) return;   // a light hit never restarts a recoil already playing
            Vector3 d = transform.position - from;
            d.z = 0f;
            _hitDir = d.sqrMagnitude > 1e-4f ? d.normalized : Vector3.right;
            _hitT = 0f;
            _hitHeavy = heavy;
        }

        public void Lunge(Vector3 toward)
        {
            _lungeTimer = 0.18f;
            _lungeDir = (toward - transform.position).normalized;
        }

        public void Flash(float amount = 1f)
        {
            _flash = Mathf.Max(_flash, amount);
            _hpShowTimer = 2.5f;
        }

        /// <summary>Per-frame sync from simulation state.</summary>
        public void Sync(Vector3 pos, float facingX, float hpFraction, float shieldFraction, bool alive, bool alwaysShowHp, bool stunned, Element status1, Element status2, float dt)
        {
            // the sim steps at 30 Hz: smooth the drawn position and the speed estimate, or units stutter and flicker
            // between walk and idle poses at 60+ fps. Teleports (spawn, dash > 2 units) snap.
            float raw = (pos - _lastPos).magnitude / Mathf.Max(dt, 0.0001f);
            bool snap = !_hasPos || (pos - _lastPos).sqrMagnitude > 4f;
            _lastPos = pos;
            _smoothPos = snap ? pos : Vector3.Lerp(_smoothPos, pos, 1f - Mathf.Exp(-22f * dt));
            _speed = snap ? 0f : Mathf.Lerp(_speed, Mathf.Min(raw, 12f), 1f - Mathf.Exp(-9f * dt));
            _hasPos = true;
            float speed = _speed;
            pos = _smoothPos;
            transform.position = pos;
            int order = WorldGfx.OrderFor(pos.y);
            _shadow.sortingOrder = order;
            if (_castShadow != null) _castShadow.sortingOrder = order;
            _ring.sortingOrder = order + 1;
            Body.sortingOrder = order + 2;
            _shieldFx.sortingOrder = order + 3;
            _hpBg.sortingOrder = order + 4;
            _hpFill.sortingOrder = order + 5;
            _status1.sortingOrder = _status2.sortingOrder = order + 6;

            Transform bt = Body.transform;
            if (!alive)
            {
                Body.sprite = _down;
                bt.localPosition = Vector3.zero;
                bt.localScale = Vector3.one * _baseScale;
                SyncCastShadow(1f);
                Body.color = _isHero ? Color.white : new Color(1, 1, 1, 0.5f);
                _hpBg.enabled = _hpFill.enabled = false;
                _status1.enabled = _status2.enabled = false;
                _shieldFx.enabled = false;
                SetBodyProps(0f, 0f);
                return;
            }

            _phase += dt * (speed > 0.2f ? 9f : 2.6f);
            _castTimer -= dt;
            _lungeTimer -= dt;
            if (_castT >= 0f && (_castT += dt) >= UnitPose.CastDuration) _castT = -1f;
            if (_hitT >= 0f && (_hitT += dt) >= (_hitHeavy ? UnitPose.HeavyHitDuration : UnitPose.HitDuration)) { _hitT = -1f; _hitHeavy = false; }
            if (_flash > 0f) _flash = Mathf.Max(0f, _flash - dt * 6f);
            _hpShowTimer -= dt;
            _attackTimer -= dt;
            float dissolve = 0f;
            if (_spawnT >= 0f)
            {
                _spawnT += dt;
                dissolve = WorldGfx.Feel.AnimAmplitude > 0f ? 1f - Mathf.Clamp01(_spawnT / SpawnTime) : 0f;
                if (_spawnT >= SpawnTime) _spawnT = -1f;
            }

            if (_tell != null && Telegraphing) Body.sprite = _tell;
            else if (_attackTimer > 0f)
                // strike first (the sim reports the hit), then the follow-through for the rest of the hold
                Body.sprite = _follow != null && _attackTimer < AttackHold * 0.55f ? _follow : _attack;
            else if (Windup && _windup != null) Body.sprite = _windup;
            else if (speed > 0.2f && _cycle != null)
            {
                // stride rate follows the run speed; 4-pose cycles step twice as often as the old a/b pair
                _walk += dt * (_cycle.Length >= 4 ? 2f : 1f) * (_isHero ? 2.5f + speed * 1.6f : 4f);
                Body.sprite = _cycle[(int)_walk % _cycle.Length];
            }
            else if (_castTimer > 0f) Body.sprite = _cast;
            else Body.sprite = _idleB != null && Mathf.Repeat(Time.time * 0.8f + Uid * 0.37f, 1f) > 0.5f ? _idleB : _idle;

            float bob = speed > 0.2f ? Mathf.Abs(Mathf.Sin(_phase)) * 0.08f : Mathf.Abs(Mathf.Sin(_phase)) * 0.035f;
            float squash = speed > 0.2f ? Mathf.Sin(_phase * 2f) * 0.04f : Mathf.Sin(_phase * 2f) * 0.02f;
            Vector3 lunge = _lungeTimer > 0f ? _lungeDir * Mathf.Sin(_lungeTimer / 0.18f * Mathf.PI) * 0.22f : Vector3.zero;
            float amp = WorldGfx.Feel.AnimAmplitude;
            BodyPose pose = UnitPose.Cast(_castT, amp).Combine(UnitPose.Hit(_hitT, _hitDir.x, _hitDir.y, _hitHeavy, amp));
            bt.localPosition = new Vector3(lunge.x + pose.X, bob + lunge.y * 0.5f + pose.Y, 0);
            float flip = facingX < -0.05f ? -1f : (facingX > 0.05f ? 1f : Mathf.Sign(bt.localScale.x == 0 ? 1 : bt.localScale.x));
            bt.localScale = new Vector3(flip * _baseScale * (1f - squash) * pose.ScaleX, _baseScale * (1f + squash) * pose.ScaleY, 1f);
            Body.color = stunned ? new Color(0.75f, 0.85f, 1f) : Color.white;
            SyncCastShadow(flip);
            SetBodyProps(_flash * 0.85f, dissolve);

            float height = Body.sprite != null ? Body.sprite.bounds.size.y * _baseScale : 1.4f;
            bool showHp = alwaysShowHp || _hpShowTimer > 0f || hpFraction < 0.999f && _isHero;
            _hpBg.enabled = _hpFill.enabled = showHp;
            if (showHp)
            {
                float w = _isHero ? 0.95f : Mathf.Clamp(height * 0.75f, 0.6f, 2.2f);
                float y = height * 0.88f + 0.08f;
                // bar sprites are 1.28 x 0.40 units at PPU 100; scale them (simple draw mode) to w x 0.17
                _hpBg.transform.localPosition = new Vector3(0, y, 0);
                _hpBg.transform.localScale = new Vector3(w / 1.28f, 0.17f / 0.4f, 1f);
                float fw = Mathf.Max(0.04f, w * hpFraction);
                _hpFill.transform.localPosition = new Vector3(-w / 2 + fw / 2, y, 0);
                _hpFill.transform.localScale = new Vector3(fw / 1.28f, 0.13f / 0.4f, 1f);
                _hpFill.color = _isHero ? Color.Lerp(new Color(1f, 0.35f, 0.35f), new Color(0.45f, 1f, 0.55f), hpFraction)
                                        : new Color(1f, 0.32f, 0.38f);
            }
            _shieldFx.enabled = shieldFraction > 0.01f;
            if (_shieldFx.enabled)
            {
                _shieldFx.color = new Color(0.6f, 0.9f, 1f, 0.35f + 0.25f * Mathf.Sin(Time.time * 6f));
                _shieldFx.transform.localPosition = new Vector3(0, height * 0.45f, 0);
                _shieldFx.transform.localScale = Vector3.one * (height * 0.95f + 0.2f);
            }
            if (status1 != _s1 || status2 != _s2)
            {
                _s1 = status1;
                _s2 = status2;
                _status1.sprite = StatusSprite(status1);
                _status2.sprite = StatusSprite(status2);
            }
            _status1.enabled = status1 != Element.None;
            _status2.enabled = status2 != Element.None;
            float sy = height * 0.88f + (showHp ? 0.32f : 0.15f);
            _status1.transform.localPosition = new Vector3(status2 != Element.None ? -0.16f : 0f, sy, 0);
            _status2.transform.localPosition = new Vector3(0.16f, sy, 0);
        }

        /// <summary>Signature status icon of an element aura (key from elements.json).</summary>
        private static Sprite StatusSprite(Element e)
        {
            if (e == Element.None) return null;
            ElementDef d = App.Content.ElementDefs[(int)e];
            return d != null ? Art.Sprite("Icons/status_" + d.StatusKey) : null;
        }
    }

    /// <summary>Short-lived sprite effects (impacts, rings, slashes, sparks) from a fixed pool.</summary>
    public sealed class FxSystem
    {
        private sealed class Fx
        {
            public SpriteRenderer R;
            public float T, Duration, StartScale, EndScale, Spin, YMul = 1f;
            public Color Color;
            public Vector3 Velocity;
            public bool Fade = true;
            public Sprite[] Frames;      // flipbook frames (null for single-sprite fx)
            public float Fps;
        }

        private readonly Transform _root;
        private readonly List<Fx> _active = new List<Fx>();
        private readonly Stack<Fx> _pool = new Stack<Fx>();
        public int MaxActive = 320;
        public int ActiveCount => _active.Count;

        public FxSystem(Transform root)
        {
            _root = root;
        }

        public void Spawn(string sprite, Vector3 pos, float startScale, float endScale, float duration, Color color, float rotation = 0f,
            float spin = 0f, Vector3 velocity = default, int orderBoost = 30, bool fade = true, float yMul = 1f, bool additive = false)
        {
            if (_active.Count >= MaxActive) return;
            Fx f = _pool.Count > 0 ? _pool.Pop() : new Fx { R = WorldGfx.NewSprite(_root, "Fx", null, 0) };
            f.R.gameObject.SetActive(true);
            f.R.sharedMaterial = additive ? WorldGfx.AdditiveMaterial : WorldGfx.SpriteMaterial;
            f.R.sprite = Art.Sprite(sprite);
            f.R.transform.position = pos;
            f.R.transform.rotation = Quaternion.Euler(0, 0, rotation);
            f.YMul = yMul;
            f.R.transform.localScale = new Vector3(startScale, startScale * yMul, 1f);
            f.R.color = color;
            f.R.sortingOrder = WorldGfx.OrderFor(pos.y) + orderBoost;
            f.T = 0f;
            f.Duration = Mathf.Max(0.01f, duration);
            f.StartScale = startScale;
            f.EndScale = endScale;
            f.Spin = spin;
            f.Color = color;
            f.Velocity = velocity;
            f.Fade = fade;
            _active.Add(f);
        }

        /// <summary>
        /// Plays a Blender-rendered flipbook (Art.Flipbook: Vfx/fb_&lt;name&gt; sheet + meta) at a world position.
        /// Missing sheets are ignored, so callers can keep their sprite fallback.
        /// </summary>
        public bool SpawnFlipbook(string name, Vector3 pos, float scale, Color color, float speed = 1f, int orderBoost = 30, bool flip = false)
        {
            if (_active.Count >= MaxActive) return false;
            Art.FlipbookData fb = Art.Flipbook(name);
            if (fb == null) return false;
            Fx f = _pool.Count > 0 ? _pool.Pop() : new Fx { R = WorldGfx.NewSprite(_root, "Fx", null, 0) };
            f.R.gameObject.SetActive(true);
            f.R.sharedMaterial = fb.Additive ? WorldGfx.AdditiveMaterial : WorldGfx.SpriteMaterial;
            f.Frames = fb.Frames;
            f.Fps = fb.Fps * speed;
            f.R.sprite = fb.Frames[0];
            f.R.flipX = flip;
            f.R.transform.position = pos;
            f.R.transform.rotation = Quaternion.identity;
            f.YMul = 1f;
            f.R.transform.localScale = Vector3.one * scale;
            f.R.color = color;
            f.R.sortingOrder = WorldGfx.OrderFor(pos.y) + orderBoost;
            f.T = 0f;
            f.Duration = fb.Frames.Length / Mathf.Max(1f, f.Fps);
            f.StartScale = f.EndScale = scale;
            f.Spin = 0f;
            f.Color = color;
            f.Velocity = Vector3.zero;
            f.Fade = false;
            _active.Add(f);
            return true;
        }

        public void Update(float dt)
        {
            for (int i = _active.Count - 1; i >= 0; i--)
            {
                Fx f = _active[i];
                f.T += dt;
                if (f.Frames != null)
                {
                    int fi = Mathf.Min(f.Frames.Length - 1, (int)(f.T * f.Fps));
                    if (f.T >= f.Duration)
                    {
                        f.Frames = null;
                        f.R.sharedMaterial = WorldGfx.SpriteMaterial;
                        f.R.flipX = false;
                        f.R.gameObject.SetActive(false);
                        _pool.Push(f);
                        _active.RemoveAt(i);
                        continue;
                    }
                    f.R.sprite = f.Frames[fi];
                    continue;
                }
                float k = f.T / f.Duration;
                if (k >= 1f)
                {
                    f.R.gameObject.SetActive(false);
                    _pool.Push(f);
                    _active.RemoveAt(i);
                    continue;
                }
                float ease = 1f - (1f - k) * (1f - k);
                float sc = Mathf.Lerp(f.StartScale, f.EndScale, ease);
                f.R.transform.localScale = new Vector3(sc, sc * f.YMul, 1f);
                if (f.Spin != 0f) f.R.transform.Rotate(0, 0, f.Spin * dt);
                if (f.Velocity != Vector3.zero) f.R.transform.position += f.Velocity * dt;
                Color c = f.Color;
                if (f.Fade) c.a *= 1f - k * k;
                f.R.color = c;
            }
        }

        public void Clear()
        {
            foreach (Fx f in _active)
            {
                f.Frames = null;
                f.R.sharedMaterial = WorldGfx.SpriteMaterial;
                f.R.flipX = false;
                f.R.gameObject.SetActive(false);
                _pool.Push(f);
            }
            _active.Clear();
        }

        public int Count => _active.Count;
    }

    /// <summary>Floating combat text, drawn in OnGUI over world positions.</summary>
    public sealed class FloatingTextSystem
    {
        public struct Entry
        {
            public Vector3 World;
            public string Text;
            public Color Color;
            public float Size;
            public float T;
            public float Life;
            public Texture Icon;
            public int Slot;
        }

        public readonly List<Entry> Entries = new List<Entry>();
        public int Max = 48;

        public void Add(Vector3 world, string text, Color color, float size, float life = 0.9f, Texture icon = null)
        {
            if (Entries.Count >= Max) Entries.RemoveAt(0);
            Entries.Add(new Entry { World = world, Text = text, Color = color, Size = size, Life = life, Icon = icon });
        }

        /// <summary>Adds a number, or refreshes the live entry with the same slot (merged hits).</summary>
        public void Upsert(int slot, Vector3 world, string text, Color color, float size, float life)
        {
            for (int i = Entries.Count - 1; i >= 0; i--)
            {
                if (Entries[i].Slot != slot) continue;
                Entry e = Entries[i];
                e.Text = text;
                e.Size = Mathf.Min(size * 1.35f, e.Size + 1.5f); // grows a little as hits stack
                e.T = Mathf.Min(e.T, 0.1f);
                Entries[i] = e;
                return;
            }
            Add(world, text, color, size, life);
            Entry n = Entries[Entries.Count - 1];
            n.Slot = slot;
            Entries[Entries.Count - 1] = n;
        }

        public void Update(float dt)
        {
            for (int i = Entries.Count - 1; i >= 0; i--)
            {
                Entry e = Entries[i];
                e.T += dt;
                e.World += new Vector3(0, dt * 0.9f, 0);
                if (e.T >= e.Life) Entries.RemoveAt(i);
                else Entries[i] = e;
            }
        }

        public void Draw(Camera cam)
        {
            foreach (Entry e in Entries)
            {
                Vector2 p = Ui.FromScreen(cam.WorldToScreenPoint(e.World));
                float k = e.T / e.Life;
                float pop = k < 0.15f ? 1f + (0.15f - k) * 3f : 1f;
                Color c = e.Color;
                c.a = k > 0.7f ? 1f - (k - 0.7f) / 0.3f : 1f;
                float size = e.Size * pop;
                float w = 360;
                if (e.Icon != null)
                {
                    Ui.Icon(p.x - size * 1.6f - 8, p.y - size * 0.75f, size * 1.4f, size * 1.4f, e.Icon, new Color(1, 1, 1, c.a));
                    Ui.Label(p.x - 6, p.y - size * 0.7f, w, size * 1.6f, e.Text, size, c, TextAnchor.UpperLeft, true);
                }
                else Ui.Label(p.x - w / 2, p.y - size * 0.7f, w, size * 1.6f, e.Text, size, c, TextAnchor.UpperCenter, true, true, true);
            }
        }
    }
}
