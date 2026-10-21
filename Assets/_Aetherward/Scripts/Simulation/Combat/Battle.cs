using System;
using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    public sealed class HeroLoadout
    {
        public HeroDef Def;
        public int RosterIndex;
        public int NodeIndex;
        public int Level = 1;
        public string EvolutionId;
        public float HpFraction = 1f;
        public bool Downed;
        public string TraitId;
        public Element Awakened;
    }

    public sealed class BattleSetup
    {
        public ContentDatabase Content;
        public WaveDef Wave;
        public ulong Seed;
        public readonly List<HeroLoadout> Heroes = new List<HeroLoadout>();
        public BattleModifiers Modifiers = new BattleModifiers();
        public float CrystalHp;
        public float CrystalMaxHp;
        public int Ascension;
        public readonly List<string> ExtraWaveModifiers = new List<string>();
        public int MaxActiveEnemies = 160;
        /// <summary>Enemy id replacements for this battle (boss pools, biome variants).</summary>
        public readonly Dictionary<string, string> Substitutions = new Dictionary<string, string>();
        /// <summary>Ascension: elites gain one extra compatible affix.</summary>
        public bool EliteExtraAffix;
        /// <summary>Battlefield (null = content default biome).</summary>
        public BiomeDef Biome;
        /// <summary>Ascension: bosses enrage below 25% HP by this amount (0 = off).</summary>
        public float BossEnrage;
        /// <summary>Ascension "double_elite": every Nth regular spawn is elite (0 = off).</summary>
        public int EliteEvery;
        public string CrystalPath;                // Crystal Evolution path id (null = none)
        public TeamTactic Tactic;                 // soft targeting weights chosen before the wave
        public PartyStance Stance = PartyStance.Balanced;   // how far from the Crystal the party fights
        /// <summary>Dynamic party (posts re-planned from threat, role and stance). False = legacy fixed node anchors.</summary>
        public bool DynamicParty = true;
        public bool UtilityTargeting = true;      // feature flag: utility scoring for basic-attack targets
        public float HazardShift;     // Ascension "hazard_shift": biome hazards fire this much more often
    }

    public enum BattleOutcome
    {
        Running,
        Cleared,
        CrystalDestroyed
    }

    /// <summary>
    /// One wave of real-time auto-combat. Pure simulation: fixed tick, seeded RNG, no engine types.
    /// The presentation layer reads public state and drains <see cref="Journal"/> each frame.
    /// </summary>
    public sealed partial class Battle
    {
        public const float TickSeconds = 1f / 30f;
        public const int MaxProcGeneration = 2;
        public const int WorldReactionBudgetPerTick = 48;
        public const int TargetReactionBudgetPerSecond = 6;

        public readonly ContentDatabase Content;
        public readonly BattleSetup Setup;
        public readonly BiomeDef Biome;
        public readonly ArenaDef Arena;
        public readonly WaveDef Wave;
        public readonly BattleModifiers Mods;
        public readonly Pcg32 Rng;
        public readonly List<HeroUnit> Heroes = new List<HeroUnit>();
        public readonly List<EnemyUnit> Enemies = new List<EnemyUnit>();
        public readonly List<Projectile> Projectiles = new List<Projectile>();
        public readonly List<Zone> Zones = new List<Zone>();
        public readonly List<DelayedStrike> Strikes = new List<DelayedStrike>();
        public readonly List<EnemyBolt> Bolts = new List<EnemyBolt>();
        public readonly Crystal Crystal = new Crystal();
        public readonly CombatJournal Journal = new CombatJournal();
        public readonly BattleStats Stats = new BattleStats();
        public readonly SpatialGrid Grid;
        public readonly List<TriggerInstance> Triggers = new List<TriggerInstance>();

        public float Time { get; private set; }
        public int TickCount { get; private set; }
        public BattleOutcome Outcome { get; private set; } = BattleOutcome.Running;
        public bool AllSpawned => _spawnCursor >= _schedule.Count;
        public int RemainingSpawns => _schedule.Count - _spawnCursor;
        public int TotalSpawns => _schedule.Count;
        public float WaveLevelScale { get; }
        public string DefeatSource { get; private set; }

        private readonly List<ScheduledSpawn> _schedule = new List<ScheduledSpawn>();
        private int _spawnCursor;
        private int _nextUid = 1;
        private int _reactionsThisTick;
        private int _reactionsThisSecond;
        private float _secondWindow;
        private bool _timeoutHandled;
        private readonly float _enemyHpScale;
        private readonly float _enemyDamageScale;
        private readonly List<EnemyUnit> _query = new List<EnemyUnit>(64);
        private readonly List<EnemyUnit> _query2 = new List<EnemyUnit>(64);
        private readonly Stack<EnemyUnit> _enemyPool = new Stack<EnemyUnit>();

        private struct ScheduledSpawn
        {
            public float Time;
            public EnemyDef Def;
            public int Lane;
            public bool Elite;
            public string Affix;
        }

        public Battle(BattleSetup setup)
        {
            Setup = setup ?? throw new ArgumentNullException(nameof(setup));
            Content = setup.Content;
            Biome = setup.Biome ?? Content.DefaultBiome ?? new BiomeDef { Arena = Content.Arena };
            Arena = Biome.Arena ?? Content.Arena;
            Wave = setup.Wave;
            Mods = setup.Modifiers ?? new BattleModifiers();
            Rng = Pcg32.Derive(setup.Seed, "battle:" + Wave.Number);
            Grid = new SpatialGrid(Arena.HalfWidth, Arena.HalfHeight, 1.5f);

            EconomyDef eco = Content.Economy;
            int w = Wave.EffectiveLevel - 1;
            float asc = 1f + Content.Difficulty.HpPerLevel * setup.Ascension * Content.Difficulty.LevelBonusShare(Wave.EffectiveLevel);
            _enemyHpScale = eco.EnemyHpMult * (1f + eco.EnemyHpGrowth * w + eco.EnemyHpGrowthQuad * w * w) * asc * (1f + Mods.EnemyHpPct) * (1f + Wave.ScalePct);
            _enemyDamageScale = (1f + eco.EnemyDamageGrowth * w) * asc * (1f + Mods.EnemyDamagePct) * (1f + Wave.ScalePct * 0.5f);
            WaveLevelScale = 1f + eco.ReactionLevelGrowth * w;

            SetupCrystal();
            SetupHeroes();
            BuildSchedule();
            SetupBiome();
            foreach (SourcedOp t in Mods.Triggers) Triggers.Add(new TriggerInstance { Source = t });
            FireTrigger("wave_start", null, null, Crystal.Pos, null);
        }

        private void SetupCrystal()
        {
            Crystal.Radius = Arena.CrystalRadius;
            Crystal.MaxHp = Setup.CrystalMaxHp;
            Crystal.Hp = SimMath.Clamp(Setup.CrystalHp, 0f, Crystal.MaxHp);
            Crystal.DamageReduction = SimMath.Clamp(Mods.CrystalReduction, 0f, 0.6f);
            Crystal.Regen = Mods.CrystalRegen;
            Crystal.Thorns = Mods.CrystalThorns;
            SetupCrystalPath();
        }

        private void SetupHeroes()
        {
            foreach (HeroLoadout l in Setup.Heroes)
            {
                HeroUnit h = HeroFactory.Create(this, l);
                h.Uid = _nextUid++;
                Heroes.Add(h);
            }
            // Team auras (e.g. Zephyr's tailwind) are applied as permanent buffs at battle start.
            foreach (HeroUnit h in Heroes) ApplyBattleStartPassive(h);
            foreach (HeroUnit h in Heroes) ApplyBattleStartTrait(h);
            ApplyStanceBonus();
        }

        private int _eliteCounter;

        private void BuildSchedule()
        {
            Pcg32 rng = Pcg32.Derive(Setup.Seed, "spawns:" + Wave.Number);
            List<int> lanes = Wave.Lanes.Count > 0 ? Wave.Lanes : new List<int> { 0, 1, 2, 3 };
            int rotate = rng.Range(0, lanes.Count);
            bool swarmMod = HasWaveModifier("swarm");
            var groups = new List<SpawnGroup>(Wave.Groups);
            for (int i = 0; i < Biome.Extra.Count; i++)
                if (Wave.Number >= Biome.ExtraWaves[i][0] && Wave.Number <= Biome.ExtraWaves[i][1]) groups.Add(Biome.Extra[i]);
            foreach (SpawnGroup g in groups)
            {
                string enemyId = Setup.Substitutions.TryGetValue(g.Enemy, out string sub) ? sub : g.Enemy;
                if (Biome.Substitutions.TryGetValue(enemyId, out string bsub) && Content.Enemies.ContainsKey(bsub)) enemyId = bsub;
                if (!Content.Enemies.TryGetValue(enemyId, out EnemyDef def))
                    throw new InvalidOperationException("Wave " + Wave.Number + " references unknown enemy " + enemyId);
                int count = g.Count;
                if (swarmMod && !def.Boss) count += count / 4;
                for (int i = 0; i < count; i++)
                {
                    int lane = Biome.MapLane(g.Lane >= 0 ? g.Lane : lanes[(rotate + i) % lanes.Count], Wave.Number);
                    float jitter = g.Interval * rng.Range(-0.15f, 0.15f);
                    _schedule.Add(new ScheduledSpawn
                    {
                        Time = g.Start + i * g.Interval + jitter,
                        Def = def,
                        Lane = lane,
                        Elite = g.Elite || (Setup.EliteEvery > 0 && !def.Boss && ++_eliteCounter % Setup.EliteEvery == 0),
                        Affix = g.Affix
                    });
                }
            }
            _schedule.Sort((a, b) =>
            {
                int c = a.Time.CompareTo(b.Time);
                return c != 0 ? c : string.CompareOrdinal(a.Def.Id, b.Def.Id);
            });
        }

        public bool HasWaveModifier(string id)
        {
            return Wave.Modifiers.Contains(id) || Setup.ExtraWaveModifiers.Contains(id);
        }

        // ------------------------------------------------------------------ tick

        /// <summary>Advances the battle by exactly one fixed tick.</summary>
        public void Tick()
        {
            if (Outcome != BattleOutcome.Running) return;
            float dt = TickSeconds;
            Time += dt;
            TickCount++;
            _reactionsThisTick = 0;
            _secondWindow += dt;
            if (_secondWindow >= 1f)
            {
                if (_reactionsThisSecond > Stats.PeakReactionsPerSecond) Stats.PeakReactionsPerSecond = _reactionsThisSecond;
                _reactionsThisSecond = 0;
                _secondWindow -= 1f;
            }

            SpawnDue();
            Grid.Rebuild(Enemies);

            UpdateCrystal(dt);
            UpdateCrystalPath(dt);
            UpdatePartyPosts(dt);
            for (int i = 0; i < Heroes.Count; i++)
            {
                Vec2 before = Heroes[i].Pos;
                UpdateHero(Heroes[i], dt);
                Stats.HeroTravel += Vec2.Distance(before, Heroes[i].Pos);
            }
            for (int i = 0; i < Enemies.Count; i++) UpdateEnemy(Enemies[i], dt);
            SeparateEnemies();
            UpdateProjectiles(dt);
            UpdateBolts(dt);
            UpdateZones(dt);
            UpdateStrikes(dt);
            UpdateTriggers(dt);
            UpdateBiome(dt);
            RemoveDead();

            if (Enemies.Count > Stats.PeakEnemies) Stats.PeakEnemies = Enemies.Count;
            Stats.Duration = Time;
            CheckOutcome();
        }

        /// <summary>Runs ticks until the wave resolves or the hard cap is reached (headless use).</summary>
        public BattleOutcome RunToEnd(float hardCapSeconds = 600f)
        {
            while (Outcome == BattleOutcome.Running && Time < hardCapSeconds)
            {
                Tick();
                Journal.Clear();
            }
            if (Outcome == BattleOutcome.Running) ForceResolve();
            return Outcome;
        }

        private void SpawnDue()
        {
            while (_spawnCursor < _schedule.Count && _schedule[_spawnCursor].Time <= Time)
            {
                // Pace rather than delete: hold spawns while the active cap is reached.
                if (Enemies.Count >= Setup.MaxActiveEnemies) break;
                ScheduledSpawn s = _schedule[_spawnCursor++];
                SpawnEnemy(s.Def, s.Lane, s.Elite, s.Affix, null);
            }
        }

        /// <summary>Adds a spawn to the pending schedule keeping time order (boss lane assaults).</summary>
        private void InsertSpawn(ScheduledSpawn spawn)
        {
            int i = _spawnCursor;
            while (i < _schedule.Count && _schedule[i].Time <= spawn.Time) i++;
            _schedule.Insert(i, spawn);
        }

        public EnemyUnit SpawnEnemy(EnemyDef def, int laneIndex, bool elite, string affix, Vec2? at)
        {
            List<LaneDef> lanes = Arena.Lanes;
            laneIndex = ((laneIndex % lanes.Count) + lanes.Count) % lanes.Count;
            LaneDef lane = lanes[laneIndex];
            EnemyUnit e = _enemyPool.Count > 0 ? _enemyPool.Pop() : new EnemyUnit();
            ResetEnemy(e);
            e.Uid = _nextUid++;
            e.Def = def;
            e.Lane = laneIndex;
            e.Elite = elite || def.Elite;
            e.Affix = affix;
            Vec2 start = lane.Points[0];
            Vec2 dir = (lane.Points[1] - lane.Points[0]).Normalized;
            Vec2 perp = new Vec2(-dir.Y, dir.X);
            e.Pos = at ?? start + perp * Rng.Range(-0.7f, 0.7f);
            e.Waypoint = at.HasValue ? NearestWaypoint(lane, e.Pos) : 1;
            e.LastProgressPos = e.Pos;

            float eliteHp = e.Elite && !def.Elite && !def.Boss ? 3.5f : 1f;
            float eliteDmg = e.Elite && !def.Elite && !def.Boss ? 1.5f : 1f;
            e.MaxHp = def.Hp * _enemyHpScale * eliteHp;
            e.Attack = def.Attack * _enemyDamageScale * eliteDmg;
            e.CrystalDamage = def.CrystalDamage * _enemyDamageScale * eliteDmg;
            e.Defense = def.Defense * (1f + 0.03f * (Wave.EffectiveLevel - 1));
            e.Speed = def.Speed * (1f + Mods.EnemySpeedPct);
            e.Radius = def.Radius * (e.Elite && !def.Elite && !def.Boss ? 1.3f : 1f);
            e.Tenacity = def.Tenacity + (e.Elite ? 0.25f : 0f);
            for (int i = 0; i < ElementUtil.Count; i++) e.Resist[i] = def.Resist[i];
            e.ShieldFront = def.Params.Flag("frontShield");
            if (HasWaveModifier("haste")) e.Speed *= 1.2f;
            if (HasWaveModifier("armored")) e.Defense += 25f;
            if (HasWaveModifier("ascension_frenzy")) e.Speed *= 1.1f;
            if (Setup.EliteExtraAffix && e.Elite && !def.Boss && string.IsNullOrEmpty(e.Affix) && Content.Affixes.Count > 0)
            {
                // Ascension: elites carry one affix (sorted ids + battle RNG: deterministic).
                var ids = new List<string>();
                foreach (AffixDef a in Content.Affixes.Values) if (AffixCompatible(def, a)) ids.Add(a.Id);
                ids.Sort(string.CompareOrdinal);
                if (ids.Count > 0) e.Affix = ids[Rng.Range(0, ids.Count)];
            }
            ApplyAffix(e);
            e.Hp = e.MaxHp;
            e.AttackTimer = def.AttackInterval * Rng.Range(0.3f, 1f);
            e.SpecialTimer = def.Params.Get("specialInterval", 6f) * Rng.Range(0.5f, 1f);
            Enemies.Add(e);
            InitEnemyMechanics(e);
            Emit(SimEventType.EnemySpawn, e.Pos, Element.None, 0f, 0, e.Uid, def.Id);
            return e;
        }

        private void ApplyAffix(EnemyUnit e)
        {
            if (string.IsNullOrEmpty(e.Affix) || !Content.Affixes.TryGetValue(e.Affix, out AffixDef a)) return;
            e.MaxHp *= 1f + a.Params.Get("hpPct");
            e.Speed *= 1f + a.Params.Get("speedPct");
            e.Defense += a.Params.Get("defense");
            e.Tenacity = SimMath.Clamp(e.Tenacity + a.Params.Get("tenacity"), 0f, 0.9f);
            string resistEl = a.Params.GetString("resistElement");
            if (!string.IsNullOrEmpty(resistEl))
            {
                int k = (int)ContentDatabase.ParseElement(resistEl);
                e.Resist[k] = SimMath.Min(MaxResist, e.Resist[k] + a.Params.Get("resist", 0.5f)); // never immune
            }
        }

        /// <summary>Resistance cap shared with the content validator: nothing is ever fully immune.</summary>
        public const float MaxResist = 0.75f;

        /// <summary>
        /// Affix compatibility: no resist affix on an element the enemy already resists (it would stack
        /// toward immunity), no speed affix on sprinters/flyers/fast runners, no affixes on summons.
        /// </summary>
        public static bool AffixCompatible(EnemyDef def, AffixDef a)
        {
            if (def.Boss || def.Tags.Contains("summon")) return false;
            string resistEl = a.Params.GetString("resistElement");
            if (!string.IsNullOrEmpty(resistEl) && def.Resist[(int)ContentDatabase.ParseElement(resistEl)] >= 0.3f) return false;
            if (a.Params.Get("speedPct") > 0f && (def.Speed >= 1.5f || def.Params.Has("sprintEvery") || def.Params.Flag("flying"))) return false;
            return true;
        }

        private static void ResetEnemy(EnemyUnit e)
        {
            e.Alive = true;
            Array.Clear(e.BossTimers, 0, e.BossTimers.Length);
            e.BossFlags = 0;
            e.ChaosElement = Element.None;
            e.ChaosTimer = 0f;
            e.Shield = 0f;
            e.HitFlash = 0f;
            e.Engaged = null;
            e.Taunter = null;
            e.TauntTimer = 0f;
            Array.Clear(e.Aura, 0, e.Aura.Length);
            Array.Clear(e.ReactionCooldown, 0, e.ReactionCooldown.Length);
            e.ReactionWindowStart = 0f;
            e.ReactionsInWindow = 0;
            e.BurnTimer = e.BurnDps = e.BurnTick = 0f;
            e.BurnSource = null;
            e.SlowTimer = e.SlowAmount = 0f;
            e.StunTimer = 0f;
            e.Frozen = false;
            e.FreezeResist = e.FreezeResistTimer = 0f;
            e.ArmorCrackTimer = 0f;
            e.ArmorCrackStacks = 0;
            e.SuperconductTimer = e.SandstormTimer = 0f;
            e.VulnerableTimer = e.VulnerableAmount = 0f;
            e.Knockback = Vec2.Zero;
            e.KnockbackTimer = e.PullTimer = e.PullStrength = 0f;
            e.Phase = 0;
            e.PhaseTimer = 0f;
            e.Summoned = 0;
            e.BuffAuraTimer = e.SpeedBuff = e.ArmorBuff = 0f;
            e.StuckTimer = 0f;
            e.Leaked = false;
            e.TelegraphTimer = 0f;
            e.TelegraphKind = 0;
            e.Invulnerable = 0f;
            e.ChillDamageReduction = 0f;
            Array.Clear(e.AdaptDamage, 0, e.AdaptDamage.Length);
            e.AdaptedElement = 0;
            e.AdaptTimer = 0f;
            ResetExpansionStatuses(e);
        }

        private static int NearestWaypoint(LaneDef lane, Vec2 p)
        {
            int best = 1;
            float bestD = float.MaxValue;
            for (int i = 1; i < lane.Points.Count; i++)
            {
                float d = Vec2.SqrDistance(lane.Points[i], p);
                if (d < bestD) { bestD = d; best = i; }
            }
            return best;
        }

        private void UpdateCrystal(float dt)
        {
            if (Crystal.HitFlash > 0f) Crystal.HitFlash -= dt;
            if (Crystal.TempReductionTimer > 0f) Crystal.TempReductionTimer -= dt;
            if (Crystal.Regen > 0f && Crystal.Hp > 0f)
                Crystal.Hp = SimMath.Min(Crystal.MaxHp, Crystal.Hp + Crystal.Regen * dt);
        }

        private void SeparateEnemies()
        {
            // Light push-apart so crowds remain readable; capped neighbour checks per enemy.
            for (int i = 0; i < Enemies.Count; i++)
            {
                EnemyUnit a = Enemies[i];
                if (!a.Alive || a.IsBoss) continue;
                Grid.Query(a.Pos, a.Radius * 1.6f, _query2);
                int checks = 0;
                for (int j = 0; j < _query2.Count && checks < 6; j++)
                {
                    EnemyUnit b = _query2[j];
                    if (b == a) continue;
                    checks++;
                    Vec2 d = a.Pos - b.Pos;
                    float dist = d.Length;
                    float min = (a.Radius + b.Radius) * 0.85f;
                    if (dist < min)
                    {
                        Vec2 push = dist > 1e-4f ? d / dist : new Vec2((a.Uid % 2 == 0) ? 1f : -1f, 0f);
                        float amount = (min - dist) * (b.IsBoss ? 1f : 0.5f);
                        a.Pos += push * amount;
                    }
                }
            }
        }

        private void RemoveDead()
        {
            for (int i = Enemies.Count - 1; i >= 0; i--)
            {
                EnemyUnit e = Enemies[i];
                if (e.Alive) continue;
                Enemies.RemoveAt(i);
                foreach (HeroUnit h in Heroes) if (h.Target == e) h.Target = null;
                _enemyPool.Push(e);
            }
        }

        private void CheckOutcome()
        {
            if (!Crystal.Alive)
            {
                Outcome = BattleOutcome.CrystalDestroyed;
                return;
            }
            if (AllSpawned && Enemies.Count == 0)
            {
                Outcome = BattleOutcome.Cleared;
                return;
            }
            // Fail-safe: past the wave time limit every remaining threat breaches the crystal.
            if (!_timeoutHandled && Time >= Wave.TimeLimit)
            {
                _timeoutHandled = true;
                Breach();
            }
            if (Time >= Wave.TimeLimit + 45f) ForceResolve();
        }

        private void Breach()
        {
            while (_spawnCursor < _schedule.Count) _spawnCursor++; // remaining spawns are cancelled
            for (int i = 0; i < Enemies.Count; i++)
            {
                EnemyUnit e = Enemies[i];
                if (!e.Alive) continue;
                float mult = e.IsBoss ? 0.35f * Crystal.MaxHp / SimMath.Max(1f, e.CrystalDamage) : 2f;
                float dmg = e.CrystalDamage * mult * SimMath.Max(0.25f, e.HpFraction);
                Stats.TimeoutBreaches++;
                DamageCrystal(dmg, e);
                e.Alive = false;
                Emit(SimEventType.Leak, e.Pos, Element.None, dmg, e.Uid, 0, e.Def.Id);
            }
            if (!Crystal.Alive) Outcome = BattleOutcome.CrystalDestroyed;
        }

        private void ForceResolve()
        {
            if (Outcome != BattleOutcome.Running) return;
            if (!_timeoutHandled)
            {
                _timeoutHandled = true;
                Breach();
            }
            Enemies.Clear();
            Outcome = Crystal.Alive ? BattleOutcome.Cleared : BattleOutcome.CrystalDestroyed;
        }

        // ------------------------------------------------------------------ helpers

        public void Emit(SimEventType type, Vec2 pos, Element el, float value, int source, int target, string id,
            bool crit = false, float radius = 0f, int gen = 0)
        {
            Journal.Emit(new SimEvent
            {
                Type = type,
                Pos = pos,
                Element = el,
                Value = value,
                SourceUid = source,
                TargetUid = target,
                Id = id,
                Crit = crit,
                Radius = radius,
                Generation = gen,
                Tick = Time
            });
        }

        public HeroUnit HeroByUid(int uid)
        {
            for (int i = 0; i < Heroes.Count; i++) if (Heroes[i].Uid == uid) return Heroes[i];
            return null;
        }

        public int LivingHeroCount
        {
            get
            {
                int c = 0;
                for (int i = 0; i < Heroes.Count; i++) if (Heroes[i].Alive) c++;
                return c;
            }
        }

        public void QueryEnemies(Vec2 center, float radius, List<EnemyUnit> results) => Grid.Query(center, radius, results);

        /// <summary>Distance an enemy still has to travel to the crystal along its lane (leak threat).</summary>
        public float RemainingPath(EnemyUnit e)
        {
            LaneDef lane = Arena.Lanes[e.Lane];
            if (e.Waypoint >= lane.Points.Count) return Vec2.Distance(e.Pos, Crystal.Pos);
            float d = Vec2.Distance(e.Pos, lane.Points[e.Waypoint]);
            for (int i = e.Waypoint; i < lane.Points.Count - 1; i++) d += Vec2.Distance(lane.Points[i], lane.Points[i + 1]);
            return d;
        }

        /// <summary>Upcoming lanes for the preparation screen telegraph.</summary>
        public static List<int> LanesForWave(WaveDef wave) => LanesForWave(wave, null);

        /// <summary>Upcoming lanes (after the biome's lane schedule) for the preparation telegraph.</summary>
        public static List<int> LanesForWave(WaveDef wave, BiomeDef biome)
        {
            var result = new List<int>();
            void Add(int l)
            {
                int m = biome != null ? biome.MapLane(l, wave.Number) : l;
                if (!result.Contains(m)) result.Add(m);
            }
            foreach (SpawnGroup g in wave.Groups)
            {
                if (g.Lane >= 0) Add(g.Lane);
                else foreach (int l in wave.Lanes) Add(l);
            }
            if (biome != null)
                for (int i = 0; i < biome.Extra.Count; i++)
                {
                    if (wave.Number < biome.ExtraWaves[i][0] || wave.Number > biome.ExtraWaves[i][1]) continue;
                    if (biome.Extra[i].Lane >= 0) Add(biome.Extra[i].Lane);
                    else foreach (int l in wave.Lanes) Add(l);
                }
            result.Sort();
            return result;
        }
    }
}
