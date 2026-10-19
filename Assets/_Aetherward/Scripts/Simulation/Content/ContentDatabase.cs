using System;
using System.Collections.Generic;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Content
{
    public sealed class LaneDef
    {
        public string Id;
        public string NameKey;
        public List<Vec2> Points = new List<Vec2>(); // spawn -> crystal
    }

    public sealed class ArenaDef
    {
        public string Id;
        public float HalfWidth = 12f;
        public float HalfHeight = 7f;
        public float CrystalRadius = 0.85f;
        public List<Vec2> Nodes = new List<Vec2>();
        public List<LaneDef> Lanes = new List<LaneDef>();
    }

    /// <summary>
    /// Immutable registry of all authored content, keyed by stable string ids. Built once at boot from
    /// JSON text (Unity: Resources/Content/*.json TextAssets; tests: files on disk).
    /// </summary>
    public sealed class ContentDatabase
    {
        public readonly Dictionary<string, HeroDef> Heroes = new Dictionary<string, HeroDef>();
        public readonly List<HeroDef> HeroList = new List<HeroDef>();
        public readonly Dictionary<string, EvolutionDef> Evolutions = new Dictionary<string, EvolutionDef>();
        public readonly Dictionary<string, EnemyDef> Enemies = new Dictionary<string, EnemyDef>();
        public readonly Dictionary<string, ReactionDef> Reactions = new Dictionary<string, ReactionDef>();
        public readonly ReactionDef[] ReactionByPair = new ReactionDef[ElementUtil.PairSlots];
        /// <summary>Category of every element pair; pairs without a reaction are Neutral or BlockedByDesign.</summary>
        public readonly ReactionCategory[] PairCategory = new ReactionCategory[ElementUtil.PairSlots];
        public readonly Dictionary<int, string> PairNote = new Dictionary<int, string>();
        public readonly Dictionary<string, FieldDef> Fields = new Dictionary<string, FieldDef>();
        public readonly ElementDef[] ElementDefs = new ElementDef[ElementUtil.Count];
        public readonly Dictionary<string, TraitDef> Traits = new Dictionary<string, TraitDef>();
        public readonly List<TraitDef> TraitList = new List<TraitDef>();
        public readonly Dictionary<string, RelicDef> Relics = new Dictionary<string, RelicDef>();
        public readonly List<RelicDef> RelicList = new List<RelicDef>();
        public readonly List<FusionDef> Fusions = new List<FusionDef>();
        public readonly Dictionary<string, CardDef> Cards = new Dictionary<string, CardDef>();
        public readonly List<CardDef> CardList = new List<CardDef>();
        public readonly List<WaveDef> Waves = new List<WaveDef>();
        public readonly Dictionary<string, EventDef> Events = new Dictionary<string, EventDef>();
        public readonly Dictionary<string, AffixDef> Affixes = new Dictionary<string, AffixDef>();
        public readonly Dictionary<string, Dictionary<string, string>> Strings = new Dictionary<string, Dictionary<string, string>>();
        public EconomyDef Economy = new EconomyDef();
        public DifficultyDef Difficulty = new DifficultyDef();
        public ArenaDef Arena = new ArenaDef();

        public ReactionDef ReactionFor(Element a, Element b) => ReactionByPair[ElementUtil.PairIndex(a, b)];
        public ReactionCategory CategoryFor(Element a, Element b) => PairCategory[ElementUtil.PairIndex(a, b)];
        public ElementDef ElementDef(Element e) => ElementDefs[(int)e];

        /// <summary>Content file names expected under Resources/Content (without extension).</summary>
        public static readonly string[] FileNames =
        {
            "elements", "traits", "heroes", "evolutions", "enemies", "reactions", "relics", "cards", "waves", "events", "economy", "arena", "difficulty",
            "loc_en", "loc_vi"
        };

        public static ContentDatabase Load(Func<string, string> readFile)
        {
            var db = new ContentDatabase();
            db.LoadElements(Parse(readFile, "elements"));
            db.LoadTraits(Parse(readFile, "traits"));
            db.LoadHeroes(Parse(readFile, "heroes"));
            db.LoadEvolutions(Parse(readFile, "evolutions"));
            db.LoadEnemies(Parse(readFile, "enemies"));
            db.LoadReactions(Parse(readFile, "reactions"));
            db.LoadRelics(Parse(readFile, "relics"));
            db.LoadCards(Parse(readFile, "cards"));
            db.LoadWaves(Parse(readFile, "waves"));
            db.LoadEvents(Parse(readFile, "events"));
            db.LoadEconomy(Parse(readFile, "economy"));
            db.LoadArena(Parse(readFile, "arena"));
            db.LoadDifficulty(Parse(readFile, "difficulty"));
            db.LoadStrings("en", Parse(readFile, "loc_en"));
            db.LoadStrings("vi", Parse(readFile, "loc_vi"));
            return db;
        }

        private static JsonNode Parse(Func<string, string> readFile, string name)
        {
            string text = readFile(name);
            if (text == null) throw new InvalidOperationException("Missing content file: " + name);
            try
            {
                return JsonNode.Parse(text);
            }
            catch (FormatException e)
            {
                throw new FormatException(name + ".json: " + e.Message, e);
            }
        }

        // ------------------------------------------------------------------ heroes

        private void LoadHeroes(JsonNode root)
        {
            foreach (JsonNode n in root["heroes"].Items)
            {
                var h = new HeroDef
                {
                    Id = n.Str("id"),
                    NameKey = n.Str("name", "hero." + n.Str("id") + ".name"),
                    TitleKey = "hero." + n.Str("id") + ".title",
                    Element = ParseElement(n.Str("element")),
                    Role = ParseEnum<HeroRole>(n.Str("role"), "role"),
                    Targeting = ParseEnum<TargetProfile>(n.Str("targeting", "nearest"), "targeting"),
                    Melee = n.Bool("melee"),
                    GrowthPerLevel = n.Float("growth", 0.12f),
                    StarterUnlocked = n.Bool("starter"),
                    RecruitCost = n.Int("cost", 6),
                    Silhouette = n.Str("silhouette", "")
                };
                JsonNode stats = n["stats"];
                ApplyStatDefaults(h.BaseStats);
                foreach (string key in stats.Keys) h.BaseStats[(int)ParseStat(key)] = stats.Float(key);
                h.Basic = new AttackDef
                {
                    Kind = n["basic"].Str("kind", "projectile"),
                    Multiplier = n["basic"].Float("mult", 1f),
                    Gauge = n["basic"].Float("gauge", 1f),
                    ProjectileSpeed = n["basic"].Float("speed", 10f),
                    Params = ParamBag.FromJson(n["basic"], "kind", "mult", "gauge", "speed")
                };
                h.Skill = ParseSkill(n["skill"], h.Id);
                h.PassiveKind = n["passive"].Str("kind");
                h.PassiveParams = ParamBag.FromJson(n["passive"], "kind");
                h.PassiveNameKey = "hero." + h.Id + ".passive.name";
                h.PassiveDescKey = "hero." + h.Id + ".passive.desc";
                h.Evolutions = n.StringList("evolutions");
                Add(Heroes, h.Id, h, "hero");
                HeroList.Add(h);
            }
            LoadFields(root["fields"]);
        }

        public static void ApplyStatDefaults(float[] s)
        {
            s[(int)StatId.AttackInterval] = 1.1f;
            s[(int)StatId.Range] = 1f;
            s[(int)StatId.SkillCooldown] = 1f; // multiplier on skill cooldown
            s[(int)StatId.CritChance] = 0.05f;
            s[(int)StatId.CritMultiplier] = 1.5f;
            s[(int)StatId.Threat] = 1f;
            s[(int)StatId.MoveSpeed] = 2.4f;
            s[(int)StatId.HealPower] = 1f;
            s[(int)StatId.LeashRadius] = 0.25f;
            s[(int)StatId.SkillPower] = 1f;
        }

        private static SkillDef ParseSkill(JsonNode n, string heroId)
        {
            return new SkillDef
            {
                Kind = n.Str("kind"),
                Cooldown = n.Float("cooldown", 6f),
                Multiplier = n.Float("mult", 1f),
                Gauge = n.Float("gauge", 1f),
                Params = ParamBag.FromJson(n, "kind", "cooldown", "mult", "gauge"),
                NameKey = "hero." + heroId + ".skill.name",
                DescKey = "hero." + heroId + ".skill.desc"
            };
        }

        private void LoadEvolutions(JsonNode root)
        {
            foreach (JsonNode n in root["evolutions"].Items)
            {
                string id = n.Str("id");
                var e = new EvolutionDef
                {
                    Id = id,
                    HeroId = n.Str("hero"),
                    NameKey = "evo." + id + ".name",
                    DescKey = "evo." + id + ".desc",
                    PassiveKind = n["passive"].Str("kind"),
                    PassiveParams = n.Has("passive") ? ParamBag.FromJson(n["passive"], "kind") : null,
                    Effects = ParseEffects(n["effects"])
                };
                if (n.Has("skill"))
                {
                    JsonNode s = n["skill"];
                    e.Skill = new SkillOverride
                    {
                        Kind = s.Str("kind"),
                        Cooldown = s.Has("cooldown") ? s.Float("cooldown") : (float?)null,
                        Multiplier = s.Has("mult") ? s.Float("mult") : (float?)null,
                        Gauge = s.Has("gauge") ? s.Float("gauge") : (float?)null,
                        Params = ParamBag.FromJson(s, "kind", "cooldown", "mult", "gauge"),
                        NameKey = "evo." + id + ".skill.name",
                        DescKey = "evo." + id + ".skill.desc"
                    };
                }
                if (n.Has("role")) e.RoleOverride = ParseEnum<HeroRole>(n.Str("role"), "role");
                if (n.Has("targeting")) e.TargetingOverride = ParseEnum<TargetProfile>(n.Str("targeting"), "targeting");
                if (n.Has("melee")) e.MeleeOverride = n.Bool("melee");
                Add(Evolutions, id, e, "evolution");
            }
        }

        // ------------------------------------------------------------------ enemies

        private void LoadEnemies(JsonNode root)
        {
            foreach (JsonNode n in root["enemies"].Items)
            {
                string id = n.Str("id");
                var e = new EnemyDef
                {
                    Id = id,
                    NameKey = "enemy." + id + ".name",
                    DescKey = "enemy." + id + ".desc",
                    Behavior = ParseEnum<EnemyBehavior>(n.Str("behavior", "melee"), "behavior"),
                    Hp = n.Float("hp", 30f),
                    Attack = n.Float("attack", 5f),
                    Defense = n.Float("defense", 0f),
                    Speed = n.Float("speed", 1.2f),
                    AttackInterval = n.Float("attackInterval", 1.2f),
                    AttackRange = n.Float("range", 0.7f),
                    CrystalDamage = n.Float("crystalDamage", n.Float("attack", 5f)),
                    Tenacity = n.Float("tenacity", 0f),
                    Radius = n.Float("radius", 0.32f),
                    Gold = n.Int("gold", 1),
                    Essence = n.Int("essence", 0),
                    Elite = n.Bool("elite"),
                    Boss = n.Bool("boss"),
                    Threat = n.Int("threat", 1),
                    Params = ParamBag.FromJson(n["params"]),
                    Tags = n.StringList("tags")
                };
                foreach (string key in n["resist"].Keys) e.Resist[(int)ParseElement(key)] = n["resist"].Float(key);
                Add(Enemies, id, e, "enemy");
            }
            foreach (JsonNode n in root["affixes"].Items)
            {
                var a = new AffixDef { Id = n.Str("id"), NameKey = "affix." + n.Str("id") + ".name", Params = ParamBag.FromJson(n, "id") };
                Add(Affixes, a.Id, a, "affix");
            }
        }

        // ------------------------------------------------------------------ reactions

        /// <summary>The 15 launch reactions keep their hand-written resolution (regression safety).</summary>
        public static readonly string[] LegacyReactionIds =
        {
            "vaporize", "overload", "melt", "firestorm", "magma", "electrocharge", "freeze", "rainstorm", "mudfield",
            "superconduct", "thunderstorm", "magnetize", "blizzard", "ice_spikes", "sandstorm"
        };

        private void LoadElements(JsonNode root)
        {
            foreach (JsonNode n in root["elements"].Items)
            {
                Element el = ParseElement(n.Str("id"));
                if (el == Element.None) throw new FormatException("elements.json: 'none' is not a definable element");
                if (ElementDefs[(int)el] != null) throw new FormatException("Duplicate element " + n.Str("id"));
                ElementDefs[(int)el] = new ElementDef
                {
                    Element = el,
                    Id = n.Str("id"),
                    NameKey = "element." + n.Str("id"),
                    Color = n.Str("color", "#ffffff"),
                    StatusKey = n.Str("status", n.Str("id")),
                    Stage = n.Int("stage"),
                    OnApply = ParseActions(n["onApply"]),
                    OnRefresh = ParseActions(n["onRefresh"])
                };
            }
            foreach (Element e in ElementUtil.All)
                if (ElementDefs[(int)e] == null) throw new FormatException("elements.json is missing " + ElementUtil.Key(e));
        }

        private void LoadTraits(JsonNode root)
        {
            foreach (JsonNode n in root["traits"].Items)
            {
                string id = n.Str("id");
                var t = new TraitDef
                {
                    Id = id,
                    NameKey = "trait." + id + ".name",
                    DescKey = "trait." + id + ".desc",
                    Rarity = ParseEnum<Rarity>(n.Str("rarity", "common"), "rarity"),
                    Weight = n.Float("weight", 1f),
                    RequireElement = ParseElement(n["requires"].Str("element")),
                    Effects = ParseEffects(n["effects"]),
                    Behaviour = ParamBag.FromJson(n["behaviour"])
                };
                foreach (string r in n["requires"].StringList("roles")) t.RequireRoles.Add(ParseEnum<HeroRole>(r, "role"));
                Add(Traits, id, t, "trait");
                TraitList.Add(t);
            }
        }

        private void LoadReactions(JsonNode root)
        {
            LoadFields(root["fields"]);
            LoadReactionList(root);
        }

        /// <summary>Fields may be declared next to reactions or next to the hero skills that spawn them.</summary>
        private void LoadFields(JsonNode arr)
        {
            foreach (JsonNode n in arr.Items)
            {
                string id = n.Str("id");
                var f = new FieldDef
                {
                    Id = id,
                    NameKey = "field." + id + ".name",
                    Element = ParseElement(n.Str("element")),
                    Tick = n.Float("tick", 0.5f),
                    DamageMult = n.Float("damageMult"),
                    DamageAsReaction = n.Bool("reactionDamage"),
                    Slow = n.Float("slow"),
                    Pull = n.Float("pull"),
                    Grow = n.Float("grow"),
                    MaxRadiusMult = n.Float("maxRadiusMult", 1.6f),
                    HeroHealPct = n.Float("heroHealPct"),
                    HeroDamageReduction = n.Float("heroDamageReduction"),
                    HeroHaste = n.Float("heroHaste"),
                    Cleanse = n.Bool("cleanse"),
                    CrystalShieldPct = n.Float("crystalShieldPct"),
                    EnemyVuln = n.Float("enemyVuln"),
                    EnemyWeaken = n.Float("enemyWeaken"),
                    ReactionAmp = n.Float("reactionAmp"),
                    BlockBolts = n.Bool("blockBolts"),
                    Zap = n.Float("zap"),
                    MaxCount = n.Int("maxCount", 4),
                    Shape = n.Str("shape", "circle"),
                    OnTick = ParseActions(n["onTick"]),
                    OnEnd = ParseActions(n["onEnd"]),
                    Params = ParamBag.FromJson(n["params"])
                };
                Add(Fields, id, f, "field");
            }
        }

        private void LoadReactionList(JsonNode root)
        {
            foreach (JsonNode n in root["reactions"].Items)
            {
                string id = n.Str("id");
                ReactionDef r = ParseReaction(n, id);
                r.Category = n.Has("category") ? ParseEnum<ReactionCategory>(n.Str("category"), "reaction category") : ReactionCategory.Signature;
                r.Legacy = !n.Has("ops");
                if (r.Legacy && Array.IndexOf(LegacyReactionIds, id) < 0)
                    throw new FormatException("Reaction " + id + " has no ops and is not a launch reaction");
                RegisterReaction(r);
            }

            foreach (JsonNode n in root["neutral"].Items) RegisterNoReaction(n, ReactionCategory.Neutral);
            foreach (JsonNode n in root["blocked"].Items) RegisterNoReaction(n, ReactionCategory.BlockedByDesign);

            // Every remaining primary pair gets the documented generic interaction (never silently ignored).
            JsonNode g = root["generic"];
            if (g.Kind == JsonKind.Object)
            {
                List<ActionOp> ops = ParseActions(g["ops"]);
                for (int i = 0; i < ElementUtil.All.Length; i++)
                {
                    for (int j = i + 1; j < ElementUtil.All.Length; j++)
                    {
                        Element a = ElementUtil.All[i], b = ElementUtil.All[j];
                        int pair = ElementUtil.PairIndex(a, b);
                        if (ReactionByPair[pair] != null || PairNote.ContainsKey(pair)) continue;
                        string id = "generic_" + ElementUtil.Key(a) + "_" + ElementUtil.Key(b);
                        ReactionDef r = ParseReaction(g, id);
                        r.A = a;
                        r.B = b;
                        r.NameKey = "reaction.generic.name";
                        r.DescKey = "reaction.generic.desc";
                        r.Category = ReactionCategory.Generic;
                        r.AutoNamed = true;
                        r.Ops = ops;
                        RegisterReaction(r);
                    }
                }
            }
        }

        private ReactionDef ParseReaction(JsonNode n, string id)
        {
            var r = new ReactionDef
            {
                Id = id,
                A = ParseElement(n.Str("a")),
                B = ParseElement(n.Str("b")),
                NameKey = "reaction." + id + ".name",
                DescKey = "reaction." + id + ".desc",
                BaseDamage = n.Float("base", 10f),
                AttackScale = n.Float("attackScale", 0.5f),
                Radius = n.Float("radius", 0f),
                Duration = n.Float("duration", 0f),
                Consume = n.Float("consume", 1f),
                Cooldown = n.Float("cooldown", 0.6f),
                Params = ParamBag.FromJson(n["params"]),
                Ops = ParseActions(n["ops"]),
                Sound = n.Str("sound")
            };
            return r;
        }

        private void RegisterReaction(ReactionDef r)
        {
            if (r.A == r.B || r.A == Element.None || r.B == Element.None)
                throw new FormatException("Reaction " + r.Id + " must combine two distinct elements");
            int pair = ElementUtil.PairIndex(r.A, r.B);
            if (ReactionByPair[pair] != null || PairNote.ContainsKey(pair)) throw new FormatException("Duplicate reaction pair for " + r.Id);
            ReactionByPair[pair] = r;
            PairCategory[pair] = r.Category;
            Add(Reactions, r.Id, r, "reaction");
        }

        private void RegisterNoReaction(JsonNode n, ReactionCategory category)
        {
            Element a = ParseElement(n.Str("a")), b = ParseElement(n.Str("b"));
            if (a == b || a == Element.None || b == Element.None) throw new FormatException("Invalid " + category + " pair");
            int pair = ElementUtil.PairIndex(a, b);
            if (ReactionByPair[pair] != null || PairNote.ContainsKey(pair)) throw new FormatException("Pair listed twice: " + n.Str("a") + "+" + n.Str("b"));
            PairCategory[pair] = category;
            PairNote[pair] = n.Str("reason", "");
        }

        public static List<ActionOp> ParseActions(JsonNode arr)
        {
            var list = new List<ActionOp>();
            foreach (JsonNode n in arr.Items) list.Add(ParseAction(n));
            return list;
        }

        public static ActionOp ParseAction(JsonNode n)
        {
            var op = new ActionOp
            {
                Op = n.Str("op"),
                Status = n.Str("status"),
                Field = n.Str("field"),
                Area = n.Bool("area"),
                Mult = n.Float("mult", 1f),
                Params = ParamBag.FromJson(n, "op", "element", "status", "field", "area", "mult")
            };
            if (string.IsNullOrEmpty(op.Op)) throw new FormatException("Action without op");
            string el = n.Str("element");
            if (el == "$incoming") op.ElementRef = ActionOp.ElementIncoming;
            else if (el == "$existing") op.ElementRef = ActionOp.ElementExisting;
            else op.Element = ParseElement(el);
            return op;
        }

        // ------------------------------------------------------------------ relics, cards

        private void LoadRelics(JsonNode root)
        {
            foreach (JsonNode n in root["relics"].Items)
            {
                string id = n.Str("id");
                var r = new RelicDef
                {
                    Id = id,
                    NameKey = "relic." + id + ".name",
                    DescKey = "relic." + id + ".desc",
                    Family = ParseEnum<RelicFamily>(n.Str("family", "combat"), "family"),
                    Rarity = ParseEnum<Rarity>(n.Str("rarity", "common"), "rarity"),
                    Price = n.Int("price", 14),
                    Fusion = n.Bool("fusion"),
                    StarterUnlocked = n.Bool("starter", true),
                    Effects = ParseEffects(n["effects"]),
                    Tags = n.StringList("tags")
                };
                Add(Relics, id, r, "relic");
                RelicList.Add(r);
            }
            foreach (JsonNode n in root["fusions"].Items)
                Fusions.Add(new FusionDef { A = n.Str("a"), B = n.Str("b"), Result = n.Str("result") });
        }

        private void LoadCards(JsonNode root)
        {
            foreach (JsonNode n in root["cards"].Items)
            {
                string id = n.Str("id");
                JsonNode req = n["requires"];
                var c = new CardDef
                {
                    Id = id,
                    NameKey = "card." + id + ".name",
                    DescKey = "card." + id + ".desc",
                    Type = ParseEnum<CardType>(n.Str("type", "stat"), "card type"),
                    Rarity = ParseEnum<Rarity>(n.Str("rarity", "common"), "rarity"),
                    MaxStacks = n.Int("maxStacks", 1),
                    Weight = n.Float("weight", 1f),
                    Effects = ParseEffects(n["effects"]),
                    Tags = n.StringList("tags"),
                    DrawbackKey = n.Has("drawback") ? "card." + id + ".drawback" : null,
                    Requires = new CardRequirement
                    {
                        Element = ParseElement(req.Str("element")),
                        Role = req.Has("role") ? ParseEnum<HeroRole>(req.Str("role"), "role") : (HeroRole?)null,
                        Hero = req.Str("hero"),
                        MinLevel = req.Int("minLevel", 0),
                        Relic = req.Str("relic"),
                        Evolved = req.Bool("evolved")
                    }
                };
                Add(Cards, id, c, "card");
                CardList.Add(c);
            }
        }

        public static List<EffectOp> ParseEffects(JsonNode arr)
        {
            var list = new List<EffectOp>();
            foreach (JsonNode n in arr.Items) list.Add(ParseEffect(n));
            return list;
        }

        public static EffectOp ParseEffect(JsonNode n)
        {
            var op = new EffectOp
            {
                Op = n.Str("op"),
                Value = n.Float("value"),
                Percent = n.Bool("pct"),
                Reaction = n.Str("reaction"),
                Trigger = n.Str("on"),
                Action = n.Str("action"),
                Rule = n.Str("rule"),
                Params = ParamBag.FromJson(n, "op", "stat", "value", "pct", "scope", "reaction", "on", "action", "rule")
            };
            if (string.IsNullOrEmpty(op.Op)) throw new FormatException("Effect without op");
            if (n.Has("stat")) op.Stat = ParseStat(n.Str("stat"));
            JsonNode scope = n["scope"];
            if (scope.Kind == JsonKind.Object)
            {
                op.ScopeElement = ParseElement(scope.Str("element"));
                if (scope.Has("role")) op.ScopeRole = ParseEnum<HeroRole>(scope.Str("role"), "role");
                op.ScopeHero = scope.Str("hero");
                op.ScopeMelee = scope.Bool("melee");
                op.ScopeRanged = scope.Bool("ranged");
            }
            return op;
        }

        // ------------------------------------------------------------------ waves, events, economy, arena

        private void LoadWaves(JsonNode root)
        {
            foreach (JsonNode n in root["waves"].Items)
            {
                var w = new WaveDef
                {
                    Number = n.Int("wave"),
                    NameKey = "wave." + n.Int("wave") + ".name",
                    HintKey = "wave." + n.Int("wave") + ".hint",
                    Gold = n.Int("gold", 10),
                    Essence = n.Int("essence", 0),
                    TimeLimit = n.Float("timeLimit", 75f),
                    Boss = n.Bool("boss"),
                    Elite = n.Bool("elite"),
                    Modifiers = n.StringList("modifiers"),
                    BossPool = n.StringList("bossPool")
                };
                foreach (JsonNode l in n["lanes"].Items) w.Lanes.Add(l.AsInt());
                foreach (string r in n.StringList("rewards")) w.Rewards.Add(ParseEnum<RewardKind>(r, "reward"));
                foreach (JsonNode g in n["groups"].Items)
                {
                    w.Groups.Add(new SpawnGroup
                    {
                        Enemy = g.Str("enemy"),
                        Count = g.Int("count", 1),
                        Lane = g.Int("lane", -1),
                        Start = g.Float("start", 0f),
                        Interval = g.Float("interval", 0.6f),
                        Elite = g.Bool("elite"),
                        Affix = g.Str("affix")
                    });
                }
                Waves.Add(w);
            }
            Waves.Sort((a, b) => a.Number.CompareTo(b.Number));
        }

        private void LoadEvents(JsonNode root)
        {
            foreach (JsonNode n in root["events"].Items)
            {
                string id = n.Str("id");
                var e = new EventDef { Id = id, NameKey = "event." + id + ".name", DescKey = "event." + id + ".desc" };
                int i = 0;
                foreach (JsonNode o in n["options"].Items)
                {
                    e.Options.Add(new EventOption
                    {
                        TextKey = "event." + id + ".opt" + i,
                        DrawbackKey = o.Has("drawback") ? "event." + id + ".opt" + i + ".drawback" : null,
                        Effects = ParseEffects(o["effects"]),
                        Gold = o.Int("gold"),
                        Essence = o.Int("essence"),
                        CrystalHpPct = o.Float("crystalHpPct"),
                        GrantRelic = o.Str("relic"),
                        WaveModifier = o.Str("waveModifier")
                    });
                    i++;
                }
                Add(Events, id, e, "event");
            }
        }

        private void LoadEconomy(JsonNode n)
        {
            var e = new EconomyDef
            {
                StartGold = n.Int("startGold", 8),
                CrystalHp = n.Int("crystalHp", 1000),
                RerollBaseCost = n.Int("rerollBaseCost", 2),
                RerollCostStep = n.Int("rerollCostStep", 1),
                ReviveBaseCost = n.Int("reviveBaseCost", 5),
                ReviveCostPerWave = n.Float("reviveCostPerWave", 0.5f),
                RepairCost = n.Int("repairCost", 4),
                RepairPct = n.Float("repairPct", 0.15f),
                InterestPer10 = n.Float("interestPer10", 1f),
                InterestCap = n.Int("interestCap", 4),
                ShopPriceGrowthPerWave = n.Float("shopPriceGrowthPerWave", 0.035f),
                RelicBasePrice = n.Int("relicBasePrice", 14),
                MaxHeroes = n.Int("maxHeroes", 6),
                LevelCap = n.Int("levelCap", 5),
                EvolutionEssence = n.Int("evolutionEssence", 3),
                SurvivorHealPct = n.Float("survivorHealPct", 0.25f),
                EnemyHpGrowth = n.Float("enemyHpGrowth", 0.16f),
                EnemyHpGrowthQuad = n.Float("enemyHpGrowthQuad", 0.012f),
                EnemyDamageGrowth = n.Float("enemyDamageGrowth", 0.07f),
                ReactionLevelGrowth = n.Float("reactionLevelGrowth", 0.12f),
                MaxActiveEnemies = n.Int("maxActiveEnemies", 160),
                XpPerWave = n.Int("xpPerWave", 1),
                XpBossBonus = n.Int("xpBossBonus", 1)
            };
            if (n.Has("xpToLevel"))
            {
                var xs = n["xpToLevel"].Items;
                e.XpToLevel = new int[xs.Count];
                for (int i = 0; i < xs.Count; i++) e.XpToLevel[i] = xs[i].AsInt();
            }
            foreach (JsonNode w in n["shopWaves"].Items) e.ShopWaves.Add(w.AsInt());
            Economy = e;
        }

        private void LoadArena(JsonNode n)
        {
            var a = new ArenaDef
            {
                Id = n.Str("id", "arcane_sanctuary"),
                HalfWidth = n.Float("halfWidth", 12f),
                HalfHeight = n.Float("halfHeight", 7f),
                CrystalRadius = n.Float("crystalRadius", 0.85f)
            };
            foreach (JsonNode p in n["nodes"].Items) a.Nodes.Add(new Vec2(p[0].AsFloat(), p[1].AsFloat()));
            foreach (JsonNode l in n["lanes"].Items)
            {
                var lane = new LaneDef { Id = l.Str("id"), NameKey = "lane." + l.Str("id") };
                foreach (JsonNode p in l["points"].Items) lane.Points.Add(new Vec2(p[0].AsFloat(), p[1].AsFloat()));
                a.Lanes.Add(lane);
            }
            Arena = a;
        }

        public static readonly string[] KnownDifficultyModules =
        {
            "frenzy", "enemy_speed", "enemy_damage", "enemy_hp", "crystal_max", "shop_prices", "blocked_node", "elite_affix", "boss_enrage",
            "hazard_shift", "split_lanes", "rarity_shift", "double_elite", "reroll_cost"
        };

        private void LoadDifficulty(JsonNode n)
        {
            var d = new DifficultyDef { HpPerLevel = n.Float("hpPerLevel", 0.08f) };
            foreach (JsonNode l in n["levels"].Items)
            {
                int level = l.Int("level");
                if (level > d.MaxLevel) d.MaxLevel = level;
                foreach (JsonNode m in l["modules"].Items)
                {
                    string id = m.Str("id");
                    if (Array.IndexOf(KnownDifficultyModules, id) < 0) throw new FormatException("difficulty.json: unknown module " + id);
                    d.Modules.Add(new DifficultyModule { Level = level, Id = id, Value = m.Float("value", 1f) });
                }
            }
            Difficulty = d;
        }

        private void LoadStrings(string lang, JsonNode n)
        {
            var table = new Dictionary<string, string>(StringComparer.Ordinal);
            foreach (string key in n.Keys) table[key] = n.Str(key);
            Strings[lang] = table;
        }

        // ------------------------------------------------------------------ helpers

        private static void Add<T>(Dictionary<string, T> dict, string id, T value, string kind)
        {
            if (string.IsNullOrEmpty(id)) throw new FormatException(kind + " without id");
            if (dict.ContainsKey(id)) throw new FormatException("Duplicate " + kind + " id '" + id + "'");
            dict[id] = value;
        }

        public static Element ParseElement(string s)
        {
            if (!ElementUtil.TryParse(s, out Element e)) throw new FormatException("Unknown element '" + s + "'");
            return e;
        }

        public static StatId ParseStat(string s)
        {
            if (!EnumParse.TryParse(s, out StatId stat) || stat == StatId.Count) throw new FormatException("Unknown stat '" + s + "'");
            return stat;
        }

        public static T ParseEnum<T>(string s, string what) where T : struct
        {
            if (!EnumParse.TryParse(s, out T v)) throw new FormatException("Unknown " + what + " '" + s + "'");
            return v;
        }
    }
}
