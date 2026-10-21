using UnityEngine;

namespace Aetherward.Game
{
    /// <summary>
    /// Atmosphere (art bible v3 section 5): slow motes drifting over the battlefield, tinted per biome
    /// (pollen and aether dust, embers, snow, rift sparks, storm static, archive dust). Below the units' sorting band,
    /// low alpha and few (about 40), so they add depth without competing with combat. Off with Minimal or Battery saver.
    /// </summary>
    public sealed class AmbientMotes : MonoBehaviour
    {
        private const int Count = 42;
        private SpriteRenderer[] _r;
        private Vector3[] _vel;
        private float[] _phase, _size;
        private Color _tint;
        private float _rise;
        private Camera _cam;

        public static AmbientMotes Create(Transform parent, string biome, Camera cam)
        {
            var m = new GameObject("AmbientMotes").AddComponent<AmbientMotes>();
            m.transform.SetParent(parent, false);
            m._cam = cam;
            switch (biome)
            {
                case "molten_crater": m._tint = new Color(1f, 0.55f, 0.2f, 0.75f); m._rise = 0.55f; break;
                case "frostfall_bastion": m._tint = new Color(0.92f, 0.97f, 1f, 0.7f); m._rise = -0.35f; break;
                case "shattered_aether": m._tint = new Color(0.85f, 0.55f, 1f, 0.7f); m._rise = 0.25f; break;
                case "stormspire_citadel": m._tint = new Color(0.7f, 0.85f, 1f, 0.6f); m._rise = 0.1f; break;
                case "sunken_archive": m._tint = new Color(0.6f, 1f, 0.9f, 0.55f); m._rise = 0.15f; break;
                default: m._tint = new Color(0.95f, 1f, 0.7f, 0.6f); m._rise = 0.2f; break;   // verdant: pollen and aether dust
            }
            m.Build();
            return m;
        }

        private void Build()
        {
            _r = new SpriteRenderer[Count];
            _vel = new Vector3[Count];
            _phase = new float[Count];
            _size = new float[Count];
            Sprite s = Art.Sprite("Vfx/spark");
            for (int i = 0; i < Count; i++)
            {
                _r[i] = WorldGfx.NewSprite(transform, "Mote", s, 30000);   // dust in the air: above everything, faint
                _r[i].sharedMaterial = WorldGfx.AdditiveMaterial;
                Respawn(i, true);
            }
        }

        private void Respawn(int i, bool anywhere)
        {
            float halfW = _cam.orthographicSize * _cam.aspect + 1f, halfH = _cam.orthographicSize + 1f;
            Vector3 c = _cam.transform.position;
            float y = anywhere ? Random.Range(-halfH, halfH) : (_rise >= 0f ? -halfH : halfH);
            _r[i].transform.position = new Vector3(c.x + Random.Range(-halfW, halfW), c.y + y, 0f);
            _vel[i] = new Vector3(Random.Range(-0.25f, 0.25f), _rise * Random.Range(0.6f, 1.4f), 0f);
            _phase[i] = Random.Range(0f, 10f);
            _size[i] = Random.Range(0.25f, 0.6f);
        }

        private void Update()
        {
            bool on = WorldGfx.Feel.FxDensity > 0.3f && !App.Settings.BatterySaver;
            float dt = Time.deltaTime;
            float halfW = _cam.orthographicSize * _cam.aspect + 1.5f, halfH = _cam.orthographicSize + 1.5f;
            Vector3 c = _cam.transform.position;
            for (int i = 0; i < Count; i++)
            {
                _r[i].enabled = on;
                if (!on) continue;
                Transform t = _r[i].transform;
                _phase[i] += dt;
                Vector3 p = t.position + (_vel[i] + new Vector3(Mathf.Sin(_phase[i] * 0.7f) * 0.2f, 0f, 0f)) * dt;
                t.position = p;
                if (Mathf.Abs(p.x - c.x) > halfW || Mathf.Abs(p.y - c.y) > halfH)
                {
                    Respawn(i, false);
                    continue;
                }
                float tw = 0.45f + 0.55f * Mathf.Abs(Mathf.Sin(_phase[i] * 1.3f));
                Color col = _tint;
                col.a *= tw;
                _r[i].color = col;
                t.localScale = Vector3.one * _size[i] * (0.8f + 0.2f * tw);
            }
        }
    }
}
