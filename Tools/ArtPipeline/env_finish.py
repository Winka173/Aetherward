#!/usr/bin/env python3
"""Finish a sanctum_env.py render into a game battlefield: value grade, edge colour, package for Unity.

  python Tools/ArtPipeline/env_finish.py --render ArtCache/Env/verdant --asset World/arena_background \
      --out ArtCache/Override [--target-mean 0.16]

- Grades the 16-bit render with one gamma so the mean luminance of the 16:9 view (26.7 x 15 of the 34 x 19.2 units)
  hits --target-mean (art bible: ground value 15-45 %, battlefield mean ~0.16, units must read lighter).
- Writes <out>/<asset>.png (RGB), the sidecar <asset>.png.json {"ppu": ...} (new 2K contract) and <out>/<asset>_env.json
  (shadow light, glow positions, edge colour) that EnvironmentFx reads; prints the measured values.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image


def lum(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--render", required=True)
    p.add_argument("--asset", default="World/arena_background")
    p.add_argument("--out", required=True)
    p.add_argument("--target-mean", type=float, default=0.16)
    a = p.parse_args()
    meta = json.load(open(os.path.join(a.render, "env_meta.json")))
    img = np.asarray(Image.open(os.path.join(a.render, "flat_raw.png"))).astype(np.float64)
    img /= 65535.0 if img.max() > 255 else 255.0
    H, W = img.shape[:2]
    vw, vh = meta["camera"]["viewUnits"]
    ppu = W / vw
    cx, cy, hw, hh = W / 2, H / 2, 26.67 / 2 * ppu, 15.0 / 2 * ppu
    view = img[int(cy - hh):int(cy + hh), int(cx - hw):int(cx + hw)]
    before = float(lum(view).mean())
    # one gamma that maps the view mean to the target (searched, since the mean of a power is not the power of the mean)
    lo, hi = 0.3, 3.0
    for _ in range(40):
        g = (lo + hi) / 2
        m = float(lum(view ** g).mean())
        lo, hi = (g, hi) if m > a.target_mean else (lo, g)
    out = np.clip(img ** g, 0, 1)
    after = float(lum(out[int(cy - hh):int(cy + hh), int(cx - hw):int(cx + hw)]).mean())
    band = max(8, int(0.25 * ppu))
    edge = np.concatenate([out[:band].reshape(-1, 3), out[-band:].reshape(-1, 3), out[:, :band].reshape(-1, 3), out[:, -band:].reshape(-1, 3)])
    edge_col = [round(float(v), 4) for v in np.median(edge, 0)]
    dst = os.path.join(a.out, a.asset + ".png")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    Image.fromarray((out * 255 + 0.5).astype(np.uint8), "RGB").save(dst, optimize=True)
    json.dump({"ppu": round(ppu, 3)}, open(dst + ".json", "w"))
    env = {"shadowDirScreen": meta["shadowDirScreen"], "shadowLengthPerHeight": meta["shadowLengthPerHeight"],
           "braziersFlat": meta.get("braziersFlat", []), "aetherCrystalsFlat": meta.get("aetherCrystalsFlat", []), "edgeColor": edge_col,
           "source": os.path.relpath(a.render).replace("\\", "/"), "gamma": round(g, 4), "viewMeanBefore": round(before, 4), "viewMean": round(after, 4)}
    json.dump(env, open(os.path.join(a.out, a.asset + "_env.json"), "w"), indent=1)
    print("%s: %dx%d ppu %.1f | view mean %.3f -> %.3f (gamma %.3f) | edge %s -> %s" % (a.asset, W, H, ppu, before, after, g, edge_col, dst))
    return 0


if __name__ == "__main__":
    sys.exit(main())
