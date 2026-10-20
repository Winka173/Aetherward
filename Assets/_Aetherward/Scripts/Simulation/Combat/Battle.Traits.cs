using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    /// <summary>Run-only hero traits: behaviour keys from traits.json read at a few combat hooks.</summary>
    public sealed partial class Battle
    {
        private static float TraitValue(HeroUnit h, string key) => h != null && h.Trait != null ? h.Trait.Behaviour.Get(key) : 0f;

        public static bool ImmuneToDebuffs(HeroUnit h) => h != null && h.Trait != null && h.Trait.Behaviour.Flag("debuffImmune");

        private void ApplyBattleStartTrait(HeroUnit h)
        {
            if (h.Trait == null || !h.Alive) return;
            ParamBag b = h.Trait.Behaviour;
            if (b.Flag("instantFirstCast")) h.SkillTimer = SimMath.Min(h.SkillTimer, 0.3f);
            float haste = b.Get("allyHaste");
            if (haste > 0f)
                for (int i = 0; i < Heroes.Count; i++)
                {
                    HeroUnit a = Heroes[i];
                    if (a.Alive && FormationDistance(a, h) <= b.Get("allyRadius", 3f))
                        AddBuff(a, StatId.AttackInterval, haste, 99999f, "trait_tactician");
                }
        }

        /// <summary>Conditional direct-hit bonuses from the attacker's trait.</summary>
        private float TraitDamageBonus(HeroUnit src, EnemyUnit e)
        {
            if (src == null || src.Trait == null) return 0f;
            ParamBag b = src.Trait.Behaviour;
            float bonus = 0f;
            if (b.Has("burningBonus") && e.Burning) bonus += b.Get("burningBonus");
            if (b.Has("executeBonus") && e.HpFraction <= b.Get("executeBelow", 0.25f)) bonus += b.Get("executeBonus");
            if (b.Has("lowHpBonus") && src.HpFraction <= b.Get("lowHpThreshold", 0.35f)) bonus += b.Get("lowHpBonus");
            return bonus;
        }

        /// <summary>Twin Caster: a chance to echo the skill at reduced power (internal cooldown; echoes never echo).</summary>
        private void TryTraitEcho(HeroUnit h)
        {
            float chance = TraitValue(h, "echoChance");
            if (chance <= 0f || h.EchoCooldown > 0f || !Rng.Chance(chance)) return;
            h.EchoCooldown = h.Trait.Behaviour.Get("echoCooldown", 6f);
            CastSkill(h, h.Trait.Behaviour.Get("echoPower", 0.5f), true);
        }
    }
}
