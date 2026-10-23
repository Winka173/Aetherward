using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    /// <summary>Everything a single hit needs; source attack is snapshotted at creation.</summary>
    public struct DamageRequest
    {
        public HeroUnit Source;
        public float Attack;        // snapshot of source attack (or flat power for triggers)
        public float Multiplier;
        public Element Element;
        public float Gauge;         // element units to apply after the hit (0 = none)
        public DamageKind Kind;
        public int Generation;      // 0 = direct; reactions/secondary effects increment
        public bool CanCrit;
        public float BonusMult;     // conditional bonuses already resolved by the caller
        public string ReactionId;   // set for reaction damage (stats + reaction-specific mods)
        public string SourceTag;    // relic/card id for trigger damage attribution
        public bool IgnoreDefense;

        public static DamageRequest From(HeroUnit src, float mult, Element el, float gauge, DamageKind kind, int gen = 0)
        {
            return new DamageRequest
            {
                Source = src,
                Attack = src != null ? src.Stat(StatId.Attack) : 0f,
                Multiplier = mult,
                Element = el,
                Gauge = gauge,
                Kind = kind,
                Generation = gen,
                CanCrit = kind == DamageKind.Basic || kind == DamageKind.Skill,
                BonusMult = 0f
            };
        }
    }

    public sealed partial class Battle
    {
        private readonly Stack<List<EnemyUnit>> _listPool = new Stack<List<EnemyUnit>>();
        /// <summary>Battle-wide readiness for reactions with a "worldCooldown" (team-buff reactions).</summary>
        private readonly Dictionary<string, float> _worldReactionReady = new Dictionary<string, float>();

        /// <summary>Re-entrancy-safe scratch list: nested reactions/triggers each get their own.</summary>
        public List<EnemyUnit> RentList() => _listPool.Count > 0 ? _listPool.Pop() : new List<EnemyUnit>(32);

        public void ReturnList(List<EnemyUnit> list)
        {
            list.Clear();
            _listPool.Push(list);
        }

        // Documented damage order (Docs/BALANCE.md):
        //   raw = Attack * Multiplier
        //   * (1 + DamageBonus + conditional bonuses)       [direct hits]
        //   * (1 + ReactionBonus + EM bonus + reaction mods) [reaction hits]
        //   * crit (chance capped 75%, multiplier capped 4x) [direct hits only]
        //   * 100 / (100 + max(0, effective defense))        [reactions ignore defense]
        //   * (1 - clamp(resist - shred, -0.5, 0.75))
        //   * vulnerability, then shield absorbs before HP.
        public float DealDamage(EnemyUnit target, DamageRequest req)
        {
            if (target == null || !target.Alive || target.Burrowed) return 0f;
            if (target.Invulnerable > 0f)
            {
                Emit(SimEventType.Miss, target.Pos, req.Element, 0f, req.Source?.Uid ?? 0, target.Uid, "immune");
                return 0f;
            }

            float raw = req.Attack * req.Multiplier * GateHoldBonus(req.Source);
            bool crit = false;
            HeroUnit src = req.Source;

            if (req.Kind == DamageKind.Reaction)
            {
                float em = src != null ? src.Stat(StatId.ElementalMastery) : 0f;
                float emBonus = 2.0f * em / (em + 150f);
                float bonus = (src != null ? src.Stat(StatId.ReactionBonus) : 0f) + emBonus + Mods.ReactionDamageAll + _activeReactionBonus;
                if (target.ReactionVulnTimer > 0f) bonus += target.ReactionVulnAmount;
                if (target.FieldTimer > 0f) bonus += target.FieldReactionAmp;
                if (req.ReactionId != null)
                {
                    ReactionMod m = Mods.ModFor(req.ReactionId);
                    if (m != null) bonus += m.DamagePct;
                    ReactionMod all = Mods.ModFor("*");
                    if (all != null) bonus += all.DamagePct;
                }
                raw *= 1f + bonus + req.BonusMult;
            }
            else
            {
                float bonus = (src != null ? src.Stat(StatId.DamageBonus) : 0f) + req.BonusMult + TraitDamageBonus(src, target);
                if (req.Kind == DamageKind.Skill && src != null) raw *= src.Stat(StatId.SkillPower);
                raw *= 1f + bonus;
                if (req.CanCrit && src != null)
                {
                    float cc = SimMath.Clamp(src.Stat(StatId.CritChance), 0f, 0.75f);
                    if (Rng.Chance(cc))
                    {
                        crit = true;
                        raw *= SimMath.Clamp(src.Stat(StatId.CritMultiplier), 1f, 4f);
                    }
                }
            }

            if (!req.IgnoreDefense && req.Kind != DamageKind.Reaction)
            {
                float def = EffectiveDefense(target);
                raw *= 100f / (100f + SimMath.Max(0f, def));
            }

            float resist = target.Resist[(int)req.Element];
            if (target.SuperconductTimer > 0f) resist -= 0.25f;
            if (target.ShieldFront && req.Kind != DamageKind.Dot && src != null)
            {
                // Shieldbearers block frontal hits: attacks from the direction they walk lose 60%.
                Vec2 toSource = (src.Pos - target.Pos).Normalized;
                if (Vec2.Dot(toSource, target.Facing) > 0.35f) resist += 0.6f;
            }
            raw *= 1f - SimMath.Clamp(resist, -0.5f, 0.75f);
            raw *= MechanicDamageTaken(target, req) * MechanicDamageTakenP4(target, req);
            // Latched parasites shrug off damage unless a hero guards the core (Light always connects).
            if (target.Latched && req.Element != Element.Light && !CoreGuarded) raw *= 0.4f;

            float vuln = 1f;
            if (target.VulnerableTimer > 0f) vuln += target.VulnerableAmount;
            if (target.HasAura(Element.Wind) && req.Element == Element.Wind) vuln += 0.1f;
            if (target.BrittleTimer > 0f) vuln += target.BrittleAmount;
            if (target.IlluminatedTimer > 0f) vuln += Mods.Rule("illuminate_power");
            if (target.FieldTimer > 0f) vuln += target.FieldVuln;
            if (target.IsBoss && target.DoomStacks > 0) vuln += target.DoomStacks * (0.03f + Mods.Rule("doom_boss"));
            raw *= vuln;
            if (raw < 1f) raw = 1f;

            float absorbed = 0f;
            if (target.Shield > 0f)
            {
                absorbed = SimMath.Min(target.Shield, raw);
                target.Shield -= absorbed;
            }
            float dealt = RedirectLinkedDamage(target, raw - absorbed);
            float hpBefore = target.Hp;
            target.Hp -= dealt;
            target.HitFlash = 0.12f;
            float effective = SimMath.Min(hpBefore, dealt) + absorbed;

            if (src != null) src.DamageDealt += effective;
            Stats.DamageByKind[(int)req.Kind] += effective;
            if (req.Generation > Stats.MaxProcDepth) Stats.MaxProcDepth = req.Generation;
            target.AdaptDamage[(int)req.Element] += effective;
            Stats.ElementDamage[(int)req.Element] += effective;
            if (req.ReactionId != null) Stats.AddReactionDamage(req.ReactionId, effective);
            if (req.SourceTag != null) Stats.AddSourceDamage(req.SourceTag, effective);
            Emit(SimEventType.Hit, target.Pos, req.Element, raw, src?.Uid ?? 0, target.Uid, req.ReactionId, crit, 0f, req.Generation);

            if (crit && src != null) FireTrigger("crit", src, target, target.Pos, null);
            OnMechanicHit(target, req);
            ReflectSkill(target, req, effective);

            if (target.Hp <= 0f)
            {
                KillEnemy(target, src);
            }
            else if (target.DoomStacks > 0 && TryDoomExecute(target, src))
            {
                // executed by Doom (credited to the Doom source)
            }
            else if (req.Gauge > 0f && req.Element != Element.None)
            {
                ApplyElement(target, req.Element, req.Gauge, src, req.Generation);
            }

            return effective;
        }

        public float EffectiveDefense(EnemyUnit e)
        {
            float def = e.Defense + e.ArmorBuff;
            if (e.ArmorCrackTimer > 0f) def *= 1f - SimMath.Clamp(e.ArmorCrackStacks * e.ArmorCrackPerStack * 2f, 0f, 0.9f);
            if (e.SuperconductTimer > 0f) def *= 0.6f;
            if (e.Corroded) def *= 0.7f;
            return def;
        }

        private void KillEnemy(EnemyUnit e, HeroUnit killer)
        {
            if (!e.Alive) return;
            e.Alive = false;
            e.Hp = 0f;
            Stats.Kills++;
            float gold = e.Def.Gold * (e.Elite && !e.Def.Elite ? 3f : 1f) * (1f + Mods.EnemyGoldPct) * SallyGold();
            Stats.GoldFromKills += gold;
            Stats.EssenceFromKills += e.Def.Essence + (e.Elite && !e.Def.Elite && !e.Def.Boss ? 1 : 0);
            if (killer != null)
            {
                killer.Kills++;
                ChargeUltimateOnKill(killer);
                OnKillPassive(killer, e);
            }
            Emit(SimEventType.EnemyDeath, e.Pos, Element.None, gold, killer?.Uid ?? 0, e.Uid, e.Def.Id);
            SpreadContagion(e);
            OnMechanicDeath(e);
            OnEnemyDeathBehaviour(e);
            FireTrigger("kill", killer, e, e.Pos, null);
        }

        // ------------------------------------------------------------------ elements & reactions

        /// <summary>
        /// Applies an element gauge. If another aura is present and the pair has a reaction (and caps
        /// allow it), the reaction fires and consumes gauge; otherwise the aura is added/refreshed.
        /// </summary>
        public void ApplyElement(EnemyUnit target, Element el, float gauge, HeroUnit source, int generation)
        {
            if (target == null || !target.Alive || target.Burrowed || el == Element.None || gauge <= 0f) return;
            gauge *= Mods.GaugeMult[(int)el];
            if (source != null) gauge *= (1f + source.Stat(StatId.StatusPower) * 0.5f) * (1f + TraitValue(source, "gaugeBonus"));

            // Strongest foreign aura that actually pairs with the incoming element (ties: lower ordinal).
            // Neutral/blocked pairs coexist and are skipped. With the six launch elements every pair
            // reacts, so this is identical to picking the strongest aura.
            Element existing = Element.None;
            float best = 0.05f;
            for (int i = 1; i < ElementUtil.Count; i++)
            {
                if (i == (int)el || target.Aura[i] <= best) continue;
                if (Content.ReactionFor(el, (Element)i) == null) continue;
                best = target.Aura[i];
                existing = (Element)i;
            }

            if (existing != Element.None)
            {
                ReactionDef r = Content.ReactionFor(el, existing);
                if (r != null && CanReact(target, r, generation))
                {
                    target.Aura[(int)existing] = SimMath.Max(0f, target.Aura[(int)existing] - r.Consume * gauge);
                    float leftover = gauge - target.Aura[(int)existing];
                    if (Mods.HasRule("lingering_elements") && leftover > 0f)
                        target.Aura[(int)el] = SimMath.Min(2f, target.Aura[(int)el] + leftover * 0.5f);
                    TriggerReaction(r, target, source, el, existing, generation + 1);
                    return;
                }
            }

            float before = target.Aura[(int)el];
            target.Aura[(int)el] = SimMath.Min(2.5f, before + gauge);
            ElementDef def = Content.ElementDefs[(int)el];
            if (before <= 0.05f)
            {
                Emit(SimEventType.StatusApplied, target.Pos, el, gauge, source?.Uid ?? 0, target.Uid, null);
                if (def != null) RunElementStatusOps(def.OnApply, target, source, generation);
            }
            else if (def != null)
            {
                RunElementStatusOps(def.OnRefresh, target, source, generation);
            }
        }

        private bool CanReact(EnemyUnit target, ReactionDef r, int generation)
        {
            int maxGen = MaxProcGeneration + (int)Mods.Rule("proc_generation_bonus");
            if (generation >= maxGen)
            {
                Stats.ReactionsBlockedByGeneration++;
                return false;
            }
            int pair = ElementUtil.PairIndex(r.A, r.B);
            if (target.ReactionCooldown[pair] > Time) return false;
            if (r.Params.Get("worldCooldown") > 0f && _worldReactionReady.TryGetValue(r.Id, out float ready) && Time < ready) return false;
            if (Time - target.ReactionWindowStart >= 1f)
            {
                target.ReactionWindowStart = Time;
                target.ReactionsInWindow = 0;
            }
            if (target.ReactionsInWindow >= TargetReactionBudgetPerSecond || _reactionsThisTick >= WorldReactionBudgetPerTick)
            {
                Stats.ReactionsBlockedByBudget++;
                return false;
            }
            return true;
        }

        public float ReactionPower(ReactionDef r, HeroUnit source)
        {
            float atk = source != null ? source.Stat(StatId.Attack) : 20f * WaveLevelScale;
            return r.BaseDamage * WaveLevelScale + r.AttackScale * atk;
        }

        private float ReactionRadius(ReactionDef r)
        {
            ReactionMod m = Mods.ModFor(r.Id);
            ReactionMod all = Mods.ModFor("*");
            float pct = (m?.RadiusPct ?? 0f) + (all?.RadiusPct ?? 0f);
            return r.Radius * (1f + pct);
        }

        private float ReactionDuration(ReactionDef r)
        {
            ReactionMod m = Mods.ModFor(r.Id);
            ReactionMod all = Mods.ModFor("*");
            float pct = (m?.DurationPct ?? 0f) + (all?.DurationPct ?? 0f);
            return r.Duration * (1f + pct);
        }

        private float ReactionStatus(ReactionDef r)
        {
            ReactionMod m = Mods.ModFor(r.Id);
            ReactionMod all = Mods.ModFor("*");
            return 1f + (m?.StatusPct ?? 0f) + (all?.StatusPct ?? 0f);
        }

        private DamageRequest ReactionHit(ReactionDef r, HeroUnit source, Element el, float mult, int gen)
        {
            return new DamageRequest
            {
                Source = source,
                Attack = ReactionPower(r, source),
                Multiplier = mult,
                Element = el,
                Gauge = 0f,
                Kind = DamageKind.Reaction,
                Generation = gen,
                ReactionId = r.Id
            };
        }

        /// <summary>Resolves one of the 15 reactions. Secondary element applications carry gen+1.</summary>
        private void TriggerReaction(ReactionDef r, EnemyUnit target, HeroUnit source, Element incoming, Element existing, int gen)
        {
            int pair = ElementUtil.PairIndex(r.A, r.B);
            target.ReactionCooldown[pair] = Time + r.Cooldown;
            float worldCd = r.Params.Get("worldCooldown");
            if (worldCd > 0f) _worldReactionReady[r.Id] = Time + worldCd;
            target.ReactionsInWindow++;
            _reactionsThisTick++;
            _reactionsThisSecond++;
            if (source != null) source.ReactionsTriggered++;

            float radius = ReactionRadius(r);
            float duration = ReactionDuration(r);
            float status = ReactionStatus(r);
            float control = status * (1f - target.Tenacity);
            Vec2 pos = target.Pos;
            List<EnemyUnit> q = RentList();
            List<EnemyUnit> q2 = RentList();
            Stats.AddReaction(r.Id, 0f);
            Emit(SimEventType.Reaction, pos, incoming, (int)existing, source?.Uid ?? 0, target.Uid, r.Id, false, radius, gen);

            // Arcane Resonant: the next reaction on the target is amplified, then the mark is consumed.
            float prevBonus = _activeReactionBonus;
            if (target.ResonantTimer > 0f)
            {
                target.ResonantTimer = 0f;
                _activeReactionBonus += 0.3f + Mods.Rule("resonance_bonus");
                Emit(SimEventType.StatusApplied, pos, Element.Arcane, 0f, source?.Uid ?? 0, target.Uid, "resonance");
            }

            if (!r.Legacy)
            {
                var ctx = new ActionContext
                {
                    Reaction = r,
                    Tag = r.Id,
                    Target = target,
                    Source = source,
                    Incoming = incoming,
                    Existing = existing,
                    Pos = pos,
                    Generation = gen,
                    Radius = radius,
                    Duration = duration,
                    StatusScale = control,
                    Power = ReactionPower(r, source)
                };
                ExecuteActions(r.Ops, ref ctx);
            }
            else switch (r.Id)
            {
                case "vaporize":
                {
                    // Steam burst: big single-target hit, plus a small splash of scalding steam.
                    DealDamage(target, ReactionHit(r, source, Element.Fire, r.Params.Get("mult", 2.2f), gen));
                    QueryEnemies(pos, radius, q);
                    for (int i = 0; i < q.Count; i++)
                        if (q[i] != target) DealDamage(q[i], ReactionHit(r, source, Element.Water, r.Params.Get("splash", 0.4f), gen));
                    break;
                }
                case "overload":
                {
                    QueryEnemies(pos, radius, q);
                    for (int i = 0; i < q.Count; i++)
                    {
                        EnemyUnit e = q[i];
                        DealDamage(e, ReactionHit(r, source, Element.Fire, r.Params.Get("mult", 1.3f), gen));
                        Knock(e, (e.Pos - pos).Normalized, r.Params.Get("knock", 0.7f) * status);
                    }
                    break;
                }
                case "melt":
                {
                    // Fire striking a Chilled target hits hardest; ice into fire is a weaker melt.
                    float mult = existing == Element.Ice ? r.Params.Get("multChilled", 2.8f) : r.Params.Get("mult", 1.6f);
                    DealDamage(target, ReactionHit(r, source, Element.Fire, mult, gen));
                    break;
                }
                case "firestorm":
                {
                    QueryEnemies(pos, radius, q);
                    for (int i = 0; i < q.Count; i++)
                    {
                        EnemyUnit e = q[i];
                        DealDamage(e, ReactionHit(r, source, Element.Fire, r.Params.Get("mult", 0.5f), gen));
                        ApplyBurn(e, source, duration);
                    }
                    break;
                }
                case "magma":
                    SpawnZone(ZoneKind.Magma, pos, radius, duration, source, Element.Fire, ReactionPower(r, source) * r.Params.Get("dpsMult", 0.45f), gen, r.Id);
                    break;
                case "electrocharge":
                {
                    DealDamage(target, ReactionHit(r, source, Element.Lightning, r.Params.Get("mult", 0.9f), gen));
                    int bounces = (int)(r.Params.Get("bounces", 3f) + (Mods.ModFor(r.Id)?.Bounces ?? 0f));
                    ChainBounce(target, source, bounces, radius, r, gen, true);
                    break;
                }
                case "freeze":
                {
                    float d = duration * control * (1f - target.FreezeResist);
                    if (target.IsBoss) d *= 0.35f;
                    if (d > 0.1f)
                    {
                        target.StunTimer = SimMath.Max(target.StunTimer, d);
                        target.Frozen = true;
                    }
                    if (target.IsBoss)
                    {
                        target.FreezeResist = SimMath.Min(0.8f, target.FreezeResist + 0.2f);
                        target.FreezeResistTimer = 10f;
                    }
                    DealDamage(target, ReactionHit(r, source, Element.Ice, r.Params.Get("mult", 0.5f), gen));
                    break;
                }
                case "rainstorm":
                {
                    QueryEnemies(pos, radius, q);
                    for (int i = 0; i < q.Count; i++)
                    {
                        EnemyUnit e = q[i];
                        DealDamage(e, ReactionHit(r, source, Element.Water, r.Params.Get("mult", 0.35f), gen));
                        if (e.Alive) ApplyElement(e, Element.Water, r.Params.Get("wetGauge", 1f), source, gen);
                    }
                    break;
                }
                case "mudfield":
                    SpawnZone(ZoneKind.Mud, pos, radius, duration, source, Element.Earth, r.Params.Get("slow", 0.45f) * status, gen, r.Id);
                    break;
                case "superconduct":
                {
                    QueryEnemies(pos, radius, q);
                    for (int i = 0; i < q.Count; i++)
                    {
                        EnemyUnit e = q[i];
                        e.SuperconductTimer = SimMath.Max(e.SuperconductTimer, duration);
                        DealDamage(e, ReactionHit(r, source, Element.Ice, r.Params.Get("mult", 0.6f), gen));
                    }
                    break;
                }
                case "thunderstorm":
                    SpawnZone(ZoneKind.Thunderstorm, pos, radius, duration, source, Element.Lightning, ReactionPower(r, source) * r.Params.Get("strikeMult", 0.8f), gen, r.Id);
                    break;
                case "magnetize":
                {
                    QueryEnemies(pos, radius, q);
                    for (int i = 0; i < q.Count; i++)
                    {
                        EnemyUnit e = q[i];
                        Pull(e, pos, r.Params.Get("pull", 3.5f) * status, 0.6f);
                        DealDamage(e, ReactionHit(r, source, Element.Lightning, r.Params.Get("mult", 0.4f), gen));
                    }
                    break;
                }
                case "blizzard":
                    SpawnZone(ZoneKind.Blizzard, pos, radius, duration, source, Element.Ice, ReactionPower(r, source) * r.Params.Get("dpsMult", 0.35f), gen, r.Id);
                    break;
                case "ice_spikes":
                {
                    int spikes = (int)r.Params.Get("spikes", 3f);
                    for (int i = 0; i < spikes; i++)
                    {
                        Vec2 off = Vec2.FromAngle(i * 6.2831853f / spikes + Rng.Range(0f, 0.6f)) * r.Params.Get("spread", 0.9f);
                        AddStrike(new DelayedStrike
                        {
                            Kind = StrikeKind.IceSpike,
                            Pos = pos + off,
                            Delay = 0.45f + i * 0.08f,
                            Radius = radius,
                            Source = source,
                            Element = Element.Ice,
                            Power = ReactionPower(r, source),
                            Multiplier = r.Params.Get("mult", 0.7f),
                            Generation = gen,
                            ReactionId = r.Id
                        });
                    }
                    break;
                }
                case "sandstorm":
                {
                    QueryEnemies(pos, radius, q);
                    for (int i = 0; i < q.Count; i++)
                    {
                        EnemyUnit e = q[i];
                        e.SandstormTimer = SimMath.Max(e.SandstormTimer, duration);
                        Slow(e, r.Params.Get("slow", 0.25f) * status, duration);
                        DealDamage(e, ReactionHit(r, source, Element.Earth, r.Params.Get("mult", 0.3f), gen));
                    }
                    break;
                }
            }

            _activeReactionBonus = prevBonus;
            NotifyReactionPassives();
            FireTrigger("reaction", source, target, pos, r.Id);
            if (Mods.HasRule("mirror_reactions") && gen < MaxProcGeneration + (int)Mods.Rule("proc_generation_bonus"))
            {
                // Elemental Mirror: reactions re-apply the consumed element to one nearby enemy.
                QueryEnemies(pos, 2.2f, q2);
                for (int i = 0; i < q2.Count; i++)
                {
                    if (q2[i] == target || !q2[i].Alive) continue;
                    ApplyElement(q2[i], existing, 0.6f, source, gen);
                    break;
                }
            }
            ReturnList(q);
            ReturnList(q2);
        }

        /// <summary>Lightning bounce between enemies, optionally only along Wet targets.</summary>
        private void ChainBounce(EnemyUnit from, HeroUnit source, int bounces, float radius, ReactionDef r, int gen, bool wetOnly)
        {
            EnemyUnit current = from;
            var hit = HitSetPool.Rent();
            List<EnemyUnit> q2 = RentList();
            hit.Add(from.Uid);
            for (int b = 0; b < bounces; b++)
            {
                QueryEnemies(current.Pos, radius, q2);
                EnemyUnit next = null;
                float bestD = float.MaxValue;
                for (int i = 0; i < q2.Count; i++)
                {
                    EnemyUnit e = q2[i];
                    if (hit.Contains(e.Uid) || !e.Alive) continue;
                    if (wetOnly && !e.Wet) continue;
                    float d = Vec2.SqrDistance(current.Pos, e.Pos);
                    if (d < bestD) { bestD = d; next = e; }
                }
                if (next == null) break;
                hit.Add(next.Uid);
                Emit(SimEventType.Strike, next.Pos, Element.Lightning, 0f, source?.Uid ?? 0, next.Uid, "chain", false, 0f, gen);
                Journal.Pending[Journal.Pending.Count - 1] = WithFrom(Journal.Pending[Journal.Pending.Count - 1], current.Pos);
                DealDamage(next, ReactionHit(r, source, Element.Lightning, r.Params.Get("bounceMult", 0.7f), gen));
                current = next;
            }
            HitSetPool.Return(hit);
            ReturnList(q2);
        }

        private static SimEvent WithFrom(SimEvent e, Vec2 from)
        {
            e.From = from;
            return e;
        }

        // ------------------------------------------------------------------ statuses

        public void ApplyBurn(EnemyUnit e, HeroUnit source, float duration)
        {
            if (!e.Alive) return;
            float atk = source != null ? source.Stat(StatId.Attack) : 15f * WaveLevelScale;
            float sp = source != null ? source.Stat(StatId.StatusPower) : 0f;
            float dps = atk * 0.22f * (1f + sp) * (1f + Mods.Rule("burn_power"));
            duration *= 1f + TraitValue(source, "burnDuration");
            if (dps >= e.BurnDps || e.BurnTimer <= 0f)
            {
                e.BurnDps = dps;
                e.BurnSource = source;
            }
            e.BurnTimer = SimMath.Max(e.BurnTimer, duration);
        }

        public void ApplyArmorCrack(EnemyUnit e, float duration, int stacks, int maxStacks = 1)
        {
            e.ArmorCrackStacks = SimMath.Clamp(e.ArmorCrackStacks + stacks, 1, maxStacks < 1 ? 1 : maxStacks);
            e.ArmorCrackTimer = SimMath.Max(e.ArmorCrackTimer, duration);
        }

        public void Slow(EnemyUnit e, float amount, float duration)
        {
            amount *= 1f - e.Tenacity;
            if (amount > e.SlowAmount || e.SlowTimer <= 0f) e.SlowAmount = SimMath.Clamp(amount, 0f, 0.7f);
            e.SlowTimer = SimMath.Max(e.SlowTimer, duration);
        }

        public void Stun(EnemyUnit e, float duration)
        {
            float d = duration * (1f - e.Tenacity);
            if (e.IsBoss) d *= 0.3f;
            if (d > e.StunTimer) e.StunTimer = d;
        }

        public void Knock(EnemyUnit e, Vec2 dir, float distance)
        {
            if (e.IsBoss) return; // bosses resist displacement but still take the damage
            distance *= 1f - e.Tenacity;
            if (distance <= 0.05f) return;
            e.Knockback = dir * (distance / 0.2f);
            e.KnockbackTimer = 0.2f;
        }

        public void Pull(EnemyUnit e, Vec2 to, float strength, float duration)
        {
            if (e.IsBoss) return;
            e.PullTarget = to;
            e.PullStrength = strength * (1f - e.Tenacity);
            e.PullTimer = SimMath.Max(e.PullTimer, duration);
        }

        // ------------------------------------------------------------------ heroes & crystal

        public void DamageHero(HeroUnit h, float amount, EnemyUnit attacker)
        {
            if (h == null || !h.Alive) return;
            float def = h.Stat(StatId.Defense);
            amount *= 100f / (100f + SimMath.Max(0f, def));
            float dr = h.Stat(StatId.DamageReduction) + (h.FieldTimer > 0f ? h.FieldDamageReduction : 0f) + HeroGuardReduction(h) + SelfPassiveReduction(h);
            amount *= 1f - SimMath.Clamp(dr, 0f, 0.75f);
            if (h.FeverTimer > 0f) amount *= 1f + h.FeverAmount;
            amount = GloomRedirect(h, amount);
            if (attacker != null)
            {
                if (attacker.Chilled) amount *= 1f - attacker.ChillDamageReduction;
                amount *= attacker.OutgoingDamageMult;
            }
            if (attacker != null && attacker.SandstormTimer > 0f && Rng.Chance(0.35f))
            {
                Emit(SimEventType.Miss, h.Pos, Element.Earth, 0f, attacker.Uid, h.Uid, "miss");
                return;
            }
            if (h.Shield > 0f)
            {
                float a = SimMath.Min(h.Shield, amount);
                h.Shield -= a;
                Stats.HeroShieldAbsorbed += a;
                amount -= a;
                if (h.Shield <= 0f && h.ShieldRetaliate > 0f) OnHeroShieldBroken(h);
                if (h.Shield <= 0f && h.ShieldGiverUid != 0) FrostBurst(h);
            }
            h.Hp -= amount;
            h.DamageTaken += amount;
            if (h.PassiveKind == "phoenix_heat" && amount > 0f) AddHeat(h, amount / SimMath.Max(1f, h.MaxHp) * h.PassiveParams.Get("damageHeat", 50f));
            h.HitFlash = 0.12f;
            Emit(SimEventType.Hit, h.Pos, Element.None, amount, attacker?.Uid ?? 0, h.Uid, "hero");
            if (attacker != null) OnHeroHit(h, attacker);
            if (h.Hp <= 0f) DownHero(h);
        }

        private void DownHero(HeroUnit h)
        {
            if (TryRebirth(h)) return;
            FireTrigger("hero_downed", h, null, h.Pos, null);
            if (h.Hp > 0f) return; // a trigger (e.g. Phoenix Feather) revived the hero
            h.Hp = 0f;
            h.Alive = false;
            h.Shield = 0f;
            h.State = HeroState.Downed;
            h.Target = null;
            Stats.HeroDowns++;
            if (h.Role == HeroRole.Guardian && Stats.FirstGuardianDownTime < 0f)
            {
                Stats.FirstGuardianDown = h.Def.Id;
                Stats.FirstGuardianDownTime = Time;
            }
            Emit(SimEventType.HeroDowned, h.Pos, Element.None, 0f, 0, h.Uid, h.Def.Id);
            foreach (EnemyUnit e in Enemies)
            {
                if (e.Engaged == h) e.Engaged = null;
                if (e.Taunter == h) { e.Taunter = null; e.TauntTimer = 0f; }
            }
        }

        public void ReviveHero(HeroUnit h, float hpFraction)
        {
            h.Alive = true;
            h.Hp = SimMath.Max(1f, h.MaxHp * hpFraction);
            h.State = HeroState.Idle;
            h.StunTimer = 0f;
            Emit(SimEventType.HeroRevived, h.Pos, Element.None, h.Hp, 0, h.Uid, h.Def.Id);
        }

        public float HealHero(HeroUnit target, float amount, HeroUnit source)
        {
            if (target == null || !target.Alive || amount <= 0f) return 0f;
            if (Mods.HasRule("no_healing")) amount *= 0.5f;
            amount *= (source != null ? source.Stat(StatId.HealPower) : 1f) * (1f + Mods.HealingPct) * (1f + TraitValue(source, "healBonus"));
            float before = target.Hp;
            target.Hp = SimMath.Min(target.MaxHp, target.Hp + amount);
            float healed = target.Hp - before;
            float overflow = amount - healed;
            if (overflow > 0f && Mods.HasRule("overheal_shield"))
                AddHeroShield(target, overflow * Mods.Rule("overheal_shield"), null);
            if (source != null) source.HealingDone += healed;
            if (healed > 0.5f) Emit(SimEventType.Heal, target.Pos, Element.Water, healed, source?.Uid ?? 0, target.Uid, null);
            return healed;
        }

        public void AddHeroShield(HeroUnit target, float amount, HeroUnit source)
        {
            if (!target.Alive || amount <= 0f) return;
            amount *= (1f + TraitValue(source, "shieldBonus")) * (1f + Mods.Rule("shield_power"));
            float cap = target.MaxHp * 0.6f; // shields are bounded (spec: healing/barrier bounded)
            target.Shield = SimMath.Min(cap, target.Shield + amount);
            Emit(SimEventType.ShieldGain, target.Pos, Element.Ice, amount, source?.Uid ?? 0, target.Uid, null);
        }

        public void HealCrystal(float amount)
        {
            if (!Crystal.Alive || amount <= 0f) return;
            Crystal.Hp = SimMath.Min(Crystal.MaxHp, Crystal.Hp + amount);
            Emit(SimEventType.Heal, Crystal.Pos, Element.None, amount, 0, -1, "crystal");
        }

        public void ShieldCrystal(float amount)
        {
            if (amount <= 0f) return;
            Crystal.Shield = SimMath.Min(Crystal.MaxHp * 0.3f, Crystal.Shield + amount);
            Emit(SimEventType.ShieldGain, Crystal.Pos, Element.Ice, amount, 0, -1, "crystal");
        }

        public void DamageCrystal(float amount, EnemyUnit attacker, string pillagerId = null, int pillagerLane = -1)
        {
            if (!Crystal.Alive) return;
            Stats.CrystalHits++;
            float reduction = Crystal.DamageReduction + (Crystal.TempReductionTimer > 0f ? Crystal.TempReduction : 0f);
            amount *= 1f - SimMath.Clamp(reduction, 0f, 0.8f);
            if (attacker != null) amount *= attacker.OutgoingDamageMult;
            if (Crystal.Shield > 0f)
            {
                float a = SimMath.Min(Crystal.Shield, amount);
                Crystal.Shield -= a;
                amount -= a;
            }
            Crystal.Hp -= amount;
            Crystal.HitFlash = 0.15f;
            Crystal.DamageTakenThisWave += amount;
            string sourceId = attacker?.Def.Id ?? pillagerId;
            int sourceLane = attacker?.Lane ?? pillagerLane;
            if (sourceId != null)
            {
                Stats.CrystalDamageByEnemy.TryGetValue(sourceId, out float d);
                Stats.CrystalDamageByEnemy[sourceId] = d + amount;
                if (attacker != null && !attacker.Leaked) { attacker.Leaked = true; Stats.Leaks++; }
                Stats.CrystalDamageByLane.TryGetValue(sourceLane, out float ld);
                Stats.CrystalDamageByLane[sourceLane] = ld + amount;
            }
            if (Stats.FirstGuardianDownTime >= 0f) Stats.CrystalDamageAfterGuardianDown += amount;
            Emit(SimEventType.CrystalHit, Crystal.Pos, Element.None, amount, attacker?.Uid ?? 0, -1, sourceId);
            FireTrigger("crystal_hit", null, attacker, Crystal.Pos, null);
            if (Crystal.Hp <= 0f)
            {
                Crystal.Hp = 0f;
                DefeatSource = sourceId ?? "breach";
            }
            if (attacker != null && Crystal.Thorns > 0f && attacker.Alive)
                DealDamage(attacker, new DamageRequest { Attack = Crystal.Thorns * WaveLevelScale, Multiplier = 1f, Element = Element.Earth, Kind = DamageKind.Trigger, Generation = MaxProcGeneration, IgnoreDefense = true, SourceTag = "crystal_thorns" });
        }
    }

    /// <summary>Tiny pool for per-chain visited sets to keep chains allocation-free in steady state.</summary>
    internal static class HitSetPool
    {
        // Thread-static so headless batch simulation can run battles in parallel (Unity uses one thread).
        [System.ThreadStatic] private static System.Collections.Generic.Stack<System.Collections.Generic.HashSet<int>> _pool;

        private static System.Collections.Generic.Stack<System.Collections.Generic.HashSet<int>> Pool =>
            _pool ?? (_pool = new System.Collections.Generic.Stack<System.Collections.Generic.HashSet<int>>());

        public static System.Collections.Generic.HashSet<int> Rent()
        {
            return Pool.Count > 0 ? Pool.Pop() : new System.Collections.Generic.HashSet<int>();
        }

        public static void Return(System.Collections.Generic.HashSet<int> set)
        {
            set.Clear();
            Pool.Push(set);
        }
    }
}
