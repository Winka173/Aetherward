using Aetherward.Sim.Meta;
using Aetherward.Sim.Presentation;
using NUnit.Framework;

namespace Aetherward.Tests
{
    /// <summary>P7 game-feel rules (engine-free). How the motion looks on screen still needs a Unity review.</summary>
    public class FeelTests
    {
        [Test]
        public void AccessibilityTogglesAreHardCapsOnThePreset()
        {
            FeelProfile cine = FeelProfile.For(EffectsPreset.Cinematic, true, 1f, false, false);
            Assert.Greater(cine.ShakeScale, 1f);
            Assert.Greater(cine.HitstopSeconds, 0f);
            Assert.AreEqual(0f, FeelProfile.For(EffectsPreset.Cinematic, false, 1f, false, false).ShakeScale, "shake off wins");
            Assert.AreEqual(0.3f, FeelProfile.For(EffectsPreset.Cinematic, true, 0.3f, false, false).FlashScale, 1e-4f, "flash slider caps");
            FeelProfile capped = FeelProfile.For(EffectsPreset.Cinematic, true, 1f, true, false);
            Assert.AreEqual(EffectsPreset.Reduced, capped.Preset, "Reduced VFX caps the preset");
            Assert.AreEqual(0f, capped.HitstopSeconds);
            Assert.AreEqual(EffectsPreset.Reduced, FeelProfile.For(EffectsPreset.Standard, true, 1f, false, true).Preset, "battery saver caps too");
            FeelProfile min = FeelProfile.For(EffectsPreset.Minimal, true, 1f, false, false);
            Assert.AreEqual(0f, min.ShakeScale);
            Assert.AreEqual(0f, min.FxDensity);
            Assert.Greater(min.AnimAmplitude, 0f, "units still show who is casting");
        }

        [Test]
        public void PresetsAreOrderedFromCalmToCinematic()
        {
            FeelProfile prev = FeelProfile.For(EffectsPreset.Minimal, true, 1f, false, false);
            foreach (EffectsPreset p in new[] { EffectsPreset.Reduced, EffectsPreset.Standard, EffectsPreset.Cinematic })
            {
                FeelProfile f = FeelProfile.For(p, true, 1f, false, false);
                Assert.GreaterOrEqual(f.ShakeScale, prev.ShakeScale);
                Assert.GreaterOrEqual(f.FxDensity, prev.FxDensity);
                Assert.GreaterOrEqual(f.AnimAmplitude, prev.AnimAmplitude);
                Assert.GreaterOrEqual(f.HitstopSeconds, prev.HitstopSeconds);
                prev = f;
            }
        }

        [Test]
        public void PresetIsSavedAndBadValuesFallBackToStandard()
        {
            var saves = new SaveService(new MemoryStorage());
            saves.SaveSettings(new SettingsModel { EffectsPreset = 0 });
            Assert.AreEqual(0, saves.LoadSettings().EffectsPreset);
            saves.SaveSettings(new SettingsModel { EffectsPreset = 9 });
            Assert.AreEqual((int)EffectsPreset.Standard, saves.LoadSettings().EffectsPreset);
            Assert.AreEqual((int)EffectsPreset.Standard, new SettingsModel().EffectsPreset);
        }

        [Test]
        public void CastReadsAsAnticipationReleaseRecovery()
        {
            Assert.IsTrue(UnitPose.Cast(0f, 1f).IsRest());
            Assert.Less(UnitPose.Cast(UnitPose.Windup * 0.9f, 1f).ScaleY, 1f, "wind-up squashes");
            Assert.Greater(UnitPose.Cast(UnitPose.Windup + UnitPose.Release * 0.95f, 1f).ScaleY, 1.05f, "release stretches");
            Assert.IsTrue(UnitPose.Cast(UnitPose.CastDuration, 1f).IsRest(), "ends exactly at rest");
            Assert.IsTrue(UnitPose.Cast(UnitPose.CastDuration - 0.001f, 1f).IsRest(0.01f), "settles smoothly");
            Assert.IsTrue(UnitPose.Cast(0.1f, 0f).IsRest(), "amplitude 0 = no motion");
            // continuity at the phase boundaries (no visible pop)
            foreach (float b in new[] { UnitPose.Windup, UnitPose.Windup + UnitPose.Release })
                Assert.AreEqual(UnitPose.Cast(b - 1e-4f, 1f).ScaleY, UnitPose.Cast(b + 1e-4f, 1f).ScaleY, 0.005f);
        }

        [Test]
        public void HitRecoilsAwayFromTheAttackerAndHeavyHitsHarder()
        {
            BodyPose light = UnitPose.Hit(UnitPose.HitDuration * 0.25f, 1f, 0f, false, 1f);
            BodyPose heavy = UnitPose.Hit(UnitPose.HeavyHitDuration * 0.25f, 1f, 0f, true, 1f);
            Assert.Greater(light.X, 0f);
            Assert.Greater(heavy.X, light.X);
            Assert.Less(UnitPose.Hit(0.03f, -1f, 0f, false, 1f).X, 0f);
            Assert.IsTrue(UnitPose.Hit(UnitPose.HitDuration, 1f, 0f, false, 1f).IsRest());
            Assert.IsTrue(UnitPose.Hit(0.05f, 1f, 0f, false, 0f).IsRest());
            BodyPose both = UnitPose.Cast(0.15f, 1f).Combine(light);
            Assert.AreEqual(light.X, both.X, 1e-5f);
        }

        [Test]
        public void HitstopIsShortRateLimitedAndHalvedAtDoubleSpeed()
        {
            var h = new Hitstop { Cooldown = 0.45f };
            h.Trigger(0.04f, 1, 10f);
            Assert.IsTrue(h.Active(10.03f));
            Assert.IsFalse(h.Active(10.05f));
            h.Trigger(0.04f, 1, 10.2f);
            Assert.IsFalse(h.Active(10.21f), "inside cooldown: ignored");
            h.Trigger(0.04f, 2, 11f);
            Assert.IsTrue(h.Active(11.015f));
            Assert.IsFalse(h.Active(11.025f), "2x speed halves the stop");
            h.Trigger(0f, 1, 20f);
            Assert.IsFalse(h.Active(20f), "preset without hitstop");
        }

        [Test]
        public void ImportantSoundsAreNeverStolenByHitSpam()
        {
            bool[] playing = { true, true, true };
            int[] pri = { AudioMix.Critical, AudioMix.Low, AudioMix.Low };
            float[] started = { 0f, 2f, 1f };
            Assert.AreEqual(2, AudioMix.PickVoice(playing, pri, started, AudioMix.Low), "oldest low voice is reused");
            int[] busy = { AudioMix.Critical, AudioMix.High, AudioMix.High };
            Assert.AreEqual(-1, AudioMix.PickVoice(playing, busy, started, AudioMix.Low), "spam is dropped, not stolen");
            Assert.AreEqual(1, AudioMix.PickVoice(new[] { true, false, true }, busy, started, AudioMix.Low), "free voice first");
            Assert.AreEqual(0.55f, AudioMix.DuckGain(AudioMix.Low, 1f, 1.5f), 1e-4f);
            Assert.AreEqual(1f, AudioMix.DuckGain(AudioMix.Critical, 1f, 1.5f));
            Assert.AreEqual(1f, AudioMix.DuckGain(AudioMix.Low, 2f, 1.5f));
        }
    }
}
