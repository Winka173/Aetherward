using System.Collections.Generic;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using UnityEngine;

namespace Aetherward.Game
{
    /// <summary>
    /// Debug overlay (Settings "Show ranges" or F3): hero attack ranges and leash circles, enemy
    /// target lines, approach lanes. Uses pooled LineRenderers so it works in any build.
    /// </summary>
    public sealed class DebugOverlay : MonoBehaviour
    {
        private BattleController _owner;
        private readonly List<LineRenderer> _lines = new List<LineRenderer>();
        private int _used;
        private Material _mat;

        public void Init(BattleController owner)
        {
            _owner = owner;
            _mat = WorldGfx.SpriteMaterial;
        }

        private LineRenderer Next()
        {
            LineRenderer lr;
            if (_used < _lines.Count) lr = _lines[_used];
            else
            {
                var go = new GameObject("DebugLine");
                go.transform.SetParent(transform, false);
                lr = go.AddComponent<LineRenderer>();
                lr.sharedMaterial = _mat;
                lr.useWorldSpace = true;
                lr.sortingOrder = 20000;
                lr.numCapVertices = 0;
                _lines.Add(lr);
            }
            _used++;
            lr.enabled = true;
            return lr;
        }

        private void Circle(Vector3 c, float r, Color color, float width = 0.03f)
        {
            LineRenderer lr = Next();
            const int seg = 40;
            lr.positionCount = seg + 1;
            for (int i = 0; i <= seg; i++)
            {
                float a = i * Mathf.PI * 2f / seg;
                lr.SetPosition(i, c + new Vector3(Mathf.Cos(a) * r, Mathf.Sin(a) * r, 0));
            }
            lr.startColor = lr.endColor = color;
            lr.startWidth = lr.endWidth = width;
        }

        private void Line(Vector3 a, Vector3 b, Color color, float width = 0.025f)
        {
            LineRenderer lr = Next();
            lr.positionCount = 2;
            lr.SetPosition(0, a);
            lr.SetPosition(1, b);
            lr.startColor = lr.endColor = color;
            lr.startWidth = lr.endWidth = width;
        }

        /// <summary>AI inspector (debug ranges toggle): each hero's last targeting decision and weighted reasons.</summary>
        private void OnGUI()
        {
            if (_owner == null || !App.Settings.ShowRanges) return;
            Battle b = _owner.Run.Battle;
            if (b == null) return;
            float y = 260;
            GUI.color = new Color(1f, 1f, 1f, 0.9f);
            foreach (HeroUnit h in b.Heroes)
            {
                TargetDecision d = h.Decision;
                string line = h.Def.Id + ": ";
                if (d == null) line += "—";
                else if (d.Reason != null && d.TargetUid == 0) line += d.Reason;
                else
                {
                    line += "target #" + d.TargetUid + " score " + d.Total.ToString("F2") + " of " + d.Candidates + (d.KeptByHysteresis ? " (kept)" : "");
                    for (int k = 0; k < TargetDecision.Components; k++) if (d.Parts[k] > 0.01f) line += "  " + TargetDecision.Names[k] + " " + d.Parts[k].ToString("F2");
                    if (d.RunnerUpUid != 0) line += "  | next #" + d.RunnerUpUid + " " + d.RunnerUpTotal.ToString("F2");
                }
                if (h.SilenceTimer > 0f) line += "  [silenced]";
                if (h.SkillTimer > 0f) line += "  skill in " + h.SkillTimer.ToString("F1") + "s";
                GUI.Label(new Rect(12, y, Screen.width - 24, 22), line);
                y += 22;
            }
            GUI.color = Color.white;
        }

        private void LateUpdate()
        {
            _used = 0;
            if (_owner != null && App.Settings.ShowRanges)
            {
                ArenaDef arena = _owner.Run.Arena;
                foreach (LaneDef lane in arena.Lanes)
                    for (int i = 0; i < lane.Points.Count - 1; i++)
                        Line(WorldGfx.V(lane.Points[i]), WorldGfx.V(lane.Points[i + 1]), new Color(1f, 0.4f, 0.4f, 0.5f), 0.05f);
                Battle b = _owner.Run.Battle;
                if (b != null)
                {
                    foreach (HeroUnit h in b.Heroes)
                    {
                        if (!h.Alive) continue;
                        Circle(WorldGfx.V(h.Pos), h.Stat(StatId.Range) + 0.3f, new Color(0.5f, 1f, 0.6f, 0.6f));
                        if (h.Stat(StatId.LeashRadius) > 0.3f) Circle(WorldGfx.V(h.Anchor), h.Stat(StatId.LeashRadius), new Color(1f, 0.85f, 0.3f, 0.5f));
                        if (h.Target != null && h.Target.Alive) Line(WorldGfx.V(h.Pos), WorldGfx.V(h.Target.Pos), new Color(0.5f, 1f, 0.6f, 0.4f));
                    }
                    int budget = 80;
                    foreach (EnemyUnit e in b.Enemies)
                    {
                        if (budget-- <= 0) break;
                        HeroUnit t = e.Taunter ?? e.Engaged;
                        if (t != null) Line(WorldGfx.V(e.Pos), WorldGfx.V(t.Pos), new Color(1f, 0.4f, 0.3f, 0.5f));
                    }
                    Circle(Vector3.zero, b.Crystal.Radius, new Color(0.5f, 0.9f, 1f, 0.7f), 0.05f);
                }
            }
            for (int i = _used; i < _lines.Count; i++) _lines[i].enabled = false;
        }
    }
}
