using System.Collections.Generic;
using System.IO;
using Aetherward.Sim.Content;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>Content may not reference art or audio that the generators have not produced.</summary>
    public class AssetContractTests
    {
        private static string Resources => Path.GetDirectoryName(TestContent.ContentDirectory);

        [Test]
        public void EveryRequiredSpriteExists()
        {
            var missing = new List<string>();
            foreach (string path in AssetManifest.RequiredArt(TestContent.Db))
                if (!File.Exists(Path.Combine(Resources, "Art", path + ".png"))) missing.Add(path);
            Assert.IsEmpty(missing, "missing art:\n" + string.Join("\n", missing));
        }

        [Test]
        public void EveryRequiredSoundExists()
        {
            var missing = new List<string>();
            foreach (string clip in AssetManifest.RequiredAudio(TestContent.Db))
            {
                string b = Path.Combine(Resources, "Audio", clip);
                if (!File.Exists(b + ".ogg") && !File.Exists(b + ".wav")) missing.Add(clip);
            }
            Assert.IsEmpty(missing, "missing audio:\n" + string.Join("\n", missing));
        }
    }
}
