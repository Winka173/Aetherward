using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    /// <summary>Expansion hero state: debuff timers from enemies and defensive auras from other heroes.</summary>
    public sealed partial class Battle
    {
        private void TickHeroDebuffs(HeroUnit h, float dt)
        {
            if (h.SilenceTimer > 0f) h.SilenceTimer -= dt;
            if (h.LeechTimer > 0f)
            {
                h.LeechTimer -= dt;
                if (h.LeechTimer <= 0f) h.LeechAmount = 0f;
            }
            if (h.FeverTimer > 0f)
            {
                h.FeverTimer -= dt;
                if (h.FeverTimer <= 0f) h.FeverAmount = 0f;
            }
            if (h.FieldTimer > 0f)
            {
                h.FieldTimer -= dt;
                if (h.FieldTimer <= 0f) h.FieldDamageReduction = h.FieldHaste = 0f;
            }
            if (h.EchoCooldown > 0f) h.EchoCooldown -= dt;
            if (h.RedirectTimer > 0f) h.RedirectTimer -= dt;
        }

        /// <summary>
        /// Damage reduction a hero receives from allies' passive auras (e.g. shielded allies near a
        /// Dawn Warden, ranged allies near a Void Sentinel). Capped together with other reductions.
        /// </summary>
        private float HeroGuardReduction(HeroUnit h)
        {
            float best = 0f;
            for (int i = 0; i < Heroes.Count; i++)
            {
                HeroUnit g = Heroes[i];
                if (!g.Alive || g == h) continue;
                float r;
                switch (g.PassiveKind)
                {
                    case "radiant_guard":
                        if (h.Shield <= 0f) continue;
                        r = g.PassiveParams.Get("reduction", 0.1f);
                        break;
                    case "backline_ward":
                        if (h.Melee) continue;
                        r = g.PassiveParams.Get("reduction", 0.12f);
                        break;
                    default:
                        continue;
                }
                if (Vec2.Distance(g.Pos, h.Pos) > g.PassiveParams.Get("radius", 3.5f)) continue;
                if (r > best) best = r;
            }
            return best;
        }
    }
}
