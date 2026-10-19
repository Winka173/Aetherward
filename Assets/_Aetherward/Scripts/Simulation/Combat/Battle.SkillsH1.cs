using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    /// <summary>
    /// Expansion Phase 3 hero skill kinds and passives: Arcane/Void (echo, rune circles, rifts, void
    /// wards), the remaining launch-element specialists (ember script, river surge, charged shot,
    /// shatter lance, zone drift, fracture punch) and Light/Shadow H2 (sun beam, curse mire).
    /// Selected by kind, tuned by params; no hero id is inspected.
    /// </summary>
    public sealed partial class Battle
    {
        private bool CastSkillH1(HeroUnit h, SkillDef s, float power, float mult, float range, Element el, ref Vec2 castPos, out bool handled)
        {
            handled = true;
            switch (s.Kind)
            {
                case "arcane_echo": return CastArcaneEcho(h, s, mult, el, ref castPos);
                case "rune_circle": return CastRuneCircle(h, s, mult, el, ref castPos);
                case "gravity_rift": return CastGravityRift(h, s, mult, el, ref castPos);
                case "void_ward": return CastVoidWard(h, s, power, mult, el, ref castPos);
                case "ember_script": return CastEmberScript(h, s, mult, el, ref castPos);
                case "river_surge": return CastRiverSurge(h, s, mult, el, ref castPos);
                case "charged_shot": return CastChargedShot(h, s, mult, el, ref castPos);
                case "shatter_lance": return CastShatterLance(h, s, mult, el, ref castPos);
                case "zone_drift": return CastZoneDrift(h, s, mult, range, el, ref castPos);
                case "fracture_punch": return CastFracturePunch(h, s, power, mult, el, ref castPos);
                case "sun_beam": return CastSunBeam(h, s, power, mult, range, el, ref castPos);
                case "curse_mire": return CastCurseMire(h, s, power, mult, el, ref castPos);
                default:
                    handled = false;
                    return false;
            }
        }

        private void HitArea(HeroUnit h, SkillDef s, Vec2 pos, float radius, float mult, Element el, List<EnemyUnit> into)
        {
            QueryEnemies(pos, radius, into);
            for (int i = 0; i < into.Count; i++)
            {
                DamageRequest d = DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill);
                d.BonusMult += PassiveBonus(h, into[i]);
                DealDamage(into[i], d);
            }
        }

        // ------------------------------------------------------------------ Arcane / Void

        /// <summary>Echo Savant: an arcane burst that leaves targets Resonant and primes an echo of the next ally skill.</summary>
        private bool CastArcaneEcho(HeroUnit h, SkillDef s, float mult, Element el, ref Vec2 castPos)
        {
            ParamBag p = s.Params;
            int bolts = (int)p.Get("bolts");
            if (bolts > 0)
            {
                // Arcane Barrage: separate bolts at the strongest enemies in range.
                List<EnemyUnit> c = RentList();
                QueryEnemies(h.Pos, h.Stat(StatId.Range) + 1.5f, c);
                c.Sort((a, b) => { int d = b.Hp.CompareTo(a.Hp); return d != 0 ? d : a.Uid.CompareTo(b.Uid); });
                int n = 0;
                for (int i = 0; i < c.Count && n < bolts; i++, n++)
                {
                    DamageRequest d = DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill);
                    d.BonusMult += PassiveBonus(h, c[i]);
                    DealDamage(c[i], d);
                    if (c[i].Alive) c[i].ResonantTimer = SimMath.Max(c[i].ResonantTimer, p.Get("resonant", 4f));
                    castPos = c[i].Pos;
                }
                ReturnList(c);
                return n > 0;
            }
            EnemyUnit t = SelectTarget(h, TargetProfile.Cluster, 1f);
            if (t == null) return false;
            List<EnemyUnit> hit = RentList();
            HitArea(h, s, t.Pos, p.Get("radius", 1.8f), mult, el, hit);
            for (int i = 0; i < hit.Count; i++) if (hit[i].Alive) hit[i].ResonantTimer = SimMath.Max(hit[i].ResonantTimer, p.Get("resonant", 4f));
            ReturnList(hit);
            h.EchoPrimed = p.Get("echoWindow", 6f);
            h.EchoCharges = (int)p.Get("echoCharges", 1f);
            Emit(SimEventType.Strike, t.Pos, Element.Arcane, 0f, h.Uid, 0, "arcane_echo", false, p.Get("radius", 1.8f));
            castPos = t.Pos;
            return true;
        }

        /// <summary>
        /// Echo Savant hook: after another hero's own (non-echo) skill, a primed savant replays it at
        /// reduced power. Echo casts never trigger echoes (anti-loop), and charges are finite.
        /// </summary>
        private void TryAllyEcho(HeroUnit caster)
        {
            for (int i = 0; i < Heroes.Count; i++)
            {
                HeroUnit s = Heroes[i];
                if (s == caster || !s.Alive || s.EchoPrimed <= 0f || s.EchoCharges <= 0) continue;
                if (--s.EchoCharges <= 0) s.EchoPrimed = 0f;
                Emit(SimEventType.StatusApplied, caster.Pos, Element.Arcane, 0f, s.Uid, caster.Uid, "echo");
                CastSkill(caster, s.Skill.Params.Get("echoPower", 0.5f), true);
                return;
            }
        }

        /// <summary>Rune Conductor: a rune circle that amplifies reactions on enemies inside it.</summary>
        private bool CastRuneCircle(HeroUnit h, SkillDef s, float mult, Element el, ref Vec2 castPos)
        {
            EnemyUnit t = SelectTarget(h, TargetProfile.Cluster, 1f);
            if (t == null) return false;
            List<EnemyUnit> hit = RentList();
            HitArea(h, s, t.Pos, s.Params.Get("radius", 2f), mult, el, hit);
            ReturnList(hit);
            SpawnSkillField(h, s, t.Pos, s.Params.Get("fieldMult", 0.2f));
            castPos = t.Pos;
            return true;
        }

        /// <summary>Rift Binder: drags a group together, stacks Unstable on it and opens a collapsing rift.</summary>
        private bool CastGravityRift(HeroUnit h, SkillDef s, float mult, Element el, ref Vec2 castPos)
        {
            ParamBag p = s.Params;
            EnemyUnit t = SelectTarget(h, TargetProfile.Cluster, 1.5f);
            if (t == null) return false;
            Vec2 at = t.Pos;
            float minC = Crystal.Radius + 1.6f;
            if (Vec2.Distance(at, Crystal.Pos) < minC) at = Crystal.Pos + (at - Crystal.Pos).Normalized * minC; // never drag foes onto the core
            List<EnemyUnit> hit = RentList();
            HitArea(h, s, at, p.Get("radius", 2.4f), mult, el, hit);
            for (int i = 0; i < hit.Count; i++)
            {
                if (!hit[i].Alive) continue;
                Pull(hit[i], at, p.Get("pull", 3f), 0.4f);
                AddUnstable(hit[i], (int)p.Get("unstable", 1f), h, 1);
            }
            ReturnList(hit);
            SpawnSkillField(h, s, at, p.Get("fieldMult", 0.3f));
            castPos = at;
            return true;
        }

        /// <summary>Void Sentinel: a ward around her that swallows enemy projectiles and seals nearby enemies.</summary>
        private bool CastVoidWard(HeroUnit h, SkillDef s, float power, float mult, Element el, ref Vec2 castPos)
        {
            ParamBag p = s.Params;
            List<EnemyUnit> c = RentList();
            QueryEnemies(h.Pos, p.Get("sealRadius", 2.4f), c);
            if (c.Count == 0 && Bolts.Count == 0)
            {
                ReturnList(c);
                return false;
            }
            for (int i = 0; i < c.Count; i++)
            {
                DealDamage(c[i], DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill));
                if (c[i].Alive) Seal(c[i], p.Get("seal", 2f));
            }
            ReturnList(c);
            SpawnSkillField(h, s, h.Pos, 0.1f);
            if (p.Get("crystalShield") > 0f) ShieldCrystal(Crystal.MaxHp * p.Get("crystalShield") * power);
            if (p.Get("taunt") > 0f) Taunt(h, p.Get("sealRadius", 2.4f), p.Get("taunt"));
            castPos = h.Pos;
            return true;
        }

        // ------------------------------------------------------------------ launch-element specialists

        /// <summary>Ember Scribe: writes burn marks on a group; marks at the threshold detonate.</summary>
        private bool CastEmberScript(HeroUnit h, SkillDef s, float mult, Element el, ref Vec2 castPos)
        {
            ParamBag p = s.Params;
            EnemyUnit t = SelectTarget(h, TargetProfile.Cluster, 1f);
            if (t == null) return false;
            List<EnemyUnit> hit = RentList();
            HitArea(h, s, t.Pos, p.Get("radius", 1.8f), mult, el, hit);
            for (int i = 0; i < hit.Count; i++)
            {
                if (!hit[i].Alive) continue;
                AddMark(hit[i], (int)p.Get("marks", 2f), h);
                TryDetonateMarks(h, hit[i]);
            }
            ReturnList(hit);
            castPos = t.Pos;
            return true;
        }

        /// <summary>Marks at the scribe's threshold detonate (consumed first, so a detonation cannot recurse).</summary>
        private void TryDetonateMarks(HeroUnit h, EnemyUnit e)
        {
            ParamBag p = h.Skill.Params;
            int at = (int)p.Get("detonateAt", 4f);
            if (e.MarkStacks < at || !e.Alive) return;
            int marks = e.MarkStacks;
            e.MarkStacks = 0;
            float r = p.Get("detonateRadius", 1.6f);
            List<EnemyUnit> c = RentList();
            QueryEnemies(e.Pos, r, c);
            Emit(SimEventType.Strike, e.Pos, Element.Fire, 0f, h.Uid, 0, "mark_detonate", false, r);
            for (int i = 0; i < c.Count; i++)
            {
                DealDamage(c[i], new DamageRequest
                {
                    Source = h, Attack = h.Stat(StatId.Attack), Multiplier = p.Get("detonateMult", 0.35f) * marks,
                    Element = Element.Fire, Gauge = 0.5f, Kind = DamageKind.Skill, Generation = 1, SourceTag = "mark_detonate"
                });
                if (c[i].Alive && p.Get("detonateBurn") > 0f) ApplyBurn(c[i], h, p.Get("detonateBurn"));
            }
            ReturnList(c);
            float buff = p.Get("teamBuff");
            if (buff > 0f)
                for (int i = 0; i < Heroes.Count; i++)
                    if (Heroes[i].Alive) AddBuff(Heroes[i], StatId.Attack, buff, p.Get("buffDuration", 3f), "kindling_script");
        }

        /// <summary>River Shaper: a surge that shoves the lead group back along its path and leaves a stream.</summary>
        private bool CastRiverSurge(HeroUnit h, SkillDef s, float mult, Element el, ref Vec2 castPos)
        {
            ParamBag p = s.Params;
            EnemyUnit t = SelectTarget(h, TargetProfile.NearestToCrystal, 1.5f);
            if (t == null) return false;
            List<EnemyUnit> hit = RentList();
            HitArea(h, s, t.Pos, p.Get("radius", 2f), mult, el, hit);
            for (int i = 0; i < hit.Count; i++)
                if (hit[i].Alive) Knock(hit[i], (hit[i].Pos - Crystal.Pos).Normalized, p.Get("push", 1.6f));
            ReturnList(hit);
            SpawnSkillField(h, s, t.Pos, p.Get("fieldMult", 0.15f));
            castPos = t.Pos;
            return true;
        }

        /// <summary>Arcshot Ranger: a charged shot that spends ramp stacks for damage (optionally split).</summary>
        private bool CastChargedShot(HeroUnit h, SkillDef s, float mult, Element el, ref Vec2 castPos)
        {
            ParamBag p = s.Params;
            EnemyUnit t = SelectTarget(h, TargetProfile.Elite, 1.5f);
            if (t == null) return false;
            float bonus = h.RampTargetUid == t.Uid ? h.RampStacks * p.Get("perRamp", 0.15f) : 0f;
            int splits = (int)p.Get("splits");
            List<EnemyUnit> c = RentList();
            c.Add(t);
            if (splits > 0)
            {
                List<EnemyUnit> near = RentList();
                QueryEnemies(t.Pos, p.Get("splitRadius", 3f), near);
                near.Sort((a, b) => { int d = Vec2.SqrDistance(a.Pos, t.Pos).CompareTo(Vec2.SqrDistance(b.Pos, t.Pos)); return d != 0 ? d : a.Uid.CompareTo(b.Uid); });
                for (int i = 0; i < near.Count && c.Count <= splits; i++) if (near[i] != t) c.Add(near[i]);
                ReturnList(near);
            }
            for (int i = 0; i < c.Count; i++)
            {
                DamageRequest d = DamageRequest.From(h, i == 0 ? mult : mult * p.Get("splitMult", 0.5f), el, s.Gauge, DamageKind.Skill);
                d.BonusMult += bonus + PassiveBonus(h, c[i]);
                if (c[i].IsBoss || c[i].Elite) d.BonusMult += p.Get("eliteBonus");
                d.CanCrit = true;
                DealDamage(c[i], d);
            }
            ReturnList(c);
            if (p.Flag("keepRamp")) h.RampStacks /= 2; else h.RampStacks = 0;
            Emit(SimEventType.Strike, t.Pos, Element.Lightning, 0f, h.Uid, 0, "charged_shot", false, 0.8f);
            castPos = t.Pos;
            return true;
        }

        /// <summary>Frostbreaker: a lance that shatters frozen targets for a big burst, or deep-chills the rest.</summary>
        private bool CastShatterLance(HeroUnit h, SkillDef s, float mult, Element el, ref Vec2 castPos)
        {
            ParamBag p = s.Params;
            EnemyUnit t = null;
            List<EnemyUnit> c = RentList();
            QueryEnemies(h.Pos, h.Stat(StatId.Range) + 1.5f, c);
            for (int i = 0; i < c.Count && t == null; i++) if (c[i].Frozen) t = c[i];
            ReturnList(c);
            if (t == null) t = SelectTarget(h, TargetProfile.Cluster, 1f);
            if (t == null) return false;
            bool frozen = t.Frozen;
            DamageRequest d = DamageRequest.From(h, mult, el, frozen ? 0f : s.Gauge * p.Get("chillGauge", 2f), DamageKind.Skill);
            d.BonusMult += PassiveBonus(h, t) + (frozen ? p.Get("frozenBonus", 1.2f) : 0f);
            DealDamage(t, d);
            if (frozen)
            {
                t.StunTimer = 0f;
                t.Frozen = false;
                t.BrittleTimer = SimMath.Max(t.BrittleTimer, p.Get("brittleDuration", 3f));
                t.BrittleAmount = SimMath.Max(t.BrittleAmount, p.Get("brittle", 0.2f));
                List<EnemyUnit> shards = RentList();
                float r = p.Get("shardRadius", 1.6f);
                QueryEnemies(t.Pos, r, shards);
                Emit(SimEventType.Strike, t.Pos, Element.Ice, 0f, h.Uid, 0, "shatter_lance", false, r);
                for (int i = 0; i < shards.Count; i++)
                    if (shards[i] != t) DealDamage(shards[i], DamageRequest.From(h, mult * p.Get("shardMult", 0.6f), Element.Ice, 0.5f, DamageKind.Skill, 1));
                ReturnList(shards);
            }
            else if (p.Get("freeze") > 0f && t.Alive)
            {
                Stun(t, p.Get("freeze"));
                t.Frozen = t.StunTimer > 0f;
            }
            castPos = t.Pos;
            return true;
        }

        /// <summary>
        /// Tempest Oracle: drifts nearby persistent fields (bounded distance, never onto the crystal)
        /// toward the densest group, then gusts it. Walls/line fields stay put so lanes never get blocked.
        /// </summary>
        private bool CastZoneDrift(HeroUnit h, SkillDef s, float mult, float range, Element el, ref Vec2 castPos)
        {
            ParamBag p = s.Params;
            EnemyUnit t = SelectTarget(h, TargetProfile.Cluster, 1.5f);
            if (t == null) return false;
            float drift = p.Get("drift", 2f), reach = range + p.Get("reach", 3f);
            float minC = Crystal.Radius + 1.2f;
            int moved = 0;
            for (int i = 0; i < Zones.Count; i++)
            {
                Zone z = Zones[i];
                if (z.Line || z.HitsLeft > 0 || Vec2.Distance(z.Pos, h.Pos) > reach) continue;
                Vec2 to = Vec2.MoveTowards(z.Pos, t.Pos, drift);
                if (Vec2.Distance(to, Crystal.Pos) < minC) continue;
                z.Pos = to;
                z.Remaining += p.Get("extend");
                moved++;
            }
            List<EnemyUnit> hit = RentList();
            HitArea(h, s, t.Pos, p.Get("radius", 1.8f), mult, el, hit);
            ReturnList(hit);
            if (moved > 0) Emit(SimEventType.StatusApplied, t.Pos, Element.Wind, moved, h.Uid, 0, "zone_drift");
            SpawnSkillField(h, s, t.Pos, p.Get("fieldMult", 0.15f));
            castPos = t.Pos;
            return true;
        }

        /// <summary>Granite Fist: a crushing punch that cracks armour and sends an aftershock through the group.</summary>
        private bool CastFracturePunch(HeroUnit h, SkillDef s, float power, float mult, Element el, ref Vec2 castPos)
        {
            ParamBag p = s.Params;
            EnemyUnit t = h.Target != null && h.Target.Alive && Vec2.Distance(h.Target.Pos, h.Pos) <= h.Stat(StatId.Range) + 1.2f
                ? h.Target : SelectTarget(h, TargetProfile.NearestToCrystal, 0.8f);
            if (t == null) return false;
            DamageRequest d = DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill);
            d.BonusMult += PassiveBonus(h, t);
            DealDamage(t, d);
            int crackMax = (int)p.Get("crackMax", 2f);
            if (t.Alive) ApplyArmorCrack(t, 4f, (int)p.Get("cracks", 1f), crackMax);
            List<EnemyUnit> c = RentList();
            float r = p.Get("shockRadius", 1.5f);
            QueryEnemies(t.Pos, r, c);
            for (int i = 0; i < c.Count; i++)
            {
                if (c[i] == t) continue;
                DealDamage(c[i], DamageRequest.From(h, mult * p.Get("shockMult", 0.4f), el, 0.5f, DamageKind.Skill, 1));
                if (c[i].Alive && p.Flag("spreadCrack")) ApplyArmorCrack(c[i], 4f, 1, crackMax);
            }
            ReturnList(c);
            Emit(SimEventType.Strike, t.Pos, Element.Earth, 0f, h.Uid, 0, "fracture_punch", false, r);
            if (p.Get("shieldPct") > 0f) AddHeroShield(h, h.MaxHp * p.Get("shieldPct") * power, h);
            if (p.Get("taunt") > 0f) Taunt(h, r + 0.5f, p.Get("taunt"));
            castPos = t.Pos;
            return true;
        }

        // ------------------------------------------------------------------ Light / Shadow H2

        /// <summary>Sun Cantor: a radiant beam that sears and Illuminates enemies and heals allies it crosses.</summary>
        private bool CastSunBeam(HeroUnit h, SkillDef s, float power, float mult, float range, Element el, ref Vec2 castPos)
        {
            ParamBag p = s.Params;
            EnemyUnit t = SelectTarget(h, TargetProfile.Cluster, 1f);
            if (t == null) return false;
            Vec2 dir = (t.Pos - h.Pos).Normalized;
            Vec2 end = h.Pos + dir * (range + p.Get("extra", 2f));
            float width = p.Get("width", 0.6f);
            List<EnemyUnit> c = RentList();
            QueryEnemies((h.Pos + end) * 0.5f, Vec2.Distance(h.Pos, end) * 0.5f + width + 0.5f, c);
            for (int i = 0; i < c.Count; i++)
            {
                EnemyUnit e = c[i];
                if (Vec2.DistanceToSegment(e.Pos, h.Pos, end) > width + e.Radius) continue;
                DamageRequest d = DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill);
                d.BonusMult += PassiveBonus(h, e);
                DealDamage(e, d);
                if (e.Alive) Illuminate(e, p.Get("illuminate", 3f), 0.15f, 0.5f);
                if (e.Alive && p.Get("brittle") > 0f)
                {
                    e.BrittleTimer = SimMath.Max(e.BrittleTimer, 3f);
                    e.BrittleAmount = SimMath.Max(e.BrittleAmount, p.Get("brittle"));
                }
            }
            ReturnList(c);
            int healed = 0, maxHeal = (int)p.Get("healTargets", 1f);
            for (int i = 0; i < Heroes.Count && healed < maxHeal; i++)
            {
                HeroUnit a = Heroes[i];
                if (!a.Alive || a.HpFraction >= 0.99f || Vec2.DistanceToSegment(a.Pos, h.Pos - dir * 3f, end) > width + 1.5f) continue;
                HealHero(a, a.MaxHp * p.Get("healPct", 0.06f) * power, h);
                healed++;
            }
            if (healed == 0)
            {
                HeroUnit low = LowestHpAlly(h.Pos, range + 2f, 0.9f);
                if (low != null) HealHero(low, low.MaxHp * p.Get("healPct", 0.06f) * 0.5f * power, h);
            }
            Emit(SimEventType.Strike, end, Element.Light, 0f, h.Uid, 0, "sun_beam", false, width);
            castPos = t.Pos;
            return true;
        }

        /// <summary>Gloom Sentinel: a cursed mire around him that taunts and weakens enemies.</summary>
        private bool CastCurseMire(HeroUnit h, SkillDef s, float power, float mult, Element el, ref Vec2 castPos)
        {
            ParamBag p = s.Params;
            List<EnemyUnit> c = RentList();
            float r = p.Get("radius", 2.2f);
            QueryEnemies(h.Pos, r, c);
            if (c.Count == 0)
            {
                ReturnList(c);
                return false;
            }
            float lifesteal = p.Get("lifesteal");
            for (int i = 0; i < c.Count; i++)
            {
                float dealt = DealDamage(c[i], DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill));
                if (lifesteal > 0f) HealHero(h, dealt * lifesteal, h);
            }
            ReturnList(c);
            Taunt(h, r, p.Get("taunt", 1.5f));
            if (p.Get("shieldPct") > 0f) AddHeroShield(h, h.MaxHp * p.Get("shieldPct") * power, h);
            SpawnSkillField(h, s, h.Pos, 0.15f);
            castPos = h.Pos;
            return true;
        }

        // ================================================================== passives & hooks

        private float PassiveBonusH1(HeroUnit h, EnemyUnit e)
        {
            ParamBag p = h.PassiveParams;
            switch (h.PassiveKind)
            {
                case "spell_memory": return e.ResonantTimer > 0f ? p.Get("bonus", 0.25f) : 0f;
                case "event_horizon": return SimMath.Min(p.Get("cap", 0.3f), e.UnstableStacks * p.Get("perStack", 0.1f));
                case "scribe_ink": return e.MarkStacks * p.Get("perMark", 0.05f);
                case "tidecaller": return e.Aura[(int)Element.Water] > 0.05f ? p.Get("bonus", 0.25f) : 0f;
                case "arcshot": return e.Uid == h.RampTargetUid ? h.RampStacks * p.Get("perStack", 0.06f) : 0f;
                case "frostbreaker": return e.Chilled ? p.Get("bonus", 0.25f) : 0f;
                case "granite_body": return SimMath.Min(p.Get("cap", 0.4f), h.Stat(StatId.Defense) * p.Get("perDefense", 0.005f));
                case "radiant_hymn": return e.Illuminated ? p.Get("bonus", 0.15f) : 0f;
                default: return 0f;
            }
        }

        private void OnBasicAttackPassiveH1(HeroUnit h, EnemyUnit target)
        {
            ParamBag p = h.PassiveParams;
            switch (h.PassiveKind)
            {
                case "arcshot":
                    if (target == null) break;
                    if (h.RampTargetUid != target.Uid)
                    {
                        h.RampTargetUid = target.Uid; // retargeting resets the ramp
                        h.RampStacks = 0;
                    }
                    if (h.RampStacks < (int)p.Get("maxStacks", 6f)) h.RampStacks++;
                    break;
                case "scribe_ink":
                    if (target == null || !target.Alive) break;
                    AddMark(target, 1, h);
                    if (h.Skill.Kind == "ember_script") TryDetonateMarks(h, target);
                    break;
                case "radiant_hymn":
                {
                    h.ComboCount++;
                    if (h.ComboCount < (int)p.Get("every", 4f)) break;
                    h.ComboCount = 0;
                    HeroUnit low = LowestHpAlly(h.Pos, p.Get("radius", 5f), 0.95f);
                    if (low != null) HealHero(low, low.MaxHp * p.Get("healPct", 0.03f), h);
                    break;
                }
            }
        }

        private void TickPassiveH1(HeroUnit h, float dt)
        {
            if (h.EchoPrimed > 0f)
            {
                h.EchoPrimed -= dt;
                if (h.EchoPrimed <= 0f) h.EchoCharges = 0;
            }
            if (h.PassiveKind == "tempest_oracle")
            {
                float r = h.PassiveParams.Get("radius", 3.5f);
                for (int i = 0; i < Heroes.Count; i++)
                {
                    HeroUnit a = Heroes[i];
                    if (a.Alive && Vec2.Distance(a.Pos, h.Pos) <= r) AddBuff(a, StatId.AttackInterval, h.PassiveParams.Get("haste", 0.08f), 0.5f, "tempest_oracle");
                }
            }
        }

        /// <summary>Rune Conductor passive: every N reactions refund part of her own cooldown (bounded, no loop).</summary>
        private void NotifyReactionPassivesH1()
        {
            for (int i = 0; i < Heroes.Count; i++)
            {
                HeroUnit h = Heroes[i];
                if (!h.Alive || h.PassiveKind != "rune_conductor") continue;
                h.PassiveStacks++;
                if (h.PassiveStacks < (int)h.PassiveParams.Get("every", 4f)) continue;
                h.PassiveStacks = 0;
                h.SkillTimer = SimMath.Max(0f, h.SkillTimer - h.PassiveParams.Get("refund", 0.8f));
            }
        }

        /// <summary>
        /// Gloom Sentinel: takes a share of the damage aimed at a badly hurt ally nearby (internal
        /// cooldown, never below 25% of his own HP). Returns the damage the ally still takes.
        /// </summary>
        private float GloomRedirect(HeroUnit target, float amount)
        {
            if (target.HpFraction > 0.5f) return amount;
            for (int i = 0; i < Heroes.Count; i++)
            {
                HeroUnit g = Heroes[i];
                if (g == target || !g.Alive || g.PassiveKind != "gloom_guard" || g.RedirectTimer > 0f || g.HpFraction < 0.25f) continue;
                if (Vec2.Distance(g.Pos, target.Pos) > g.PassiveParams.Get("radius", 3f)) continue;
                g.RedirectTimer = g.PassiveParams.Get("cooldown", 0.5f);
                float share = amount * g.PassiveParams.Get("share", 0.35f);
                g.Hp = SimMath.Max(1f, g.Hp - share * (1f - g.PassiveParams.Get("selfReduction", 0.3f)));
                return amount - share;
            }
            return amount;
        }
    }
}
