namespace Aetherward.Sim.Presentation
{
    /// <summary>
    /// Assistive mode (P4): while a boss telegraph is on screen at 2x speed, play at 1x until the strike lands, so
    /// the readable window is the same as at normal speed. Simulation results are unaffected (only real-time pacing).
    /// </summary>
    public sealed class TelegraphAssist
    {
        public bool Enabled;
        private float _slowUntil = float.MinValue;

        /// <param name="lead">Simulation seconds until the telegraphed strike resolves.</param>
        public void OnTelegraph(bool fromBoss, float lead, float now)
        {
            if (!Enabled || !fromBoss || lead <= 0f) return;
            float until = now + lead;   // at 1x, sim seconds == real seconds
            if (until > _slowUntil) _slowUntil = until;
        }

        public int EffectiveSpeed(int requested, float now) => Enabled && requested > 1 && now < _slowUntil ? 1 : requested;

        public bool Active(float now) => Enabled && now < _slowUntil;

        public void Reset() => _slowUntil = float.MinValue;
    }
}
