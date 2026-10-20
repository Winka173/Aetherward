using System;

namespace Aetherward.Sim.Presentation
{
    /// <summary>Settings → Effects intensity. Stored as an int in settings ("fxPreset").</summary>
    public enum EffectsPreset
    {
        Minimal = 0,
        Reduced = 1,
        Standard = 2,
        Cinematic = 3
    }

    /// <summary>
    /// Game-feel multipliers for one effects preset (P7), engine-free so the rules are unit tested.
    /// Accessibility toggles are hard caps the preset can never exceed: Screen shake off = no shake at any preset,
    /// Flash intensity caps every flash, Reduced VFX / Battery saver cap the preset at Reduced.
    /// Presentation only: nothing here changes simulation results (hitstop delays real-time pacing, not ticks).
    /// </summary>
    public readonly struct FeelProfile
    {
        public readonly EffectsPreset Preset;
        public readonly float ShakeScale;      // multiplies every camera shake request
        public readonly float FlashScale;      // multiplies sprite hit flashes (already capped by FlashIntensity)
        public readonly float FxDensity;       // 0..1: probability scale for optional sprite effects
        public readonly float AnimAmplitude;   // cast/hit pose strength (0 = units stay at rest pose)
        public readonly float HitstopSeconds;  // real-time pause on heavy impacts (0 = off)

        private FeelProfile(EffectsPreset p, float shake, float flash, float fx, float anim, float hitstop)
        {
            Preset = p;
            ShakeScale = shake;
            FlashScale = flash;
            FxDensity = fx;
            AnimAmplitude = anim;
            HitstopSeconds = hitstop;
        }

        public static FeelProfile For(EffectsPreset requested, bool screenShake, float flashIntensity, bool reducedVfx, bool batterySaver)
        {
            EffectsPreset p = requested;
            if ((reducedVfx || batterySaver) && p > EffectsPreset.Reduced) p = EffectsPreset.Reduced;
            float shake, flash, fx, anim, stop;
            switch (p)
            {
                case EffectsPreset.Minimal: shake = 0f; flash = 0.35f; fx = 0f; anim = 0.35f; stop = 0f; break;
                case EffectsPreset.Reduced: shake = 0.5f; flash = 0.7f; fx = 0.45f; anim = 0.7f; stop = 0f; break;
                case EffectsPreset.Cinematic: shake = 1.25f; flash = 1f; fx = 1f; anim = 1.25f; stop = 0.06f; break;
                default: shake = 1f; flash = 1f; fx = 1f; anim = 1f; stop = 0.04f; break;
            }
            if (!screenShake) shake = 0f;
            flash *= Math.Max(0f, Math.Min(1f, flashIntensity));
            return new FeelProfile(p, shake, flash, fx, anim, stop);
        }

        public static EffectsPreset Clamp(int stored) =>
            stored < (int)EffectsPreset.Minimal || stored > (int)EffectsPreset.Cinematic ? EffectsPreset.Standard : (EffectsPreset)stored;
    }

    /// <summary>
    /// Hitstop budget: a short real-time freeze on heavy impacts (crit, boss slam, big crystal hit). Rate-limited so a
    /// stream of crits never stalls the battle: at most one stop per <see cref="Cooldown"/> seconds, and at 2x speed
    /// the stop is halved. Returns the seconds of pacing to withhold; the simulation itself still runs every tick.
    /// </summary>
    public sealed class Hitstop
    {
        public float Cooldown = 0.45f;
        private float _until = float.MinValue, _ready = float.MinValue;

        public void Trigger(float seconds, int speed, float now)
        {
            if (seconds <= 0f || now < _ready) return;
            float s = speed > 1 ? seconds * 0.5f : seconds;
            _until = Math.Max(_until, now + s);
            _ready = now + Cooldown;
        }

        public bool Active(float now) => now < _until;

        public void Reset()
        {
            _until = _ready = float.MinValue;
        }
    }
}
