using UnityEditor;
using UnityEngine;

namespace Aetherward.EditorTools
{
    /// <summary>Diagnostic: which sprite sizes Unity compresses. Batch: -executeMethod Aetherward.EditorTools.TextureCompressionProbe.Run</summary>
    public static class TextureCompressionProbe
    {
        public static void Run()
        {
            AssetDatabase.Refresh();
            foreach (int n in new[] { 400, 512, 404, 384 })
            {
                string path = "Assets/ProbeTmp/p" + n + ".png";
                var imp = (TextureImporter)AssetImporter.GetAtPath(path);
                foreach (bool sprite in new[] { false, true })
                {
                    imp.textureType = sprite ? TextureImporterType.Sprite : TextureImporterType.Default;
                    imp.mipmapEnabled = true;
                    imp.textureCompression = TextureImporterCompression.Compressed;
                    imp.SaveAndReimport();
                    var t = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
                    Debug.Log("PROBE " + n + " sprite=" + sprite + " -> " + t.format + " mips " + t.mipmapCount);
                }
            }
            Debug.Log("PROBE compressOnImport=" + EditorPrefs.GetBool("CompressAssetsOnImport", true) + " " + EditorSettings.assetPipelineMode);
        }
    }
}
