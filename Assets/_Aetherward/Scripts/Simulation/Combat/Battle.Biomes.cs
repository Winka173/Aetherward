using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    /// <summary>Biome rules: telegraphed hazards and destructible cover. Data in biomes.json.</summary>
    public sealed partial class Battle
    {
        private float[] _hazardTimers;
        private Pcg32 _hazardRng;

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

        private void UpdateBiome(float dt)
        {
            for (int i = 0; i < _hazardTimers.Length; i++)
            {
                HazardDef hz = Biome.Hazards[i];
                if (Wave.Number < hz.FromWave || hz.Points.Count == 0) continue;
                _hazardTimers[i] -= dt;
                if (_hazardTimers[i] > 0f) continue;
                _hazardTimers[i] = hz.Interval;
                // Deterministic choice of distinct vents; heroes get a telegraph (Delay) to read the threat.
                int start = _hazardRng.Range(0, hz.Points.Count);
                for (int k = 0; k < hz.Count && k < hz.Points.Count; k++)
                {
                    Vec2 p = hz.Points[(start + k * 2) % hz.Points.Count];
                    AddStrike(new DelayedStrike
                    {
                        Kind = StrikeKind.Hazard,
                        Pos = p,
                        Delay = hz.Delay,
                        Radius = hz.Radius,
                        Element = hz.Kind == "lava_vents" ? Element.Fire : Element.None,
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
