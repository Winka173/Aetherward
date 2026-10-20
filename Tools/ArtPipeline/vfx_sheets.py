#!/usr/bin/env python3
"""Pack vfx_flipbooks.py frames into game flipbook sheets (4x4 x 512 px = 2048, power of two, so Unity compresses it).

  python Tools/ArtPipeline/vfx_sheets.py --frames ArtCache/Vfx --out ArtProduction/generated

Writes <out>/Vfx/fb_<name>.png (+ .png.json contract) and <out>/Vfx/fb_<name>_meta.json read by FxSystem.SpawnFlipbook:
cols/rows/frames/fps/ppu/pivot/blend. Transparent pixels are defringed so filtering never pulls in dark halos.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_finish import defringe  # noqa: E402

# per effect: world units across one 256 px cell (the render's ortho extent), playback, blending, pivot (effect origin)
EFFECTS = {
    "fire_burst": dict(extent=2.6, fps=24, blend="additive", pivot=[0.5, 0.18], glow="#ff7a2a",
                       ramp=("#c0281a", "#ff7a1a", "#ffd23a", "#fff6c0")),
    "smoke_puff": dict(extent=1.62, fps=20, blend="alpha", pivot=[0.5, 0.18], ramp=("#3a3048", "#6e6680", "#b4aec0"), ink="#1b1226"),
    "steam_burst": dict(extent=1.8, fps=20, blend="alpha", pivot=[0.5, 0.18], ramp=("#7f9fc0", "#c8e2f4", "#ffffff"), ink="#2a3f66"),
    "rift_mist": dict(extent=1.62, fps=16, blend="alpha", pivot=[0.5, 0.18], ramp=("#4a1050", "#a0287a", "#ff6ab0"), ink="#1b0a22"),
    "lightning_arc": dict(extent=2.4, fps=24, blend="additive", pivot=[0.5, 0.12], glow="#7fa6ff"),
    "water_splash": dict(extent=2.2, fps=24, blend="alpha", pivot=[0.5, 0.18], ramp=("#1f5fd0", "#3fb8ff", "#d8f8ff"), ink="#0e2350"),
}
COLS = ROWS = 4
CELL = 512


def _hex(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)


def toon(im, ramp, ink, additive):
    """Ravenswatch-style fx: hard-edged shapes (thresholded alpha), colour cut into flat bands of a designed ramp,
    and a dark ink rim on alpha-blended fx (additive fire has no rim: black adds nothing)."""
    a = np.asarray(im, float) / 255
    al = a[..., 3]
    lum = a[..., :3] @ np.array([0.2126, 0.7152, 0.0722])
    n = len(ramp)
    inside = lum[al > 0.18]
    # bands by rank inside the shape, so every frame shows the whole ramp in even areas (flat comic shading)
    edges = np.percentile(inside, [100.0 * (i + 1) / (n + 0.6) for i in range(n - 1)]) if inside.size else np.zeros(n - 1)
    k = np.searchsorted(edges, lum)
    t = k / max(n - 1, 1)
    cols = np.stack([_hex(h) for h in ramp])
    rgb = cols[k]
    shape = np.clip((al - 0.18) / 0.08, 0, 1)
    out = np.zeros_like(a)
    out[..., :3] = rgb
    out[..., 3] = shape * 255 if not additive else np.clip(shape * (0.55 + 0.45 * t), 0, 1) * 255
    o = Image.fromarray(out.astype(np.uint8), "RGBA")
    if ink and not additive:
        m = Image.fromarray((shape * 255).astype(np.uint8))
        rim = np.asarray(m.filter(ImageFilter.MaxFilter(7)), float) / 255
        base = np.zeros_like(a)
        base[..., :3] = _hex(ink)
        base[..., 3] = rim * 255
        b = Image.fromarray(base.astype(np.uint8), "RGBA")
        b.alpha_composite(o)
        o = b
    return o


def with_glow(im, hexcol):
    """Additive effects: a tinted halo (blurred alpha) under the rendered core, so thin bolts read at game size."""
    a = im.getchannel("A")
    halo = np.maximum(np.asarray(a.filter(ImageFilter.GaussianBlur(6)), float), np.asarray(a.filter(ImageFilter.GaussianBlur(14)), float) * 0.8) / 255
    halo = np.clip(halo * 1.6, 0, 0.85)
    col = np.array([int(hexcol[i:i + 2], 16) for i in (1, 3, 5)], float)
    g = np.zeros((im.height, im.width, 4), float)
    g[..., :3] = col
    g[..., 3] = halo * 255
    out = Image.fromarray(g.astype(np.uint8), "RGBA")
    out.alpha_composite(im)
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--frames", default="ArtCache/Vfx")
    p.add_argument("--out", default="ArtProduction/generated")
    a = p.parse_args()
    os.makedirs(os.path.join(a.out, "Vfx"), exist_ok=True)
    for name, e in EFFECTS.items():
        d = os.path.join(a.frames, name)
        if not os.path.isdir(d):
            print("skip (not rendered): " + name)
            continue
        frames = sorted(f for f in os.listdir(d) if f.endswith(".png"))[:COLS * ROWS]
        sheet = Image.new("RGBA", (COLS * CELL, ROWS * CELL), (0, 0, 0, 0))
        for i, f in enumerate(frames):
            im = Image.open(os.path.join(d, f)).convert("RGBA").resize((CELL, CELL), Image.LANCZOS)
            if e.get("ramp"):
                im = toon(im, e["ramp"], e.get("ink"), e["blend"] == "additive")
            if e.get("glow"):
                im = with_glow(im, e["glow"])
            sheet.alpha_composite(im, ((i % COLS) * CELL, (i // COLS) * CELL))
        arr = defringe(np.asarray(sheet))
        dst = os.path.join(a.out, "Vfx", "fb_%s.png" % name)
        Image.fromarray(arr).save(dst, optimize=True)
        ppu = CELL / e["extent"]
        json.dump({"like": "Vfx/glow", "ppu": round(ppu, 3)}, open(dst + ".json", "w"))
        meta = {"cols": COLS, "rows": ROWS, "frames": len(frames), "fps": e["fps"], "ppu": round(ppu, 3), "pivot": e["pivot"],
                "blend": e["blend"]}
        json.dump(meta, open(os.path.join(a.out, "Vfx", "fb_%s_meta.json" % name), "w"), indent=1)
        print("%s: %d frames -> %s (ppu %.1f, %s)" % (name, len(frames), dst, ppu, e["blend"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
