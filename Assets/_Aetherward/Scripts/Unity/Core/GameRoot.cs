using System;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Aetherward.Game
{
    public enum AppScreen
    {
        Boot,
        MainMenu,
        Battle,
        Results
    }

    /// <summary>
    /// Persistent root created before the first scene loads. Initializes services and attaches the
    /// right screen controller for the active scene. Works with the four authored scenes
    /// (Boot, MainMenu, Battle, Results) and, as a fallback, inside any empty scene.
    /// </summary>
    public sealed class GameRoot : MonoBehaviour
    {
        public static GameRoot Instance { get; private set; }
        public static readonly string[] SceneNames = { "Boot", "MainMenu", "Battle", "Results" };

        private MonoBehaviour _controller;
        public AppScreen Current { get; private set; }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        private static void Bootstrap()
        {
            if (Instance != null) return;
            var go = new GameObject("GameRoot");
            DontDestroyOnLoad(go);
            go.AddComponent<GameRoot>();
        }

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
            Input.multiTouchEnabled = true;
            Screen.sleepTimeout = SleepTimeout.NeverSleep;
            App.Initialize();
            App.Audio = AudioService.Create(transform);
            App.ApplySettings();
            SceneManager.sceneLoaded += OnSceneLoaded;
        }

        private void Start()
        {
            AttachFor(SceneManager.GetActiveScene().name);
        }

        private void OnDestroy()
        {
            SceneManager.sceneLoaded -= OnSceneLoaded;
        }

        private void OnSceneLoaded(Scene scene, LoadSceneMode mode)
        {
            if (mode == LoadSceneMode.Single) AttachFor(scene.name);
        }

        private void AttachFor(string sceneName)
        {
            AppScreen screen;
            switch (sceneName)
            {
                case "MainMenu": screen = AppScreen.MainMenu; break;
                case "Battle": screen = AppScreen.Battle; break;
                case "Results": screen = AppScreen.Results; break;
                default: screen = AppScreen.Boot; break;
            }
            Attach(screen);
        }

        private void Attach(AppScreen screen)
        {
            if (_controller != null) Destroy(_controller.gameObject);
            Current = screen;
            var go = new GameObject(screen + "Controller");
            switch (screen)
            {
                case AppScreen.Boot: _controller = go.AddComponent<BootController>(); break;
                case AppScreen.MainMenu: _controller = go.AddComponent<MenuController>(); break;
                case AppScreen.Battle: _controller = go.AddComponent<BattleController>(); break;
                case AppScreen.Results: _controller = go.AddComponent<ResultsController>(); break;
            }
        }

        /// <summary>Loads the scene for a screen if it is in the build, else swaps controllers in place.</summary>
        public void GoTo(AppScreen screen)
        {
            string name = SceneNames[(int)screen];
            if (Application.CanStreamedLevelBeLoaded(name)) SceneManager.LoadScene(name);
            else Attach(screen);
        }

        private void OnApplicationPause(bool paused)
        {
            if (paused) SaveAll();
        }

        private void OnApplicationQuit()
        {
            SaveAll();
        }

        private static void SaveAll()
        {
            try
            {
                if (App.Ready)
                {
                    App.SaveRun();
                    App.SaveMeta();
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning("Save on pause failed: " + e.Message);
            }
        }

        /// <summary>Shared orthographic camera setup that fits the arena on any aspect ratio.</summary>
        public static Camera EnsureCamera(Color background)
        {
            Camera cam = Camera.main;
            if (cam == null)
            {
                var go = new GameObject("Main Camera");
                go.tag = "MainCamera";
                cam = go.AddComponent<Camera>();
                go.AddComponent<AudioListener>();
            }
            cam.orthographic = true;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = background;
            cam.transform.position = new Vector3(0, 0, -10);
            cam.nearClipPlane = 0.1f;
            cam.farClipPlane = 100f;
            return cam;
        }
    }

    /// <summary>Splash: loads content/saves (already done by GameRoot) and moves to the main menu.</summary>
    public sealed class BootController : MonoBehaviour
    {
        private float _t;

        private void Start()
        {
            GameRoot.EnsureCamera(new Color(0.08f, 0.09f, 0.18f));
            App.Audio.PlayMusic("menu_loop");
        }

        private void Update()
        {
            _t += Time.unscaledDeltaTime;
            if (_t > 1.4f || (_t > 0.4f && Input.GetMouseButtonDown(0))) GameRoot.Instance.GoTo(AppScreen.MainMenu);
        }

        private void OnGUI()
        {
            Ui.Begin();
            Ui.DrawRect(0, 0, Ui.W, Ui.H, new Color(0.08f, 0.09f, 0.18f));
            Ui.Icon(Ui.W / 2 - 360, Ui.H / 2 - 260, 720, 225, Art.Tex("UI/title_emblem"));
            Ui.Label(0, Ui.H / 2 - 40, Ui.W, 120, App.Loc.Get("game.title"), 92, Ui.Gold, TextAnchor.MiddleCenter, true);
            Ui.Label(0, Ui.H / 2 + 80, Ui.W, 50, App.Loc.Get("game.tagline"), 30, Ui.Muted, TextAnchor.MiddleCenter);
            Ui.Bar(Ui.W / 2 - 300, Ui.H - 160, 600, 28, Mathf.Clamp01(_t / 1.4f), Ui.Teal);
            Ui.Label(0, Ui.H - 120, Ui.W, 40, App.Loc.Get("common.loading"), 24, Ui.Muted, TextAnchor.MiddleCenter);
        }
    }
}
