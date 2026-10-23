using Aetherward.Sim.Run;

namespace Aetherward.Sim.Content
{
    /// <summary>Localized wording for Battle Insights codes; confidence decides how certain the sentence sounds.</summary>
    public static class InsightText
    {
        public static string Describe(Localization l, ContentDatabase db, string code)
        {
            var (kind, a, conf) = BattleInsights.Parse(code);
            string body;
            switch (kind)
            {
                case "threat":
                    body = l.Format("insight.threat", db.Enemies.TryGetValue(a[0], out EnemyDef e) ? l.Get(e.NameKey) : a[0], a[1]);
                    break;
                case "gate":
                case "lane":
                    int lane = int.Parse(a[0], System.Globalization.CultureInfo.InvariantCulture);
                    string laneName = lane >= 0 && lane < db.Arena.Lanes.Count ? l.Get(db.Arena.Lanes[lane].NameKey) : a[0];
                    body = l.Format(kind == "gate" ? "insight.gate" : a[2] == "-1" ? "insight.lane_nocov" : "insight.lane", laneName, a[1], a[2]);
                    break;
                case "tank":
                    body = l.Format("insight.tank", db.Heroes.TryGetValue(a[0], out HeroDef h) ? l.Get(h.NameKey) : a[0], a[1], a[2]);
                    break;
                case "timeout":
                    body = l.Format("insight.timeout", a[0]);
                    break;
                default:
                    body = l.Get("insight.no_evidence");
                    break;
            }
            return conf == "high" ? body : l.Get("insight.conf." + conf) + " " + body;
        }
    }
}
