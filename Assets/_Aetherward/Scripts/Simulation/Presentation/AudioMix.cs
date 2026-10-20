namespace Aetherward.Sim.Presentation
{
    /// <summary>
    /// SFX voice allocation and ducking rules (P7), engine-free so they are unit tested. With a fixed pool of voices,
    /// a burst of hit sounds must never cut off a boss roar or a telegraph warning:
    ///  - a free voice is used first;
    ///  - otherwise the voice with the lowest priority (oldest among equals) is stolen, but only if its priority is
    ///    not higher than the new sound's; a low-priority sound that finds only important voices is dropped.
    /// Ducking: a high-priority cue lowers every other SFX for a short time so the cue is heard over the mix.
    /// </summary>
    public static class AudioMix
    {
        public const int Low = 0, Normal = 1, High = 2, Critical = 3;

        /// <summary>Returns the voice index to use, or -1 to drop the new sound.</summary>
        public static int PickVoice(bool[] playing, int[] priority, float[] startedAt, int newPriority)
        {
            for (int i = 0; i < playing.Length; i++)
                if (!playing[i]) return i;
            int best = -1;
            for (int i = 0; i < playing.Length; i++)
            {
                if (priority[i] > newPriority) continue;
                if (best < 0 || priority[i] < priority[best] || priority[i] == priority[best] && startedAt[i] < startedAt[best]) best = i;
            }
            return best;
        }

        /// <summary>Volume multiplier for a sound of <paramref name="priority"/> while a duck is active until <paramref name="duckUntil"/>.</summary>
        public static float DuckGain(int priority, float now, float duckUntil, float depth = 0.45f) =>
            priority < Critical && now < duckUntil ? 1f - depth : 1f;
    }
}
