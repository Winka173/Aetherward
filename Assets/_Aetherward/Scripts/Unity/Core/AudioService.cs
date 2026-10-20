using System.Collections.Generic;
using Aetherward.Sim.Presentation;
using UnityEngine;

namespace Aetherward.Game
{
    public enum SoundCategory
    {
        Sfx,
        Ui
    }

    /// <summary>
    /// Pooled one-shot SFX with per-sound rate limiting (no stacking 40 hit sounds in one frame) and
    /// a crossfading music player. Volumes come from the category sliders in Settings.
    /// Voices are allocated by priority (AudioMix): hit spam can never steal the voice of a boss roar or a telegraph
    /// warning, and a Critical cue ducks other SFX briefly so it is heard over the mix.
    /// </summary>
    public sealed class AudioService : MonoBehaviour
    {
        private const int Voices = 20;
        private readonly List<AudioSource> _voices = new List<AudioSource>();
        private readonly bool[] _playing = new bool[Voices];
        private readonly int[] _priority = new int[Voices];
        private readonly float[] _startedAt = new float[Voices];
        private float _duckUntil = float.MinValue;
        private readonly Dictionary<string, AudioClip> _clips = new Dictionary<string, AudioClip>();
        private readonly Dictionary<string, float> _lastPlayed = new Dictionary<string, float>();
        private AudioSource _musicA, _musicB;
        private bool _aActive = true;
        private string _currentMusic;
        private float _fade = 1f;

        public static AudioService Create(Transform parent)
        {
            var go = new GameObject("Audio");
            go.transform.SetParent(parent, false);
            var svc = go.AddComponent<AudioService>();
            for (int i = 0; i < Voices; i++)
            {
                var src = go.AddComponent<AudioSource>();
                src.playOnAwake = false;
                svc._voices.Add(src);
            }
            svc._musicA = go.AddComponent<AudioSource>();
            svc._musicB = go.AddComponent<AudioSource>();
            foreach (AudioSource m in new[] { svc._musicA, svc._musicB })
            {
                m.loop = true;
                m.playOnAwake = false;
            }
            return svc;
        }

        private AudioClip Clip(string path)
        {
            if (_clips.TryGetValue(path, out AudioClip c)) return c;
            c = Resources.Load<AudioClip>("Audio/" + path);
            _clips[path] = c;
            return c;
        }

        private float CategoryVolume(SoundCategory cat)
        {
            var s = App.Settings;
            return s.MasterVolume * (cat == SoundCategory.Ui ? s.UiVolume : s.SfxVolume);
        }

        public void Play(string name, float volume = 1f, float pitchVariance = 0.06f, SoundCategory cat = SoundCategory.Sfx, float minInterval = 0.05f,
                         int priority = AudioMix.Normal)
        {
            if (App.Settings == null) return;
            float now = Time.unscaledTime;
            if (_lastPlayed.TryGetValue(name, out float last) && now - last < minInterval) return;
            _lastPlayed[name] = now;
            AudioClip clip = Clip("Sfx/" + name);
            if (clip == null) return;
            for (int i = 0; i < _voices.Count; i++) _playing[i] = _voices[i].isPlaying;
            int v = AudioMix.PickVoice(_playing, _priority, _startedAt, priority);
            if (v < 0) return;   // every voice is busy with something more important
            AudioSource src = _voices[v];
            _priority[v] = priority;
            _startedAt[v] = now;
            if (priority >= AudioMix.Critical) _duckUntil = now + 0.6f;
            src.pitch = 1f + Random.Range(-pitchVariance, pitchVariance);
            src.volume = Mathf.Clamp01(volume * CategoryVolume(cat) * (cat == SoundCategory.Ui ? 1f : AudioMix.DuckGain(priority, now, _duckUntil)));
            src.clip = clip;
            src.Play();
        }

        public void Ui(string name) => Play(name, 0.8f, 0.02f, SoundCategory.Ui, 0.03f, AudioMix.High);

        public void PlayMusic(string name)
        {
            if (_currentMusic == name) return;
            _currentMusic = name;
            AudioClip clip = Clip("Music/" + name);
            if (clip == null) return;
            AudioSource incoming = _aActive ? _musicB : _musicA;
            incoming.clip = clip;
            incoming.volume = 0f;
            incoming.Play();
            _aActive = !_aActive;
            _fade = 0f;
        }

        public void ApplyVolumes()
        {
            _fade = Mathf.Min(_fade, 0.999f);
        }

        private void Update()
        {
            if (App.Settings == null) return;
            float target = App.Settings.MasterVolume * App.Settings.MusicVolume * 0.7f;
            _fade = Mathf.Min(1f, _fade + Time.unscaledDeltaTime / 1.2f);
            AudioSource active = _aActive ? _musicA : _musicB;
            AudioSource other = _aActive ? _musicB : _musicA;
            active.volume = target * _fade;
            other.volume = target * (1f - _fade);
            if (_fade >= 1f && other.isPlaying) other.Stop();
        }
    }
}
