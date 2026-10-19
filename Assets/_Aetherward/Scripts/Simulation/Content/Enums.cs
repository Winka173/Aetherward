namespace Aetherward.Sim.Content
{
    public enum Element
    {
        None = 0,
        Fire = 1,
        Water = 2,
        Lightning = 3,
        Ice = 4,
        Wind = 5,
        Earth = 6,
        // Expansion elements (append-only: values are stable and never reordered).
        Light = 7,
        Shadow = 8,
        Nature = 9,
        Poison = 10,
        Arcane = 11,
        Void = 12
    }

    public enum HeroRole
    {
        Guardian,
        Mage,
        Bruiser,
        Assassin,
        Support,
        Healer,
        Ranger,
        Controller
    }

    /// <summary>
    /// Every stat that the modifier pipeline can touch. Order matters only for array indexing.
    /// AttackInterval and SkillCooldown are "lower is better": percentage modifiers on them are
    /// applied as haste (value / (1 + haste)) so stacking never reaches zero.
    /// </summary>
    public enum StatId
    {
        MaxHp,
        Attack,
        Defense,
        AttackInterval,
        Range,
        SkillCooldown,
        CritChance,
        CritMultiplier,
        ElementalMastery,
        StatusPower,
        Threat,
        MoveSpeed,
        HealPower,
        DamageBonus,
        ReactionBonus,
        DamageReduction,
        LeashRadius,
        SkillPower,
        Count
    }

    public enum TargetProfile
    {
        Nearest,
        NearestToCrystal,
        Cluster,
        Elite,
        Execute,
        ReactionOpportunity,
        LowestHpAlly,
        Strongest
    }

    public enum EnemyBehavior
    {
        Melee,
        Runner,
        Ranged,
        Sapper,
        Summoner,
        Buffer,
        Boss
    }

    public enum Rarity
    {
        Common,
        Rare,
        Epic,
        Legendary,
        Cursed
    }

    public enum CardType
    {
        Stat,
        AbilityModifier,
        HeroSpecialization,
        TeamSynergy,
        ElementReaction,
        Mutation,
        CursedPact
    }

    public enum RelicFamily
    {
        Combat,
        Element,
        Defense,
        Chaos
    }

    /// <summary>Reward screens offered after a wave. Order defines presentation order.</summary>
    public enum RewardKind
    {
        Draft,
        Recruit,
        Shop,
        Relic,
        Evolution,
        Event,
        Pact,
        CrystalEvolution
    }

    public static class ElementUtil
    {
        public const int Count = 13; // including None at index 0
        /// <summary>Size of per-pair arrays; <see cref="PairIndex"/> is always below this.</summary>
        public const int PairSlots = 256;

        /// <summary>The twelve primary elements in stable order (content stage gating lives in elements.json).</summary>
        public static readonly Element[] All =
        {
            Element.Fire, Element.Water, Element.Lightning, Element.Ice, Element.Wind, Element.Earth,
            Element.Light, Element.Shadow, Element.Nature, Element.Poison, Element.Arcane, Element.Void
        };

        private static readonly string[] Keys =
        {
            "none", "fire", "water", "lightning", "ice", "wind", "earth", "light", "shadow", "nature", "poison", "arcane", "void"
        };

        public static bool TryParse(string s, out Element e)
        {
            if (string.IsNullOrEmpty(s))
            {
                e = Element.None;
                return true;
            }
            for (int i = 0; i < Keys.Length; i++)
            {
                if (Keys[i] != s) continue;
                e = (Element)i;
                return true;
            }
            e = Element.None;
            return false;
        }

        public static string Key(Element e)
        {
            int i = (int)e;
            return i > 0 && i < Keys.Length ? Keys[i] : "none";
        }

        /// <summary>Order-independent slot for a reaction pair, e.g. (Water, Fire) == (Fire, Water).</summary>
        public static int PairIndex(Element a, Element b)
        {
            int x = (int)a, y = (int)b;
            if (x > y) { int t = x; x = y; y = t; }
            return x * 16 + y;
        }
    }

    public static class EnumParse
    {
        public static bool TryParse<T>(string s, out T value) where T : struct
        {
            value = default;
            if (string.IsNullOrEmpty(s)) return false;
            // Content uses snake_case / lowercase; enum names are PascalCase.
            string pascal = ToPascal(s);
            return System.Enum.TryParse(pascal, true, out value);
        }

        public static string ToPascal(string s)
        {
            var sb = new System.Text.StringBuilder(s.Length);
            bool upper = true;
            foreach (char c in s)
            {
                if (c == '_' || c == '-' || c == ' ') { upper = true; continue; }
                sb.Append(upper ? char.ToUpperInvariant(c) : c);
                upper = false;
            }
            return sb.ToString();
        }

        public static string ToSnake(string pascal)
        {
            var sb = new System.Text.StringBuilder(pascal.Length + 4);
            for (int i = 0; i < pascal.Length; i++)
            {
                char c = pascal[i];
                if (char.IsUpper(c) && i > 0) sb.Append('_');
                sb.Append(char.ToLowerInvariant(c));
            }
            return sb.ToString();
        }
    }
}
