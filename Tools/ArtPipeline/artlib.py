"""Shared helpers for the Aetherward art pipeline and Art Quality Validator (engine-free, deterministic).

Paths default to the repository layout but every entry point accepts overrides so tests can point the
validator at intentionally broken fixtures.
"""
import hashlib
import json
import os
import re

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ART = os.path.join(ROOT, "Assets", "_Aetherward", "Resources", "Art")
CONTENT = os.path.join(ROOT, "Assets", "_Aetherward", "Resources", "Content")
SETTINGS = os.path.join(ROOT, "Tools", "AssetGen", "import_settings.json")
MANIFEST = os.path.join(ROOT, "Docs", "ASSET_MANIFEST.json")
UNITY_SCRIPTS = os.path.join(ROOT, "Assets", "_Aetherward", "Scripts", "Unity")
WAIVERS = os.path.join(HERE, "waivers.json")
SPEC = os.path.join(HERE, "art_spec.json")

# Element signal colours (primary, secondary) — mirror of Tools/AssetGen/art/heroes.py ELEMENT.
ELEMENTS = {
    "fire": ("#ff5a2c", "#ffb230"), "water": ("#2f8cff", "#5fe0ff"), "lightning": ("#8c4dff", "#ffe14a"),
    "ice": ("#7fd8ff", "#e8fbff"), "wind": ("#2fd39a", "#c4ffd9"), "earth": ("#b9773a", "#8fc24a"),
    "light": ("#ffd84a", "#fff7cc"), "shadow": ("#a3306b", "#3a0f2c"), "nature": ("#3fa34d", "#b6ec6a"),
    "poison": ("#a8e030", "#6a2a9a"), "arcane": ("#ff5fd2", "#ffd6f6"), "void": ("#5146d9", "#140c38"),
}


def hex_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float64) / 255.0


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write_text(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump_json(obj, path, **kw):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, **kw)


def read_json(path):
    """JSON with // line comments (the content files use them)."""
    text = "\n".join(l for l in read_text(path).splitlines() if not l.strip().startswith("//"))
    return json.loads(text)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_rgba(path):
    """Returns float RGBA array in 0..1, plus the PIL mode the file was stored in."""
    im = Image.open(path)
    mode = im.mode
    return np.asarray(im.convert("RGBA"), dtype=np.float64) / 255.0, mode


def luminance(rgb):
    """Relative luminance (sRGB -> linear, Rec.709 weights). rgb: (...,3) in 0..1."""
    c = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    return c[..., 0] * 0.2126 + c[..., 1] * 0.7152 + c[..., 2] * 0.0722


def contrast_ratio(l1, l2):
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def mask(a, thr=0.5):
    return a[..., 3] >= thr


def bbox(m):
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def iou(m1, m2):
    if m1.shape != m2.shape:
        return 0.0
    u = np.logical_or(m1, m2).sum()
    return float(np.logical_and(m1, m2).sum() / u) if u else 1.0


def hue_histogram(a, bins=24):
    """Saturation-weighted hue histogram of opaque, reasonably saturated pixels (normalized)."""
    rgb, al = a[..., :3], a[..., 3]
    mx, mn = rgb.max(-1), rgb.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    sel = (al > 0.5) & (sat > 0.25) & (mx > 0.2)
    if not sel.any():
        return np.zeros(bins)
    r, g, b = rgb[..., 0][sel], rgb[..., 1][sel], rgb[..., 2][sel]
    d = (mx - mn)[sel] + 1e-9
    m = mx[sel]
    h = np.where(m == r, ((g - b) / d) % 6, np.where(m == g, (b - r) / d + 2, (r - g) / d + 4)) / 6.0
    hist, _ = np.histogram(h, bins=bins, range=(0, 1), weights=sat[sel])
    s = hist.sum()
    return hist / s if s else hist


def rgb_hue(rgb):
    r, g, b = rgb
    mx, mn = max(rgb), min(rgb)
    if mx == mn:
        return None
    d = mx - mn
    if mx == r:
        h = ((g - b) / d) % 6
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h / 6.0


# Colour-vision deficiency simulation (Machado et al. 2009, severity 1.0) applied in linear RGB.
CVD = {
    "protanopia": np.array([[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]]),
    "deuteranopia": np.array([[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]]),
    "tritanopia": np.array([[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]]),
}


def to_linear(rgb):
    return np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)


def to_srgb(lin):
    lin = np.clip(lin, 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)


def simulate_cvd(rgb, kind):
    return to_srgb(to_linear(rgb) @ CVD[kind].T)


def to_lab(rgb):
    lin = to_linear(np.asarray(rgb, dtype=np.float64))
    m = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = lin @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def delta_e(c1, c2):
    return float(np.linalg.norm(to_lab(c1) - to_lab(c2)))


META_PIVOT = re.compile(r"spritePivot: \{x: ([-0-9.e]+), y: ([-0-9.e]+)\}")
META_PPU = re.compile(r"spritePixelsToUnits: ([-0-9.e]+)")
ART_CALL = re.compile(r'Art\.(?:Tex|Sprite)\(\s*"([^"]+)"\s*\)')


def literal_art_refs(script_dir):
    """String-literal Art.Tex/Art.Sprite paths in Unity scripts (dynamic paths cannot be checked statically)."""
    refs = {}
    for dp, _, files in os.walk(script_dir):
        for f in files:
            if not f.endswith(".cs"):
                continue
            p = os.path.join(dp, f)
            for i, line in enumerate(read_text(p).splitlines(), 1):
                for m in ART_CALL.finditer(line):
                    refs.setdefault(m.group(1), []).append(os.path.relpath(p, ROOT) + ":" + str(i))
    return refs


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def value_histogram(a, bins=8):
    """Luminance histogram of opaque pixels (normalized) — value structure, independent of hue."""
    sel = a[..., 3] > 0.5
    if not sel.any():
        return np.zeros(bins)
    hist, _ = np.histogram(luminance(a[..., :3])[sel], bins=bins, range=(0, 1))
    return hist / hist.sum()


def icon_structure(path, size=48):
    """Z-normalised luminance of an icon at HUD size, composited on mid grey after deuteranopia simulation."""
    with Image.open(path) as im:
        a = np.asarray(im.convert("RGBA").resize((size, size), Image.LANCZOS), dtype=np.float64) / 255.0
    rgb = simulate_cvd(a[..., :3], "deuteranopia")
    comp = rgb * a[..., 3:] + 0.35 * (1 - a[..., 3:])
    lum = luminance(comp)
    return (lum - lum.mean()) / (lum.std() + 1e-6)


GUID_REF = re.compile(r"guid: ([0-9a-f]{32})")
RES_LOAD = re.compile(r'Resources\.Load<(\w+)>\(\s*"([^"]+)"\s*\)')
RES_EXT = {"Shader": (".shader",), "Font": (".ttf", ".otf"), "TextAsset": (".json", ".txt", ".bytes", ".csv"), "Texture2D": (".png",),
           "Sprite": (".png",), "AudioClip": (".wav", ".ogg", ".mp3"), "Material": (".mat",)}


def broken_guid_references(unity_root):
    """GUIDs referenced by serialized Unity files that no .meta defines (Unity built-ins 0000000000000000x... excluded)."""
    defined, refs = set(), []
    for dp, _, fs in os.walk(unity_root):
        for f in fs:
            p = os.path.join(dp, f)
            if f.endswith(".meta"):
                for line in read_text(p).splitlines()[:3]:
                    if line.startswith("guid:"):
                        defined.add(line.split(":", 1)[1].strip())
            elif f.endswith((".unity", ".prefab", ".mat", ".asset", ".controller", ".anim", ".spriteatlas")):
                for g in set(GUID_REF.findall(read_text(p))):
                    refs.append((os.path.relpath(p, unity_root).replace("\\", "/"), g))
    return [{"file": f, "guid": g} for f, g in sorted(refs) if g not in defined and not g.startswith("0000000000000000")]


def missing_resources(script_dir, resources_dir):
    out = []
    for dp, _, fs in os.walk(script_dir):
        for f in fs:
            if not f.endswith(".cs"):
                continue
            p = os.path.join(dp, f)
            for i, line in enumerate(read_text(p).splitlines(), 1):
                for m in RES_LOAD.finditer(line):
                    exts = RES_EXT.get(m.group(1))
                    if exts and not any(os.path.exists(os.path.join(resources_dir, m.group(2) + e)) for e in exts):
                        out.append((m.group(2), f"{os.path.relpath(p, ROOT)}:{i}"))
    return out


def atlas_bleed(page, rects, padding):
    """Pixels from one sprite inside another sprite's padding ring (texture bleeding risk). page: RGBA float array."""
    issues = []
    occ = page[..., 3] > 0.02
    for name, (x, y, w, h) in rects.items():
        x0, y0, x1, y1 = max(0, x - padding), max(0, y - padding), min(page.shape[1], x + w + padding), min(page.shape[0], y + h + padding)
        ring = np.zeros_like(occ)
        ring[y0:y1, x0:x1] = True
        ring[y:y + h, x:x + w] = False
        if (occ & ring).any():
            issues.append(name)
    return issues
