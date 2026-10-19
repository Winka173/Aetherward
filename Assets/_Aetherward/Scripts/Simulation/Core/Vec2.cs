using System;

namespace Aetherward.Sim.Core
{
    /// <summary>Minimal engine-independent 2D vector used by the simulation.</summary>
    [Serializable]
    public struct Vec2 : IEquatable<Vec2>
    {
        public float X;
        public float Y;

        public static readonly Vec2 Zero = new Vec2(0f, 0f);

        public Vec2(float x, float y)
        {
            X = x;
            Y = y;
        }

        public float Length => MathF.Sqrt(X * X + Y * Y);
        public float SqrLength => X * X + Y * Y;

        public Vec2 Normalized
        {
            get
            {
                float len = Length;
                return len > 1e-5f ? new Vec2(X / len, Y / len) : Zero;
            }
        }

        public static Vec2 operator +(Vec2 a, Vec2 b) => new Vec2(a.X + b.X, a.Y + b.Y);
        public static Vec2 operator -(Vec2 a, Vec2 b) => new Vec2(a.X - b.X, a.Y - b.Y);
        public static Vec2 operator -(Vec2 a) => new Vec2(-a.X, -a.Y);
        public static Vec2 operator *(Vec2 a, float s) => new Vec2(a.X * s, a.Y * s);
        public static Vec2 operator *(float s, Vec2 a) => new Vec2(a.X * s, a.Y * s);
        public static Vec2 operator /(Vec2 a, float s) => new Vec2(a.X / s, a.Y / s);

        public static float Dot(Vec2 a, Vec2 b) => a.X * b.X + a.Y * b.Y;
        public static float Distance(Vec2 a, Vec2 b) => (a - b).Length;
        public static float SqrDistance(Vec2 a, Vec2 b) => (a - b).SqrLength;

        public static Vec2 Lerp(Vec2 a, Vec2 b, float t)
        {
            return new Vec2(a.X + (b.X - a.X) * t, a.Y + (b.Y - a.Y) * t);
        }

        public static Vec2 FromAngle(float radians) => new Vec2(MathF.Cos(radians), MathF.Sin(radians));

        public float Angle => MathF.Atan2(Y, X);

        /// <summary>Moves toward target by at most maxStep without overshooting.</summary>
        public static Vec2 MoveTowards(Vec2 current, Vec2 target, float maxStep)
        {
            Vec2 delta = target - current;
            float dist = delta.Length;
            if (dist <= maxStep || dist < 1e-6f) return target;
            return current + delta / dist * maxStep;
        }

        /// <summary>Closest distance from point p to segment ab.</summary>
        public static float DistanceToSegment(Vec2 p, Vec2 a, Vec2 b)
        {
            Vec2 ab = b - a;
            float lenSq = ab.SqrLength;
            if (lenSq < 1e-8f) return Distance(p, a);
            float t = Dot(p - a, ab) / lenSq;
            if (t < 0f) t = 0f; else if (t > 1f) t = 1f;
            return Distance(p, a + ab * t);
        }

        public bool Equals(Vec2 other) => X == other.X && Y == other.Y;
        public override bool Equals(object obj) => obj is Vec2 v && Equals(v);
        public override int GetHashCode() => HashCode.Combine(X, Y);
        public override string ToString() => "(" + X.ToString("0.00") + ", " + Y.ToString("0.00") + ")";
    }

    public static class SimMath
    {
        public static float Clamp(float v, float min, float max) => v < min ? min : (v > max ? max : v);
        public static int Clamp(int v, int min, int max) => v < min ? min : (v > max ? max : v);
        public static float Clamp01(float v) => v < 0f ? 0f : (v > 1f ? 1f : v);
        public static float Lerp(float a, float b, float t) => a + (b - a) * t;
        public static float Max(float a, float b) => a > b ? a : b;
        public static float Min(float a, float b) => a < b ? a : b;
    }
}
