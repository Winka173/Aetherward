using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    /// <summary>Builds a battle-ready hero from its definition, run level, evolution and active modifiers.</summary>
    public static class HeroFactory
    {
        /// <summary>Stats where modifiers add directly instead of scaling (chances, bonuses, reductions).</summary>
        public static bool IsAdditive(StatId s)
        {
            switch (s)
            {
                case StatId.CritChance:
                case StatId.CritMultiplier:
                case StatId.DamageBonus:
                case StatId.ReactionBonus:
                case StatId.DamageReduction:
                case StatId.StatusPower:
                    return true;
                default:
                    return false;
            }
        }

        public static HeroUnit Create(Battle battle, HeroLoadout l)
        {
            ContentDatabase content = battle.Content;
            HeroDef def = l.Def;
            var h = new HeroUnit
            {
                Def = def,
                RosterIndex = l.RosterIndex,
                NodeIndex = l.NodeIndex,
                Level = l.Level,
                EvolutionId = l.EvolutionId,
                Skill = def.Skill,
                Basic = def.Basic,
                PassiveKind = def.PassiveKind,
                PassiveParams = def.PassiveParams,
                Role = def.Role,
                Targeting = def.Targeting,
                Melee = def.Melee
            };

            float[] flat = new float[(int)StatId.Count];
            float[] pct = new float[(int)StatId.Count];

            EvolutionDef evo = null;
            if (!string.IsNullOrEmpty(l.EvolutionId) && content.Evolutions.TryGetValue(l.EvolutionId, out evo))
            {
                h.Skill = def.Skill.With(evo.Skill);
                if (!string.IsNullOrEmpty(evo.PassiveKind))
                {
                    h.PassiveKind = evo.PassiveKind;
                    h.PassiveParams = evo.PassiveParams ?? new ParamBag();
                }
                if (evo.RoleOverride.HasValue) h.Role = evo.RoleOverride.Value;
                if (evo.TargetingOverride.HasValue) h.Targeting = evo.TargetingOverride.Value;
                if (evo.MeleeOverride.HasValue) h.Melee = evo.MeleeOverride.Value;
                foreach (EffectOp op in evo.Effects)
                    if (op.Op == "stat") Accumulate(op, 1, flat, pct);
            }

            foreach (SourcedOp s in battle.Mods.StatOps)
                if (s.Op.MatchesHero(def, h.Melee)) Accumulate(s.Op, s.Stacks, flat, pct);

            float levelMult = 1f;
            for (int i = 1; i < l.Level; i++) levelMult *= 1f + def.GrowthPerLevel;

            for (int i = 0; i < (int)StatId.Count; i++)
            {
                var id = (StatId)i;
                float b = def.BaseStats[i];
                if (id == StatId.MaxHp || id == StatId.Attack) b *= levelMult;
                if (id == StatId.Defense) b += 2f * (l.Level - 1);
                if (id == StatId.ElementalMastery) b += 8f * (l.Level - 1);
                float v;
                if (IsAdditive(id)) v = b + flat[i] + pct[i];
                else if (id == StatId.AttackInterval || id == StatId.SkillCooldown) v = (b + flat[i]) / (1f + SimMath.Max(-0.5f, pct[i]));
                else v = (b + flat[i]) * (1f + pct[i]);
                h.Stats[i] = v;
            }
            h.Stats[(int)StatId.AttackInterval] = SimMath.Max(0.18f, h.Stats[(int)StatId.AttackInterval]);
            h.Stats[(int)StatId.SkillCooldown] = SimMath.Max(0.35f, h.Stats[(int)StatId.SkillCooldown]);
            h.Stats[(int)StatId.CritChance] = SimMath.Clamp(h.Stats[(int)StatId.CritChance], 0f, 0.75f);
            h.Stats[(int)StatId.DamageReduction] = SimMath.Clamp(h.Stats[(int)StatId.DamageReduction], 0f, 0.6f);

            h.MaxHp = h.Stats[(int)StatId.MaxHp];
            h.Hp = h.MaxHp * SimMath.Clamp01(l.HpFraction);
            h.Radius = h.Melee ? 0.4f : 0.36f;
            h.Anchor = l.NodeIndex >= 0 && l.NodeIndex < content.Arena.Nodes.Count ? content.Arena.Nodes[l.NodeIndex] : Vec2.Zero;
            h.Pos = h.Anchor;
            h.Facing = (Vec2.Zero - h.Anchor).SqrLength > 0.01f ? (h.Anchor - Vec2.Zero).Normalized : new Vec2(1f, 0f);
            h.AttackTimer = 0.2f + 0.1f * l.RosterIndex;
            h.SkillTimer = h.Skill.Cooldown * 0.5f * h.Stats[(int)StatId.SkillCooldown];
            h.RetargetTimer = 0.03f * l.RosterIndex; // stagger expensive searches across ticks
            if (l.Downed || h.Hp <= 0f)
            {
                h.Alive = false;
                h.Hp = 0f;
                h.State = HeroState.Downed;
            }
            return h;
        }

        private static void Accumulate(EffectOp op, int stacks, float[] flat, float[] pct)
        {
            int i = (int)op.Stat;
            if (op.Percent) pct[i] += op.Value * stacks;
            else flat[i] += op.Value * stacks;
        }
    }
}
