using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    /// <summary>
    /// Hero ultimates (dynamic party): a charge that fills while the hero is fighting (and faster from kills), then a
    /// huge element-signature spell on the densest enemy cluster in reach. Defined per element so every hero has one:
    /// Fire meteor rain, Ice frost nova, Lightning thunder dome + chain, Water tidal sanctuary (party heal + shield),
    /// Wind cyclone pull, Earth quake, Light radiant dome (party + Crystal shield), the rest a void eruption.
    /// Presentation reads the Strike events "ult_cast" and "ult_&lt;element&gt;".
    /// </summary>
    public sealed partial class Battle
    {
        public const float UltSeconds = 32f;           // seconds of fighting to fill the charge
        public const float UltKillCharge = 0.04f;      // extra charge per kill credited to the hero
        private const float UltMinCluster = 3f;
        /// <summary>Balance knob: ultimates are a spectacle first; their damage is scaled so run win rates stay on target.</summary>
        public const float UltPower = 0.4f;        // enemy "weight" needed to spend it (elites 3, bosses 6)

        private void TickUltimate(HeroUnit h, float dt)
        {
            if (h.Target != null && h.Ult < 1f) h.Ult = SimMath.Min(1f, h.Ult + dt / UltSeconds);
            if (h.Ult < 1f || h.CastLock > 0f || h.SilenceTimer > 0f) return;
            if (!BestCluster(h, out Vec2 at)) return;
            CastUltimate(h, at);
            h.Ult = 0f;
            h.CastLock = 0.6f;
            h.State = HeroState.Cast;
        }

        /// <summary>A kill credited to a hero tops up their ultimate.</summary>
        public void ChargeUltimateOnKill(HeroUnit h)
        {
            if (h != null && h.Alive) h.Ult = SimMath.Min(1f, h.Ult + UltKillCharge);
        }

        private bool BestCluster(HeroUnit h, out Vec2 at)
        {
            at = h.Pos;
            float reach = h.Stat(StatId.Range) + 4f;
            List<EnemyUnit> near = RentList(), around = RentList();
            QueryEnemies(h.Pos, reach, near);
            near.Sort((a, b) => a.Uid.CompareTo(b.Uid));
            float best = 0f;
            for (int i = 0; i < near.Count; i++)
            {
                EnemyUnit e = near[i];
                if (!e.Alive || e.Burrowed) continue;
                around.Clear();
                QueryEnemies(e.Pos, 3f, around);
                float w = 0f;
                for (int k = 0; k < around.Count; k++)
                    if (around[k].Alive) w += around[k].IsBoss ? 6f : around[k].Elite ? 3f : 1f;
                if (w > best)
                {
                    best = w;
                    at = e.Pos;
                }
            }
            ReturnList(near);
            ReturnList(around);
            return best >= UltMinCluster;
        }

        private void UltStrike(HeroUnit h, Vec2 pos, float delay, float radius, float mult, float stun, Element el)
        {
            AddStrike(new DelayedStrike
            {
                Kind = StrikeKind.Ultimate, Pos = pos, Delay = delay, Total = delay, Radius = radius, Source = h, Element = el,
                Power = h.Stat(StatId.Attack), Multiplier = mult * UltPower, Gauge = 1f, Stun = stun * 0.6f
            });
        }

        private void CastUltimate(HeroUnit h, Vec2 at)
        {
            Element el = h.Def.Element;
            Emit(SimEventType.Strike, at, el, 0f, h.Uid, 0, "ult_cast", false, 0f);
            Stats.Ultimates++;
            switch (el)
            {
                case Element.Fire:
                    // meteor rain: five impacts walking across the cluster
                    for (int i = 0; i < 5; i++)
                    {
                        float a = i * 2.39996f;     // golden-angle spread, deterministic
                        Vec2 off = new Vec2(System.MathF.Cos(a), System.MathF.Sin(a)) * (i == 0 ? 0f : 1.1f + 0.35f * i);
                        UltStrike(h, at + off, 0.35f + 0.22f * i, 1.9f, 2.4f, 0f, Element.Fire);
                    }
                    break;
                case Element.Ice:
                    UltStrike(h, at, 0.35f, 3.6f, 2.2f, 1.6f, Element.Ice);
                    break;
                case Element.Lightning:
                    UltStrike(h, at, 0.3f, 4.2f, 2.6f, 0.6f, Element.Lightning);
                    ChainUltimate(h, at, 4);
                    break;
                case Element.Water:
                    for (int i = 0; i < Heroes.Count; i++)
                    {
                        HeroUnit a = Heroes[i];
                        if (!a.Alive || Vec2.Distance(a.Pos, h.Pos) > 6f) continue;
                        HealHero(a, a.MaxHp * 0.3f * UltPower, h);
                        AddHeroShield(a, a.MaxHp * 0.15f * UltPower, h);
                    }
                    UltStrike(h, at, 0.3f, 3.4f, 1.3f, 0f, Element.Water);
                    KnockAround(at, 3.4f, 1.6f);
                    break;
                case Element.Wind:
                    UltStrike(h, at, 0.45f, 3.6f, 1.9f, 0f, Element.Wind);
                    PullAround(at, 4.2f);
                    break;
                case Element.Earth:
                    UltStrike(h, at, 0.4f, 4f, 2.4f, 0.8f, Element.Earth);
                    break;
                case Element.Light:
                    for (int i = 0; i < Heroes.Count; i++)
                        if (Heroes[i].Alive) AddHeroShield(Heroes[i], Heroes[i].MaxHp * 0.25f * UltPower, h);
                    ShieldCrystal(Crystal.MaxHp * 0.08f * UltPower);
                    UltStrike(h, at, 0.3f, 3f, 1.6f, 0f, Element.Light);
                    break;
                default:
                    UltStrike(h, at, 0.4f, 3.4f, 2.8f, 0f, el);
                    break;
            }
        }

        private void ChainUltimate(HeroUnit h, Vec2 at, int count)
        {
            List<EnemyUnit> near = RentList();
            QueryEnemies(at, 6f, near);
            near.Sort((a, b) =>
            {
                int c = b.Hp.CompareTo(a.Hp);
                return c != 0 ? c : a.Uid.CompareTo(b.Uid);
            });
            for (int i = 0, n = 0; i < near.Count && n < count; i++)
            {
                if (!near[i].Alive) continue;
                Emit(SimEventType.Strike, near[i].Pos, Element.Lightning, 0f, h.Uid, near[i].Uid, "chain", false, 0.3f);
                UltStrike(h, near[i].Pos, 0.45f + 0.08f * n, 1.2f, 1.6f, 0.4f, Element.Lightning);
                n++;
            }
            ReturnList(near);
        }

        private void KnockAround(Vec2 at, float radius, float distance)
        {
            List<EnemyUnit> near = RentList();
            QueryEnemies(at, radius, near);
            for (int i = 0; i < near.Count; i++)
                if (near[i].Alive && !near[i].IsBoss) Knock(near[i], (near[i].Pos - at).Normalized, distance);
            ReturnList(near);
        }

        private void PullAround(Vec2 at, float radius)
        {
            List<EnemyUnit> near = RentList();
            QueryEnemies(at, radius, near);
            for (int i = 0; i < near.Count; i++)
                if (near[i].Alive && !near[i].IsBoss) Pull(near[i], at, 3.5f, 1.2f);
            ReturnList(near);
        }
    }
}
