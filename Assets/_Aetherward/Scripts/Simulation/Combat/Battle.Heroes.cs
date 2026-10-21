using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    /// <summary>Hero AI: Idle -> FindTarget -> ApproachWithinLeash -> Attack/Cast -> Recover -> Return, plus Stunned/Downed.</summary>
    public sealed partial class Battle
    {
        private const float RetargetInterval = 0.25f;

        private void UpdateHero(HeroUnit h, float dt)
        {
            if (!h.Alive) return;
            if (h.HitFlash > 0f) h.HitFlash -= dt;
            for (int i = h.Buffs.Count - 1; i >= 0; i--)
            {
                TimedBuff b = h.Buffs[i];
                b.Remaining -= dt;
                if (b.Remaining <= 0f) h.Buffs.RemoveAt(i);
                else h.Buffs[i] = b;
            }
            if (h.BarrierTimer > 0f)
            {
                h.BarrierTimer -= dt;
                if (h.BarrierTimer <= 0f && h.ShieldRetaliate > 0f && h.Shield <= 0f) h.ShieldRetaliate = 0f;
            }
            if (h.RetaliateTimer > 0f) h.RetaliateTimer -= dt;
            TickHeroDebuffs(h, dt);
            TickPassive(h, dt);

            if (h.StunTimer > 0f)
            {
                h.StunTimer -= dt;
                h.State = HeroState.Stunned;
                return;
            }

            float haste = 1f + (h.FieldTimer > 0f ? h.FieldHaste : 0f);
            if (h.ChillTimer > 0f)
            {
                h.ChillTimer -= dt;
                haste *= 1f - h.ChillAmount;
            }
            h.AttackTimer -= dt * haste;
            h.SkillTimer -= dt * haste * (h.LeechTimer > 0f ? 1f - h.LeechAmount : 1f);
            h.RetargetTimer -= dt;
            if (h.CastLock > 0f) h.CastLock -= dt;

            if (h.Target != null && (!h.Target.Alive || !InAcquireRange(h, h.Target, 1.25f))) h.Target = null;
            if (h.Target == null || h.RetargetTimer <= 0f)
            {
                h.Target = SelectTarget(h);
                h.RetargetTimer = RetargetInterval;
            }

            if (h.SkillTimer <= 0f && h.CastLock <= 0f && h.SilenceTimer <= 0f)
            {
                if (CastSkill(h, 1f, false))
                {
                    h.SkillTimer = h.Skill.Cooldown * h.Stat(StatId.SkillCooldown);
                    h.CastLock = 0.3f;
                    h.State = HeroState.Cast;
                    return;
                }
                h.SkillTimer = 0.2f; // nothing worth casting on; re-check shortly
            }

            TickUltimate(h, dt);
            if (h.State == HeroState.Cast && h.CastLock >= 0.6f) return;   // just cast the ultimate
            float leash = EffectiveLeash(h);
            if (h.Target != null)
            {
                float reach = AttackReach(h, h.Target);
                float dist = Vec2.Distance(h.Pos, h.Target.Pos);
                h.Facing = (h.Target.Pos - h.Pos).Normalized;
                if (h.AttackTimer > 0.15f && Kite(h, leash, dt)) return;
                if (dist > reach)
                {
                    if (h.Melee || leash > 0.3f)
                    {
                        Vec2 desired = h.Target.Pos - h.Facing * (reach * 0.8f);
                        MoveHeroWithinLeash(h, desired, leash, dt);
                        h.State = HeroState.Approach;
                    }
                    else
                    {
                        h.State = HeroState.Idle;
                    }
                }
                else if (h.AttackTimer <= 0f && h.CastLock <= 0f)
                {
                    BasicAttack(h, h.Target);
                    h.AttackTimer = h.Stat(StatId.AttackInterval);
                    h.State = HeroState.Attack;
                }
            }
            else
            {
                if (Vec2.SqrDistance(h.Pos, h.Anchor) > 0.0025f)
                {
                    if (Setup.DynamicParty) MoveHeroWithinLeash(h, h.Anchor, leash, dt);
                    else h.Pos = Vec2.MoveTowards(h.Pos, h.Anchor, h.Stat(StatId.MoveSpeed) * dt);
                    h.State = HeroState.Return;
                }
                else h.State = HeroState.Idle;
            }
        }

        private void MoveHeroWithinLeash(HeroUnit h, Vec2 desired, float leash, float dt)
        {
            Vec2 offset = desired - h.Anchor;
            if (offset.Length > leash) desired = h.Anchor + offset.Normalized * leash;
            Vec2 next = Vec2.MoveTowards(h.Pos, desired, h.Stat(StatId.MoveSpeed) * dt);
            // Collision-safe: keep out of the crystal and away from other heroes.
            float minC = Crystal.Radius + h.Radius;
            if (Vec2.Distance(next, Crystal.Pos) < minC) next = Crystal.Pos + (next - Crystal.Pos).Normalized * minC;
            for (int i = 0; i < Heroes.Count; i++)
            {
                HeroUnit o = Heroes[i];
                if (o == h || !o.Alive) continue;
                float min = h.Radius + o.Radius;
                Vec2 d = next - o.Pos;
                float len = d.Length;
                if (len < min && len > 1e-4f) next = o.Pos + d / len * min;
            }
            h.Pos = ClampToWalk(next, h.Radius);
        }

        public float AttackReach(HeroUnit h, EnemyUnit e) => h.Stat(StatId.Range) + e.Radius + h.Radius * 0.5f;

        private bool InAcquireRange(HeroUnit h, EnemyUnit e, float slack)
        {
            float acquire = h.Stat(StatId.Range) + EffectiveLeash(h) + e.Radius;
            return Vec2.Distance(h.Anchor, e.Pos) <= acquire * slack;
        }

        // ------------------------------------------------------------------ targeting

        /// <summary>Capped, allocation-free target search with deterministic uid tie-break.</summary>
        public EnemyUnit SelectTarget(HeroUnit h) => Setup.UtilityTargeting ? SelectTargetUtility(h) : SelectTarget(h, h.Targeting, 0f);

        /// <summary>The role targeting profile's raw preference for an enemy (higher is better).</summary>
        private float ProfileScore(HeroUnit h, TargetProfile profile, EnemyUnit e)
        {
            float score;
            switch (profile)
            {
                case TargetProfile.Nearest:
                    score = -Vec2.SqrDistance(h.Pos, e.Pos);
                    break;
                case TargetProfile.NearestToCrystal:
                    score = -RemainingPath(e);
                    break;
                case TargetProfile.Cluster:
                    score = ClusterScore(e, 1.5f) * 10f - RemainingPath(e) * 0.1f;
                    break;
                case TargetProfile.Elite:
                    score = (e.IsBoss ? 3000f : 0f) + (e.Elite ? 2000f : 0f) + e.MaxHp * 0.01f - RemainingPath(e) * 0.05f;
                    break;
                case TargetProfile.Execute:
                    score = (1f - e.HpFraction) * 100f + (e.Elite ? 20f : 0f);
                    break;
                case TargetProfile.ReactionOpportunity:
                    score = ReactionOpportunity(h.Def.Element, e) * 100f - RemainingPath(e);
                    break;
                case TargetProfile.Strongest:
                    score = e.Hp;
                    break;
                default:
                    score = -RemainingPath(e);
                    break;
            }
            return score;
        }


        public EnemyUnit SelectTarget(HeroUnit h, TargetProfile profile, float extraRange)
        {
            float range = h.Stat(StatId.Range) + EffectiveLeash(h) + extraRange;
            List<EnemyUnit> c = RentList();
            QueryEnemies(h.Anchor, range, c);
            EnemyUnit best = null;
            float bestScore = float.MinValue;
            int evaluated = 0;
            for (int i = 0; i < c.Count && evaluated < 40; i++)
            {
                EnemyUnit e = c[i];
                if (!e.Alive || e.Burrowed) continue;
                evaluated++;
                float score = ProfileScore(h, profile, e);
                if (score > bestScore)
                {
                    bestScore = score;
                    best = e;
                }
            }
            ReturnList(c);
            return best;
        }

        private int ClusterScore(EnemyUnit e, float radius)
        {
            List<EnemyUnit> c = RentList();
            QueryEnemies(e.Pos, radius, c);
            int n = c.Count;
            ReturnList(c);
            return n;
        }

        private float ReactionOpportunity(Element mine, EnemyUnit e)
        {
            for (int i = 1; i < ElementUtil.Count; i++)
            {
                if (i == (int)mine || e.Aura[i] <= 0.05f) continue;
                if (Content.ReactionFor(mine, (Element)i) != null) return 1f;
            }
            return 0f;
        }

        public HeroUnit LowestHpAlly(Vec2 from, float range, float belowFraction)
        {
            HeroUnit best = null;
            float bestF = belowFraction;
            for (int i = 0; i < Heroes.Count; i++)
            {
                HeroUnit h = Heroes[i];
                if (!h.Alive || Vec2.Distance(from, h.Pos) > range) continue;
                if (h.HpFraction < bestF)
                {
                    bestF = h.HpFraction;
                    best = h;
                }
            }
            return best;
        }

        // ------------------------------------------------------------------ attacks

        private void BasicAttack(HeroUnit h, EnemyUnit target)
        {
            h.AttackCount++;
            FireTrigger("basic_attack", h, target, target.Pos, null);
            DamageRequest d = DamageRequest.From(h, h.Basic.Multiplier, h.Def.Element, h.Basic.Gauge, DamageKind.Basic);
            d.BonusMult += PassiveBonus(h, target);
            Emit(SimEventType.BasicAttack, h.Pos, h.Def.Element, 0f, h.Uid, target.Uid, h.Melee ? "melee" : "ranged");

            // Element gauge is applied at most every other basic attack: keeps auras readable.
            bool slipstream = h.PassiveKind == "slipstream" && h.PassiveStacks > 0;
            if (h.AttackCount % 2 == 0 && !h.Basic.Params.Flag("alwaysApply") && !slipstream) d.Gauge = 0f;
            // Elemental Awakening: every other element-applying basic carries the secondary element.
            if (h.SecondaryElement != Element.None && h.AttackCount % 4 == 1) d.Element = h.SecondaryElement;

            int pierceEvery = (int)(h.Skill.Params.Get("basicPierceEvery") > 0 ? h.Skill.Params.Get("basicPierceEvery") : h.Basic.Params.Get("pierceEvery"));
            if (h.Melee || h.Basic.Kind == "melee")
            {
                DealDamage(target, d);
            }
            else if (pierceEvery > 0 && h.AttackCount % pierceEvery == 0)
            {
                FireProjectile(h, ProjectileKind.Pierce, target, target.Pos, h.Basic.ProjectileSpeed * 1.3f, 0.35f, d, "basic_pierce");
            }
            else
            {
                FireProjectile(h, ProjectileKind.Single, target, target.Pos, h.Basic.ProjectileSpeed, 0f, d, "basic");
            }
            OnBasicAttackPassive(h);
            OnBasicAttackPassiveExt(h, target);
        }

        public void Taunt(HeroUnit h, float radius, float duration)
        {
            List<EnemyUnit> c = RentList();
            QueryEnemies(h.Pos, radius, c);
            for (int i = 0; i < c.Count; i++)
            {
                EnemyUnit e = c[i];
                if (e.Def.Behavior == EnemyBehavior.Sapper && !e.Elite) continue; // sappers ignore taunts by design
                float d = e.IsBoss ? duration * 0.3f : duration * (1f - e.Tenacity * 0.5f);
                e.Taunter = h;
                e.TauntTimer = SimMath.Max(e.TauntTimer, d);
            }
            ReturnList(c);
            Emit(SimEventType.Taunt, h.Pos, h.Def.Element, duration, h.Uid, 0, "taunt", false, radius);
        }

        // ------------------------------------------------------------------ skills

        /// <summary>
        /// Executes the hero's active skill (possibly evolved). Returns false if no meaningful target
        /// exists, so cooldowns are not wasted. <paramref name="power"/> scales echo casts.
        /// </summary>
        public bool CastSkill(HeroUnit h, float power, bool echo)
        {
            SkillDef s = h.Skill;
            float range = h.Stat(StatId.Range) + EffectiveLeash(h) + s.Params.Get("rangeBonus", 0f);
            Element el = h.Def.Element;
            float mult = s.Multiplier * power;
            bool cast = false;
            Vec2 castPos = h.Pos;

            switch (s.Kind)
            {
                case "fireball":
                {
                    EnemyUnit t = SelectTarget(h, TargetProfile.Cluster, s.Params.Get("rangeBonus", 1f));
                    if (t == null) break;
                    DamageRequest d = DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill);
                    Projectile p = FireProjectile(h, ProjectileKind.Explode, t, t.Pos, s.Params.Get("speed", 8f), s.Params.Get("radius", 1.3f), d, s.Kind);
                    p.Burn = true;
                    p.BurnSpread = s.Params.Get("burnSpread");
                    castPos = t.Pos;
                    cast = true;
                    break;
                }
                case "meteor":
                {
                    EnemyUnit t = SelectTarget(h, TargetProfile.Cluster, s.Params.Get("rangeBonus", 1.5f));
                    if (t == null) break;
                    Vec2 lead = t.Pos + t.Facing * t.Speed * 0.5f; // lead the target slightly
                    AddStrike(new DelayedStrike
                    {
                        Kind = StrikeKind.Meteor,
                        Pos = lead,
                        Delay = s.Params.Get("delay", 0.9f),
                        Radius = s.Params.Get("radius", 2.2f),
                        Source = h,
                        Element = el,
                        Power = h.Stat(StatId.Attack),
                        Multiplier = mult,
                        Gauge = s.Gauge,
                        Stun = s.Params.Get("stun", 0.4f)
                    });
                    castPos = lead;
                    cast = true;
                    break;
                }
                case "cleave":
                {
                    EnemyUnit t = h.Target;
                    if (t == null || Vec2.Distance(h.Pos, t.Pos) > AttackReach(h, t) + 0.6f) break;
                    float radius = s.Params.Get("radius", 1.6f);
                    float cosHalf = System.MathF.Cos(s.Params.Get("arc", 130f) * 0.5f * 0.0174533f);
                    Vec2 dir = (t.Pos - h.Pos).Normalized;
                    List<EnemyUnit> c = RentList();
                    QueryEnemies(h.Pos, radius, c);
                    for (int i = 0; i < c.Count; i++)
                    {
                        EnemyUnit e = c[i];
                        Vec2 to = (e.Pos - h.Pos).Normalized;
                        if (Vec2.Dot(to, dir) < cosHalf && Vec2.Distance(e.Pos, h.Pos) > 0.5f) continue;
                        DamageRequest d = DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill);
                        d.BonusMult += PassiveBonus(h, e);
                        DealDamage(e, d);
                    }
                    ReturnList(c);
                    if (s.Params.Get("taunt") > 0f) Taunt(h, s.Params.Get("tauntRadius", 2.2f), s.Params.Get("taunt"));
                    if (s.Params.Get("groundDuration") > 0f)
                        SpawnZone(ZoneKind.BurningGround, h.Pos + dir * radius * 0.6f, radius * 0.7f, s.Params.Get("groundDuration"), h, el, h.Stat(StatId.Attack) * s.Params.Get("groundPower", 0.5f), 1, null);
                    if (s.Params.Get("shieldPct") > 0f) AddHeroShield(h, h.MaxHp * s.Params.Get("shieldPct"), h);
                    castPos = t.Pos;
                    cast = true;
                    break;
                }
                case "duel_strike":
                {
                    EnemyUnit t = SelectTarget(h, TargetProfile.Elite, 0f) ?? h.Target;
                    if (t == null || Vec2.Distance(h.Anchor, t.Pos) > range + 0.5f) break;
                    h.Pos = ClampToLeash(h, t.Pos - (t.Pos - h.Pos).Normalized * (t.Radius + h.Radius));
                    int hits = (int)s.Params.Get("hits", 3f);
                    for (int i = 0; i < hits && t.Alive; i++)
                    {
                        DamageRequest d = DamageRequest.From(h, mult, el, i == 0 ? s.Gauge : 0f, DamageKind.Skill);
                        d.BonusMult += PassiveBonus(h, t);
                        DealDamage(t, d);
                    }
                    AddBuff(h, StatId.AttackInterval, s.Params.Get("haste", 0.4f), s.Params.Get("hasteDuration", 3f), "duel_strike");
                    castPos = t.Pos;
                    cast = true;
                    break;
                }
                case "heal_rain":
                {
                    HeroUnit ally = LowestHpAlly(h.Pos, range + 2.5f, s.Params.Get("healBelow", 0.85f));
                    Vec2 pos;
                    if (ally != null) pos = ally.Pos;
                    else
                    {
                        EnemyUnit t = SelectTarget(h, TargetProfile.Cluster, 0f);
                        if (t == null) break;
                        pos = t.Pos;
                    }
                    float atk = h.Stat(StatId.Attack);
                    // Zone power is the per-tick damage multiplier (offensive rain only).
                    Zone z = SpawnZone(ZoneKind.HealingRain, pos, s.Params.Get("radius", 2.2f), s.Params.Get("duration", 3f), h, Element.Water,
                        mult, 0, null);
                    z.Heal = atk * s.Params.Get("heal", 0.55f) * power;
                    z.Offensive = s.Params.Flag("offensive");
                    if (s.Params.Get("reviveHp") > 0f && !h.ReviveUsedThisWave)
                    {
                        for (int i = 0; i < Heroes.Count; i++)
                        {
                            HeroUnit d = Heroes[i];
                            if (d.Alive) continue;
                            ReviveHero(d, s.Params.Get("reviveHp"));
                            h.ReviveUsedThisWave = true;
                            break;
                        }
                    }
                    if (h.PassiveKind == "tidecall") HealCrystal(Crystal.MaxHp * h.PassiveParams.Get("crystalHealPct", 0.006f) * power);
                    castPos = pos;
                    cast = true;
                    break;
                }
                case "push_wave":
                {
                    EnemyUnit t = SelectTarget(h, TargetProfile.NearestToCrystal, 0f);
                    if (t == null) break;
                    Vec2 dir = (t.Pos - h.Pos).Normalized;
                    float length = s.Params.Get("length", 4f);
                    float width = s.Params.Get("width", 0.9f);
                    Vec2 end = h.Pos + dir * length;
                    List<EnemyUnit> c = RentList();
                    QueryEnemies(Vec2.Lerp(h.Pos, end, 0.5f), length * 0.5f + width, c);
                    for (int i = 0; i < c.Count; i++)
                    {
                        EnemyUnit e = c[i];
                        if (Vec2.DistanceToSegment(e.Pos, h.Pos, end) > width + e.Radius) continue;
                        DamageRequest d = DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill);
                        if (e.Wet) d.BonusMult += s.Params.Get("wetBonus");
                        DealDamage(e, d);
                        if (!e.Alive) continue;
                        Vec2 away = (e.Pos - Crystal.Pos).Normalized;
                        Knock(e, away, s.Params.Get("knock", 1.5f));
                        if (h.PassiveKind == "undertow")
                        {
                            e.VulnerableTimer = h.PassiveParams.Get("duration", 3f);
                            e.VulnerableAmount = SimMath.Max(e.VulnerableAmount, h.PassiveParams.Get("amount", 0.15f));
                        }
                    }
                    ReturnList(c);
                    if (s.Params.Get("healAllies") > 0f)
                    {
                        for (int i = 0; i < Heroes.Count; i++)
                        {
                            HeroUnit a = Heroes[i];
                            if (a.Alive && Vec2.DistanceToSegment(a.Pos, h.Pos - dir * 2f, end) <= width + 1.2f)
                                HealHero(a, h.Stat(StatId.Attack) * s.Params.Get("healAllies") * power, h);
                        }
                    }
                    if (s.Params.Get("crystalShield") > 0f) ShieldCrystal(Crystal.MaxHp * s.Params.Get("crystalShield") * power);
                    castPos = end;
                    cast = true;
                    break;
                }
                case "chain_lightning":
                {
                    TargetProfile prof = s.Params.Flag("preferWet") ? TargetProfile.ReactionOpportunity : TargetProfile.NearestToCrystal;
                    EnemyUnit t = SelectTarget(h, prof, 0.5f);
                    if (t == null) break;
                    int jumps = (int)s.Params.Get("jumps", 4f);
                    float falloff = s.Params.Get("falloff", 0.85f);
                    float jumpRange = s.Params.Get("jumpRange", 2.6f);
                    bool preferWet = s.Params.Flag("preferWet");
                    var visited = HitSetPool.Rent();
                    List<EnemyUnit> c = RentList();
                    EnemyUnit cur = t;
                    Vec2 from = h.Pos;
                    float m = mult;
                    for (int j = 0; j <= jumps && cur != null; j++)
                    {
                        visited.Add(cur.Uid);
                        Emit(SimEventType.Strike, cur.Pos, el, 0f, h.Uid, cur.Uid, "chain", false, 0f);
                        Journal.Pending[Journal.Pending.Count - 1] = WithFrom(Journal.Pending[Journal.Pending.Count - 1], from);
                        int reactionsBefore = h.ReactionsTriggered;
                        DamageRequest d = DamageRequest.From(h, m, el, s.Gauge, DamageKind.Skill);
                        d.BonusMult += PassiveBonus(h, cur);
                        DealDamage(cur, d);
                        if (s.Params.Get("refundOnReaction") > 0f && h.ReactionsTriggered > reactionsBefore)
                            h.SkillTimer -= s.Params.Get("refundOnReaction");
                        from = cur.Pos;
                        m *= falloff;
                        QueryEnemies(cur.Pos, jumpRange, c);
                        EnemyUnit next = null;
                        float bestScore = float.MinValue;
                        for (int i = 0; i < c.Count; i++)
                        {
                            EnemyUnit e = c[i];
                            if (visited.Contains(e.Uid) || !e.Alive) continue;
                            float score = -Vec2.SqrDistance(cur.Pos, e.Pos) + (preferWet && e.Wet ? 100f : 0f);
                            if (score > bestScore) { bestScore = score; next = e; }
                        }
                        cur = next;
                    }
                    if (s.Params.Get("stormAtEnd") > 0f)
                        SpawnZone(ZoneKind.Thunderstorm, from, 1.6f, s.Params.Get("stormAtEnd"), h, Element.Lightning, h.Stat(StatId.Attack) * 0.6f, 1, null);
                    HitSetPool.Return(visited);
                    ReturnList(c);
                    castPos = t.Pos;
                    cast = true;
                    break;
                }
                case "dash_strike":
                {
                    EnemyUnit t = SelectTarget(h, s.Params.Flag("execute") ? TargetProfile.Execute : TargetProfile.Elite, 0f);
                    if (t == null) break;
                    Vec2 start = h.Pos;
                    h.Pos = ClampToLeash(h, t.Pos - (t.Pos - h.Pos).Normalized * (t.Radius + h.Radius));
                    DamageRequest d = DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill);
                    d.BonusMult += PassiveBonus(h, t);
                    if (s.Params.Flag("execute"))
                    {
                        float threshold = s.Params.Get("executeThreshold", 0.18f);
                        if (!t.IsBoss && t.HpFraction <= threshold) d.Attack = t.Hp * 4f + 100f;
                        else d.BonusMult += s.Params.Get("bossBonus", 0.5f);
                    }
                    DealDamage(t, d);
                    if (s.Params.Get("trailDuration") > 0f)
                        SpawnZone(ZoneKind.StormTrail, Vec2.Lerp(start, h.Pos, 0.5f), SimMath.Max(1.2f, Vec2.Distance(start, h.Pos) * 0.6f),
                            s.Params.Get("trailDuration"), h, Element.Lightning, h.Stat(StatId.Attack) * s.Params.Get("trailPower", 0.5f), 0, null);
                    castPos = t.Pos;
                    cast = true;
                    break;
                }
                case "frost_nova":
                {
                    EnemyUnit t = SelectTarget(h, TargetProfile.Cluster, 0.5f);
                    if (t == null) break;
                    float radius = s.Params.Get("radius", 1.8f);
                    List<EnemyUnit> c = RentList();
                    QueryEnemies(t.Pos, radius, c);
                    for (int i = 0; i < c.Count; i++)
                    {
                        EnemyUnit e = c[i];
                        DamageRequest d = DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill);
                        if (e.Frozen) d.BonusMult += s.Params.Get("frozenBonus");
                        DealDamage(e, d);
                        if (!e.Alive) continue;
                        Slow(e, s.Params.Get("slow", 0.4f), s.Params.Get("slowDuration", 2.5f));
                        if (h.PassiveKind == "frostbite") e.ChillDamageReduction = h.PassiveParams.Get("reduction", 0.15f);
                        if (s.Params.Get("frozenBonus") > 0f)
                        {
                            e.VulnerableTimer = SimMath.Max(e.VulnerableTimer, 3f);
                            e.VulnerableAmount = SimMath.Max(e.VulnerableAmount, s.Params.Get("frozenBonus") * 0.5f);
                        }
                    }
                    ReturnList(c);
                    if (s.Params.Get("zoneDuration") > 0f)
                        SpawnZone(ZoneKind.Blizzard, t.Pos, radius, s.Params.Get("zoneDuration"), h, Element.Ice, h.Stat(StatId.Attack) * s.Params.Get("zonePower", 0.45f), 1, null);
                    if (s.Params.Get("crystalShield") > 0f) ShieldCrystal(Crystal.MaxHp * s.Params.Get("crystalShield") * power);
                    castPos = t.Pos;
                    cast = true;
                    break;
                }
                case "ice_shield":
                {
                    bool threatened = h.Target != null || h.HpFraction < 0.9f;
                    if (!threatened) break;
                    AddHeroShield(h, h.MaxHp * s.Params.Get("shieldPct", 0.25f) * power, h);
                    h.ShieldRetaliate = h.Stat(StatId.Attack) * s.Params.Get("retaliate", 0.6f);
                    h.BarrierTimer = s.Params.Get("duration", 5f);
                    Taunt(h, s.Params.Get("tauntRadius", 2.2f), s.Params.Get("taunt", 2.5f));
                    if (s.Params.Get("allyShieldPct") > 0f)
                    {
                        for (int i = 0; i < Heroes.Count; i++)
                        {
                            HeroUnit a = Heroes[i];
                            if (a != h && a.Alive && Vec2.Distance(a.Pos, h.Pos) <= s.Params.Get("allyRadius", 3f))
                                AddHeroShield(a, a.MaxHp * s.Params.Get("allyShieldPct") * power, h);
                        }
                    }
                    cast = true;
                    break;
                }
                case "vortex":
                {
                    EnemyUnit t = SelectTarget(h, TargetProfile.Cluster, 1f);
                    if (t == null) break;
                    float radius = s.Params.Get("radius", 2.2f);
                    Zone z = SpawnZone(ZoneKind.Vortex, t.Pos, radius, s.Params.Get("duration", 1.6f), h, Element.Wind, mult, 0, null);
                    SpreadAuras(t.Pos, radius, h);
                    if (s.Params.Get("teamHaste") > 0f)
                        for (int i = 0; i < Heroes.Count; i++)
                            if (Heroes[i].Alive) AddBuff(Heroes[i], StatId.AttackInterval, s.Params.Get("teamHaste"), s.Params.Get("hasteDuration", 4f), "gale_tactician");
                    castPos = z.Pos;
                    cast = true;
                    break;
                }
                case "pierce_arrow":
                {
                    EnemyUnit t = SelectTarget(h, TargetProfile.Cluster, 2f);
                    if (t == null) break;
                    int arrows = (int)s.Params.Get("arrows", 1f);
                    float spread = s.Params.Get("spread", 14f) * 0.0174533f;
                    float baseAngle = (t.Pos - h.Pos).Angle;
                    for (int i = 0; i < arrows; i++)
                    {
                        float a = baseAngle + (i - (arrows - 1) * 0.5f) * spread;
                        Vec2 target = h.Pos + Vec2.FromAngle(a) * 8f;
                        DamageRequest d = DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill);
                        FireProjectile(h, ProjectileKind.Pierce, null, target, s.Params.Get("speed", 16f), s.Params.Get("width", 0.45f), d, s.Kind);
                    }
                    castPos = t.Pos;
                    cast = true;
                    break;
                }
                case "stone_barrier":
                {
                    List<EnemyUnit> c = RentList();
                    float radius = s.Params.Get("tauntRadius", 2.6f);
                    QueryEnemies(h.Pos, radius, c);
                    int n = c.Count;
                    for (int i = 0; i < c.Count; i++)
                    {
                        DamageRequest d = DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill);
                        DealDamage(c[i], d);
                    }
                    ReturnList(c);
                    if (n == 0 && h.HpFraction > 0.8f) break;
                    Taunt(h, radius, s.Params.Get("taunt", 3f));
                    AddBuff(h, StatId.Defense, s.Params.Get("armorPct", 0.6f), s.Params.Get("duration", 4f), "stone_barrier");
                    AddHeroShield(h, h.MaxHp * s.Params.Get("shieldPct", 0.12f) * power, h);
                    h.BarrierTimer = s.Params.Get("duration", 4f);
                    if (s.Params.Get("crystalReduction") > 0f)
                    {
                        Crystal.TempReduction = s.Params.Get("crystalReduction");
                        Crystal.TempReductionTimer = s.Params.Get("duration", 4f);
                    }
                    if (s.Params.Get("retaliate") > 0f) h.ShieldRetaliate = h.Stat(StatId.Attack) * s.Params.Get("retaliate");
                    cast = true;
                    break;
                }
                case "ground_slam":
                {
                    float radius = s.Params.Get("radius", 1.6f);
                    bool single = s.Params.Flag("single");
                    EnemyUnit t = h.Target;
                    if (t == null || Vec2.Distance(h.Pos, t.Pos) > (single ? AttackReach(h, t) + 0.4f : radius + 0.4f)) break;
                    List<EnemyUnit> c = RentList();
                    if (single) c.Add(t);
                    else QueryEnemies(h.Pos, radius, c);
                    for (int i = 0; i < c.Count; i++)
                    {
                        EnemyUnit e = c[i];
                        DamageRequest d = DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill);
                        d.BonusMult += PassiveBonus(h, e);
                        DealDamage(e, d);
                        if (!e.Alive) continue;
                        ApplyArmorCrack(e, s.Params.Get("crackDuration", 4f), (int)s.Params.Get("crackStacks", 1f), (int)s.Params.Get("crackMax", 1f));
                        Stun(e, s.Params.Get("stun", 0.4f));
                    }
                    ReturnList(c);
                    if (s.Params.Get("aftershock") > 0f)
                    {
                        AddStrike(new DelayedStrike
                        {
                            Kind = StrikeKind.Aftershock,
                            Pos = h.Pos,
                            Delay = 1f,
                            Radius = radius * 1.2f,
                            Source = h,
                            Element = el,
                            Power = h.Stat(StatId.Attack),
                            Multiplier = mult * s.Params.Get("aftershock"),
                            Gauge = 0.5f,
                            Stun = 0.3f
                        });
                    }
                    castPos = single ? t.Pos : h.Pos;
                    cast = true;
                    break;
                }
                default:
                    cast = CastSkillExt(h, s, power, mult, range, el, ref castPos);
                    break;
            }

            if (!cast) return false;
            h.CastCount++;
            h.SkillCasts++;
            Emit(SimEventType.SkillCast, castPos, el, power, h.Uid, 0, s.Kind, false, 0f, echo ? 1 : 0);
            if (!echo)
            {
                FireTrigger("skill_cast", h, null, castPos, null);
                TryTraitEcho(h);
                TryAllyEcho(h);
                MimicOnHeroCast(h);
            }
            return true;
        }

        private Vec2 ClampToLeash(HeroUnit h, Vec2 desired)
        {
            float leash = EffectiveLeash(h);
            Vec2 off = desired - h.Anchor;
            if (off.Length > leash) desired = h.Anchor + off.Normalized * leash;
            float minC = Crystal.Radius + h.Radius;
            if (Vec2.Distance(desired, Crystal.Pos) < minC) desired = Crystal.Pos + (desired - Crystal.Pos).Normalized * minC;
            return desired;
        }

        /// <summary>Wind spread: the strongest foreign aura in the area is copied to its neighbours.</summary>
        private void SpreadAuras(Vec2 pos, float radius, HeroUnit source)
        {
            List<EnemyUnit> c = RentList();
            QueryEnemies(pos, radius, c);
            Element spread = Element.None;
            float best = 0.2f;
            for (int i = 0; i < c.Count; i++)
            {
                for (int k = 1; k < ElementUtil.Count; k++)
                {
                    if (k == (int)Element.Wind) continue;
                    if (c[i].Aura[k] > best) { best = c[i].Aura[k]; spread = (Element)k; }
                }
            }
            if (spread != Element.None)
            {
                for (int i = 0; i < c.Count; i++)
                    if (c[i].Alive && !c[i].HasAura(spread)) ApplyElement(c[i], spread, 0.6f, source, 1);
            }
            else
            {
                for (int i = 0; i < c.Count; i++) ApplyElement(c[i], Element.Wind, 0.8f, source, 0);
            }
            ReturnList(c);
        }

        // ------------------------------------------------------------------ passives

        private void ApplyBattleStartPassive(HeroUnit h)
        {
            switch (h.PassiveKind)
            {
                case "tailwind":
                    for (int i = 0; i < Heroes.Count; i++)
                    {
                        HeroUnit a = Heroes[i];
                        if (a.Alive && FormationDistance(a, h) <= h.PassiveParams.Get("radius", 3.4f))
                            AddBuff(a, StatId.AttackInterval, h.PassiveParams.Get("haste", 0.12f), 99999f, "tailwind");
                    }
                    break;
                case "bulwark":
                    for (int i = 0; i < Heroes.Count; i++)
                    {
                        HeroUnit a = Heroes[i];
                        if (a.Alive && a != h && FormationDistance(a, h) <= h.PassiveParams.Get("radius", 2.8f))
                            AddBuff(a, StatId.Defense, h.PassiveParams.Get("defensePct", 0.3f), 99999f, "bulwark");
                    }
                    break;
            }
            ApplyBattleStartPassiveExt(h);
        }

        private void TickPassive(HeroUnit h, float dt)
        {
            if (h.PassiveKind == "heat_up" && h.PassiveStacks > 0)
            {
                h.PassiveTimer -= dt;
                if (h.PassiveTimer <= 0f)
                {
                    h.PassiveStacks = 0;
                    h.Buffs.RemoveAll(b => b.Source == "heat_up");
                }
            }
            if (h.PassiveKind == "living_fortress" && h.Alive)
                h.Hp = SimMath.Min(h.MaxHp, h.Hp + h.MaxHp * h.PassiveParams.Get("regen", 0.01f) * dt);
            TickPassiveExt(h, dt);
        }

        /// <summary>Conditional damage bonuses from passives (added to DamageRequest.BonusMult).</summary>
        public float PassiveBonus(HeroUnit h, EnemyUnit e)
        {
            if (e == null) return 0f;
            switch (h.PassiveKind)
            {
                case "kindling": return e.Burning ? h.PassiveParams.Get("bonus", 0.2f) : 0f;
                case "static": return e.HasAura(Element.Lightning) ? h.PassiveParams.Get("bonus", 0.2f) : 0f;
                case "keen_eye": return Vec2.Distance(h.Pos, e.Pos) > h.PassiveParams.Get("distance", 3.5f) ? h.PassiveParams.Get("bonus", 0.25f) : 0f;
                case "crushing": return e.ArmorCrackTimer > 0f ? h.PassiveParams.Get("bonus", 0.25f) * e.ArmorCrackStacks : 0f;
                case "shatter": return e.Frozen ? h.PassiveParams.Get("bonus", 1f) : 0f;
                case "inferno": return e.Burning ? h.PassiveParams.Get("bonus", 0.35f) : 0f;
                default: return PassiveBonusExt(h, e);
            }
        }

        private void OnBasicAttackPassive(HeroUnit h)
        {
            if (h.PassiveKind == "heat_up")
            {
                int max = (int)h.PassiveParams.Get("maxStacks", 5f);
                if (h.PassiveStacks < max) h.PassiveStacks++;
                h.PassiveTimer = 2.5f;
                h.Buffs.RemoveAll(b => b.Source == "heat_up");
                h.Buffs.Add(new TimedBuff { Stat = StatId.AttackInterval, Percent = h.PassiveStacks * h.PassiveParams.Get("perStack", 0.07f), Remaining = 2.5f, Source = "heat_up" });
            }
        }

        private void OnKillPassive(HeroUnit h, EnemyUnit victim)
        {
            if (h.PassiveKind == "momentum") h.SkillTimer *= 1f - h.PassiveParams.Get("refund", 0.5f);
        }

        private void OnHeroHit(HeroUnit h, EnemyUnit attacker)
        {
            if (!attacker.Alive) return;
            OnHeroHitExt(h, attacker);
            if (h.ShieldRetaliate > 0f && h.RetaliateTimer <= 0f)
            {
                h.RetaliateTimer = 0.4f;
                DealDamage(attacker, new DamageRequest { Source = h, Attack = h.ShieldRetaliate, Multiplier = 1f, Element = h.Def.Element, Gauge = 0.5f, Kind = DamageKind.Skill, Generation = 0 });
            }
            else if ((h.PassiveKind == "retaliate" || h.PassiveKind == "living_fortress") && h.RetaliateTimer <= 0f)
            {
                h.RetaliateTimer = h.PassiveParams.Get("cooldown", 0.8f);
                DealDamage(attacker, DamageRequest.From(h, h.PassiveParams.Get("mult", 0.5f), h.Def.Element, h.PassiveParams.Get("gauge", 0.5f), DamageKind.Skill));
            }
        }

        private void OnHeroShieldBroken(HeroUnit h)
        {
            float burst = h.Skill.Params.Get("shatterBurst");
            if (burst > 0f)
            {
                List<EnemyUnit> c = RentList();
                QueryEnemies(h.Pos, 2f, c);
                Emit(SimEventType.Strike, h.Pos, Element.Ice, 0f, h.Uid, 0, "shatter", false, 2f);
                for (int i = 0; i < c.Count; i++)
                    DealDamage(c[i], DamageRequest.From(h, burst, Element.Ice, 1f, DamageKind.Skill));
                ReturnList(c);
            }
            h.ShieldRetaliate = 0f;
        }
    }
}
