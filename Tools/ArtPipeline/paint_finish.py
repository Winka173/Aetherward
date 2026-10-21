#!/usr/bin/env python3
"""Finish a hand-painted battlefield (R04+) for the game.

  python Tools/ArtPipeline/paint_finish.py --paint ArtHandoff/returns/R04/exports/World/verdant_paint.png \
      --asset World/arena_background --env-from Assets/_Aetherward/Resources/Art/World/arena_background_env.json \
      --view 36 20.25 --out ArtProduction/generated

- Upscales 4x with Real-ESRGAN (anime model: clean ink, flat cel shapes) on the GPU.
- Stores it at 4096 x 2048 (power of two, so Unity compresses it), squashed vertically. The game stretches it back:
  PPU = 4096 / view width, and <asset>_env.json gets "bgScaleY" = (view height * PPU) / 2048.
- Copies the shadow light from --env-from. The painted props sit where the painter put them, so the old brazier and
  aether-crystal glow positions are dropped; the Crystal pool glow stays (the socket is layout-locked).
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image

ESRGAN = r"C:\Users\Winka\Tools\realesrgan\realesrgan-ncnn-vulkan.exe"


def grade(im, target, sat):
    """Push the painting under the units: one gamma to the target mean, a little less saturation, cooler darks."""
    import numpy as np
    x = np.asarray(im).astype(np.float32) / 255
    W3 = np.array([0.2126, 0.7152, 0.0722], np.float32)
    mean = float((x @ W3).mean())
    g = np.log(target) / np.log(max(mean, 1e-3))
    x = np.clip(x, 1e-4, 1) ** g
    lum = (x @ W3)[..., None]
    x = lum + (x - lum) * sat
    cool = np.clip(1 - lum * 2.2, 0, 1)
    x = x * (1 - 0.12 * cool) + np.array([0.12, 0.10, 0.22], np.float32) * 0.12 * cool
    print("grade: mean %.3f -> %.3f (gamma %.3f), sat %.2f" % (mean, float((x @ W3).mean()), g, sat))
    return Image.fromarray((np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--paint", required=True)
    p.add_argument("--asset", default="World/arena_background")
    p.add_argument("--env-from", required=True)
    p.add_argument("--view", nargs=2, type=float, default=[36.0, 20.25])
    p.add_argument("--out", default="ArtProduction/generated")
    p.add_argument("--target-mean", type=float, default=0.34, help="view luminance after the grade (units must stay the brightest)")
    p.add_argument("--sat", type=float, default=0.86)
    a = p.parse_args()
    tmp = os.path.join(tempfile.gettempdir(), "aw_paint_x4.png")
    r = subprocess.run([ESRGAN, "-i", os.path.abspath(a.paint), "-o", tmp, "-n", "realesrgan-x4plus-anime", "-s", "4"],
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(tmp):
        print(r.stderr[-800:])
        return 1
    big = Image.open(tmp).convert("RGB")
    W, H = a.view
    out = grade(big.resize((4096, 2048), Image.LANCZOS), a.target_mean, a.sat)
    dst = os.path.join(a.out, a.asset + ".png")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    out.save(dst, optimize=True)
    ppu = 4096.0 / W
    scale_y = H * ppu / 2048.0
    json.dump({"ppu": round(ppu, 3)}, open(dst + ".json", "w"))
    env = json.load(open(a.env_from))
    env.update({"bgScaleY": round(scale_y, 4), "braziersFlat": [], "aetherCrystalsFlat": [], "painted": os.path.basename(a.paint)})
    json.dump(env, open(os.path.join(a.out, a.asset + "_env.json"), "w"), indent=1)
    print("%s: %s x4 -> %s, ppu %.2f, bgScaleY %.4f" % (a.asset, Image.open(a.paint).size, out.size, ppu, scale_y))
    return 0


if __name__ == "__main__":
    sys.exit(main())
