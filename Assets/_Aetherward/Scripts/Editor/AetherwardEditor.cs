using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using Aetherward.Game;
using Aetherward.Sim.Content;
using Aetherward.Sim.Run;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Aetherward.EditorTools
{
    /// <summary>Editor menu: validation, scene rebuild, balance sampling, save reset.</summary>
    public static class AetherwardMenu
    {
        public const string ScenesFolder = "Assets/_Aetherward/Scenes";
        private static readonly string[] Scenes = { "Boot", "MainMenu", "Battle", "Results" };

        public static ContentDatabase LoadContent()
        {
            return ContentDatabase.Load(name =>
            {
                string path = "Assets/_Aetherward/Resources/Content/" + name + ".json";
                return File.Exists(path) ? File.ReadAllText(path) : null;
            });
        }

        [MenuItem("Aetherward/Validate Content and Art", priority = 1)]
        public static void ValidateMenu()
        {
            List<string> errors = Validate();
            if (errors.Count == 0)
            {
                Debug.Log("Aetherward validation passed: content, localization (en/vi) and art references are consistent.");
                EditorUtility.DisplayDialog("Aetherward", "Validation passed.", "OK");
            }
            else
            {
                Debug.LogError("Aetherward validation found " + errors.Count + " problem(s):\n" + string.Join("\n", errors));
                EditorUtility.DisplayDialog("Aetherward", errors.Count + " problem(s). See Console.", "OK");
            }
        }

        /// <summary>Content rules + every sprite the game loads by convention must exist with sprite import.</summary>
        public static List<string> Validate()
        {
            ContentDatabase db = LoadContent();
            List<string> errors = ContentValidator.Validate(db);
            void Need(string path)
            {
                string asset = "Assets/_Aetherward/Resources/Art/" + path + ".png";
                if (!File.Exists(asset)) { errors.Add("missing art " + asset); return; }
                var importer = AssetImporter.GetAtPath(asset) as TextureImporter;
                if (importer != null && importer.textureType != TextureImporterType.Sprite) errors.Add("not imported as sprite: " + asset);
            }
            var seen = new HashSet<string>();
            foreach (string path in AssetManifest.RequiredArt(db))
                if (seen.Add(path)) Need(path);
            foreach (string clip in AssetManifest.RequiredAudio(db))
                if (seen.Add(clip) && !File.Exists("Assets/_Aetherward/Resources/Audio/" + clip + ".ogg") && !File.Exists("Assets/_Aetherward/Resources/Audio/" + clip + ".wav"))
                    errors.Add("missing audio " + clip);
            return errors;
        }

        [MenuItem("Aetherward/Rebuild Scenes", priority = 20)]
        public static void RebuildScenes()
        {
            Directory.CreateDirectory(ScenesFolder);
            var entries = new List<EditorBuildSettingsScene>();
            foreach (string name in Scenes)
            {
                Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
                var marker = new GameObject(name + "SceneMarker");
                SceneManager.MoveGameObjectToScene(marker, scene);
                string path = ScenesFolder + "/" + name + ".unity";
                EditorSceneManager.SaveScene(scene, path);
                entries.Add(new EditorBuildSettingsScene(path, true));
            }
            EditorBuildSettings.scenes = entries.ToArray();
            EditorSceneManager.OpenScene(ScenesFolder + "/Boot.unity");
            Debug.Log("Aetherward scenes rebuilt: " + string.Join(", ", Scenes));
        }

        [MenuItem("Aetherward/Play From Boot", priority = 21)]
        public static void PlayFromBoot()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            EditorSceneManager.OpenScene(ScenesFolder + "/Boot.unity");
            EditorApplication.isPlaying = true;
        }

        [MenuItem("Aetherward/Simulate 6 Archetype Runs (headless)", priority = 40)]
        public static void SimulateRuns()
        {
            ContentDatabase db = LoadContent();
            var sb = new StringBuilder("Aetherward headless simulation (seed 4242):\n");
            foreach (Strategy st in Strategy.Archetypes)
            {
                RunController rc = RunController.NewRun(db, 4242, st.Starters, 0, RunUnlocks.Everything(db));
                bool ok = new AutoPilot(rc, st).PlayToEnd();
                RunResults r = RunResults.Build(rc);
                sb.AppendLine(st.Name + ": " + (r.Victory ? "VICTORY" : "defeat at wave " + rc.State.Wave) + ", reactions " + r.TotalReactions +
                              ", active " + (rc.State.ActiveSeconds / 60f).ToString("0.0") + " min" + (ok ? "" : " (STUCK)"));
            }
            Debug.Log(sb.ToString());
        }

        [MenuItem("Aetherward/Delete Local Save Data", priority = 60)]
        public static void DeleteSaves()
        {
            string dir = Path.Combine(Application.persistentDataPath, "saves");
            if (!Directory.Exists(dir)) return;
            if (!EditorUtility.DisplayDialog("Aetherward", "Delete all local Aetherward saves (profile, settings, run)?", "Delete", "Cancel")) return;
            Directory.Delete(dir, true);
            Debug.Log("Deleted " + dir);
        }
    }

    /// <summary>
    /// Re-applies sprite import settings written by Tools/AssetGen (pivot, PPU, 9-slice border) so
    /// regenerated PNGs always import consistently, even if a .meta was lost.
    /// </summary>
    public sealed class AetherwardTexturePostprocessor : AssetPostprocessor
    {
        private const string Root = "Assets/_Aetherward/Resources/Art/";
        private static Dictionary<string, float[]> _settings;

        private static Dictionary<string, float[]> Settings
        {
            get
            {
                if (_settings != null) return _settings;
                _settings = new Dictionary<string, float[]>();
                const string path = "Tools/AssetGen/import_settings.json";
                if (!File.Exists(path)) return _settings;
                Sim.Core.JsonNode root = Sim.Core.JsonNode.Parse(File.ReadAllText(path));
                foreach (string key in root.Keys)
                {
                    Sim.Core.JsonNode n = root[key];
                    var piv = n["pivot"];
                    var b = n["border"];
                    _settings[key] = new[] { n.Float("ppu", 100f), piv[0].AsFloat(0.5f), piv[1].AsFloat(0.5f), b[0].AsFloat(), b[1].AsFloat(), b[2].AsFloat(), b[3].AsFloat() };
                }
                return _settings;
            }
        }

        private void OnPreprocessTexture()
        {
            if (!assetPath.StartsWith(Root)) return;
            var importer = (TextureImporter)assetImporter;
            importer.textureType = TextureImporterType.Sprite;
            importer.spriteImportMode = SpriteImportMode.Single;
            // World sprites are drawn 1.5-3x smaller than authored (a 400 px hero is ~144 px at 1080p, ~192 px at 1440p):
            // mipmaps + trilinear keep them clean instead of shimmering. 9-slice UI is drawn near native size.
            bool ui = assetPath.StartsWith(Root + "UI/");
            importer.mipmapEnabled = !ui;
            importer.mipmapFilter = TextureImporterMipFilter.KaiserFilter;
            importer.mipMapsPreserveCoverage = false;
            importer.alphaIsTransparency = true;
            importer.filterMode = ui ? FilterMode.Bilinear : FilterMode.Trilinear;
            importer.anisoLevel = ui ? 1 : 2;
            importer.wrapMode = TextureWrapMode.Clamp;
            if (!Settings.TryGetValue(assetPath, out float[] s)) return;
            var ts = new TextureImporterSettings();
            importer.ReadTextureSettings(ts);
            ts.spritePixelsPerUnit = s[0];
            ts.spriteAlignment = (int)SpriteAlignment.Custom;
            ts.spritePivot = new Vector2(s[1], s[2]);
            ts.spriteBorder = new Vector4(s[3], s[4], s[5], s[6]);
            ts.spriteMeshType = s[3] + s[4] + s[5] + s[6] > 0 ? SpriteMeshType.FullRect : SpriteMeshType.Tight;
            importer.SetTextureSettings(ts);
            if (assetPath.Contains("arena_background") || assetPath.Contains("/World/bg_")) importer.maxTextureSize = 4096;   // all battlefields, not only the default
        }
    }
}
