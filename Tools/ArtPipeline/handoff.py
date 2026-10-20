#!/usr/bin/env python3
"""Art handoff between the lead (Claude) and an art specialist agent (Codex) — requests, guides, intake.

  request --batch B01        expand ArtHandoff/requests/B01/batch.json into INPUT_MANIFEST.json (facts read from
                             the live project: size, PPU, pivot, border, .meta GUID, code references), copy the
                             draw layout/scale guides into references/guides/ (current sprites are referenced by live path)
  brief   --batch B02        write CODEX_ART_REQUEST.md from batch.json + COMMON_CONTRACT + game data + ArtProduction/designs
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


def biome_for_background(asset):
    for b in jsonc(os.path.join(A.CONTENT, "biomes.json"))["biomes"]:
        if b.get("background") == asset:
            return b
    return None


def layout_guide(path, size, ppu, biome=None):
    """Battlefield guide at the background's own pixel grid: lanes, nodes, crystal, camera views,
    plus the biome's hazard points, special nodes and covers when the biome has its own arena."""
    arena = biome["arena"] if biome and isinstance(biome.get("arena"), dict) else jsonc(ARENA)
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
    if biome:
        special = {t["node"]: t["trait"] for t in biome.get("nodeTraits", [])}
        for i, tr in special.items():
            x, y = arena["nodes"][i]
            d.text((px(x, y)[0] + 30, px(x, y)[1] - 10), tr, fill=(255, 230, 120, 255), font=font(20))
        for hz in biome.get("hazards", []):
            for x, y in hz.get("points", []):
                r = hz.get("radius", 1.0) * ppu
                c = px(x, y)
                d.ellipse([c[0] - r, c[1] - r * 0.62, c[0] + r, c[1] + r * 0.62], outline=(255, 170, 40, 255), width=3)
                d.text((c[0] - r, c[1] - r * 0.62 - 24), hz["kind"], fill=(255, 170, 40, 255), font=font(18))
        for cv in biome.get("covers", []):
            c, r = px(*cv["pos"]), cv["radius"] * ppu
            d.ellipse([c[0] - r, c[1] - r * 0.62, c[0] + r, c[1] + r * 0.62], outline=(160, 220, 255, 255), width=3)
            d.text((c[0] - r, c[1] + r * 0.62), "cover", fill=(160, 220, 255, 255), font=font(18))
        for ls in biome.get("laneSchedule", []):
            lane = arena["lanes"][ls["lane"]]
            d.text(px(*lane["points"][1]), "opens at wave %d" % ls["opensAt"], fill=(255, 255, 255, 255), font=font(20))
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
    gd = os.path.join(rq, "references", "guides")
    os.makedirs(gd, exist_ok=True)
    groups = []
    for g in spec["groups"]:
        assets = []
        for pat in g.get("assets", []):
            hits = sorted(os.path.relpath(p, A.ART).replace("\\", "/")[:-4]
                          for p in glob.glob(os.path.join(A.ART, pat + ".png")))
            if not hits:
                raise SystemExit("pattern matches no live asset: " + pat)
            for asset in hits:
                f = asset_facts(asset, settings)
                f["currentReference"] = f["livePath"]
                if "footRowFromTop" in f:
                    gp = os.path.join(gd, "unit__" + asset.replace("/", "__") + ".png")
                    unit_guide(gp, f, asset)
                    f["guide"] = os.path.relpath(gp, A.ROOT).replace("\\", "/")
                if asset.startswith("World/") and f["mode"] == "RGB":
                    gp = os.path.join(gd, "layout__" + asset.replace("/", "__") + ".png")
                    layout_guide(gp, f["size"], f["ppu"], biome_for_background(asset))
                    f["guide"] = os.path.relpath(gp, A.ROOT).replace("\\", "/")
                assets.append(f)
        # new animation frames: the contract (size/PPU/pivot/border) is copied from a live sibling ("like")
        for n in g.get("new", []):
            f = asset_facts(n["like"], settings)
            f.update({"id": n["id"], "livePath": LIVE_REL + n["id"] + ".png", "guid": None, "codeRefs": [], "new": True, "like": n["like"]})
            f["currentReference"] = LIVE_REL + n["like"] + ".png"
            if "footRowFromTop" in f:
                gp = os.path.join(gd, "unit__" + n["id"].replace("/", "__") + ".png")
                unit_guide(gp, f, n["id"] + " (new)")
                f["guide"] = os.path.relpath(gp, A.ROOT).replace("\\", "/")
            assets.append(f)
        groups.append(dict({k: v for k, v in g.items() if k not in ("assets", "new")}, assets=assets))
    out = {"batch": a.batch, "generatedBy": "Tools/ArtPipeline/handoff.py request", "camera": spec.get("camera"),
           "groups": groups, "assetCount": sum(len(g["assets"]) for g in groups)}
    A.dump_json(out, os.path.join(rq, "INPUT_MANIFEST.json"), indent=1)
    log("%s: %d assets in %d groups -> INPUT_MANIFEST.json" % (a.batch, out["assetCount"], len(groups)))
    return 0


# ------------------------------------------------------------------------------------------------ brief

DESIGNS = os.path.join(A.ROOT, "ArtProduction", "designs")
ROLE_SHAPES = {
    "guardian": "wide trapezoid, >= 1.35x a mage's width, shield or slab mass, low centre of gravity, heavy pauldrons",
    "bruiser": "inverted triangle, huge arms or weapon, forward-leaning stance",
    "mage": "tall triangle (robe flares to the floor), staff or focus rising above the head",
    "healer": "vertical and calm, halo / orbiting ring / aura element above or behind the shoulders",
    "support": "vertical and calm, halo / orbiting ring / aura element above or behind the shoulders",
    "ranger": "narrow body, long diagonal bow line or long weapon, light cloak, stance turned sideways",
    "assassin": "compact, crouched and low, angled blades, scarf or sash tails for speed",
    "controller": "asymmetric, floating objects, ribbons or chains around the body",
}
ENEMY_SUFFIXES = ("_attack", "_tell", "_a", "_b")


class Content:
    def __init__(self):
        c = A.CONTENT
        loc = jsonc(os.path.join(c, "loc_en.json"))
        self.loc = loc.get("entries", loc)
        self.heroes = {h["id"]: h for h in jsonc(os.path.join(c, "heroes.json"))["heroes"]}
        ev = jsonc(os.path.join(c, "evolutions.json"))
        self.evos = {e["id"]: e for e in ev.get("evolutions", ev)}
        self.enemies = {e["id"]: e for e in jsonc(os.path.join(c, "enemies.json"))["enemies"]}
        self.hero_design = A.read_json(os.path.join(DESIGNS, "heroes.json"))
        self.enemy_design = A.read_json(os.path.join(DESIGNS, "enemies.json"))

    def t(self, key, default=""):
        return str(self.loc.get(key, default)).replace("\n", " ")


def subject(asset_id):
    cat, name = asset_id.split("/", 1)
    if cat in ("Heroes", "Portraits"):
        return cat, name.split("_")[0]
    if cat == "Enemies":
        for suf in ENEMY_SUFFIXES:
            if name.endswith(suf):
                return cat, name[: -len(suf)]
    return cat, name


def frame_table(assets):
    rows = ["| Asset | Size | PPU | Foot row | Status | Current ref (size/purpose only) |", "|---|---|---|---|---|---|"]
    for f in assets:
        foot = str(f.get("footRowFromTop", "-")) + (" (flyer: lift >= 10%)" if f.get("flyer") else "")
        status = "**new** (like `%s`)" % f["like"] if f.get("new") else "redraw"
        rows.append("| `%s` | %dx%d | %s | %s | %s | `%s` |" % (f["id"], f["size"][0], f["size"][1], f["ppu"], foot, status,
                                                              f["currentReference"]))
    return "\n".join(rows)


def hero_block(C, hid, assets):
    h = C.heroes[hid]
    d = C.hero_design.get(hid, {})
    role = h["role"]
    out = ["#### %s — \"%s\" (`%s`)" % (C.t("hero.%s.name" % hid, hid), C.t("hero.%s.title" % hid), hid),
           "- Data: element **%s**, role **%s**, %s, silhouette note \"%s\"." % (h["element"], role, "melee" if h.get("melee") else "ranged",
                                                                             h.get("silhouette", "")),
           "- Role shape: " + ROLE_SHAPES.get(role, ""),
           "- Base design: " + d.get("base", "(lead: missing design)")]
    for slot, eid in zip(("evoA", "evoB"), h.get("evolutions", [])):
        e = C.evos.get(eid, {})
        rc = e.get("role")
        out.append("- %s = **%s**%s — %s Design: %s" % (
            slot, C.t("evo.%s.name" % eid, eid), (" (becomes **%s**: %s)" % (rc, ROLE_SHAPES.get(rc, ""))) if rc else "",
            C.t("evo.%s.desc" % eid), d.get(slot, "(lead: missing design)")))
    out += ["", frame_table(assets), ""]
    return out


def enemy_block(C, eid, assets):
    e = C.enemies[eid]
    d = C.enemy_design.get(eid, {})
    tags = [t for t in e.get("tags", [])]
    out = ["#### %s (`%s`)%s" % (C.t("enemy.%s.name" % eid, eid), eid, " — BOSS" if e.get("boss") else ""),
           "- Data: behaviour **%s**, tags %s, radius %s. \"%s\"" % (e.get("behavior"), ", ".join(tags), e.get("radius"), C.t("enemy.%s.desc" % eid)),
           "- Size class: **%s**. Design: %s" % (d.get("size", "?"), d.get("design", "(lead: missing design)")), "", frame_table(assets), ""]
    return out


LOC_KEYS = {"Cards": ("card.%s.name", "card.%s.desc"), "Relics": ("relic.%s.name", "relic.%s.desc")}


def generic_rows(C, assets):
    rows = ["| Asset | Size | PPU | 9-slice | Meaning (from game data) | Current ref |", "|---|---|---|---|---|---|"]
    for f in assets:
        cat, name = f["id"].split("/", 1)
        meaning = ""
        if cat in LOC_KEYS:
            meaning = "%s — %s" % (C.t(LOC_KEYS[cat][0] % name, name), C.t(LOC_KEYS[cat][1] % name))
        elif cat == "Icons":
            kind, _, key = name.partition("_")
            meaning = {"element": lambda: C.t("element." + key, key) + " element",
                       "reaction": lambda: "%s — %s" % (C.t("reaction.%s.name" % key, key), C.t("reaction.%s.desc" % key)),
                       "status": lambda: "%s — %s" % (C.t("status." + key, key), C.t("status.%s.desc" % key)),
                       "trait": lambda: "%s — %s" % (C.t("trait.%s.name" % key, key), C.t("trait.%s.desc" % key)),
                       "role": lambda: C.t("role." + key, key) + " role",
                       "ui": lambda: "UI glyph: " + key.replace("_", " ")}.get(kind, lambda: name)()
        elif cat == "Vfx":
            kind, _, key = name.partition("_")
            meaning = {"field": lambda: "ground field: " + C.t("field.%s.name" % key, key), "zone": lambda: "ground zone: " + C.t("zone." + key, key),
                       "impact": lambda: key + " basic-hit impact", "projectile": lambda: key + " projectile (points +X)"}.get(kind, lambda: name)()
        border = f.get("border", [0, 0, 0, 0])
        rows.append("| `%s` | %dx%d | %s | %s | %s | `%s` |" % (f["id"], f["size"][0], f["size"][1], f["ppu"],
                                                              "-" if not any(border) else str(border), meaning.replace("|", "/"), f["currentReference"]))
    return rows


def cmd_brief(a):
    rq = os.path.join(HANDOFF, "requests", a.batch)
    spec = A.read_json(os.path.join(rq, "batch.json"))
    man = A.read_json(os.path.join(rq, "INPUT_MANIFEST.json"))
    C = Content()
    b = a.batch
    L = ["# CODEX ART REQUEST — Batch %s: %s" % (b, spec["title"]), "",
         "| | |", "|---|---|",
         "| batch_id | `%s` |" % b,
         "| From → To | Claude Code (lead: integration, QA, animation) → Codex (GPT-6.1 Sol, art production) |",
         "| Writable folder | `C:\\Users\\Winka\\Projects\\Aetherward\\ArtHandoff\\returns\\%s\\` — **only this folder** |" % b,
         "| Priority | %s |" % spec.get("priority", "normal"),
         "| Depends on | %s |" % spec.get("depends", "B01 style lock"),
         "| Goal | %s |" % spec["goal"], "",
         "Together with `ArtHandoff/requests/COMMON_CONTRACT.md` (binding) this file is self-contained.",
         "Generated by `Tools/ArtPipeline/handoff.py brief` from `batch.json`, the game data and `ArtProduction/designs/`.", "",
         "## 1. Read first",
         "1. `ArtHandoff/requests/COMMON_CONTRACT.md` — technical contract, animation-frame rules, method, scope, done.",
         "2. `ArtProduction/ART_BIBLE.md` — the style.",
         "3. `ArtHandoff/returns/B01/README.md` § Style lock and `ArtHandoff/returns/B01/DELIVERABLE_MANIFEST.json` → `styleLock` — reuse verbatim.",
         "4. `ArtHandoff/requests/%s/INPUT_MANIFEST.json` — the exact %d assets with size, PPU, pivot, border, foot row, flyer flag, guides." % (b, man["assetCount"]),
         "5. `ArtHandoff/requests/%s/references/guides/` — per-unit canvas guides (foot row, centre line, icon box)." % b, "",
         "## 2. Style references (attach to image generation as reference images)"]
    L += ["- `%s`" % r for r in spec.get("styleRefs", [])] or ["- the B01 exports in `ArtHandoff/returns/B01/exports/Art/`"]
    if spec.get("notes"):
        L += ["", "## 3. Batch notes", spec["notes"]]
    L += ["", "## 4. Assets"]
    for g in man["groups"]:
        L += ["", "### %s (%s)" % (g.get("title", g["id"]), g.get("priority", "")), g.get("design", "")]
        by = {}
        for f in g["assets"]:
            by.setdefault(subject(f["id"]), []).append(f)
        generic = []
        for (cat, sid), fs in by.items():
            if cat == "Heroes" and sid in C.heroes:
                L += hero_block(C, sid, fs)
            elif cat == "Enemies" and sid in C.enemies:
                L += enemy_block(C, sid, fs)
            else:
                generic += fs
        if generic:
            L += generic_rows(C, generic) + [""]
    L += ["## 5. Return, self-QA, done",
          "- Return everything to `ArtHandoff/returns/%s/` with the layout of COMMON_CONTRACT §8 and the manifest template "
          "`ArtHandoff/requests/B01/DELIVERABLE_MANIFEST.template.json`." % b,
          "- Self-QA (repo root):", "```",
          "python Tools\\ArtPipeline\\handoff.py preview --batch %s --overlay ArtHandoff\\returns\\%s\\exports\\Art --out ArtHandoff\\returns\\%s\\previews --tag %s" % (b, b, b, b.lower()),
          "python Tools\\ArtPipeline\\handoff.py intake  --batch %s --stage-dir ArtHandoff\\returns\\%s\\_work\\stage --qa-dir ArtHandoff\\returns\\%s\\qa" % (b, b, b),
          "```",
          "- Done = COMMON_CONTRACT §9. The last message of the run: delivered/blocked counts, the intake result, the top three risks.", ""]
    path = os.path.join(rq, "CODEX_ART_REQUEST.md")
    A.write_text(path, "\n".join(L))
    log("%s: brief -> %s" % (b, os.path.relpath(path, A.ROOT)))
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


def stack(images, bg=(0, 0, 0, 255)):
    W = max(i.width for i in images)
    out = Image.new("RGBA", (W, sum(i.height for i in images)), bg)
    y = 0
    for i in images:
        out.alpha_composite(i, (0, y))
        y += i.height
    return out


def flat_sheet(art, ids, per_row=10):
    """Non-unit assets (icons, cards, relics, UI, VFX) at native size and at 50%, on dark and light backdrops."""
    rows = []
    for k in range(0, len(ids), per_row):
        chunk = [art.get(i)[0] for i in ids[k:k + per_row]]
        cell = max(max(c.width, c.height) for c in chunk) + 12
        for bgc in ((34, 36, 40, 255), (150, 150, 150, 255)):
            row = Image.new("RGBA", (cell * len(chunk) + cell // 2 * len(chunk), cell), bgc)
            x = 0
            for c in chunk:
                row.alpha_composite(c, (x + 6, (cell - c.height) // 2))
                half = c.resize((max(1, c.width // 2), max(1, c.height // 2)), Image.LANCZOS)
                row.alpha_composite(half, (x + cell + 6, (cell - half.height) // 2))
                x += cell + cell // 2
            rows.append(row)
    return stack(rows)


def cmd_preview(a):
    rq = os.path.join(HANDOFF, "requests", a.batch)
    lp = os.path.join(rq, "benchmark_layout.json")
    layout = A.read_json(lp if os.path.exists(lp) else os.path.join(HANDOFF, "requests", "B01", "benchmark_layout.json"))
    req = A.read_json(os.path.join(rq, "INPUT_MANIFEST.json"))
    settings = A.read_json(A.SETTINGS)
    for g in req["groups"]:
        for f in g["assets"]:
            if f.get("new"):   # new frames borrow the PPU/pivot of their live sibling
                settings[LIVE_REL + f["id"] + ".png"] = settings[LIVE_REL + f["like"] + ".png"]
    art = ArtSet(a.overlay, settings)
    os.makedirs(a.out, exist_ok=True)
    tag = a.tag or ("overlay" if a.overlay else "live")
    note = "OFFLINE COMPOSITE (handoff.py preview, %s art) - not a Unity screenshot" % tag
    for h in (1080, 720):
        render_scene(art, layout, h, note).save(os.path.join(a.out, "scene_%s_%dp.png" % (tag, h)))
    ids = [f["id"] for g in req["groups"] for f in g["assets"] if os.path.exists(art.path(f["id"]))]
    chars = [i for i in ids if i.startswith(("Heroes/", "Enemies/", "World/crystal_"))]
    for mode in ("colour", "silhouette", "gray"):
        if chars:
            rows = [sheet(art, chars[k:k + 14], h, mode) for k in range(0, len(chars), 14) for h in (1080, 720)]
            stack(rows).convert("RGB").save(os.path.join(a.out, "units_%s_%s.png" % (tag, mode)))
    flats = [i for i in ids if i.split("/")[0] in ("Icons", "Cards", "Relics", "UI", "Vfx", "Portraits") or
             (i.startswith("World/") and art.get(i)[0].width <= 512)]
    if flats:
        flat_sheet(art, flats).convert("RGB").save(os.path.join(a.out, "flat_%s.png" % tag))
    log("preview (%s) -> %s" % (tag, a.out))
    return 0


# ------------------------------------------------------------------------------------------------ intake

def lowest_opaque_row(im):
    alpha = im.getchannel("A")
    bbox = alpha.point(lambda v: 255 if v > 128 else 0).getbbox()
    return None if bbox is None else bbox[3] - 1


SEPARATION_MIN = 0.10


def value_separation(stage, ids):
    """Mean luminance of each unit's 3 px edge band vs the mean of the staged default battlefield."""
    import numpy as np
    from scipy.ndimage import binary_erosion

    def lum(a):
        return (0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]) / 255.0
    bg = np.asarray(Image.open(os.path.join(stage, "Art", "World", "arena_background.png")).convert("RGB")).astype(float)
    ground = float(lum(bg).mean())
    out = {}
    for uid in ids:
        a = np.asarray(Image.open(os.path.join(stage, "Art", uid + ".png")).convert("RGBA")).astype(float)
        m = a[..., 3] > 128
        edge = m & ~binary_erosion(m, iterations=3)
        if edge.any():
            out[uid] = (float(lum(a[..., :3])[edge].mean()), ground)
    return out


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
    shutil.copytree(A.ART, os.path.join(stage, "Art"))   # with .meta: the validator checks GUID/pivot/PPU against them
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
    # value separation (review warning): a unit's 3 px edge band must read lighter than the battlefield it stands on
    sep = value_separation(stage, [r_["id"] for r_ in rows if r_["status"] == "OK" and r_["id"].startswith(("Heroes/", "Enemies/"))])
    for uid, (edge_l, ground_l) in sep.items():
        if edge_l < ground_l + SEPARATION_MIN:
            notes.append("%s: edge luminance %.2f vs ground %.2f (needs >= +%.2f): add rim light / lift edge values" % (uid, edge_l, ground_l, SEPARATION_MIN))
    # write scope: nothing outside ArtHandoff/returns/<batch> may change
    r = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=A.ROOT, capture_output=True, text=True)
    stray = [ln[3:].strip('"') for ln in r.stdout.splitlines()]
    # other batches may be returning in parallel; each Codex sandbox can only write its own returns/<batch>/
    stray = [s for s in stray if s and not s.startswith(("ArtHandoff/returns/", "Temp/"))
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
        # settings/manifest are keyed by live paths: rewrite them to the stage root, as ap.py validate does
        live_root, stage_rel = LIVE_REL.rstrip("/"), os.path.relpath(os.path.join(stage, "Art"), A.ROOT).replace("\\", "/")
        man = A.load_json(A.MANIFEST)
        for m in man:
            m["path"] = m["path"].replace(live_root, stage_rel, 1)
        sett = {k.replace(live_root, stage_rel, 1): val for k, val in A.read_json(A.SETTINGS).items()}
        A.dump_json(man, os.path.join(stage, "manifest.staged.json"))
        A.dump_json(sett, os.path.join(stage, "settings.staged.json"))
        v = subprocess.run([sys.executable, os.path.join(A.HERE, "validate.py"), "--art", os.path.join(stage, "Art"),
                            "--settings", os.path.join(stage, "settings.staged.json"), "--manifest", os.path.join(stage, "manifest.staged.json"),
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
    br = sub.add_parser("brief")
    br.add_argument("--batch", required=True)
    v = sub.add_parser("preview")
    v.add_argument("--batch", required=True)
    v.add_argument("--overlay", default=None, help="Art-root-shaped dir whose PNGs replace live ones (e.g. ArtHandoff/returns/B01/exports/Art)")
    v.add_argument("--out", required=True)
    v.add_argument("--tag", default=None)
    a = p.parse_args()
    return {"request": cmd_request, "brief": cmd_brief, "intake": cmd_intake, "preview": cmd_preview}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
