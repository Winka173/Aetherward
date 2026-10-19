using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    /// <summary>
    /// Expansion hero skill kinds and passives. Like the launch kinds, behaviour is selected by the
    /// skill/passive "kind" from data; numbers come from params. No hero id is ever inspected.
    /// </summary>
    public sealed partial class Battle
    {
        // ================================================================== skills

        private bool CastSkillExt(HeroUnit h, SkillDef s, float power, float mult, float range, Element el, ref Vec2 castPos)
        {
            switch (s.Kind)
            {
                case "dawn_aegis": return CastDawnAegis(h, s, power, mult, el, ref castPos);
                case "oath_of_doom": return CastOathOfDoom(h, s, mult, range, el, ref castPos);
                case "phoenix_slash": return CastPhoenixSlash(h, s, mult, el, ref castPos);
                case "tide_blessing": return CastTideBlessing(h, s, power, mult, range, el, ref castPos);
                case "deploy_pylon": return CastDeployPylon(h, s, mult, range, ref castPos);
                case "frost_aegis": return CastFrostAegis(h, s, power, ref castPos);
                case "gust_step": return CastGustStep(h, s, mult, el, ref castPos);
                case "raise_wall": return CastRaiseWall(h, s, mult, ref castPos);
                default:
                {
                    bool cast = CastSkillNature(h, s, power, mult, el, ref castPos, out bool handled);
                    if (handled) return cast;
                    cast = CastSkillH1(h, s, power, mult, range, el, ref castPos, out handled);
                    return handled && cast;
                }
            }
        }

        /// <summary>Dawn Warden: shield the most hurt ally, cleanse nearby allies, sear and Illuminate enemies around her.</summary>
        private bool CastDawnAegis(HeroUnit h, SkillDef s, float power, float mult, Element el, ref Vec2 castPos)
        {
            ParamBag p = s.Params;
            HeroUnit ally = LowestHpAlly(h.Pos, p.Get("allyRange", 4.5f), p.Get("shieldBelow", 0.95f));
            List<EnemyUnit> c = RentList();
            QueryEnemies(h.Pos, p.Get("radius", 2.6f), c);
            if (ally == null && c.Count == 0)
            {
                ReturnList(c);
                return false;
            }
            if (ally == null) ally = h;
            AddHeroShield(ally, ally.MaxHp * p.Get("shieldPct", 0.22f) * power, h);
            float allPct = p.Get("allShieldPct");
            if (allPct > 0f)
                for (int i = 0; i < Heroes.Count; i++)
                {
                    HeroUnit a = Heroes[i];
                    if (a != ally && a.Alive && Vec2.Distance(a.Pos, h.Pos) <= p.Get("allRadius", 3.2f)) AddHeroShield(a, a.MaxHp * allPct * power, h);
                }
            if (p.Get("crystalShield") > 0f) ShieldCrystal(Crystal.MaxHp * p.Get("crystalShield") * power);
            for (int i = 0; i < Heroes.Count; i++)
                if (Heroes[i].Alive && Vec2.Distance(Heroes[i].Pos, h.Pos) <= p.Get("cleanseRadius", 2.8f)) CleanseHero(Heroes[i]);
            DetachNear(h.Pos, p.Get("cleanseRadius", 2.8f) + 1f);
            for (int i = 0; i < c.Count; i++)
            {
                EnemyUnit e = c[i];
                DamageRequest d = DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill);
                if (e.Illuminated) d.BonusMult += p.Get("illuminatedBonus");
                DealDamage(e, d);
            }
            float purge = p.Get("purgeRadius");
            if (purge > 0f)
            {
                QueryEnemies(h.Pos, purge, c);
                for (int i = 0; i < c.Count; i++)
                {
                    EnemyUnit e = c[i];
                    e.Shield = 0f;
                    e.SpeedBuff = e.ArmorBuff = 0f;
                    Illuminate(e, 4f, p.Get("purgeWeaken", 0.2f), 1f);
                }
                Emit(SimEventType.Strike, h.Pos, Element.Light, 0f, h.Uid, 0, "purge", false, purge);
            }
            ReturnList(c);
            castPos = ally.Pos;
            return true;
        }

        /// <summary>Oathbinder: binds several enemies with Doom (elites first); Doom executes them below the threshold.</summary>
        private bool CastOathOfDoom(HeroUnit h, SkillDef s, float mult, float range, Element el, ref Vec2 castPos)
        {
            ParamBag p = s.Params;
            List<EnemyUnit> c = RentList();
            QueryEnemies(h.Anchor, range, c);
            bool elitesOnly = p.Flag("elitesOnly");
            for (int i = c.Count - 1; i >= 0; i--)
                if (!c[i].Alive || (elitesOnly && !c[i].Elite && !c[i].IsBoss)) c.RemoveAt(i);
            if (c.Count == 0 && elitesOnly)
            {
                QueryEnemies(h.Anchor, range, c); // nothing elite in range: fall back to anything
                for (int i = c.Count - 1; i >= 0; i--) if (!c[i].Alive) c.RemoveAt(i);
            }
            if (c.Count == 0)
            {
                ReturnList(c);
                return false;
            }
            c.Sort((a, b) =>
            {
                int ea = (a.IsBoss ? 2 : 0) + (a.Elite ? 1 : 0), eb = (b.IsBoss ? 2 : 0) + (b.Elite ? 1 : 0);
                if (ea != eb) return eb.CompareTo(ea);
                int d = RemainingPath(a).CompareTo(RemainingPath(b));
                return d != 0 ? d : a.Uid.CompareTo(b.Uid);
            });
            int marks = System.Math.Min(c.Count, (int)p.Get("marks", 3f));
            for (int i = 0; i < marks; i++)
            {
                EnemyUnit e = c[i];
                AddDoom(e, (int)p.Get("doomStacks", 2f), h);
                if (p.Get("brittle") > 0f) ApplyStatus(e, "brittle", p, 1f, h, 0);
                Emit(SimEventType.Strike, e.Pos, Element.Shadow, 0f, h.Uid, e.Uid, "oath", false, 0.5f);
                Journal.Pending[Journal.Pending.Count - 1] = WithFrom(Journal.Pending[Journal.Pending.Count - 1], h.Pos);
                DamageRequest d = DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill);
                d.BonusMult += PassiveBonus(h, e);
                DealDamage(e, d);
            }
            castPos = c[0].Pos;
            ReturnList(c);
            return true;
        }

        /// <summary>Phoenix Knight: fiery sweep around herself that builds Heat.</summary>
        private bool CastPhoenixSlash(HeroUnit h, SkillDef s, float mult, Element el, ref Vec2 castPos)
        {
            EnemyUnit t = h.Target;
            if (t == null || Vec2.Distance(h.Pos, t.Pos) > AttackReach(h, t) + 0.6f) return false;
            List<EnemyUnit> c = RentList();
            QueryEnemies(h.Pos, s.Params.Get("radius", 1.6f), c);
            for (int i = 0; i < c.Count; i++) DealDamage(c[i], DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill));
            ReturnList(c);
            if (s.Params.Get("taunt") > 0f) Taunt(h, s.Params.Get("tauntRadius", 2.2f), s.Params.Get("taunt"));
            AddHeat(h, s.Params.Get("heat", 25f));
            castPos = h.Pos;
            return true;
        }

        /// <summary>Tide Oracle: soaks a cluster Wet (optionally catalysing reactions) and heals the most hurt allies.</summary>
        private bool CastTideBlessing(HeroUnit h, SkillDef s, float power, float mult, float range, Element el, ref Vec2 castPos)
        {
            ParamBag p = s.Params;
            EnemyUnit t = SelectTarget(h, TargetProfile.Cluster, 0.5f);
            HeroUnit hurt = LowestHpAlly(h.Pos, range + 2.5f, p.Get("healBelow", 0.92f));
            if (t == null && hurt == null) return false;
            if (t != null)
            {
                List<EnemyUnit> c = RentList();
                QueryEnemies(t.Pos, p.Get("radius", 2.2f), c);
                for (int i = 0; i < c.Count; i++)
                {
                    EnemyUnit e = c[i];
                    DealDamage(e, DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill));
                    if (e.Alive && p.Get("reactionVuln") > 0f)
                    {
                        e.ReactionVulnTimer = SimMath.Max(e.ReactionVulnTimer, p.Get("vulnDuration", 4f));
                        e.ReactionVulnAmount = SimMath.Max(e.ReactionVulnAmount, p.Get("reactionVuln"));
                    }
                }
                ReturnList(c);
                castPos = t.Pos;
            }
            else castPos = hurt.Pos;
            // Heal the N most hurt allies in reach (distinct heroes, deterministic order).
            var hurtList = new List<HeroUnit>();
            for (int i = 0; i < Heroes.Count; i++)
                if (Heroes[i].Alive && Heroes[i].HpFraction < 0.999f && Vec2.Distance(Heroes[i].Pos, h.Pos) <= range + 2.5f) hurtList.Add(Heroes[i]);
            hurtList.Sort((a, b) => { int d = a.HpFraction.CompareTo(b.HpFraction); return d != 0 ? d : a.Uid.CompareTo(b.Uid); });
            int targets = System.Math.Min(hurtList.Count, (int)p.Get("healTargets", 2f));
            for (int k = 0; k < targets; k++) HealHero(hurtList[k], hurtList[k].MaxHp * p.Get("healPct", 0.08f) * power, h);
            return true;
        }

        /// <summary>Storm Engineer: deploys a conductive pylon near the densest enemies (never on the crystal).</summary>
        private bool CastDeployPylon(HeroUnit h, SkillDef s, float mult, float range, ref Vec2 castPos)
        {
            EnemyUnit t = SelectTarget(h, TargetProfile.Cluster, 1f);
            if (t == null) return false;
            if (!Content.Fields.TryGetValue(s.Params.GetString("field", "pylon"), out FieldDef f)) return false;
            Vec2 pos = t.Pos;
            Vec2 off = pos - h.Anchor;
            if (off.Length > range) pos = h.Anchor + off.Normalized * range;
            float minC = Crystal.Radius + s.Params.Get("minCrystal", 1.6f);
            if (Vec2.Distance(pos, Crystal.Pos) < minC) pos = Crystal.Pos + (pos - Crystal.Pos).Normalized * minC;
            SpawnField(f, pos, s.Params.Get("radius", 2.2f), s.Params.Get("duration", 8f), h, h.Stat(StatId.Attack) * mult, 0, s.Kind, null);
            castPos = pos;
            return true;
        }

        /// <summary>Frost Paladin: shields herself and the most endangered ally; a broken shield explodes in frost.</summary>
        private bool CastFrostAegis(HeroUnit h, SkillDef s, float power, ref Vec2 castPos)
        {
            ParamBag p = s.Params;
            HeroUnit ally = null;
            float worst = 0.95f;
            for (int i = 0; i < Heroes.Count; i++)
            {
                HeroUnit a = Heroes[i];
                if (a == h || !a.Alive || Vec2.Distance(a.Pos, h.Pos) > p.Get("allyRange", 3.5f)) continue;
                float f = a.HpFraction - (EngagedCount(a) > 0 ? 0.3f : 0f);
                if (f < worst) { worst = f; ally = a; }
            }
            bool threatened = h.Target != null || h.HpFraction < 0.9f || ally != null;
            if (!threatened) return false;
            float burst = h.Stat(StatId.Attack) * p.Get("burstMult", 1.4f);
            AddHeroShield(h, h.MaxHp * p.Get("shieldPct", 0.18f) * power, h);
            h.ShieldGiverUid = h.Uid;
            h.ShieldBurst = burst;
            if (ally != null)
            {
                AddHeroShield(ally, ally.MaxHp * p.Get("allyShieldPct", 0.2f) * power, h);
                ally.ShieldGiverUid = h.Uid;
                ally.ShieldBurst = burst;
            }
            if (p.Get("crystalShield") > 0f) ShieldCrystal(Crystal.MaxHp * p.Get("crystalShield") * power);
            if (p.Get("taunt") > 0f) Taunt(h, p.Get("tauntRadius", 2f), p.Get("taunt"));
            castPos = ally != null ? ally.Pos : h.Pos;
            return true;
        }

        private int EngagedCount(HeroUnit h)
        {
            int n = 0;
            for (int i = 0; i < Enemies.Count; i++) if (Enemies[i].Alive && Enemies[i].Engaged == h) n++;
            return n;
        }

        /// <summary>A shield granted by a Frost Paladin broke: frost burst around the shielded hero.</summary>
        private void FrostBurst(HeroUnit shielded)
        {
            HeroUnit giver = HeroByUid(shielded.ShieldGiverUid);
            float power = shielded.ShieldBurst;
            shielded.ShieldGiverUid = 0;
            shielded.ShieldBurst = 0f;
            if (giver == null || power <= 0f) return;
            ParamBag p = giver.Skill.Params;
            float radius = p.Get("burstRadius", 2f);
            List<EnemyUnit> c = RentList();
            QueryEnemies(shielded.Pos, radius, c);
            Emit(SimEventType.Strike, shielded.Pos, Element.Ice, 0f, giver.Uid, 0, "frost_burst", false, radius);
            for (int i = 0; i < c.Count; i++)
            {
                EnemyUnit e = c[i];
                var d = new DamageRequest { Source = giver, Attack = power, Multiplier = 1f, Element = Element.Ice, Gauge = p.Get("burstGauge", 1f), Kind = DamageKind.Skill };
                if (e.Frozen) d.BonusMult += p.Get("frozenBonus");
                DealDamage(e, d);
                if (!e.Alive) continue;
                Slow(e, 0.35f, 2f);
                if (p.Get("burstStun") > 0f) Stun(e, p.Get("burstStun"));
            }
            ReturnList(c);
        }

        /// <summary>Gale Dancer: dashes into a group, gusts enemies together and primes Slipstream.</summary>
        private bool CastGustStep(HeroUnit h, SkillDef s, float mult, Element el, ref Vec2 castPos)
        {
            ParamBag p = s.Params;
            bool single = p.Flag("single");
            EnemyUnit t = SelectTarget(h, single ? TargetProfile.Elite : TargetProfile.Cluster, 0.5f);
            if (t == null) return false;
            h.Pos = ClampToLeash(h, t.Pos - (t.Pos - h.Pos).Normalized * (t.Radius + h.Radius));
            if (single)
            {
                DamageRequest d = DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill);
                d.BonusMult += PassiveBonus(h, t) + (t.HpFraction < p.Get("executeBelow", 0.3f) ? p.Get("executeBonus", 0.6f) : 0f);
                DealDamage(t, d);
            }
            else
            {
                List<EnemyUnit> c = RentList();
                QueryEnemies(t.Pos, p.Get("pullRadius", 2f), c);
                for (int i = 0; i < c.Count; i++)
                {
                    Pull(c[i], t.Pos, p.Get("pull", 3f), 0.4f);
                    DealDamage(c[i], DamageRequest.From(h, mult, el, s.Gauge, DamageKind.Skill));
                }
                ReturnList(c);
                if (p.Get("vortex") > 0f)
                {
                    SpawnZone(ZoneKind.Vortex, t.Pos, 1.6f, p.Get("vortex"), h, Element.Wind, 0.3f, 0, null);
                    SpreadAuras(t.Pos, 2f, h);
                }
            }
            if (h.PassiveKind == "slipstream") h.PassiveStacks = (int)h.PassiveParams.Get("hits", 3f);
            castPos = t.Pos;
            return true;
        }

        /// <summary>
        /// Stone Architect: raises a temporary wall across the lead enemy's path. Walls slow and grind
        /// but never block outright, and are never placed next to the crystal (paths stay valid).
        /// </summary>
        private bool CastRaiseWall(HeroUnit h, SkillDef s, float mult, ref Vec2 castPos)
        {
            ParamBag p = s.Params;
            EnemyUnit t = SelectTarget(h, TargetProfile.NearestToCrystal, 2f);
            if (t == null || !Content.Fields.TryGetValue(p.GetString("field", "stone_wall"), out FieldDef f)) return false;
            Vec2 dir = t.Facing.SqrLength > 0.01f ? t.Facing.Normalized : (Crystal.Pos - t.Pos).Normalized;
            Vec2 center = t.Pos + dir * p.Get("ahead", 1.2f);
            float minC = Crystal.Radius + p.Get("minCrystal", 2f);
            if (Vec2.Distance(center, Crystal.Pos) < minC) center = Crystal.Pos + (center - Crystal.Pos).Normalized * minC;
            Vec2 perp = new Vec2(-dir.Y, dir.X) * p.Get("halfLength", 1.2f);
            SpawnField(f, center - perp, p.Get("width", 0.45f), p.Get("duration", 4.5f), h, h.Stat(StatId.Attack) * mult, 0, s.Kind, center + perp);
            castPos = center;
            return true;
        }

        // ================================================================== passives

        private void ApplyBattleStartPassiveExt(HeroUnit h)
        {
            if (h.PassiveKind == "phoenix_heat") h.Heat = 0f;
        }

        private void TickPassiveExt(HeroUnit h, float dt)
        {
            TickPassiveH1(h, dt);
            switch (h.PassiveKind)
            {
                case "overclock":
                {
                    int pylons = 0;
                    for (int i = 0; i < Zones.Count; i++)
                        if (Zones[i].Owner == h && Zones[i].Field != null && Zones[i].Field.Params.Flag("pylon")) pylons++;
                    if (pylons > 0) AddBuff(h, StatId.AttackInterval, pylons * h.PassiveParams.Get("perPylon", 0.08f), 0.5f, "overclock");
                    break;
                }
                case "fortify":
                {
                    for (int i = 0; i < Zones.Count; i++)
                    {
                        if (Zones[i].Owner != h || Zones[i].Field == null || !Zones[i].Field.Params.Flag("wall")) continue;
                        Crystal.TempReduction = SimMath.Max(Crystal.TempReductionTimer > 0f ? Crystal.TempReduction : 0f, h.PassiveParams.Get("reduction", 0.08f));
                        Crystal.TempReductionTimer = SimMath.Max(Crystal.TempReductionTimer, 0.25f);
                        break;
                    }
                    break;
                }
            }
        }

        private float PassiveBonusExt(HeroUnit h, EnemyUnit e)
        {
            switch (h.PassiveKind)
            {
                case "purifying_light": return e.Illuminated ? h.PassiveParams.Get("bonus", 0.25f) : 0f;
                case "binding_oath": return e.DoomStacks > 0 ? h.PassiveParams.Get("bonusPerDoom", 0.04f) * e.DoomStacks : 0f;
                case "covenant": return (e.IsBoss || e.Elite) ? h.PassiveParams.Get("bonusPerDoom", 0.06f) * e.DoomStacks : 0f;
                case "slipstream": return h.PassiveStacks > 0 ? h.PassiveParams.Get("bonus", 0.4f) : 0f;
                default: return PassiveBonusNature(h, e);
            }
        }

        private void OnBasicAttackPassiveExt(HeroUnit h, EnemyUnit target)
        {
            OnBasicAttackPassiveH1(h, target);
            switch (h.PassiveKind)
            {
                case "phoenix_heat":
                    AddHeat(h, h.PassiveParams.Get("hitHeat", 3f));
                    break;
                case "slipstream":
                    if (h.PassiveStacks > 0) h.PassiveStacks--;
                    break;
                case "shatter_rhythm":
                {
                    h.ComboCount++;
                    if (h.ComboCount < (int)h.PassiveParams.Get("every", 3f) || target == null) break;
                    h.ComboCount = 0;
                    List<EnemyUnit> c = RentList();
                    float r = h.PassiveParams.Get("radius", 1.4f);
                    QueryEnemies(target.Pos, r, c);
                    Emit(SimEventType.Strike, target.Pos, Element.Ice, 0f, h.Uid, 0, "frost_slam", false, r);
                    for (int i = 0; i < c.Count; i++)
                        DealDamage(c[i], DamageRequest.From(h, h.PassiveParams.Get("mult", 0.8f), Element.Ice, 0.6f, DamageKind.Skill));
                    ReturnList(c);
                    break;
                }
            }
        }

        private void OnHeroHitExt(HeroUnit h, EnemyUnit attacker)
        {
            ThornsOnHit(h, attacker);
            if (h.PassiveKind == "glacial_resolve" && h.Shield > 0f && attacker.Alive)
            {
                Slow(attacker, h.PassiveParams.Get("slow", 0.2f), 1f);
                attacker.Aura[(int)Element.Ice] = SimMath.Max(attacker.Aura[(int)Element.Ice], 0.4f);
            }
        }

        /// <summary>Heat (Phoenix Knight): fills from hits dealt/taken; at 100 releases a fire burst.</summary>
        private void AddHeat(HeroUnit h, float amount)
        {
            if (h.PassiveKind != "phoenix_heat" || !h.Alive || amount <= 0f) return;
            h.Heat += amount;
            if (h.Heat < 100f) return;
            h.Heat = 0f;
            HeatBurst(h, h.PassiveParams.Get("burstMult", 1.8f));
        }

        private void HeatBurst(HeroUnit h, float mult)
        {
            ParamBag p = h.PassiveParams;
            float r = p.Get("burstRadius", 2.2f);
            List<EnemyUnit> c = RentList();
            QueryEnemies(h.Pos, r, c);
            Emit(SimEventType.Strike, h.Pos, Element.Fire, 0f, h.Uid, 0, "heat_burst", false, r);
            for (int i = 0; i < c.Count; i++)
            {
                DealDamage(c[i], DamageRequest.From(h, mult, Element.Fire, 1f, DamageKind.Skill));
                if (c[i].Alive) ApplyBurn(c[i], h, 3f);
            }
            ReturnList(c);
            float ward = p.Get("wardShield");
            if (ward > 0f)
                for (int i = 0; i < Heroes.Count; i++)
                    if (Heroes[i].Alive && Vec2.Distance(Heroes[i].Pos, h.Pos) <= p.Get("wardRadius", 3f)) AddHeroShield(Heroes[i], Heroes[i].MaxHp * ward, h);
        }

        /// <summary>Once-per-wave rebirth for heroes whose passive declares it. Returns true if the hero rose again.</summary>
        private bool TryRebirth(HeroUnit h)
        {
            if (h.PassiveKind != "phoenix_heat" || h.ReviveUsedThisWave) return false;
            float hp = h.PassiveParams.Get("rebirth");
            if (hp <= 0f) return false;
            h.ReviveUsedThisWave = true;
            h.Hp = h.MaxHp * hp;
            h.Heat = 0f;
            Emit(SimEventType.HeroRevived, h.Pos, Element.Fire, h.Hp, 0, h.Uid, "rebirth");
            float burst = h.PassiveParams.Get("rebirthBurst");
            if (burst > 0f) HeatBurst(h, burst);
            else if (h.PassiveParams.Get("wardShield") > 0f) HeatBurst(h, 0.5f);
            if (h.PassiveParams.Get("rebirthCrystalShield") > 0f) ShieldCrystal(Crystal.MaxHp * h.PassiveParams.Get("rebirthCrystalShield"));
            return true;
        }

        /// <summary>Reaction-counting passives (Tide Oracle) tick on every reaction in the battle.</summary>
        private void NotifyReactionPassives()
        {
            NotifyReactionPassivesH1();
            for (int i = 0; i < Heroes.Count; i++)
            {
                HeroUnit h = Heroes[i];
                if (!h.Alive || (h.PassiveKind != "reaction_tide" && h.PassiveKind != "catalyst_tide")) continue;
                h.PassiveStacks++;
                if (h.PassiveStacks < (int)h.PassiveParams.Get("every", 8f)) continue;
                h.PassiveStacks = 0;
                Emit(SimEventType.StatusApplied, h.Pos, Element.Water, 0f, h.Uid, h.Uid, h.PassiveKind);
                if (h.PassiveKind == "reaction_tide")
                {
                    for (int k = 0; k < Heroes.Count; k++) HealHero(Heroes[k], Heroes[k].MaxHp * h.PassiveParams.Get("healPct", 0.05f), h);
                    HealCrystal(Crystal.MaxHp * h.PassiveParams.Get("crystalPct", 0.004f));
                }
                else
                {
                    float sec = h.PassiveParams.Get("refund", 0.5f);
                    for (int k = 0; k < Heroes.Count; k++) Heroes[k].SkillTimer = SimMath.Max(0f, Heroes[k].SkillTimer - sec);
                }
            }
        }

        /// <summary>Doom execution credited to a hero: Oathbinder passives react.</summary>
        private void OnDoomExecuted(HeroUnit credit, EnemyUnit victim)
        {
            if (credit == null) return;
            if (credit.PassiveKind == "binding_oath" || credit.PassiveKind == "covenant")
                credit.SkillTimer *= 1f - credit.PassiveParams.Get("refund", 0.25f);
            int spread = (int)credit.Skill.Params.Get("verdictSpread");
            if (spread <= 0) return;
            List<EnemyUnit> c = RentList();
            QueryEnemies(victim.Pos, 2.5f, c);
            int n = 0;
            for (int i = 0; i < c.Count && n < 2; i++)
            {
                if (c[i] == victim || !c[i].Alive) continue;
                AddDoom(c[i], spread, credit);
                n++;
            }
            ReturnList(c);
        }

        /// <summary>Field links (pylons): enemies near the segment between two linked fields take damage.</summary>
        private void UpdateFieldLinks(Zone z)
        {
            FieldDef f = z.Field;
            float linkMult = f.Params.Get("linkMult");
            if (linkMult <= 0f) return;
            float linkRange = f.Params.Get("linkRange", 4.5f);
            for (int i = 0; i < Zones.Count; i++)
            {
                Zone o = Zones[i];
                if (o == z || o.Field != f || o.Owner != z.Owner || o.Uid < z.Uid) continue;
                float d = Vec2.Distance(z.Pos, o.Pos);
                if (d > linkRange || d < 0.5f) continue;
                List<EnemyUnit> c = RentList();
                QueryEnemies(Vec2.Lerp(z.Pos, o.Pos, 0.5f), d * 0.5f + 0.6f, c);
                Emit(SimEventType.Strike, o.Pos, Element.Lightning, 0f, z.Owner?.Uid ?? 0, 0, "link", false, 0f, z.Generation);
                Journal.Pending[Journal.Pending.Count - 1] = WithFrom(Journal.Pending[Journal.Pending.Count - 1], z.Pos);
                for (int k = 0; k < c.Count; k++)
                {
                    EnemyUnit e = c[k];
                    if (Vec2.DistanceToSegment(e.Pos, z.Pos, o.Pos) > 0.5f + e.Radius) continue;
                    DealDamage(e, new DamageRequest { Source = z.Owner, Attack = z.Power, Multiplier = linkMult, Element = f.Element, Kind = DamageKind.Skill, Generation = 1, SourceTag = z.Tag });
                }
                ReturnList(c);
            }
        }
    }
}
