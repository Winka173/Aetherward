using System;
using System.Collections.Generic;
using System.IO;
using Aetherward.Sim.Content;
using Aetherward.Sim.Meta;
using Aetherward.Sim.Run;
using UnityEngine;

namespace Aetherward.Game
{
    /// <summary>
    /// Process-wide services, created once by <see cref="GameRoot"/>. Presentation code reads these;
    /// gameplay rules live in the simulation assembly.
    /// </summary>
    public static class App
    {
        public const string Version = "0.1.0";

        public static ContentDatabase Content { get; private set; }
        public static Localization Loc { get; private set; }
        public static EffectDescriber Fx { get; private set; }
        public static SaveService Saves { get; private set; }
        public static SettingsModel Settings { get; private set; }
        public static MetaProfile Meta { get; private set; }
        public static AudioService Audio { get; set; }
        public static bool SaveWasReset { get; private set; }
        public static string LoadError { get; private set; }
        public static bool Ready => Content != null;

        /// <summary>The run being played (null in menus). Restored from save on Continue.</summary>
        public static RunController Run { get; set; }
        public static RunResults LastResults { get; set; }
        public static List<string> LastUnlocks { get; set; } = new List<string>();

        public static void Initialize()
        {
            if (Ready) return;
            try
            {
                Content = ContentDatabase.Load(name =>
                {
                    TextAsset t = Resources.Load<TextAsset>("Content/" + name);
                    return t != null ? t.text : null;
                });
            }
            catch (Exception e)
            {
                LoadError = e.Message;
                Debug.LogError("Aetherward content failed to load: " + e);
                throw;
            }
            Saves = new SaveService(new FileSaveStorage(Application.persistentDataPath));
            Settings = Saves.LoadSettings();
            Meta = Saves.LoadMeta(Content);
            SaveWasReset = Saves.LastError != null && Meta.TotalRuns == 0;
            if (Saves.LastError != null) Debug.LogWarning("Save fallback used: " + Saves.LastError);
            if (string.IsNullOrEmpty(Settings.Language) || Array.IndexOf(Localization.Supported, Settings.Language) < 0)
                Settings.Language = Application.systemLanguage == SystemLanguage.Vietnamese ? "vi" : "en";
            Loc = new Localization(Content, Settings.Language);
            Fx = new EffectDescriber(Content, Loc);
            ApplySettings();
        }

        public static void SetLanguage(string lang)
        {
            Settings.Language = lang;
            Loc.SetLanguage(lang);
            SaveSettings();
        }

        public static void ApplySettings()
        {
            QualitySettings.vSyncCount = 0;
            Application.targetFrameRate = Settings.TargetFps;
            if (Audio != null) Audio.ApplyVolumes();
        }

        public static void SaveSettings()
        {
            Saves.SaveSettings(Settings);
            ApplySettings();
        }

        public static void SaveMeta() => Saves.SaveMeta(Meta);

        public static void SaveRun()
        {
            if (Run != null && !Run.State.Finished) Saves.SaveRun(Run.State);
        }

        public static bool HasSavedRun => Saves.LoadRun(Content) != null;

        public static RunController ResumeRun()
        {
            RunState s = Saves.LoadRun(Content);
            if (s == null) return null;
            // A run saved mid-battle resumes at that wave's preparation (spec: wave boundary).
            if (s.Phase == RunPhase.Battle) s.Phase = RunPhase.Prepare;
            Run = new RunController(Content, s, Meta.ToRunUnlocks());
            return Run;
        }

        public static void ClearRun()
        {
            Saves.Delete("run");
            Run = null;
        }
    }

    /// <summary>Atomic file storage: write temp, replace target (keeping the previous copy as .bak).</summary>
    public sealed class FileSaveStorage : ISaveStorage
    {
        private readonly string _dir;

        public FileSaveStorage(string dir)
        {
            _dir = Path.Combine(dir, "saves");
            Directory.CreateDirectory(_dir);
        }

        private string PathFor(string key) => Path.Combine(_dir, key + ".json");

        public string Read(string key)
        {
            string p = PathFor(key);
            try
            {
                return File.Exists(p) ? File.ReadAllText(p) : null;
            }
            catch (IOException)
            {
                return null;
            }
        }

        public void Write(string key, string text)
        {
            string p = PathFor(key);
            string tmp = p + ".tmp";
            try
            {
                File.WriteAllText(tmp, text);
                // Atomic swap where the platform supports it; the previous file is never deleted before the new one exists.
                if (File.Exists(p)) File.Replace(tmp, p, null);
                else File.Move(tmp, p);
            }
            catch (IOException e)
            {
                Debug.LogError("Save failed for " + key + ": " + e.Message);
            }
        }

        public void Delete(string key)
        {
            string p = PathFor(key);
            if (File.Exists(p)) File.Delete(p);
        }
    }

    /// <summary>Resources-backed sprite/texture cache. Missing art logs once and returns null.</summary>
    public static class Art
    {
        private static readonly Dictionary<string, Sprite> Sprites = new Dictionary<string, Sprite>();
        private static readonly HashSet<string> Missing = new HashSet<string>();

        public static Sprite Sprite(string path)
        {
            if (Sprites.TryGetValue(path, out Sprite s)) return s;
            s = Resources.Load<Sprite>("Art/" + path);
            if (s == null && Missing.Add(path)) Debug.LogWarning("Missing sprite Art/" + path);
            Sprites[path] = s;
            return s;
        }

        public static Texture2D Tex(string path)
        {
            Sprite s = Sprite(path);
            return s != null ? s.texture : null;
        }

        public static Texture2D Portrait(string heroId) => Tex("Portraits/" + heroId);
        public static Texture2D ElementIcon(Element e) => Tex("Icons/element_" + ElementUtil.Key(e));
        public static Texture2D Icon(string name) => Tex("Icons/ui_" + name);
    }
}
