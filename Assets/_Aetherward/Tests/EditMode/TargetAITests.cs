using Aetherward.Sim.Combat;
using Aetherward.Sim.Content;
using Aetherward.Sim.Core;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>Phase 2 utility targeting: tactics as soft weights, hysteresis, reach, determinism, inspector data.</summary>
    public class TargetAITests
    {
        private static Battle Make(TeamTactic tactic, params (string, int)[] heroes)
        {
            BattleSetup s = TestContent.Setup(1, 3, heroes);
            s.Wave = new WaveDef { Number = 6, TimeLimit = 999f };
            s.Tactic = tactic;
            return new Battle(s);
        }

        private static EnemyUnit Spawn(Battle b, string id, Vec2 at, int lane = 0)
        {
            EnemyUnit e = b.SpawnEnemy(b.Content.Enemies[id], lane, false, null, at);
            e.Speed = 0f;
            e.MaxHp = e.Hp = 5000f;
            return e;
        }

        [Test]
        public void FocusBossPrefersTheBossProtectCrystalPrefersTheLeaker()
        {
            foreach (TeamTactic t in new[] { TeamTactic.FocusBoss, TeamTactic.ProtectCrystal })
            {
                Battle b = Make(t, ("sylph", 4));
                HeroUnit h = b.Heroes[0];
                EnemyUnit boss = Spawn(b, "siegebreaker_golem", h.Pos + new Vec2(3.5f, 1.2f));
                EnemyUnit leaker = Spawn(b, "grunt", new Vec2(2.4f, 0.2f));
                b.Tick();
                EnemyUnit pick = b.SelectTarget(h);
                Assert.AreSame(t == TeamTactic.FocusBoss ? boss : leaker, pick, t.ToString());
                Assert.AreEqual(pick.Uid, h.Decision.TargetUid);
                Assert.Greater(h.Decision.Candidates, 1);
            }
        }

        [Test]
        public void ElementalChainPrefersReactionTargets()
        {
            Battle b = Make(TeamTactic.ElementalChain, ("ignis", 4));
            HeroUnit h = b.Heroes[0];
            EnemyUnit plain = Spawn(b, "grunt", h.Pos + new Vec2(2.0f, 0.5f));
            EnemyUnit wet = Spawn(b, "grunt", h.Pos + new Vec2(2.6f, -0.6f));
            b.Tick();
            System.Array.Clear(plain.Aura, 0, plain.Aura.Length);
            System.Array.Clear(wet.Aura, 0, wet.Aura.Length);
            wet.Aura[(int)Element.Water] = 1f;
            h.Target = null; // preference only (hysteresis has its own test)
            Assert.AreSame(wet, b.SelectTarget(h));
            Assert.Greater(h.Decision.Parts[3], 0f, "reaction component recorded for the inspector");
        }

        [Test]
        public void HysteresisPreventsJitterButYieldsToAClearlyBetterTarget()
        {
            Battle b = Make(TeamTactic.Balanced, ("sylph", 4));
            HeroUnit h = b.Heroes[0];
            EnemyUnit a = Spawn(b, "grunt", h.Pos + new Vec2(2.5f, 0.3f));
            EnemyUnit c = Spawn(b, "grunt", h.Pos + new Vec2(2.5f, -0.3f));
            b.Tick();
            h.Target = b.SelectTarget(h);
            EnemyUnit first = h.Target;
            for (int i = 0; i < 10; i++) Assert.AreSame(first, b.SelectTarget(h), "near-equal candidates do not flip-flop");
            EnemyUnit boss = Spawn(b, "siegebreaker_golem", h.Pos + new Vec2(2.0f, 0f));
            b.Tick();
            b.Setup.Tactic = TeamTactic.FocusBoss;
            Assert.AreSame(boss, b.SelectTarget(h), "a clearly better target wins");
        }

        [Test]
        public void NeverTargetsOutOfReachAndExplainsNoTarget()
        {
            Battle b = Make(TeamTactic.Balanced, ("terra", 0));
            HeroUnit h = b.Heroes[0];
            Spawn(b, "grunt", new Vec2(11f, 6f));
            b.Tick();
            Assert.IsNull(b.SelectTarget(h));
            Assert.AreEqual("no target in reach", h.Decision.Reason);
        }

        [Test]
        public void UtilityTargetingIsDeterministicInFullWaves()
        {
            int Play()
            {
                BattleSetup s = TestContent.Setup(12, 8, ("terra", 0), ("ignis", 4), ("sylph", 8), ("volt", 6), ("marina", 2), ("kael", 5));
                foreach (HeroLoadout l in s.Heroes) l.Level = 4;
                s.Tactic = TeamTactic.ProtectCrystal;
                Battle b = new Battle(s);
                b.RunToEnd();
                return b.Stats.Kills * 1000 + (int)b.Crystal.Hp;
            }
            Assert.AreEqual(Play(), Play());
        }
    }
}
