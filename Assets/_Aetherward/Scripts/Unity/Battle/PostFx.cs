using Aetherward.Sim.Presentation;
using UnityEngine;

namespace Aetherward.Game
{
    /// <summary>
    /// Battle-camera post-processing for the built-in renderer: bloom on emissive highlights (the Crystal, flames,
    /// spells), a light night grade and a vignette. IMGUI is drawn after image effects, so the HUD stays untouched.
    /// Off with Battery saver or the Minimal effects preset; bloom is skipped with Reduced VFX.
    /// </summary>
    [RequireComponent(typeof(Camera))]
    public sealed class PostFx : MonoBehaviour
    {
        private const int Levels = 5;
        private static readonly int ThresholdId = Shader.PropertyToID("_Threshold");
        private static readonly int BloomTexId = Shader.PropertyToID("_BloomTex");
        private static readonly int BloomIntensityId = Shader.PropertyToID("_BloomIntensity");
        private static readonly int LiftId = Shader.PropertyToID("_Lift"), GammaId = Shader.PropertyToID("_Gamma"), GainId = Shader.PropertyToID("_Gain");
        private static readonly int SaturationId = Shader.PropertyToID("_Saturation"), VignetteId = Shader.PropertyToID("_Vignette");
        private readonly RenderTexture[] _chain = new RenderTexture[Levels];
        private Material _mat;

        public float Threshold = 0.85f, Knee = 0.3f, BloomIntensity = 0.4f, Saturation = 1.06f, Vignette = 0.32f;
        public Color Lift = new Color(0.012f, 0.016f, 0.03f), Gamma = new Color(1f, 1f, 1.02f), Gain = new Color(1.04f, 1.02f, 1f);

        private bool Active => App.Settings != null && !App.Settings.BatterySaver && App.Settings.EffectsPreset != (int)EffectsPreset.Minimal;

        private void OnRenderImage(RenderTexture src, RenderTexture dst)
        {
            if (_mat == null)
            {
                Shader s = Resources.Load<Shader>("Shaders/PostFX");
                if (s == null || !s.isSupported) { Graphics.Blit(src, dst); enabled = false; return; }
                _mat = new Material(s) { hideFlags = HideFlags.HideAndDontSave };
            }
            if (!Active) { Graphics.Blit(src, dst); return; }
            bool bloom = !App.Settings.ReducedVfx;
            _mat.SetVector(ThresholdId, new Vector4(Threshold, Knee, 8f, 0));
            _mat.SetFloat(BloomIntensityId, bloom ? BloomIntensity : 0f);
            _mat.SetColor(LiftId, Lift);
            _mat.SetColor(GammaId, Gamma);
            _mat.SetColor(GainId, Gain);
            _mat.SetFloat(SaturationId, Saturation);
            _mat.SetFloat(VignetteId, Vignette);
            RenderTexture top = null;
            if (bloom)
            {
                int w = src.width / 2, h = src.height / 2;
                for (int i = 0; i < Levels; i++)
                {
                    _chain[i] = RenderTexture.GetTemporary(Mathf.Max(1, w), Mathf.Max(1, h), 0, src.format);
                    Graphics.Blit(i == 0 ? src : _chain[i - 1], _chain[i], _mat, i == 0 ? 0 : 1);
                    w /= 2;
                    h /= 2;
                }
                for (int i = Levels - 1; i > 0; i--) Graphics.Blit(_chain[i], _chain[i - 1], _mat, 2);
                top = _chain[0];
            }
            _mat.SetTexture(BloomTexId, top != null ? (Texture)top : Texture2D.blackTexture);
            Graphics.Blit(src, dst, _mat, 3);
            for (int i = 0; i < Levels; i++)
            {
                if (_chain[i] != null) RenderTexture.ReleaseTemporary(_chain[i]);
                _chain[i] = null;
            }
        }

        private void OnDestroy()
        {
            if (_mat != null) Destroy(_mat);
        }
    }
}
