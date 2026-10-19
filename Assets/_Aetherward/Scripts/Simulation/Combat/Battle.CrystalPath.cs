using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    /// <summary>
    /// Crystal Evolution (feature-flagged): one permanent, mutually exclusive path chosen mid-run.
    /// bastion = sturdier Crystal, pulse = periodic Arcane nova around the Crystal, thorn = strong retaliation.
    /// Values live in <see cref="CrystalPaths"/> so tests, UI text and balance reports share one source.
    /// </summary>
    public sealed partial class Battle
    {
        private float _crystalPulseTimer;

        private void SetupCrystalPath()
        {
            switch (Setup.CrystalPath)
            {
                case CrystalPaths.Bastion:
                    Crystal.DamageReduction = SimMath.Clamp(Crystal.DamageReduction + CrystalPaths.BastionReduction, 0f, 0.6f);
                    Crystal.Regen += Crystal.MaxHp * CrystalPaths.BastionRegenPct;
                    break;
                case CrystalPaths.Thorn:
                    Crystal.Thorns += CrystalPaths.ThornAttack;
                    break;
                case CrystalPaths.Pulse:
                    _crystalPulseTimer = CrystalPaths.PulseInterval;
                    break;
            }
        }

        private void UpdateCrystalPath(float dt)
        {
            if (Setup.CrystalPath != CrystalPaths.Pulse || !Crystal.Alive) return;
            _crystalPulseTimer -= dt;
            if (_crystalPulseTimer > 0f) return;
            _crystalPulseTimer = CrystalPaths.PulseInterval;
            List<EnemyUnit> c = RentList();
            QueryEnemies(Crystal.Pos, CrystalPaths.PulseRadius, c);
            c.Sort((a, b) => a.Uid.CompareTo(b.Uid));
            Emit(SimEventType.Strike, Crystal.Pos, Element.Arcane, CrystalPaths.PulseRadius, 0, 0, "crystal_pulse");
            for (int i = 0; i < c.Count; i++)
            {
                if (!c[i].Alive) continue;
                DealDamage(c[i], new DamageRequest { Attack = CrystalPaths.PulseAttack * WaveLevelScale, Multiplier = 1f, Element = Element.Arcane, Kind = DamageKind.Trigger, Generation = MaxProcGeneration, SourceTag = "crystal_pulse" });
            }
            ReturnList(c);
        }
    }

    /// <summary>Crystal Evolution path ids and tuning (shared by sim, run layer, UI and tests).</summary>
    public static class CrystalPaths
    {
        public const string Bastion = "bastion";
        public const string Pulse = "pulse";
        public const string Thorn = "thorn";
        public static readonly string[] All = { Bastion, Pulse, Thorn };

        /// <summary>Clearing this wave offers the choice (once per run).</summary>
        public const int OfferAfterWave = 6;

        public const float BastionReduction = 0.07f;
        public const float BastionRegenPct = 0.0015f;  // of max HP per second
        public const float PulseInterval = 6f;
        public const float PulseRadius = 3.2f;
        public const float PulseAttack = 55f;          // Arcane, scaled by wave level
        public const float ThornAttack = 45f;          // added to Crystal thorns (scaled by wave level)

        public static bool IsValid(string id) => id == Bastion || id == Pulse || id == Thorn;
    }
}
