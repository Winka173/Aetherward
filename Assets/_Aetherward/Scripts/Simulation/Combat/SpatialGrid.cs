using System.Collections.Generic;
using Aetherward.Sim.Core;

namespace Aetherward.Sim.Combat
{
    /// <summary>
    /// Uniform grid over the arena for enemy proximity queries (targeting, AoE, separation, chains).
    /// Rebuilt once per tick; queries never allocate when given a reusable result list.
    /// </summary>
    public sealed class SpatialGrid
    {
        private readonly float _cell;
        private readonly float _minX, _minY;
        private readonly int _cols, _rows;
        private readonly List<EnemyUnit>[] _cells;

        public SpatialGrid(float halfWidth, float halfHeight, float cellSize)
        {
            _cell = cellSize;
            _minX = -halfWidth - 2f;
            _minY = -halfHeight - 2f;
            _cols = (int)((halfWidth * 2f + 4f) / cellSize) + 1;
            _rows = (int)((halfHeight * 2f + 4f) / cellSize) + 1;
            _cells = new List<EnemyUnit>[_cols * _rows];
            for (int i = 0; i < _cells.Length; i++) _cells[i] = new List<EnemyUnit>(8);
        }

        public void Rebuild(List<EnemyUnit> enemies)
        {
            for (int i = 0; i < _cells.Length; i++) _cells[i].Clear();
            for (int i = 0; i < enemies.Count; i++)
            {
                EnemyUnit e = enemies[i];
                if (!e.Alive) continue;
                _cells[CellIndex(e.Pos)].Add(e);
            }
        }

        private int CellIndex(Vec2 p)
        {
            int cx = SimMath.Clamp((int)((p.X - _minX) / _cell), 0, _cols - 1);
            int cy = SimMath.Clamp((int)((p.Y - _minY) / _cell), 0, _rows - 1);
            return cy * _cols + cx;
        }

        /// <summary>Collects living enemies whose body overlaps the circle. Results are in grid order.</summary>
        public void Query(Vec2 center, float radius, List<EnemyUnit> results)
        {
            results.Clear();
            int x0 = SimMath.Clamp((int)((center.X - radius - 1f - _minX) / _cell), 0, _cols - 1);
            int x1 = SimMath.Clamp((int)((center.X + radius + 1f - _minX) / _cell), 0, _cols - 1);
            int y0 = SimMath.Clamp((int)((center.Y - radius - 1f - _minY) / _cell), 0, _rows - 1);
            int y1 = SimMath.Clamp((int)((center.Y + radius + 1f - _minY) / _cell), 0, _rows - 1);
            for (int y = y0; y <= y1; y++)
            {
                for (int x = x0; x <= x1; x++)
                {
                    List<EnemyUnit> cell = _cells[y * _cols + x];
                    for (int i = 0; i < cell.Count; i++)
                    {
                        EnemyUnit e = cell[i];
                        if (!e.Alive) continue;
                        float r = radius + e.Radius;
                        if (Vec2.SqrDistance(center, e.Pos) <= r * r) results.Add(e);
                    }
                }
            }
            // Deterministic order regardless of cell traversal: sort by uid.
            if (results.Count > 1) results.Sort(UidComparer.Instance);
        }

        private sealed class UidComparer : IComparer<EnemyUnit>
        {
            public static readonly UidComparer Instance = new UidComparer();
            public int Compare(EnemyUnit a, EnemyUnit b) => a.Uid.CompareTo(b.Uid);
        }
    }
}
