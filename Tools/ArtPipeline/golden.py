#!/usr/bin/env python3
"""Golden-sample evidence sheets (before/after at real on-screen sizes). Read-only on the project.

  python3 Tools/ArtPipeline/golden.py --before Temp/ArtEvidence/Assets/_Aetherward/Resources/Art \
      --before-settings Temp/ArtEvidence/Tools/AssetGen/import_settings.json

Produces Reports/ArtRegeneration/art_evidence/golden_*.png:
  hero (all 7 frames), crystal damage states, boss frames + telegraph decal, card art at draft-panel size,
  status icons under colour-vision simulation. Sizes use the battle camera (15 world units tall) at 720p/1080p.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artlib as A  # noqa: E402

OUT = os.path.join(A.ROOT, "Reports", "ArtRegeneration", "art_evidence")
LIVE = "Assets/_Aetherward/Resources/Art/"


def load(art, rel):
    p = os.path.join(art, rel + ".png")
    return Image.open(p).convert("RGBA") if os.path.exists(p) else None


def at_screen(img, ppu, height):
    k = (height / 15.0) / ppu
    return img.resize((max(1, round(img.width * k)), max(1, round(img.height * k))), Image.LANCZOS)


def sheet(rows, title, out, bg=(52, 56, 74)):
    """rows: list of (label, [(caption, image)])."""
    cw = max(max((im.width for _, im in r) if r else [0]) for _, r in rows) + 24
    ch = max(max((im.height for _, im in r) if r else [0]) for _, r in rows) + 40
    cols = max(len(r) for _, r in rows)
    s = Image.new("RGB", (240 + cols * cw, 40 + len(rows) * ch), bg)
    d = ImageDraw.Draw(s)
    d.text((8, 10), title, fill=(240, 240, 240))
    for i, (label, items) in enumerate(rows):
        y = 40 + i * ch
        d.text((8, y + ch // 2), label, fill=(220, 220, 220))
        for j, (cap, im) in enumerate(items):
            x = 240 + j * cw
            d.text((x, y), cap, fill=(200, 200, 210))
            s.paste(im, (x + (cw - im.width) // 2, y + 16 + (ch - 16 - im.height)), im)
    os.makedirs(OUT, exist_ok=True)
    s.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", required=True)
    ap.add_argument("--before-settings", required=True)
    ap.add_argument("--hero", default="ignis")
    ap.add_argument("--boss", default="nyxhollow")
    a = ap.parse_args()
    sets = {"before": (a.before, A.load_json(a.before_settings)), "after": (A.ART, A.load_json(A.SETTINGS))}
    written = []

    # 1) Hero: every frame at 1080p and 720p on-screen size.
    rows = []
    for tag, (art, st) in sets.items():
        for hgt in (1080, 720):
            items = []
            for fr in ("idle", "cast", "evoA", "evoA_cast", "evoB", "evoB_cast", "downed"):
                rel = f"Heroes/{a.hero}_{fr}"
                im = load(art, rel)
                if im is not None:
                    items.append((fr, at_screen(im, st[LIVE + rel + ".png"]["ppu"], hgt)))
            rows.append((f"{tag} {hgt}p", items))
    written.append(sheet(rows, f"Golden hero '{a.hero}': all frames at on-screen size (before = baseline commit, after = pipeline)",
                         os.path.join(OUT, f"golden_hero_{a.hero}.png")))

    # 2) Crystal damage states on the darkest and brightest battlefields.
    bgs = {n: Image.open(os.path.join(A.ART, "World", n + ".png")).convert("RGBA") for n in ("bg_molten_crater", "bg_frostfall_bastion")}
    rows = []
    for tag, (art, st) in sets.items():
        items = []
        for state in ("intact", "cracked", "critical"):
            rel = f"World/crystal_{state}"
            im = at_screen(load(art, rel), st[LIVE + rel + ".png"]["ppu"], 1080)
            for bn, bg in bgs.items():
                w, h = bg.size
                tile = bg.crop((w // 2 - 200, h // 2 - 200, w // 2 + 200, h // 2 + 200)).resize((im.width + 40, im.height + 30))
                tile.alpha_composite(im, (20, 15))
                items.append((f"{state}/{bn[3:9]}", tile))
        rows.append((tag, items))
    written.append(sheet(rows, "Golden crystal: damage states on darkest/brightest biome, 1080p size", os.path.join(OUT, "golden_crystal.png")))

    # 3) Boss frames + telegraph decal.
    rows = []
    for tag, (art, st) in sets.items():
        items = []
        for fr in ("a", "b"):
            rel = f"Enemies/{a.boss}_{fr}"
            items.append((fr, at_screen(load(art, rel), st[LIVE + rel + ".png"]["ppu"], 1080)))
        tel = load(art, "Vfx/telegraph")
        items.append(("telegraph", tel.resize((tel.width // 2, tel.height // 2))))
        rows.append((tag, items))
    written.append(sheet(rows, f"Golden boss '{a.boss}' (frames a/b) + telegraph decal; death = Unity fade (not a sprite)", os.path.join(OUT, "golden_boss.png")))

    # 4) Card art at the draft-panel size (160 virtual px of 1080) at 1080p and 720p.
    cards = sorted(f[:-4] for f in os.listdir(os.path.join(A.ART, "Cards")) if f.endswith(".png"))[:8]
    rows = []
    for tag, (art, _) in sets.items():
        for hgt in (1080, 720):
            px = round(160 * hgt / 1080)
            rows.append((f"{tag} {hgt}p", [(c[:10], load(art, "Cards/" + c).resize((px, px), Image.LANCZOS)) for c in cards]))
    written.append(sheet(rows, "Card art at draft-panel size (panel itself is IMGUI: needs Unity to capture)", os.path.join(OUT, "golden_draft_cards.png")))

    # 5) Status icons under colour-vision simulation (must differ by shape, not only hue).
    icons = sorted(f[:-4] for f in os.listdir(os.path.join(A.ART, "Icons")) if f.startswith("status_") and f.endswith(".png"))
    rows = []
    for kind in ("normal", "deuteranopia", "protanopia", "tritanopia"):
        items = []
        for ic in icons[:14]:
            im = load(A.ART, "Icons/" + ic).resize((48, 48), Image.LANCZOS)
            if kind != "normal":
                arr = np.asarray(im, dtype=np.float64) / 255.0
                rgb = A.simulate_cvd(arr[..., :3], kind)
                im = Image.fromarray((np.dstack([rgb, arr[..., 3:]]) * 255).clip(0, 255).astype(np.uint8), "RGBA")
            items.append((ic[7:15], im))
        rows.append((kind, items))
    written.append(sheet(rows, "Status icons at HUD size under colour-vision simulation", os.path.join(OUT, "golden_status_cvd.png")))
    for w in written:
        print("golden ->", os.path.relpath(w, A.ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
