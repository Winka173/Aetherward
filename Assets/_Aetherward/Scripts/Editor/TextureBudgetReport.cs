using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Profiling;

namespace Aetherward.EditorTools
{
    /// <summary>
    /// What the art actually costs once Unity has imported it: per texture the imported format, size, mip count and
    /// runtime memory for the active build target, plus totals per category. Batch:
    ///   Unity -batchmode -quit -executeMethod Aetherward.EditorTools.TextureBudgetReport.Run
    /// Writes Reports/ArtQuality/texture_memory.csv and texture_memory.md.
    /// </summary>
    public static class TextureBudgetReport
    {
        private const string Root = "Assets/_Aetherward/Resources/Art/";

        [MenuItem("Aetherward/Reports/Texture Memory", priority = 200)]
        public static void Run()
        {
            var rows = new List<string> { "path,format,width,height,mips,runtimeKB,compression,platformFormat" };
            var byCat = new Dictionary<string, long>();
            string target = EditorUserBuildSettings.activeBuildTarget.ToString();
            foreach (string guid in AssetDatabase.FindAssets("t:Texture2D", new[] { Root.TrimEnd('/') }))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
                var imp = AssetImporter.GetAtPath(path) as TextureImporter;
                if (tex == null || imp == null) continue;
                long bytes = Profiler.GetRuntimeMemorySizeLong(tex);
                TextureImporterPlatformSettings ps = imp.GetPlatformTextureSettings(target == "StandaloneWindows64" ? "Standalone" : target);
                rows.Add(string.Join(",", path, tex.format, tex.width, tex.height, tex.mipmapCount, bytes / 1024, imp.textureCompression,
                    ps.overridden ? ps.format.ToString() : "auto"));
                string cat = path.Substring(Root.Length).Split('/')[0];
                byCat[cat] = (byCat.TryGetValue(cat, out long v) ? v : 0) + bytes;
            }
            Directory.CreateDirectory("Reports/ArtQuality");
            File.WriteAllLines("Reports/ArtQuality/texture_memory.csv", rows);
            var md = new List<string> { "# Texture memory (imported, " + target + ")", "", "| Category | MB |", "|---|---|" };
            md.AddRange(byCat.OrderByDescending(kv => kv.Value).Select(kv => "| " + kv.Key + " | " + (kv.Value / 1048576f).ToString("0.0") + " |"));
            md.Add("| **total** | " + (byCat.Values.Sum() / 1048576f).ToString("0.0") + " |");
            File.WriteAllLines("Reports/ArtQuality/texture_memory.md", md);
            Debug.Log("TextureBudgetReport: " + (rows.Count - 1) + " textures, " + (byCat.Values.Sum() / 1048576f).ToString("0.0") + " MB");
        }
    }
}
