using System;
using System.Collections.Generic;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    /// <summary>Deterministic navigation over the union of walk regions, with wall and crystal clearance.
    /// A shared grid is built once per battle; direct movement avoids searches in open rooms.</summary>
    public sealed class HavenNavigation
    {
        private const float Step = 0.5f;
        private static readonly System.Runtime.CompilerServices.ConditionalWeakTable<ArenaDef, HavenNavigation> Cache = new System.Runtime.CompilerServices.ConditionalWeakTable<ArenaDef, HavenNavigation>();
        public static HavenNavigation For(ArenaDef arena) => Cache.GetValue(arena, a => new HavenNavigation(a));
        private readonly ArenaDef _arena;
        private readonly int _width, _height;
        private readonly bool[] _open;
        private readonly int[] _parent, _queue;
        private readonly List<int>[] _edges;
        private const float Clearance = 0.42f;

        public HavenNavigation(ArenaDef arena)
        {
            _arena = arena;
            _width = (int)(arena.HalfWidth * 2f / Step) + 1;
            _height = (int)(arena.HalfHeight * 2f / Step) + 1;
            int count = _width * _height;
            _open = new bool[count]; _parent = new int[count]; _queue = new int[count];
            _edges = new List<int>[count];
            for (int i = 0; i < count; i++) _open[i] = CanStand(Point(i), Clearance);
            for (int i = 0; i < count; i++)
            {
                if (!_open[i]) continue;
                _edges[i] = new List<int>(8);
                int x = i % _width, y = i / _width;
                for (int dy = -1; dy <= 1; dy++)
                    for (int dx = -1; dx <= 1; dx++)
                    {
                        if ((dx == 0 && dy == 0) || x + dx < 0 || x + dx >= _width || y + dy < 0 || y + dy >= _height) continue;
                        int n = i + dy * _width + dx;
                        if (_open[n] && CanTravel(Point(i), Point(n), Clearance)) _edges[i].Add(n);
                    }
            }
        }

        private Vec2 Point(int i) => new Vec2(i % _width * Step - _arena.HalfWidth, i / _width * Step - _arena.HalfHeight);

        private bool Inside(Vec2 p)
        {
            foreach (float[] w in _arena.Walk)
                if (p.X >= w[0] && p.X <= w[2] && p.Y >= w[1] && p.Y <= w[3]) return true;
            return false;
        }

        public bool CanStand(Vec2 p, float radius)
        {
            if (Math.Abs(p.X) + radius > _arena.HalfWidth || Math.Abs(p.Y) + radius > _arena.HalfHeight) return false;
            if (p.Length < _arena.CrystalRadius + radius + 0.02f) return false;
            if (!Inside(p) || !Inside(p + new Vec2(radius, 0)) || !Inside(p - new Vec2(radius, 0))
                || !Inside(p + new Vec2(0, radius)) || !Inside(p - new Vec2(0, radius))) return false;
            foreach (float[] w in _arena.Walls)
            {
                float x = Math.Max(w[0], Math.Min(w[2], p.X)), y = Math.Max(w[1], Math.Min(w[3], p.Y));
                if (Vec2.SqrDistance(p, new Vec2(x, y)) < radius * radius) return false;
            }
            return true;
        }

        public bool CanTravel(Vec2 from, Vec2 to, float radius)
        {
            int steps = Math.Max(1, (int)Math.Ceiling(Vec2.Distance(from, to) / 0.15f));
            for (int i = 0; i <= steps; i++)
                if (!CanStand(from + (to - from) * ((float)i / steps), radius)) return false;
            return true;
        }

        private int Nearest(Vec2 p, Vec2? visibleFrom = null)
        {
            int best = -1; float dist = float.MaxValue;
            for (int i = 0; i < _open.Length; i++)
            {
                if (!_open[i]) continue;
                float d = Vec2.SqrDistance(p, Point(i));
                if (d >= dist || (visibleFrom.HasValue && !CanTravel(visibleFrom.Value, Point(i), Clearance))) continue;
                best = i; dist = d;
            }
            return best;
        }

        public Vec2 Project(Vec2 p, float radius)
        {
            if (CanStand(p, radius)) return p;
            int n = Nearest(p);
            return n >= 0 ? Point(n) : p;
        }

        public void FindPath(Vec2 from, Vec2 to, List<Vec2> path)
        {
            path.Clear();
            int start = Nearest(from, from), end = Nearest(to);
            if (start < 0 || end < 0) return;
            Array.Fill(_parent, -1);
            int head = 0, tail = 0;
            _queue[tail++] = start; _parent[start] = start;
            while (head < tail && _parent[end] < 0)
            {
                int at = _queue[head++];
                foreach (int n in _edges[at])
                {
                    if (_parent[n] >= 0) continue;
                    _parent[n] = at; _queue[tail++] = n;
                }
            }
            if (_parent[end] < 0) return;
            for (int at = end; at != start; at = _parent[at]) path.Add(Point(at));
            path.Add(Point(start)); path.Reverse();
            if (CanTravel(Point(end), to, Clearance)) path.Add(to);
        }
    }
}
