#!/usr/bin/env python3
"""Layout guide for a painted battlefield (R04+): what the painter must keep exactly where the simulation has it.

  python Tools/ArtPipeline/layout_guide.py --render ArtCache/EnvLayout/verdant/flat_raw.png --biome verdant_sanctuary \
      --view 36 20.25 --out ArtHandoff/requests/R04/references/verdant

Writes <out>_layout.png (the Blender toon render, the composition to repaint), <out>_guide.png (the same with lane centre
lines, lane width, the inner dais ring, the Crystal and the open intercept field drawn on top) and <out>_lanes_mask.png
(lanes white on black, used by the lead to check a returned painting against the simulation).
Game (x, y) maps to screen exactly: px = (x / W + 0.5) * width, py = (0.5 - y / H) * height.
"""
import argparse
import json
import os
import re

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORLD_SCALE = 1.3          # ContentDatabase.WorldScale
CRYSTAL = (0.0, -0.55)
DAIS_R = 3.9               # sanctum_env.DAIS_R (ground units; screen y squashed by 0.62)
FIELD_R = 5.8              # props kept out of this radius
LANE_HALF = 0.95           # painted road half width (game units)


def jsonc(path):
    return json.loads(re.sub(r"^\s*//.*$", "", open(path, encoding="utf-8").read(), flags=re.M))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--render", default=None, help="Blender layout render; omitted = a plain canvas (haven layouts)")
    p.add_argument("--size", nargs=2, type=int, default=[3344, 1882])
    p.add_argument("--biome", default="verdant_sanctuary")
    p.add_argument("--view", nargs=2, type=float, default=[36.0, 20.25])
    p.add_argument("--out", required=True)
    a = p.parse_args()
    content = os.path.join(ROOT, "Assets", "_Aetherward", "Resources", "Content")
    arena = jsonc(os.path.join(content, "arena.json"))
    biome = next(b for b in jsonc(os.path.join(content, "biomes.json"))["biomes"] if b["id"] == a.biome)
    if isinstance(biome.get("arena"), dict):
        arena = biome["arena"]
    W, H = a.view
    img = Image.open(a.render).convert("RGB") if a.render else Image.new("RGB", tuple(a.size), (96, 118, 74))
    w, h = img.size

    def px(x, y):
        return ((x / W + 0.5) * w, (0.5 - y / H) * h)

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    img.save(a.out + "_layout.png")
    g = img.copy()
    d = ImageDraw.Draw(g, "RGBA")
    m = Image.new("L", img.size, 0)
    dm = ImageDraw.Draw(m)
    ppu = w / W
    sc = arena.get("scale", WORLD_SCALE)
    # haven: walls (footprint = where the wall meets the ground) and where heroes may walk
    for x0, y0, x1, y1 in arena.get("walk", []):
        (ax, ay), (bx, by) = px(x0 * sc, y1 * sc), px(x1 * sc, y0 * sc)
        d.rectangle([ax, ay, bx, by], fill=(255, 255, 255, 28), outline=(255, 255, 255, 90), width=2)
    for x0, y0, x1, y1 in arena.get("walls", []):
        (ax, ay), (bx, by) = px(x0 * sc, y1 * sc), px(x1 * sc, y0 * sc)
        d.rectangle([ax, ay, bx, by], fill=(40, 40, 52, 235), outline=(255, 255, 255, 255), width=3)
    for lane in arena["lanes"]:
        if "gate" in lane:
            gx, gy = px(lane["gate"][0] * sc, lane["gate"][1] * sc)
            d.ellipse([gx - 10, gy - 10, gx + 10, gy + 10], outline=(80, 255, 120, 255), width=4)
    for lane in arena["lanes"]:
        pts = [px(x * sc, y * sc) for x, y in lane["points"]]
        d.line(pts, fill=(255, 40, 40, 110), width=int(2 * LANE_HALF * ppu), joint="curve")
        d.line(pts, fill=(255, 255, 255, 255), width=4, joint="curve")
        dm.line(pts, fill=255, width=int(2 * LANE_HALF * ppu), joint="curve")
        x0, y0 = pts[0]
        d.ellipse([x0 - 14, y0 - 14, x0 + 14, y0 + 14], fill=(255, 40, 40, 255))
        d.text((x0 + 16, y0 - 8), "spawn " + lane["id"], fill=(255, 255, 255, 255))
    cx, cy = px(*CRYSTAL)
    # the open field is a game-space circle (screen circle); the dais is a ground-space circle (screen ellipse)
    rings = ((FIELD_R, 1.0, (255, 255, 255, 200), 3), (DAIS_R, 0.62, (255, 220, 60, 255), 5))
    if arena.get("walls"):     # haven: no open field; a smaller ritual platform for the Crystal
        rings = ((2.8, 0.62, (255, 220, 60, 255), 5),)
    for r, ky, col, wd in rings:
        rx, ry = r * ppu, r * ky * ppu
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=col, width=wd)
    d.ellipse([cx - 0.85 * ppu, cy - 0.85 * 0.62 * ppu, cx + 0.85 * ppu, cy + 0.85 * 0.62 * ppu], outline=(80, 240, 255, 255), width=5)
    if not arena.get("walls"):
        d.text((cx + DAIS_R * ppu + 8, cy - 8), "inner dais ring (keep)", fill=(255, 220, 60, 255))
        d.text((cx + FIELD_R * ppu + 8, cy + 10), "open intercept field: no props inside", fill=(255, 255, 255, 255))
    for hz in biome.get("hazards", []):
        for x, y in hz.get("points", []):
            hx, hy = px(x * sc, y * sc)
            r = hz.get("radius", 1.3) * ppu
            d.ellipse([hx - r, hy - r * 0.62, hx + r, hy + r * 0.62], outline=(255, 140, 0, 255), width=4)
            d.text((hx + r + 4, hy - 6), "hazard " + hz.get("kind", ""), fill=(255, 160, 40, 255))
    g.save(a.out + "_guide.png")
    m.save(a.out + "_lanes_mask.png")
    print("guide:", a.out + "_guide.png", img.size)


if __name__ == "__main__":
    main()
