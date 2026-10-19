using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Run
{
    /// <summary>
    /// Smart draft: weighted eligibility with soft constraints. Guarantees at least one actionable
    /// card for the current roster when one exists, never offers duplicates, maxed or ineligible
    /// cards, and keeps randomness meaningful rather than always suggesting the optimal pick.
    /// </summary>
    public static class DraftGenerator
    {
        public static float RarityWeight(Rarity r, int wave)
        {
            switch (r)
            {
                case Rarity.Common: return 1f;
                case Rarity.Rare: return 0.65f;
                case Rarity.Epic: return wave >= 4 ? 0.35f : 0.12f;
                case Rarity.Legendary: return wave >= 7 ? 0.16f : 0f;
                case Rarity.Cursed: return 0.25f;
                default: return 0.5f;
            }
        }

        public static bool IsEligible(RunController rc, CardDef c, bool pact)
        {
            RunState s = rc.State;
            if ((c.Type == CardType.CursedPact) != pact) return false;
            if (s.CardStacks(c.Id) >= c.MaxStacks) return false;
            CardRequirement r = c.Requires;
            if (r.Element != Element.None && !RosterHasElement(rc, r.Element)) return false;
            if (r.Role.HasValue && !RosterHasRole(rc, r.Role.Value)) return false;
            if (!string.IsNullOrEmpty(r.Hero))
            {
                HeroRunState h = null;
                foreach (HeroRunState x in s.Heroes) if (x.DefId == r.Hero) h = x;
                if (h == null || h.Level < r.MinLevel) return false;
                if (r.Evolved && string.IsNullOrEmpty(h.EvolutionId)) return false;
            }
            if (!string.IsNullOrEmpty(r.Relic) && !s.Relics.Contains(r.Relic)) return false;
            return true;
        }

        /// <summary>Synergy: the card has a requirement that the roster satisfies (it is "for" this build).</summary>
        public static bool IsSynergy(CardDef c)
        {
            CardRequirement r = c.Requires;
            return r.Element != Element.None || r.Role.HasValue || !string.IsNullOrEmpty(r.Hero) || !string.IsNullOrEmpty(r.Relic);
        }

        public static string TagFor(RunController rc, CardDef c)
        {
            if (!string.IsNullOrEmpty(c.Requires.Hero)) return "specialization";
            if (IsSynergy(c)) return "synergy";
            if (c.Type == CardType.Mutation) return "pivot";
            return null;
        }

        public static List<CardDef> Generate(RunController rc, Pcg32 rng, int count, bool pact)
        {
            var pool = new List<CardDef>();
            var weights = new List<float>();
            foreach (CardDef c in rc.Content.CardList)
            {
                if (!IsEligible(rc, c, pact)) continue;
                float w = c.Weight * RarityWeight(c.Rarity, rc.State.Wave) * rc.RarityShift(c.Rarity);
                if (w <= 0f) continue;
                if (IsSynergy(c)) w *= 1.6f;
                pool.Add(c);
                weights.Add(w);
            }
            var result = new List<CardDef>(count);
            if (pool.Count == 0) return result;

            // Slot 1: guarantee an actionable synergy card if any exist.
            if (!pact)
            {
                int synergyIndex = WeightedPick(rng, pool, weights, true);
                if (synergyIndex >= 0) Take(pool, weights, result, synergyIndex);
            }
            while (result.Count < count && pool.Count > 0)
            {
                int i = WeightedPick(rng, pool, weights, false);
                if (i < 0) break;
                Take(pool, weights, result, i);
            }
            // Strategic alternative: never three copies of the current plan when a different direction exists.
            if (!pact && result.Count >= 3 && result.TrueForAll(IsSynergy))
            {
                int alt = -1;
                float total = 0f;
                for (int i = 0; i < pool.Count; i++) if (!IsSynergy(pool[i])) total += weights[i];
                if (total > 0f)
                {
                    float roll = rng.NextFloat() * total;
                    for (int i = 0; i < pool.Count && alt < 0; i++)
                    {
                        if (IsSynergy(pool[i])) continue;
                        roll -= weights[i];
                        if (roll <= 0f) alt = i;
                    }
                    if (alt < 0) alt = pool.FindLastIndex(c => !IsSynergy(c));
                    result[result.Count - 1] = pool[alt];
                }
            }
            // Present in a stable but shuffled order so the guaranteed card is not always first.
            for (int i = result.Count - 1; i > 0; i--)
            {
                int j = rng.Range(0, i + 1);
                CardDef t = result[i];
                result[i] = result[j];
                result[j] = t;
            }
            return result;
        }

        private static void Take(List<CardDef> pool, List<float> weights, List<CardDef> result, int i)
        {
            result.Add(pool[i]);
            pool.RemoveAt(i);
            weights.RemoveAt(i);
        }

        private static int WeightedPick(Pcg32 rng, List<CardDef> pool, List<float> weights, bool synergyOnly)
        {
            float total = 0f;
            for (int i = 0; i < pool.Count; i++) if (!synergyOnly || IsSynergy(pool[i])) total += weights[i];
            if (total <= 0f) return -1;
            float roll = rng.NextFloat() * total;
            for (int i = 0; i < pool.Count; i++)
            {
                if (synergyOnly && !IsSynergy(pool[i])) continue;
                roll -= weights[i];
                if (roll <= 0f) return i;
            }
            for (int i = pool.Count - 1; i >= 0; i--) if (!synergyOnly || IsSynergy(pool[i])) return i;
            return -1;
        }

        public static bool RosterHasElement(RunController rc, Element e)
        {
            foreach (HeroRunState h in rc.State.Heroes) if (rc.Content.Heroes[h.DefId].Element == e) return true;
            return false;
        }

        public static bool RosterHasRole(RunController rc, HeroRole role)
        {
            foreach (HeroRunState h in rc.State.Heroes)
            {
                HeroDef d = rc.Content.Heroes[h.DefId];
                HeroRole effective = d.Role;
                if (!string.IsNullOrEmpty(h.EvolutionId) && rc.Content.Evolutions.TryGetValue(h.EvolutionId, out EvolutionDef evo) && evo.RoleOverride.HasValue)
                    effective = evo.RoleOverride.Value;
                if (effective == role) return true;
            }
            return false;
        }
    }
}
