using System.Collections.Generic;

namespace Aetherward.Sim.Content
{
    /// <summary>
    /// Data-integrity checks run by tests and by the Unity menu "Aetherward > Validate Content":
    /// cross-catalog ids, value bounds, evolution links, localization coverage for every content key
    /// in every language, and fully resolved tooltip templates.
    /// </summary>
    public static class ContentValidator
    {
        private static readonly HashSet<string> KnownOps = new HashSet<string>
        {
            "stat", "crystal", "enemy", "reaction", "gauge", "healing", "economy", "trigger", "rule", "skill", "card"
        };

        private static readonly HashSet<string> KnownTriggers = new HashSet<string>
        {
            "skill_cast", "basic_attack", "kill", "crit", "wave_start", "crystal_hit", "hero_downed", "reaction", "periodic", "doom_execute"
        };

        private static readonly HashSet<string> KnownActions = new HashSet<string>
        {
            "burst", "apply_element", "chain", "heal_team", "crystal_shield", "crystal_heal", "gold", "team_buff", "hero_buff",
            "revive", "zone", "refund_cooldown", "team_refund_cooldown", "echo_cast", "execute", "slow_all",
            "apply_status", "field", "team_shield", "cleanse_team"
        };

        private static readonly HashSet<string> KnownRules = new HashSet<string>
        {
            "mirror_reactions", "burn_power", "lingering_elements", "proc_generation_bonus", "overheal_shield", "no_healing",
            "doom_max", "doom_threshold", "doom_boss", "poison_max", "poison_power", "contagion_targets", "contagion_stacks",
            "resonance_bonus", "collapse_radius", "collapse_power", "mark_max", "shield_power", "field_duration", "illuminate_power"
        };

        private static readonly HashSet<string> KnownSkills = new HashSet<string>
        {
            "fireball", "meteor", "cleave", "duel_strike", "heal_rain", "push_wave", "chain_lightning", "dash_strike",
            "frost_nova", "ice_shield", "vortex", "pierce_arrow", "stone_barrier", "ground_slam",
            // expansion
            "dawn_aegis", "oath_of_doom", "phoenix_slash", "tide_blessing", "deploy_pylon", "frost_aegis", "gust_step", "raise_wall"
        };

        public static readonly HashSet<string> KnownActionOps = new HashSet<string>
        {
            "damage", "status", "apply", "field", "pull", "knock", "chain", "consume", "hero_shield", "hero_heal", "hero_buff",
            "crystal_shield", "cleanse", "refund", "echo", "suppress", "spread", "delayed", "shards", "collapse"
        };

        public static readonly HashSet<string> KnownStatuses = new HashSet<string>
        {
            "burn", "armor_crack", "slow", "stun", "vulnerable", "brittle", "reaction_vuln", "illuminate", "doom", "root", "poison",
            "resonant", "unstable", "mark", "seal"
        };

        public static readonly HashSet<string> KnownStatusChecks = new HashSet<string>
        {
            "illuminated", "doomed", "rooted", "poisoned", "corroded", "resonant", "unstable", "frozen", "chilled", "burning", "wet", "marked", "elite"
        };

        public static readonly HashSet<string> KnownTraitKeys = new HashSet<string>
        {
            "burnDuration", "burningBonus", "echoChance", "echoPower", "echoCooldown", "gaugeBonus", "debuffImmune", "shieldBonus",
            "healBonus", "lowHpThreshold", "lowHpBonus", "executeBelow", "executeBonus", "allyHaste", "allyRadius", "instantFirstCast"
        };

        private static readonly HashSet<string> Consumable = new HashSet<string> { "poison", "doom", "mark", "freeze" };

        /// <summary>Authored signature reactions must stay inside this band (spec: 25-35, no 66-pair trap).</summary>
        public const int MinSignature = 25, MaxSignature = 35;

        private static void CheckActions(ContentDatabase db, string owner, List<ActionOp> ops, List<string> errors)
        {
            foreach (ActionOp op in ops)
            {
                if (!KnownActionOps.Contains(op.Op)) { errors.Add(owner + ": unknown action op " + op.Op); continue; }
                if ((op.Op == "status" || op.Op == "spread") && !KnownStatuses.Contains(op.Status ?? "")) errors.Add(owner + ": unknown status " + op.Status);
                if (op.Op == "consume" && !Consumable.Contains(op.Status ?? "")) errors.Add(owner + ": status " + op.Status + " cannot be consumed");
                if (op.Op == "field" && !db.Fields.ContainsKey(op.Field ?? "")) errors.Add(owner + ": unknown field " + op.Field);
                string filter = op.Params.GetString("filter") ?? op.Params.GetString("bonusIf") ?? op.Params.GetString("requires");
                if (filter != null && !KnownStatusChecks.Contains(filter)) errors.Add(owner + ": unknown status check " + filter);
                string delayedStatus = op.Params.GetString("status");
                if ((op.Op == "delayed" || op.Op == "shards") && delayedStatus != null && !KnownStatuses.Contains(delayedStatus))
                    errors.Add(owner + ": unknown strike status " + delayedStatus);
            }
        }

        private static void CheckReactionMatrix(ContentDatabase db, List<string> errors)
        {
            int signature = 0, legacy = 0;
            foreach (ReactionDef r in db.Reactions.Values)
            {
                if (r.Category == ReactionCategory.Signature) signature++;
                if (r.Legacy) legacy++;
                if (!r.Legacy && r.Ops.Count == 0) errors.Add("reaction " + r.Id + ": no ops");
                CheckActions(db, "reaction " + r.Id, r.Ops, errors);
            }
            if (legacy != ContentDatabase.LegacyReactionIds.Length) errors.Add("expected " + ContentDatabase.LegacyReactionIds.Length + " launch reactions, found " + legacy);
            if (signature < MinSignature || signature > MaxSignature) errors.Add("signature reactions must be " + MinSignature + "-" + MaxSignature + ", found " + signature);
            Element[] all = ElementUtil.All;
            for (int i = 0; i < all.Length; i++)
            {
                for (int j = i + 1; j < all.Length; j++)
                {
                    int pair = ElementUtil.PairIndex(all[i], all[j]);
                    bool covered = db.ReactionByPair[pair] != null || db.PairNote.ContainsKey(pair);
                    if (!covered) errors.Add("pair " + ElementUtil.Key(all[i]) + "+" + ElementUtil.Key(all[j]) + " has no defined behaviour");
                }
            }
            foreach (ElementDef e in db.ElementDefs)
            {
                if (e == null) continue;
                CheckActions(db, "element " + e.Id, e.OnApply, errors);
                CheckActions(db, "element " + e.Id, e.OnRefresh, errors);
            }
            foreach (FieldDef f in db.Fields.Values)
            {
                CheckActions(db, "field " + f.Id, f.OnTick, errors);
                CheckActions(db, "field " + f.Id, f.OnEnd, errors);
                if (f.MaxCount < 1 || f.MaxCount > 8) errors.Add("field " + f.Id + ": maxCount must be 1-8");
                if (f.Tick < 0.2f) errors.Add("field " + f.Id + ": tick too fast");
            }
        }

        public static List<string> Validate(ContentDatabase db)
        {
            var errors = new List<string>();
            void Err(string s) => errors.Add(s);
            CheckReactionMatrix(db, errors);

            foreach (HeroDef h in db.HeroList)
            {
                if (!KnownSkills.Contains(h.Skill.Kind)) Err("hero " + h.Id + ": unknown skill kind " + h.Skill.Kind);
                if (h.Evolutions.Count != 2) Err("hero " + h.Id + ": needs exactly 2 evolutions");
                foreach (string e in h.Evolutions)
                    if (!db.Evolutions.ContainsKey(e)) Err("hero " + h.Id + ": missing evolution " + e);
                if (h.BaseStats[(int)StatId.MaxHp] <= 0 || h.BaseStats[(int)StatId.Attack] <= 0) Err("hero " + h.Id + ": non-positive base stats");
                if (h.Skill.Cooldown < 1f) Err("hero " + h.Id + ": skill cooldown too low");
            }
            foreach (EvolutionDef e in db.Evolutions.Values)
            {
                if (!db.Heroes.ContainsKey(e.HeroId)) Err("evolution " + e.Id + ": unknown hero " + e.HeroId);
                else if (!db.Heroes[e.HeroId].Evolutions.Contains(e.Id)) Err("evolution " + e.Id + ": not listed by its hero");
                if (e.Skill != null && e.Skill.Kind != null && !KnownSkills.Contains(e.Skill.Kind)) Err("evolution " + e.Id + ": unknown skill " + e.Skill.Kind);
                if (e.Skill == null && e.PassiveKind == null && !e.RoleOverride.HasValue) Err("evolution " + e.Id + ": must change mechanics");
                CheckOps(db, "evolution " + e.Id, e.Effects, errors);
            }
            foreach (EnemyDef en in db.Enemies.Values)
            {
                for (int i = 0; i < en.Resist.Length; i++)
                    if (en.Resist[i] > 0.75f) Err("enemy " + en.Id + ": resistance above 75% (no full immunity allowed)");
                if (en.Tenacity >= 1f) Err("enemy " + en.Id + ": tenacity must be < 1 (bosses resist but are never immune)");
                string summon = en.Params.GetString("summon");
                if (summon != null && !db.Enemies.ContainsKey(summon)) Err("enemy " + en.Id + ": unknown summon " + summon);
            }
            foreach (RelicDef r in db.RelicList) CheckOps(db, "relic " + r.Id, r.Effects, errors);
            foreach (FusionDef f in db.Fusions)
            {
                if (!db.Relics.ContainsKey(f.A) || !db.Relics.ContainsKey(f.B) || !db.Relics.ContainsKey(f.Result)) Err("fusion " + f.Result + ": unknown relic");
                else if (!db.Relics[f.Result].Fusion) Err("fusion " + f.Result + ": result must be fusion-only");
            }
            foreach (CardDef c in db.CardList)
            {
                CheckOps(db, "card " + c.Id, c.Effects, errors);
                if (!string.IsNullOrEmpty(c.Requires.Hero) && !db.Heroes.ContainsKey(c.Requires.Hero)) Err("card " + c.Id + ": unknown hero requirement");
                if (c.Type == CardType.CursedPact && c.DrawbackKey == null) Err("card " + c.Id + ": pacts must declare a drawback");
                if (c.MaxStacks < 1) Err("card " + c.Id + ": maxStacks < 1");
            }
            if (db.Waves.Count != 20) Err("expected 20 waves, found " + db.Waves.Count);
            for (int i = 0; i < db.Waves.Count; i++)
            {
                WaveDef w = db.Waves[i];
                if (w.Number != i + 1) Err("wave numbering gap at " + (i + 1));
                if (w.Groups.Count == 0) Err("wave " + w.Number + ": no spawn groups");
                foreach (SpawnGroup g in w.Groups)
                {
                    if (!db.Enemies.ContainsKey(g.Enemy)) Err("wave " + w.Number + ": unknown enemy " + g.Enemy);
                    if (g.Lane >= db.Arena.Lanes.Count) Err("wave " + w.Number + ": lane out of range");
                    if (!string.IsNullOrEmpty(g.Affix) && !db.Affixes.ContainsKey(g.Affix)) Err("wave " + w.Number + ": unknown affix " + g.Affix);
                }
                foreach (int l in w.Lanes) if (l < 0 || l >= db.Arena.Lanes.Count) Err("wave " + w.Number + ": bad lane " + l);
                if (w.TimeLimit < 30f) Err("wave " + w.Number + ": time limit too short");
                foreach (string b in w.BossPool)
                    if (!db.Enemies.TryGetValue(b, out EnemyDef bd) || !bd.Boss) Err("wave " + w.Number + ": boss pool entry " + b + " is not a boss");
                if (w.BossPool.Count > 0 && !w.Groups.Exists(g => g.Enemy == w.BossPool[0])) Err("wave " + w.Number + ": boss pool default must be spawned by the wave");
            }
            foreach (EventDef ev in db.Events.Values)
                foreach (EventOption o in ev.Options)
                    if (!string.IsNullOrEmpty(o.GrantRelic) && !db.Relics.ContainsKey(o.GrantRelic)) Err("event " + ev.Id + ": unknown relic " + o.GrantRelic);
            if (db.Arena.Nodes.Count != 12) Err("arena must have 12 nodes");
            foreach (TraitDef t in db.TraitList)
            {
                CheckOps(db, "trait " + t.Id, t.Effects, errors);
                foreach (EffectOp op in t.Effects) if (op.Op != "stat") Err("trait " + t.Id + ": only stat ops allowed");
                foreach (string k in t.Behaviour.NumberKeys) if (!KnownTraitKeys.Contains(k)) Err("trait " + t.Id + ": unknown behaviour " + k);
                bool anyEligible = false;
                foreach (HeroDef h in db.HeroList) anyEligible |= t.EligibleFor(h);
                if (!anyEligible) Err("trait " + t.Id + ": no eligible hero");
            }

            CheckLocalization(db, errors);
            return errors;
        }

        private static void CheckOps(ContentDatabase db, string owner, List<EffectOp> ops, List<string> errors)
        {
            foreach (EffectOp op in ops)
            {
                if (!KnownOps.Contains(op.Op)) errors.Add(owner + ": unknown op " + op.Op);
                if (op.Op == "trigger")
                {
                    if (!KnownTriggers.Contains(op.Trigger)) errors.Add(owner + ": unknown trigger " + op.Trigger);
                    if (!KnownActions.Contains(op.Action)) errors.Add(owner + ": unknown action " + op.Action);
                }
                if (op.Op == "rule" && !KnownRules.Contains(op.Rule)) errors.Add(owner + ": unknown rule " + op.Rule);
                if ((op.Op == "reaction" || (op.Op == "trigger" && op.Trigger == "reaction")) && !string.IsNullOrEmpty(op.Reaction) && op.Reaction != "*" && !db.Reactions.ContainsKey(op.Reaction))
                    errors.Add(owner + ": unknown reaction " + op.Reaction);
                if (op.Op == "skill")
                {
                    string hero = op.Params.GetString("hero");
                    if (!db.Heroes.ContainsKey(hero ?? "")) errors.Add(owner + ": skill op for unknown hero " + hero);
                }
                if (op.Op == "stat" && op.Percent && (op.Value < -0.9f || op.Value > 3f)) errors.Add(owner + ": percentage out of bounds");
            }
        }

        public static IEnumerable<string> RequiredKeys(ContentDatabase db)
        {
            foreach (HeroDef h in db.HeroList)
            {
                yield return h.NameKey;
                yield return h.TitleKey;
                yield return h.Skill.NameKey;
                yield return h.Skill.DescKey;
                yield return h.PassiveNameKey;
                yield return h.PassiveDescKey;
            }
            foreach (EvolutionDef e in db.Evolutions.Values)
            {
                yield return e.NameKey;
                yield return e.DescKey;
                if (e.Skill != null)
                {
                    yield return e.Skill.NameKey;
                    yield return e.Skill.DescKey;
                }
                if (e.PassiveKind != null) yield return "passive." + e.PassiveKind + ".desc";
            }
            foreach (EnemyDef en in db.Enemies.Values)
            {
                yield return en.NameKey;
                yield return en.DescKey;
            }
            foreach (AffixDef a in db.Affixes.Values) yield return a.NameKey;
            foreach (ReactionDef r in db.Reactions.Values)
            {
                yield return r.NameKey;
                yield return r.DescKey;
            }
            foreach (Element e in ElementUtil.All)
            {
                ElementDef d = db.ElementDef(e);
                yield return d.NameKey;
                yield return "status." + d.StatusKey;
                yield return "status." + d.StatusKey + ".desc";
            }
            foreach (FieldDef f in db.Fields.Values) yield return f.NameKey;
            foreach (TraitDef t in db.TraitList)
            {
                yield return t.NameKey;
                yield return t.DescKey;
            }
            foreach (string note in db.PairNote.Values) yield return "pair." + note;
            foreach (RelicDef r in db.RelicList)
            {
                yield return r.NameKey;
                yield return r.DescKey;
            }
            foreach (CardDef c in db.CardList)
            {
                yield return c.NameKey;
                if (c.DrawbackKey != null) yield return c.DrawbackKey;
            }
            foreach (EventDef ev in db.Events.Values)
            {
                yield return ev.NameKey;
                yield return ev.DescKey;
                foreach (EventOption o in ev.Options)
                {
                    yield return o.TextKey;
                    if (o.DrawbackKey != null) yield return o.DrawbackKey;
                }
            }
            foreach (WaveDef w in db.Waves)
            {
                yield return w.NameKey;
                yield return w.HintKey;
            }
            foreach (LaneDef l in db.Arena.Lanes) yield return l.NameKey;
        }

        private static void CheckLocalization(ContentDatabase db, List<string> errors)
        {
            foreach (string lang in Localization.Supported)
            {
                if (!db.Strings.ContainsKey(lang))
                {
                    errors.Add("missing language table " + lang);
                    continue;
                }
                var l = new Localization(db, lang);
                var fx = new EffectDescriber(db, l);
                foreach (string key in RequiredKeys(db))
                    if (!db.Strings[lang].ContainsKey(key)) errors.Add(lang + ": missing key " + key);

                // Tooltips must fully resolve: no leftover {tokens}, no raw keys.
                foreach (HeroDef h in db.HeroList)
                {
                    CheckResolved(errors, lang, h.Id + " skill", l.SkillText(h.Skill, h.Skill.DescKey));
                    CheckResolved(errors, lang, h.Id + " passive", l.PassiveText(h.PassiveParams, h.PassiveDescKey));
                }
                foreach (EvolutionDef e in db.Evolutions.Values)
                {
                    if (e.Skill == null) continue;
                    SkillDef s = db.Heroes[e.HeroId].Skill.With(e.Skill);
                    CheckResolved(errors, lang, e.Id + " skill", l.SkillText(s, s.DescKey));
                    if (e.PassiveKind != null) CheckResolved(errors, lang, e.Id + " passive", l.PassiveText(e.PassiveParams, "passive." + e.PassiveKind + ".desc"));
                }
                foreach (ReactionDef r in db.Reactions.Values)
                    CheckResolved(errors, lang, r.Id, ReactionText(l, r));
                foreach (TraitDef t in db.TraitList)
                    CheckResolved(errors, lang, "trait " + t.Id, l.PassiveText(t.Behaviour, t.DescKey));
                l.Missing.Clear();
                foreach (RelicDef r in db.RelicList) fx.Describe(r.Effects);
                foreach (CardDef c in db.CardList) fx.Describe(c.Effects);
                foreach (EvolutionDef e in db.Evolutions.Values) fx.Describe(e.Effects);
                foreach (string missing in l.Missing) errors.Add(lang + ": effect text key missing " + missing);
            }
        }

        public static string ReactionText(Localization l, ReactionDef r)
        {
            return Localization.Fill(l.Get(r.DescKey), name =>
            {
                switch (name)
                {
                    case "radius": return r.Radius;
                    case "duration": return r.Duration;
                    default: return r.Params.Has(name) ? r.Params.Get(name) : (float?)null;
                }
            });
        }

        private static void CheckResolved(List<string> errors, string lang, string what, string text)
        {
            if (text == null || text.IndexOf('{') >= 0 || text.StartsWith("hero.") || text.StartsWith("evo.") || text.StartsWith("reaction."))
                errors.Add(lang + ": unresolved text for " + what + ": " + text);
        }
    }
}
