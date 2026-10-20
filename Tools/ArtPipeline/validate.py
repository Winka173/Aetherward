#!/usr/bin/env python3
"""Aetherward Art Quality Validator.

Checks every runtime sprite against Tools/ArtPipeline/art_spec.json and writes per-asset JSON/CSV plus a
Markdown/HTML summary. Exit code 1 when a blocking defect remains (not covered by an unexpired waiver).
Numeric checks cannot judge aesthetics: every asset also gets a PENDING human-review slot, and contact sheets
(ap.py preview) are meant for that review.

Usage: python3 Tools/ArtPipeline/validate.py [--art DIR] [--settings F] [--manifest F] [--content DIR]
                                             [--scripts DIR] [--waivers F] [--out DIR] [--today YYYY-MM-DD]
"""
import argparse
import csv
import datetime
import html
import itertools
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artlib as A  # noqa: E402

ERROR, WARN, INFO = "error", "warning", "info"


class Report:
    def __init__(self):
        self.issues = []          # dicts: asset, check, severity, message, value
        self.assets = {}          # rel -> metrics
        self.globals = {}

    def add(self, asset, check, severity, message, value=None):
        self.issues.append({"asset": asset, "check": check, "severity": severity, "message": message,
                            "value": None if value is None else round(float(value), 4)})


def load_waivers(path, today):
    if not path or not os.path.exists(path):
        return []
    out = []
    for w in A.load_json(path).get("waivers", []):
        w = dict(w)
        w["expired"] = w.get("expires", "9999-12-31") < today
        out.append(w)
    return out


def waived(issue, waivers):
    for w in waivers:
        if w["check"] == issue["check"] and (w["asset"] == issue["asset"] or (w["asset"].endswith("*") and issue["asset"].startswith(w["asset"][:-1]))):
            return w
    return None


def category_of(rel):
    return rel.split("/")[0]


def run(args):
    spec = A.load_json(args.spec)
    th = spec["thresholds"]
    cats = spec["categories"]
    rep = Report()
    today = args.today or datetime.date.today().isoformat()

    # ------------------------------------------------------------------ inventory, manifest, metas, settings
    files = []
    for dp, _, fs in os.walk(args.art):
        for f in fs:
            if f.lower().endswith(".png"):
                files.append(os.path.relpath(os.path.join(dp, f), args.art).replace("\\", "/"))
    files.sort()
    root_rel = lambda r: os.path.relpath(os.path.join(args.art, r), A.ROOT).replace("\\", "/")  # noqa: E731
    settings = A.load_json(args.settings) if os.path.exists(args.settings) else {}
    manifest = A.load_json(args.manifest) if os.path.exists(args.manifest) else []
    man_by_path = {m["path"]: m for m in manifest}

    lower = defaultdict(list)
    for r in files:
        lower[r.lower()].append(r)
        stem = os.path.splitext(os.path.basename(r))[0].lower()
        lower["name:" + category_of(r).lower() + "/" + stem].append(r)
    for k, v in lower.items():
        if len(v) > 1:
            for r in v:
                rep.add(r, "duplicate_path", ERROR, "case-insensitive path/name collision: " + ", ".join(v))

    guids = defaultdict(list)
    for r in files:
        rr = root_rel(r)
        m = man_by_path.get(rr)
        if m is None:
            rep.add(r, "manifest_missing", ERROR, "no provenance entry in " + os.path.basename(args.manifest))
        elif not m.get("license"):
            rep.add(r, "license_missing", ERROR, "manifest entry has no license")
        if rr not in settings:
            rep.add(r, "import_settings_missing", ERROR, "no import settings (pivot/PPU) for this sprite")
        meta = os.path.join(args.art, r + ".meta")
        if not os.path.exists(meta):
            rep.add(r, "meta_missing", ERROR, "Unity .meta missing (run Tools/gen_meta.py)")
        else:
            mtext = A.read_text(meta)
            for line in mtext.splitlines():
                if line.startswith("guid:"):
                    guids[line.split(":", 1)[1].strip()].append(r)
            st = settings.get(rr)
            mp = A.META_PIVOT.search(mtext)
            mu = A.META_PPU.search(mtext)
            if st and mp and (abs(float(mp.group(1)) - st["pivot"][0]) > 1e-4 or abs(float(mp.group(2)) - st["pivot"][1]) > 1e-4):
                rep.add(r, "meta_settings_mismatch", ERROR, f".meta pivot ({mp.group(1)}, {mp.group(2)}) differs from import settings {st['pivot']} (run gen_meta --refresh-textures)")
            if st and mu and abs(float(mu.group(1)) - st.get("ppu", 100)) > 1e-4:
                rep.add(r, "meta_settings_mismatch", ERROR, f".meta PPU {mu.group(1)} differs from import settings {st.get('ppu')}")
    for g, rs in guids.items():
        if len(rs) > 1:
            for r in rs:
                rep.add(r, "duplicate_guid", ERROR, "GUID " + g + " shared by " + ", ".join(rs))
    art_root_rel = os.path.relpath(args.art, A.ROOT).replace("\\", "/")
    for m in manifest:
        if m["path"].startswith(art_root_rel + "/") and not os.path.exists(os.path.join(A.ROOT, m["path"])):
            rep.add(m["path"][len(art_root_rel) + 1:], "manifest_orphan", ERROR, "manifest lists a file that does not exist")

    # ------------------------------------------------------------------ per-image checks
    masks, imgs = {}, {}
    for r in files:
        cat = category_of(r)
        cs = cats.get(cat, {"kind": "other", "sizes": None})
        a, mode = A.load_rgba(os.path.join(args.art, r))
        h, w = a.shape[:2]
        mk = A.mask(a)
        opaque = float(mk.mean())
        met = {"category": cat, "w": w, "h": h, "opaque": round(opaque, 4), "bytesRGBA32": w * h * 4}
        rep.assets[r] = met
        if cs.get("sizes") and [w, h] not in cs["sizes"]:
            rep.add(r, "size_mismatch", ERROR, f"{w}x{h} not in {cs['sizes']}")
        if w % 4 or h % 4:
            rep.add(r, "block_alignment", WARN, f"{w}x{h} is not a multiple of 4 (ASTC/ETC2 blocks)")
        if mode not in ("RGBA", "LA", "PA") and not cs.get("opaqueOk"):
            rep.add(r, "no_alpha_channel", ERROR, "stored without alpha (" + mode + ")")
        if not (a[..., 3] > 0.02).any():
            rep.add(r, "empty_image", ERROR, "no visible pixels")
            continue
        if cs["kind"] in ("unit", "icon"):
            masks[r], imgs[r] = mk, a
            edge = np.concatenate([a[0, :, 3], a[-1, :, 3], a[:, 0, 3], a[:, -1, 3]])
            if (edge > 0.5).any() and not cs.get("allowBorder"):
                rep.add(r, "cropped_silhouette", ERROR, "opaque pixels touch the canvas edge (cropped)", float((edge > 0.5).mean()))
            else:
                bb = A.bbox(mk)
                margin = cs.get("safeMargin", 0)
                if bb and margin and (bb[0] < margin or bb[1] < margin or bb[2] > w - 1 - margin or bb[3] > h - 1 - margin) and not cs.get("allowBorder"):
                    rep.add(r, "outside_safe_bounds", WARN, f"silhouette within {margin}px of the edge")
            # White/light halo: semi-transparent rim pixels that are much brighter than the opaque body.
            rim = (a[..., 3] > 0.04) & (a[..., 3] < 0.5)
            if rim.sum() > 20:
                lum = A.luminance(a[..., :3])
                body = float(np.median(lum[mk])) if mk.any() else 0.0
                ratio = float(((lum > 0.85) & (lum > body + 0.3) & rim).sum() / rim.sum())
                met["haloRatio"] = round(ratio, 4)
                if ratio > th["haloFringeRatio"]:
                    rep.add(r, "white_halo", WARN, "bright fringe on semi-transparent edge (premultiply/bleed issue)", ratio)
            if cs["kind"] == "unit" and opaque < th["overdrawMinOpaque"]:
                # Unity "Tight" sprite meshes (no 9-slice border) skip most transparent pixels; FullRect pays for all.
                sset = settings.get(root_rel(r), {})
                tight = not any(sset.get("border", [0, 0, 0, 0]))
                rep.add(r, "overdraw_waste", INFO if tight else WARN,
                        f"only {opaque:.0%} of the quad is opaque" + (" (Tight mesh limits the fill cost)" if tight else " (FullRect mesh: fill-rate cost)"), opaque)
            # Lighting direction: shading rule is light from upper-left.
            if cs["kind"] == "unit" and mk.sum() > 400:
                bb = A.bbox(mk)
                cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
                lum = A.luminance(a[..., :3])
                yy, xx = np.mgrid[0:h, 0:w]
                tl = lum[mk & (xx < cx) & (yy < cy)]
                br = lum[mk & (xx > cx) & (yy > cy)]
                if len(tl) and len(br):
                    diff = float(br.mean() - tl.mean())
                    met["lightingBRminusTL"] = round(diff, 4)
                    if diff > th["lightingInversion"]:
                        rep.add(r, "lighting_direction", WARN, "lower-right brighter than upper-left (shading rule: light from upper-left)", diff)

    # ------------------------------------------------------------------ unit sets: frames, feet, scale, jumps, evolutions
    heroes = A.read_json(os.path.join(args.content, "heroes.json"))["heroes"] if os.path.exists(os.path.join(args.content, "heroes.json")) else []
    enemies = A.read_json(os.path.join(args.content, "enemies.json"))["enemies"] if os.path.exists(os.path.join(args.content, "enemies.json")) else []
    hero_frames = spec["unitSets"]["heroFrames"]
    present = set(files)
    for hd in heroes:
        for f in hero_frames:
            if f"Heroes/{hd['id']}_{f}.png" not in present:
                rep.add(f"Heroes/{hd['id']}_{f}.png", "missing_frame", ERROR, f"hero {hd['id']} has no '{f}' frame")
    for ed in enemies:
        for f in spec["unitSets"]["enemyFrames"]:
            if f"Enemies/{ed['id']}_{f}.png" not in present:
                rep.add(f"Enemies/{ed['id']}_{f}.png", "missing_frame", ERROR, f"enemy {ed['id']} has no '{f}' frame")
    for name, key in (("relics.json", "relics"), ("cards.json", "cards")):
        p = os.path.join(args.content, name)
        if os.path.exists(p):
            folder = "Relics" if key == "relics" else "Cards"
            for d in A.read_json(p)[key]:
                if f"{folder}/{d['id']}.png" not in present:
                    rep.add(f"{folder}/{d['id']}.png", "missing_reference", ERROR, f"{key[:-1]} '{d['id']}' has no icon (loaded by id at runtime)")
    if os.path.isdir(args.scripts):
        for ref, where in sorted(A.literal_art_refs(args.scripts).items()):
            if ref + ".png" not in present:
                rep.add(ref + ".png", "missing_reference", ERROR, "Unity script references a missing sprite: " + where[0])

    feet = {}
    for r in files:
        cat = category_of(r)
        if not cats.get(cat, {}).get("footRowFromPivot") or r not in masks or "_downed" in r:
            continue
        s = settings.get(root_rel(r))
        bb = A.bbox(masks[r])
        if not s or not bb:
            continue
        h = rep.assets[r]["h"]
        pivot_row = h - 1 - s["pivot"][1] * h
        feet[r] = bb[3] - pivot_row
        rep.assets[r]["footOffsetPx"] = round(feet[r], 1)
        rep.assets[r]["heightPx"] = bb[3] - bb[1] + 1
        if abs(feet[r]) > th["footTolerancePx"] * (h / 320.0 if cat == "Heroes" else h / 256.0):
            rep.add(r, "foot_pivot_mismatch", WARN, f"lowest opaque row is {feet[r]:+.0f}px from the pivot (units float or sink)", feet[r])

    for cat in ("Heroes", "Enemies"):
        hs = [(r, rep.assets[r]["heightPx"]) for r in feet if category_of(r) == cat and rep.assets[r]["h"] == (320 if cat == "Heroes" else 256)]
        if len(hs) > 4:
            med = float(np.median([v for _, v in hs]))
            for r, v in hs:
                if abs(v - med) / med > th["scaleOutlierPct"]:
                    rep.add(r, "scale_outlier", WARN, f"silhouette height {v}px vs category median {med:.0f}px", v / med)

    def frame_pair(r1, r2, thr, check):
        if r1 in masks and r2 in masks:
            v = A.iou(masks[r1], masks[r2])
            rep.assets[r2]["iouVs_" + os.path.basename(r1)[:-4]] = round(v, 4)
            if v < thr:
                rep.add(r2, check, WARN, f"silhouette IoU {v:.2f} vs {os.path.basename(r1)} (identity drift / pop)", v)
            return v
        return None

    evo_rows = []
    for hd in heroes:
        hid = hd["id"]
        base = f"Heroes/{hid}_idle.png"
        frame_pair(base, f"Heroes/{hid}_cast.png", th["frameJumpIoU"], "frame_jump")
        for b in ("A", "B"):
            frame_pair(f"Heroes/{hid}_evo{b}.png", f"Heroes/{hid}_evo{b}_cast.png", th["frameJumpIoU"], "frame_jump")
        # Evolution identity (P3): each branch must differ from the base AND from the other branch.
        pairs = [(base, f"Heroes/{hid}_evoA.png"), (base, f"Heroes/{hid}_evoB.png"), (f"Heroes/{hid}_evoA.png", f"Heroes/{hid}_evoB.png")]
        row = {"hero": hid}
        for p1, p2 in pairs:
            if p1 in masks and p2 in masks:
                v = A.iou(masks[p1], masks[p2])
                hd1, hd2 = A.hue_histogram(imgs[p1]), A.hue_histogram(imgs[p2])
                hue = float(0.5 * np.abs(hd1 - hd2).sum())
                val = float(0.5 * np.abs(A.value_histogram(imgs[p1]) - A.value_histogram(imgs[p2])).sum())
                tag = os.path.basename(p1)[len(hid) + 1:-4] + "~" + os.path.basename(p2)[len(hid) + 1:-4]
                row[tag] = {"iou": round(v, 3), "hueDist": round(hue, 3), "valueDist": round(val, 3)}
                if v > th["weakEvolutionIoU"] and hue < th["weakEvolutionHueDist"] and val < th["weakEvolutionValueDist"]:
                    rep.add(p2, "weak_evolution", WARN,
                            f"{tag}: silhouette IoU {v:.2f}, hue distance {hue:.2f}, value distance {val:.2f} — branch not visually distinct", v)
        evo_rows.append(row)
    rep.globals["evolutionDistinctness"] = evo_rows
    for ed in enemies:
        frame_pair(f"Enemies/{ed['id']}_a.png", f"Enemies/{ed['id']}_b.png", th["enemyFrameIoU"], "frame_jump")

    # Element signalling: hero art must carry its element hue.
    for hd in heroes:
        r = f"Heroes/{hd['id']}_idle.png"
        el = hd.get("element")
        if r not in imgs or el not in A.ELEMENTS:
            continue
        hist = A.hue_histogram(imgs[r])
        best = 0.0
        for c in A.ELEMENTS[el]:
            hue = A.rgb_hue(tuple(A.hex_rgb(c)))
            if hue is None:
                continue
            idx = int(hue * len(hist)) % len(hist)
            best = max(best, float(hist[idx] + hist[(idx - 1) % len(hist)] + hist[(idx + 1) % len(hist)]))
        rep.assets[r]["elementHueShare"] = round(best, 4)
        if best < 0.08:
            rep.add(r, "element_signal_weak", WARN, f"only {best:.0%} of saturated pixels near the {el} hue", best)

    # ------------------------------------------------------------------ readability vs battlefields and spell density
    bgs = [os.path.join(args.art, "World", f) for f in sorted(os.listdir(os.path.join(args.art, "World")))
           if f.startswith(("bg_", "arena_background")) and f.endswith(".png")] if os.path.isdir(os.path.join(args.art, "World")) else []
    fields = [os.path.join(args.art, "Vfx", f) for f in sorted(os.listdir(os.path.join(args.art, "Vfx")))
              if f.startswith("field_") and f.endswith(".png")] if os.path.isdir(os.path.join(args.art, "Vfx")) else []
    bg_lum = []
    for p in bgs:
        a, _ = A.load_rgba(p)
        hh, ww = a.shape[:2]
        centre = a[hh // 4: 3 * hh // 4, ww // 4: 3 * ww // 4, :3]   # where units fight
        bg_lum.append((os.path.basename(p), float(np.median(A.luminance(centre)))))
    spell_lum = []
    if fields and bg_lum:
        # Peak spell density: 4 overlapping field textures averaged over the darkest battlefield.
        acc = None
        for p in fields[:: max(1, len(fields) // 4)][:4]:
            a, _ = A.load_rgba(p)
            col = (a[..., :3] * a[..., 3:4]).reshape(-1, 3).mean(0) / max(1e-6, a[..., 3].mean())
            acc = col if acc is None else acc + col
        spell_lum.append(float(A.luminance((acc / 4)[None, :])[0]))
    rep.globals["battlefieldLuminance"] = bg_lum
    for r in files:
        if category_of(r) not in ("Heroes", "Enemies") or r not in imgs or "_downed" in r or not bg_lum:
            continue
        a = imgs[r]
        lum = A.luminance(a[..., :3])
        body = float(np.median(lum[masks[r]]))
        # Outer silhouette ring (ink outline) — what separates the unit from the floor.
        m = masks[r]
        ring = m & ~(np.roll(m, 3, 0) & np.roll(m, -3, 0) & np.roll(m, 3, 1) & np.roll(m, -3, 1))
        ring_l = float(np.median(lum[ring])) if ring.any() else body
        worst = min(max(A.contrast_ratio(body, bl), A.contrast_ratio(ring_l, bl)) for _, bl in bg_lum)
        rep.assets[r]["minBattlefieldContrast"] = round(worst, 3)
        if worst < th["minEdgeContrast"]:
            rep.add(r, "low_contrast_battlefield", WARN, f"body/outline contrast {worst:.2f}:1 on the least favourable battlefield", worst)
        if spell_lum:
            sc = A.contrast_ratio(body, spell_lum[0])
            rep.assets[r]["spellContrast"] = round(sc, 3)
            if sc < th["minSpellContrast"]:
                rep.add(r, "low_contrast_spells", WARN, f"body contrast {sc:.2f}:1 against dense spell fields", sc)

    # Colour-vision deficiency: element signal colours must stay distinguishable or carry a shape cue.
    cvd = []
    names = sorted(A.ELEMENTS)
    has_glyphs = all(f"Icons/element_{n}.png" in present for n in names)
    for kind in A.CVD:
        sim = {n: A.simulate_cvd(A.hex_rgb(A.ELEMENTS[n][0])[None, :], kind)[0] for n in names}
        for n1, n2 in itertools.combinations(names, 2):
            d = A.delta_e(sim[n1], sim[n2])
            if d < th["cvdMinDeltaE"]:
                cvd.append({"vision": kind, "pair": [n1, n2], "deltaE": round(d, 2)})
    rep.globals["cvdConfusablePairs"] = cvd
    rep.globals["elementGlyphIcons"] = has_glyphs
    for c in cvd:
        rep.add("Icons/element_*", "cvd_confusable", INFO if has_glyphs else WARN,
                f"{c['pair'][0]} vs {c['pair'][1]} ΔE {c['deltaE']} under {c['vision']}" + (" (element glyph icons provide a shape cue)" if has_glyphs else ""),
                c["deltaE"])

    # ------------------------------------------------------------------ budgets
    totals = defaultdict(int)
    for r, m in rep.assets.items():
        totals[m["category"]] += m["bytesRGBA32"]
    rep.globals["textureMB_RGBA32"] = {k: round(v / 1048576, 2) for k, v in sorted(totals.items())}
    hero_frames_bytes = [m["bytesRGBA32"] for r, m in rep.assets.items() if m["category"] == "Heroes"]
    if hero_frames_bytes:
        per_hero = sum(hero_frames_bytes) / max(1, len(heroes))
        rep.globals["heroWorkingSetMB_RGBA32"] = round(6 * per_hero / 1048576, 2)   # 6 deployed heroes, all frames
    for cat, mb in spec["budgetsMB"].items():
        if cat.startswith("_"):
            continue
        if totals.get(cat, 0) / 1048576 > mb:
            rep.add(cat + "/*", "texture_budget", WARN, f"{totals[cat] / 1048576:.1f} MB RGBA32 exceeds the {mb} MB budget", totals[cat] / 1048576)

    # ------------------------------------------------------------------ waivers and decisions
    waivers = load_waivers(args.waivers, today)
    for w in waivers:
        if w["expired"]:
            rep.add(w["asset"], "waiver_expired", ERROR, f"waiver for '{w['check']}' expired on {w['expires']}: {w.get('reason', '')}")
    for i in rep.issues:
        w = waived(i, waivers)
        i["waived"] = bool(w and not w["expired"] and i["check"] != "waiver_expired")
        if i["waived"]:
            i["waiver"] = w.get("reason", "")
    per_asset = defaultdict(list)
    for i in rep.issues:
        per_asset[i["asset"]].append(i)
    refine_checks = {"weak_evolution", "frame_jump", "scale_outlier", "low_contrast_battlefield", "low_contrast_spells",
                     "foot_pivot_mismatch", "white_halo", "element_signal_weak", "lighting_direction"}
    for r, m in rep.assets.items():
        iss = [i for i in per_asset.get(r, []) if not i["waived"]]
        if any(i["severity"] == ERROR for i in iss):
            m["decision"] = "REMAKE"
        elif any(i["check"] in refine_checks for i in iss):
            m["decision"] = "REFINE"
        else:
            m["decision"] = "KEEP"
        m["humanReview"] = "PENDING"
        m["issues"] = sorted({i["check"] for i in iss})
    return rep


def write(rep, out):
    os.makedirs(out, exist_ok=True)
    blocking = [i for i in rep.issues if i["severity"] == ERROR and not i["waived"]]
    warnings = [i for i in rep.issues if i["severity"] == WARN and not i["waived"]]
    doc = {"summary": {"assets": len(rep.assets), "blocking": len(blocking), "warnings": len(warnings),
                       "waived": sum(i["waived"] for i in rep.issues),
                       "decisions": {d: sum(1 for m in rep.assets.values() if m.get("decision") == d) for d in ("KEEP", "REFINE", "REMAKE")}},
           "globals": rep.globals, "issues": rep.issues, "assets": rep.assets}
    A.dump_json(doc, os.path.join(out, "report.json"), indent=1, ensure_ascii=False, sort_keys=True)
    with open(os.path.join(out, "assets.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["asset", "category", "w", "h", "opaque", "decision", "human_review", "issues"])
        for r, m in sorted(rep.assets.items()):
            wr.writerow([r, m["category"], m["w"], m["h"], m["opaque"], m.get("decision"), m.get("humanReview"), " ".join(m.get("issues", []))])
    with open(os.path.join(out, "issues.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["asset", "check", "severity", "waived", "value", "message"])
        for i in sorted(rep.issues, key=lambda i: (i["severity"] != ERROR, i["check"], i["asset"])):
            wr.writerow([i["asset"], i["check"], i["severity"], i["waived"], i["value"], i["message"]])
    by_check = defaultdict(lambda: [0, 0, 0])
    for i in rep.issues:
        k = by_check[(i["check"], i["severity"])]
        k[0] += 1
        k[1] += i["waived"]
    s = doc["summary"]
    md = ["# Art quality report", "",
          f"- Assets: **{s['assets']}** · blocking: **{s['blocking']}** · warnings: **{s['warnings']}** · waived: {s['waived']}",
          f"- Decisions (automated): KEEP {s['decisions']['KEEP']} · REFINE {s['decisions']['REFINE']} · REMAKE {s['decisions']['REMAKE']} · human review: PENDING for all (aesthetics are not scored numerically)",
          "", "## Issues by check", "| Check | Severity | Count | Waived |", "|---|---|---|---|"]
    for (c, sev), (n, wv, _) in sorted(by_check.items(), key=lambda kv: (kv[0][1] != ERROR, kv[0][0])):
        md.append(f"| {c} | {sev} | {n} | {wv} |")
    md += ["", "## Texture memory (RGBA32 upper bound, MB)", "| Category | MB |", "|---|---|"]
    for k, v in rep.globals.get("textureMB_RGBA32", {}).items():
        md.append(f"| {k} | {v} |")
    md += ["", "## Battlefield luminance (centre median)", ", ".join(f"{n} {l:.3f}" for n, l in rep.globals.get("battlefieldLuminance", []))]
    md += ["", "## Blocking issues (first 60)"] + [f"- `{i['asset']}` **{i['check']}**: {i['message']}" for i in blocking[:60]] + (["- none"] if not blocking else [])
    md += ["", "## Warnings (first 80)"] + [f"- `{i['asset']}` {i['check']}: {i['message']}" for i in warnings[:80]] + (["- none"] if not warnings else [])
    A.write_text(os.path.join(out, "summary.md"), "\n".join(md) + "\n")
    rows = "".join(f"<tr class='{html.escape(i['severity'])}'><td>{html.escape(i['asset'])}</td><td>{html.escape(i['check'])}</td>"
                   f"<td>{i['severity']}</td><td>{'yes' if i['waived'] else ''}</td><td>{html.escape(i['message'])}</td></tr>"
                   for i in sorted(rep.issues, key=lambda i: (i["severity"] != ERROR, i["check"], i["asset"])))
    A.write_text(os.path.join(out, "summary.html"), 
        "<!doctype html><meta charset='utf-8'><title>Art quality</title><style>body{font:14px system-ui;margin:16px}"
        "table{border-collapse:collapse}td,th{border:1px solid #888;padding:3px 6px}.error{background:#f8d0d0}.warning{background:#fbf0c8}</style>"
        f"<h1>Art quality</h1><p>{s['assets']} assets · {s['blocking']} blocking · {s['warnings']} warnings · {s['waived']} waived</p>"
        f"<table><tr><th>Asset</th><th>Check</th><th>Severity</th><th>Waived</th><th>Message</th></tr>{rows}</table>")
    return len(blocking)


def parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--art", default=A.ART)
    p.add_argument("--settings", default=A.SETTINGS)
    p.add_argument("--manifest", default=A.MANIFEST)
    p.add_argument("--content", default=A.CONTENT)
    p.add_argument("--scripts", default=A.UNITY_SCRIPTS)
    p.add_argument("--waivers", default=A.WAIVERS)
    p.add_argument("--spec", default=A.SPEC)
    p.add_argument("--out", default=os.path.join(A.ROOT, "Reports", "ArtQuality"))
    p.add_argument("--today", default=None)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    rep = run(args)
    n = write(rep, args.out)
    print(f"art-validate: {len(rep.assets)} assets, {n} blocking, "
          f"{sum(1 for i in rep.issues if i['severity'] == WARN and not i['waived'])} warnings -> {args.out}")
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
