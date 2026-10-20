using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using Aetherward.Sim.Content;
using Aetherward.Sim.Run;
using UnityEngine;

namespace Aetherward.Game
{
    /// <summary>
    /// Command line of a capture run: <c>-awCapture spec.json</c> (optionally <c>-awArtOverride dir</c>).
    /// Without the flag nothing here does anything.
    /// </summary>
    public static class CaptureArgs
    {
        private static bool _parsed;
        private static string _spec, _override;

        public static bool Active { get { Parse(); return _spec != null; } }
        public static string SpecPath { get { Parse(); return _spec; } }
        public static string ArtOverride { get { Parse(); return _override; } }
        public static string SaveRoot => Path.Combine(Application.temporaryCachePath, "aw_capture_" + System.Diagnostics.Process.GetCurrentProcess().Id);

        private static void Parse()
        {
            if (_parsed) return;
            _parsed = true;
            string[] a = Environment.GetCommandLineArgs();
            for (int i = 0; i < a.Length - 1; i++)
            {
                if (a[i] == "-awCapture") _spec = a[i + 1];
                else if (a[i] == "-awArtOverride") _override = a[i + 1];
            }
        }
    }

    [Serializable]
    public sealed class CaptureSpec
    {
        [Serializable]
        public sealed class Hero
        {
            public string id;
            public int node = -1;
            public int level = 1;
            public string evolution;
        }

        [Serializable]
        public sealed class Group
        {
            public string enemy;
            public int count = 1;
            public int lane = -1;
            public float start;
            public float interval = 0.6f;
        }

        [Serializable]
        public sealed class Shot
        {
            public float t;          // seconds after the wave starts; negative = during preparation
            public string name;
        }

        public string label;
        public string commit;
        public ulong seed = 1;
        public string biome;
        public int wave = 10;
        public Hero[] heroes;
        public Group[] groups;
        public int[] lanes;
        public Shot[] shots;
        public string outDir;
    }

    /// <summary>
    /// Benchmark capture: plays a real run in the real Battle scene with a scripted roster and wave, saves
    /// ScreenCapture screenshots (world + IMGUI HUD) at the requested times, writes capture_info.json and quits.
    /// The custom wave replaces the content entry in memory only; saves go to a throwaway folder.
    /// </summary>
    public sealed class CaptureDirector : MonoBehaviour
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Boot()
        {
            if (!CaptureArgs.Active) return;
            Art.OverrideRoot = CaptureArgs.ArtOverride;
            Application.runInBackground = true;   // the player window may not keep focus while capturing
            var go = new GameObject("CaptureDirector");
            DontDestroyOnLoad(go);
            go.AddComponent<CaptureDirector>();
        }

        private readonly List<string> _written = new List<string>();

        private IEnumerator Start()
        {
            CaptureSpec spec = JsonUtility.FromJson<CaptureSpec>(File.ReadAllText(CaptureArgs.SpecPath));
            Directory.CreateDirectory(spec.outDir);
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!(App.Ready && GameRoot.Instance != null && GameRoot.Instance.Current == AppScreen.MainMenu))
            {
                if (Time.realtimeSinceStartup > timeout) { Fail("menu never became ready"); yield break; }
                yield return null;
            }
            App.Settings.PauseOnFocusLoss = false;   // throwaway capture profile only

            var ids = new List<string>();
            foreach (CaptureSpec.Hero h in spec.heroes) ids.Add(h.id);
            RunController rc = RunController.NewRun(App.Content, spec.seed, ids, 0, RunUnlocks.Everything(App.Content), spec.biome);
            for (int i = 0; i < spec.heroes.Length; i++)
            {
                HeroRunState h = rc.State.Heroes[i];
                h.Level = Mathf.Max(1, spec.heroes[i].level);
                if (spec.heroes[i].node >= 0) h.Node = spec.heroes[i].node;
                if (!string.IsNullOrEmpty(spec.heroes[i].evolution)) h.EvolutionId = spec.heroes[i].evolution;
            }
            rc.State.BlockedNode = -1;
            rc.State.Wave = spec.wave;
            InstallWave(spec);
            App.ClearRun();
            App.Run = rc;
            GameRoot.Instance.GoTo(AppScreen.Battle);
            timeout = Time.realtimeSinceStartup + 30f;
            BattleController battle = null;
            while (battle == null)
            {
                if (Time.realtimeSinceStartup > timeout) { Fail("battle scene never loaded"); yield break; }
                battle = FindFirstObjectByType<BattleController>();
                yield return null;
            }
            for (int i = 0; i < 30; i++) yield return null;   // let views, nodes and lane arrows settle

            var shots = new List<CaptureSpec.Shot>(spec.shots);
            shots.Sort((a, b) => a.t.CompareTo(b.t));
            int next = 0;
            while (next < shots.Count && shots[next].t < 0)
            {
                yield return Shoot(spec, shots[next++]);
            }
            battle.StartWave();
            Time.timeScale = 1f;
            float t0 = Time.time;
            while (next < shots.Count)
            {
                if (rc.State.Phase != RunPhase.Battle) { Debug.LogWarning("capture: wave ended before shot " + shots[next].name); break; }
                if (Time.time - t0 >= shots[next].t) yield return Shoot(spec, shots[next++]);
                else yield return null;
            }
            WriteInfo(spec, rc);
            Quit(0);
        }

        private static void InstallWave(CaptureSpec spec)
        {
            var w = new WaveDef { Number = spec.wave, TimeLimit = 600f, Gold = 0 };
            bool boss = false;
            foreach (CaptureSpec.Group g in spec.groups)
            {
                w.Groups.Add(new SpawnGroup { Enemy = g.enemy, Count = g.count, Lane = g.lane, Start = g.start, Interval = g.interval });
                if (App.Content.Enemies.TryGetValue(g.enemy, out EnemyDef d) && d.Boss) boss = true;
            }
            w.Boss = boss;
            w.Lanes.AddRange(spec.lanes);
            App.Content.Waves[spec.wave - 1] = w;
        }

        private IEnumerator Shoot(CaptureSpec spec, CaptureSpec.Shot shot)
        {
            string path = Path.Combine(spec.outDir, shot.name + ".png");
            yield return new WaitForEndOfFrame();
            ScreenCapture.CaptureScreenshot(path);
            for (int i = 0; i < 3; i++) yield return null;   // the capture is written at the end of a later frame
            _written.Add(Path.GetFileName(path));
            Debug.Log("capture: " + path);
        }

        private void WriteInfo(CaptureSpec spec, RunController rc)
        {
            var lines = new List<string>
            {
                "\"kind\": \"Unity player screenshot (real Battle scene, scripted roster and wave)\"",
                "\"label\": \"" + spec.label + "\"",
                "\"commit\": \"" + spec.commit + "\"",
                "\"unity\": \"" + Application.unityVersion + "\"",
                "\"platform\": \"" + Application.platform + "\"",
                "\"screen\": [" + Screen.width + ", " + Screen.height + "]",
                "\"artOverride\": \"" + (CaptureArgs.ArtOverride ?? "").Replace("\\", "/") + "\"",
                "\"overridesLoaded\": " + Art.OverridesLoaded,
                "\"wave\": " + spec.wave,
                "\"phaseAtEnd\": \"" + rc.State.Phase + "\"",
                "\"shots\": [\"" + string.Join("\", \"", _written) + "\"]"
            };
            File.WriteAllText(Path.Combine(spec.outDir, "capture_info.json"), "{\n  " + string.Join(",\n  ", lines) + "\n}\n");
        }

        private void Fail(string why)
        {
            Debug.LogError("capture failed: " + why);
            Quit(1);
        }

        private static void Quit(int code)
        {
#if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit(code);
#endif
        }
    }
}
