using System.Collections.Generic;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Content
{
    /// <summary>Named numeric/string parameters for skills, behaviours and effect ops.</summary>
    public sealed class ParamBag
    {
        private readonly Dictionary<string, float> _numbers = new Dictionary<string, float>();
        private readonly Dictionary<string, string> _strings = new Dictionary<string, string>();

        public static ParamBag FromJson(JsonNode node, params string[] skipKeys)
        {
            var bag = new ParamBag();
            if (node == null || node.Kind != JsonKind.Object) return bag;
            foreach (string key in node.Keys)
            {
                if (System.Array.IndexOf(skipKeys, key) >= 0) continue;
                JsonNode v = node[key];
                if (v.Kind == JsonKind.Number) bag._numbers[key] = v.AsFloat();
                else if (v.Kind == JsonKind.String) bag._strings[key] = v.AsString();
                else if (v.Kind == JsonKind.Bool) bag._numbers[key] = v.AsBool() ? 1f : 0f;
            }
            return bag;
        }

        public float Get(string key, float fallback = 0f) => _numbers.TryGetValue(key, out float v) ? v : fallback;
        public string GetString(string key, string fallback = null) => _strings.TryGetValue(key, out string v) ? v : fallback;
        public bool Has(string key) => _numbers.ContainsKey(key) || _strings.ContainsKey(key);
        public bool Flag(string key) => _numbers.TryGetValue(key, out float v) && v != 0f;
        public void Set(string key, float value) => _numbers[key] = value;
        public void SetString(string key, string value) => _strings[key] = value;
        public IEnumerable<string> NumberKeys => _numbers.Keys;
        public IEnumerable<string> StringKeys => _strings.Keys;

        public ParamBag Clone()
        {
            var b = new ParamBag();
            foreach (var kv in _numbers) b._numbers[kv.Key] = kv.Value;
            foreach (var kv in _strings) b._strings[kv.Key] = kv.Value;
            return b;
        }

        /// <summary>Returns a copy with overrides applied on top (used by evolutions).</summary>
        public ParamBag Merge(ParamBag overrides)
        {
            ParamBag b = Clone();
            if (overrides == null) return b;
            foreach (var kv in overrides._numbers) b._numbers[kv.Key] = kv.Value;
            foreach (var kv in overrides._strings) b._strings[kv.Key] = kv.Value;
            return b;
        }
    }

    public sealed class AttackDef
    {
        public string Kind;            // "projectile" | "melee"
        public float Multiplier = 1f;
        public float Gauge = 1f;       // element units applied per hit
        public float ProjectileSpeed = 9f;
        public ParamBag Params = new ParamBag();
    }

    public sealed class SkillDef
    {
        public string Kind;            // behaviour key interpreted by HeroSkills
        public float Cooldown = 6f;
        public float Multiplier = 1f;
        public float Gauge = 1f;
        public ParamBag Params = new ParamBag();
        public string NameKey;
        public string DescKey;

        public SkillDef With(SkillOverride o)
        {
            if (o == null) return this;
            return new SkillDef
            {
                Kind = o.Kind ?? Kind,
                Cooldown = o.Cooldown ?? Cooldown,
                Multiplier = o.Multiplier ?? Multiplier,
                Gauge = o.Gauge ?? Gauge,
                Params = Params.Merge(o.Params),
                NameKey = o.NameKey ?? NameKey,
                DescKey = o.DescKey ?? DescKey
            };
        }
    }

    public sealed class SkillOverride
    {
        public string Kind;
        public float? Cooldown;
        public float? Multiplier;
        public float? Gauge;
        public ParamBag Params;
        public string NameKey;
        public string DescKey;
    }

    public sealed class HeroDef
    {
        public string Id;
        public string NameKey;
        public string TitleKey;
        public Element Element;
        public HeroRole Role;
        public readonly float[] BaseStats = new float[(int)StatId.Count];
        public float GrowthPerLevel = 0.12f;  // multiplicative HP/Attack growth per run level
        public TargetProfile Targeting;
        public bool Melee;
        public AttackDef Basic;
        public SkillDef Skill;
        public string PassiveKind;
        public ParamBag PassiveParams = new ParamBag();
        public string PassiveNameKey;
        public string PassiveDescKey;
        public List<string> Evolutions = new List<string>();
        public bool StarterUnlocked;
        public int RecruitCost = 6;
        public string Silhouette; // art hint, used by validators
    }

    public sealed class EvolutionDef
    {
        public string Id;
        public string HeroId;
        public string NameKey;
        public string DescKey;
        public SkillOverride Skill;
        public string PassiveKind;            // optional replacement passive
        public ParamBag PassiveParams;
        public List<EffectOp> Effects = new List<EffectOp>();
        public HeroRole? RoleOverride;
        public TargetProfile? TargetingOverride;
        public bool? MeleeOverride;
    }

    public sealed class EnemyDef
    {
        public string Id;
        public string NameKey;
        public string DescKey;
        public EnemyBehavior Behavior;
        public float Hp;
        public float Attack;
        public float Defense;
        public float Speed;
        public float AttackInterval = 1.2f;
        public float AttackRange = 0.7f;
        public float CrystalDamage;
        public readonly float[] Resist = new float[ElementUtil.Count];
        public float Tenacity;   // 0..1 reduction of crowd control duration/strength
        public float Radius = 0.32f;
        public int Gold = 1;
        public int Essence;
        public bool Elite;
        public bool Boss;
        public int Threat = 1;   // budget points used by the wave director
        public ParamBag Params = new ParamBag();
        public List<string> Tags = new List<string>();
    }

    public sealed class ReactionDef
    {
        public string Id;
        public Element A;
        public Element B;
        public string NameKey;
        public string DescKey;
        public float BaseDamage;      // flat reaction base, scaled by wave level
        public float AttackScale;     // fraction of source attack snapshot
        public float Radius;
        public float Duration;
        public float Consume = 1f;    // gauge units removed from the existing aura
        public float Cooldown = 0.6f; // per-target anti-repeat window for this reaction
        public ParamBag Params = new ParamBag();
    }

    /// <summary>
    /// A declarative effect. Relics, cards, evolutions and pacts are lists of these. Only the op type
    /// is interpreted by code; the owning content id is never inspected by combat logic.
    /// </summary>
    public sealed class EffectOp
    {
        public string Op;              // stat | crystal | enemy | reaction | economy | trigger | rule | gauge
        public StatId Stat;
        public float Value;
        public bool Percent;
        // Scope filters for hero-targeted ops.
        public Element ScopeElement;
        public HeroRole? ScopeRole;
        public string ScopeHero;
        public bool ScopeMelee;
        public bool ScopeRanged;
        // Reaction filter ("*" = all).
        public string Reaction;
        public string Trigger;         // for op == trigger
        public string Action;          // for op == trigger
        public string Rule;            // for op == rule
        public ParamBag Params = new ParamBag();

        public bool MatchesHero(HeroDef hero, bool melee)
        {
            if (ScopeElement != Element.None && hero.Element != ScopeElement) return false;
            if (ScopeRole.HasValue && hero.Role != ScopeRole.Value) return false;
            if (!string.IsNullOrEmpty(ScopeHero) && hero.Id != ScopeHero) return false;
            if (ScopeMelee && !melee) return false;
            if (ScopeRanged && melee) return false;
            return true;
        }
    }

    public sealed class RelicDef
    {
        public string Id;
        public string NameKey;
        public string DescKey;
        public RelicFamily Family;
        public Rarity Rarity;
        public int Price = 10;
        public bool Fusion;          // only obtainable via fusion
        public bool StarterUnlocked = true;
        public List<EffectOp> Effects = new List<EffectOp>();
        public List<string> Tags = new List<string>();
    }

    public sealed class FusionDef
    {
        public string A;
        public string B;
        public string Result;
    }

    public sealed class CardRequirement
    {
        public Element Element;     // roster must contain this element
        public HeroRole? Role;
        public string Hero;         // roster must contain this hero
        public int MinLevel;        // ...at this run level
        public string Relic;        // must own relic
        public bool Evolved;        // that hero must be evolved
    }

    public sealed class CardDef
    {
        public string Id;
        public string NameKey;
        public string DescKey;
        public CardType Type;
        public Rarity Rarity;
        public int MaxStacks = 1;
        public float Weight = 1f;
        public CardRequirement Requires = new CardRequirement();
        public List<EffectOp> Effects = new List<EffectOp>();
        public List<string> Tags = new List<string>();
        public string DrawbackKey;  // for cursed/pact cards: exact drawback text
    }

    public sealed class SpawnGroup
    {
        public string Enemy;
        public int Count = 1;
        public int Lane;            // index into arena lanes; -1 = rotate through wave lanes
        public float Start;
        public float Interval = 0.6f;
        public bool Elite;
        public string Affix;        // optional elite affix id
    }

    public sealed class WaveDef
    {
        public int Number;
        public string NameKey;
        public string HintKey;      // counterplay hint shown during prep
        public List<SpawnGroup> Groups = new List<SpawnGroup>();
        public List<int> Lanes = new List<int>();
        public List<RewardKind> Rewards = new List<RewardKind>();
        public List<string> Modifiers = new List<string>();
        public int Gold = 10;
        public int Essence;
        public float TimeLimit = 75f;
        public bool Boss;
        public bool Elite;
    }

    public sealed class EventDef
    {
        public string Id;
        public string NameKey;
        public string DescKey;
        public List<EventOption> Options = new List<EventOption>();
    }

    public sealed class EventOption
    {
        public string TextKey;
        public string DrawbackKey;
        public List<EffectOp> Effects = new List<EffectOp>();
        public int Gold;
        public int Essence;
        public float CrystalHpPct;  // negative = cost
        public string GrantRelic;
        public string WaveModifier; // applied to next wave (challenge)
    }

    public sealed class AffixDef
    {
        public string Id;
        public string NameKey;
        public ParamBag Params = new ParamBag();
    }

    public sealed class EconomyDef
    {
        public int StartGold = 8;
        public int CrystalHp = 1000;
        public int RerollBaseCost = 2;
        public int RerollCostStep = 1;
        public int ReviveBaseCost = 5;
        public float ReviveCostPerWave = 0.5f;
        public int RepairCost = 4;
        public float RepairPct = 0.15f;
        public float InterestPer10 = 1f;
        public int InterestCap = 4;
        public float ShopPriceGrowthPerWave = 0.035f;
        public int RelicBasePrice = 14;
        public int MaxHeroes = 6;
        public int LevelCap = 5;
        public int[] XpToLevel = { 0, 2, 5, 9, 14 };
        public int EvolutionEssence = 3;
        public float SurvivorHealPct = 0.25f;
        public float PostWaveDraftCount = 3;
        public List<int> ShopWaves = new List<int>();
        public float EnemyHpGrowth = 0.16f;       // linear per wave
        public float EnemyHpGrowthQuad = 0.012f;  // quadratic per wave
        public float EnemyDamageGrowth = 0.07f;
        public float ReactionLevelGrowth = 0.12f;
        public int MaxActiveEnemies = 160;
        public int XpPerWave = 1;
        public int XpBossBonus = 1;
    }
}
