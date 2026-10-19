using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    /// <summary>
    /// Phase 2 enemy mechanics (all param-driven): sprints, plates, flying, burrowing, channelled heals,
    /// silences, siege artillery, soul links, stoking, phasing, statues; bosses Seraphyne and Gravemaw.
    /// </summary>
    public sealed partial class Battle
    {
        /// <summary>Per-tick behaviour hooks for expansion enemies (called before movement).</summary>
        private void UpdateEnemyMechanics(EnemyUnit e, float dt)
        {
            ParamBag p = e.Def.Params;
            if (p.Has("sprintEvery"))
            {
                if (e.SprintTimer > 0f) e.SprintTimer -= dt;
                e.Timer2 -= dt;
                if (e.Timer2 <= 0f && !e.Stunned && !e.Rooted)
                {
                    e.Timer2 = p.Get("sprintEvery", 4f);
                    e.SprintTimer = p.Get("sprintDuration", 1.2f);
                    Emit(SimEventType.StatusApplied, e.Pos, Element.None, 0f, e.Uid, e.Uid, "sprint");
                }
            }
            UpdateEnemyMechanicsP4(e, dt);
            if (e.Burrowed) UpdateBurrow(e, dt);
            if (e.SealTimer > 0f) return;
            if (p.Has("healEvery")) UpdatePriest(e, dt);
            if (p.Has("silenceEvery")) UpdateHexBinder(e, dt);
            if (p.Has("linkRadius")) UpdateSoulLinks(e, dt);
        }

        private void InitEnemyMechanics(EnemyUnit e)
        {
            ParamBag p = e.Def.Params;
            if (p.Flag("burrow"))
            {
                e.Burrowed = true;
                Emit(SimEventType.StatusApplied, e.Pos, Element.Earth, 0f, e.Uid, e.Uid, "burrowed");
            }
            if (p.Has("sprintEvery")) e.Timer2 = p.Get("sprintEvery", 4f) * Rng.Range(0.4f, 1f);
            if (p.Has("silenceEvery")) e.Timer2 = p.Get("silenceEvery", 6f) * 0.5f;
            if (p.Has("chaosCycle")) e.ChaosElement = ElementUtil.All[Rng.Range(0, ElementUtil.All.Length)];
            if (p.GetString("boss") == "generic")
            {
                e.BossTimers[TMark] = p.Get("markInterval") * 0.6f;
                e.BossTimers[TSummon] = p.Get("summonInterval") * 0.5f;
                e.BossTimers[TVolley] = p.Get("volleyInterval") * 0.7f;
                e.BossTimers[TExpose] = p.Get("exposeEvery", 999f);
            }
            if (p.Has("healEvery")) e.SpecialTimer = p.Get("healEvery", 3f) * 0.5f;
            if (p.Has("linkRadius")) e.SpecialTimer = 0f;
        }

        public bool IsFlying(EnemyUnit e) => e.Def.Params.Flag("flying");

        /// <summary>Speed multiplier from expansion mechanics (sprints, stoking).</summary>
        private float MechanicSpeed(EnemyUnit e)
        {
            float m = 1f + e.Stoke;
            if (e.SprintTimer > 0f) m *= e.Def.Params.Get("sprintMult", 1.9f);
            if (e.Burrowed && e.SurfaceTimer > 0f) m = 0f; // surfacing: holds still during the telegraph
            return m;
        }

        // ------------------------------------------------------------------ damage hooks

        /// <summary>Damage multiplier from defensive mechanics of the target (plates, phasing, statues, links).</summary>
        private float MechanicDamageTaken(EnemyUnit target, DamageRequest req)
        {
            ParamBag p = target.Def.Params;
            float m = 1f;
            float plated = p.Get("plated");
            if (plated > 0f && req.Kind == DamageKind.Basic && target.ArmorCrackTimer <= 0f && !target.Corroded) m *= 1f - plated;
            float phasing = p.Get("phasing");
            if (phasing > 0f && target.IlluminatedTimer <= 0f) m *= 1f - phasing;
            if (IsFlying(target) && req.Kind == DamageKind.Basic && req.Source != null && req.Source.Melee) m *= 0.5f;
            float guard = p.Get("statueGuard");
            if (guard > 0f && _statuesAlive > 0) m *= 1f - guard;
            return m;
        }

        /// <summary>Soul Link: a share of the damage a linked enemy takes is redirected to its binder.</summary>
        private float RedirectLinkedDamage(EnemyUnit target, float raw)
        {
            EnemyUnit binder = target.LinkedTo;
            if (binder == null || !binder.Alive || binder == target) return raw;
            float share = raw * binder.Def.Params.Get("linkShare", 0.4f);
            binder.Hp -= share;
            binder.HitFlash = 0.12f;
            if (binder.Hp <= 0f) KillEnemy(binder, null);
            return raw - share;
        }

        private void OnMechanicHit(EnemyUnit target, DamageRequest req)
        {
            ParamBag p = target.Def.Params;
            string stoke = p.GetString("stokeElement");
            if (stoke != null && req.Element != Element.None && ElementUtil.Key(req.Element) == stoke)
                target.Stoke = SimMath.Min(p.Get("stokeMax", 0.3f), target.Stoke + p.Get("stokePerHit", 0.03f));
        }

        private void OnMechanicDeath(EnemyUnit e)
        {
            string field = e.Def.Params.GetString("deathField");
            if (field != null && Content.Fields.TryGetValue(field, out FieldDef f)) SpawnField(f, e.Pos, 1.6f, 4f, null, 0f, 0, "death_" + e.Def.Id, null);
            OnEnemyDeathNature(e);
            if (e.Def.Params.Flag("statue")) _statuesAlive = System.Math.Max(0, _statuesAlive - 1);
            for (int i = 0; i < Enemies.Count; i++) if (Enemies[i].LinkedTo == e) Enemies[i].LinkedTo = null;
            // A guarded boss's statues shatter with her, so an out-of-reach statue can never stall the wave.
            if (e.Def.Params.Has("statueGuard"))
                for (int i = 0; i < Enemies.Count; i++)
                    if (Enemies[i].Alive && Enemies[i].Def.Params.Flag("statue")) KillEnemy(Enemies[i], null);
        }

        // ------------------------------------------------------------------ behaviours

        private void UpdateBurrow(EnemyUnit e, float dt)
        {
            if (e.SurfaceTimer > 0f)
            {
                e.SurfaceTimer -= dt;
                if (e.SurfaceTimer <= 0f)
                {
                    e.Burrowed = false;
                    Emit(SimEventType.Strike, e.Pos, Element.Earth, 0f, e.Uid, 0, "surface", false, 1.1f);
                }
                return;
            }
            if (RemainingPath(e) <= e.Def.Params.Get("surfaceDist", 3.2f) || Vec2.Distance(e.Pos, Crystal.Pos) <= Crystal.Radius + e.Def.Params.Get("surfaceDist", 3.2f))
            {
                e.SurfaceTimer = e.Def.Params.Get("surfaceDelay", 1.2f);
                Emit(SimEventType.Telegraph, e.Pos, Element.Earth, e.SurfaceTimer, e.Uid, 0, "surface", false, 1.1f);
            }
        }

        private void UpdatePriest(EnemyUnit e, float dt)
        {
            ParamBag p = e.Def.Params;
            if (e.ChannelTimer > 0f)
            {
                if (e.Stunned)
                {
                    e.ChannelTimer = 0f; // interrupted
                    e.SpecialTimer = p.Get("healEvery", 3f) * 0.5f;
                    Emit(SimEventType.Miss, e.Pos, Element.None, 0f, 0, e.Uid, "interrupted");
                    return;
                }
                e.ChannelTimer -= dt;
                if (e.ChannelTimer > 0f) return;
                List<EnemyUnit> c = RentList();
                float r = p.Get("healRadius", 2.6f);
                QueryEnemies(e.Pos, r, c);
                Emit(SimEventType.Strike, e.Pos, Element.Void, 0f, e.Uid, 0, "enemy_heal", false, r);
                for (int i = 0; i < c.Count; i++)
                {
                    EnemyUnit a = c[i];
                    if (!a.Alive) continue;
                    a.Hp = SimMath.Min(a.MaxHp, a.Hp + a.MaxHp * p.Get("healPct", 0.06f));
                }
                ReturnList(c);
                return;
            }
            e.SpecialTimer -= dt;
            if (e.SpecialTimer > 0f || e.Stunned) return;
            e.SpecialTimer = p.Get("healEvery", 3f);
            e.ChannelTimer = p.Get("channel", 0.8f);
            Emit(SimEventType.Telegraph, e.Pos, Element.Void, e.ChannelTimer, e.Uid, 0, "channel_heal", false, p.Get("healRadius", 2.6f));
        }

        private void UpdateHexBinder(EnemyUnit e, float dt)
        {
            e.Timer2 -= dt;
            if (e.Timer2 > 0f || e.Stunned) return;
            e.Timer2 = e.Def.Params.Get("silenceEvery", 6f);
            HeroUnit best = null;
            float bestD = e.Def.AttackRange + 1.5f;
            for (int i = 0; i < Heroes.Count; i++)
            {
                HeroUnit h = Heroes[i];
                if (!h.Alive) continue;
                float d = Vec2.Distance(h.Pos, e.Pos);
                if (d < bestD) { bestD = d; best = h; }
            }
            if (best == null || ImmuneToDebuffs(best)) return;
            best.SilenceTimer = SimMath.Max(best.SilenceTimer, e.Def.Params.Get("silenceDuration", 2.5f));
            Emit(SimEventType.StatusApplied, best.Pos, Element.Arcane, 0f, e.Uid, best.Uid, "silenced");
        }

        private void UpdateSoulLinks(EnemyUnit e, float dt)
        {
            e.SpecialTimer -= dt;
            if (e.SpecialTimer > 0f) return;
            e.SpecialTimer = 0.5f;
            List<EnemyUnit> c = RentList();
            QueryEnemies(e.Pos, e.Def.Params.Get("linkRadius", 3f), c);
            c.Sort((a, b) =>
            {
                int d = Vec2.SqrDistance(a.Pos, e.Pos).CompareTo(Vec2.SqrDistance(b.Pos, e.Pos));
                return d != 0 ? d : a.Uid.CompareTo(b.Uid);
            });
            int n = 0, max = (int)e.Def.Params.Get("linkCount", 3f);
            for (int i = 0; i < c.Count; i++)
            {
                EnemyUnit a = c[i];
                if (a == e || !a.Alive || a.IsBoss || a.Def.Params.Has("linkRadius")) continue;
                if (n < max && (a.LinkedTo == null || a.LinkedTo == e || !a.LinkedTo.Alive)) { a.LinkedTo = e; n++; }
            }
            ReturnList(c);
        }

        /// <summary>Siege enemies stop at range and shell the crystal (telegraphed). Returns true when sieging.</summary>
        private bool UpdateSiege(EnemyUnit e, float dt)
        {
            ParamBag p = e.Def.Params;
            float range = p.Get("siegeRange");
            if (range <= 0f || Vec2.Distance(e.Pos, Crystal.Pos) > range + Crystal.Radius) return false;
            e.Facing = (Crystal.Pos - e.Pos).Normalized;
            e.StuckTimer = 0f;
            e.SpecialTimer -= dt;
            if (e.SpecialTimer > 0f || e.SealTimer > 0f) return true;
            e.SpecialTimer = p.Get("shellEvery", 4.5f);
            Vec2 off = Vec2.FromAngle(Rng.Range(0f, 6.283f)) * 0.3f;
            AddStrike(new DelayedStrike
            {
                Kind = StrikeKind.BossSlam,
                Pos = Crystal.Pos + off,
                Delay = p.Get("shellDelay", 1.6f),
                Radius = p.Get("shellRadius", 1f),
                EnemySource = e,
                Power = e.CrystalDamage * 2f * p.Get("shellMult", 1f), // the crystal takes half of a slam
                Element = Element.Earth
            });
            return true;
        }

        // ------------------------------------------------------------------ bosses

        private int _statuesAlive;

        /// <summary>
        /// Seraphyne: frost marks freeze heroes standing in them (telegraphed); at 60% she raises two
        /// destructible statues that guard her; below 45% a blizzard slows the attacks of nearby heroes.
        /// </summary>
        private void UpdateSeraphyne(EnemyUnit e, float dt)
        {
            ParamBag p = e.Def.Params;
            if (e.Phase == 0 && e.HpFraction <= p.Get("statueAt", 0.6f))
            {
                e.Phase = 1;
                if (Content.Enemies.TryGetValue("ice_statue", out EnemyDef statue))
                {
                    Vec2 side = new Vec2(-e.Facing.Y, e.Facing.X);
                    for (int i = 0; i < (int)p.Get("statueCount", 2f); i++)
                    {
                        EnemyUnit s = SpawnEnemy(statue, e.Lane, false, null, e.Pos + side * (i == 0 ? 1.6f : -1.6f));
                        s.Speed = 0f;
                        _statuesAlive++;
                    }
                }
                Emit(SimEventType.BossPhase, e.Pos, Element.Ice, 1f, e.Uid, 0, "seraphyne_statues", false, 2f);
            }
            if (e.Phase == 1 && e.HpFraction <= p.Get("blizzardAt", 0.45f))
            {
                e.Phase = 2;
                Emit(SimEventType.BossPhase, e.Pos, Element.Ice, 2f, e.Uid, 0, "seraphyne_blizzard", false, 3f);
            }
            if (e.Phase == 2)
            {
                float r = p.Get("blizzardRadius", 3.2f);
                for (int i = 0; i < Heroes.Count; i++)
                {
                    HeroUnit h = Heroes[i];
                    if (!h.Alive || Vec2.Distance(h.Pos, e.Pos) > r + h.Radius) continue;
                    h.ChillTimer = 0.4f;
                    h.ChillAmount = p.Get("blizzardSlow", 0.3f);
                }
            }
            if (e.SealTimer > 0f || e.Stunned) return;
            e.SpecialTimer -= dt;
            if (e.SpecialTimer > 0f) return;
            e.SpecialTimer = p.Get("markInterval", 8f);
            int placed = 0;
            for (int i = 0; i < Heroes.Count && placed < (int)p.Get("markCount", 2f); i++)
            {
                HeroUnit h = Heroes[(i + TickCount) % Heroes.Count];
                if (!h.Alive) continue;
                AddStrike(new DelayedStrike
                {
                    Kind = StrikeKind.BossSlam,
                    Pos = h.Pos,
                    Delay = p.Get("markDelay", 1.8f),
                    Radius = p.Get("markRadius", 1.1f),
                    EnemySource = e,
                    Power = e.Attack * p.Get("markMult", 0.8f),
                    Element = Element.Ice,
                    HeroStun = p.Get("markStun", 1f)
                });
                placed++;
            }
        }

        /// <summary>
        /// Gravemaw: slow armoured titan. Shells the area around the crystal, then vents its armour
        /// (Exposed). At half HP it breaches forward along its lane after a telegraph.
        /// </summary>
        private void UpdateGravemaw(EnemyUnit e, float dt)
        {
            ParamBag p = e.Def.Params;
            if (e.PhaseTimer > 0f)
            {
                e.PhaseTimer -= dt;
                if (e.PhaseTimer <= 0f) e.Defense += p.Get("ventArmor", 60f);
            }
            if (e.Timer2 > 0f)
            {
                e.Timer2 -= dt;
                if (e.Timer2 <= 0f)
                {
                    // vent after the volley lands: the counter window
                    e.Defense -= p.Get("ventArmor", 60f);
                    e.PhaseTimer = p.Get("ventDuration", 4f);
                    Emit(SimEventType.BossPhase, e.Pos, Element.Earth, 2f, e.Uid, 0, "gravemaw_exposed", false, 2f);
                }
            }
            if (e.Phase == 0 && e.HpFraction <= p.Get("breachAt", 0.5f))
            {
                e.Phase = 1;
                LaneDef lane = Arena.Lanes[e.Lane];
                Vec2 target = e.Waypoint < lane.Points.Count ? lane.Points[e.Waypoint] : Crystal.Pos;
                Vec2 dest = Vec2.MoveTowards(e.Pos, target, p.Get("breachDistance", 3f));
                Emit(SimEventType.BossPhase, e.Pos, Element.Earth, 1f, e.Uid, 0, "gravemaw_breach", false, 2f);
                AddStrike(new DelayedStrike { Kind = StrikeKind.BossSlam, Pos = Vec2.Lerp(e.Pos, dest, 0.5f), Delay = 1.4f, Radius = 1.4f, EnemySource = e, Power = e.Attack * p.Get("breachMult", 2f), Element = Element.Earth });
                AddStrike(new DelayedStrike { Kind = StrikeKind.BossSlam, Pos = dest, Delay = 1.6f, Radius = 1.4f, EnemySource = e, Power = e.Attack * p.Get("breachMult", 2f), Element = Element.Earth });
                e.TelegraphTimer = 1.5f;
                e.TelegraphPos = dest;
                e.TelegraphKind = 7;
            }
            if (e.TelegraphTimer > 0f && e.TelegraphKind == 7)
            {
                e.TelegraphTimer -= dt;
                if (e.TelegraphTimer <= 0f) e.Pos = e.TelegraphPos;
                return;
            }
            if (e.SealTimer > 0f || e.Stunned) return;
            e.SpecialTimer -= dt;
            if (e.SpecialTimer > 0f) return;
            e.SpecialTimer = p.Get("volleyInterval", 10f);
            float delay = p.Get("volleyDelay", 1.8f);
            for (int k = 0; k < (int)p.Get("volleyCount", 3f); k++)
            {
                Vec2 pos = Crystal.Pos + Vec2.FromAngle(k * 2.094f + Rng.Range(0f, 0.6f)) * 2.3f;
                AddStrike(new DelayedStrike { Kind = StrikeKind.BossSlam, Pos = pos, Delay = delay + k * 0.25f, Radius = p.Get("volleyRadius", 1.2f), EnemySource = e, Power = e.Attack * p.Get("volleyMult", 1.4f), Element = Element.Earth });
            }
            e.Timer2 = delay + 0.9f;
        }
    }
}
