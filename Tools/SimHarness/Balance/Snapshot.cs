using System.Globalization;
using System.IO;
using System.Text;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Run;

namespace Aetherward.Balance
{
    /// <summary>
    /// Plays a seeded auto-pilot run up to a wave, simulates that wave for N seconds and dumps the
    /// world state as JSON. Used by Tools/AssetGen/preview/compose_frame.py to render an OFFLINE
    /// composite of what the battlefield contains (not a Unity capture).
    /// </summary>
    public static class Snapshot
    {
        private static string F(float v) => v.ToString("0.###", CultureInfo.InvariantCulture);

        public static void Write(ContentDatabase db, Strategy st, int wave, float seconds, string path)
        {
            RunController rc = RunController.NewRun(db, 4242, st.Starters, 0, RunUnlocks.Everything(db));
            var pilot = new AutoPilot(rc, st);
            for (int guard = 0; guard < 4000 && !(rc.State.Phase == RunPhase.Prepare && rc.State.Wave == wave) && !rc.State.Finished; guard++)
            {
                switch (rc.State.Phase)
                {
                    case RunPhase.Prepare: pilot.Prepare(); rc.StartWave(); break;
                    case RunPhase.Battle: rc.Battle.RunToEnd(); rc.ResolveBattle(); break;
                    default: pilot.PlayToEnd(1); break;
                }
            }
            pilot.Prepare();
            Battle b = rc.StartWave();
            while (b.Time < seconds && b.Outcome == BattleOutcome.Running) { b.Tick(); b.Journal.Clear(); }
            var sb = new StringBuilder();
            sb.Append("{\"wave\":").Append(wave).Append(",\"time\":").Append(F(b.Time)).Append(",\"crystal\":").Append(F(b.Crystal.HpFraction));
            sb.Append(",\"heroes\":[");
            for (int i = 0; i < b.Heroes.Count; i++)
            {
                HeroUnit h = b.Heroes[i];
                string evo = h.EvolutionId == null ? "" : (h.Def.Evolutions.IndexOf(h.EvolutionId) == 0 ? "A" : "B");
                if (i > 0) sb.Append(',');
                sb.Append("{\"id\":\"").Append(h.Def.Id).Append("\",\"evo\":\"").Append(evo).Append("\",\"x\":").Append(F(h.Pos.X)).Append(",\"y\":").Append(F(h.Pos.Y))
                  .Append(",\"fx\":").Append(F(h.Facing.X)).Append(",\"hp\":").Append(F(h.HpFraction)).Append(",\"alive\":").Append(h.Alive ? "true" : "false").Append('}');
            }
            sb.Append("],\"enemies\":[");
            bool first = true;
            foreach (EnemyUnit e in b.Enemies)
            {
                if (!e.Alive) continue;
                if (!first) sb.Append(',');
                first = false;
                e.DominantStatuses(out Element s1, out Element s2);
                sb.Append("{\"id\":\"").Append(e.Def.Id).Append("\",\"x\":").Append(F(e.Pos.X)).Append(",\"y\":").Append(F(e.Pos.Y)).Append(",\"fx\":").Append(F(e.Facing.X))
                  .Append(",\"hp\":").Append(F(e.HpFraction)).Append(",\"elite\":").Append(e.Elite ? "true" : "false").Append(",\"boss\":").Append(e.IsBoss ? "true" : "false")
                  .Append(",\"s1\":\"").Append(ElementUtil.Key(s1)).Append("\",\"s2\":\"").Append(ElementUtil.Key(s2)).Append("\"}");
            }
            sb.Append("],\"zones\":[");
            for (int i = 0; i < b.Zones.Count; i++)
            {
                Zone z = b.Zones[i];
                if (i > 0) sb.Append(',');
                sb.Append("{\"kind\":\"").Append(z.Kind).Append("\",\"x\":").Append(F(z.Pos.X)).Append(",\"y\":").Append(F(z.Pos.Y)).Append(",\"r\":").Append(F(z.Radius)).Append('}');
            }
            sb.Append("],\"projectiles\":[");
            first = true;
            foreach (Projectile p in b.Projectiles)
            {
                if (!p.Alive) continue;
                if (!first) sb.Append(',');
                first = false;
                sb.Append("{\"visual\":\"").Append(p.Visual).Append("\",\"el\":\"").Append(ElementUtil.Key(p.Damage.Element)).Append("\",\"x\":").Append(F(p.Pos.X))
                  .Append(",\"y\":").Append(F(p.Pos.Y)).Append(",\"dx\":").Append(F(p.Dir.X)).Append(",\"dy\":").Append(F(p.Dir.Y)).Append('}');
            }
            sb.Append("],\"strikes\":[");
            for (int i = 0; i < b.Strikes.Count; i++)
            {
                DelayedStrike s = b.Strikes[i];
                if (i > 0) sb.Append(',');
                sb.Append("{\"kind\":\"").Append(s.Kind).Append("\",\"x\":").Append(F(s.Pos.X)).Append(",\"y\":").Append(F(s.Pos.Y)).Append(",\"r\":").Append(F(s.Radius)).Append('}');
            }
            sb.Append("]}");
            File.WriteAllText(path, sb.ToString());
            System.Console.WriteLine("snapshot -> " + path + " (enemies " + b.Enemies.Count + ")");
        }
    }
}
