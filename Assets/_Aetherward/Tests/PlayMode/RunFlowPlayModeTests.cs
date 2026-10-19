using System.Collections;
using Aetherward.Game;
using Aetherward.Sim.Run;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Aetherward.Tests
{
    /// <summary>
    /// End-to-end smoke test inside the Unity player loop: boot -> menu -> new run -> place hero ->
    /// fight wave 1 at 2x -> reward -> next prepare -> abandon -> results -> menu.
    /// Requires the Unity Test Framework package (Window > Package Manager).
    /// </summary>
    public class RunFlowPlayModeTests
    {
        private static IEnumerator WaitFor(System.Func<bool> cond, float timeout)
        {
            float t = 0f;
            while (!cond() && t < timeout)
            {
                t += Time.unscaledDeltaTime;
                yield return null;
            }
            Assert.IsTrue(cond(), "condition not met within " + timeout + "s");
        }

        [UnityTest]
        public IEnumerator BootToBattleToResults()
        {
            SceneManager.LoadScene("Boot");
            yield return WaitFor(() => GameRoot.Instance != null && GameRoot.Instance.Current == AppScreen.MainMenu, 10f);
            Assert.IsTrue(App.Ready);

            App.ClearRun();
            App.Run = RunController.NewRun(App.Content, 12345, new[] { "ignis", "terra" }, 0, App.Meta.ToRunUnlocks());
            GameRoot.Instance.GoTo(AppScreen.Battle);
            yield return WaitFor(() => GameRoot.Instance.Current == AppScreen.Battle, 10f);
            RunController rc = App.Run;
            Assert.AreEqual(RunPhase.Prepare, rc.State.Phase);
            Assert.IsTrue(rc.PlaceHero(rc.State.Heroes[0].Uid, 5), "placement command works in play mode");

            var battle = Object.FindObjectOfType<BattleController>();
            Assert.IsNotNull(battle);
            battle.StartWave();
            Assert.AreEqual(RunPhase.Battle, rc.State.Phase);
            Time.timeScale = 1f;
            yield return WaitFor(() => rc.State.Phase != RunPhase.Battle, 120f);
            Assert.AreEqual(RunPhase.Reward, rc.State.Phase, "wave 1 should be cleared by two heroes");
            Assert.IsTrue(rc.Choose(0));
            Assert.AreEqual(RunPhase.Prepare, rc.State.Phase);
            Assert.AreEqual(2, rc.State.Wave);

            rc.Abandon();
            yield return WaitFor(() => GameRoot.Instance.Current == AppScreen.Results, 10f);
            Assert.IsNotNull(App.LastResults);
            GameRoot.Instance.GoTo(AppScreen.MainMenu);
            yield return WaitFor(() => GameRoot.Instance.Current == AppScreen.MainMenu, 10f);
        }
    }
}
