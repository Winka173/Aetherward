#!/usr/bin/env python3
"""OFFLINE battlefield composite (NOT a Unity capture).

Draws a simulator snapshot (Tools/SimHarness/Balance --snapshot) with the real sprites at the same
camera scale and pivots the Unity view uses (ortho size 7.5 at 1920x1080), to review readability:
unit scale, silhouettes, crowd density, lane/zone legibility. HUD is approximated only.

Usage: python3 Tools/AssetGen/preview/compose_frame.py snapshot.json out.png
"""
import json
import math
import os
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
# AW_ART_DIR / AW_SETTINGS let the same snapshot be rendered with another art set (before/after comparisons).
ART = os.environ.get("AW_ART_DIR") or os.path.join(ROOT, "Assets", "_Aetherward", "Resources", "Art")
SETTINGS = json.load(open(os.environ.get("AW_SETTINGS") or os.path.join(ROOT, "Tools", "AssetGen", "import_settings.json")))
LIVE_REL = "Assets/_Aetherward/Resources/Art/"
W, H = 1920, 1080
ORTHO = 7.5
PX = H / (2 * ORTHO)
cache = {}


def sprite(rel):
    if rel not in cache:
        path = os.path.join(ART, rel + ".png")
        key = LIVE_REL + rel + ".png"   # settings are keyed by the live path, whatever ART points at
        img = Image.open(path).convert("RGBA")
        s = SETTINGS.get(key, {"ppu": 100, "pivot": [0.5, 0.5]})
        cache[rel] = (img, s["ppu"], s["pivot"])
    return cache[rel]


def to_px(x, y):
    return W / 2 + x * PX, H / 2 - y * PX


def draw(canvas, rel, x, y, scale=1.0, flip=False, alpha=1.0, rot=0.0, sx=None, sy=None):
    img, ppu, pivot = sprite(rel)
    units_w, units_h = img.width / ppu, img.height / ppu
    tw = max(1, int(units_w * PX * (sx if sx is not None else scale)))
    th = max(1, int(units_h * PX * (sy if sy is not None else scale)))
    im = img.resize((tw, th), Image.LANCZOS)
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if rot:
        im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    if alpha < 1.0:
        a = im.split()[3].point(lambda v: int(v * alpha))
        im.putalpha(a)
    cx, cy = to_px(x, y)
    px = cx - im.width * (pivot[0] if not rot else 0.5)
    py = cy - im.height * (1 - pivot[1] if not rot else 0.5)
    canvas.alpha_composite(im, (int(px), int(py)))


def main(snap_path, out_path):
    s = json.load(open(snap_path))
    canvas = Image.new("RGBA", (W, H), (40, 77, 61, 255))
    draw(canvas, os.environ.get("AW_BACKGROUND", "World/arena_background"), 0, 0)
    arena = json.loads("\n".join(l for l in open(os.path.join(ROOT, "Assets/_Aetherward/Resources/Content/arena.json")).read().splitlines()
                                 if not l.strip().startswith("//")))
    for n in arena["nodes"]:
        draw(canvas, "World/node_empty", n[0], n[1] - 0.05, alpha=0.35)
    zone_names = {"Magma": "magma", "Mud": "mud", "Thunderstorm": "thunderstorm", "Blizzard": "blizzard", "HealingRain": "healing_rain",
                  "Vortex": "vortex", "BurningGround": "burning_ground", "StormTrail": "storm_trail", "TempestLink": "tempest_link"}
    for z in s["zones"]:
        draw(canvas, "Vfx/zone_" + zone_names.get(z["kind"], "magma"), z["x"], z["y"], sx=z["r"], sy=z["r"] * 0.62, alpha=0.9)
    for st in s["strikes"]:
        draw(canvas, "Vfx/telegraph", st["x"], st["y"], sx=st["r"], sy=st["r"] * 0.62, alpha=0.7)
    units = []
    for h in s["heroes"]:
        pose = ("_evo" + h["evo"]) if h["evo"] else "_idle"
        units.append((h["y"], "hero", h, ("Heroes/" + h["id"] + (pose if h["alive"] else "_downed"))))
    for e in s["enemies"]:
        units.append((e["y"], "enemy", e, "Enemies/" + e["id"] + "_a"))
    units.append((-0.6, "crystal", {"x": 0, "y": -0.55}, "World/crystal_intact" if s["crystal"] > 0.6 else ("World/crystal_cracked" if s["crystal"] > 0.25 else "World/crystal_critical")))
    units.sort(key=lambda u: -u[0])
    for y, kind, u, rel in units:
        if kind == "crystal":
            draw(canvas, rel, u["x"], u["y"])
            continue
        draw(canvas, "World/shadow", u["x"], u["y"], scale=0.9 if kind == "hero" else 0.8, alpha=0.9)
        scale = 1.3 if kind == "enemy" and u.get("elite") and u["id"] != "ravager" and not u.get("boss") else 1.0
        draw(canvas, rel, u["x"], u["y"], scale=scale, flip=u["fx"] < -0.05)
        if kind == "enemy":
            img, ppu, piv = sprite(rel)
            top = u["y"] + img.height / ppu * scale * 0.88 + 0.08
            for k, st in enumerate([u["s1"], u["s2"]]):
                if st != "none":
                    icon = {"fire": "burn", "water": "wet", "lightning": "charged", "ice": "chill", "wind": "windmark", "earth": "armor_crack"}.get(st)
                    if icon is None or not os.path.exists(os.path.join(ART, "Icons/status_" + icon + ".png")):
                        continue
                    draw(canvas, "Icons/status_" + icon, u["x"] + (k - 0.5) * 0.4 * (1 if u["s2"] != "none" else 0), top + 0.15)
            if u["hp"] < 0.999 or u.get("elite") or u.get("boss"):
                cx, cy = to_px(u["x"], top)
                wpx = max(30, img.height / ppu * scale * 0.75 * PX)
                d = ImageDraw.Draw(canvas)
                d.rounded_rectangle([cx - wpx / 2, cy - 6, cx + wpx / 2, cy + 6], 5, fill=(20, 20, 40, 230))
                d.rounded_rectangle([cx - wpx / 2 + 2, cy - 4, cx - wpx / 2 + 2 + (wpx - 4) * u["hp"], cy + 4], 4, fill=(255, 82, 97, 255))
    for p in s["projectiles"]:
        rel = "Vfx/fireball" if p["visual"] == "fireball" else ("Vfx/arrow" if p["visual"] == "pierce_arrow" else "Vfx/projectile_" + (p["el"] if p["el"] != "none" else "earth"))
        draw(canvas, rel, p["x"], p["y"] + 0.55, rot=math.degrees(math.atan2(p["dy"], p["dx"])))
    d = ImageDraw.Draw(canvas)
    font_path = os.path.join(ROOT, "Assets/_Aetherward/Resources/Fonts/BeVietnamPro-Black.ttf")
    f = ImageFont.truetype(font_path, 34)
    small = ImageFont.truetype(font_path, 20)
    d.rounded_rectangle([W / 2 - 300, 12, W / 2 + 300, 108], 18, fill=(29, 33, 64, 220), outline=(255, 211, 90, 255), width=3)
    d.text((W / 2, 40), "WAVE %d / 20" % s["wave"], font=f, fill=(255, 211, 90, 255), anchor="mm")
    d.text((W / 2, 82), "t = %.1fs  ·  enemies %d" % (s["time"], len(s["enemies"])), font=small, fill=(220, 225, 240, 255), anchor="mm")
    d.text((16, H - 30), "OFFLINE COMPOSITE from simulator snapshot - not a Unity screenshot (HUD approximated)", font=small, fill=(255, 255, 255, 200))
    canvas.convert("RGB").save(out_path, quality=92)
    print("wrote", out_path)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
