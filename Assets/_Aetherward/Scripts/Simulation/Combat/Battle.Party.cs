using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    /// <summary>
    /// Party stance chosen before a wave: how far from the Crystal the party fights.
    /// Defensive holds the inner ring, Balanced the intercept ring, Aggressive pushes out onto the approach lanes.
    /// </summary>
    public enum PartyStance
    {
        Defensive,
        Balanced,
        Aggressive
    }

    /// <summary>
    /// Dynamic party: every hero's <see cref="HeroUnit.Anchor"/> is a moving post instead of a fixed node.
    /// Posts are re-planned twice a second from lane threat (enemies on the field, or the lanes still to spawn),
    /// the hero's role and the party stance. Frontliners stand on the most threatened lanes, casters and rangers
    /// spread behind them, supports stay with the most hurt ally, assassins hunt casters and elites, and anyone
    /// close enough drops everything when an enemy reaches the Crystal. The existing leash/approach logic then
    /// fights around the post, so targeting, skills and enemy engagement keep working unchanged.
    /// </summary>
    public sealed partial class Battle
    {
        private const float PostReplanInterval = 0.5f;
        private const float PostEaseSpeed = 4.5f;          // units/s an anchor slides toward its new post
        private const float LaneSwitchMargin = 1.3f;       // hysteresis: a new lane must be this much hotter
        private const float EmergencyRadius = 1.9f;        // enemy this close to the Crystal edge triggers the override

        private float _postTimer;
        private float[] _laneThreat;
        private readonly List<int> _hotLanes = new List<int>(8);

        public static float StanceRadius(PartyStance s) => s == PartyStance.Defensive ? 2.5f : s == PartyStance.Aggressive ? 5.4f : 3.8f;
        public static float StanceLeash(PartyStance s) => s == PartyStance.Defensive ? 2.0f : s == PartyStance.Aggressive ? 3.6f : 2.8f;

        /// <summary>Leash a hero fights within around its post: the stance leash, or more if a stat (relic, trait) grants it.</summary>
        private float EffectiveLeash(HeroUnit h)
        {
            float stat = h.Stat(StatId.LeashRadius);
            return Setup.DynamicParty ? System.Math.Max(stat, StanceLeash(Setup.Stance)) : stat;
        }

        /// <summary>
        /// Start-of-battle aura reach between two heroes' formation spots, in the original sanctum's units: the
        /// battlefield was widened by <see cref="ContentDatabase.WorldScale"/>, the formation rings with it, and the
        /// aura radii in content were tuned for the old spacing.
        /// </summary>
        public static float FormationDistance(HeroUnit a, HeroUnit b) => Vec2.Distance(a.Anchor, b.Anchor) / ContentDatabase.WorldScale;

        /// <summary>Aggressive "Momentum": fighting out on the lanes is riskier, so it hits harder (+12% attack).</summary>
        public const float AggressiveMomentum = 0.12f;

        private void ApplyStanceBonus()
        {
            if (!Setup.DynamicParty || Setup.Stance != PartyStance.Aggressive) return;
            for (int i = 0; i < Heroes.Count; i++)
                if (Heroes[i].Alive) AddBuff(Heroes[i], StatId.Attack, AggressiveMomentum, 99999f, "stance_momentum");
        }

        private static bool IsFrontline(HeroRole r) => r == HeroRole.Guardian || r == HeroRole.Bruiser;

        private void UpdatePartyPosts(float dt)
        {
            if (!Setup.DynamicParty) return;
            _postTimer -= dt;
            if (_postTimer <= 0f)
            {
                _postTimer = PostReplanInterval;
                PlanPosts();
            }
            for (int i = 0; i < Heroes.Count; i++)
            {
                HeroUnit h = Heroes[i];
                if (h.Alive) h.Anchor = Vec2.MoveTowards(h.Anchor, h.Post, PostEaseSpeed * dt);
            }
        }

        private void MeasureLaneThreat()
        {
            int n = Arena.Lanes.Count;
            if (_laneThreat == null || _laneThreat.Length != n) _laneThreat = new float[n];
            for (int i = 0; i < n; i++) _laneThreat[i] = 0f;
            for (int i = 0; i < Enemies.Count; i++)
            {
                EnemyUnit e = Enemies[i];
                if (!e.Alive || e.Lane < 0 || e.Lane >= n) continue;
                float d = Vec2.Distance(e.Pos, Crystal.Pos);
                float weight = (e.Def.Threat + (e.Elite ? 3f : 0f) + (e.IsBoss ? 8f : 0f)) * (1f + 8f / (1f + d));
                _laneThreat[e.Lane] += weight;
            }
            // nothing on the field yet: read the lanes still to spawn in the next few seconds
            bool any = false;
            for (int i = 0; i < n; i++) any |= _laneThreat[i] > 0f;
            if (!any)
            {
                for (int k = _spawnCursor; k < _schedule.Count && _schedule[k].Time <= Time + 6f; k++)
                {
                    ScheduledSpawn s = _schedule[k];
                    if (s.Lane >= 0 && s.Lane < n) _laneThreat[s.Lane] += s.Def.Threat + (s.Elite ? 3f : 0f);
                }
            }
            _hotLanes.Clear();
            for (int i = 0; i < n; i++)
                if (_laneThreat[i] > 0f) _hotLanes.Add(i);
            _hotLanes.Sort((a, b) =>
            {
                int c = _laneThreat[b].CompareTo(_laneThreat[a]);
                return c != 0 ? c : a.CompareTo(b);
            });
        }

        /// <summary>The point on a lane (walked from the Crystal end outward) at the given distance from the Crystal.</summary>
        private Vec2 LanePointAt(int lane, float radius)
        {
            List<Vec2> pts = Arena.Lanes[lane].Points;
            Vec2 c = Crystal.Pos;
            for (int i = pts.Count - 1; i > 0; i--)
            {
                Vec2 a = pts[i], b = pts[i - 1];             // a is nearer the Crystal
                float da = Vec2.Distance(a, c), db = Vec2.Distance(b, c);
                if (db >= radius && da <= radius)
                {
                    float t = db - da > 1e-4f ? (radius - da) / (db - da) : 0f;
                    return a + (b - a) * t;
                }
            }
            Vec2 dir = (pts[0] - c).Normalized;
            return c + dir * radius;
        }

        private void PlanPosts()
        {
            MeasureLaneThreat();
            PartyStance stance = Setup.Stance;
            float R = StanceRadius(stance);
            Vec2 c = Crystal.Pos;

            // emergency: enemies at the Crystal pull the nearest fighters back regardless of role
            EnemyUnit breacher = null;
            float best = float.MaxValue;
            for (int i = 0; i < Enemies.Count; i++)
            {
                EnemyUnit e = Enemies[i];
                if (!e.Alive) continue;
                float d = Vec2.Distance(e.Pos, c) - Crystal.Radius - e.Radius;
                if (d < EmergencyRadius && d < best)
                {
                    best = d;
                    breacher = e;
                }
            }

            int front = 0, back = 0;
            HeroUnit hurt = null;
            float hurtFrac = 0.999f;
            for (int i = 0; i < Heroes.Count; i++)
            {
                HeroUnit h = Heroes[i];
                if (!h.Alive) continue;
                float f = h.Hp / System.Math.Max(1f, h.MaxHp);
                if (f < hurtFrac)
                {
                    hurtFrac = f;
                    hurt = h;
                }
            }

            PickRescuers(breacher, stance == PartyStance.Defensive ? 3 : 2);
            for (int i = 0; i < Heroes.Count; i++)
            {
                HeroUnit h = Heroes[i];
                if (!h.Alive) continue;
                if (_rescuers.Contains(h))
                {
                    h.Post = c + (breacher.Pos - c).Normalized * (Crystal.Radius + 0.9f);
                    continue;
                }
                int lane = PickLane(h, IsFrontline(h.Role) ? front : back);
                Vec2 dir = lane >= 0 ? (LanePointAt(lane, R) - c).Normalized : (h.Post - c).Normalized;
                if (dir.SqrLength < 1e-4f) dir = h.Facing.SqrLength > 1e-4f ? h.Facing : new Vec2(1f, 0f);
                Vec2 side = new Vec2(-dir.Y, dir.X);
                switch (h.Role)
                {
                    case HeroRole.Guardian:
                    case HeroRole.Bruiser:
                    {
                        Vec2 p = lane >= 0 ? LanePointAt(lane, R * (h.Role == HeroRole.Bruiser ? 1.12f : 1f)) : c + dir * R;
                        // a second frontliner on the same lane stands beside the first
                        h.Post = p + side * (front >= _hotLanes.Count && _hotLanes.Count > 0 ? ((front & 1) == 0 ? 0.8f : -0.8f) : 0f);
                        front++;
                        break;
                    }
                    case HeroRole.Assassin:
                    {
                        EnemyUnit prey = BestPrey(R + 2.5f);
                        h.Post = prey != null ? prey.Pos : c + dir * (R * 1.15f);
                        break;
                    }
                    case HeroRole.Support:
                    case HeroRole.Healer:
                    {
                        Vec2 toward = hurt != null && hurt != h ? hurt.Pos : c + dir * R;
                        Vec2 d = toward - c;
                        float r = System.Math.Min(d.Length, R * 0.55f);
                        h.Post = c + (d.SqrLength > 1e-4f ? d.Normalized : dir) * System.Math.Max(r, Crystal.Radius + 0.8f);
                        break;
                    }
                    default: // mage, controller, ranger: behind the frontline, spread sideways
                    {
                        float depth = h.Role == HeroRole.Ranger ? 0.7f : 0.62f;
                        float spread = ((back & 1) == 0 ? 1f : -1f) * (0.9f + 0.5f * (back / 2));
                        h.Post = c + dir * (R * depth) + side * spread;
                        back++;
                        break;
                    }
                }
                h.Post = ClampToArena(h.Post, h.Radius);
            }
        }

        private readonly List<HeroUnit> _rescuers = new List<HeroUnit>(2);

        /// <summary>
        /// Who drops their post for an enemy at the Crystal: the nearest fighters, mobile roles first (assassin,
        /// bruiser, ranger before a tank, so the lane holder keeps its lane), never a support.
        /// </summary>
        private void PickRescuers(EnemyUnit breacher, int count)
        {
            _rescuers.Clear();
            if (breacher == null) return;
            for (int k = 0; k < count; k++)
            {
                HeroUnit best = null;
                float bestCost = float.MaxValue;
                for (int i = 0; i < Heroes.Count; i++)
                {
                    HeroUnit h = Heroes[i];
                    if (!h.Alive || h.Role == HeroRole.Support || h.Role == HeroRole.Healer || _rescuers.Contains(h)) continue;
                    float cost = Vec2.Distance(h.Pos, breacher.Pos) + (h.Role == HeroRole.Guardian ? 3f : 0f);
                    if (cost < bestCost)
                    {
                        bestCost = cost;
                        best = h;
                    }
                }
                if (best == null) break;
                _rescuers.Add(best);
            }
        }

        /// <summary>Lane for the k-th hero of a group, with hysteresis so posts do not flicker between lanes.</summary>
        private int PickLane(HeroUnit h, int k)
        {
            if (_hotLanes.Count == 0) return h.PostLane;
            int want = _hotLanes[k % _hotLanes.Count];
            int cur = h.PostLane;
            if (cur >= 0 && cur < _laneThreat.Length && cur != want && _laneThreat[cur] > 0f
                && _laneThreat[want] < _laneThreat[cur] * LaneSwitchMargin)
                want = cur;
            h.PostLane = want;
            return want;
        }

        /// <summary>Casters, summoners, elites and bosses inside the hunt radius, nearest to the Crystal first.</summary>
        private EnemyUnit BestPrey(float huntRadius)
        {
            EnemyUnit best = null;
            float bestScore = float.MinValue;
            for (int i = 0; i < Enemies.Count; i++)
            {
                EnemyUnit e = Enemies[i];
                if (!e.Alive) continue;
                float d = Vec2.Distance(e.Pos, Crystal.Pos);
                if (d > huntRadius) continue;
                float score = (e.Def.Behavior == EnemyBehavior.Ranged || e.Def.Behavior == EnemyBehavior.Summoner ? 4f : 0f)
                              + (e.Elite ? 3f : 0f) + (e.IsBoss ? 2f : 0f) + e.Def.Threat - d * 0.3f;
                if (score > bestScore)
                {
                    bestScore = score;
                    best = e;
                }
            }
            return best;
        }

        private Vec2 ClampToArena(Vec2 p, float r)
        {
            float hw = Arena.HalfWidth - r - 0.4f, hh = Arena.HalfHeight - r - 0.4f;
            p = new Vec2(System.Math.Max(-hw, System.Math.Min(hw, p.X)), System.Math.Max(-hh, System.Math.Min(hh, p.Y)));
            float minC = Crystal.Radius + r + 0.2f;
            Vec2 d = p - Crystal.Pos;
            if (d.Length < minC) p = Crystal.Pos + (d.SqrLength > 1e-6f ? d.Normalized : new Vec2(1f, 0f)) * minC;
            return p;
        }

        /// <summary>Ranged heroes step back when a melee enemy is on top of them (kiting), staying inside their leash.</summary>
        private bool Kite(HeroUnit h, float leash, float dt)
        {
            if (h.Melee || !Setup.DynamicParty) return false;
            EnemyUnit threat = null;
            float best = float.MaxValue;
            for (int i = 0; i < Enemies.Count; i++)
            {
                EnemyUnit e = Enemies[i];
                if (!e.Alive || e.Def.Behavior == EnemyBehavior.Ranged) continue;
                float d = Vec2.Distance(e.Pos, h.Pos) - e.Radius - h.Radius;
                if (d < 0.6f && d < best)
                {
                    best = d;
                    threat = e;
                }
            }
            if (threat == null) return false;
            Vec2 away = (h.Pos - threat.Pos).Normalized;
            Vec2 toCrystal = (Crystal.Pos - h.Pos).Normalized;
            Vec2 step = (away * 0.75f + toCrystal * 0.25f).Normalized;
            MoveHeroWithinLeash(h, h.Pos + step * 1.2f, leash, dt);
            h.State = HeroState.Approach;
            return true;
        }
    }
}
