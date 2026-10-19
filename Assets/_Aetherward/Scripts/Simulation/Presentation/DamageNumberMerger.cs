using System.Collections.Generic;

namespace Aetherward.Sim.Presentation
{
    /// <summary>
    /// Readability rule for floating damage numbers (engine-free so it can be unit tested): hits on the same
    /// target within <see cref="Window"/> seconds fold into one growing number instead of a pile of small ones.
    /// A crit always keeps its own number (it is a moment worth seeing). Callers own the visual entries; this
    /// class only decides "new number" vs "add to number N".
    /// </summary>
    public sealed class DamageNumberMerger
    {
        public struct Result
        {
            public bool Merged;   // true: update the existing number with Slot
            public int Slot;      // caller's id for the floating entry
            public float Total;   // value to display
        }

        private struct Open
        {
            public int Slot;
            public float Total;
            public float Since;
        }

        public float Window = 0.3f;
        private readonly Dictionary<int, Open> _open = new Dictionary<int, Open>();
        private int _nextSlot = 1;

        public Result Add(int targetUid, float value, bool crit, float now)
        {
            if (!crit && _open.TryGetValue(targetUid, out Open o) && now - o.Since <= Window)
            {
                o.Total += value;
                _open[targetUid] = o;
                return new Result { Merged = true, Slot = o.Slot, Total = o.Total };
            }
            int slot = _nextSlot++;
            if (!crit) _open[targetUid] = new Open { Slot = slot, Total = value, Since = now };
            return new Result { Merged = false, Slot = slot, Total = value };
        }

        /// <summary>Drops merge windows older than <see cref="Window"/> (call once per frame).</summary>
        public void Prune(float now)
        {
            if (_open.Count == 0) return;
            _stale.Clear();
            foreach (var kv in _open) if (now - kv.Value.Since > Window) _stale.Add(kv.Key);
            foreach (int k in _stale) _open.Remove(k);
        }

        public void Clear() => _open.Clear();

        private readonly List<int> _stale = new List<int>();
    }
}
