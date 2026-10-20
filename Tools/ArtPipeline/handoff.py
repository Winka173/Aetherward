#!/usr/bin/env python3
"""Art handoff between the lead (Claude) and an art specialist agent (Codex) — requests, guides, intake.

  request --batch B01        expand ArtHandoff/requests/B01/batch.json into INPUT_MANIFEST.json (facts read from
                             the live project: size, PPU, pivot, border, .meta GUID, code references), copy the
                             current sprites to references/current/ and draw layout/scale guides into references/guides/
  intake  --batch B01        check ArtHandoff/returns/B01 against the request (manifest, files, size, alpha, foot row,
                             write scope), stage the returned exports over a copy of the live art in Temp/ArtStage-B01
                             and run the Art Quality Validator on that stage. Never touches Assets/.

Exit codes: 0 ok, 1 intake found blocking problems, 2 usage/input error. Run from the repository root.
"""
import argparse
import fnmatch
import glob
import json
import os
import re
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artlib as A  # noqa: E402

HANDOFF = os.path.join(A.ROOT, "ArtHandoff")
LIVE_REL = "Assets/_Aetherward/Resources/Art/"
ARENA = os.path.join(A.CONTENT, "arena.json")
FOOT_TOL_PX = 6
GUID = re.compile(r"^guid: ([0-9a-f]{32})", re.M)


def log(msg):
    print("[handoff] " + msg, flush=True)


def jsonc(path):
    text = A.read_text(path)
    text = re.sub(r"^\s*//.*$", "", text, flags=re.M)
    return json.loads(text)


def code_refs(asset):
    """Literal or pattern references to an Art-relative asset id in the Unity scripts (file:line)."""
    cat, name = asset.split("/", 1)
    head, _, tail = name.partition("_")
    keys = ['"' + asset + '"', '"' + cat + "/" + head + "_", '_' + tail + '"' if tail else None]
    out = []
    for p in sorted(glob.glob(os.path.join(A.UNITY_SCRIPTS, "**", "*.cs"), recursive=True)):
        for i, line in enumerate(A.read_text(p).splitlines(), 1):
            if any(k and k in line for k in keys) and ('"' + cat + "/") in line or keys[0] in line:
                out.append("%s:%d" % (os.path.relpath(p, A.ROOT).replace("\\", "/"), i))
    return out[:6]


def asset_facts(asset, settings):
    live = os.path.join(A.ART, asset + ".png")
    key = LIVE_REL + asset + ".png"
    if not os.path.exists(live):
        raise SystemExit("unknown asset id (no live file): " + asset)
    im = Image.open(live)
    s = settings.get(key, {})
    meta = A.read_text(live + ".meta")
    g = GUID.search(meta)
    w, h = im.size
    pivot = s.get("pivot", [0.5, 0.5])
    facts = {
        "id": asset,
        "livePath": key,
        "size": [w, h],
        "mode": im.mode,
        "ppu": s.get("ppu"),
        "pivot": pivot,
        "border": s.get("border", [0, 0, 0, 0]),
        "worldSize": [round(w / s["ppu"], 3), round(h / s["ppu"], 3)] if s.get("ppu") else None,
        "guid": g.group(1) if g else None,
        "codeRefs": code_refs(asset),
    }
    if asset.startswith(("Heroes/", "Enemies/")) or asset.startswith("World/crystal_"):
        facts["footRowFromTop"] = int(round(h - pivot[1] * h))
    if asset.startswith("Enemies/") and asset.rsplit("_", 1)[0][len("Enemies/"):] in flyers():
        facts["flyer"] = True   # params.flying: drawn lifted above the foot row; the shadow sprite marks the ground
    return facts


def flyers():
    return {e["id"] for e in jsonc(os.path.join(A.CONTENT, "enemies.json"))["enemies"] if (e.get("params") or {}).get("flying")}


# ------------------------------------------------------------------------------------------------ guides

def font(size):
    for f in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def layout_guide(path, size, ppu):
    """Battlefield guide at the background's own pixel grid: lanes, nodes, crystal, camera views."""
    arena = jsonc(ARENA)
    W, H = size
    img = Image.new("RGBA", (W, H), (24, 26, 30, 255))
    d = ImageDraw.Draw(img)

    def px(x, y):
        return W / 2 + x * ppu, H / 2 - y * ppu

    for gx in range(-15, 16):
        d.line([px(gx, -9), px(gx, 9)], fill=(48, 52, 60, 255), width=1)
    for gy in range(-9, 10):
        d.line([px(-16, gy), px(16, gy)], fill=(48, 52, 60, 255), width=1)
    # camera: orthographicSize = max(7.5, 13.2/aspect) -> visible rect per aspect
    for aspect, col, label in ((16 / 9, (90, 200, 255, 255), "16:9 view 26.7x15"), (20 / 9, (255, 200, 90, 255), "20:9 view"),
                               (4 / 3, (200, 120, 255, 255), "4:3 view")):
        half_h = max(7.5, 13.2 / aspect)
        half_w = half_h * aspect
        d.rectangle([px(-half_w, half_h), px(half_w, -half_h)], outline=col, width=3)
        d.text(px(-half_w + 0.15, half_h - 0.1), label, fill=col, font=font(22))
    lane_w = 1.3 * ppu
    for lane in arena["lanes"]:
        pts = [px(x, y) for x, y in lane["points"]] + [px(0, 0)]
        d.line(pts, fill=(200, 70, 60, 150), width=int(lane_w), joint="curve")
        d.line(pts, fill=(255, 120, 100, 255), width=3)
        sx, sy = pts[0]
        d.text((min(max(sx, 10), W - 160), min(max(sy, 10), H - 40)), "lane " + lane["id"], fill=(255, 170, 150, 255), font=font(24))
    # ground ellipses use y = 0.62 * radius (telegraphs, zones) -> the floor plane's projection ratio
    for i, (x, y) in enumerate(arena["nodes"]):
        cx, cy = px(x, y)
        rx, ry = 0.64 * ppu, 0.64 * 0.62 * ppu
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=(120, 255, 160, 255), width=3)
        d.text((cx - 8, cy - 12), str(i), fill=(120, 255, 160, 255), font=font(22))
        # hero stands here: 2.0 x 2.0 unit sprite, feet at the node
        d.rectangle([cx - 0.5 * ppu, cy - 1.75 * ppu, cx + 0.5 * ppu, cy], outline=(120, 255, 160, 90), width=1)
    cx, cy = px(0, -0.55)
    d.rectangle([cx - 1.0 * ppu, cy - 2.5 * ppu + 0.07 * 2.5 * ppu, cx + 1.0 * ppu, cy + 0.07 * 2.5 * ppu], outline=(120, 220, 255, 255), width=3)
    r = arena["crystalRadius"] * ppu
    d.ellipse([px(0, 0)[0] - r, px(0, 0)[1] - r * 0.62, px(0, 0)[0] + r, px(0, 0)[1] + r * 0.62], outline=(120, 220, 255, 255), width=3)
    d.text((cx + 1.05 * ppu, cy - 1.2 * ppu), "crystal sprite 2x2.5u, feet (0,-0.55)", fill=(120, 220, 255, 255), font=font(22))
    d.text((20, H - 60), "LAYOUT GUIDE (utility, not art). %dx%d px, PPU %d, origin = image centre. Red band = enemy path (keep flat & readable). "
           "Green = 12 hero nodes + standing box. Floor ellipse ratio 0.62." % (W, H, ppu), fill=(230, 230, 230, 255), font=font(22))
    img.save(path)


def unit_guide(path, facts, label):
    w, h = facts["size"]
    foot = facts["footRowFromTop"]
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline=(255, 255, 255, 160), width=1)
    d.line([(0, foot), (w, foot)], fill=(255, 80, 80, 255), width=2)
    d.line([(w / 2, 0), (w / 2, h)], fill=(80, 160, 255, 160), width=1)
    if facts["id"].startswith("Heroes/"):
        d.rectangle([40, 80, 360, 399], outline=(120, 255, 160, 200), width=2)   # HeroIcon crop box (UI/Ui.cs)
        # World/shadow is 1 x 0.375 units, scaled (0.95, 0.9) under heroes (WorldViews.cs)
        rx, ry = 0.95 * facts["ppu"] / 2, 0.375 * 0.9 * facts["ppu"] / 2
        d.ellipse([w / 2 - rx, foot - ry, w / 2 + rx, foot + ry], outline=(255, 200, 80, 200), width=1)
    d.text((4, 4), label, fill=(255, 255, 255, 230), font=font(12))
    d.text((4, foot + 2), "foot row y=%d (pivot)" % foot, fill=(255, 120, 120, 255), font=font(12))
    img.save(path)


def cmd_request(a):
    rq = os.path.join(HANDOFF, "requests", a.batch)
    spec = A.read_json(os.path.join(rq, "batch.json"))
    settings = A.read_json(A.SETTINGS)
    cur = os.path.join(rq, "references", "current")
    gd = os.path.join(rq, "references", "guides")
    os.makedirs(cur, exist_ok=True)
    os.makedirs(gd, exist_ok=True)
    groups = []
    for g in spec["groups"]:
        assets = []
        for pat in g["assets"]:
            hits = sorted(os.path.relpath(p, A.ART).replace("\\", "/")[:-4]
                          for p in glob.glob(os.path.join(A.ART, pat + ".png")))
            if not hits:
                raise SystemExit("pattern matches no live asset: " + pat)
            for asset in hits:
                f = asset_facts(asset, settings)
                dst = os.path.join(cur, asset.replace("/", "__") + ".png")
                shutil.copyfile(os.path.join(A.ART, asset + ".png"), dst)
                f["currentReference"] = os.path.relpath(dst, A.ROOT).replace("\\", "/")
                if "footRowFromTop" in f:
                    gp = os.path.join(gd, "unit__" + asset.replace("/", "__") + ".png")
                    unit_guide(gp, f, asset)
                    f["guide"] = os.path.relpath(gp, A.ROOT).replace("\\", "/")
                if asset.startswith("World/") and f["mode"] == "RGB":
                    gp = os.path.join(gd, "layout__" + asset.replace("/", "__") + ".png")
                    layout_guide(gp, f["size"], f["ppu"])
                    f["guide"] = os.path.relpath(gp, A.ROOT).replace("\\", "/")
                assets.append(f)
        groups.append(dict({k: v for k, v in g.items() if k != "assets"}, assets=assets))
    out = {"batch": a.batch, "generatedBy": "Tools/ArtPipeline/handoff.py request", "camera": spec.get("camera"),
           "groups": groups, "assetCount": sum(len(g["assets"]) for g in groups)}
    A.dump_json(out, os.path.join(rq, "INPUT_MANIFEST.json"), indent=1)
    log("%s: %d assets in %d groups -> INPUT_MANIFEST.json" % (a.batch, out["assetCount"], len(groups)))
    return 0


# ------------------------------------------------------------------------------------------------ preview

class ArtSet:
    """Sprites resolved through an optional overlay dir (returned exports) on top of the live art."""

    def __init__(self, overlay, settings):
        self.overlay, self.settings, self.cache = overlay, settings, {}

    def path(self, rel):
        if self.overlay and os.path.exists(os.path.join(self.overlay, rel + ".png")):
            return os.path.join(self.overlay, rel + ".png")
        return os.path.join(A.ART, rel + ".png")

    def get(self, rel):
        if rel not in self.cache:
            s = self.settings.get(LIVE_REL + rel + ".png", {"ppu": 100, "pivot": [0.5, 0.5]})
            self.cache[rel] = (Image.open(self.path(rel)).convert("RGBA"), s["ppu"], s["pivot"])
        return self.cache[rel]


def render_scene(art, layout, height, label):
    """Same camera maths as the Unity battle view: ortho 7.5 on 16:9, sprites at PPU/pivot, y-sorted."""
    W, H = height * 16 // 9, height
    px_u = H / 15.0
    arena = jsonc(ARENA)
    enemies = {e["id"]: e for e in jsonc(os.path.join(A.CONTENT, "enemies.json"))["enemies"]}
    canvas = Image.new("RGBA", (W, H), (20, 22, 26, 255))

    def put(rel, x, y, sx=1.0, sy=None, flip=False, alpha=1.0, rot=0.0, center=False):
        img, ppu, pivot = art.get(rel)
        tw = max(1, int(img.width / ppu * px_u * sx))
        th = max(1, int(img.height / ppu * px_u * (sy if sy is not None else sx)))
        im = img.resize((tw, th), Image.LANCZOS)
        if flip:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        if rot:
            im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
            center = True
        if alpha < 1.0:
            im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
        cx, cy = W / 2 + x * px_u, H / 2 - y * px_u
        ox = im.width * (0.5 if center else pivot[0])
        oy = im.height * (0.5 if center else 1 - pivot[1])
        canvas.alpha_composite(im, (int(cx - ox), int(cy - oy)))

    put(layout["background"], 0, 0)
    for i in layout.get("emptyNodes", []):
        n = arena["nodes"][i]
        put("World/node_empty", n[0], n[1] - 0.05, alpha=0.35)
    for f in layout["fx"]:
        if f.get("ground"):
            put(f["sprite"], f["x"], f["y"], sx=f["rx"], sy=f["rx"] * 0.62, alpha=f.get("alpha", 1.0))
    units = []
    for h in layout["heroes"]:
        n = arena["nodes"][h["node"]]
        units.append((n[1], "hero", h, n[0], n[1]))
    for e in layout["enemies"]:
        units.append((e["y"], "enemy", e, e["x"], e["y"]))
    c = layout["crystal"]
    units.append((c["y"], "crystal", c, c["x"], c["y"]))
    for _, kind, u, x, y in sorted(units, key=lambda t: -t[0]):
        if kind == "hero":
            put("World/shadow", x, y, sx=0.95, sy=0.9, alpha=0.9)
            put(u["sprite"], x, y, flip=u.get("flip", False))
        elif kind == "enemy":
            d = enemies.get(u["id"], {})
            sc = 1.25 if u.get("boss") else 1.0
            put("World/shadow", x, y, sx=(2.6 if u.get("boss") else 2.4) * d.get("radius", 0.35) * sc, sy=0.9 * sc, alpha=0.9)
            put("Enemies/%s_%s" % (u["id"], u["frame"]), x, y, sx=sc, flip=u.get("flip", False))
        else:
            put(u["sprite"], x, y)
    for f in layout["fx"]:
        if not f.get("ground"):
            put(f["sprite"], f["x"], f["y"], sx=f.get("scale", 1.0), rot=f.get("rot", 0.0), alpha=f.get("alpha", 1.0), center=True)
    d = ImageDraw.Draw(canvas)
    d.text((8, H - 22 if H < 900 else H - 30), label, fill=(255, 255, 255, 255), font=font(14 if H < 900 else 20))
    return canvas.convert("RGB")


def sheet(art, ids, height_px, mode):
    """Characters side by side at their on-screen size; mode = colour | silhouette | gray."""
    cells = []
    for rel in ids:
        img, ppu, pivot = art.get(rel)
        scale = (1.25 if img.width >= 512 else 1.0) * height_px / 15.0 / ppu
        im = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.LANCZOS)
        if mode == "silhouette":
            black = Image.new("RGBA", im.size, (0, 0, 0, 255))
            black.putalpha(im.getchannel("A").point(lambda v: 255 if v > 100 else 0))
            im = black
        elif mode == "gray":
            g = im.convert("LA").convert("RGBA")
            g.putalpha(im.getchannel("A"))
            im = g
        cells.append((rel, im))
    pad = 10
    W = sum(im.width for _, im in cells) + pad * (len(cells) + 1)
    H = max(im.height for _, im in cells) + 2 * pad + 16
    bg = (210, 210, 210, 255) if mode == "silhouette" else (34, 36, 40, 255)
    out = Image.new("RGBA", (W, H), bg)
    x = pad
    d = ImageDraw.Draw(out)
    for rel, im in cells:
        out.alpha_composite(im, (x, H - pad - 16 - im.height))
        d.text((x, H - 16), rel.split("/")[-1][:14], fill=(120, 120, 120, 255) if mode == "silhouette" else (200, 200, 200, 255), font=font(10))
        x += im.width + pad
    return out


def cmd_preview(a):
    rq = os.path.join(HANDOFF, "requests", a.batch)
    layout = A.read_json(os.path.join(rq, "benchmark_layout.json"))
    req = A.read_json(os.path.join(rq, "INPUT_MANIFEST.json"))
    art = ArtSet(a.overlay, A.read_json(A.SETTINGS))
    os.makedirs(a.out, exist_ok=True)
    tag = a.tag or ("overlay" if a.overlay else "live")
    note = "OFFLINE COMPOSITE (handoff.py preview, %s art) - not a Unity screenshot" % tag
    for h in (1080, 720):
        render_scene(art, layout, h, note).save(os.path.join(a.out, "scene_%s_%dp.png" % (tag, h)))
    chars = [f["id"] for g in req["groups"] for f in g["assets"] if f["id"].startswith(("Heroes/", "Enemies/", "World/crystal_"))]
    for mode in ("colour", "silhouette", "gray"):
        rows = [sheet(art, chars, h, mode) for h in (1080, 720)]
        W = max(r.width for r in rows)
        out = Image.new("RGBA", (W, sum(r.height for r in rows)), (0, 0, 0, 255))
        y = 0
        for r in rows:
            out.alpha_composite(r, (0, y))
            y += r.height
        out.convert("RGB").save(os.path.join(a.out, "units_%s_%s.png" % (tag, mode)))
    log("preview (%s) -> %s" % (tag, a.out))
    return 0


# ------------------------------------------------------------------------------------------------ intake

def lowest_opaque_row(im):
    alpha = im.getchannel("A")
    bbox = alpha.point(lambda v: 255 if v > 128 else 0).getbbox()
    return None if bbox is None else bbox[3] - 1


def cmd_intake(a):
    rq = os.path.join(HANDOFF, "requests", a.batch)
    rt = os.path.join(HANDOFF, "returns", a.batch)
    req = A.read_json(os.path.join(rq, "INPUT_MANIFEST.json"))
    mpath = os.path.join(rt, "DELIVERABLE_MANIFEST.json")
    if not os.path.exists(mpath):
        log("BLOCKED: no DELIVERABLE_MANIFEST.json in " + rt)
        return 1
    dm = A.read_json(mpath)
    delivered = {d["id"]: d for d in dm.get("assets", [])}
    problems, notes, rows = [], [], []
    stage = a.stage_dir or os.path.join(A.ROOT, "Temp", "ArtStage-" + a.batch)
    if os.path.exists(stage):
        shutil.rmtree(stage)
    shutil.copytree(A.ART, os.path.join(stage, "Art"), ignore=shutil.ignore_patterns("*.meta"))
    for g in req["groups"]:
        for f in g["assets"]:
            d = delivered.get(f["id"])
            row = {"id": f["id"], "group": g["id"], "status": "MISSING"}
            rows.append(row)
            if d is None:
                (problems if g.get("required", True) else notes).append(f["id"] + ": not in DELIVERABLE_MANIFEST")
                continue
            if d.get("status") in ("skipped", "blocked"):
                row["status"] = d["status"].upper()
                (problems if g.get("required", True) else notes).append("%s: %s (%s)" % (f["id"], d["status"], d.get("reason", "no reason")))
                continue
            p = os.path.join(rt, d.get("export", ""))
            if not d.get("export") or not os.path.isfile(p):
                problems.append(f["id"] + ": export file missing: " + str(d.get("export")))
                continue
            try:
                im = Image.open(p)
                im.load()
            except Exception as e:  # noqa: BLE001
                problems.append("%s: unreadable PNG (%s)" % (f["id"], e))
                continue
            row["status"] = "OK"
            if list(im.size) != f["size"]:
                problems.append("%s: size %s, contract %s" % (f["id"], list(im.size), f["size"]))
                row["status"] = "FAIL"
            if f["mode"] == "RGBA":
                if im.mode != "RGBA":
                    problems.append("%s: mode %s, needs RGBA" % (f["id"], im.mode))
                    row["status"] = "FAIL"
                elif im.getchannel("A").getextrema()[0] == 255:
                    problems.append(f["id"] + ": no transparent pixels (background not removed)")
                    row["status"] = "FAIL"
            if "footRowFromTop" in f and im.mode == "RGBA":
                low = lowest_opaque_row(im)
                row["footRow"] = low
                if f.get("flyer"):
                    # lifted at least 10% of the canvas, never below the ground line
                    if low is None or low > f["footRowFromTop"] - 0.10 * f["size"][1]:
                        problems.append("%s: flyer lowest row %s must be >= %d px above the foot row %d" % (
                            f["id"], low, int(0.10 * f["size"][1]), f["footRowFromTop"]))
                        row["status"] = "FAIL"
                elif low is None or abs(low - f["footRowFromTop"]) > FOOT_TOL_PX + (12 if "downed" in f["id"] else 0):
                    problems.append("%s: lowest opaque row %s, pivot row %d (tol %d)" % (f["id"], low, f["footRowFromTop"], FOOT_TOL_PX))
                    row["status"] = "FAIL"
            for k in ("source", "generator"):
                if not d.get(k):
                    notes.append("%s: manifest has no '%s'" % (f["id"], k))
            if row["status"] == "OK":
                dst = os.path.join(stage, "Art", f["id"] + ".png")
                im.save(dst)
    # write scope: nothing outside ArtHandoff/returns/<batch> may change
    r = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=A.ROOT, capture_output=True, text=True)
    stray = [ln[3:].strip('"') for ln in r.stdout.splitlines()]
    stray = [s for s in stray if s and not s.startswith(("ArtHandoff/returns/" + a.batch + "/", "Temp/"))
             and not any(fnmatch.fnmatch(s, pat) for pat in (a.allow or []))]
    report = {"batch": a.batch, "delivered": len(delivered), "requested": sum(len(g["assets"]) for g in req["groups"]),
              "blocking": problems, "notes": notes, "rows": rows, "strayWorkingTreeChanges": stray, "stage": os.path.relpath(stage, A.ROOT)}
    qa = a.qa_dir or os.path.join(A.ROOT, "ArtProduction", "reviews", a.batch)
    os.makedirs(qa, exist_ok=True)
    A.dump_json(report, os.path.join(qa, "intake.json"), indent=1)
    log("%d/%d delivered, %d blocking, %d notes, %d stray changes -> %s" % (
        report["delivered"], report["requested"], len(problems), len(notes), len(stray), os.path.relpath(qa, A.ROOT)))
    for p in problems[:40]:
        log("  BLOCK " + p)
    if a.validate:
        ok_ids = [r_["id"] for r_ in rows if r_["status"] == "OK"]
        v = subprocess.run([sys.executable, os.path.join(A.HERE, "validate.py"), "--art", os.path.join(stage, "Art"),
                            "--out", os.path.join(qa, "validator"), "--only"] + ok_ids, cwd=A.ROOT)
        log("validator exit %d -> %s" % (v.returncode, os.path.join(qa, "validator")))
    return 1 if problems else 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("request")
    r.add_argument("--batch", required=True)
    i = sub.add_parser("intake")
    i.add_argument("--batch", required=True)
    i.add_argument("--validate", action="store_true", help="also run validate.py on the stage")
    i.add_argument("--allow", nargs="*", help="extra working-tree paths (fnmatch) that may have changed")
    i.add_argument("--stage-dir", default=None, help="default Temp/ArtStage-<batch>")
    i.add_argument("--qa-dir", default=None, help="default ArtProduction/reviews/<batch>")
    v = sub.add_parser("preview")
    v.add_argument("--batch", required=True)
    v.add_argument("--overlay", default=None, help="Art-root-shaped dir whose PNGs replace live ones (e.g. ArtHandoff/returns/B01/exports/Art)")
    v.add_argument("--out", required=True)
    v.add_argument("--tag", default=None)
    a = p.parse_args()
    return {"request": cmd_request, "intake": cmd_intake, "preview": cmd_preview}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
