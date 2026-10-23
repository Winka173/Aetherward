"""Generate original, deterministic elemental ultimate cues (no external samples).

Run from the repository root: python Tools/AudioPipeline/ultimate_cues.py
These synthesized cues can later be replaced by authored audio under the same IDs.
"""
from pathlib import Path
import math
import random
import struct
import wave

ROOT = Path(__file__).resolve().parents[2]
ELEMENTS = ["fire", "water", "lightning", "ice", "wind", "earth",
            "light", "shadow", "nature", "poison", "arcane", "void"]


def generate():
    target = ROOT / "Assets/_Aetherward/Resources/Audio/Sfx"
    target.mkdir(parents=True, exist_ok=True)
    for index, element in enumerate(ELEMENTS):
        rng = random.Random(1701 + index)
        rate, seconds = 22050, 1.15
        samples = []
        base = 90 + index * 23
        noise_mix = 0.4 if element in {"fire", "earth", "wind", "poison"} else 0.12
        phase = 0.0
        for i in range(int(rate * seconds)):
            t = i / rate
            envelope = min(1.0, t / 0.025) * math.exp(-3.8 * t)
            phase += 2 * math.pi * base * (1 + 1.7 * math.exp(-9 * t)) / rate
            tone = (math.sin(phase) + 0.35 * math.sin(phase * 1.5)
                    + 0.2 * math.sin(phase * (3 if element == "lightning" else 2)))
            shimmer = math.sin(2 * math.pi * (900 + index * 90) * t) * math.exp(-7 * t)
            sample = envelope * (tone * 0.4 + rng.uniform(-1, 1) * noise_mix + shimmer * 0.12)
            samples.append(struct.pack("<h", int(max(-1, min(1, sample)) * 24000)))
        with wave.open(str(target / f"ult_{element}.wav"), "wb") as audio:
            audio.setparams((1, 2, rate, 0, "NONE", "not compressed"))
            audio.writeframes(b"".join(samples))


if __name__ == "__main__":
    generate()
