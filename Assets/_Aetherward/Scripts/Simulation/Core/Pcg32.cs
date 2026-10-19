using System;

namespace Aetherward.Sim.Core
{
    /// <summary>
    /// Deterministic PCG32 generator (O'Neill, PCG-XSH-RR). Independent of UnityEngine.Random so
    /// combat, draft and wave rolls replay identically for a given seed on the same platform.
    /// </summary>
    public sealed class Pcg32
    {
        private const ulong Multiplier = 6364136223846793005UL;
        private ulong _state;
        private readonly ulong _increment;

        public Pcg32(ulong seed, ulong stream = 1442695040888963407UL)
        {
            _increment = (stream << 1) | 1UL;
            _state = 0UL;
            NextUInt();
            _state += seed;
            NextUInt();
        }

        /// <summary>Derives an independent child stream, e.g. one per wave or per system.</summary>
        public static Pcg32 Derive(ulong seed, string streamName)
        {
            return new Pcg32(seed ^ Hash64(streamName), Hash64(streamName + "#stream"));
        }

        public uint NextUInt()
        {
            ulong old = _state;
            _state = unchecked(old * Multiplier + _increment);
            uint xorShifted = (uint)(((old >> 18) ^ old) >> 27);
            int rot = (int)(old >> 59);
            return (xorShifted >> rot) | (xorShifted << ((-rot) & 31));
        }

        /// <summary>Uniform float in [0, 1).</summary>
        public float NextFloat()
        {
            return (NextUInt() >> 8) * (1f / 16777216f);
        }

        public float Range(float min, float max)
        {
            return min + (max - min) * NextFloat();
        }

        /// <summary>Uniform int in [min, maxExclusive). Uses rejection sampling to avoid modulo bias.</summary>
        public int Range(int min, int maxExclusive)
        {
            if (maxExclusive <= min) return min;
            uint bound = (uint)(maxExclusive - min);
            uint threshold = (uint)(-(int)bound) % bound;
            while (true)
            {
                uint r = NextUInt();
                if (r >= threshold) return min + (int)(r % bound);
            }
        }

        public bool Chance(float probability)
        {
            if (probability <= 0f) return false;
            if (probability >= 1f) return true;
            return NextFloat() < probability;
        }

        /// <summary>FNV-1a 64-bit; stable across runtimes (unlike string.GetHashCode).</summary>
        public static ulong Hash64(string text)
        {
            ulong hash = 14695981039346656037UL;
            if (text == null) return hash;
            for (int i = 0; i < text.Length; i++)
            {
                hash ^= text[i];
                hash = unchecked(hash * 1099511628211UL);
            }
            return hash;
        }

        /// <summary>Human-friendly seed formatting, e.g. "7F3A-91C2".</summary>
        public static string FormatSeed(ulong seed)
        {
            uint folded = (uint)(seed ^ (seed >> 32));
            return (folded >> 16).ToString("X4") + "-" + (folded & 0xFFFF).ToString("X4");
        }

        public static ulong SeedFromTime(DateTime utcNow)
        {
            return Hash64(utcNow.Ticks.ToString());
        }
    }
}
