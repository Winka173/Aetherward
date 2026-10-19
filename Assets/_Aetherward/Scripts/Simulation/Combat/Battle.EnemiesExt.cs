using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    /// <summary>
    /// Expansion enemy mechanics, all keyed by params in enemies.json (never by enemy id): hero
    /// debuff auras (Mana Leech), crystal latching (Crystal Parasite), death bursts (Ash Imp) and
    /// the Ember Tyrant boss script. Every threat has a documented counter.
    /// </summary>
    public sealed partial class Battle
    {
        private int _coreGuardTick = -1;
        private bool _coreGuarded;

        /// <summary>True when a living hero stands within 2.5 m of the crystal edge (near-core guard).</summary>
        public bool CoreGuarded
        {
            get
            {
                if (_coreGuardTick == TickCount) return _coreGuarded;
                _coreGuardTick = TickCount;
                _coreGuarded = false;
                for (int i = 0; i < Heroes.Count; i++)
                    if (Heroes[i].Alive && Vec2.Distance(Heroes[i].Pos, Crystal.Pos) <= Crystal.Radius + 2.5f) { _coreGuarded = true; break; }
                return _coreGuarded;
            }
        }

        private void UpdateEnemyAuras(EnemyUnit e, float dt)
        {
            ParamBag p = e.Def.Params;
            float leechRadius = p.Get("leechRadius");
            if (leechRadius <= 0f || e.SealTimer > 0f || e.Stunned) return;
            e.Timer2 -= dt;
            if (e.Timer2 > 0f) return;
            e.Timer2 = 0.5f;
            for (int i = 0; i < Heroes.Count; i++)
            {
                HeroUnit h = Heroes[i];
                if (!h.Alive || ImmuneToDebuffs(h) || Vec2.Distance(h.Pos, e.Pos) > leechRadius + h.Radius) continue;
                if (h.LeechTimer <= 0f) Emit(SimEventType.StatusApplied, h.Pos, Element.Arcane, 0f, e.Uid, h.Uid, "leeched");
                h.LeechTimer = 1f;
                h.LeechAmount = SimMath.Max(h.LeechAmount, p.Get("leechAmount", 0.35f));
            }
        }

        /// <summary>Crystal Parasite reached the crystal: it latches on (resists damage unless the core is guarded).</summary>
        private void Latch(EnemyUnit e)
        {
            if (e.Latched) return;
            e.Latched = true;
            Emit(SimEventType.StatusApplied, e.Pos, Element.None, 0f, e.Uid, e.Uid, "latched");
        }

        /// <summary>Light (Illuminate) or a cleanse rips a latched parasite off the crystal and stuns it.</summary>
        public void Detach(EnemyUnit e)
        {
            if (!e.Latched || !e.Alive) return;
            e.Latched = false;
            Vec2 away = (e.Pos - Crystal.Pos).SqrLength > 1e-4f ? (e.Pos - Crystal.Pos).Normalized : new Vec2(1f, 0f);
            e.Knockback = away * (1.6f / 0.2f);
            e.KnockbackTimer = 0.2f;
            e.StunTimer = SimMath.Max(e.StunTimer, 1.2f);
            Emit(SimEventType.Strike, e.Pos, Element.Light, 0f, 0, e.Uid, "detach", false, 0.6f);
        }

        private void DetachNear(Vec2 pos, float radius)
        {
            List<EnemyUnit> c = RentList();
            QueryEnemies(pos, radius, c);
            for (int i = 0; i < c.Count; i++) if (c[i].Latched) Detach(c[i]);
            ReturnList(c);
        }

        private void DeathBurst(EnemyUnit e)
        {
            float r = e.Def.Params.Get("deathBurst");
            if (r <= 0f) return;
            Emit(SimEventType.Strike, e.Pos, Element.Fire, 0f, e.Uid, 0, "death_burst", false, r);
            for (int i = 0; i < Heroes.Count; i++)
            {
                HeroUnit h = Heroes[i];
                if (h.Alive && Vec2.Distance(h.Pos, e.Pos) <= r + h.Radius) DamageHero(h, e.Attack * e.Def.Params.Get("deathBurstMult", 1f), e);
            }
        }

        // ------------------------------------------------------------------ Ignaroth, the Ember Tyrant

        /// <summary>
        /// P1: telegraphed lava eruptions under heroes and Ash Imp summons. At 50% HP it Overheats:
        /// tougher against Fire, weaker to Water/Ice, a scorching aura, faster eruptions, and every
        /// vent cycle it cools down and is Exposed (the counter window).
        /// </summary>
        private void UpdateIgnaroth(EnemyUnit e, float dt)
        {
            ParamBag p = e.Def.Params;
            if (e.Phase == 0 && e.HpFraction <= p.Get("heatAt", 0.5f))
            {
                e.Phase = 1;
                e.Invulnerable = 1.2f;
                e.Resist[(int)Element.Fire] += p.Get("heatResist", 0.35f);
                e.Resist[(int)Element.Water] -= p.Get("heatVuln", 0.35f);
                e.Resist[(int)Element.Ice] -= p.Get("heatVuln", 0.35f);
                e.PhaseTimer = p.Get("ventInterval", 12f);
                Emit(SimEventType.BossPhase, e.Pos, Element.Fire, 1f, e.Uid, 0, "ignaroth_heat", false, 2f);
            }
            if (e.Phase == 1)
            {
                if (TickCount % 15 == 0)
                {
                    float r = p.Get("auraRadius", 2.2f);
                    for (int i = 0; i < Heroes.Count; i++)
                    {
                        HeroUnit h = Heroes[i];
                        if (h.Alive && Vec2.Distance(h.Pos, e.Pos) <= r + h.Radius) DamageHero(h, e.Attack * p.Get("auraMult", 0.12f), e);
                    }
                }
                e.PhaseTimer -= dt;
                if (e.PhaseTimer <= 0f)
                {
                    e.PhaseTimer = p.Get("ventInterval", 12f);
                    e.VulnerableTimer = p.Get("ventDuration", 3f);
                    e.VulnerableAmount = p.Get("ventVuln", 0.4f);
                    Emit(SimEventType.BossPhase, e.Pos, Element.Fire, 2f, e.Uid, 0, "ignaroth_vent", false, 2f);
                }
            }
            if (e.SealTimer > 0f || e.Stunned) return;

            e.Timer2 -= dt;
            if (e.Timer2 <= 0f)
            {
                e.Timer2 = p.Get("summonInterval", 9f);
                if (Content.Enemies.TryGetValue(p.GetString("summon", "ash_imp"), out EnemyDef imp))
                {
                    Emit(SimEventType.Telegraph, e.Pos, Element.Fire, 0.6f, e.Uid, 0, "summon", false, 1.6f);
                    for (int i = 0; i < (int)p.Get("summonCount", 3f); i++)
                        SpawnEnemy(imp, e.Lane, false, null, e.Pos + Vec2.FromAngle(i * 2.1f + Rng.Range(0f, 0.5f)) * 0.9f);
                }
            }

            e.SpecialTimer -= dt;
            if (e.SpecialTimer > 0f) return;
            e.SpecialTimer = p.Get("lavaInterval", 7f) * (e.Phase == 1 ? 0.7f : 1f);
            int count = (int)p.Get("lavaCount", 3f), placed = 0;
            for (int i = 0; i < Heroes.Count && placed < count; i++)
            {
                HeroUnit h = Heroes[(i + TickCount) % Heroes.Count];
                if (!h.Alive) continue;
                AddStrike(new DelayedStrike
                {
                    Kind = StrikeKind.BossSlam,
                    Pos = h.Pos,
                    Delay = p.Get("lavaDelay", 1.6f),
                    Radius = p.Get("lavaRadius", 1.3f),
                    EnemySource = e,
                    Power = e.Attack * p.Get("lavaMult", 1.6f),
                    Element = Element.Fire
                });
                placed++;
            }
        }
    }
}
