using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    /// <summary>Execution context for declarative actions (reaction resolution, field expiry, relics).</summary>
    public struct ActionContext
    {
        public ReactionDef Reaction;   // null outside reactions
        public string Tag;             // reaction/field id used for attribution
        public EnemyUnit Target;       // may be null (field expiry)
        public HeroUnit Source;
        public Element Incoming;
        public Element Existing;
        public Vec2 Pos;
        public int Generation;
        public float Radius;
        public float Duration;
        public float StatusScale;
        public float Power;            // attack snapshot used for non-reaction damage
        public int Consumed;           // stacks consumed by the last consume op (scales later ops)
    }

    public sealed partial class Battle
    {
        /// <summary>Extra reaction damage active while a reaction resolves (Resonant, rune circles).</summary>
        private float _activeReactionBonus;

        private void ExecuteActions(List<ActionOp> ops, ref ActionContext ctx)
        {
            for (int i = 0; i < ops.Count; i++) ExecuteAction(ops[i], ref ctx);
        }

        private void ExecuteAction(ActionOp op, ref ActionContext ctx)
        {
            ParamBag p = op.Params;
            Element el = op.Resolve(ctx.Incoming, ctx.Existing);
            float radius = p.Has("radius") ? p.Get("radius") : SimMath.Max(0.6f, ctx.Radius);
            List<EnemyUnit> q = RentList();
            CollectTargets(op, ref ctx, radius, q);
            switch (op.Op)
            {
                case "damage":
                {
                    float mult = op.Mult * (p.Has("perConsumed") ? System.Math.Max(1, ctx.Consumed) * p.Get("perConsumed") : 1f);
                    string bonusIf = p.GetString("bonusIf");
                    for (int i = 0; i < q.Count; i++)
                    {
                        EnemyUnit e = q[i];
                        DamageRequest d = ActionHit(ref ctx, el, mult);
                        if (bonusIf != null && HasStatus(e, bonusIf)) d.BonusMult += p.Get("bonus", 0.5f);
                        d.Gauge = p.Get("gauge");
                        DealDamage(e, d);
                    }
                    break;
                }
                case "status":
                    for (int i = 0; i < q.Count; i++) ApplyStatus(q[i], op.Status, p, ctx.StatusScale, ctx.Source, ctx.Generation);
                    break;
                case "apply":
                    for (int i = 0; i < q.Count; i++)
                        if (q[i].Alive) ApplyElement(q[i], el, p.Get("gauge", 0.8f), ctx.Source, ctx.Generation);
                    break;
                case "field":
                {
                    if (!Content.Fields.TryGetValue(op.Field, out FieldDef f)) break;
                    float dur = p.Has("duration") ? p.Get("duration") : SimMath.Max(1f, ctx.Duration);
                    float fr = p.Has("radius") ? p.Get("radius") : SimMath.Max(1f, ctx.Radius);
                    SpawnField(f, ctx.Pos, fr, dur, ctx.Source, ctx.Power * op.Mult, ctx.Generation, ctx.Tag, null);
                    break;
                }
                case "pull":
                    for (int i = 0; i < q.Count; i++) Pull(q[i], ctx.Pos, p.Get("strength", 3f) * ctx.StatusScale, p.Get("duration", 0.6f));
                    break;
                case "knock":
                    for (int i = 0; i < q.Count; i++)
                    {
                        Vec2 dir = (q[i].Pos - ctx.Pos).SqrLength > 1e-4f ? (q[i].Pos - ctx.Pos).Normalized : (q[i].Pos - Crystal.Pos).Normalized;
                        Knock(q[i], dir, p.Get("distance", 0.8f) * ctx.StatusScale);
                    }
                    break;
                case "chain":
                    if (ctx.Target != null && ctx.Target.Alive)
                        ChainGeneric(ctx.Target, ref ctx, (int)p.Get("bounces", 3f), p.Get("jump", 2.6f), op.Mult, el, p.GetString("requires"));
                    break;
                case "consume":
                {
                    int consumed = 0;
                    for (int i = 0; i < q.Count; i++) consumed += ConsumeStatus(q[i], op.Status, p.Get("fraction", 0.5f));
                    ctx.Consumed = consumed;
                    break;
                }
                case "hero_shield":
                {
                    float pct = p.Get("pct", 0.1f) * ctx.StatusScale;
                    HeroUnit src = ctx.Source;
                    ForHeroesNear(ctx.Pos, p.Get("heroRadius", 2.6f), p.Flag("nearest"), h => AddHeroShield(h, h.MaxHp * pct, src));
                    break;
                }
                case "hero_heal":
                {
                    float pct = p.Get("pct", 0.05f);
                    HeroUnit src = ctx.Source;
                    ForHeroesNear(ctx.Pos, p.Get("heroRadius", 2.6f), p.Flag("nearest"), h => HealHero(h, h.MaxHp * pct, src));
                    break;
                }
                case "hero_buff":
                {
                    StatId stat = ContentDatabase.ParseStat(p.GetString("stat", "attack_interval"));
                    string tag = ctx.Tag;
                    ForHeroesNear(ctx.Pos, p.Get("heroRadius", 3f), p.Flag("nearest"), h => AddBuff(h, stat, p.Get("pct", 0.15f), p.Get("duration", 4f), tag));
                    break;
                }
                case "crystal_shield":
                    ShieldCrystal(Crystal.MaxHp * p.Get("pct", 0.02f));
                    break;
                case "cleanse":
                    ForHeroesNear(ctx.Pos, p.Get("heroRadius", 2.6f), false, CleanseHero);
                    DetachNear(ctx.Pos, p.Get("heroRadius", 2.6f) + 1f);
                    break;
                case "refund":
                {
                    float sec = p.Get("seconds", 0.5f);
                    if (p.Flag("self")) { if (ctx.Source != null) ctx.Source.SkillTimer = SimMath.Max(0f, ctx.Source.SkillTimer - sec); }
                    else ForHeroesNear(ctx.Pos, p.Get("heroRadius", 3f), false, h => h.SkillTimer = SimMath.Max(0f, h.SkillTimer - sec));
                    break;
                }
                case "echo":
                {
                    HeroUnit h = ctx.Source;
                    if (h != null && h.Alive && h.EchoCooldown <= 0f && ctx.Generation <= MaxProcGeneration)
                    {
                        h.EchoCooldown = p.Get("cooldown", 2.5f);
                        CastSkill(h, op.Mult, true); // echo casts never fire skill_cast, so they cannot echo again
                    }
                    break;
                }
                case "suppress":
                    for (int i = 0; i < q.Count; i++) Seal(q[i], p.Get("duration", 2f) * ctx.StatusScale);
                    break;
                case "spread":
                {
                    int n = (int)p.Get("count", 2f);
                    string filter = p.GetString("filter");
                    for (int i = 0; i < q.Count && n > 0; i++)
                    {
                        EnemyUnit e = q[i];
                        if (e == ctx.Target || !e.Alive) continue;
                        if (filter != null && !HasStatus(e, filter)) continue;
                        ApplyStatus(e, op.Status, p, ctx.StatusScale, ctx.Source, ctx.Generation);
                        n--;
                    }
                    break;
                }
                case "delayed":
                {
                    float mult = op.Mult * (p.Has("perConsumed") ? System.Math.Max(1, ctx.Consumed) * p.Get("perConsumed") : 1f);
                    AddStrike(new DelayedStrike
                    {
                        Kind = StrikeKind.ReactionBurst,
                        Pos = ctx.Pos,
                        Delay = p.Get("delay", 1f),
                        Radius = radius,
                        Source = ctx.Source,
                        Element = el,
                        Power = ctx.Reaction != null ? ReactionPower(ctx.Reaction, ctx.Source) : ctx.Power,
                        Multiplier = mult,
                        Generation = ctx.Generation,
                        ReactionId = ctx.Reaction != null ? ctx.Reaction.Id : null,
                        SourceTag = ctx.Tag,
                        Status = p.GetString("status"),
                        StatusParams = p,
                        Stun = p.Get("stun")
                    });
                    break;
                }
                case "shards":
                {
                    int count = (int)p.Get("count", 3f);
                    float spread = p.Get("spread", 1.2f);
                    for (int i = 0; i < count; i++)
                    {
                        Vec2 off = Vec2.FromAngle(i * 6.2831853f / count + Rng.Range(0f, 0.5f)) * spread;
                        AddStrike(new DelayedStrike
                        {
                            Kind = StrikeKind.ReactionBurst,
                            Pos = ctx.Pos + off,
                            Delay = p.Get("delay", 0.35f) + i * 0.06f,
                            Radius = p.Get("shardRadius", 0.7f),
                            Source = ctx.Source,
                            Element = el,
                            Power = ctx.Reaction != null ? ReactionPower(ctx.Reaction, ctx.Source) : ctx.Power,
                            Multiplier = op.Mult,
                            Generation = ctx.Generation,
                            ReactionId = ctx.Reaction != null ? ctx.Reaction.Id : null,
                            SourceTag = ctx.Tag,
                            Status = p.GetString("status"),
                            StatusParams = p
                        });
                    }
                    break;
                }
                case "collapse":
                    Collapse(ctx.Pos, radius, ctx.Source, op.Mult * (p.Has("perConsumed") ? System.Math.Max(1, ctx.Consumed) * p.Get("perConsumed") : 1f), ctx.Generation, ctx.Tag);
                    break;
            }
            ReturnList(q);
        }

        /// <summary>Area ops hit everything in radius; single ops hit the reaction target only.</summary>
        private void CollectTargets(ActionOp op, ref ActionContext ctx, float radius, List<EnemyUnit> q)
        {
            if (op.Area || ctx.Target == null || op.Op == "spread")
            {
                QueryEnemies(ctx.Pos, radius, q);
                // Deterministic order for capped ops (spread): nearest first, uid tie-break.
                Vec2 pos = ctx.Pos;
                q.Sort((a, b) =>
                {
                    int d = Vec2.SqrDistance(a.Pos, pos).CompareTo(Vec2.SqrDistance(b.Pos, pos));
                    return d != 0 ? d : a.Uid.CompareTo(b.Uid);
                });
            }
            else if (ctx.Target.Alive) q.Add(ctx.Target);
        }

        private DamageRequest ActionHit(ref ActionContext ctx, Element el, float mult)
        {
            if (ctx.Reaction != null) return ReactionHit(ctx.Reaction, ctx.Source, el, mult, ctx.Generation);
            return new DamageRequest
            {
                Source = ctx.Source,
                Attack = ctx.Power,
                Multiplier = mult,
                Element = el,
                Kind = DamageKind.Trigger,
                Generation = ctx.Generation,
                SourceTag = ctx.Tag
            };
        }

        private void ForHeroesNear(Vec2 pos, float radius, bool nearestIfNone, System.Action<HeroUnit> action)
        {
            bool any = false;
            for (int i = 0; i < Heroes.Count; i++)
            {
                HeroUnit h = Heroes[i];
                if (!h.Alive || Vec2.Distance(h.Pos, pos) > radius + h.Radius) continue;
                action(h);
                any = true;
            }
            if (any || !nearestIfNone) return;
            HeroUnit best = null;
            float bestD = float.MaxValue;
            for (int i = 0; i < Heroes.Count; i++)
            {
                HeroUnit h = Heroes[i];
                if (!h.Alive) continue;
                float d = Vec2.SqrDistance(h.Pos, pos);
                if (d < bestD) { bestD = d; best = h; }
            }
            if (best != null) action(best);
        }

        public void CleanseHero(HeroUnit h)
        {
            if (h.SilenceTimer > 0f || h.LeechTimer > 0f || h.FeverTimer > 0f)
                Emit(SimEventType.StatusApplied, h.Pos, Element.Light, 0f, 0, h.Uid, "cleanse");
            h.SilenceTimer = 0f;
            h.LeechTimer = 0f;
            h.LeechAmount = 0f;
            h.FeverTimer = 0f;
        }

        public bool HasStatus(EnemyUnit e, string status)
        {
            switch (status)
            {
                case "illuminated": return e.IlluminatedTimer > 0f;
                case "doomed": return e.DoomStacks > 0;
                case "rooted": return e.RootTimer > 0f;
                case "poisoned": return e.PoisonStacks > 0;
                case "corroded": return e.Corroded;
                case "resonant": return e.ResonantTimer > 0f;
                case "unstable": return e.UnstableStacks > 0;
                case "frozen": return e.Frozen;
                case "chilled": return e.Chilled;
                case "burning": return e.Burning;
                case "wet": return e.Wet;
                case "marked": return e.MarkStacks > 0;
                case "elite": return e.Elite || e.IsBoss;
                default: return false;
            }
        }

        /// <summary>Removes a fraction of a stacking status and returns how many stacks were consumed.</summary>
        private int ConsumeStatus(EnemyUnit e, string status, float fraction)
        {
            int n;
            switch (status)
            {
                case "poison":
                    if (e.PoisonStacks <= 0) return 0;
                    n = System.Math.Max(1, (int)(e.PoisonStacks * fraction));
                    e.PoisonStacks -= n;
                    return n;
                case "doom":
                    if (e.DoomStacks <= 0) return 0;
                    n = System.Math.Max(1, (int)(e.DoomStacks * fraction));
                    e.DoomStacks -= n;
                    return n;
                case "mark":
                    if (e.MarkStacks <= 0) return 0;
                    n = System.Math.Max(1, (int)(e.MarkStacks * fraction));
                    e.MarkStacks -= n;
                    return n;
                case "freeze":
                    if (!e.Frozen) return 0;
                    e.Frozen = false;
                    e.StunTimer = SimMath.Min(e.StunTimer, 0.05f);
                    return 1;
                default:
                    return 0;
            }
        }

        /// <summary>Bounded chain between enemies (optionally only those carrying a status).</summary>
        private void ChainGeneric(EnemyUnit from, ref ActionContext ctx, int bounces, float jump, float mult, Element el, string requires)
        {
            EnemyUnit current = from;
            var hit = HitSetPool.Rent();
            List<EnemyUnit> q = RentList();
            hit.Add(from.Uid);
            for (int b = 0; b < bounces; b++)
            {
                QueryEnemies(current.Pos, jump, q);
                EnemyUnit next = null;
                float bestD = float.MaxValue;
                for (int i = 0; i < q.Count; i++)
                {
                    EnemyUnit e = q[i];
                    if (hit.Contains(e.Uid) || !e.Alive) continue;
                    if (requires != null && !HasStatus(e, requires)) continue;
                    float d = Vec2.SqrDistance(current.Pos, e.Pos);
                    if (d < bestD || (d == bestD && next != null && e.Uid < next.Uid)) { bestD = d; next = e; }
                }
                if (next == null) break;
                hit.Add(next.Uid);
                Emit(SimEventType.Strike, next.Pos, el, 0f, ctx.Source?.Uid ?? 0, next.Uid, "chain", false, 0f, ctx.Generation);
                Journal.Pending[Journal.Pending.Count - 1] = WithFrom(Journal.Pending[Journal.Pending.Count - 1], current.Pos);
                DealDamage(next, ActionHit(ref ctx, el, mult));
                current = next;
            }
            HitSetPool.Return(hit);
            ReturnList(q);
        }

        // ------------------------------------------------------------------ fields

        public Zone SpawnField(FieldDef f, Vec2 pos, float radius, float duration, HeroUnit owner, float power, int gen, string tag, Vec2? end)
        {
            int same = 0;
            for (int i = 0; i < Zones.Count; i++) if (Zones[i].Field == f) same++;
            if (same >= f.MaxCount)
            {
                for (int i = 0; i < Zones.Count; i++)
                {
                    if (Zones[i].Field != f) continue;
                    Zones.RemoveAt(i);
                    break;
                }
            }
            // Skill/relic fields (not reaction zones) last longer with "field_duration" (e.g. Mason's Level).
            if (owner != null && (tag == null || !Content.Reactions.ContainsKey(tag))) duration *= 1f + Mods.Rule("field_duration");
            var z = new Zone
            {
                Uid = _nextFxUid++,
                Kind = ZoneKind.Field,
                Field = f,
                Pos = pos,
                End = end ?? pos,
                Line = f.Shape == "line" && end.HasValue,
                Radius = radius,
                BaseRadius = radius,
                Remaining = duration,
                Duration = duration,
                Power = power,
                Element = f.Element,
                Owner = owner,
                Generation = gen,
                ReactionId = f.DamageAsReaction ? tag : null,
                Tag = tag,
                TickTimer = 0.05f
            };
            Zones.Add(z);
            Emit(SimEventType.ZoneSpawn, pos, f.Element, duration, owner?.Uid ?? 0, z.Uid, f.Id, false, radius, gen);
            if (z.Line)
            {
                Journal.Pending[Journal.Pending.Count - 1] = WithFrom(Journal.Pending[Journal.Pending.Count - 1], z.End);
            }
            return z;
        }

        public bool InsideField(Zone z, Vec2 p, float extra)
        {
            if (z.Line) return Vec2.DistanceToSegment(p, z.Pos, z.End) <= z.Radius + extra;
            return Vec2.Distance(p, z.Pos) <= z.Radius + extra;
        }

        private void UpdateField(Zone z, float dt, bool tick, List<EnemyUnit> inside)
        {
            FieldDef f = z.Field;
            if (f.Grow > 0f) z.Radius = SimMath.Min(z.BaseRadius * f.MaxRadiusMult, z.Radius + f.Grow * dt);
            Vec2 center = z.Line ? Vec2.Lerp(z.Pos, z.End, 0.5f) : z.Pos;
            float queryR = z.Line ? Vec2.Distance(z.Pos, z.End) * 0.5f + z.Radius : z.Radius;
            QueryEnemies(center, queryR, inside);
            for (int i = inside.Count - 1; i >= 0; i--)
                if (!InsideField(z, inside[i].Pos, inside[i].Radius * 0.5f)) inside.RemoveAt(i);

            for (int i = 0; i < inside.Count; i++)
            {
                EnemyUnit e = inside[i];
                bool ignores = e.Def.Params.Flag("ignoreFields");
                if (f.Slow > 0f && !ignores) Slow(e, f.Slow, 0.3f);
                if (f.Pull > 0f && !ignores) Pull(e, z.Pos, f.Pull, 0.15f);
                if (f.EnemyVuln > 0f || f.EnemyWeaken > 0f || f.ReactionAmp > 0f)
                {
                    e.FieldTimer = 0.25f;
                    e.FieldVuln = SimMath.Max(e.FieldVuln, f.EnemyVuln);
                    e.FieldWeaken = SimMath.Max(e.FieldWeaken, f.EnemyWeaken);
                    e.FieldReactionAmp = SimMath.Max(e.FieldReactionAmp, f.ReactionAmp);
                }
            }

            for (int i = 0; i < Heroes.Count; i++)
            {
                HeroUnit h = Heroes[i];
                if (!h.Alive || !InsideField(z, h.Pos, h.Radius + 0.3f)) continue;
                if (f.HeroDamageReduction > 0f || f.HeroHaste > 0f)
                {
                    h.FieldTimer = 0.25f;
                    h.FieldDamageReduction = SimMath.Max(h.FieldDamageReduction, f.HeroDamageReduction);
                    h.FieldHaste = SimMath.Max(h.FieldHaste, f.HeroHaste);
                }
                if (tick)
                {
                    if (f.HeroHealPct > 0f) HealHero(h, h.MaxHp * f.HeroHealPct, z.Owner);
                    if (f.Cleanse) CleanseHero(h);
                }
            }

            if (!tick) return;
            z.TickTimer = f.Tick;
            UpdateFieldLinks(z);
            var ctx = new ActionContext
            {
                Tag = z.Tag,
                Source = z.Owner,
                Pos = z.Pos,
                Generation = System.Math.Max(1, z.Generation),
                Radius = z.Radius,
                StatusScale = 1f,
                Power = z.Power,
                Incoming = f.Element,
                Existing = f.Element
            };
            float regen = f.Params.Get("enemyRegen");
            for (int i = 0; i < inside.Count; i++)
            {
                EnemyUnit e = inside[i];
                if (regen > 0f && e.Alive) e.Hp = SimMath.Min(e.MaxHp, e.Hp + e.MaxHp * regen);
                if (f.DamageMult > 0f)
                {
                    DealDamage(e, new DamageRequest
                    {
                        Source = z.Owner,
                        Attack = z.Power,
                        Multiplier = f.DamageMult,
                        Element = f.Element,
                        Kind = z.ReactionId != null ? DamageKind.Reaction : DamageKind.Dot,
                        Generation = System.Math.Max(1, z.Generation),
                        ReactionId = z.ReactionId,
                        SourceTag = z.ReactionId == null ? z.Tag : null
                    });
                }
                if (!e.Alive || f.OnTick.Count == 0) continue;
                ctx.Target = e;
                ctx.Pos = e.Pos;
                for (int k = 0; k < f.OnTick.Count; k++)
                {
                    ActionOp op = f.OnTick[k];
                    if (op.Op == "status") ApplyStatus(e, op.Status, op.Params, 1f, z.Owner, ctx.Generation);
                    else if (op.Op == "apply") ApplyElement(e, op.Resolve(f.Element, f.Element), op.Params.Get("gauge", 0.5f), z.Owner, ctx.Generation);
                }
            }
            if (f.Zap > 0f && inside.Count > 0)
            {
                EnemyUnit e = inside[Rng.Range(0, inside.Count)];
                Emit(SimEventType.Strike, e.Pos, f.Element, 0f, z.Owner?.Uid ?? 0, e.Uid, "zap", false, 0.3f, z.Generation);
                Journal.Pending[Journal.Pending.Count - 1] = WithFrom(Journal.Pending[Journal.Pending.Count - 1], z.Pos);
                DealDamage(e, new DamageRequest
                {
                    Source = z.Owner,
                    Attack = z.Power,
                    Multiplier = f.Zap,
                    Element = f.Element,
                    Gauge = f.Params.Get("zapGauge", 0.5f),
                    Kind = DamageKind.Skill,
                    Generation = System.Math.Max(1, z.Generation),
                    SourceTag = z.Tag
                });
                if (z.Owner != null && f.Params.Get("zapRefund") > 0f)
                    for (int i = 0; i < Heroes.Count; i++)
                        if (Heroes[i].Alive && Heroes[i] != z.Owner && Vec2.Distance(Heroes[i].Pos, z.Pos) <= f.Params.Get("refundRadius", 2.5f))
                            Heroes[i].SkillTimer = SimMath.Max(0f, Heroes[i].SkillTimer - f.Params.Get("zapRefund"));
            }
            if (f.CrystalShieldPct > 0f && InsideField(z, Crystal.Pos, Crystal.Radius)) ShieldCrystal(Crystal.MaxHp * f.CrystalShieldPct);
        }

        private void ExpireField(Zone z)
        {
            FieldDef f = z.Field;
            if (f.OnEnd.Count == 0) return;
            var ctx = new ActionContext
            {
                Tag = z.Tag,
                Source = z.Owner,
                Pos = z.Line ? Vec2.Lerp(z.Pos, z.End, 0.5f) : z.Pos,
                Generation = System.Math.Max(1, z.Generation),
                Radius = z.Radius,
                Duration = z.Duration,
                StatusScale = 1f,
                Power = z.Power,
                Incoming = f.Element,
                Existing = f.Element
            };
            ExecuteActions(f.OnEnd, ref ctx);
        }
    }
}
