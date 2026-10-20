using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace Aetherward.Game
{
    /// <summary>
    /// Lighting data a battlefield was rendered with (Tools/ArtPipeline/blender/sanctum_env.py → env_meta.json), shipped
    /// next to the background as Resources/Art/World/&lt;name&gt;_env.json. Flat arrays: JsonUtility cannot read nested ones.
    /// </summary>
    [Serializable]
    public sealed class EnvMeta
    {
        public float[] shadowDirScreen = { 0.8f, 0.6f };
        public float shadowLengthPerHeight = 0.6f;
        public float[] braziersFlat = new float[0];
        public float[] aetherCrystalsFlat = new float[0];
        public float[] edgeColor = { 0.06f, 0.07f, 0.09f };
    }

    /// <summary>
    /// Living light on the battlefield: unit shadows that follow the background's sun, a breathing Crystal light pool,
    /// flickering braziers and pulsing aether crystals (additive glows over the background, under the units).
    /// </summary>
    public sealed class EnvironmentFx : MonoBehaviour
    {
        private struct Glow
        {
            public SpriteRenderer R;
            public Color Color;
            public float Scale, Phase, Speed, Flicker;
        }

        private readonly List<Glow> _glows = new List<Glow>();
        private static Material _additive;
        public const float ElevationCos = 0.7848f;   // cos(asin(0.62)): a sprite's screen height is its world height x this

        public static EnvMeta Load(string background)
        {
            string name = Path.GetFileName(background) + "_env";
            string text = null;
            if (Art.OverrideRoot != null)
            {
                string f = Path.Combine(Art.OverrideRoot, Path.GetDirectoryName(background) ?? "", name + ".json");
                if (File.Exists(f)) text = File.ReadAllText(f);
            }
            if (text == null)
            {
                TextAsset t = Resources.Load<TextAsset>("Art/" + Path.GetDirectoryName(background)?.Replace('\\', '/') + "/" + name);
                if (t != null) text = t.text;
            }
            return text != null ? JsonUtility.FromJson<EnvMeta>(text) : null;
        }

        public static EnvironmentFx Create(Transform parent, string background, Camera cam)
        {
            EnvMeta meta = Load(background);
            var fx = new GameObject("EnvironmentFx").AddComponent<EnvironmentFx>();
            fx.transform.SetParent(parent, false);
            Vector2 dir = meta != null ? new Vector2(meta.shadowDirScreen[0], meta.shadowDirScreen[1]) : new Vector2(0.8f, 0.6f);
            // keep unit shadows a little shorter than the props': units must stay readable in a crowd
            float len = (meta != null ? meta.shadowLengthPerHeight : 0.6f) / ElevationCos * 0.75f;
            WorldGfx.ApplyEnvironmentLight(dir, len, meta != null ? 0.5f : 0.35f);
            if (meta != null && meta.edgeColor != null && meta.edgeColor.Length >= 3 && cam != null)
                cam.backgroundColor = new Color(meta.edgeColor[0], meta.edgeColor[1], meta.edgeColor[2]);
            fx.Add(new Vector3(0f, -0.35f, 0f), new Color(0.45f, 0.85f, 1f), 5.5f, 0.32f, 0.9f, 0.02f);   // crystal pool
            if (meta != null)
            {
                for (int i = 0; i + 1 < meta.braziersFlat.Length; i += 2)
                    fx.Add(new Vector3(meta.braziersFlat[i], meta.braziersFlat[i + 1], 0), new Color(0.38f, 0.95f, 0.85f), 2.6f, 0.45f, 9f, 0.18f);
                for (int i = 0; i + 1 < meta.aetherCrystalsFlat.Length; i += 2)
                    fx.Add(new Vector3(meta.aetherCrystalsFlat[i], meta.aetherCrystalsFlat[i + 1], 0), new Color(0.45f, 0.85f, 1f), 1.8f, 0.35f, 1.3f, 0.05f);
            }
            return fx;
        }

        private void Add(Vector3 pos, Color c, float scale, float alpha, float speed, float flicker)
        {
            if (_additive == null)
            {
                Shader s = Resources.Load<Shader>("Shaders/SpriteAdditive");
                _additive = s != null ? new Material(s) : WorldGfx.SpriteMaterial;
            }
            SpriteRenderer r = WorldGfx.NewSprite(transform, "Glow", Art.Sprite("Vfx/glow"), -8500);
            r.sharedMaterial = _additive;
            r.transform.position = pos;
            c.a = alpha;
            _glows.Add(new Glow { R = r, Color = c, Scale = scale, Phase = UnityEngine.Random.value * 10f, Speed = speed, Flicker = flicker });
        }

        private void Update()
        {
            float amp = WorldGfx.Feel.AnimAmplitude > 0f ? 1f : 0f;
            float t = Time.time;
            foreach (Glow g in _glows)
            {
                // slow breathing plus, for flames, a fast two-frequency flicker
                float breathe = Mathf.Sin(t * g.Speed * 0.35f + g.Phase) * 0.12f;
                float flick = (Mathf.PerlinNoise(t * g.Speed, g.Phase) - 0.5f) * 2f * g.Flicker;
                float k = 1f + amp * (breathe + flick);
                Color c = g.Color;
                c.a *= k;
                g.R.color = c;
                g.R.transform.localScale = Vector3.one * g.Scale * (1f + amp * flick * 0.3f);
            }
        }
    }
}
