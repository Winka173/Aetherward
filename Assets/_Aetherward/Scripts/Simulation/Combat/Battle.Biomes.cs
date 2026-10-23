using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    /// <summary>Biome rules: telegraphed hazards and destructible cover. Data in biomes.json.</summary>
    public sealed partial class Battle
    {
        private float[] _hazardTimers;
        private Pcg32 _hazardRng;

        private void UpdateAreaTraits()
        {
            foreach (HeroUnit hero in Heroes)
            {
                hero.Buffs.RemoveAll(b => b.Source != null && b.Source.StartsWith("area:"));
                if (!hero.Alive) continue;
                foreach (AreaTraitDef area in Biome.AreaTraits)
                {
                    if (Vec2.Distance(hero.Pos, area.Pos) > area.Radius) continue;
                    foreach (EffectOp op in area.Effects)
                        if (op.Op == "stat") hero.Buffs.Add(new TimedBuff { Stat = op.Stat,
                            Percent = op.Percent ? op.Value : 0f, Flat = op.Percent ? 0f : op.Value,
                            Remaining = 1f, Source = "area:" + area.Id });
                }
            }
        }

        private void SetupBiome()
        {
            _hazardTimers = new float[Biome.Hazards.Count];
            for (int i = 0; i < _hazardTimers.Length; i++) _hazardTimers[i] = Biome.Hazards[i].Interval * 0.6f;
            _hazardRng = Pcg32.Derive(Setup.Seed, "hazard:" + Wave.Number);
            foreach (CoverDef c in Biome.Covers)
            {
                if (!Content.Fields.TryGetValue(c.Field, out FieldDef f)) continue;
                Zone z = SpawnField(f, c.Pos, c.Radius, 99999f, null, 0f, 0, "biome", null);
                z.HitsLeft = c.Hits;
            }
        }

        /// <summary>Hazard kinds: lava vents (Fire), lightning strikes (Lightning), aether rifts (Void, pull), tidal surges (Water, push).</summary>
        public static Element HazardElement(string kind)
        {
            switch (kind)
            {
                case "lava_vents": return Element.Fire;
                case "lightning_strikes": return Element.Lightning;
                case "aether_rifts": return Element.Void;
                case "tidal_surge": return Element.Water;
                default: return Element.None;
            }
        }

        /// <summary>Rifts drag enemies inward, surges shove them back from the crystal (bosses resist both).</summary>
        private void HazardDisplacement(DelayedStrike s)
        {
            bool rift = s.SourceTag == "hazard_aether_rifts", surge = s.SourceTag == "hazard_tidal_surge";
            if (!rift && !surge) return;
            List<EnemyUnit> c = RentList();
            QueryEnemies(s.Pos, s.Radius + 0.5f, c);
            for (int i = 0; i < c.Count; i++)
            {
                if (rift) Pull(c[i], s.Pos, 2.4f, 0.4f);
                else Knock(c[i], (c[i].Pos - Crystal.Pos).Normalized, 1.4f);
            }
            ReturnList(c);
        }

        private void UpdateBiome(float dt)
        {
            for (int i = 0; i < _hazardTimers.Length; i++)
            {
                HazardDef hz = Biome.Hazards[i];
                if (Wave.Number < hz.FromWave || hz.Points.Count == 0) continue;
                _hazardTimers[i] -= dt;
                if (_hazardTimers[i] > 0f) continue;
                _hazardTimers[i] = hz.Interval * (1f - SimMath.Clamp(Setup.HazardShift, 0f, 0.6f));
                // Deterministic choice of distinct vents; heroes get a telegraph (Delay) to read the threat.
                int start = _hazardRng.Range(0, hz.Points.Count);
                for (int k = 0; k < hz.Count && k < hz.Points.Count; k++)
                {
                    Vec2 p = hz.Points[(start + k) % hz.Points.Count];
                    AddStrike(new DelayedStrike
                    {
                        Kind = StrikeKind.Hazard,
                        Pos = p,
                        Delay = hz.Delay,
                        Radius = hz.Radius,
                        Element = HazardElement(hz.Kind),
                        Power = hz.Power * WaveLevelScale,
                        Multiplier = 1f,
                        HeroDamagePct = hz.HeroDamagePct,
                        SourceTag = "hazard_" + hz.Kind,
                        Generation = MaxProcGeneration
                    });
                }
            }
        }
    }
}
