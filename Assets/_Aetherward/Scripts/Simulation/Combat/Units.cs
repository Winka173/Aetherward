using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    public enum HeroState
    {
        Idle,
        Approach,
        Attack,
        Cast,
        Return,
        Stunned,
        Downed
    }

    /// <summary>Temporary stat buff with expiry, e.g. Gale Tactician haste or Terra's barrier armor.</summary>
    public struct TimedBuff
    {
        public StatId Stat;
        public float Percent;
        public float Remaining;
        public string Source;
    }

    public abstract class Combatant
    {
        public int Uid;
        public Vec2 Pos;
        public float Radius = 0.35f;
        public float Hp;
        public float MaxHp;
        public float Shield;
        public bool Alive = true;
        public float HitFlash;      // presentation hint, seconds remaining
        public Vec2 Facing = new Vec2(1f, 0f);

        public float HpFraction => MaxHp > 0f ? Hp / MaxHp : 0f;
    }

    public sealed class HeroUnit : Combatant
    {
        public HeroDef Def;
        public int RosterIndex;
        public int NodeIndex;
        public Vec2 Anchor;
        public int Level = 1;
        public string EvolutionId;
        public SkillDef Skill;
        public AttackDef Basic;
        public string PassiveKind;
        public ParamBag PassiveParams;
        public HeroRole Role;
        public TargetProfile Targeting;
        public bool Melee;
        public readonly float[] Stats = new float[(int)StatId.Count];
        public readonly List<TimedBuff> Buffs = new List<TimedBuff>(4);

        public HeroState State = HeroState.Idle;
        public EnemyUnit Target;
        public float AttackTimer;
        public float SkillTimer;
        public float RetargetTimer;
        public float StunTimer;
        public float CastLock;       // brief lock while casting (presentation sync)
        public int AttackCount;
        public int CastCount;
        public int PassiveStacks;
        public float PassiveTimer;
        public float RetaliateTimer;
        public bool ReviveUsedThisWave;
        public float BarrierTimer;   // Terra/Glacius defensive window
        public float ShieldRetaliate; // Glacius shield retaliation power while shield up

        // Expansion: debuffs from enemies, field effects, shield bursts, echo limits.
        public float SilenceTimer;    // Hex disruptor: skill cannot be cast
        public float LeechTimer;      // Mana Leech: skill cooldown recovers slower
        public float LeechAmount;
        public float FeverTimer;      // Plague Doctor tradeoff: takes more damage
        public float FeverAmount;
        public float ChillTimer;      // boss blizzard: attacks recover slower
        public float ChillAmount;
        public float FieldTimer;      // refreshed while standing in a supportive field
        public float FieldDamageReduction;
        public float FieldHaste;
        public int ShieldGiverUid;    // whose shield is up (Frost Paladin burst on break)
        public float ShieldBurst;     // burst power when that shield breaks
        public float EchoCooldown;    // spell echo internal cooldown
        public float Heat;            // Phoenix Knight resource
        public int RampStacks;        // Arcshot ramp on one target
        public int RampTargetUid;
        public int ComboCount;
        public float RedirectTimer;   // Gloom Sentinel guard internal cooldown
        public float ThornTimer;      // Thornguard: thorns reflect damage while > 0
        public float ThornMult;
        public float ThornRoot;
        public float ThornCooldown;
        public float EchoPrimed;      // Echo Savant: window in which the next ally skill is echoed
        public int EchoCharges;
        public float DoctorCooldown;  // Plague Doctor passive heal internal cooldown
        public string TraitId;
        public TraitDef Trait;
        public Element SecondaryElement; // Elemental Awakening (run-only)

        // Per-wave statistics; aggregated into run results.
        public float DamageDealt;
        public float HealingDone;
        public float DamageTaken;
        public int Kills;
        public int ReactionsTriggered;
        public int SkillCasts;

        public float Stat(StatId id)
        {
            float v = Stats[(int)id];
            for (int i = 0; i < Buffs.Count; i++)
            {
                if (Buffs[i].Stat != id) continue;
                if (id == StatId.AttackInterval || id == StatId.SkillCooldown) v /= 1f + Buffs[i].Percent;
                else v *= 1f + Buffs[i].Percent;
            }
            return v;
        }

        public bool Downed => !Alive;
        public bool Evolved => !string.IsNullOrEmpty(EvolutionId);
        public float SkillParam(string key, float fallback = 0f) => Skill.Params.Get(key, fallback);
        public bool SkillFlag(string key) => Skill.Params.Flag(key);
    }

    public sealed class EnemyUnit : Combatant
    {
        public EnemyDef Def;
        public int Lane;
        public int Waypoint;
        public bool Elite;
        public string Affix;
        public float Attack;
        public float Defense;
        public float Speed;
        public float CrystalDamage;
        public readonly float[] Resist = new float[ElementUtil.Count];
        public float Tenacity;
        public float AttackTimer;
        public HeroUnit Engaged;
        public HeroUnit Taunter;
        public float TauntTimer;

        // Element auras and statuses.
        public readonly float[] Aura = new float[ElementUtil.Count];
        public readonly float[] ReactionCooldown = new float[ElementUtil.PairSlots];
        public float ReactionWindowStart;
        public int ReactionsInWindow;
        public float BurnTimer;
        public float BurnDps;
        public float BurnTick;
        public HeroUnit BurnSource;
        public float SlowTimer;
        public float SlowAmount;
        public float StunTimer;      // freeze / stun
        public bool Frozen;
        public float FreezeResist;   // bosses accumulate freeze resistance
        public float FreezeResistTimer;
        public float ArmorCrackTimer;
        public int ArmorCrackStacks;
        public float ArmorCrackPerStack = 0.15f;
        public float SuperconductTimer;
        public float SandstormTimer;
        public float VulnerableTimer;
        public float VulnerableAmount;
        public Vec2 Knockback;       // velocity applied over a few ticks
        public float KnockbackTimer;
        public float PullTimer;
        public Vec2 PullTarget;
        public float PullStrength;
        public float ChillDamageReduction;

        // Behaviour state.
        public float SpecialTimer;
        public int Phase;
        public float PhaseTimer;
        public int Summoned;
        public float BuffAuraTimer;
        public float SpeedBuff;      // from Banner bearers
        public float ArmorBuff;
        public Vec2 LastProgressPos;
        public float StuckTimer;
        public bool Leaked;          // reached crystal at least once
        public bool ShieldFront;     // shieldbearer: frontal block
        public float TelegraphTimer;
        public Vec2 TelegraphPos;
        public float TelegraphRadius;
        public int TelegraphKind;
        public float Invulnerable;   // brief phase transition window
        public readonly float[] AdaptDamage = new float[ElementUtil.Count];
        public int AdaptedElement;
        public float AdaptTimer;

        // Expansion statuses (see Battle.Statuses.cs; all bounded by caps).
        public float IlluminatedTimer;
        public float IlluminatedWeaken;
        public int DoomStacks;
        public float DoomTimer;
        public HeroUnit DoomSource;
        public float RootTimer;
        public float RootImmune;
        public int PoisonStacks;
        public float PoisonTimer;
        public float PoisonTick;
        public float PoisonDpsPerStack;
        public HeroUnit PoisonSource;
        public int ContagionDepth;
        public float ResonantTimer;
        public int UnstableStacks;
        public float UnstableCooldown;
        public HeroUnit UnstableSource;
        public float BrittleTimer;
        public float BrittleAmount;
        public float ReactionVulnTimer;
        public float ReactionVulnAmount;
        public int MarkStacks;        // Ember Scribe burn marks
        public float MarkTimer;
        public HeroUnit MarkOwner;
        public float FieldTimer;      // refreshed while inside fields
        public float FieldVuln;
        public float FieldWeaken;
        public float FieldReactionAmp;
        public float SealTimer;       // abilities suppressed (Astral Seal / Portal Seal)
        public bool Latched;          // Crystal Parasite attached to the crystal
        public bool Enraged;          // Ascension boss enrage triggered
        public bool Burrowed;         // underground: untouchable until it surfaces
        public float SurfaceTimer;
        public float SprintTimer;
        public float ChannelTimer;
        public float Stoke;           // speed gained from absorbed element hits
        public EnemyUnit LinkedTo;    // Soul Binder link
        public float Timer2;          // secondary behaviour timer (auras, boss summons)
        public float SpecialCooldownMult = 1f;

        public bool IsBoss => Def.Boss;
        public bool HasAura(Element e) => Aura[(int)e] > 0.05f;
        public bool Chilled => Aura[(int)Element.Ice] > 0.05f || Frozen;
        public bool Wet => Aura[(int)Element.Water] > 0.05f;
        public bool Burning => BurnTimer > 0f;
        public bool Stunned => StunTimer > 0f;
        public bool Rooted => RootTimer > 0f;
        public bool Illuminated => IlluminatedTimer > 0f;
        public bool Corroded => PoisonStacks >= 5;
        /// <summary>Multiplier on damage this enemy deals (Illuminated, weakening fields).</summary>
        public float OutgoingDamageMult => (1f - (IlluminatedTimer > 0f ? IlluminatedWeaken : 0f)) * (1f - (FieldTimer > 0f ? FieldWeaken : 0f));

        /// <summary>Two dominant visible statuses for the HUD (spec: show up to two icons).</summary>
        public void DominantStatuses(out Element first, out Element second)
        {
            first = Element.None;
            second = Element.None;
            float a = 0.05f, b = 0.05f;
            for (int i = 1; i < ElementUtil.Count; i++)
            {
                float v = Aura[i];
                if (v > a) { second = first; b = a; first = (Element)i; a = v; }
                else if (v > b) { second = (Element)i; b = v; }
            }
        }
    }

    public sealed class Crystal
    {
        public Vec2 Pos = Vec2.Zero;
        public float Radius = 0.85f;
        public float Hp;
        public float MaxHp;
        public float Shield;
        public float DamageReduction;     // from relics (0..0.8)
        public float TempReductionTimer;  // Bedrock Warden barrier window
        public float TempReduction;
        public float Regen;               // hp per second
        public float Thorns;              // damage returned to attackers
        public float HitFlash;
        public float DamageTakenThisWave;
        public bool Alive => Hp > 0f;
        public float HpFraction => MaxHp > 0 ? Hp / MaxHp : 0f;
    }
}
