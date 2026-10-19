namespace Aetherward.Sim.Run
{
    /// <summary>
    /// Defaults for features that can be switched off without code changes elsewhere. Each run copies the
    /// flag into its own state (and save), so changing a default never alters a run in progress.
    /// </summary>
    public static class FeatureFlags
    {
        /// <summary>Crystal Evolution: one permanent, exclusive Crystal path offered after wave 6.</summary>
        public static bool CrystalEvolution = true;

        /// <summary>Utility-scored basic-attack targeting (false = legacy per-profile targeting).</summary>
        public static bool UtilityTargeting = true;
    }
}
