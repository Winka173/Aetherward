using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    public sealed partial class Battle
    {
        private const float AuraDecayPerSecond = 0.4f;

        private void UpdateEnemy(EnemyUnit e, float dt)
        {
            if (!e.Alive) return;
            UpdateEnemyStatuses(e, dt);
            if (!e.Alive) return;

            // Forced displacement applies even while stunned.
            if (e.KnockbackTimer > 0f)
            {
                e.KnockbackTimer -= dt;
                e.Pos += e.Knockback * dt;
                ClampToArena(e);
            }
            if (e.PullTimer > 0f)
            {
                e.PullTimer -= dt;
                if (Vec2.Distance(e.Pos, e.PullTarget) > 0.3f) e.Pos = Vec2.MoveTowards(e.Pos, e.PullTarget, e.PullStrength * dt);
            }
            if (e.Invulnerable > 0f) e.Invulnerable -= dt;

            if (e.IsBoss && Setup.BossEnrage > 0f && !e.Enraged && e.HpFraction <= 0.25f)
            {
                // Ascension 5: a telegraphed last-quarter enrage (never invulnerable, never instant crystal damage).
                e.Enraged = true;
                e.Attack *= 1f + Setup.BossEnrage;
                e.Speed *= 1f + Setup.BossEnrage * 0.6f;
                Emit(SimEventType.BossPhase, e.Pos, Element.None, 3f, e.Uid, 0, "boss_enrage", false, 2f);
            }
            if (e.Def.Params.GetString("boss") != null) UpdateBoss(e, dt);
            if (!e.Alive) return;

            if (e.StunTimer > 0f)
            {
                e.StunTimer -= dt;
                if (e.StunTimer <= 0f) e.Frozen = false;
                return;
            }
            if (e.TelegraphTimer > 0f) return; // channelling a telegraphed attack (bosses, elites)

            e.AttackTimer -= dt;
            float speed = e.Speed * (1f - (e.SlowTimer > 0f ? e.SlowAmount : 0f)) * (1f + e.SpeedBuff);
            if (e.Chilled) speed *= 0.85f;
            if (e.RootTimer > 0f) speed = 0f; // rooted: holds position but can still attack in reach
            EnemyBehavior b = e.Def.Behavior;

            if (e.SealTimer <= 0f)
            {
                if (b == EnemyBehavior.Summoner) UpdateSummoner(e, dt);
                if (b == EnemyBehavior.Buffer) UpdateBuffer(e, dt);
            }

            // Taunt overrides normal targeting (sappers are immune, see Taunt()).
            if (e.TauntTimer > 0f)
            {
                e.TauntTimer -= dt;
                if (e.Taunter != null && e.Taunter.Alive)
                {
                    EngageHero(e, e.Taunter, speed, dt);
                    return;
                }
                e.Taunter = null;
            }

            if (b == EnemyBehavior.Ranged && UpdateRanged(e, speed, dt)) return;

            if (b != EnemyBehavior.Sapper && b != EnemyBehavior.Runner && b != EnemyBehavior.Ranged)
            {
                if (e.Engaged != null && (!e.Engaged.Alive || Vec2.Distance(e.Pos, e.Engaged.Pos) > EngageRadius(e, e.Engaged) + 1.2f))
                    e.Engaged = null;
                if (e.Engaged == null && ((TickCount + e.Uid) % 6 == 0)) e.Engaged = FindHeroToEngage(e);
                if (e.Engaged != null)
                {
                    EngageHero(e, e.Engaged, speed, dt);
                    return;
                }
            }
            else if (b == EnemyBehavior.Runner)
            {
                // Runners only fight when physically body-blocked by a hero.
                HeroUnit blocker = FindHeroWithin(e, e.Radius + 0.45f);
                if (blocker != null)
                {
                    EngageHero(e, blocker, speed, dt);
                    return;
                }
            }

            AdvanceOrAttackCrystal(e, speed, dt);
        }

        private void UpdateEnemyStatuses(EnemyUnit e, float dt)
        {
            if (e.HitFlash > 0f) e.HitFlash -= dt;
            for (int i = 1; i < ElementUtil.Count; i++)
            {
                if (e.Aura[i] <= 0f) continue;
                e.Aura[i] -= AuraDecayPerSecond * dt * (i == (int)Element.Ice && e.Frozen ? 0.2f : 1f);
                if (e.Aura[i] < 0f) e.Aura[i] = 0f;
            }
            if (e.SlowTimer > 0f) e.SlowTimer -= dt;
            if (e.ArmorCrackTimer > 0f)
            {
                e.ArmorCrackTimer -= dt;
                if (e.ArmorCrackTimer <= 0f) e.ArmorCrackStacks = 0;
            }
            if (e.SuperconductTimer > 0f) e.SuperconductTimer -= dt;
            if (e.SandstormTimer > 0f) e.SandstormTimer -= dt;
            if (e.VulnerableTimer > 0f)
            {
                e.VulnerableTimer -= dt;
                if (e.VulnerableTimer <= 0f) e.VulnerableAmount = 0f;
            }
            if (e.FreezeResistTimer > 0f)
            {
                e.FreezeResistTimer -= dt;
                if (e.FreezeResistTimer <= 0f) e.FreezeResist = 0f;
            }
            if (e.BuffAuraTimer > 0f)
            {
                e.BuffAuraTimer -= dt;
                if (e.BuffAuraTimer <= 0f) { e.SpeedBuff = 0f; e.ArmorBuff = 0f; }
            }
            if (!e.Chilled) e.ChillDamageReduction = 0f;
            if (e.Def.Params.Flag("adaptive")) UpdateAdaptive(e, dt);
            TickExpansionStatuses(e, dt);
            if (!e.Alive) return;
            UpdateEnemyAuras(e, dt);

            if (e.BurnTimer > 0f)
            {
                e.BurnTimer -= dt;
                e.BurnTick -= dt;
                if (e.BurnTick <= 0f)
                {
                    e.BurnTick = 0.5f;
                    // Burn ticks re-apply a small Fire gauge (generation 1) so DoT can trigger reactions
                    // like Vaporize on Wet targets, but never chain beyond the generation cap.
                    bool applyGauge = ((int)(e.BurnTimer * 2f)) % 2 == 0;
                    DealDamage(e, new DamageRequest
                    {
                        Source = e.BurnSource,
                        Attack = e.BurnDps * 0.5f,
                        Multiplier = 1f,
                        Element = Element.Fire,
                        Gauge = applyGauge ? 0.25f : 0f,
                        Kind = DamageKind.Dot,
                        Generation = 1,
                        IgnoreDefense = true
                    });
                }
            }
        }

        /// <summary>
        /// Adaptive counter enemies: periodically harden against the element that hurt them most.
        /// Capped partial resistance, shown to the player, never full immunity.
        /// </summary>
        private void UpdateAdaptive(EnemyUnit e, float dt)
        {
            e.AdaptTimer -= dt;
            if (e.AdaptTimer > 0f) return;
            e.AdaptTimer = e.Def.Params.Get("adaptInterval", 3f);
            int best = 0;
            float bestD = 0f;
            for (int i = 1; i < ElementUtil.Count; i++)
                if (e.AdaptDamage[i] > bestD) { bestD = e.AdaptDamage[i]; best = i; }
            if (best == 0 || best == e.AdaptedElement) return;
            if (e.AdaptedElement != 0) e.Resist[e.AdaptedElement] = e.Def.Resist[e.AdaptedElement];
            e.AdaptedElement = best;
            e.Resist[best] = e.Def.Resist[best] + e.Def.Params.Get("adaptResist", 0.45f);
            System.Array.Clear(e.AdaptDamage, 0, e.AdaptDamage.Length);
            Emit(SimEventType.StatusApplied, e.Pos, (Element)best, 0f, 0, e.Uid, "adapt");
        }

        private float EngageRadius(EnemyUnit e, HeroUnit h)
        {
            float baseR = e.Def.Params.Get("engage", 0.9f);
            return baseR + 0.35f * h.Stat(StatId.Threat) + e.Radius + h.Radius;
        }

        private HeroUnit FindHeroToEngage(EnemyUnit e)
        {
            HeroUnit best = null;
            float bestScore = float.MinValue;
            for (int i = 0; i < Heroes.Count; i++)
            {
                HeroUnit h = Heroes[i];
                if (!h.Alive) continue;
                float d = Vec2.Distance(e.Pos, h.Pos);
                if (d > EngageRadius(e, h)) continue;
                float score = h.Stat(StatId.Threat) * 2f - d;
                if (score > bestScore) { bestScore = score; best = h; }
            }
            return best;
        }

        private HeroUnit FindHeroWithin(EnemyUnit e, float r)
        {
            for (int i = 0; i < Heroes.Count; i++)
            {
                HeroUnit h = Heroes[i];
                if (h.Alive && Vec2.Distance(e.Pos, h.Pos) <= r + h.Radius) return h;
            }
            return null;
        }

        private void EngageHero(EnemyUnit e, HeroUnit h, float speed, float dt)
        {
            float reach = e.Def.AttackRange + e.Radius + h.Radius;
            float d = Vec2.Distance(e.Pos, h.Pos);
            if (d > reach)
            {
                Vec2 dir = (h.Pos - e.Pos).Normalized;
                e.Facing = dir;
                e.Pos = Vec2.MoveTowards(e.Pos, h.Pos - dir * reach * 0.9f, speed * dt);
                return;
            }
            if (e.AttackTimer <= 0f)
            {
                e.AttackTimer = e.Def.AttackInterval;
                DamageHero(h, e.Attack, e);
            }
            e.StuckTimer = 0f;
        }

        private bool UpdateRanged(EnemyUnit e, float speed, float dt)
        {
            float range = e.Def.AttackRange;
            HeroUnit target = null;
            float bestD = float.MaxValue;
            for (int i = 0; i < Heroes.Count; i++)
            {
                HeroUnit h = Heroes[i];
                if (!h.Alive) continue;
                float d = Vec2.Distance(e.Pos, h.Pos);
                if (d <= range && d < bestD) { bestD = d; target = h; }
            }
            if (target == null) return false;
            e.Facing = (target.Pos - e.Pos).Normalized;
            if (e.AttackTimer <= 0f)
            {
                e.AttackTimer = e.Def.AttackInterval;
                FireBolt(e, target, false, e.Attack);
            }
            e.StuckTimer = 0f;
            return true;
        }

        private void AdvanceOrAttackCrystal(EnemyUnit e, float speed, float dt)
        {
            float stopDist = Crystal.Radius + e.Radius + (e.Def.Behavior == EnemyBehavior.Ranged ? e.Def.AttackRange * 0.8f : 0.05f);
            float toCrystal = Vec2.Distance(e.Pos, Crystal.Pos);
            if (toCrystal <= stopDist + 0.05f)
            {
                e.Facing = (Crystal.Pos - e.Pos).Normalized;
                e.StuckTimer = 0f;
                if (e.Def.Params.Flag("latch")) Latch(e);
                if (e.AttackTimer > 0f) return;
                e.AttackTimer = e.Def.AttackInterval;
                if (e.Def.Behavior == EnemyBehavior.Ranged) FireBolt(e, null, true, e.CrystalDamage);
                else DamageCrystal(e.CrystalDamage, e);
                if (e.Def.Behavior == EnemyBehavior.Sapper)
                {
                    // Sappers detonate on the crystal: one big hit, then they are gone.
                    e.Alive = false;
                    Emit(SimEventType.EnemyDeath, e.Pos, Element.None, 0f, 0, e.Uid, e.Def.Id);
                }
                return;
            }

            LaneDef lane = Content.Arena.Lanes[e.Lane];
            Vec2 target = e.Waypoint < lane.Points.Count ? lane.Points[e.Waypoint] : Crystal.Pos;
            if (Vec2.Distance(e.Pos, target) < 0.35f && e.Waypoint < lane.Points.Count)
            {
                e.Waypoint++;
                target = e.Waypoint < lane.Points.Count ? lane.Points[e.Waypoint] : Crystal.Pos;
            }
            if (e.Waypoint >= lane.Points.Count - 1 && toCrystal < 2.5f) target = Crystal.Pos;
            Vec2 dir = (target - e.Pos).Normalized;
            e.Facing = dir;
            e.Pos = Vec2.MoveTowards(e.Pos, target, speed * dt);
            if (Vec2.Distance(e.Pos, Crystal.Pos) < stopDist) e.Pos = Crystal.Pos + (e.Pos - Crystal.Pos).Normalized * stopDist;

            // Stuck diagnostics: no progress for 6s while not fighting -> nudge to next waypoint.
            e.StuckTimer += dt;
            if (e.StuckTimer >= 6f)
            {
                if (Vec2.Distance(e.Pos, e.LastProgressPos) < 0.4f && speed > 0.05f)
                {
                    Stats.StuckRecoveries++;
                    e.Pos = Vec2.MoveTowards(e.Pos, target, 1.2f);
                }
                e.LastProgressPos = e.Pos;
                e.StuckTimer = 0f;
            }
        }

        private void ClampToArena(EnemyUnit e)
        {
            float hw = Content.Arena.HalfWidth + 1f, hh = Content.Arena.HalfHeight + 1f;
            e.Pos = new Vec2(SimMath.Clamp(e.Pos.X, -hw, hw), SimMath.Clamp(e.Pos.Y, -hh, hh));
        }

        private void UpdateSummoner(EnemyUnit e, float dt)
        {
            e.SpecialTimer -= dt;
            int cap = (int)e.Def.Params.Get("summonCap", 8f);
            if (e.SpecialTimer > 0f || e.Summoned >= cap) return;
            e.SpecialTimer = e.Def.Params.Get("specialInterval", 6f);
            string id = e.Def.Params.GetString("summon", "swarmling");
            if (!Content.Enemies.TryGetValue(id, out EnemyDef def)) return;
            int n = (int)e.Def.Params.Get("summonCount", 2f);
            Emit(SimEventType.Telegraph, e.Pos, Element.None, 0.4f, e.Uid, 0, "summon", false, 1f);
            for (int i = 0; i < n && e.Summoned < cap; i++)
            {
                Vec2 at = e.Pos + Vec2.FromAngle(Rng.Range(0f, 6.283f)) * 0.6f;
                SpawnEnemy(def, e.Lane, false, null, at);
                e.Summoned++;
            }
        }

        private void UpdateBuffer(EnemyUnit e, float dt)
        {
            e.SpecialTimer -= dt;
            if (e.SpecialTimer > 0f) return;
            e.SpecialTimer = 0.5f;
            List<EnemyUnit> c = RentList();
            QueryEnemies(e.Pos, e.Def.Params.Get("auraRadius", 2.2f), c);
            for (int i = 0; i < c.Count; i++)
            {
                EnemyUnit a = c[i];
                if (a == e) continue;
                a.SpeedBuff = e.Def.Params.Get("speedBuff", 0.25f);
                a.ArmorBuff = e.Def.Params.Get("armorBuff", 15f);
                a.BuffAuraTimer = 0.7f;
            }
            ReturnList(c);
        }

        private void OnEnemyDeathBehaviour(EnemyUnit e)
        {
            DeathBurst(e);
            string split = e.Def.Params.GetString("splitInto");
            if (!string.IsNullOrEmpty(split) && Content.Enemies.TryGetValue(split, out EnemyDef def))
            {
                int n = (int)e.Def.Params.Get("splitCount", 2f);
                for (int i = 0; i < n; i++) SpawnEnemy(def, e.Lane, false, null, e.Pos + Vec2.FromAngle(i * 3.14159f) * 0.3f);
            }
        }

        // ------------------------------------------------------------------ bosses

        private void UpdateBoss(EnemyUnit e, float dt)
        {
            switch (e.Def.Params.GetString("boss"))
            {
                case "golem": UpdateGolem(e, dt); break;
                case "warden": UpdateWarden(e, dt); break;
                case "ignaroth": UpdateIgnaroth(e, dt); break;
            }
        }

        /// <summary>
        /// Siegebreaker Golem: telegraphed charge slam at the strongest-threat hero (or the crystal),
        /// and a temporary armour phase at 50% HP that Armor Crack / Superconduct counter.
        /// </summary>
        private void UpdateGolem(EnemyUnit e, float dt)
        {
            ParamBag p = e.Def.Params;
            if (e.Phase == 0 && e.HpFraction <= 0.5f && p.Get("armorPhase") > 0f)
            {
                e.Phase = 1;
                e.PhaseTimer = p.Get("armorDuration", 7f);
                e.Defense += p.Get("armorPhase", 90f);
                Emit(SimEventType.BossPhase, e.Pos, Element.Earth, 1f, e.Uid, 0, "golem_armor", false, 1.5f);
            }
            if (e.Phase == 1)
            {
                e.PhaseTimer -= dt;
                if (e.PhaseTimer <= 0f)
                {
                    e.Phase = 2;
                    e.Defense -= p.Get("armorPhase", 90f);
                    Emit(SimEventType.BossPhase, e.Pos, Element.Earth, 2f, e.Uid, 0, "golem_exposed", false, 1.5f);
                }
            }

            if (e.TelegraphTimer > 0f)
            {
                e.TelegraphTimer -= dt;
                if (e.TelegraphTimer <= 0f)
                {
                    // Charge: travel to the marked spot, slam there.
                    e.Pos = Vec2.MoveTowards(e.Pos, e.TelegraphPos, p.Get("chargeDistance", 3.5f));
                }
                return;
            }
            e.SpecialTimer -= dt;
            if (e.SpecialTimer > 0f || e.StunTimer > 0f) return;
            e.SpecialTimer = p.Get("chargeInterval", 8f);
            HeroUnit target = null;
            float best = float.MinValue;
            for (int i = 0; i < Heroes.Count; i++)
            {
                HeroUnit h = Heroes[i];
                if (!h.Alive || Vec2.Distance(h.Pos, e.Pos) > 5f) continue;
                float s = h.Stat(StatId.Threat) - Vec2.Distance(h.Pos, e.Pos) * 0.3f;
                if (s > best) { best = s; target = h; }
            }
            Vec2 aim = target != null ? target.Pos : Vec2.MoveTowards(e.Pos, Crystal.Pos, 3f);
            e.TelegraphPos = aim;
            e.TelegraphRadius = p.Get("slamRadius", 1.6f);
            float windup = p.Get("windup", 1.3f);
            e.TelegraphTimer = windup;
            AddStrike(new DelayedStrike
            {
                Kind = StrikeKind.BossSlam,
                Pos = aim,
                Delay = windup + 0.15f,
                Radius = e.TelegraphRadius,
                EnemySource = e,
                Power = e.Attack * p.Get("slamMult", 2.5f),
                Element = Element.Earth
            });
        }

        /// <summary>
        /// The Rift Warden: P1 summons riftlings; P2 marks a lane and sends a telegraphed assault down
        /// it; P3 casts a 3-slam sequence and is then Exposed (+50% damage taken) as a safety window.
        /// </summary>
        private void UpdateWarden(EnemyUnit e, float dt)
        {
            ParamBag p = e.Def.Params;
            int desired = e.HpFraction > 0.66f ? 0 : (e.HpFraction > 0.33f ? 1 : 2);
            if (desired > e.Phase)
            {
                e.Phase = desired;
                e.Invulnerable = 1.5f;
                e.SpecialTimer = 2f;
                e.Summoned = 0;
                Emit(SimEventType.BossPhase, e.Pos, Element.None, e.Phase, e.Uid, 0, "warden_phase_" + (e.Phase + 1), false, 2f);
            }

            if (e.TelegraphTimer > 0f)
            {
                e.TelegraphTimer -= dt;
                if (e.TelegraphTimer <= 0f && e.TelegraphKind == 3)
                {
                    e.VulnerableTimer = p.Get("exposedDuration", 4.5f);
                    e.VulnerableAmount = p.Get("exposedAmount", 0.5f);
                    Emit(SimEventType.BossPhase, e.Pos, Element.None, 9f, e.Uid, 0, "warden_exposed", false, 2f);
                }
                return;
            }

            e.SpecialTimer -= dt;
            if (e.SpecialTimer > 0f) return;

            if (e.Phase == 0)
            {
                e.SpecialTimer = p.Get("summonInterval", 7f);
                if (Content.Enemies.TryGetValue(p.GetString("summon", "riftling"), out EnemyDef add))
                {
                    Emit(SimEventType.Telegraph, e.Pos, Element.None, 0.6f, e.Uid, 0, "summon", false, 2f);
                    int n = (int)p.Get("summonCount", 4f);
                    for (int i = 0; i < n; i++) SpawnEnemy(add, (e.Lane + i) % Content.Arena.Lanes.Count, false, null, null);
                }
            }
            else if (e.Phase == 1)
            {
                e.SpecialTimer = p.Get("laneInterval", 9f);
                int lane = Rng.Range(0, Content.Arena.Lanes.Count);
                LaneDef l = Content.Arena.Lanes[lane];
                Emit(SimEventType.Telegraph, l.Points[0], Element.None, 1.5f, e.Uid, lane, "lane_mark", false, 0f);
                // Telegraphed strikes march down the lane; heroes standing on it take hits.
                for (int i = 1; i < l.Points.Count; i++)
                {
                    AddStrike(new DelayedStrike
                    {
                        Kind = StrikeKind.BossLaneMark,
                        Pos = l.Points[i],
                        Delay = 1.5f + i * 0.35f,
                        Radius = 1.1f,
                        EnemySource = e,
                        Power = e.Attack * p.Get("laneMult", 1.2f)
                    });
                }
                if (Content.Enemies.TryGetValue(p.GetString("laneSummon", "runner"), out EnemyDef runner))
                    for (int i = 0; i < (int)p.Get("laneSummonCount", 4f); i++)
                        InsertSpawn(new ScheduledSpawn { Time = Time + 1.5f + i * 0.4f, Def = runner, Lane = lane });
            }
            else
            {
                e.SpecialTimer = p.Get("sequenceInterval", 10f);
                e.TelegraphKind = 3;
                e.TelegraphTimer = 3f;
                int k = 0;
                for (int i = 0; i < Heroes.Count && k < 3; i++)
                {
                    HeroUnit h = Heroes[(i + TickCount) % Heroes.Count];
                    if (!h.Alive) continue;
                    AddStrike(new DelayedStrike
                    {
                        Kind = StrikeKind.BossSlam,
                        Pos = h.Pos,
                        Delay = 1.2f + k * 0.7f,
                        Radius = 1.3f,
                        EnemySource = e,
                        Power = e.Attack * p.Get("slamMult", 1.6f)
                    });
                    k++;
                }
            }
        }
    }
}
