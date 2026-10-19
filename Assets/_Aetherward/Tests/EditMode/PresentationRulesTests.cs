using Aetherward.Sim.Meta;
using Aetherward.Sim.Presentation;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>Phase 7 readability/accessibility rules that are engine-free (visuals themselves are unverified).</summary>
    public class PresentationRulesTests
    {
        [Test]
        public void HitsOnOneTargetMergeInsideTheWindow()
        {
            var m = new DamageNumberMerger { Window = 0.3f };
            DamageNumberMerger.Result a = m.Add(7, 10f, false, 0f);
            DamageNumberMerger.Result b = m.Add(7, 15f, false, 0.2f);
            Assert.IsFalse(a.Merged);
            Assert.IsTrue(b.Merged);
            Assert.AreEqual(a.Slot, b.Slot);
            Assert.AreEqual(25f, b.Total, 1e-4f);
            Assert.IsFalse(m.Add(8, 5f, false, 0.2f).Merged, "different target gets its own number");
            Assert.IsFalse(m.Add(7, 5f, false, 0.6f).Merged, "window expired");
        }

        [Test]
        public void CritsKeepTheirOwnNumberAndPruneForgetsOldWindows()
        {
            var m = new DamageNumberMerger();
            m.Add(1, 10f, false, 0f);
            DamageNumberMerger.Result crit = m.Add(1, 50f, true, 0.05f);
            Assert.IsFalse(crit.Merged);
            Assert.AreEqual(50f, crit.Total);
            Assert.IsTrue(m.Add(1, 1f, false, 0.1f).Merged, "the crit did not steal the open window");
            m.Prune(5f);
            Assert.IsFalse(m.Add(1, 1f, false, 5.05f).Merged);
        }

        [Test]
        public void AccessibilitySettingsRoundTripAndClamp()
        {
            var saves = new SaveService(new MemoryStorage());
            saves.SaveSettings(new SettingsModel { FlashIntensity = 0.25f, PauseOnFocusLoss = false, BatterySaver = true });
            SettingsModel s = saves.LoadSettings();
            Assert.AreEqual(0.25f, s.FlashIntensity, 1e-3f);
            Assert.IsFalse(s.PauseOnFocusLoss);
            Assert.IsTrue(s.BatterySaver);
            Assert.AreEqual(1f, new SettingsModel().FlashIntensity);
            Assert.IsTrue(new SettingsModel().PauseOnFocusLoss);
        }
    }
}
