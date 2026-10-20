using System;
using System.Linq;
using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>Dynamic party: heroes leave their start nodes, take role posts and fight out on the lanes.</summary>
    public class DynamicPartyTests
    {
        private static readonly (string, int)[] Party =
        {
            ("glacius", 0), ("cinder", 1), ("ignis", 4), ("veyra", 5), ("raiden", 6), ("marina", 2)
        };

        private static Battle Run(PartyStance stance, float seconds, Action<Battle> each = null)
        {
            BattleSetup s = TestContent.Setup(12, 21, Party);
            s.Stance = stance;
            var b = new Battle(s);
            for (int t = 0; t < seconds * 30 && b.Outcome == BattleOutcome.Running; t++)
            {
                b.Tick();
                b.Journal.Clear();
                each?.Invoke(b);
            }
            return b;
        }

        private static float MeanDistance(Battle b, Func<HeroUnit, bool> who) =>
            b.Heroes.Where(h => h.Alive && who(h)).Select(h => Vec2.Distance(h.Pos, b.Crystal.Pos)).DefaultIfEmpty(0f).Average();

        [Test]
        public void FrontlinersFightOutOnTheLanesAndStancesSetTheDistance()
        {
            float def = 0f, agg = 0f;
            int n = 0;
            Run(PartyStance.Defensive, 20f, b => { if (b.TickCount % 15 == 0) { def += MeanDistance(b, h => h.Role == HeroRole.Guardian || h.Role == HeroRole.Bruiser); n++; } });
            def /= Math.Max(1, n);
            n = 0;
            Run(PartyStance.Aggressive, 20f, b => { if (b.TickCount % 15 == 0) { agg += MeanDistance(b, h => h.Role == HeroRole.Guardian || h.Role == HeroRole.Bruiser); n++; } });
            agg /= Math.Max(1, n);
            TestContext.WriteLine($"frontline mean distance from the Crystal: defensive {def:0.00}, aggressive {agg:0.00}");
            Assert.Greater(def, 2.2f, "defensive frontliners still stand off the Crystal");
            Assert.Greater(agg, def + 0.8f, "aggressive pushes clearly further out (time-averaged, incl. chases and rescues)");
        }

        [Test]
        public void SupportsStayBehindTheFrontline()
        {
            float front = 0f, support = 0f;
            Run(PartyStance.Balanced, 20f, b =>
            {
                if (b.TickCount % 15 != 0) return;
                front += MeanDistance(b, h => h.Role == HeroRole.Guardian || h.Role == HeroRole.Bruiser);
                support += MeanDistance(b, h => h.Role == HeroRole.Healer || h.Role == HeroRole.Support);
            });
            Assert.Less(support, front, "the healer keeps behind the tanks");
        }

        [Test]
        public void PartyIsDeterministic()
        {
            Battle a = Run(PartyStance.Balanced, 15f), c = Run(PartyStance.Balanced, 15f);
            for (int i = 0; i < a.Heroes.Count; i++)
                Assert.AreEqual(a.Heroes[i].Pos.X, c.Heroes[i].Pos.X, 1e-5f);
        }
    }
}
