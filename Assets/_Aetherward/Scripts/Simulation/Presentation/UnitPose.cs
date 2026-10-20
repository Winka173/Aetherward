using System;

namespace Aetherward.Sim.Presentation
{
    /// <summary>Offset (world units) and scale applied to a unit's body sprite on top of its idle bob.</summary>
    public struct BodyPose
    {
        public float X, Y, ScaleX, ScaleY;

        public static BodyPose Rest => new BodyPose { ScaleX = 1f, ScaleY = 1f };

        /// <summary>Offsets add, scales multiply (a hit during a cast keeps both readable).</summary>
        public BodyPose Combine(BodyPose o) => new BodyPose { X = X + o.X, Y = Y + o.Y, ScaleX = ScaleX * o.ScaleX, ScaleY = ScaleY * o.ScaleY };

        public bool IsRest(float eps = 1e-4f) =>
            Math.Abs(X) < eps && Math.Abs(Y) < eps && Math.Abs(ScaleX - 1f) < eps && Math.Abs(ScaleY - 1f) < eps;
    }

    /// <summary>
    /// Procedural cast and hit poses (P7), engine-free so timing is unit tested. A skill cast reads as
    /// anticipation → release → recovery instead of a single wobble; a hit recoils away from the attacker and settles.
    /// Every curve starts and ends exactly at rest, so interrupted or overlapping animations never leave a unit
    /// skewed. <c>amplitude</c> comes from <see cref="FeelProfile.AnimAmplitude"/> (0 = always at rest).
    /// </summary>
    public static class UnitPose
    {
        public const float Windup = 0.09f, Release = 0.10f, Recover = 0.26f;
        public const float CastDuration = Windup + Release + Recover;
        public const float HitDuration = 0.14f, HeavyHitDuration = 0.2f;

        private const float Squash = 0.08f, Stretch = 0.10f, Rise = 0.06f;

        /// <param name="t">Seconds since the cast started.</param>
        public static BodyPose Cast(float t, float amplitude)
        {
            if (t <= 0f || t >= CastDuration || amplitude <= 0f) return BodyPose.Rest;
            float s, y;   // s > 0 stretches tall, s < 0 squashes
            if (t < Windup)
            {
                float u = EaseInOut(t / Windup);
                s = -Squash * u;
                y = -0.03f * u;
            }
            else if (t < Windup + Release)
            {
                float u = EaseOut((t - Windup) / Release);
                s = -Squash + (Squash + Stretch) * u;
                y = -0.03f + (0.03f + Rise) * u;
            }
            else
            {
                // Damped settle: from full stretch back to rest with one small undershoot.
                float u = (t - Windup - Release) / Recover;
                float k = (1f - u) * (float)Math.Cos(u * Math.PI * 1.5);
                s = Stretch * k;
                y = Rise * Math.Max(0f, k);
            }
            s *= amplitude;
            return new BodyPose { X = 0f, Y = y * amplitude, ScaleX = 1f - s * 0.6f, ScaleY = 1f + s };
        }

        /// <param name="t">Seconds since the hit.</param>
        /// <param name="dirX">Unit vector from the attacker to the victim (recoil direction).</param>
        public static BodyPose Hit(float t, float dirX, float dirY, bool heavy, float amplitude)
        {
            float dur = heavy ? HeavyHitDuration : HitDuration;
            if (t <= 0f || t >= dur || amplitude <= 0f) return BodyPose.Rest;
            float u = t / dur;
            // Fast knock-out (first 25%), eased return.
            float k = u < 0.25f ? EaseOut(u / 0.25f) : 1f - EaseInOut((u - 0.25f) / 0.75f);
            float dist = (heavy ? 0.16f : 0.09f) * amplitude * k;
            float sq = (heavy ? 0.09f : 0.05f) * amplitude * k;
            return new BodyPose { X = dirX * dist, Y = dirY * dist * 0.5f, ScaleX = 1f + sq, ScaleY = 1f - sq };
        }

        private static float EaseOut(float u) => 1f - (1f - u) * (1f - u);

        private static float EaseInOut(float u) => u * u * (3f - 2f * u);
    }
}
