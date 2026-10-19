using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    /// <summary>
    /// Nature/Poison hero skill kinds and passives (Expansion Phase 2): root blooms, thorn barriers,
    /// catalyst flasks and the plague doctor's infect-and-heal. Selected by kind, tuned by params.
    /// </summary>
    public sealed partial class Battle
    {
        private bool CastSkillNature(HeroUnit h, SkillDef s, float power, float mult, Element el, ref Vec2 castPos, out bool handled)
        {
            handled = true;
            switch (s.Kind)
            {
                case "root_bloom": return CastRootBloom(h, s, mult, el, ref castPos);
                case "thorn_wall": return CastThornWall(h, s, power, mult, el, ref castPos);
                case "catalyst_flask": return CastCatalystFlask(h, s, mult, el, ref castPos);
                case "plague_cure": return CastPlagueCure(h, s, power, mult, el, ref castPos);
                default:
                    handled = false;
                    return false;
            }
        }

        /// <summary>Spawns the skill's optional field (param "field") at a position, kept off the crystal.</summary>
        private void SpawnSkillField(HeroUnit h, SkillDef s, Vec2 pos, float mult)
        {
            string id = s.Params.GetString("field");
            if (id == null || !Content.Fields.TryGetValue(id, out FieldDef f)) return;
            float minC = Crystal.Radius + s.Params.Get("minCrystal", 1.4f);
            if (Vec2.Distance(pos, Crystal.Pos) < minC) pos = Crystal.Pos + (pos - Crystal.Pos).Normalized * minC;
            SpawnField(f, pos, s.Params.Get("fieldRadius", 1.8f), s.Params.Get("fieldDuration", 5f), h, h.Stat(StatId.Attack) * mult, 0, s.Kind, null);
        }

        /// <summary>Grove Warden: a burst of vines at the densest group that damages and Roots.</summary>
        private bool CastRootBloom(HeroUnit h, SkillDef s, float mult, Element el, ref Vec2 castPos)
        {
            ParamBag p = s.Params;
            EnemyUnit t = SelectTarget(h, TargetProfile.Cluster, 1f);
            if (t == null) return false;
            List<EnemyUnit> c = RentList();
            float r = p.Get("radius", 2.0f);
            QueryEnemies(t.Pos, r, c);
            for (int i = 0; i < c.Count; i++)
            {
                EnemyUnit e = c[i];
                DamageRequest d = DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill);
                d.BonusMult += PassiveBonus(h, e);
                DealDamage(e, d);
                if (e.Alive) Root(e, p.Get("rootDuration", 1.2f));
            }
            ReturnList(c);
            Emit(SimEventType.Strike, t.Pos, Element.Nature, 0f, h.Uid, 0, "root_bloom", false, r);
            SpawnSkillField(h, s, t.Pos, p.Get("fieldMult", 0.3f));
            castPos = t.Pos;
            return true;
        }

        /// <summary>
        /// Thornguard: raises a bark shield and thorns (attackers take reflected damage), taunting nearby
        /// enemies; with "lash" it first whips the densest group at range, rooting it.
        /// </summary>
        private bool CastThornWall(HeroUnit h, SkillDef s, float power, float mult, Element el, ref Vec2 castPos)
        {
            ParamBag p = s.Params;
            List<EnemyUnit> c = RentList();
            QueryEnemies(h.Pos, p.Get("tauntRadius", 2.2f), c);
            EnemyUnit lash = p.Get("lashRadius") > 0f ? SelectTarget(h, TargetProfile.Cluster, p.Get("lashRange", 2.5f)) : null;
            if (c.Count == 0 && lash == null && h.HpFraction > 0.9f)
            {
                ReturnList(c);
                return false;
            }
            castPos = h.Pos;
            if (lash != null)
            {
                QueryEnemies(lash.Pos, p.Get("lashRadius"), c);
                for (int i = 0; i < c.Count; i++)
                {
                    DamageRequest d = DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill);
                    d.BonusMult += PassiveBonus(h, c[i]);
                    DealDamage(c[i], d);
                    if (c[i].Alive) Root(c[i], p.Get("rootDuration", 1.0f));
                }
                Emit(SimEventType.Strike, lash.Pos, Element.Nature, 0f, h.Uid, 0, "thorn_lash", false, p.Get("lashRadius"));
                castPos = lash.Pos;
            }
            ReturnList(c);
            AddHeroShield(h, h.MaxHp * p.Get("shieldPct", 0.15f) * power, h);
            h.ThornTimer = p.Get("duration", 5f);
            h.ThornMult = p.Get("reflectMult", 0.45f) * power;
            h.ThornRoot = p.Get("thornRoot");
            Taunt(h, p.Get("tauntRadius", 2.2f), p.Get("taunt", 1.5f));
            return true;
        }

        /// <summary>Alchemist: a flask that poisons a group, optionally detonating poison already there, and leaves a patch.</summary>
        private bool CastCatalystFlask(HeroUnit h, SkillDef s, float mult, Element el, ref Vec2 castPos)
        {
            ParamBag p = s.Params;
            EnemyUnit t = SelectTarget(h, TargetProfile.Cluster, 1f);
            if (t == null) return false;
            List<EnemyUnit> c = RentList();
            float r = p.Get("radius", 1.8f);
            QueryEnemies(t.Pos, r, c);
            float detonate = p.Get("detonatePerStack");
            for (int i = 0; i < c.Count; i++)
            {
                EnemyUnit e = c[i];
                DamageRequest d = DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill);
                d.BonusMult += PassiveBonus(h, e);
                if (detonate > 0f && e.PoisonStacks > 0)
                {
                    // Volatile Mixture: consume half the stacks for burst damage (consumed, so it cannot loop).
                    int used = System.Math.Max(1, e.PoisonStacks / 2);
                    e.PoisonStacks -= used;
                    d.BonusMult += detonate * used;
                }
                DealDamage(e, d);
                if (e.Alive) AddPoison(e, (int)p.Get("stacks", 2f), p.Get("poisonDuration", 6f), h);
            }
            ReturnList(c);
            Emit(SimEventType.Strike, t.Pos, Element.Poison, 0f, h.Uid, 0, "catalyst_flask", false, r);
            SpawnSkillField(h, s, t.Pos, p.Get("fieldMult", 0.25f));
            castPos = t.Pos;
            return true;
        }

        /// <summary>
        /// Plague Doctor: infects a group, then heals the most hurt ally for more the more enemies are
        /// poisoned nearby. Tradeoff: the healed ally runs a Fever (takes more damage) unless "remedy".
        /// </summary>
        private bool CastPlagueCure(HeroUnit h, SkillDef s, float power, float mult, Element el, ref Vec2 castPos)
        {
            ParamBag p = s.Params;
            EnemyUnit t = SelectTarget(h, TargetProfile.Cluster, 1f);
            HeroUnit ally = LowestHpAlly(h.Pos, p.Get("healRange", 5f), p.Get("healBelow", 0.85f));
            if (t == null && ally == null) return false;
            List<EnemyUnit> c = RentList();
            if (t != null)
            {
                QueryEnemies(t.Pos, p.Get("radius", 1.8f), c);
                for (int i = 0; i < c.Count; i++)
                {
                    EnemyUnit e = c[i];
                    DealDamage(e, DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill));
                    if (e.Alive) AddPoison(e, (int)p.Get("stacks", 2f), p.Get("poisonDuration", 6f), h);
                }
                Emit(SimEventType.Strike, t.Pos, Element.Poison, 0f, h.Uid, 0, "infect", false, p.Get("radius", 1.8f));
                castPos = t.Pos;
            }
            if (ally != null)
            {
                QueryEnemies(ally.Pos, p.Get("countRadius", 5f), c);
                int poisoned = 0;
                for (int i = 0; i < c.Count; i++) if (c[i].Alive && c[i].PoisonStacks > 0) poisoned++;
                poisoned = System.Math.Min(poisoned, (int)p.Get("countMax", 6f));
                float pct = p.Get("healPct", 0.08f) + p.Get("healPerPoisoned", 0.02f) * poisoned;
                HealHero(ally, ally.MaxHp * pct * power, h);
                if (p.Flag("cleanse")) CleanseHero(ally);
                float buff = p.Get("hasteBuff");
                if (buff > 0f) AddBuff(ally, StatId.AttackInterval, buff, p.Get("buffDuration", 4f), "remedy");
                float fever = p.Get("fever");
                if (fever > 0f && !ImmuneToDebuffs(ally))
                {
                    ally.FeverAmount = SimMath.Max(ally.FeverAmount, fever);
                    ally.FeverTimer = SimMath.Max(ally.FeverTimer, p.Get("feverDuration", 3f));
                }
                if (t == null) castPos = ally.Pos;
            }
            ReturnList(c);
            return true;
        }

        // ================================================================== passives & hooks

        private float PassiveBonusNature(HeroUnit h, EnemyUnit e)
        {
            switch (h.PassiveKind)
            {
                case "deep_roots": return e.Rooted ? h.PassiveParams.Get("bonus", 0.3f) : 0f;
                case "catalysis": return SimMath.Min(h.PassiveParams.Get("cap", 0.3f), e.PoisonStacks * h.PassiveParams.Get("perStack", 0.04f));
                default: return 0f;
            }
        }

        /// <summary>Barkskin: up to "max" damage reduction as the hero loses health.</summary>
        private float SelfPassiveReduction(HeroUnit h)
        {
            if (h.PassiveKind != "barkskin") return 0f;
            float missing = 1f - h.HpFraction;
            return SimMath.Min(h.PassiveParams.Get("max", 0.2f), missing * h.PassiveParams.Get("perMissing", 0.4f));
        }

        /// <summary>Thorns: attackers take reflected Nature damage (and may be rooted).</summary>
        private void ThornsOnHit(HeroUnit h, EnemyUnit attacker)
        {
            if (h.ThornTimer <= 0f || !attacker.Alive || h.ThornCooldown > 0f) return;
            h.ThornCooldown = 0.25f;
            DealDamage(attacker, DamageRequest.From(h, h.ThornMult, Element.Nature, 0.4f, DamageKind.Skill, 1));
            if (h.ThornRoot > 0f && attacker.Alive) Root(attacker, h.ThornRoot);
        }

        private void TickNatureHero(HeroUnit h, float dt)
        {
            if (h.ThornTimer > 0f) h.ThornTimer -= dt;
            if (h.ThornCooldown > 0f) h.ThornCooldown -= dt;
            if (h.DoctorCooldown > 0f) h.DoctorCooldown -= dt;
        }

        /// <summary>Plague Doctor passive: a poisoned enemy dying near Sable mends the most hurt ally (internal cooldown).</summary>
        private void OnEnemyDeathNature(EnemyUnit dead)
        {
            if (dead.PoisonStacks <= 0) return;
            for (int i = 0; i < Heroes.Count; i++)
            {
                HeroUnit h = Heroes[i];
                if (!h.Alive || h.PassiveKind != "plague_doctor" || h.DoctorCooldown > 0f) continue;
                if (Vec2.Distance(h.Pos, dead.Pos) > h.PassiveParams.Get("radius", 5f)) continue;
                HeroUnit ally = LowestHpAlly(h.Pos, h.PassiveParams.Get("radius", 5f) + 1f, 0.99f);
                if (ally == null) continue;
                h.DoctorCooldown = h.PassiveParams.Get("cooldown", 1.5f);
                HealHero(ally, ally.MaxHp * h.PassiveParams.Get("healPct", 0.03f), h);
            }
        }
    }
}
