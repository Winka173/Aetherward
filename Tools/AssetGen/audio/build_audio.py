#!/usr/bin/env python3
"""Synthesizes all Aetherward SFX and music loops with numpy (no samples, no third-party audio).

Each element has its own sonic identity so effects are distinguishable without colour:
  fire = crackling noise + low whoomp, water = bubbly pitch glides, lightning = buzzy FM zaps,
  ice = glassy high partials, wind = filtered noise sweeps, earth = thuds and rumbles.
Music loops are simple original compositions (pentatonic/modal), generated note by note.

Usage: python3 Tools/AssetGen/audio/build_audio.py   (requires ffmpeg for .ogg, falls back to .wav)
"""
import os
import shutil
import subprocess
import wave
import numpy as np

SR = 44100
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(ROOT, "Assets", "_Aetherward", "Resources", "Audio")
rng = np.random.default_rng(20261019)


def t_of(dur):
    return np.arange(int(SR * dur)) / SR


def env(n, a=0.005, d=0.1, s=0.0, r=0.1, sustain_time=0.0):
    a_n, d_n, s_n, r_n = int(a * SR), int(d * SR), int(sustain_time * SR), int(r * SR)
    e = np.concatenate([np.linspace(0, 1, max(a_n, 1)), np.linspace(1, s, max(d_n, 1)), np.full(s_n, s), np.linspace(s, 0, max(r_n, 1))])
    if len(e) < n:
        e = np.concatenate([e, np.zeros(n - len(e))])
    return e[:n]


def exp_env(n, decay):
    return np.exp(-np.arange(n) / SR / decay)


def noise(n):
    return rng.uniform(-1, 1, n)


def lowpass(x, cutoff):
    """One-pole low-pass; cutoff may be an array for sweeps."""
    cutoff = np.broadcast_to(cutoff, x.shape)
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.zeros_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    return y


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def sine(freq, t):
    phase = 2 * np.pi * np.cumsum(np.broadcast_to(freq, t.shape)) / SR
    return np.sin(phase)


def tri(freq, t):
    phase = np.cumsum(np.broadcast_to(freq, t.shape)) / SR
    return 2 * np.abs(2 * (phase % 1) - 1) - 1


def square(freq, t, duty=0.5):
    phase = np.cumsum(np.broadcast_to(freq, t.shape)) / SR
    return np.where((phase % 1) < duty, 1.0, -1.0)


def saw(freq, t):
    phase = np.cumsum(np.broadcast_to(freq, t.shape)) / SR
    return 2 * (phase % 1) - 1


def reverb(x, mix=0.25, room=0.35):
    """Small Schroeder-style reverb: parallel combs + allpass."""
    out = np.zeros(len(x) + int(SR * 0.6))
    xp = np.concatenate([x, np.zeros(len(out) - len(x))])
    for delay_ms, fb in ((29.7, 0.72), (37.1, 0.7), (41.1, 0.68), (43.7, 0.66)):
        d = int(SR * delay_ms / 1000)
        y = np.copy(xp)
        for i in range(d, len(y)):
            y[i] += y[i - d] * fb * room / 0.35
        out += y * 0.25
    wet = out
    return np.concatenate([x, np.zeros(len(out) - len(x))]) * (1 - mix) + wet * mix


def normalize(x, peak=0.85):
    m = np.max(np.abs(x)) or 1.0
    return x / m * peak


def fade(x, ms=8):
    n = int(SR * ms / 1000)
    if len(x) > 2 * n:
        x[:n] *= np.linspace(0, 1, n)
        x[-n:] *= np.linspace(1, 0, n)
    return x


ffmpeg = shutil.which("ffmpeg")
written = []


def write(rel, x, peak=0.85, use_reverb=False, rv=0.2, loop=False):
    n = len(x)
    if use_reverb:
        x = reverb(x, rv)
    if loop:
        # wrap the reverb tail onto the start so the loop point is seamless; no fades
        tail = x[n:]
        x = np.copy(x[:n])
        x[:len(tail)] += tail[:n]
        x = normalize(x, peak)
    else:
        x = fade(normalize(x, peak))
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    wav_path = path + ".wav"
    with wave.open(wav_path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    if ffmpeg:
        ogg = path + ".ogg"
        r = subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", wav_path, "-c:a", "libvorbis", "-q:a", "5", ogg])
        if r.returncode == 0:
            os.remove(wav_path)
            written.append(ogg)
            return
    written.append(wav_path)


# ============================================================================ SFX

def sfx_ui():
    t = t_of(0.08)
    write("Sfx/ui_click", sine(1400, t) * exp_env(len(t), 0.015) + 0.3 * sine(2800, t) * exp_env(len(t), 0.008), 0.6)
    t = t_of(0.35)
    f = np.where(t < 0.1, 660, 990)
    write("Sfx/ui_confirm", (tri(f, t) * 0.7 + sine(f * 2, t) * 0.2) * env(len(t), 0.005, 0.25, 0.0, 0.05), 0.6, True, 0.15)
    t = t_of(0.3)
    write("Sfx/ui_error", square(np.linspace(220, 160, len(t)), t, 0.3) * env(len(t), 0.005, 0.25, 0, 0.05) * 0.5, 0.5)
    t = t_of(0.25)
    write("Sfx/ui_card", lowpass(noise(len(t)), np.linspace(6000, 1200, len(t))) * env(len(t), 0.002, 0.2, 0, 0.03) + 0.4 * sine(np.linspace(500, 900, len(t)), t) * exp_env(len(t), 0.05), 0.55)
    t = t_of(0.5)
    coin = sum(sine(f, t) * exp_env(len(t), 0.12) * (0.6 ** i) for i, f in enumerate((1568, 2093, 3136)))
    coin[int(0.07 * SR):] += sum(sine(f, t[:-int(0.07 * SR)]) * exp_env(len(t) - int(0.07 * SR), 0.12) * (0.6 ** i) for i, f in enumerate((2093, 2637)))
    write("Sfx/coin", coin, 0.55, True, 0.15)
    t = t_of(0.4)
    write("Sfx/ui_reroll", lowpass(noise(len(t)), np.linspace(800, 5000, len(t))) * env(len(t), 0.05, 0.3, 0, 0.05) + 0.5 * sine(np.linspace(300, 1200, len(t)), t) * env(len(t), 0.02, 0.35, 0, 0.03), 0.5)


def sfx_elements():
    # --- hits
    t = t_of(0.3)
    n = len(t)
    crackle = noise(n) * (rng.uniform(0, 1, n) > 0.92)
    write("Sfx/hit_fire", lowpass(noise(n), 2500) * exp_env(n, 0.06) + 0.6 * sine(np.linspace(160, 60, n), t) * exp_env(n, 0.08) + crackle * exp_env(n, 0.1) * 0.6, 0.7)
    write("Sfx/hit_water", sine(np.linspace(900, 300, n), t) * exp_env(n, 0.07) + 0.5 * lowpass(noise(n), 1800) * exp_env(n, 0.05), 0.65)
    fm = sine(1200 + 800 * sine(85, t), t)
    write("Sfx/hit_lightning", (square(np.linspace(1800, 600, n), t, 0.2) * 0.4 + fm * 0.5) * exp_env(n, 0.05), 0.55)
    write("Sfx/hit_ice", sum(sine(f, t) * exp_env(n, 0.12 / (i + 1)) for i, f in enumerate((2637, 3951, 5274))) + 0.3 * highpass(noise(n), 4000) * exp_env(n, 0.02), 0.55)
    write("Sfx/hit_wind", lowpass(highpass(noise(n), 600), np.linspace(4000, 900, n)) * env(n, 0.01, 0.22, 0, 0.05), 0.55)
    write("Sfx/hit_earth", sine(np.linspace(110, 45, n), t) * exp_env(n, 0.1) + 0.6 * lowpass(noise(n), 500) * exp_env(n, 0.07), 0.8)
    write("Sfx/hit_physical", lowpass(noise(n), 3000) * exp_env(n, 0.03) + 0.5 * sine(np.linspace(220, 90, n), t) * exp_env(n, 0.05), 0.65)
    # --- casts (whoosh + element tone)
    t = t_of(0.55)
    n = len(t)
    whoosh = lowpass(noise(n), np.concatenate([np.linspace(300, 4000, n // 2), np.linspace(4000, 600, n - n // 2)])) * env(n, 0.15, 0.35, 0, 0.05)
    tones = {"fire": saw(np.linspace(180, 90, n), t) * 0.3, "water": sine(np.linspace(400, 800, n) + 40 * sine(7, t), t) * 0.5,
             "lightning": square(440 + 300 * sine(30, t), t, 0.25) * 0.25, "ice": sum(sine(f, t) * 0.25 for f in (1760, 2217, 2637)),
             "wind": lowpass(noise(n), 1200) * 0.6, "earth": sine(np.linspace(90, 60, n), t) * 0.8}
    for el, tone in tones.items():
        write("Sfx/cast_" + el, whoosh * 0.8 + tone * env(n, 0.05, 0.4, 0, 0.1), 0.6, True, 0.18)


def sfx_reactions():
    t = t_of(0.9)
    n = len(t)
    boom = sine(np.linspace(140, 40, n), t) * exp_env(n, 0.25) + lowpass(noise(n), np.linspace(5000, 300, n)) * exp_env(n, 0.2)
    write("Sfx/react_explosion", boom, 0.9, True, 0.2)
    hiss = highpass(noise(n), 3000) * env(n, 0.01, 0.6, 0, 0.2) * 0.7 + sine(np.linspace(1200, 1500, n), t) * exp_env(n, 0.2) * 0.3
    write("Sfx/react_steam", hiss, 0.6, True, 0.2)
    zaps = np.zeros(n)
    for k in range(4):
        s0 = int(k * 0.12 * SR)
        tt = t[: n - s0]
        zaps[s0:] += square(1500 - k * 200 + 400 * sine(60, tt), tt, 0.2) * exp_env(len(tt), 0.05) * 0.6
    write("Sfx/react_chain", zaps, 0.6, True, 0.15)
    crack = sum(sine(f, t) * exp_env(n, 0.4) for f in (2093, 2637, 3136, 4186)) * 0.3 + highpass(noise(n), 5000) * exp_env(n, 0.03)
    write("Sfx/react_freeze", crack, 0.6, True, 0.3)
    storm = lowpass(noise(n), 900 + 700 * sine(1.5, t)) * env(n, 0.2, 0.5, 0.3, 0.2) * 0.8
    write("Sfx/react_storm", storm, 0.6, True, 0.25)
    rumble = lowpass(noise(n), 200) * env(n, 0.05, 0.6, 0.2, 0.2) * 1.5 + sine(50, t) * exp_env(n, 0.4)
    write("Sfx/react_rumble", rumble, 0.85, True, 0.2)
    t2 = t_of(0.6)
    bell = sum(sine(f, t2) * exp_env(len(t2), 0.5 / (i + 1)) for i, f in enumerate((880, 1320, 1760, 2640)))
    write("Sfx/react_generic", bell * 0.5 + 0.3 * lowpass(noise(len(t2)), 3000) * exp_env(len(t2), 0.05), 0.55, True, 0.3)


def sfx_expansion():
    """Six expansion elements (hits + casts) and the reaction families they introduce."""
    t = t_of(0.3)
    n = len(t)
    shimmer = sum(sine(f, t) * exp_env(n, 0.1 / (i + 1)) for i, f in enumerate((1568, 2349, 3136)))
    write("Sfx/hit_light", shimmer * 0.6 + 0.25 * highpass(noise(n), 6000) * exp_env(n, 0.02), 0.55)
    write("Sfx/hit_shadow", lowpass(noise(n), np.linspace(1500, 200, n)) * env(n, 0.005, 0.25, 0, 0.05) + 0.5 * sine(np.linspace(220, 70, n), t) * exp_env(n, 0.09), 0.7)
    rustle = lowpass(highpass(noise(n), 1500), 5000) * (0.5 + 0.5 * sine(23, t)) * env(n, 0.01, 0.25, 0, 0.04)
    write("Sfx/hit_nature", rustle + 0.4 * sine(np.linspace(300, 180, n), t) * exp_env(n, 0.05), 0.6)
    bubble = sum(sine(np.linspace(400 + 150 * k, 900 + 150 * k, n), t) * exp_env(n, 0.04) * (0.7 ** k) for k in range(3))
    write("Sfx/hit_poison", bubble * 0.6 + 0.3 * lowpass(noise(n), 1200) * exp_env(n, 0.06), 0.6)
    write("Sfx/hit_arcane", sine(1320 + 220 * sine(12, t), t) * exp_env(n, 0.09) * 0.6 + 0.3 * sine(1980, t) * exp_env(n, 0.05), 0.55)
    write("Sfx/hit_void", sine(np.linspace(60, 140, n), t) * env(n, 0.04, 0.24, 0, 0.02) + 0.4 * lowpass(noise(n), np.linspace(200, 2000, n)) * env(n, 0.05, 0.2, 0, 0.03), 0.75)
    t = t_of(0.55)
    n = len(t)
    whoosh = lowpass(noise(n), np.concatenate([np.linspace(300, 4000, n // 2), np.linspace(4000, 600, n - n // 2)])) * env(n, 0.15, 0.35, 0, 0.05)
    tones = {"light": sum(sine(f, t) * 0.22 for f in (1046, 1318, 1568)), "shadow": saw(np.linspace(110, 70, n), t) * 0.25,
             "nature": tri(np.linspace(330, 440, n), t) * 0.4, "poison": sine(np.linspace(500, 300, n) + 60 * sine(9, t), t) * 0.45,
             "arcane": sine(880 + 440 * sine(5, t), t) * 0.35, "void": sine(np.linspace(55, 110, n), t) * 0.8}
    for el, tone in tones.items():
        write("Sfx/cast_" + el, whoosh * 0.8 + tone * env(n, 0.05, 0.4, 0, 0.1), 0.6, True, 0.18)
    t = t_of(0.9)
    n = len(t)
    chord = sum(sine(f, t) * exp_env(n, 0.5 / (i + 1)) for i, f in enumerate((523, 659, 784, 1046)))
    write("Sfx/react_holy", chord * 0.45 + 0.2 * highpass(noise(n), 7000) * exp_env(n, 0.05), 0.55, True, 0.35)
    dark = lowpass(noise(n), np.linspace(2500, 150, n)) * env(n, 0.02, 0.6, 0, 0.2) + sine(np.linspace(180, 45, n), t) * exp_env(n, 0.35)
    write("Sfx/react_dark", dark, 0.75, True, 0.3)
    toxic = np.zeros(n)
    for k in range(6):
        s0 = int(k * 0.09 * SR)
        tt = t[: n - s0]
        toxic[s0:] += sine(np.linspace(300 + 60 * k, 800 + 60 * k, len(tt)), tt) * exp_env(len(tt), 0.04) * 0.5
    write("Sfx/react_toxic", toxic + 0.2 * lowpass(noise(n), 900) * exp_env(n, 0.3), 0.6, True, 0.2)
    sparkles = sum(sine(f, t) * exp_env(n, 0.3) * (0.8 ** i) for i, f in enumerate((1760, 2637, 3520, 4186)))
    write("Sfx/react_arcane", sparkles * 0.4 + sine(440 + 220 * sine(3, t), t) * exp_env(n, 0.4) * 0.3, 0.55, True, 0.35)
    implode = sine(np.linspace(40, 180, n), t) * env(n, 0.3, 0.5, 0, 0.05) + lowpass(noise(n), np.linspace(100, 3000, n)) * env(n, 0.4, 0.45, 0, 0.03)
    write("Sfx/react_void", implode, 0.8, True, 0.25)
    growth = lowpass(highpass(noise(n), 1200), 4000) * (0.5 + 0.5 * sine(17, t)) * env(n, 0.05, 0.6, 0, 0.2) + tri(np.linspace(220, 330, n), t) * exp_env(n, 0.4) * 0.3
    write("Sfx/react_growth", growth, 0.6, True, 0.25)


def sfx_game():
    t = t_of(0.35)
    n = len(t)
    write("Sfx/enemy_death", lowpass(noise(n), np.linspace(4000, 400, n)) * exp_env(n, 0.08) + 0.5 * sine(np.linspace(600, 200, n), t) * exp_env(n, 0.1), 0.6)
    t = t_of(0.6)
    n = len(t)
    write("Sfx/enemy_spawn", sine(np.linspace(200, 500, n) + 30 * sine(9, t), t) * env(n, 0.2, 0.3, 0, 0.1) * 0.5 + lowpass(noise(n), 1500) * env(n, 0.1, 0.4, 0, 0.1) * 0.4, 0.45, True, 0.3)
    t = t_of(0.5)
    n = len(t)
    write("Sfx/crystal_hit", sum(sine(f, t) * exp_env(n, 0.25) for f in (523, 784, 1046)) * 0.4 + lowpass(noise(n), 2500) * exp_env(n, 0.04), 0.7, True, 0.3)
    t = t_of(0.9)
    n = len(t)
    write("Sfx/crystal_crack", highpass(noise(n), 2000) * exp_env(n, 0.08) + sum(sine(f, t) * exp_env(n, 0.5) for f in (370, 554, 740)) * 0.35, 0.8, True, 0.35)
    t = t_of(0.7)
    n = len(t)
    write("Sfx/hero_down", tri(np.linspace(440, 110, n), t) * env(n, 0.01, 0.6, 0, 0.1) * 0.6, 0.6, True, 0.2)
    write("Sfx/hero_revive", tri(np.linspace(220, 880, n), t) * env(n, 0.05, 0.5, 0, 0.15) * 0.5 + sum(sine(f, t) for f in (880, 1320)) * exp_env(n, 0.3) * 0.2, 0.6, True, 0.3)
    t = t_of(0.8)
    n = len(t)
    arp = np.zeros(n)
    for k, f in enumerate((523, 659, 784, 1046)):
        s0 = int(k * 0.08 * SR)
        tt = t[: n - s0]
        arp[s0:] += tri(f, tt) * exp_env(len(tt), 0.25) * 0.5
    write("Sfx/level_up", arp, 0.6, True, 0.3)
    t = t_of(1.6)
    n = len(t)
    evo = sum(sine(f * (1 + 0.5 * t / 1.6), t) * (0.5 ** i) for i, f in enumerate((262, 392, 523, 784))) * env(n, 0.3, 1.0, 0.2, 0.3)
    write("Sfx/evolution", evo + 0.2 * highpass(noise(n), 6000) * env(n, 0.5, 0.8, 0, 0.3), 0.7, True, 0.45)
    t = t_of(1.2)
    n = len(t)
    horn = (saw(196, t) * 0.4 + saw(294, t) * 0.3 + saw(392, t) * 0.2)
    write("Sfx/wave_start", lowpass(horn, 1400) * env(n, 0.08, 0.3, 0.6, 0.4, 0.4), 0.65, True, 0.35)
    t = t_of(1.4)
    n = len(t)
    fan = np.zeros(n)
    for k, (f, d) in enumerate(((523, 0.0), (659, 0.12), (784, 0.24), (1046, 0.4))):
        s0 = int(d * SR)
        tt = t[: n - s0]
        fan[s0:] += (tri(f, tt) * 0.6 + sine(f * 2, tt) * 0.2) * exp_env(len(tt), 0.5)
    write("Sfx/wave_clear", fan, 0.65, True, 0.35)
    t = t_of(1.4)
    n = len(t)
    write("Sfx/boss_roar", lowpass(saw(np.linspace(90, 60, n) + 6 * sine(11, t), t), 700) * env(n, 0.1, 0.6, 0.6, 0.4, 0.3) + lowpass(noise(n), 400) * env(n, 0.1, 1.0, 0, 0.2) * 0.5, 0.85, True, 0.3)
    t = t_of(0.5)
    n = len(t)
    write("Sfx/telegraph", square(np.where((t * 8).astype(int) % 2 == 0, 880, 660), t, 0.5) * env(n, 0.005, 0.45, 0, 0.04) * 0.3, 0.45)
    t = t_of(2.4)
    n = len(t)
    vic = np.zeros(n)
    for k, (f, d) in enumerate(((392, 0), (523, 0.18), (659, 0.36), (784, 0.54), (1046, 0.9))):
        s0 = int(d * SR)
        tt = t[: n - s0]
        vic[s0:] += (tri(f, tt) * 0.5 + tri(f * 1.5, tt) * 0.2) * exp_env(len(tt), 0.7)
    write("Sfx/victory", vic, 0.7, True, 0.4)
    t = t_of(2.0)
    n = len(t)
    dfeat = np.zeros(n)
    for k, (f, d) in enumerate(((392, 0), (370, 0.35), (349, 0.7), (262, 1.05))):
        s0 = int(d * SR)
        tt = t[: n - s0]
        dfeat[s0:] += tri(f, tt) * exp_env(len(tt), 0.5) * 0.6
    write("Sfx/defeat", dfeat, 0.65, True, 0.45)


# ============================================================================ music

NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def freq(name, octave):
    return 440.0 * 2 ** ((NOTE[name] + 12 * (octave + 1) - 69) / 12.0)


def render_track(bpm, bars, chords, melody_fn, style, beats_per_bar=4):
    beat = 60.0 / bpm
    total = int(SR * beat * beats_per_bar * bars)
    out = np.zeros(total)
    for bar in range(bars):
        root, quality = chords[bar % len(chords)]
        third = 3 if quality == "m" else 4
        tones = [freq(root, 3), freq(root, 3) * 2 ** (third / 12), freq(root, 3) * 2 ** (7 / 12)]
        bar_start = int(bar * beats_per_bar * beat * SR)
        # pad
        dur = beats_per_bar * beat
        t = t_of(dur)
        pad = sum(tri(f, t) * 0.12 + sine(f * 2, t) * 0.05 for f in tones) * env(len(t), 0.3, 0.2, 0.8, 0.3, dur - 0.8)
        seg = out[bar_start:bar_start + len(t)]
        seg += pad[:len(seg)]
        # bass
        for b in range(beats_per_bar):
            if style == "menu" and b % 2:
                continue
            s0 = bar_start + int(b * beat * SR)
            tt = t_of(beat * 0.9)
            f = freq(root, 2) if b % 2 == 0 else freq(root, 2) * 2 ** (7 / 12)
            bass = (sine(f, tt) * 0.5 + tri(f, tt) * 0.2) * exp_env(len(tt), beat * 0.6)
            seg2 = out[s0:s0 + len(tt)]
            seg2 += bass[:len(seg2)] * (0.5 if style == "menu" else 0.8)
        # drums
        if style != "menu":
            for step in range(beats_per_bar * 2):
                s0 = bar_start + int(step * beat / 2 * SR)
                if step % 4 == 0 or (style == "boss" and step % 2 == 0):
                    tt = t_of(0.25)
                    kick = sine(np.linspace(120, 45, len(tt)), tt) * exp_env(len(tt), 0.07)
                    seg3 = out[s0:s0 + len(tt)]
                    seg3 += kick[:len(seg3)] * 0.9
                if step % 4 == 2:
                    tt = t_of(0.2)
                    snare = lowpass(noise(len(tt)), 5000) * exp_env(len(tt), 0.05) * 0.45 + sine(190, tt) * exp_env(len(tt), 0.03) * 0.3
                    seg3 = out[s0:s0 + len(tt)]
                    seg3 += snare[:len(seg3)]
                tt = t_of(0.06)
                hat = highpass(noise(len(tt)), 7000) * exp_env(len(tt), 0.015) * (0.25 if step % 2 else 0.15)
                seg3 = out[s0:s0 + len(tt)]
                seg3 += hat[:len(seg3)]
        # melody
        for (beat_pos, length, note, octave) in melody_fn(bar, root, quality):
            s0 = bar_start + int(beat_pos * beat * SR)
            tt = t_of(length * beat)
            f = freq(note, octave)
            vib = f * (1 + 0.004 * sine(5.5, tt))
            if style == "boss":
                lead = saw(vib, tt) * 0.12 + square(vib, tt, 0.3) * 0.08
                lead = lowpass(lead, 2600)
            else:
                lead = tri(vib, tt) * 0.25 + sine(vib * 2, tt) * 0.06
            lead *= env(len(tt), 0.01, 0.15, 0.6, 0.12, max(0.0, length * beat - 0.3))
            seg4 = out[s0:s0 + len(tt)]
            seg4 += lead[:len(seg4)]
    return out


def music():
    # Menu: gentle, D dorian-ish, 84 bpm.
    menu_chords = [("D", "m"), ("C", ""), ("A#", ""), ("C", ""), ("D", "m"), ("F", ""), ("G", ""), ("A", "m")]
    menu_scale = ["D", "F", "G", "A", "C"]

    def menu_mel(bar, root, q):
        r = np.random.default_rng(bar + 7)
        notes = []
        pos = 0.0
        while pos < 4:
            ln = r.choice([1.0, 1.0, 0.5, 2.0])
            if r.random() > 0.25:
                notes.append((pos, min(ln, 4 - pos), menu_scale[r.integers(0, 5)], 5))
            pos += ln
        return notes

    x = render_track(84, 16, menu_chords, menu_mel, "menu")
    write("Music/menu_loop", x, 0.6, True, 0.3, loop=True)

    # Battle: energetic, A minor pentatonic, 128 bpm.
    battle_chords = [("A", "m"), ("F", ""), ("C", ""), ("G", ""), ("A", "m"), ("F", ""), ("G", ""), ("E", "m")]
    battle_scale = ["A", "C", "D", "E", "G"]

    def battle_mel(bar, root, q):
        r = np.random.default_rng(bar * 3 + 11)
        motif = [(0, 0.5), (0.5, 0.5), (1, 1.0), (2, 0.5), (2.5, 0.5), (3, 1.0)]
        notes = []
        base = r.integers(0, 3)
        for k, (p, ln) in enumerate(motif):
            idx = (base + [0, 1, 2, 1, 3, 2][k] + (bar % 2)) % 5
            notes.append((p, ln, battle_scale[idx], 5 if k < 4 else 4 + (bar % 2)))
        return notes

    x = render_track(128, 16, battle_chords, battle_mel, "battle")
    write("Music/battle_loop", x, 0.6, True, 0.2, loop=True)

    # Boss: driving, D phrygian flavour, 140 bpm.
    boss_chords = [("D", "m"), ("D#", ""), ("D", "m"), ("C", ""), ("A#", ""), ("C", ""), ("D", "m"), ("A", "m")]
    boss_scale = ["D", "D#", "F", "G", "A", "A#", "C"]

    def boss_mel(bar, root, q):
        notes = []
        for k in range(8):
            if (k + bar) % 3 == 2:
                continue
            idx = (k * 2 + bar) % 7
            notes.append((k * 0.5, 0.45, boss_scale[idx], 4 if k < 4 else 5))
        return notes

    x = render_track(140, 16, boss_chords, boss_mel, "boss")
    write("Music/boss_loop", x, 0.62, True, 0.2, loop=True)


if __name__ == "__main__":
    import sys
    if "--only" in sys.argv:
        # Partial rebuild (avoids re-encoding unchanged launch audio): --only expansion
        globals()["sfx_" + sys.argv[sys.argv.index("--only") + 1]]()
    else:
        sfx_ui()
        sfx_elements()
        sfx_reactions()
        sfx_expansion()
        sfx_game()
        music()
    print("wrote %d audio files" % len(written))
