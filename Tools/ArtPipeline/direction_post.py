#!/usr/bin/env python3
"""Post-process the three direction benchmarks and add a combat-UI MOCKUP per direction.

  python3 Tools/ArtPipeline/direction_post.py

Inputs : Reports/ArtDirection/raw/{mythic,painterly,pixel}.png (Blender renders, Tools/ArtPipeline/blender/direction_benchmark.py)
Outputs: Reports/ArtDirection/benchmarks/{look}_1080p.png, {look}_720p.png, compare_all_720p.png, units_closeup.png
Every image is labelled: OFFLINE RENDER + UI MOCKUP (not a Unity screenshot). Hero portraits in the UI are crops of
the same render (projected from the scene's real hero positions), not separately painted art.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW = os.path.join(ROOT, "Reports", "ArtDirection", "raw")
OUT = os.path.join(ROOT, "Reports", "ArtDirection", "benchmarks")
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SANS = os.path.join(ROOT, "Assets", "_Aetherward", "Resources", "Fonts", "BeVietnamPro-SemiBold.ttf")

# Camera of direction_benchmark.py (keep in sync): ortho 19 wide, elevation 38°, target (0, 2.4, 1.0).
ORTHO, ELEV, TARGET = 19.0, math.radians(38), np.array([0.0, 2.4, 1.0])
HEROES = [("Guardian", (1.9, -1.6), "#4a8aff"), ("Pyromancer", (-2.6, -1.9), "#ff7a2a"), ("Ranger", (-3.4, 1.4), "#5adf6a"),
          ("Cleric", (-0.6, -3.0), "#ffe08a"), ("Shadowblade", (3.4, 1.0), "#c070ff"), ("Berserker", (0.7, 3.2), "#ff4a3a")]


def project(x, y, z, w, h):
    up = np.array([0.0, math.sin(ELEV), math.cos(ELEV)])
    p = np.array([x, y, z]) - TARGET
    sx = w / 2 + p[0] / ORTHO * w
    sy = h / 2 - float(p @ up) / (ORTHO * h / w) * h
    return sx, sy


def hexc(h, a=255):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def font(path, size):
    return ImageFont.truetype(path, size)


def denoise(im):
    """No OpenImageDenoiser in this Blender build: a light median + bilateral-ish blend (documented)."""
    med = im.filter(ImageFilter.MedianFilter(3))
    return Image.blend(im, med, 0.6)


def portraits(src, size):
    w, h = src.size
    out = []
    for name, (x, y), col in HEROES:
        cx, cy = project(x, y, 0.27 + 1.75, w, h)      # head height (heroes scaled 1.2 in the scene)
        r = h * 0.06
        crop = src.crop((int(cx - r), int(cy - r * 0.9), int(cx + r), int(cy + r * 1.1))).resize((size, size), Image.LANCZOS)
        out.append((name, crop, col))
    return out


def ui_mythic(img, style):
    """Dark mythic / painterly HUD: gilded frames, serif titles, boss bar, crystal bar, hero portraits with HP + skill rings."""
    w, h = img.size
    base = img.convert("RGBA")
    ov = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    gold = hexc("#c9a24a") if style == "mythic" else hexc("#e0b878")
    panel = (14, 12, 22, 210) if style == "mythic" else (40, 30, 24, 200)
    s = w / 1920
    # vignette for focus on the crystal
    yy, xx = np.mgrid[0:h, 0:w]
    v = np.clip(((xx - w / 2) / (w * 0.62)) ** 2 + ((yy - h * 0.55) / (h * 0.62)) ** 2, 0, 1) ** 1.6
    vig = Image.fromarray((v * (150 if style == "mythic" else 90)).astype(np.uint8), "L")
    base = Image.composite(Image.new("RGBA", base.size, (0, 0, 0, 255)), base, vig)
    # boss bar (top centre)
    bx0, bx1, by = w / 2 - 520 * s, w / 2 + 520 * s, 26 * s
    d.rounded_rectangle([bx0 - 6 * s, by - 6 * s, bx1 + 6 * s, by + 46 * s], 8 * s, fill=panel, outline=gold, width=max(2, int(3 * s)))
    d.rectangle([bx0, by + 18 * s, bx1, by + 38 * s], fill=(40, 10, 10, 230))
    d.rectangle([bx0, by + 18 * s, bx0 + (bx1 - bx0) * 0.72, by + 38 * s], fill=hexc("#c8381e"))
    d.text((w / 2, by + 9 * s), "MOLTEN COLOSSUS", font=font(SERIF, int(20 * s)), fill=gold, anchor="mm")
    # wave + crystal (top left)
    d.rounded_rectangle([20 * s, 20 * s, 420 * s, 118 * s], 10 * s, fill=panel, outline=gold, width=max(2, int(2 * s)))
    d.text((40 * s, 34 * s), "WAVE 20 / 20", font=font(SERIF, int(30 * s)), fill=gold)
    d.text((40 * s, 76 * s), "CRYSTAL", font=font(SANS, int(16 * s)), fill=(200, 230, 255, 255))
    d.rectangle([130 * s, 78 * s, 400 * s, 98 * s], fill=(10, 30, 45, 230))
    d.rectangle([130 * s, 78 * s, 130 * s + 270 * s * 0.64, 98 * s], fill=hexc("#3ad0ff"))
    # speed / pause (top right)
    for i, t in enumerate(("II", "2x")):
        x = w - (150 - i * 70) * s
        d.ellipse([x, 30 * s, x + 56 * s, 86 * s], fill=panel, outline=gold, width=max(2, int(2 * s)))
        d.text((x + 28 * s, 58 * s), t, font=font(SERIF, int(22 * s)), fill=gold, anchor="mm")
    # hero dock (bottom) with portraits cropped from the render
    ps = int(96 * s)
    ports = portraits(img, ps)
    x0 = w / 2 - (len(ports) * (ps + 18 * s)) / 2
    for i, (name, crop, col) in enumerate(ports):
        x, y = x0 + i * (ps + 18 * s), h - ps - 40 * s
        d.rounded_rectangle([x - 4 * s, y - 4 * s, x + ps + 4 * s, y + ps + 26 * s], 8 * s, fill=panel, outline=hexc(col), width=max(2, int(3 * s)))
        ov.paste(crop, (int(x), int(y)))
        d.rectangle([x, y + ps + 6 * s, x + ps, y + ps + 14 * s], fill=(30, 10, 10, 230))
        d.rectangle([x, y + ps + 6 * s, x + ps * (0.55 + 0.07 * i), y + ps + 14 * s], fill=hexc("#5ad06a"))
        d.arc([x + ps - 30 * s, y + 4 * s, x + ps - 4 * s, y + 30 * s], -90, -90 + 360 * (0.25 + 0.12 * i), fill=gold, width=max(2, int(4 * s)))
    # boss warning (telegraph callout) - top priority readability
    d.text((w / 2, by + 74 * s), "! SLAM INCOMING", font=font(SERIF, int(24 * s)), fill=hexc("#ff5a4a"), anchor="mm")
    out = Image.alpha_composite(base, ov)
    d2 = ImageDraw.Draw(out)
    d2.text((12 * s, h - 22 * s), "OFFLINE RENDER (Blender, procedural) + UI MOCKUP - not a Unity screenshot", font=font(SANS, int(15 * s)), fill=(255, 255, 255, 200))
    return out.convert("RGB")


def ui_pixel(img):
    """Pixel-art HUD drawn at the native 640x360 grid with a bitmap-style font, then scaled with the frame."""
    w, h = img.size
    base = img.convert("RGBA")
    d = ImageDraw.Draw(base)
    f = ImageFont.load_default()
    ink, gold, panel = (12, 10, 18, 255), (214, 172, 80, 255), (22, 18, 30, 235)
    def box(x0, y0, x1, y1):
        d.rectangle([x0, y0, x1, y1], fill=panel, outline=ink)
        d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], outline=gold)
    box(w / 2 - 170, 6, w / 2 + 170, 24)
    d.rectangle([w / 2 - 164, 16, w / 2 + 164, 21], fill=(60, 14, 14, 255))
    d.rectangle([w / 2 - 164, 16, w / 2 - 164 + 328 * 0.72, 21], fill=(200, 56, 30, 255))
    d.text((w / 2 - 44, 7), "MOLTEN COLOSSUS", font=f, fill=gold)
    box(6, 6, 132, 36)
    d.text((12, 9), "WAVE 20/20", font=f, fill=gold)
    d.rectangle([12, 24, 126, 30], fill=(10, 30, 45, 255))
    d.rectangle([12, 24, 12 + 114 * 0.64, 30], fill=(58, 208, 255, 255))
    ps = 30
    ports = portraits(img, ps)
    x0 = w / 2 - (len(ports) * (ps + 6)) / 2
    for i, (name, crop, col) in enumerate(ports):
        x, y = int(x0 + i * (ps + 6)), h - ps - 12
        box(x - 2, y - 2, x + ps + 1, y + ps + 7)
        base.paste(crop.quantize(16).convert("RGBA"), (x, y))
        d.rectangle([x, y + ps + 2, x + ps - 1, y + ps + 4], fill=(30, 10, 10, 255))
        d.rectangle([x, y + ps + 2, x + int((ps - 1) * (0.55 + 0.07 * i)), y + ps + 4], fill=(90, 208, 106, 255))
    d.text((w / 2 - 40, 28), "! SLAM INCOMING", font=f, fill=(255, 90, 74, 255))
    return base


def pixelize(img):
    """Palette quantisation (48 colours, no dithering) at native res; the frame is then scaled 3x nearest."""
    q = img.convert("RGB").quantize(colors=48, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    return q.convert("RGB")


def main():
    os.makedirs(OUT, exist_ok=True)
    results = {}
    for look in ("mythic", "painterly", "pixel"):
        p = os.path.join(RAW, look + ".png")
        if not os.path.exists(p):
            print("missing", p)
            continue
        im = Image.open(p).convert("RGB")
        if look == "pixel":
            ui = ui_pixel(pixelize(im))
            big = ui.convert("RGB").resize((1920, 1080), Image.NEAREST)
            d = ImageDraw.Draw(big)
            d.text((12, 1058), "OFFLINE RENDER (Blender, 640x360 native, palette-quantised, 3x nearest) + UI MOCKUP - not a Unity screenshot",
                   font=font(SANS, 15), fill=(255, 255, 255))
        else:
            im = denoise(im)
            big = ui_mythic(im.resize((1920, 1080), Image.LANCZOS), look)
        big.save(os.path.join(OUT, f"{look}_1080p.png"))
        small = big.resize((1280, 720), Image.LANCZOS if look != "pixel" else Image.NEAREST)
        small.save(os.path.join(OUT, f"{look}_720p.png"))
        results[look] = small
        print("benchmark ->", os.path.relpath(os.path.join(OUT, f"{look}_1080p.png"), ROOT))
    cur = os.path.join(ROOT, "Reports", "ArtRegeneration", "art_evidence", "scene_w20_bg_molten_crater_after.jpg")
    tiles = [("CURRENT (flat cartoon, offline composite)", Image.open(cur).convert("RGB").resize((1280, 720)) if os.path.exists(cur) else None)]
    tiles += [(n, results.get(k)) for k, n in (("mythic", "A. Dark Mythic Fantasy"), ("pixel", "B. Dark Fantasy Pixel Art"), ("painterly", "C. Painterly Dark Fantasy 2.5D"))]
    sheet = Image.new("RGB", (2560, 1500), (12, 12, 16))
    d = ImageDraw.Draw(sheet)
    for i, (name, t) in enumerate(tiles):
        x, y = (i % 2) * 1280, (i // 2) * 750
        if t is not None:
            sheet.paste(t, (x, y + 30))
        d.text((x + 10, y + 4), name + " — 720p", font=font(SANS, 22), fill=(240, 240, 240))
    sheet.save(os.path.join(OUT, "compare_all_720p.png"))
    print("compare ->", os.path.relpath(os.path.join(OUT, "compare_all_720p.png"), ROOT))
    # Mobile readability: the same frames at 640x360 (about what a phone shows of a 6" landscape screen at arm's
    # length), with the centre (crystal + hero ring) cropped back up 2x so silhouettes can be judged at that size.
    sheet = Image.new("RGB", (1280 * 2, 40 + len(tiles) * 380), (12, 12, 16))
    d = ImageDraw.Draw(sheet)
    d.text((10, 8), "Mobile readability: left = full frame at 640x360, right = centre of that 640x360 frame shown 2x (nearest)",
           font=font(SANS, 22), fill=(240, 240, 240))
    for i, (name, t) in enumerate(tiles):
        if t is None:
            continue
        y = 40 + i * 380
        m = t.resize((640, 360), Image.LANCZOS)
        sheet.paste(m, (0, y))
        sheet.paste(m.crop((160, 70, 480, 250)).resize((640, 360), Image.NEAREST), (660, y))
        d.text((1320, y + 10), name, font=font(SANS, 22), fill=(240, 240, 240))
    sheet.save(os.path.join(OUT, "units_closeup.png"))
    print("mobile ->", os.path.relpath(os.path.join(OUT, "units_closeup.png"), ROOT))


if __name__ == "__main__":
    main()
