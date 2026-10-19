using System.Collections.Generic;
using System.Globalization;

namespace Aetherward.Sim.Content
{
    /// <summary>
    /// Builds tooltip lines directly from effect ops, so the text players read is generated from the
    /// same numbers the simulation uses (spec: tooltips must match the actual formula).
    /// </summary>
    public sealed class EffectDescriber
    {
        private readonly Localization _l;
        private readonly ContentDatabase _db;

        public EffectDescriber(ContentDatabase db, Localization l)
        {
            _db = db;
            _l = l;
        }

        private static string Pct(float v, bool signed = true)
        {
            string s = Localization.Number(v * 100f);
            return signed && v > 0 ? "+" + s : s;
        }

        private static string Num(float v, bool signed = false)
        {
            string s = Localization.Number(v);
            return signed && v > 0 ? "+" + s : s;
        }

        public List<string> Describe(IList<EffectOp> ops, int stacks = 1)
        {
            var lines = new List<string>();
            foreach (EffectOp op in ops) Describe(op, stacks, lines);
            return lines;
        }

        public string ReactionName(string id) => id == "*" || string.IsNullOrEmpty(id) ? _l.Get("fx.all_reactions") : _l.ReactionName(id);

        private string Scope(EffectOp op)
        {
            if (!string.IsNullOrEmpty(op.ScopeHero)) return _l.Format("fx.scope.hero", _l.Get("hero." + op.ScopeHero + ".name"));
            if (op.ScopeElement != Element.None) return _l.Format("fx.scope.element", _l.Element(op.ScopeElement));
            if (op.ScopeRole.HasValue) return _l.Format("fx.scope.role", _l.Role(op.ScopeRole.Value));
            if (op.ScopeMelee) return _l.Get("fx.scope.melee");
            if (op.ScopeRanged) return _l.Get("fx.scope.ranged");
            return "";
        }

        public void Describe(EffectOp op, int stacks, List<string> lines)
        {
            ParamBag p = op.Params;
            switch (op.Op)
            {
                case "stat":
                {
                    float v = op.Value * stacks;
                    string scope = Scope(op);
                    if (op.Stat == StatId.AttackInterval) lines.Add(_l.Format("fx.attack_speed", Pct(v)) + scope);
                    else if (op.Stat == StatId.SkillCooldown) lines.Add(_l.Format("fx.skill_haste", Pct(v)) + scope);
                    else if (op.Percent || IsChanceStat(op.Stat)) lines.Add(_l.Format("fx.stat_pct", Pct(v), _l.Stat(op.Stat)) + scope);
                    else lines.Add(_l.Format("fx.stat_flat", Num(v, true), _l.Stat(op.Stat)) + scope);
                    break;
                }
                case "crystal":
                    if (p.Has("maxHpPct")) lines.Add(_l.Format("fx.crystal_max_hp", Pct(p.Get("maxHpPct") * stacks)));
                    if (p.Has("maxHp")) lines.Add(_l.Format("fx.crystal_max_hp_flat", Num(p.Get("maxHp") * stacks, true)));
                    if (p.Has("reduction")) lines.Add(_l.Format("fx.crystal_reduction", Pct(p.Get("reduction") * stacks, false)));
                    if (p.Has("regen")) lines.Add(_l.Format("fx.crystal_regen", Num(p.Get("regen") * stacks)));
                    if (p.Has("thorns")) lines.Add(_l.Format("fx.crystal_thorns", Num(p.Get("thorns") * stacks)));
                    break;
                case "enemy":
                    if (p.Has("hpPct")) lines.Add(_l.Format("fx.enemy_hp", Pct(p.Get("hpPct") * stacks)));
                    if (p.Has("speedPct")) lines.Add(_l.Format("fx.enemy_speed", Pct(p.Get("speedPct") * stacks)));
                    if (p.Has("damagePct")) lines.Add(_l.Format("fx.enemy_damage", Pct(p.Get("damagePct") * stacks)));
                    if (p.Has("goldPct")) lines.Add(_l.Format("fx.enemy_gold", Pct(p.Get("goldPct") * stacks)));
                    break;
                case "reaction":
                {
                    string r = ReactionName(op.Reaction);
                    if (p.Has("damagePct")) lines.Add(_l.Format("fx.reaction_damage", r, Pct(p.Get("damagePct") * stacks)));
                    if (p.Has("radiusPct")) lines.Add(_l.Format("fx.reaction_radius", r, Pct(p.Get("radiusPct") * stacks)));
                    if (p.Has("durationPct")) lines.Add(_l.Format("fx.reaction_duration", r, Pct(p.Get("durationPct") * stacks)));
                    if (p.Has("bounces")) lines.Add(_l.Format("fx.reaction_bounces", r, Num(p.Get("bounces") * stacks, true)));
                    if (p.Has("statusPct")) lines.Add(_l.Format("fx.reaction_status", r, Pct(p.Get("statusPct") * stacks)));
                    break;
                }
                case "gauge":
                {
                    string el = p.GetString("element", "all");
                    string name = el == "all" ? _l.Get("fx.all_elements") : _l.Element(ContentDatabase.ParseElement(el));
                    lines.Add(_l.Format("fx.gauge", Pct(p.Get("pct") * stacks), name));
                    break;
                }
                case "healing":
                    lines.Add(_l.Format("fx.healing", Pct(p.Get("pct") * stacks)));
                    break;
                case "economy":
                    if (p.Has("goldPct")) lines.Add(_l.Format("fx.gold_pct", Pct(p.Get("goldPct") * stacks)));
                    if (p.Has("waveGold")) lines.Add(_l.Format("fx.wave_gold", Num(p.Get("waveGold") * stacks, true)));
                    if (p.Has("interestCap")) lines.Add(_l.Format("fx.interest_cap", Num(p.Get("interestCap") * stacks, true)));
                    if (p.Has("xpBonus")) lines.Add(_l.Format("fx.xp_bonus", Num(p.Get("xpBonus") * stacks, true)));
                    if (p.Has("essenceOnElite")) lines.Add(_l.Format("fx.essence_elite", Num(p.Get("essenceOnElite") * stacks, true)));
                    if (p.Has("shopDiscount")) lines.Add(_l.Format("fx.shop_discount", Pct(p.Get("shopDiscount") * stacks, false)));
                    if (p.Has("freeRerolls")) lines.Add(_l.Format("fx.free_rerolls", Num(p.Get("freeRerolls") * stacks)));
                    if (p.Has("reviveDiscount")) lines.Add(_l.Format("fx.revive_discount", Pct(p.Get("reviveDiscount") * stacks, false)));
                    break;
                case "rule":
                {
                    float v = (op.Value != 0f ? op.Value : 1f) * stacks;
                    string key = "fx.rule." + op.Rule;
                    lines.Add(_l.Format(key, Localization.Number(PercentRules.Contains(op.Rule) ? v * 100f : v)));
                    break;
                }
                case "skill":
                {
                    string hero = _l.Get("hero." + p.GetString("hero") + ".name");
                    string param = _l.Get("skillparam." + p.GetString("param"));
                    string amount = p.Has("add") ? Num(p.Get("add") * stacks, true) : Pct(p.Get("pct") * stacks);
                    lines.Add(_l.Format("fx.skill", hero, param, amount));
                    break;
                }
                case "trigger":
                    lines.Add(DescribeTrigger(op, stacks));
                    break;
                case "card":
                    lines.Add(_l.Format("fx.card", _l.Get("card." + p.GetString("id") + ".name")));
                    break;
            }
        }

        /// <summary>Rules whose value is a fraction shown as a percentage in tooltips.</summary>
        private static readonly HashSet<string> PercentRules = new HashSet<string>
        {
            "burn_power", "overheal_shield", "doom_threshold", "doom_boss", "poison_power", "resonance_bonus", "collapse_radius",
            "collapse_power", "shield_power", "field_duration", "illuminate_power"
        };

        /// <summary>Localization key of a status id used by actions (apply_status) and reactions.</summary>
        public static string StatusKey(string status)
        {
            switch (status)
            {
                case "illuminate": return "status.illuminated";
                case "root": return "status.rooted";
                case "poison": return "status.poisoned";
                case "mark": return "status.marked";
                case "seal": return "status.sealed";
                default: return "status." + status;
            }
        }

        private static bool IsChanceStat(StatId s)
        {
            return s == StatId.CritChance || s == StatId.DamageBonus || s == StatId.ReactionBonus || s == StatId.DamageReduction || s == StatId.StatusPower;
        }

        private string DescribeTrigger(EffectOp op, int stacks)
        {
            ParamBag p = op.Params;
            string when;
            if (op.Trigger == "reaction") when = _l.Format("fx.on.reaction", ReactionName(op.Reaction));
            else if (op.Trigger == "periodic") when = _l.Format("fx.on.periodic", Num(p.Get("interval", 5f)));
            else when = _l.Get("fx.on." + op.Trigger);
            if (p.Has("heroElement")) when += _l.Format("fx.filter.element", _l.Element(ContentDatabase.ParseElement(p.GetString("heroElement"))));
            var qualifiers = new List<string>();
            if (p.Get("every") > 1f) qualifiers.Add(_l.Format("fx.every", Num(p.Get("every"))));
            if (p.Has("chance") && p.Get("chance") < 1f) qualifiers.Add(_l.Format("fx.chance", Pct(p.Get("chance"), false)));
            string what;
            float s = stacks;
            switch (op.Action)
            {
                case "burst":
                {
                    string el = p.GetString("element", "none");
                    string elName = el == "none" ? _l.Get("fx.physical") : _l.Element(ContentDatabase.ParseElement(el));
                    what = _l.Format("fx.do.burst", Pct(p.Get("power", 1f) * s, false), elName, Num(p.Get("radius", 1.2f)));
                    break;
                }
                case "apply_element":
                    what = _l.Format("fx.do.apply_element", _l.Element(ContentDatabase.ParseElement(p.GetString("element"))), Num(p.Get("radius", 1.5f)));
                    break;
                case "chain": what = _l.Format("fx.do.chain", Num(p.Get("bounces", 3f) * s)); break;
                case "heal_team": what = _l.Format("fx.do.heal_team", Pct(p.Get("pct", 0.05f) * s, false)); break;
                case "crystal_shield": what = _l.Format("fx.do.crystal_shield", Pct(p.Get("pct", 0.03f) * s, false)); break;
                case "crystal_heal": what = _l.Format("fx.do.crystal_heal", Pct(p.Get("pct", 0.01f) * s, false)); break;
                case "gold": what = _l.Format("fx.do.gold", Num(p.Get("amount", 1f) * s)); break;
                case "team_buff":
                case "hero_buff":
                {
                    StatId stat = ContentDatabase.ParseStat(p.GetString("stat", "attack"));
                    what = _l.Format(op.Action == "team_buff" ? "fx.do.team_buff" : "fx.do.hero_buff", Pct(p.Get("pct", 0.2f) * s, false), _l.Stat(stat), Num(p.Get("duration", 4f)));
                    break;
                }
                case "revive": what = _l.Format("fx.do.revive", Pct(p.Get("hpPct", 0.5f), false)); break;
                case "zone": what = _l.Format("fx.do.zone", _l.Get("zone." + p.GetString("kind", "burning_ground")), Num(p.Get("radius", 1.4f)), Num(p.Get("duration", 3f))); break;
                case "refund_cooldown": what = _l.Format("fx.do.refund_cooldown", Num(p.Get("seconds", 1f) * s)); break;
                case "team_refund_cooldown": what = _l.Format("fx.do.team_refund_cooldown", Num(p.Get("seconds", 1f) * s)); break;
                case "echo_cast": what = _l.Format("fx.do.echo_cast", Pct(p.Get("power", 0.5f) * s, false)); break;
                case "execute": what = _l.Format("fx.do.execute", Pct(p.Get("threshold", 0.12f), false)); break;
                case "slow_all": what = _l.Format("fx.do.slow_all", Num(p.Get("radius", 3f)), Pct(p.Get("slow", 0.3f), false), Num(p.Get("duration", 2f))); break;
                case "apply_status":
                {
                    string status = _l.Get(StatusKey(p.GetString("status")));
                    what = p.Get("radius") > 0f ? _l.Format("fx.do.apply_status_area", status, Num(p.Get("radius"))) : _l.Format("fx.do.apply_status", status);
                    break;
                }
                case "field": what = _l.Format("fx.do.field", _l.Get("field." + p.GetString("field") + ".name"), Num(p.Get("radius", 1.6f)), Num(p.Get("duration", 3f))); break;
                case "team_shield": what = _l.Format("fx.do.team_shield", Pct(p.Get("pct", 0.1f) * s, false)); break;
                case "cleanse_team": what = _l.Get("fx.do.cleanse_team"); break;
                default: what = op.Action; break;
            }
            string text = when + (qualifiers.Count > 0 ? " (" + string.Join(", ", qualifiers) + ")" : "") + ": " + what;
            if (p.Get("cooldown") > 0f) text += _l.Format("fx.cooldown", Num(p.Get("cooldown")));
            if (p.Get("usesPerWave") > 0f) text += _l.Format("fx.uses", Num(p.Get("usesPerWave")));
            return text;
        }

        public string SkillDescription(SkillDef s) => _l.SkillText(s, s.DescKey);

        public static string Join(List<string> lines) => string.Join("\n", lines);

        public static string F(float v) => v.ToString("0.#", CultureInfo.InvariantCulture);
    }
}
