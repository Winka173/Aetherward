using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    public enum ProjectileKind
    {
        Single,     // homing single-target
        Explode,    // AoE on impact
        Pierce      // straight line, hits everything it passes once
    }

    public sealed class Projectile
    {
        public int Uid;
        public ProjectileKind Kind;
        public Vec2 Pos;
        public Vec2 Dir;
        public float Speed;
        public float Remaining;     // max travel distance left (pierce) or lifetime safety
        public EnemyUnit Target;
        public Vec2 TargetPos;
        public float Radius;        // explosion radius / pierce width
        public DamageRequest Damage;
        public string Visual;       // presentation key (skill kind or "basic")
        public bool Alive;
        public bool Burn;           // apply Burn on impact (Ember Weaver)
        public float BurnSpread;    // radius to spread Burn
        public HashSet<int> Pierced;
    }

    public enum ZoneKind
    {
        Magma,
        Mud,
        Thunderstorm,
        Blizzard,
        HealingRain,
        Vortex,
        BurningGround,
        StormTrail,
        TempestLink,
        Field           // data-driven (FieldDef): expansion reactions, skills, relics
    }

    public sealed class Zone
    {
        public int Uid;
        public ZoneKind Kind;
        public Vec2 Pos;
        public float Radius;
        public float Remaining;
        public float Duration;
        public float TickTimer;
        public float Power;
        public Element Element;
        public HeroUnit Owner;
        public int Generation;
        public string ReactionId;
        public float Heal;          // healing rain: heal per tick
        public bool Offensive;      // healing rain variant that damages
        public FieldDef Field;      // set for ZoneKind.Field
        public Vec2 End;            // line fields: second endpoint
        public bool Line;
        public float BaseRadius;
        public string Tag;          // attribution id (reaction/skill/relic)
    }

    public enum StrikeKind
    {
        Meteor,
        IceSpike,
        Aftershock,
        BossSlam,
        BossLaneMark,
        ReactionBurst,  // declarative delayed/shard strikes
        Hazard          // biome hazards: hit heroes and enemies alike
    }

    public sealed class DelayedStrike
    {
        public StrikeKind Kind;
        public Vec2 Pos;
        public float Delay;
        public float Total;
        public float Radius;
        public HeroUnit Source;
        public EnemyUnit EnemySource;
        public Element Element;
        public float Power;
        public float Multiplier;
        public int Generation;
        public string ReactionId;
        public float Stun;
        public float Gauge;
        public string SourceTag;
        public string Status;       // optional status applied to each enemy hit
        public ParamBag StatusParams;
    }

    /// <summary>Enemy ranged attack in flight (visible, short travel so presentation can show it).</summary>
    public sealed class EnemyBolt
    {
        public Vec2 Pos;
        public Vec2 Target;
        public HeroUnit HeroTarget;
        public bool AtCrystal;
        public float Speed;
        public float Damage;
        public EnemyUnit Owner;
        public bool Alive;
    }

    public sealed partial class Battle
    {
        private int _nextFxUid = 1;
        private readonly Stack<Projectile> _projectilePool = new Stack<Projectile>();

        public Projectile FireProjectile(HeroUnit src, ProjectileKind kind, EnemyUnit target, Vec2 targetPos, float speed,
            float radius, DamageRequest dmg, string visual)
        {
            Projectile p = _projectilePool.Count > 0 ? _projectilePool.Pop() : new Projectile();
            p.Uid = _nextFxUid++;
            p.Kind = kind;
            p.Pos = src.Pos;
            p.Target = target;
            p.TargetPos = target != null ? target.Pos : targetPos;
            p.Dir = (p.TargetPos - p.Pos).Normalized;
            if (p.Dir.SqrLength < 0.5f) p.Dir = src.Facing;
            p.Speed = speed;
            p.Radius = radius;
            p.Damage = dmg;
            p.Visual = visual;
            p.Alive = true;
            p.Burn = false;
            p.BurnSpread = 0f;
            p.Remaining = kind == ProjectileKind.Pierce ? radius > 0f ? 9f : 9f : 6f;
            if (kind == ProjectileKind.Pierce)
            {
                if (p.Pierced == null) p.Pierced = new HashSet<int>();
                p.Pierced.Clear();
            }
            Projectiles.Add(p);
            return p;
        }

        private void UpdateProjectiles(float dt)
        {
            for (int i = 0; i < Projectiles.Count; i++)
            {
                Projectile p = Projectiles[i];
                if (!p.Alive) continue;
                float step = p.Speed * dt;
                if (p.Kind == ProjectileKind.Pierce)
                {
                    p.Pos += p.Dir * step;
                    p.Remaining -= step;
                    List<EnemyUnit> hits = RentList();
                    QueryEnemies(p.Pos, p.Radius, hits);
                    for (int k = 0; k < hits.Count; k++)
                    {
                        EnemyUnit e = hits[k];
                        if (p.Pierced.Contains(e.Uid)) continue;
                        p.Pierced.Add(e.Uid);
                        DealDamage(e, p.Damage);
                    }
                    ReturnList(hits);
                    if (p.Remaining <= 0f || OutOfArena(p.Pos)) p.Alive = false;
                    continue;
                }

                if (p.Target != null && p.Target.Alive) p.TargetPos = p.Target.Pos;
                Vec2 to = p.TargetPos - p.Pos;
                float dist = to.Length;
                p.Remaining -= dt;
                if (dist <= step + 0.15f || p.Remaining <= 0f)
                {
                    p.Pos = p.TargetPos;
                    Impact(p);
                    p.Alive = false;
                }
                else
                {
                    p.Dir = to / dist;
                    p.Pos += p.Dir * step;
                }
            }
            for (int i = Projectiles.Count - 1; i >= 0; i--)
            {
                if (Projectiles[i].Alive) continue;
                _projectilePool.Push(Projectiles[i]);
                Projectiles.RemoveAt(i);
            }
        }

        private void Impact(Projectile p)
        {
            if (p.Kind == ProjectileKind.Explode)
            {
                List<EnemyUnit> hits = RentList();
                QueryEnemies(p.Pos, p.Radius, hits);
                Emit(SimEventType.Strike, p.Pos, p.Damage.Element, 0f, p.Damage.Source?.Uid ?? 0, 0, p.Visual, false, p.Radius);
                for (int k = 0; k < hits.Count; k++)
                {
                    EnemyUnit e = hits[k];
                    DealDamage(e, p.Damage);
                    if (p.Burn && e.Alive) ApplyBurn(e, p.Damage.Source, 4f);
                }
                if (p.BurnSpread > 0f)
                {
                    QueryEnemies(p.Pos, p.BurnSpread, hits);
                    for (int k = 0; k < hits.Count; k++) ApplyBurn(hits[k], p.Damage.Source, 4f);
                }
                ReturnList(hits);
            }
            else if (p.Target != null && p.Target.Alive)
            {
                DealDamage(p.Target, p.Damage);
                if (p.Burn && p.Target.Alive) ApplyBurn(p.Target, p.Damage.Source, 4f);
            }
        }

        private bool OutOfArena(Vec2 p)
        {
            return p.X < -Content.Arena.HalfWidth - 2f || p.X > Content.Arena.HalfWidth + 2f ||
                   p.Y < -Content.Arena.HalfHeight - 2f || p.Y > Content.Arena.HalfHeight + 2f;
        }

        // ------------------------------------------------------------------ zones

        public Zone SpawnZone(ZoneKind kind, Vec2 pos, float radius, float duration, HeroUnit owner, Element el, float power,
            int gen, string reactionId)
        {
            // Cap concurrent zones: oldest of the same kind expires first (readability + performance).
            int sameKind = 0;
            for (int i = 0; i < Zones.Count; i++) if (Zones[i].Kind == kind) sameKind++;
            if (sameKind >= 6)
            {
                for (int i = 0; i < Zones.Count; i++)
                {
                    if (Zones[i].Kind != kind) continue;
                    Zones.RemoveAt(i);
                    break;
                }
            }
            var z = new Zone
            {
                Uid = _nextFxUid++,
                Kind = kind,
                Pos = pos,
                Radius = radius,
                Remaining = duration,
                Duration = duration,
                Power = power,
                Element = el,
                Owner = owner,
                Generation = gen,
                ReactionId = reactionId,
                TickTimer = 0f
            };
            Zones.Add(z);
            Emit(SimEventType.ZoneSpawn, pos, el, duration, owner?.Uid ?? 0, z.Uid, kind.ToString(), false, radius, gen);
            return z;
        }

        private void UpdateZones(float dt)
        {
            for (int zi = 0; zi < Zones.Count; zi++)
            {
                Zone z = Zones[zi];
                z.Remaining -= dt;
                z.TickTimer -= dt;
                bool tick = z.TickTimer <= 0f;
                List<EnemyUnit> inside = RentList();
                switch (z.Kind)
                {
                    case ZoneKind.Field:
                        UpdateField(z, dt, tick, inside);
                        break;
                    case ZoneKind.Mud:
                        QueryEnemies(z.Pos, z.Radius, inside);
                        for (int i = 0; i < inside.Count; i++) Slow(inside[i], z.Power, 0.3f);
                        break;
                    case ZoneKind.Vortex:
                        QueryEnemies(z.Pos, z.Radius, inside);
                        for (int i = 0; i < inside.Count; i++) Pull(inside[i], z.Pos, 2.2f, 0.15f);
                        if (tick)
                        {
                            z.TickTimer = 0.5f;
                            for (int i = 0; i < inside.Count; i++)
                            {
                                DamageRequest d = DamageRequest.From(z.Owner, z.Power, Element.Wind, 0.4f, DamageKind.Skill, z.Generation);
                                d.CanCrit = false;
                                DealDamage(inside[i], d);
                            }
                        }
                        break;
                    case ZoneKind.HealingRain:
                        if (tick)
                        {
                            z.TickTimer = 0.5f;
                            for (int i = 0; i < Heroes.Count; i++)
                            {
                                HeroUnit h = Heroes[i];
                                if (h.Alive && Vec2.Distance(h.Pos, z.Pos) <= z.Radius + h.Radius) HealHero(h, z.Heal, z.Owner);
                            }
                            QueryEnemies(z.Pos, z.Radius, inside);
                            for (int i = 0; i < inside.Count; i++)
                            {
                                if (z.Offensive)
                                {
                                    DamageRequest d = DamageRequest.From(z.Owner, z.Power, Element.Water, 0.5f, DamageKind.Skill, z.Generation);
                                    d.CanCrit = false;
                                    DealDamage(inside[i], d);
                                }
                                else
                                {
                                    ApplyElement(inside[i], Element.Water, 0.5f, z.Owner, z.Generation);
                                }
                            }
                        }
                        break;
                    case ZoneKind.Thunderstorm:
                    case ZoneKind.StormTrail:
                    case ZoneKind.TempestLink:
                        if (tick)
                        {
                            z.TickTimer = z.Kind == ZoneKind.Thunderstorm ? 0.7f : 0.5f;
                            QueryEnemies(z.Pos, z.Radius, inside);
                            if (inside.Count > 0)
                            {
                                int strikes = z.Kind == ZoneKind.TempestLink ? 2 : 1;
                                for (int s = 0; s < strikes; s++)
                                {
                                    EnemyUnit e = inside[Rng.Range(0, inside.Count)];
                                    Emit(SimEventType.Strike, e.Pos, Element.Lightning, 0f, z.Owner?.Uid ?? 0, e.Uid, "storm_bolt", false, 0.3f, z.Generation);
                                    DealDamage(e, new DamageRequest
                                    {
                                        Source = z.Owner,
                                        Attack = z.Power,
                                        Multiplier = 1f,
                                        Element = Element.Lightning,
                                        Gauge = z.Kind == ZoneKind.StormTrail ? 0.5f : 0f,
                                        Kind = z.ReactionId != null ? DamageKind.Reaction : DamageKind.Skill,
                                        Generation = z.Generation,
                                        ReactionId = z.ReactionId,
                                        SourceTag = z.Kind == ZoneKind.TempestLink ? "tempest_engine" : null
                                    });
                                }
                            }
                        }
                        break;
                    case ZoneKind.Magma:
                    case ZoneKind.Blizzard:
                    case ZoneKind.BurningGround:
                        if (tick)
                        {
                            z.TickTimer = 0.5f;
                            QueryEnemies(z.Pos, z.Radius, inside);
                            for (int i = 0; i < inside.Count; i++)
                            {
                                EnemyUnit e = inside[i];
                                DealDamage(e, new DamageRequest
                                {
                                    Source = z.Owner,
                                    Attack = z.Power * 0.5f,
                                    Multiplier = 1f,
                                    Element = z.Element,
                                    Kind = z.ReactionId != null ? DamageKind.Reaction : DamageKind.Dot,
                                    Generation = z.Generation,
                                    ReactionId = z.ReactionId
                                });
                                if (z.Kind == ZoneKind.Blizzard && e.Alive)
                                {
                                    e.Aura[(int)Element.Ice] = SimMath.Max(e.Aura[(int)Element.Ice], 0.6f);
                                    Slow(e, 0.3f, 0.6f);
                                }
                            }
                        }
                        break;
                }
                ReturnList(inside);
            }
            for (int i = Zones.Count - 1; i >= 0; i--)
            {
                if (Zones[i].Remaining > 0f) continue;
                Zone dead = Zones[i];
                Zones.RemoveAt(i);
                if (dead.Kind == ZoneKind.Field) ExpireField(dead);
            }
        }

        // ------------------------------------------------------------------ delayed strikes

        public void AddStrike(DelayedStrike s)
        {
            s.Total = s.Delay;
            Strikes.Add(s);
            Emit(SimEventType.Telegraph, s.Pos, s.Element, s.Delay, s.Source?.Uid ?? s.EnemySource?.Uid ?? 0, 0, s.Kind.ToString(), false, s.Radius, s.Generation);
        }

        private void UpdateStrikes(float dt)
        {
            for (int i = 0; i < Strikes.Count; i++)
            {
                DelayedStrike s = Strikes[i];
                s.Delay -= dt;
                if (s.Delay > 0f) continue;
                ResolveStrike(s);
            }
            Strikes.RemoveAll(s => s.Delay <= 0f);
        }

        private void ResolveStrike(DelayedStrike s)
        {
            Emit(SimEventType.Strike, s.Pos, s.Element, 0f, s.Source?.Uid ?? 0, 0, s.Kind.ToString(), false, s.Radius, s.Generation);
            if (s.Kind == StrikeKind.BossSlam || s.Kind == StrikeKind.BossLaneMark)
            {
                for (int i = 0; i < Heroes.Count; i++)
                {
                    HeroUnit h = Heroes[i];
                    if (h.Alive && Vec2.Distance(h.Pos, s.Pos) <= s.Radius + h.Radius) DamageHero(h, s.Power, s.EnemySource);
                }
                if (Vec2.Distance(Crystal.Pos, s.Pos) <= s.Radius + Crystal.Radius) DamageCrystal(s.Power * 0.5f, s.EnemySource);
                return;
            }
            if (s.Kind == StrikeKind.Hazard)
            {
                for (int i = 0; i < Heroes.Count; i++)
                {
                    HeroUnit h = Heroes[i];
                    if (h.Alive && Vec2.Distance(h.Pos, s.Pos) <= s.Radius + h.Radius) DamageHero(h, s.Power, null);
                }
            }
            List<EnemyUnit> hits = RentList();
            QueryEnemies(s.Pos, s.Radius, hits);
            bool trigger = s.Kind == StrikeKind.Hazard || (s.Kind == StrikeKind.ReactionBurst && s.ReactionId == null);
            for (int k = 0; k < hits.Count; k++)
            {
                EnemyUnit e = hits[k];
                DealDamage(e, new DamageRequest
                {
                    Source = s.Source,
                    Attack = s.Power,
                    Multiplier = s.Multiplier,
                    Element = s.Element,
                    Gauge = s.Gauge,
                    Kind = s.ReactionId != null ? DamageKind.Reaction : (trigger ? DamageKind.Trigger : DamageKind.Skill),
                    Generation = s.Generation,
                    ReactionId = s.ReactionId,
                    SourceTag = s.SourceTag,
                    CanCrit = s.ReactionId == null && !trigger
                });
                if (s.Stun > 0f && e.Alive) Stun(e, s.Stun);
                if (s.Status != null && e.Alive) ApplyStatus(e, s.Status, s.StatusParams, 1f, s.Source, s.Generation);
            }
            ReturnList(hits);
        }

        // ------------------------------------------------------------------ enemy bolts

        public void FireBolt(EnemyUnit owner, HeroUnit target, bool atCrystal, float damage)
        {
            Bolts.Add(new EnemyBolt
            {
                Pos = owner.Pos,
                Target = atCrystal ? Crystal.Pos : target.Pos,
                HeroTarget = target,
                AtCrystal = atCrystal,
                Speed = 7f,
                Damage = damage,
                Owner = owner,
                Alive = true
            });
        }

        private void UpdateBolts(float dt)
        {
            for (int i = 0; i < Bolts.Count; i++)
            {
                EnemyBolt b = Bolts[i];
                if (b.HeroTarget != null && b.HeroTarget.Alive) b.Target = b.HeroTarget.Pos;
                b.Pos = Vec2.MoveTowards(b.Pos, b.Target, b.Speed * dt);
                if (BoltBlocked(b))
                {
                    b.Alive = false;
                    Emit(SimEventType.Miss, b.Pos, Element.Void, 0f, b.Owner?.Uid ?? 0, 0, "blocked");
                    continue;
                }
                if (Vec2.SqrDistance(b.Pos, b.Target) > 0.04f) continue;
                b.Alive = false;
                if (b.AtCrystal) DamageCrystal(b.Damage, b.Owner);
                else if (b.HeroTarget != null && b.HeroTarget.Alive) DamageHero(b.HeroTarget, b.Damage, b.Owner);
            }
            Bolts.RemoveAll(b => !b.Alive);
        }

        private bool BoltBlocked(EnemyBolt b)
        {
            for (int i = 0; i < Zones.Count; i++)
            {
                Zone z = Zones[i];
                if (z.Kind == ZoneKind.Field && z.Field.BlockBolts && InsideField(z, b.Pos, 0f)) return true;
            }
            return false;
        }

        // ------------------------------------------------------------------ declarative triggers (relics/cards)

        /// <summary>
        /// Fires all trigger ops listening to an event. Only the op's declared filters and action are
        /// read; the owning relic/card id is used for statistics only.
        /// </summary>
        public void FireTrigger(string on, HeroUnit hero, EnemyUnit enemy, Vec2 pos, string reactionId)
        {
            for (int i = 0; i < Triggers.Count; i++)
            {
                TriggerInstance t = Triggers[i];
                EffectOp op = t.Source.Op;
                if (op.Trigger != on) continue;
                if (t.Cooldown > 0f) continue;
                if (!string.IsNullOrEmpty(op.Reaction) && op.Reaction != "*" && op.Reaction != reactionId) continue;
                string el = op.Params.GetString("heroElement");
                if (!string.IsNullOrEmpty(el) && (hero == null || ElementUtil.Key(hero.Def.Element) != el)) continue;
                string heroId = op.Params.GetString("hero");
                if (!string.IsNullOrEmpty(heroId) && (hero == null || hero.Def.Id != heroId)) continue;
                int maxUses = (int)op.Params.Get("usesPerWave");
                if (maxUses > 0 && t.UsesThisWave >= maxUses) continue;
                int every = (int)op.Params.Get("every");
                if (every > 1)
                {
                    t.Counter++;
                    if (t.Counter < every) continue;
                    t.Counter = 0;
                }
                float chance = op.Params.Get("chance", 1f);
                if (chance < 1f && !Rng.Chance(chance)) continue;
                t.Cooldown = op.Params.Get("cooldown");
                t.UsesThisWave++;
                ExecuteAction(t.Source, hero, enemy, pos);
            }
        }

        private void UpdateTriggers(float dt)
        {
            for (int i = 0; i < Triggers.Count; i++)
            {
                TriggerInstance t = Triggers[i];
                if (t.Cooldown > 0f) t.Cooldown -= dt;
                if (t.Source.Op.Trigger == "periodic" && t.Cooldown <= 0f)
                {
                    t.Cooldown = t.Source.Op.Params.Get("interval", 5f);
                    ExecuteAction(t.Source, null, null, Crystal.Pos);
                }
            }
        }

        private void ExecuteAction(SourcedOp src, HeroUnit hero, EnemyUnit enemy, Vec2 pos)
        {
            EffectOp op = src.Op;
            ParamBag p = op.Params;
            float stacks = src.Stacks;
            float dealt = 0f;
            Emit(SimEventType.RelicProc, pos, Element.None, 0f, hero?.Uid ?? 0, enemy?.Uid ?? 0, src.Source);
            switch (op.Action)
            {
                case "burst":
                {
                    Element el = ContentDatabase.ParseElement(p.GetString("element", "none"));
                    float power = p.Get("power", 1f) * stacks;
                    float atk = hero != null ? hero.Stat(StatId.Attack) : 25f * WaveLevelScale;
                    float radius = p.Get("radius", 1.2f);
                    List<EnemyUnit> hits = RentList();
                    QueryEnemies(pos, radius, hits);
                    Emit(SimEventType.Strike, pos, el, 0f, hero?.Uid ?? 0, 0, "relic_burst", false, radius, MaxProcGeneration);
                    for (int i = 0; i < hits.Count; i++)
                    {
                        dealt += DealDamage(hits[i], new DamageRequest
                        {
                            Source = hero,
                            Attack = atk,
                            Multiplier = power,
                            Element = el,
                            Gauge = p.Get("gauge"),
                            Kind = DamageKind.Trigger,
                            Generation = (int)p.Get("generation", MaxProcGeneration),
                            SourceTag = src.Source
                        });
                    }
                    ReturnList(hits);
                    break;
                }
                case "apply_element":
                {
                    Element el = ContentDatabase.ParseElement(p.GetString("element"));
                    List<EnemyUnit> hits = RentList();
                    QueryEnemies(pos, p.Get("radius", 1.5f), hits);
                    for (int i = 0; i < hits.Count; i++) ApplyElement(hits[i], el, p.Get("gauge", 1f) * stacks, hero, (int)p.Get("generation", 1f));
                    ReturnList(hits);
                    break;
                }
                case "chain":
                {
                    if (enemy == null || !enemy.Alive) break;
                    ReactionDef ec = Content.Reactions["electrocharge"];
                    ChainBounce(enemy, hero, (int)(p.Get("bounces", 3f) * stacks), p.Get("radius", 3f), ec, MaxProcGeneration, false);
                    break;
                }
                case "heal_team":
                    for (int i = 0; i < Heroes.Count; i++) HealHero(Heroes[i], Heroes[i].MaxHp * p.Get("pct", 0.05f) * stacks, null);
                    break;
                case "crystal_shield":
                    ShieldCrystal(Crystal.MaxHp * p.Get("pct", 0.03f) * stacks);
                    break;
                case "crystal_heal":
                    HealCrystal(Crystal.MaxHp * p.Get("pct", 0.01f) * stacks);
                    break;
                case "gold":
                    Stats.GoldFromKills += p.Get("amount", 1f) * stacks;
                    break;
                case "team_buff":
                {
                    StatId stat = ContentDatabase.ParseStat(p.GetString("stat", "attack"));
                    for (int i = 0; i < Heroes.Count; i++)
                    {
                        HeroUnit h = Heroes[i];
                        if (!h.Alive) continue;
                        AddBuff(h, stat, p.Get("pct", 0.2f) * stacks, p.Get("duration", 4f), src.Source);
                    }
                    break;
                }
                case "hero_buff":
                    if (hero != null && hero.Alive)
                        AddBuff(hero, ContentDatabase.ParseStat(p.GetString("stat", "attack")), p.Get("pct", 0.2f) * stacks, p.Get("duration", 4f), src.Source);
                    break;
                case "revive":
                    if (hero != null && hero.Hp <= 0f)
                    {
                        hero.Hp = hero.MaxHp * p.Get("hpPct", 0.5f);
                        Emit(SimEventType.HeroRevived, hero.Pos, Element.Fire, hero.Hp, 0, hero.Uid, src.Source);
                    }
                    break;
                case "zone":
                {
                    ZoneKind kind = ContentDatabase.ParseEnum<ZoneKind>(p.GetString("kind", "burning_ground"), "zone kind");
                    Element el = ContentDatabase.ParseElement(p.GetString("element", "fire"));
                    float atk = hero != null ? hero.Stat(StatId.Attack) : 25f * WaveLevelScale;
                    SpawnZone(kind, pos, p.Get("radius", 1.4f), p.Get("duration", 3f), hero, el, atk * p.Get("power", 0.5f) * stacks, MaxProcGeneration, null);
                    break;
                }
                case "refund_cooldown":
                    if (hero != null) hero.SkillTimer = SimMath.Max(0f, hero.SkillTimer - p.Get("seconds", 1f) * stacks);
                    break;
                case "team_refund_cooldown":
                    for (int i = 0; i < Heroes.Count; i++)
                        Heroes[i].SkillTimer = SimMath.Max(0f, Heroes[i].SkillTimer - p.Get("seconds", 1f) * stacks);
                    break;
                case "echo_cast":
                    if (hero != null && hero.Alive) CastSkill(hero, p.Get("power", 0.5f) * stacks, true);
                    break;
                case "execute":
                    if (enemy != null && enemy.Alive && !enemy.IsBoss && enemy.HpFraction <= p.Get("threshold", 0.12f))
                    {
                        dealt += enemy.Hp;
                        DealDamage(enemy, new DamageRequest { Source = hero, Attack = enemy.Hp + enemy.Shield + 1f, Multiplier = 1f, Kind = DamageKind.Trigger, IgnoreDefense = true, Generation = MaxProcGeneration, SourceTag = src.Source });
                    }
                    break;
                case "slow_all":
                {
                    List<EnemyUnit> hits = RentList();
                    QueryEnemies(pos, p.Get("radius", 3f), hits);
                    for (int i = 0; i < hits.Count; i++) Slow(hits[i], p.Get("slow", 0.3f), p.Get("duration", 2f));
                    ReturnList(hits);
                    break;
                }
            }
            Stats.AddSource(src.Source, 0f);
        }

        public void AddBuff(HeroUnit h, StatId stat, float pct, float duration, string source)
        {
            // Same-source buffs refresh instead of stacking (no runaway stacking from rapid triggers).
            for (int i = 0; i < h.Buffs.Count; i++)
            {
                if (h.Buffs[i].Source != source || h.Buffs[i].Stat != stat) continue;
                TimedBuff b = h.Buffs[i];
                b.Remaining = SimMath.Max(b.Remaining, duration);
                b.Percent = SimMath.Max(b.Percent, pct);
                h.Buffs[i] = b;
                return;
            }
            h.Buffs.Add(new TimedBuff { Stat = stat, Percent = pct, Remaining = duration, Source = source });
        }
    }
}
