"""Arena background (Arcane Sanctuary), crystal states, defence-node pads, lane telegraph arrows,
ground shadow. The background is generated from the same arena.json the simulation uses, so lanes
and nodes in the art always match gameplay.
"""
import json
import math
import os
import random
import cairo
from toolkit import (INK, Canvas, hex2rgb, mix, shade, light, paint, flat, stroke, glow, sparkle,
                     smooth_closed, smooth_open, ellipse_path, rrect_path, poly_path, star_path, outlined_line)

PPU = 80                     # background pixels per world unit
WORLD_W, WORLD_H = 30.0, 17.0
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def load_arena():
    path = os.path.join(ROOT, "Assets", "_Aetherward", "Resources", "Content", "arena.json")
    text = "\n".join(l for l in open(path).read().splitlines() if not l.strip().startswith("//"))
    return json.loads(text)


def to_px(x, y):
    return ((x + WORLD_W / 2) * PPU, (WORLD_H / 2 - y) * PPU)


def load_biomes():
    path = os.path.join(ROOT, "Assets", "_Aetherward", "Resources", "Content", "biomes.json")
    text = "\n".join(l for l in open(path).read().splitlines() if not l.strip().startswith("//"))
    return json.loads(text)["biomes"]


def background(arena=None, theme="verdant", biome=None):
    """Battlefield background generated from an arena definition (lanes/nodes in world units).

    theme "verdant" is the original Arcane Sanctuary (default arena.json); "molten", "frost", "aether",
    "storm" and "archive" are the biome arenas from biomes.json (biome supplies hazards / nodeTraits for markers).
    """
    if arena is None:
        arena = load_arena()
    if theme == "molten":
        return _molten_background(arena, biome or {})
    if theme == "frost":
        return _frost_background(arena, biome or {})
    if theme == "aether":
        return _aether_background(arena, biome or {})
    if theme == "storm":
        return _storm_background(arena, biome or {})
    if theme == "archive":
        return _archive_background(arena, biome or {})
    return _verdant_background(arena)


def _verdant_background(arena):
    w, h = int(WORLD_W * PPU), int(WORLD_H * PPU)
    cv = Canvas(w, h)
    ctx = cv.ctx
    rnd = random.Random(1337)
    grass = hex2rgb("#3f7a5c")
    grass_dark = hex2rgb("#2f5f4c")
    # base vertical gradient (slight vignette toward the edges)
    grad = cairo.RadialGradient(w / 2, h / 2, 100, w / 2, h / 2, w * 0.62)
    grad.add_color_stop_rgb(0, *light(grass, 0.08))
    grad.add_color_stop_rgb(0.7, *grass)
    grad.add_color_stop_rgb(1, *shade(grass_dark, 0.35))
    ctx.set_source(grad)
    ctx.paint()
    # mottled ground patches
    for _ in range(900):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.uniform(14, 60)
        col = mix(grass, grass_dark if rnd.random() < 0.6 else light(grass, 0.25), rnd.uniform(0.3, 0.8))
        flat(ctx, lambda c, x=x, y=y, r=r: ellipse_path(c, x, y, r, r * rnd.uniform(0.5, 0.9), rnd.uniform(0, 3)), col, 0.18)

    # lanes: worn dirt paths with cobble edges, drawn from the simulation's lane polylines
    dirt = hex2rgb("#b49067")
    for lane in arena["lanes"]:
        pts = [to_px(*p) for p in lane["points"]]
        pts = [(pts[0][0] + (pts[0][0] - pts[1][0]) * 0.3, pts[0][1] + (pts[0][1] - pts[1][1]) * 0.3)] + pts
        for col, width, alpha in ((shade(dirt, 0.45), 1.75 * PPU, 0.55), (dirt, 1.45 * PPU, 0.9), (light(dirt, 0.18), 0.8 * PPU, 0.5)):
            ctx.save()
            ctx.new_path()
            smooth_open(ctx, pts)
            ctx.set_source_rgba(*col, alpha)
            ctx.set_line_width(width)
            ctx.stroke()
            ctx.restore()
        # pebbles along the path
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            n = int(math.hypot(x1 - x0, y1 - y0) / 26)
            for k in range(n):
                t = k / max(n, 1)
                px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                ox, oy = rnd.uniform(-50, 50), rnd.uniform(-50, 50)
                rr = rnd.uniform(4, 9)
                paint(ctx, lambda c, a=px + ox, b=py + oy, rr=rr: ellipse_path(c, a, b, rr, rr * 0.75), mix(dirt, hex2rgb("#8a7a6a"), 0.6),
                      lw=2, hi=False, shade_amt=0.25, alpha=0.8)

    # sanctuary plaza: concentric stone rings around the crystal
    cx, cy = to_px(0, 0)
    stone = hex2rgb("#9aa0b8")
    plaza_r = 5.6 * PPU
    flat(ctx, lambda c: ellipse_path(c, cx, cy + 10, plaza_r + 26, plaza_r * 0.82 + 26), shade(grass_dark, 0.4), 0.45)
    paint(ctx, lambda c: ellipse_path(c, cx, cy, plaza_r, plaza_r * 0.8), stone, lw=8, shade_amt=0.18, hi_size=0.7, hi_pos=(-0.2, -0.3))
    # flagstone tint variation (filled ring segments), then mortar lines
    for ring in range(1, 6):
        segments = 8 + ring * 6
        r0, r1 = plaza_r * (ring - 1) / 5.0, plaza_r * ring / 5.0
        for k in range(segments):
            a0 = k * 2 * math.pi / segments + ring * 0.21
            a1 = a0 + 2 * math.pi / segments
            tint = mix(stone, hex2rgb("#c9b9a6") if rnd.random() < 0.5 else hex2rgb("#7f86a4"), rnd.uniform(0.05, 0.3))
            def seg(c, a0=a0, a1=a1, r0=r0, r1=r1):
                c.save(); c.translate(cx, cy); c.scale(1, 0.8)
                c.arc(0, 0, r1, a0, a1); c.arc_negative(0, 0, max(r0, 0.1), a1, a0); c.close_path(); c.restore()
            flat(ctx, seg, tint, 0.85)
    for ring in range(1, 5):
        rr = plaza_r * ring / 5.0
        stroke(ctx, lambda c, rr=rr: ellipse_path(c, cx, cy, rr, rr * 0.8), shade(stone, 0.35), 3.5, 0.7)
        segments = 8 + ring * 6
        for k in range(segments):
            a = k * 2 * math.pi / segments + ring * 0.21
            r0, r1 = plaza_r * (ring - 1) / 5.0, rr
            stroke(ctx, lambda c, a=a, r0=r0, r1=r1: (c.move_to(cx + math.cos(a) * r0, cy + math.sin(a) * r0 * 0.8),
                                                      c.line_to(cx + math.cos(a) * r1, cy + math.sin(a) * r1 * 0.8)), shade(stone, 0.35), 3, 0.6)
    # rune ring
    rune = hex2rgb("#7fe8ff")
    rr = plaza_r * 0.62
    glow(ctx, cx, cy, rr * 1.2, rune, 0.12)
    stroke(ctx, lambda c: ellipse_path(c, cx, cy, rr, rr * 0.8), rune, 5, 0.65)
    stroke(ctx, lambda c: ellipse_path(c, cx, cy, rr * 0.9, rr * 0.72), rune, 2.5, 0.5)
    for k in range(16):
        a = k * math.pi / 8
        x, y = cx + math.cos(a) * rr * 0.95, cy + math.sin(a) * rr * 0.76
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(a + math.pi / 2)
        stroke(ctx, lambda c, k=k: (c.move_to(-7, -6), c.line_to(0, 6 if k % 2 else -2), c.line_to(7, -6)), rune, 3, 0.7)
        ctx.restore()
    # moss creeping on the plaza edge
    for _ in range(140):
        a = rnd.uniform(0, 2 * math.pi)
        r = plaza_r * rnd.uniform(0.86, 1.02)
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * 0.8
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, rnd.uniform(6, 18), rnd.uniform(4, 10)), light(grass, 0.1), 0.6)

    # decoration: grass tufts, flowers, rocks, ruined pillars (kept off lanes and plaza)
    lane_segments = []
    for lane in arena["lanes"]:
        pts = [to_px(*p) for p in lane["points"]]
        lane_segments += list(zip(pts[:-1], pts[1:]))

    def near_lane(x, y, d):
        for (a, b) in lane_segments:
            ax, ay = a
            bx, by = b
            dx, dy = bx - ax, by - ay
            L = dx * dx + dy * dy
            t = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / L)) if L > 0 else 0
            if math.hypot(x - (ax + dx * t), y - (ay + dy * t)) < d:
                return True
        return False

    def free(x, y, d=1.2 * PPU):
        if math.hypot((x - cx) / 1.0, (y - cy) / 0.8) < plaza_r + 40:
            return False
        return not near_lane(x, y, d)

    for _ in range(420):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        if not free(x, y, 0.95 * PPU):
            continue
        col = mix(grass, hex2rgb("#7fcf6a"), rnd.uniform(0.3, 0.7))
        for k in range(3):
            a = -math.pi / 2 + (k - 1) * 0.45
            stroke(ctx, lambda c, a=a: (c.move_to(x, y), c.line_to(x + math.cos(a) * 16, y + math.sin(a) * 18)), col, 4.5)
    flower_cols = [hex2rgb("#ffd35a"), hex2rgb("#ff8ac0"), hex2rgb("#b9a0ff"), hex2rgb("#ffffff")]
    for _ in range(160):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        if not free(x, y):
            continue
        col = rnd.choice(flower_cols)
        for k in range(5):
            a = k * 2 * math.pi / 5
            flat(ctx, lambda c, a=a: ellipse_path(c, x + math.cos(a) * 5, y + math.sin(a) * 5, 4.5, 4.5), col)
        flat(ctx, lambda c: ellipse_path(c, x, y, 3, 3), hex2rgb("#ffb23a"))
    rock = hex2rgb("#8c8f9c")
    for _ in range(46):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        if not free(x, y, 1.4 * PPU):
            continue
        r = rnd.uniform(18, 40)
        pts = [(x + math.cos(a) * r * rnd.uniform(0.75, 1.1), y + math.sin(a) * r * 0.7 * rnd.uniform(0.75, 1.1)) for a in
               [k * 2 * math.pi / 7 for k in range(7)]]
        flat(ctx, lambda c: ellipse_path(c, x + 4, y + r * 0.5, r * 1.05, r * 0.35), (0, 0, 0), 0.22)
        paint(ctx, lambda c, pts=pts: smooth_closed(c, pts, 0.4), rock, lw=5, shade_amt=0.3)
    # ruined pillars at the four corners of the plaza
    for (wx, wy) in ((-7.4, 4.6), (7.4, 4.6), (-7.4, -4.6), (7.4, -4.6), (-10.5, 1.2), (10.5, -1.4)):
        x, y = to_px(wx, wy)
        flat(ctx, lambda c: ellipse_path(c, x + 6, y + 6, 46, 16), (0, 0, 0), 0.25)
        paint(ctx, lambda c: rrect_path(c, x - 30, y - 120, 60, 124, 8), hex2rgb("#b8bccc"), lw=6, shade_amt=0.25)
        for k in range(3):
            stroke(ctx, lambda c, k=k: (c.move_to(x - 16 + k * 16, y - 108), c.line_to(x - 16 + k * 16, y - 10)), shade(hex2rgb("#b8bccc"), 0.3), 3)
        paint(ctx, lambda c: rrect_path(c, x - 38, y - 132, 76, 18, 6), hex2rgb("#d0d4e0"), lw=6, shade_amt=0.2)
        glow(ctx, x, y - 150, 30, rune, 0.5)
        paint(ctx, lambda c: poly_path(c, [(x, y - 170), (x + 10, y - 150), (x, y - 134), (x - 10, y - 150)]), rune, lw=4, hi_size=0.8)

    # lane mouths: rift portals at spawn points (just off the visible edge on most screens)
    for lane in arena["lanes"]:
        x, y = to_px(*lane["points"][0])
        glow(ctx, x, y, 120, hex2rgb("#b07aff"), 0.45)
        stroke(ctx, lambda c: ellipse_path(c, x, y, 54, 54), hex2rgb("#d0a8ff"), 5, 0.8)
    return cv


# ---------------------------------------------------------------------------- biome battlefields

LANE_HALF = 0.875 * PPU      # half of the drawn lane width (1.75 world units)


def _lane_paths(arena):
    """Lane polylines in px, with the spawn end extended off-screen exactly like the verdant arena."""
    out = []
    for lane in arena["lanes"]:
        pts = [to_px(*p) for p in lane["points"]]
        pts = [(pts[0][0] + (pts[0][0] - pts[1][0]) * 0.3, pts[0][1] + (pts[0][1] - pts[1][1]) * 0.3)] + pts
        out.append(pts)
    return out


def _seg_dist(x, y, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / L)) if L > 0 else 0
    return math.hypot(x - (ax + dx * t), y - (ay + dy * t))


def _poly_dist(x, y, pts):
    return min(_seg_dist(x, y, a, b) for a, b in zip(pts[:-1], pts[1:]))


def _seg_hit(p1, p2, p3, p4):
    """Intersection point of segments p1p2 and p3p4, or None."""
    d = (p2[0] - p1[0]) * (p4[1] - p3[1]) - (p2[1] - p1[1]) * (p4[0] - p3[0])
    if abs(d) < 1e-9:
        return None
    t = ((p3[0] - p1[0]) * (p4[1] - p3[1]) - (p3[1] - p1[1]) * (p4[0] - p3[0])) / d
    u = ((p3[0] - p1[0]) * (p2[1] - p1[1]) - (p3[1] - p1[1]) * (p2[0] - p1[0])) / d
    if 0 <= t <= 1 and 0 <= u <= 1:
        return (p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t)
    return None


def _draw_lanes(ctx, lanes, layers):
    for pts in lanes:
        for col, width, alpha in layers:
            ctx.save()
            ctx.new_path()
            smooth_open(ctx, pts)
            ctx.set_source_rgba(*col, alpha)
            ctx.set_line_width(width)
            ctx.stroke()
            ctx.restore()


def _lane_pebbles(ctx, rnd, lanes, col, spread=50):
    for pts in lanes:
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            n = int(math.hypot(x1 - x0, y1 - y0) / 26)
            for k in range(n):
                t = k / max(n, 1)
                px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                ox, oy = rnd.uniform(-spread, spread), rnd.uniform(-spread, spread)
                rr = rnd.uniform(4, 9)
                paint(ctx, lambda c, a=px + ox, b=py + oy, rr=rr: ellipse_path(c, a, b, rr, rr * 0.75), col,
                      lw=2, hi=False, shade_amt=0.25, alpha=0.8)


def _portals(ctx, arena, col, ring):
    for lane in arena["lanes"]:
        x, y = to_px(*lane["points"][0])
        glow(ctx, x, y, 120, col, 0.45)
        stroke(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 54, 54), ring, 5, 0.8)


def _base(ctx, w, h, rnd, mid, dark, center, patch_cols, n=900, alpha=0.18):
    grad = cairo.RadialGradient(w / 2, h / 2, 100, w / 2, h / 2, w * 0.62)
    grad.add_color_stop_rgb(0, *center)
    grad.add_color_stop_rgb(0.7, *mid)
    grad.add_color_stop_rgb(1, *dark)
    ctx.set_source(grad)
    ctx.paint()
    for _ in range(n):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.uniform(14, 60)
        col = mix(mid, rnd.choice(patch_cols), rnd.uniform(0.3, 0.8))
        flat(ctx, lambda c, x=x, y=y, r=r: ellipse_path(c, x, y, r, r * rnd.uniform(0.5, 0.9), rnd.uniform(0, 3)), col, alpha)


def _plaza(ctx, rnd, cx, cy, plaza_r, stone, tints, line_col, rune, edge_col):
    flat(ctx, lambda c: ellipse_path(c, cx, cy + 10, plaza_r + 22, plaza_r * 0.82 + 22), edge_col, 0.5)
    paint(ctx, lambda c: ellipse_path(c, cx, cy, plaza_r, plaza_r * 0.8), stone, lw=8, shade_amt=0.18, hi_size=0.7, hi_pos=(-0.2, -0.3))
    rings = 3
    for ring in range(1, rings + 1):
        segments = 6 + ring * 5
        r0, r1 = plaza_r * (ring - 1) / rings, plaza_r * ring / rings
        for k in range(segments):
            a0 = k * 2 * math.pi / segments + ring * 0.21
            a1 = a0 + 2 * math.pi / segments
            tint = mix(stone, rnd.choice(tints), rnd.uniform(0.05, 0.3))

            def seg(c, a0=a0, a1=a1, r0=r0, r1=r1):
                c.save(); c.translate(cx, cy); c.scale(1, 0.8)
                c.arc(0, 0, r1, a0, a1); c.arc_negative(0, 0, max(r0, 0.1), a1, a0); c.close_path(); c.restore()
            flat(ctx, seg, tint, 0.85)
            stroke(ctx, seg, line_col, 3, 0.6)
    rr = plaza_r * 0.78
    glow(ctx, cx, cy, rr * 1.3, rune, 0.14)
    stroke(ctx, lambda c: ellipse_path(c, cx, cy, rr, rr * 0.8), rune, 5, 0.7)
    for k in range(12):
        a = k * math.pi / 6
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.8
        flat(ctx, lambda c, x=x, y=y: star_path(c, x, y, 9, 3.5, 4), rune, 0.8)


def _molten_background(arena, biome):
    w, h = int(WORLD_W * PPU), int(WORLD_H * PPU)
    cv = Canvas(w, h)
    ctx = cv.ctx
    rnd = random.Random(4242)
    basalt = hex2rgb("#3a3133")
    ash = hex2rgb("#5a5050")
    lava = hex2rgb("#ff6a1a")
    hot = hex2rgb("#ffd24a")
    crust = hex2rgb("#1c1012")
    _base(ctx, w, h, rnd, basalt, hex2rgb("#181214"), hex2rgb("#463b3a"),
          [hex2rgb("#241c1e"), hex2rgb("#5a4c48"), hex2rgb("#4a3430")])
    lanes = _lane_paths(arena)
    cx, cy = to_px(0, 0)

    def lane_d(x, y):
        return min(_poly_dist(x, y, pts) for pts in lanes)

    # lava rivers: two arcs around the central island (point-symmetric like the lanes), ending in pools
    rivers = []
    for side in (1, -1):
        pts = []
        for k in range(15):
            a = math.radians(-58 + k * 116 / 14.0)
            r = 5.9 + 0.12 * math.sin(k * 0.9)
            pts.append(to_px(side * math.cos(a) * r, side * math.sin(a) * r))
        rivers.append(pts)
    river_w = 0.95 * PPU
    pools = [(pts[0], 0.95 * PPU) for pts in rivers] + [(pts[-1], 0.95 * PPU) for pts in rivers]
    # extra pools on open ground, well clear of lanes, nodes, plaza and vents
    vents = [to_px(*p) for hz in biome.get("hazards", []) for p in hz.get("points", [])]
    nodes = [to_px(*n) for n in arena["nodes"]]
    tries = 0
    while len(pools) < 10 and tries < 4000:
        tries += 1
        x, y = rnd.uniform(1.0 * PPU, w - 1.0 * PPU), rnd.uniform(0.8 * PPU, h - 0.8 * PPU)
        r = rnd.uniform(0.7, 1.25) * PPU
        if lane_d(x, y) < r + LANE_HALF + 0.5 * PPU:
            continue
        if math.hypot(x - cx, y - cy) < 7.2 * PPU:
            continue
        if any(math.hypot(x - px, y - py) < r + pr + 0.6 * PPU for (px, py), pr in pools):
            continue
        pools.append(((x, y), r))

    def river_path(c, pts):
        smooth_open(c, pts)

    # ember-lit crust cracks across the ground (off lanes)
    for _ in range(170):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        if lane_d(x, y) < LANE_HALF + 20 or math.hypot((x - cx), (y - cy) / 0.8) < 3.3 * PPU:
            continue
        a = rnd.uniform(0, 2 * math.pi)
        pts = [(x, y)]
        for _k in range(3):
            a += rnd.uniform(-0.8, 0.8)
            L = rnd.uniform(14, 34)
            pts.append((pts[-1][0] + math.cos(a) * L, pts[-1][1] + math.sin(a) * L))
        stroke(ctx, lambda c, pts=pts: smooth_open(c, pts), crust, 5, 0.7)
        stroke(ctx, lambda c, pts=pts: smooth_open(c, pts), lava, 1.6, 0.45)

    # ash-trodden lanes
    _draw_lanes(ctx, lanes, ((hex2rgb("#1e1618"), 1.75 * PPU, 0.6), (ash, 1.45 * PPU, 0.92), (light(ash, 0.15), 0.8 * PPU, 0.45)))
    _lane_pebbles(ctx, rnd, lanes, hex2rgb("#2a2224"))

    # lava (glow halo, scorched bank, molten body, bright core)
    for pts in rivers:
        for k in range(0, len(pts), 2):
            glow(ctx, pts[k][0], pts[k][1], 2.0 * PPU, lava, 0.28)
    for (x, y), r in pools:
        glow(ctx, x, y, r * 2.2, lava, 0.3)
    for col, wf, alpha in ((crust, 1.45, 1.0), (hex2rgb("#c0300e"), 1.08, 1.0), (lava, 0.86, 1.0), (hot, 0.34, 0.75)):
        for pts in rivers:
            ctx.save()
            ctx.new_path()
            river_path(ctx, pts)
            ctx.set_source_rgba(*col, alpha)
            ctx.set_line_width(river_w * wf)
            ctx.stroke()
            ctx.restore()
        for (x, y), r in pools:
            flat(ctx, lambda c, x=x, y=y, r=r, wf=wf: ellipse_path(c, x, y, r * (0.5 + wf * 0.6), r * (0.5 + wf * 0.6) * 0.72), col, alpha)
    # crust floes drifting on the lava
    for pts in rivers:
        for i in range(1, len(pts) - 1, 2):
            x, y = pts[i]
            x += rnd.uniform(-10, 10)
            y += rnd.uniform(-10, 10)
            paint(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, rnd.uniform(8, 16), rnd.uniform(5, 9), rnd.uniform(0, 3)), hex2rgb("#3a2422"),
                  lw=3, hi=False, alpha=0.9)
    for (x, y), r in pools:
        sparkle(ctx, x - r * 0.3, y - r * 0.2, 10, light(hot, 0.5), 0.8)

    # basalt bridges where lanes cross the lava (shared lanes produce one bridge)
    bridges = []
    for lane in lanes:
        for a, b in zip(lane[:-1], lane[1:]):
            for pts in rivers:
                dense = []
                ctx.new_path()
                river_path(ctx, pts)
                for kind, pp in ctx.copy_path_flat():
                    if kind in (cairo.PATH_MOVE_TO, cairo.PATH_LINE_TO):
                        dense.append(pp)
                ctx.new_path()
                for p, q in zip(dense[:-1], dense[1:]):
                    hit = _seg_hit(a, b, p, q)
                    if hit and not any(math.hypot(hit[0] - bx, hit[1] - by) < PPU for bx, by, _ in bridges):
                        bridges.append((hit[0], hit[1], math.atan2(b[1] - a[1], b[0] - a[0])))
    stone = hex2rgb("#4e4448")
    for (x, y, ang) in bridges:
        L, W = river_w * 1.45 + 0.9 * PPU, 2.0 * PPU
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(ang)
        flat(ctx, lambda c: rrect_path(c, -L / 2 + 6, -W / 2 + 12, L, W, 14), (0, 0, 0), 0.4)
        paint(ctx, lambda c: rrect_path(c, -L / 2, -W / 2, L, W, 14), stone, lw=7, shade_amt=0.2, hi_size=0.6)
        flat(ctx, lambda c: rrect_path(c, -L / 2 + 10, -W * 0.36, L - 20, W * 0.72, 10), mix(stone, ash, 0.55), 0.95)
        for k in range(1, 5):
            xx = -L / 2 + k * L / 5
            stroke(ctx, lambda c, xx=xx: (c.move_to(xx, -W / 2 + 6), c.line_to(xx + 4, W / 2 - 6)), shade(stone, 0.4), 4, 0.8)
        for sgn in (-1, 1):
            for k in range(6):
                xx = -L / 2 + 14 + k * (L - 28) / 5
                paint(ctx, lambda c, xx=xx, sgn=sgn: rrect_path(c, xx - 11, sgn * W / 2 - 11, 22, 22, 5), light(stone, 0.1), lw=4, hi=False)
        ctx.restore()

    # central obsidian dais with an ember rune ring
    plaza_r = 2.9 * PPU
    _plaza(ctx, rnd, cx, cy, plaza_r, hex2rgb("#4a4048"), [hex2rgb("#5e5258"), hex2rgb("#2e2630")], hex2rgb("#221a20"),
           hex2rgb("#ff9a3a"), hex2rgb("#140e10"))

    # heated nodes: warm glow and glowing seams under the pad
    for t in biome.get("nodeTraits", []):
        x, y = nodes[t["node"]]
        glow(ctx, x, y, 1.15 * PPU, lava, 0.45)
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 0.72 * PPU, 0.5 * PPU), hex2rgb("#5a3a30"), 0.7)
        for k in range(5):
            a = k * 2 * math.pi / 5 + 0.4
            pts = [(x + math.cos(a) * 18, y + math.sin(a) * 13), (x + math.cos(a + 0.3) * 40, y + math.sin(a + 0.3) * 28),
                   (x + math.cos(a) * 60, y + math.sin(a) * 42)]
            stroke(ctx, lambda c, pts=pts: smooth_open(c, pts), lava, 5, 0.85)
            stroke(ctx, lambda c, pts=pts: smooth_open(c, pts), hot, 2, 0.8)

    # lava vents (hazard points): soot ring, cracked mound, faint glow — subtle, the runtime telegraphs eruptions
    for (x, y) in vents:
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 0.7 * PPU, 0.5 * PPU), hex2rgb("#120c0e"), 0.45)
        paint(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 0.38 * PPU, 0.27 * PPU), hex2rgb("#3a2c2c"), lw=5, shade_amt=0.3, hi=False)
        glow(ctx, x, y, 0.45 * PPU, lava, 0.55)
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 0.13 * PPU, 0.09 * PPU), hot, 0.9)
        for k in range(6):
            a = k * math.pi / 3 + 0.2
            stroke(ctx, lambda c, x=x, y=y, a=a: (c.move_to(x + math.cos(a) * 0.16 * PPU, y + math.sin(a) * 0.12 * PPU),
                                                  c.line_to(x + math.cos(a) * 0.5 * PPU, y + math.sin(a) * 0.36 * PPU)), lava, 3, 0.7)

    # decor: basalt boulders, obsidian shards, ember motes (kept off lanes, lava, plaza and nodes)
    def free(x, y, d):
        if math.hypot(x - cx, (y - cy) / 0.8) < plaza_r + 40:
            return False
        if lane_d(x, y) < LANE_HALF + d:
            return False
        if any(_poly_dist(x, y, pts) < river_w + d for pts in rivers):
            return False
        if any(math.hypot(x - px, y - py) < pr + d for (px, py), pr in pools):
            return False
        if any(math.hypot(x - nx, y - ny) < 0.8 * PPU + d for nx, ny in nodes + vents):
            return False
        return True

    rock = hex2rgb("#4a4044")
    for _ in range(70):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.uniform(18, 40)
        if not free(x, y, r + 10):
            continue
        pts = [(x + math.cos(a) * r * rnd.uniform(0.75, 1.1), y + math.sin(a) * r * 0.7 * rnd.uniform(0.75, 1.1)) for a in
               [k * 2 * math.pi / 7 for k in range(7)]]
        flat(ctx, lambda c: ellipse_path(c, x + 4, y + r * 0.5, r * 1.05, r * 0.35), (0, 0, 0), 0.3)
        paint(ctx, lambda c, pts=pts: smooth_closed(c, pts, 0.4), rock, lw=5, shade_amt=0.3)
    obs = hex2rgb("#2a2034")
    for _ in range(40):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        if not free(x, y, 50):
            continue
        for k in range(rnd.randint(2, 4)):
            ox, hh = rnd.uniform(-22, 22), rnd.uniform(30, 64)
            paint(ctx, lambda c, ox=ox, hh=hh: poly_path(c, [(x + ox - 10, y), (x + ox + rnd.uniform(-6, 6), y - hh), (x + ox + 10, y)]),
                  obs, lw=4, shade_amt=0.25, hi_size=0.5)
            stroke(ctx, lambda c, ox=ox, hh=hh: (c.move_to(x + ox - 3, y - 4), c.line_to(x + ox, y - hh * 0.8)), hex2rgb("#a080d0"), 2, 0.6)
    for _ in range(220):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        if lane_d(x, y) < LANE_HALF:
            continue
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 2.2, 2.2), rnd.choice([lava, hot]), rnd.uniform(0.35, 0.8))

    _portals(ctx, arena, hex2rgb("#ff5a2a"), hex2rgb("#ffb070"))
    return cv


def _frost_background(arena, biome):
    w, h = int(WORLD_W * PPU), int(WORLD_H * PPU)
    cv = Canvas(w, h)
    ctx = cv.ctx
    rnd = random.Random(7331)
    snow = hex2rgb("#d6e4f2")
    snow_sh = hex2rgb("#a9bdd6")
    ice = hex2rgb("#bfe8ff")
    _base(ctx, w, h, rnd, snow, hex2rgb("#8aa2c0"), hex2rgb("#eaf2fa"), [snow_sh, hex2rgb("#f4f8ff"), hex2rgb("#c4d4e8")], alpha=0.22)
    lanes = _lane_paths(arena)
    cx, cy = to_px(0, 0)
    nodes = [to_px(*n) for n in arena["nodes"]]
    covers = [(to_px(*cv_["pos"]), cv_.get("radius", 1.0) * PPU) for cv_ in biome.get("covers", [])]

    def lane_d(x, y):
        return min(_poly_dist(x, y, pts) for pts in lanes)

    # courtyard paving peeking through the snow (inside the walls, under everything else)
    flag = hex2rgb("#8e9cb2")
    tile = 0.9 * PPU
    x0, x1 = to_px(-12.4, 0)[0], to_px(12.4, 0)[0]
    y0, y1 = to_px(0, 6.6)[1], to_px(0, -6.6)[1]
    row = 0
    y = y0
    while y < y1:
        x = x0 - (tile / 2 if row % 2 else 0)
        while x < x1:
            if rnd.random() < 0.4:
                col = mix(flag, rnd.choice([hex2rgb("#a8b4c8"), hex2rgb("#76849c")]), rnd.uniform(0.1, 0.4))
                flat(ctx, lambda c, x=x, y=y: rrect_path(c, x + 3, y + 3, tile - 6, tile * 0.8 - 6, 6), col, rnd.uniform(0.12, 0.26))
            x += tile
        y += tile * 0.8
        row += 1
    # windswept snow over the paving
    for _ in range(500):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.uniform(20, 70)
        flat(ctx, lambda c, x=x, y=y, r=r: ellipse_path(c, x, y, r, r * rnd.uniform(0.4, 0.7), rnd.uniform(-0.3, 0.3)), (0.96, 0.98, 1.0), 0.35)

    # trodden slush lanes
    slush = hex2rgb("#9fb2c8")
    _draw_lanes(ctx, lanes, ((hex2rgb("#6e84a0"), 1.75 * PPU, 0.55), (slush, 1.45 * PPU, 0.9), (light(slush, 0.25), 0.8 * PPU, 0.5)))
    _lane_pebbles(ctx, rnd, lanes, hex2rgb("#7a8aa0"))
    # boot prints along lanes
    for pts in lanes:
        for i in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            ang = math.atan2(by - ay, bx - ax)
            n = int(math.hypot(bx - ax, by - ay) / 40)
            for k in range(n):
                t = k / max(n, 1)
                side = 1 if k % 2 else -1
                px = ax + (bx - ax) * t - math.sin(ang) * side * 12 + rnd.uniform(-20, 20)
                py = ay + (by - ay) * t + math.cos(ang) * side * 12 + rnd.uniform(-20, 20)
                flat(ctx, lambda c, px=px, py=py, ang=ang: ellipse_path(c, px, py, 8, 4.5, ang), hex2rgb("#7a90ac"), 0.35)

    # central icy plaza
    plaza_r = 2.9 * PPU
    _plaza(ctx, rnd, cx, cy, plaza_r, hex2rgb("#a8bcd4"), [hex2rgb("#d0e4f4"), hex2rgb("#8aa0bc")], hex2rgb("#6a7e9a"),
           hex2rgb("#7fe8ff"), hex2rgb("#7088a8"))

    # frozen tiles at trait nodes
    for t in biome.get("nodeTraits", []):
        x, y = nodes[t["node"]]
        glow(ctx, x, y, 1.1 * PPU, hex2rgb("#9ae0ff"), 0.45)
        hexp = [(x + math.cos(k * math.pi / 3) * 0.82 * PPU, y + math.sin(k * math.pi / 3) * 0.6 * PPU) for k in range(6)]
        paint(ctx, lambda c, hexp=hexp: poly_path(c, hexp), ice, lw=5, shade_amt=0.2, hi_size=0.6, alpha=0.95, ink=hex2rgb("#3a5a8a"))
        for k in range(4):
            a = k * 1.7 + 0.3
            stroke(ctx, lambda c, a=a: (c.move_to(x, y), c.line_to(x + math.cos(a) * 0.55 * PPU, y + math.sin(a) * 0.4 * PPU)), (1, 1, 1), 2.5, 0.8)
        sparkle(ctx, x - 0.4 * PPU, y - 0.2 * PPU, 10)

    # fortress walls along the edges with battlements; gaps (gates) wherever a lane passes
    wall = hex2rgb("#8a94a8")
    wall_top = hex2rgb("#b4bccc")
    T = 0.85 * PPU            # wall thickness
    gap = LANE_HALF + 0.45 * PPU

    def wall_run(ax, ay, bx, by, inward):
        """Splits a wall line into blocks; returns runs of consecutive blocks clear of every lane."""
        L = math.hypot(bx - ax, by - ay)
        n = int(L / (0.5 * PPU))
        runs, cur = [], []
        for k in range(n):
            t0, t1 = k / n, (k + 1) / n
            mx, my = ax + (bx - ax) * (t0 + t1) / 2 + inward[0] * T / 2, ay + (by - ay) * (t0 + t1) / 2 + inward[1] * T / 2
            if lane_d(mx, my) < gap + T * 0.5:
                if cur:
                    runs.append(cur)
                cur = []
            else:
                cur.append((t0, t1))
        if cur:
            runs.append(cur)
        return [(ax + (bx - ax) * r[0][0], ay + (by - ay) * r[0][0], ax + (bx - ax) * r[-1][1], ay + (by - ay) * r[-1][1]) for r in runs]

    top_y, bot_y = to_px(0, 6.75)[1], to_px(0, -6.75)[1]
    left_x, right_x = to_px(-12.5, 0)[0], to_px(12.5, 0)[0]
    lines = [((left_x, top_y), (right_x, top_y), (0, -1)), ((left_x, bot_y), (right_x, bot_y), (0, 1)),
             ((left_x, top_y), (left_x, bot_y), (-1, 0)), ((right_x, top_y), (right_x, bot_y), (1, 0))]
    towers = []
    for (a, b, out) in lines:
        # the wall body extends outward from the line (toward the canvas edge)
        for (sx, sy, ex, ey) in wall_run(a[0], a[1], b[0], b[1], out):
            if math.hypot(ex - sx, ey - sy) < 0.6 * PPU:
                continue
            towers += [(sx, sy), (ex, ey)]
            if out[1] != 0:      # horizontal wall: seen as a front face with merlons
                ytop = sy + (-T if out[1] < 0 else 0)
                flat(ctx, lambda c: rrect_path(c, sx, ytop + T + 6, ex - sx, 22, 8), (0.1, 0.12, 0.2), 0.25)
                paint(ctx, lambda c: rrect_path(c, sx, ytop, ex - sx, T, 6), wall, lw=6, shade_amt=0.2, hi=False)
                bw = 0.5 * PPU
                k = 0
                xx = sx
                while xx < ex - 4:
                    bwk = min(bw, ex - xx)
                    yy = ytop + (k % 2) * T / 2
                    stroke(ctx, lambda c, xx=xx, yy=yy: (c.move_to(xx, yy), c.line_to(xx, yy + T / 2)), shade(wall, 0.4), 3, 0.7)
                    xx += bwk
                    k += 1
                stroke(ctx, lambda c: (c.move_to(sx, ytop + T / 2), c.line_to(ex, ytop + T / 2)), shade(wall, 0.4), 3, 0.7)
                xx = sx + 6
                while xx < ex - 26:
                    paint(ctx, lambda c, xx=xx: rrect_path(c, xx, ytop - 22, 26, 26, 4), wall_top, lw=5, shade_amt=0.2, hi=False)
                    flat(ctx, lambda c, xx=xx: rrect_path(c, xx + 2, ytop - 24, 22, 8, 4), (1, 1, 1), 0.95)
                    xx += 46
                flat(ctx, lambda c: rrect_path(c, sx + 4, ytop - 2, ex - sx - 8, 10, 5), (0.98, 0.99, 1.0), 0.9)
            else:                # vertical wall: top of the rampart walk with crenellations on the inner edge
                xl = sx - (T if out[0] < 0 else 0)
                flat(ctx, lambda c: rrect_path(c, xl - (10 if out[0] > 0 else -10), sy, T, ey - sy, 8), (0.1, 0.12, 0.2), 0.22)
                paint(ctx, lambda c: rrect_path(c, xl, sy, T, ey - sy, 6), wall_top, lw=6, shade_amt=0.15, hi=False)
                yy = sy + 6
                while yy < ey - 26:
                    mx = xl + (T - 24 if out[0] < 0 else 0)
                    paint(ctx, lambda c, mx=mx, yy=yy: rrect_path(c, mx, yy, 24, 26, 4), wall, lw=4.5, shade_amt=0.2, hi=False)
                    flat(ctx, lambda c, mx=mx, yy=yy: rrect_path(c, mx + 2, yy + 2, 20, 9, 4), (1, 1, 1), 0.9)
                    yy += 46
                for k in range(int((ey - sy) / 60)):
                    flat(ctx, lambda c, k=k: ellipse_path(c, xl + T / 2 + rnd.uniform(-8, 8), sy + 30 + k * 60, 16, 10), (1, 1, 1), 0.7)
    # round towers at every wall end (flanking the gates) — only where clear of lanes
    stone_t = hex2rgb("#9aa4b8")
    for (x, y) in towers:
        r = 0.62 * PPU
        if lane_d(x, y) < r + LANE_HALF * 0.6:
            continue
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x + 8, y + 14, r * 1.05, r * 0.8), (0.1, 0.12, 0.2), 0.3)
        paint(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, r, r * 0.85), stone_t, lw=6, shade_amt=0.25, hi_size=0.6)
        for k in range(8):
            a = k * math.pi / 4
            paint(ctx, lambda c, a=a, x=x, y=y: rrect_path(c, x + math.cos(a) * r * 0.78 - 9, y + math.sin(a) * r * 0.66 - 9, 18, 18, 4),
                  wall_top, lw=4, hi=False, shade_amt=0.2)
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x - 4, y - 4, r * 0.5, r * 0.38), (1, 1, 1), 0.9)

    # snow drifts and frozen props (off lanes, nodes, plaza, covers, walls)
    def free(x, y, d):
        if math.hypot(x - cx, (y - cy) / 0.8) < plaza_r + 40:
            return False
        if lane_d(x, y) < LANE_HALF + d:
            return False
        if any(math.hypot(x - nx, y - ny) < 0.8 * PPU + d for nx, ny in nodes):
            return False
        if any(math.hypot(x - px, y - py) < pr + d for (px, py), pr in covers):
            return False
        if not (left_x + T * 0.6 + d < x < right_x - T * 0.6 - d and top_y + 30 + d < y < bot_y - 10 - d):
            return False
        return True

    for _ in range(220):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.uniform(30, 70)
        if not free(x, y, r * 0.6):
            continue
        pts = [(x - r, y + 6), (x - r * 0.5, y - r * 0.32), (x + r * 0.2, y - r * 0.42), (x + r, y + 2), (x + r * 0.3, y + r * 0.25),
               (x - r * 0.5, y + r * 0.22)]
        paint(ctx, lambda c, pts=pts: smooth_closed(c, pts, 0.5), (0.97, 0.98, 1.0), lw=0, shade_amt=0.3, hi=False, outline=False)
        stroke(ctx, lambda c, x=x, y=y, r=r: smooth_open(c, [(x - r * 0.8, y - 2), (x, y - r * 0.36), (x + r * 0.8, y - 2)]), snow_sh, 3, 0.6)
    rock = hex2rgb("#7a869c")
    for _ in range(40):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.uniform(16, 32)
        if not free(x, y, r + 10):
            continue
        pts = [(x + math.cos(a) * r * rnd.uniform(0.75, 1.1), y + math.sin(a) * r * 0.7 * rnd.uniform(0.75, 1.1)) for a in
               [k * 2 * math.pi / 7 for k in range(7)]]
        flat(ctx, lambda c: ellipse_path(c, x + 4, y + r * 0.5, r * 1.05, r * 0.35), (0.1, 0.12, 0.25), 0.2)
        paint(ctx, lambda c, pts=pts: smooth_closed(c, pts, 0.4), rock, lw=5, shade_amt=0.3)
        flat(ctx, lambda c: ellipse_path(c, x - r * 0.1, y - r * 0.45, r * 0.7, r * 0.25), (1, 1, 1), 0.95)
    # frozen braziers (blue fire) — fixed, symmetric spots, skipped if a lane is close
    for (wx, wy) in ((-7.6, 4.4), (7.6, -4.4), (-9.6, -5.2), (9.6, 5.0), (-5.6, 4.9), (5.6, -4.9)):
        x, y = to_px(wx, wy)
        if not free(x, y, 30):
            continue
        flat(ctx, lambda c: ellipse_path(c, x + 6, y + 8, 40, 14), (0.1, 0.12, 0.25), 0.25)
        paint(ctx, lambda c: poly_path(c, [(x - 16, y), (x - 24, y - 60), (x + 24, y - 60), (x + 16, y)]), hex2rgb("#6a7488"), lw=5, shade_amt=0.25)
        paint(ctx, lambda c: ellipse_path(c, x, y - 64, 34, 12), hex2rgb("#8a94a8"), lw=5, hi=False)
        glow(ctx, x, y - 84, 50, hex2rgb("#7fe8ff"), 0.6)
        paint(ctx, lambda c: smooth_closed(c, [(x - 20, y - 66), (x - 14, y - 92), (x - 4, y - 82), (x + 2, y - 112), (x + 12, y - 86), (x + 20, y - 66)], 0.4),
              hex2rgb("#9af0ff"), lw=4, hi=False, shade_amt=0)
        flat(ctx, lambda c: smooth_closed(c, [(x - 9, y - 68), (x, y - 92), (x + 9, y - 68)], 0.5), (1, 1, 1), 0.9)
    # falling snow
    for _ in range(320):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 2.6, 2.6), (1, 1, 1), rnd.uniform(0.4, 0.85))

    _portals(ctx, arena, hex2rgb("#7a9aff"), hex2rgb("#c8d8ff"))
    return cv


# ---------------------------------------------------------------------------------------------------
# shared helpers for the aether / storm / archive biomes


def _dense(ctx, pts):
    """Flattened points of the smoothed lane curve (same curve smooth_open strokes)."""
    ctx.save()
    ctx.new_path()
    smooth_open(ctx, pts)
    flat_pts = [pp for kind, pp in ctx.copy_path_flat() if kind in (cairo.PATH_MOVE_TO, cairo.PATH_LINE_TO)]
    ctx.new_path()
    ctx.restore()
    return flat_pts


def _resample(dense, step):
    """(x, y, angle) every `step` px along a dense polyline."""
    out = []
    carry = 0.0
    for (ax, ay), (bx, by) in zip(dense[:-1], dense[1:]):
        L = math.hypot(bx - ax, by - ay)
        if L <= 0:
            continue
        ang = math.atan2(by - ay, bx - ax)
        t = carry
        while t < L:
            out.append((ax + (bx - ax) * t / L, ay + (by - ay) * t / L, ang))
            t += step
        carry = t - L
    return out


def _blob(rnd, x, y, rx, ry, n=12, jit=(0.86, 1.08)):
    return [(x + math.cos(k * 2 * math.pi / n) * rx * rnd.uniform(*jit), y + math.sin(k * 2 * math.pi / n) * ry * rnd.uniform(*jit))
            for k in range(n)]


def _best_spot(x, y, r, lane_d, prefer=-math.pi / 2, n=16):
    """Point at distance r around (x, y) farthest from any lane (ties broken toward `prefer`)."""
    best, best_s = None, -1e9
    for k in range(n):
        a = prefer + k * 2 * math.pi / n
        px, py = x + math.cos(a) * r, y + math.sin(a) * r * 0.8
        s = lane_d(px, py) + 12 * math.cos(a - prefer)
        if s > best_s:
            best, best_s = (px, py), s
    return best


def _paved_lane(ctx, dense, edge, body, joint, width, step, alpha=1.0):
    """A paved strip along a lane: dark edge, slab body, cross joints."""
    for col, wf, a in ((edge, 1.0, 0.95), (body, 0.86, 1.0)):
        ctx.save()
        ctx.new_path()
        poly = dense
        ctx.move_to(*poly[0])
        for p in poly[1:]:
            ctx.line_to(*p)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_source_rgba(*col, a * alpha)
        ctx.set_line_width(width * wf)
        ctx.stroke()
        ctx.restore()
    hw = width * 0.43
    for i, (x, y, ang) in enumerate(_resample(dense, step)):
        nx, ny = -math.sin(ang), math.cos(ang)
        off = (step * 0.5) if i % 2 else 0
        tx, ty = math.cos(ang) * off, math.sin(ang) * off
        stroke(ctx, lambda c, x=x, y=y, nx=nx, ny=ny: (c.move_to(x - nx * hw, y - ny * hw), c.line_to(x + nx * hw, y + ny * hw)),
               joint, 3, 0.55 * alpha)
        # staggered half joint along the centre
        stroke(ctx, lambda c, x=x, y=y, tx=tx, ty=ty, nx=nx, ny=ny: (c.move_to(x + tx, y + ty), c.line_to(x + tx + nx * hw * 0.02, y + ty + ny * hw * 0.02)),
               joint, 2, 0.3 * alpha)
    # long seam down the middle
    ctx.save()
    ctx.new_path()
    ctx.move_to(*dense[0])
    for p in dense[1:]:
        ctx.line_to(*p)
    ctx.set_source_rgba(*joint, 0.35 * alpha)
    ctx.set_line_width(2.5)
    ctx.stroke()
    ctx.restore()


def _wall_runs(lane_d, ax, ay, bx, by, inward, T, gap):
    """Splits a wall line into blocks; returns runs of consecutive blocks clear of every lane."""
    L = math.hypot(bx - ax, by - ay)
    n = int(L / (0.5 * PPU))
    runs, cur = [], []
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n
        mx, my = ax + (bx - ax) * (t0 + t1) / 2 + inward[0] * T / 2, ay + (by - ay) * (t0 + t1) / 2 + inward[1] * T / 2
        if lane_d(mx, my) < gap + T * 0.5:
            if cur:
                runs.append(cur)
            cur = []
        else:
            cur.append((t0, t1))
    if cur:
        runs.append(cur)
    return [(ax + (bx - ax) * r[0][0], ay + (by - ay) * r[0][0], ax + (bx - ax) * r[-1][1], ay + (by - ay) * r[-1][1]) for r in runs]


# ---------------------------------------------------------------------------------------------------
# Shattered Aether: floating islands over a starry violet rift


def _aether_background(arena, biome):
    w, h = int(WORLD_W * PPU), int(WORLD_H * PPU)
    cv = Canvas(w, h)
    ctx = cv.ctx
    rnd = random.Random(9091)
    magenta = hex2rgb("#e05aff")
    violet = hex2rgb("#8a5cff")
    cyan = hex2rgb("#7ad8ff")
    # the void: deep violet with nebula clouds and stars
    grad = cairo.RadialGradient(w / 2, h / 2, 80, w / 2, h / 2, w * 0.65)
    grad.add_color_stop_rgb(0, *hex2rgb("#34205a"))
    grad.add_color_stop_rgb(0.6, *hex2rgb("#1d1236"))
    grad.add_color_stop_rgb(1, *hex2rgb("#0a0616"))
    ctx.set_source(grad)
    ctx.paint()
    for _ in range(26):
        glow(ctx, rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(160, 420), rnd.choice([magenta, violet, hex2rgb("#4a6aff")]),
             rnd.uniform(0.08, 0.2))
    # a great rift tearing diagonally through the void
    rift = [(-60, h * 0.95), (w * 0.22, h * 0.72), (w * 0.5, h * 0.52), (w * 0.78, h * 0.3), (w + 60, h * 0.05)]
    for col, lw, a in ((violet, 260, 0.10), (magenta, 120, 0.12), (hex2rgb("#ffb0ff"), 22, 0.18)):
        stroke(ctx, lambda c: smooth_open(c, rift), col, lw, a)
    for _ in range(900):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.uniform(0.8, 2.4)
        flat(ctx, lambda c, x=x, y=y, r=r: ellipse_path(c, x, y, r, r), rnd.choice([(1, 1, 1), light(cyan, 0.5), light(magenta, 0.6)]),
             rnd.uniform(0.3, 0.9))
    for _ in range(45):
        sparkle(ctx, rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(5, 11), (1, 1, 1), rnd.uniform(0.5, 0.9))

    lanes = _lane_paths(arena)
    dense = [_dense(ctx, pts) for pts in lanes]
    cx, cy = to_px(0, 0)
    nodes = [to_px(*n) for n in arena["nodes"]]
    rifts = [to_px(*p) for hz in biome.get("hazards", []) for p in hz.get("points", [])]

    def lane_d(x, y):
        return min(_poly_dist(x, y, pts) for pts in lanes)

    # islands: a central isle holding the plaza and every node, plus isles under each rift and lane bend
    islands = [_blob(rnd, cx, cy, 6.0 * PPU, 4.7 * PPU, n=20, jit=(0.94, 1.04))]
    centres = rifts + [to_px(*lane["points"][1]) for lane in arena["lanes"]]
    for (x, y) in centres:
        r = rnd.uniform(1.45, 1.75) * PPU
        islands.append(_blob(rnd, x, y, r, r * 0.78, n=11))
    # distant fragments drifting in the void (smaller, clear of lanes)
    fragments = []
    for _ in range(400):
        if len(fragments) >= 16:
            break
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.uniform(0.35, 0.8) * PPU
        if lane_d(x, y) < r + LANE_HALF + 0.4 * PPU:
            continue
        if any(_poly_dist(x, y, pts + pts[:1]) < r + 0.6 * PPU or _inside(ctx, pts, x, y) for pts in islands):
            continue
        if any(math.hypot(x - fx, y - fy) < r + fr + 30 for fx, fy, fr in fragments):
            continue
        fragments.append((x, y, r))

    rock_top = hex2rgb("#6c6488")
    rock_side = hex2rgb("#3a2f58")
    moss = hex2rgb("#5a8a9a")

    def underside(pts, depth):
        ys = [p[1] for p in pts]
        ymid = (max(ys) + min(ys)) / 2
        span = max(max(ys) - ymid, 1)
        xmid = sum(p[0] for p in pts) / len(pts)
        out = []
        for (x, y) in pts:
            f = max(0.0, (y - ymid) / span)
            out.append((x + (xmid - x) * 0.3 * f, y + depth * (0.3 + 0.9 * f) * rnd.uniform(0.8, 1.2)))
        return out

    for (x, y, r) in fragments:
        pts = _blob(rnd, x, y, r, r * 0.7, n=8)
        paint(ctx, lambda c, pts=underside(pts, r * 0.8): smooth_closed(c, pts, 0.35), rock_side, lw=4, shade_amt=0.3, hi=False, alpha=0.85)
        paint(ctx, lambda c, pts=pts: smooth_closed(c, pts, 0.4), mix(rock_top, hex2rgb("#2a2040"), 0.35), lw=4, shade_amt=0.2, hi=False,
              alpha=0.9)
    # island undersides (cliffs + hanging crystal roots), then the tops
    for i, pts in enumerate(islands):
        depth = (1.3 if i == 0 else 0.9) * PPU
        low = underside(pts, depth)
        glow(ctx, sum(p[0] for p in low) / len(low), max(p[1] for p in low), depth * 1.4, violet, 0.25)
        paint(ctx, lambda c, low=low: smooth_closed(c, low, 0.4), rock_side, lw=6, shade_amt=0.35, hi=False)
        for k in range(len(low)):
            x, y = low[k]
            if y < max(p[1] for p in low) - depth * 0.7:
                continue
            hh = rnd.uniform(0.25, 0.6) * PPU
            paint(ctx, lambda c, x=x, y=y, hh=hh: poly_path(c, [(x - 12, y - 8), (x + rnd.uniform(-5, 5), y + hh), (x + 12, y - 8)]),
                  rock_side, lw=4, shade_amt=0.25, hi=False)
            if rnd.random() < 0.5:
                flat(ctx, lambda c, x=x, y=y, hh=hh: poly_path(c, [(x - 4, y), (x, y + hh * 0.7), (x + 4, y)]), light(magenta, 0.3), 0.8)
        # strata lines on the cliff face
        for s in (0.4, 0.7):
            mid = [(px, py + (ly - py) * s) for (px, py), (lx, ly) in zip(pts, low)]
            stroke(ctx, lambda c, mid=mid: smooth_closed(c, mid, 0.4), shade(rock_side, 0.4), 3, 0.5)
    for i, pts in enumerate(islands):
        paint(ctx, lambda c, pts=pts: smooth_closed(c, pts, 0.4), rock_top, lw=6, shade_amt=0.18, hi_size=0.6)
        ctx.save()
        ctx.new_path()
        smooth_closed(ctx, pts, 0.4)
        ctx.clip()
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        for _ in range(int((max(xs) - min(xs)) * (max(ys) - min(ys)) / 2600)):
            x, y = rnd.uniform(min(xs), max(xs)), rnd.uniform(min(ys), max(ys))
            r = rnd.uniform(14, 46)
            col = mix(rock_top, rnd.choice([moss, hex2rgb("#7a6aa0"), hex2rgb("#544c6c")]), rnd.uniform(0.3, 0.7))
            flat(ctx, lambda c, x=x, y=y, r=r: ellipse_path(c, x, y, r, r * 0.65, rnd.uniform(0, 3)), col, 0.3)
        # rim highlight along the far (upper) edge
        stroke(ctx, lambda c, pts=pts: smooth_closed(c, [(x, y + 7) for x, y in pts], 0.4), light(rock_top, 0.35), 5, 0.5)
        ctx.restore()

    # stone causeways along the lanes: arched bridges over the void, paved on the islands
    stone = hex2rgb("#9a90b4")
    for d in dense:
        stroke(ctx, lambda c, d=d: (c.move_to(d[0][0], d[0][1] + 26), [c.line_to(x, y + 26) for x, y in d[1:]]), (0.03, 0.01, 0.08), 1.5 * PPU, 0.45)
        stroke(ctx, lambda c, d=d: (c.move_to(d[0][0], d[0][1] + 14), [c.line_to(x, y + 14) for x, y in d[1:]]), rock_side, 1.6 * PPU, 1.0)
    for d in dense:
        _paved_lane(ctx, d, hex2rgb("#2a2040"), stone, shade(stone, 0.45), 1.7 * PPU, 0.5 * PPU)
    # curbs + rune posts only where the causeway crosses open void
    for d in dense:
        for i, (x, y, ang) in enumerate(_resample(d, 0.62 * PPU)):
            if any(_inside(ctx, pts, x, y) for pts in islands):
                continue
            nx, ny = -math.sin(ang), math.cos(ang)
            for sgn in (-1, 1):
                px, py = x + nx * sgn * 0.76 * PPU, y + ny * sgn * 0.76 * PPU
                paint(ctx, lambda c, px=px, py=py: rrect_path(c, px - 9, py - 9, 18, 18, 4), light(stone, 0.12), lw=3.5, hi=False, shade_amt=0.25)
                if i % 3 == 0:
                    glow(ctx, px, py - 4, 16, magenta, 0.5)

    # central plaza with a magenta rune ring
    plaza_r = 2.9 * PPU
    _plaza(ctx, rnd, cx, cy, plaza_r, hex2rgb("#8a80a8"), [hex2rgb("#a89ccc"), hex2rgb("#5e5480")], hex2rgb("#3a3056"),
           hex2rgb("#f08aff"), hex2rgb("#22163a"))

    # aether rifts at hazard points: dark tear with swirling magenta-violet arms
    for (x, y) in rifts:
        glow(ctx, x, y, 1.15 * PPU, magenta, 0.4)
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 0.62 * PPU, 0.46 * PPU), hex2rgb("#120826"), 0.55)
        for arm in range(4):
            a0 = arm * math.pi / 2 + 0.3
            sp = [(x + math.cos(a0 + t * 2.4) * (0.12 + 0.5 * t) * PPU, y + math.sin(a0 + t * 2.4) * (0.12 + 0.5 * t) * 0.72 * PPU)
                  for t in [k / 8.0 for k in range(9)]]
            stroke(ctx, lambda c, sp=sp: smooth_open(c, sp), violet, 9, 0.75)
            stroke(ctx, lambda c, sp=sp: smooth_open(c, sp), light(magenta, 0.25), 3.5, 0.9)
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 0.13 * PPU, 0.09 * PPU), (0.04, 0.0, 0.08), 1.0)
        stroke(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 0.15 * PPU, 0.11 * PPU), hex2rgb("#ffc8ff"), 2.5, 0.9)
        for k in range(5):
            a = rnd.uniform(0, 2 * math.pi)
            rr = rnd.uniform(0.55, 0.8) * PPU
            sparkle(ctx, x + math.cos(a) * rr, y + math.sin(a) * rr * 0.72, rnd.uniform(5, 9), light(magenta, 0.6), 0.85)

    # aether nodes: cyan-violet wellspring with orbiting shards
    for t in biome.get("nodeTraits", []):
        x, y = nodes[t["node"]]
        glow(ctx, x, y, 1.2 * PPU, cyan, 0.4)
        glow(ctx, x, y, 0.8 * PPU, violet, 0.45)
        stroke(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 0.8 * PPU, 0.58 * PPU), light(cyan, 0.3), 4, 0.8)
        stroke(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 0.92 * PPU, 0.67 * PPU), violet, 2, 0.6)
        for k in range(6):
            a = k * math.pi / 3 + 0.25
            sx, sy = x + math.cos(a) * 0.86 * PPU, y + math.sin(a) * 0.62 * PPU - 10
            flat(ctx, lambda c, sx=sx, sy=sy: ellipse_path(c, sx, sy + 18, 8, 3), (0, 0, 0), 0.3)
            paint(ctx, lambda c, sx=sx, sy=sy: poly_path(c, [(sx, sy - 16), (sx + 7, sy), (sx, sy + 9), (sx - 7, sy)]), hex2rgb("#a8e8ff"),
                  lw=3, shade_amt=0.3, hi=False, ink=hex2rgb("#2a1a5a"))
        sparkle(ctx, x - 0.45 * PPU, y - 0.35 * PPU, 10, (1, 1, 1), 0.9)

    # decor on the islands: aether crystal clusters and rubble (off lanes, nodes, plaza, rifts)
    def free(x, y, d):
        if math.hypot(x - cx, (y - cy) / 0.8) < plaza_r + 40:
            return False
        if lane_d(x, y) < LANE_HALF + d:
            return False
        if any(math.hypot(x - nx, y - ny) < 0.95 * PPU + d for nx, ny in nodes):
            return False
        if any(math.hypot(x - rx, y - ry) < 0.95 * PPU + d for rx, ry in rifts):
            return False
        return any(_inside(ctx, pts, x, y) and _poly_dist(x, y, pts + pts[:1]) > d + 10 for pts in islands)

    for _ in range(700):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        if not free(x, y, 30):
            continue
        flat(ctx, lambda c: ellipse_path(c, x + 4, y + 4, 30, 10), (0.05, 0.02, 0.1), 0.35)
        glow(ctx, x, y - 20, 40, violet, 0.3)
        for k in range(rnd.randint(2, 4)):
            ox, hh = rnd.uniform(-16, 16), rnd.uniform(26, 56)
            col = rnd.choice([hex2rgb("#c08aff"), hex2rgb("#8ad8ff"), hex2rgb("#e090ff")])
            paint(ctx, lambda c, ox=ox, hh=hh: poly_path(c, [(x + ox - 8, y), (x + ox + rnd.uniform(-5, 5), y - hh), (x + ox + 8, y)]),
                  col, lw=3.5, shade_amt=0.3, hi_size=0.5, ink=hex2rgb("#24123e"))
            stroke(ctx, lambda c, ox=ox, hh=hh: (c.move_to(x + ox - 2, y - 4), c.line_to(x + ox, y - hh * 0.8)), (1, 1, 1), 1.6, 0.6)
    for _ in range(160):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.uniform(10, 22)
        if not free(x, y, r + 6):
            continue
        pts = _blob(rnd, x, y, r, r * 0.7, n=7, jit=(0.75, 1.1))
        flat(ctx, lambda c: ellipse_path(c, x + 3, y + r * 0.5, r, r * 0.3), (0.05, 0.02, 0.1), 0.3)
        paint(ctx, lambda c, pts=pts: smooth_closed(c, pts, 0.4), hex2rgb("#5c5478"), lw=4, shade_amt=0.3, hi=False)
    # drifting aether motes everywhere except on the lanes
    for _ in range(260):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        if lane_d(x, y) < LANE_HALF:
            continue
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 2.4, 2.4), rnd.choice([magenta, cyan, (1, 1, 1)]), rnd.uniform(0.35, 0.85))

    _portals(ctx, arena, hex2rgb("#c25aff"), hex2rgb("#f4c4ff"))
    return cv


def _inside(ctx, pts, x, y):
    ctx.save()
    ctx.new_path()
    smooth_closed(ctx, pts, 0.4)
    hit = ctx.in_fill(x, y)
    ctx.new_path()
    ctx.restore()
    return hit


# ---------------------------------------------------------------------------------------------------
# Stormspire Citadel: storm-grey courtyard on a mountain peak


def _storm_background(arena, biome):
    w, h = int(WORLD_W * PPU), int(WORLD_H * PPU)
    cv = Canvas(w, h)
    ctx = cv.ctx
    rnd = random.Random(5150)
    bolt = hex2rgb("#9adcff")
    # the mountain falling away beyond the walls
    _base(ctx, w, h, rnd, hex2rgb("#4a505e"), hex2rgb("#1a1d26"), hex2rgb("#5c6270"),
          [hex2rgb("#2e323e"), hex2rgb("#626878"), hex2rgb("#3c4250")], n=600, alpha=0.25)
    lanes = _lane_paths(arena)
    dense = [_dense(ctx, pts) for pts in lanes]
    cx, cy = to_px(0, 0)
    nodes = [to_px(*n) for n in arena["nodes"]]
    strikes = [to_px(*p) for hz in biome.get("hazards", []) for p in hz.get("points", [])]

    def lane_d(x, y):
        return min(_poly_dist(x, y, pts) for pts in lanes)

    top_y, bot_y = to_px(0, 6.75)[1], to_px(0, -6.75)[1]
    left_x, right_x = to_px(-12.5, 0)[0], to_px(12.5, 0)[0]
    # crags on the slopes outside the courtyard
    crag = hex2rgb("#3c414e")
    for _ in range(500):
        x, y = rnd.uniform(-40, w + 40), rnd.uniform(-40, h + 40)
        if left_x - 10 < x < right_x + 10 and top_y - 10 < y < bot_y + 10:
            continue
        r = rnd.uniform(26, 70)
        pts = [(x - r, y + r * 0.3), (x - r * 0.3 + rnd.uniform(-8, 8), y - r * rnd.uniform(0.5, 0.9)), (x + r * 0.2, y - r * rnd.uniform(0.3, 0.6)),
               (x + r, y + r * 0.3)]
        paint(ctx, lambda c, pts=pts: poly_path(c, pts), mix(crag, rnd.choice([hex2rgb("#5a6070"), hex2rgb("#262a34")]), rnd.uniform(0.1, 0.5)),
              lw=4, shade_amt=0.35, hi=False, alpha=0.9)
    # courtyard flagstones
    flag = hex2rgb("#6c7282")
    flat(ctx, lambda c: rrect_path(c, left_x, top_y, right_x - left_x, bot_y - top_y, 10), flag, 1.0)
    tile = 0.82 * PPU
    row = 0
    y = top_y
    while y < bot_y:
        x = left_x - (tile / 2 if row % 2 else 0)
        while x < right_x:
            col = mix(flag, rnd.choice([hex2rgb("#7c8292"), hex2rgb("#5a606e"), hex2rgb("#687080"), hex2rgb("#747a8a")]), rnd.uniform(0.2, 0.8))
            tw = min(tile, right_x - x)
            if x >= left_x - 1 and tw > 8:
                flat(ctx, lambda c, x=x, y=y, tw=tw: rrect_path(c, x + 2, y + 2, tw - 4, min(tile * 0.8, bot_y - y) - 4, 5), col, 0.95)
                stroke(ctx, lambda c, x=x, y=y, tw=tw: rrect_path(c, x + 2, y + 2, tw - 4, min(tile * 0.8, bot_y - y) - 4, 5),
                       hex2rgb("#3a3e4a"), 2.5, 0.55)
            x += tile
        y += tile * 0.8
        row += 1
    # weathering: cracks and rain-darkened patches
    for _ in range(160):
        x, y = rnd.uniform(left_x, right_x), rnd.uniform(top_y, bot_y)
        r = rnd.uniform(30, 90)
        flat(ctx, lambda c, x=x, y=y, r=r: ellipse_path(c, x, y, r, r * 0.6, rnd.uniform(0, 3)), hex2rgb("#3e4452"), 0.12)
    for _ in range(90):
        x, y = rnd.uniform(left_x, right_x), rnd.uniform(top_y, bot_y)
        a = rnd.uniform(0, 2 * math.pi)
        pts = [(x, y)]
        for _k in range(3):
            a += rnd.uniform(-0.7, 0.7)
            L = rnd.uniform(14, 30)
            pts.append((pts[-1][0] + math.cos(a) * L, pts[-1][1] + math.sin(a) * L))
        stroke(ctx, lambda c, pts=pts: smooth_open(c, pts), hex2rgb("#2e323c"), 3, 0.55)

    # worn processional lanes (darker granite slabs)
    for d in dense:
        _paved_lane(ctx, d, hex2rgb("#2c303a"), hex2rgb("#545a68"), hex2rgb("#30343e"), 1.72 * PPU, 0.55 * PPU, alpha=0.92)
    _draw_lanes(ctx, lanes, ((light(hex2rgb("#545a68"), 0.2), 0.7 * PPU, 0.18),))

    # central plaza with a storm-blue rune ring
    plaza_r = 2.9 * PPU
    _plaza(ctx, rnd, cx, cy, plaza_r, hex2rgb("#7a8090"), [hex2rgb("#9098a8"), hex2rgb("#5a6070")], hex2rgb("#3a3e4a"),
           hex2rgb("#8fdcff"), hex2rgb("#262a34"))

    # scorched strike marks at hazard points: burn splash + branching (Lichtenberg) scars
    for (x, y) in strikes:
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 0.85 * PPU, 0.62 * PPU), hex2rgb("#14161c"), 0.35)
        flat(ctx, lambda c, x=x, y=y: star_path(c, x, y, 0.62 * PPU, 0.28 * PPU, 9, rot=0.3), hex2rgb("#101216"), 0.5)
        for k in range(7):
            a = k * 2 * math.pi / 7 + rnd.uniform(-0.2, 0.2)
            pts = [(x, y)]
            ang = a
            for _s in range(4):
                ang += rnd.uniform(-0.5, 0.5)
                L = rnd.uniform(0.13, 0.2) * PPU
                pts.append((pts[-1][0] + math.cos(ang) * L, pts[-1][1] + math.sin(ang) * L * 0.75))
            stroke(ctx, lambda c, pts=pts: poly_path_open(c, pts), (0.05, 0.05, 0.07), 5, 0.8)
            stroke(ctx, lambda c, pts=pts: poly_path_open(c, pts), bolt, 1.8, 0.55)
            bx, by = pts[2]
            b2 = (bx + math.cos(a + 0.8) * 0.18 * PPU, by + math.sin(a + 0.8) * 0.13 * PPU)
            stroke(ctx, lambda c, bx=bx, by=by, b2=b2: (c.move_to(bx, by), c.line_to(*b2)), (0.05, 0.05, 0.07), 3.5, 0.7)
        glow(ctx, x, y, 0.45 * PPU, bolt, 0.4)
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 0.16 * PPU, 0.11 * PPU), hex2rgb("#0a0b0e"), 0.9)
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x - 2, y - 2, 0.06 * PPU, 0.04 * PPU), light(bolt, 0.4), 0.8)

    # lightning-rod pylons at trait nodes: copper ring around the pad and two crackling rods
    copper = hex2rgb("#c0783a")
    for t in biome.get("nodeTraits", []):
        x, y = nodes[t["node"]]
        glow(ctx, x, y, 1.15 * PPU, bolt, 0.4)
        stroke(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 0.8 * PPU, 0.58 * PPU), shade(copper, 0.4), 9, 0.9)
        stroke(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 0.8 * PPU, 0.58 * PPU), copper, 5, 1.0)
        for k in range(8):
            a = k * math.pi / 4 + math.pi / 8
            flat(ctx, lambda c, a=a: ellipse_path(c, x + math.cos(a) * 0.8 * PPU, y + math.sin(a) * 0.58 * PPU, 5, 4), light(copper, 0.4), 0.95)
        tips = []
        for sgn in (-1, 1):
            px, py = x + sgn * 0.98 * PPU, y + 0.12 * PPU
            hh = 1.15 * PPU
            flat(ctx, lambda c, px=px, py=py: ellipse_path(c, px + 6, py + 6, 22, 9), (0.05, 0.05, 0.08), 0.4)
            paint(ctx, lambda c, px=px, py=py: poly_path(c, [(px - 15, py), (px - 10, py - 18), (px + 10, py - 18), (px + 15, py)]),
                  hex2rgb("#4a505e"), lw=4, shade_amt=0.3, hi=False)
            paint(ctx, lambda c, px=px, py=py, hh=hh: rrect_path(c, px - 4.5, py - hh, 9, hh - 16, 3), copper, lw=3.5, shade_amt=0.35, hi=False)
            for ring in (0.35, 0.6):
                paint(ctx, lambda c, px=px, py=py, hh=hh, ring=ring: ellipse_path(c, px, py - hh * ring - 16 * (1 - ring), 9, 4),
                      light(copper, 0.2), lw=2.5, hi=False, shade_amt=0.2)
            paint(ctx, lambda c, px=px, py=py, hh=hh: ellipse_path(c, px, py - hh - 4, 8, 8), hex2rgb("#d8f4ff"), lw=3, hi=False, shade_amt=0.2)
            glow(ctx, px, py - hh - 4, 34, bolt, 0.7)
            tips.append((px, py - hh - 4))
        # arc between the rod tips, bowing over the pad
        (ax, ay), (bx, by) = tips
        arc = [(ax, ay)]
        for k in range(1, 8):
            tt = k / 8.0
            arc.append((ax + (bx - ax) * tt + rnd.uniform(-5, 5), ay + (by - ay) * tt - math.sin(tt * math.pi) * 22 + rnd.uniform(-8, 8)))
        arc.append((bx, by))
        stroke(ctx, lambda c, arc=arc: poly_path_open(c, arc), bolt, 6, 0.45)
        stroke(ctx, lambda c, arc=arc: poly_path_open(c, arc), (1, 1, 1), 2, 0.9)

    # battlements along the courtyard edge with gates wherever a lane passes
    wall = hex2rgb("#596070")
    wall_top = hex2rgb("#7c8494")
    T = 0.85 * PPU
    gap = LANE_HALF + 0.45 * PPU
    lines = [((left_x, top_y), (right_x, top_y), (0, -1)), ((left_x, bot_y), (right_x, bot_y), (0, 1)),
             ((left_x, top_y), (left_x, bot_y), (-1, 0)), ((right_x, top_y), (right_x, bot_y), (1, 0))]
    towers = []
    for (a, b, out) in lines:
        for (sx, sy, ex, ey) in _wall_runs(lane_d, a[0], a[1], b[0], b[1], out, T, gap):
            if math.hypot(ex - sx, ey - sy) < 0.6 * PPU:
                continue
            towers += [(sx, sy), (ex, ey)]
            if out[1] != 0:
                ytop = sy + (-T if out[1] < 0 else 0)
                flat(ctx, lambda c: rrect_path(c, sx, ytop + T + 6, ex - sx, 22, 8), (0.05, 0.06, 0.1), 0.3)
                paint(ctx, lambda c: rrect_path(c, sx, ytop, ex - sx, T, 6), wall, lw=6, shade_amt=0.2, hi=False)
                k = 0
                xx = sx
                while xx < ex - 4:
                    yy = ytop + (k % 2) * T / 2
                    stroke(ctx, lambda c, xx=xx, yy=yy: (c.move_to(xx, yy), c.line_to(xx, yy + T / 2)), shade(wall, 0.4), 3, 0.7)
                    xx += 0.5 * PPU
                    k += 1
                stroke(ctx, lambda c: (c.move_to(sx, ytop + T / 2), c.line_to(ex, ytop + T / 2)), shade(wall, 0.4), 3, 0.7)
                xx = sx + 6
                while xx < ex - 26:
                    paint(ctx, lambda c, xx=xx: rrect_path(c, xx, ytop - 22, 26, 26, 4), wall_top, lw=5, shade_amt=0.25, hi=False)
                    xx += 46
                flat(ctx, lambda c: rrect_path(c, sx + 4, ytop - 1, ex - sx - 8, 6, 3), light(wall_top, 0.25), 0.6)
            else:
                xl = sx - (T if out[0] < 0 else 0)
                flat(ctx, lambda c: rrect_path(c, xl - (10 if out[0] > 0 else -10), sy, T, ey - sy, 8), (0.05, 0.06, 0.1), 0.28)
                paint(ctx, lambda c: rrect_path(c, xl, sy, T, ey - sy, 6), wall_top, lw=6, shade_amt=0.15, hi=False)
                yy = sy + 6
                while yy < ey - 26:
                    mx = xl + (T - 24 if out[0] < 0 else 0)
                    paint(ctx, lambda c, mx=mx, yy=yy: rrect_path(c, mx, yy, 24, 26, 4), wall, lw=4.5, shade_amt=0.25, hi=False)
                    yy += 46
    banner = hex2rgb("#2a5a9a")
    for (x, y) in towers:
        r = 0.62 * PPU
        if lane_d(x, y) < r + LANE_HALF * 0.6:
            continue
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x + 8, y + 14, r * 1.05, r * 0.8), (0.05, 0.06, 0.1), 0.35)
        paint(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, r, r * 0.85), hex2rgb("#6a7282"), lw=6, shade_amt=0.25, hi_size=0.6)
        for k in range(8):
            a = k * math.pi / 4
            paint(ctx, lambda c, a=a, x=x, y=y: rrect_path(c, x + math.cos(a) * r * 0.78 - 9, y + math.sin(a) * r * 0.66 - 9, 18, 18, 4),
                  wall_top, lw=4, hi=False, shade_amt=0.2)
        # storm beacon on each tower
        glow(ctx, x, y - 4, r * 0.9, bolt, 0.45)
        paint(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y - 4, 11, 11), hex2rgb("#cdeeff"), lw=3, hi=False, shade_amt=0.15)
        paint(ctx, lambda c, x=x, y=y: poly_path(c, [(x - 2, y - 8), (x - 2, y - 52), (x + 26, y - 44), (x + 2, y - 36)]), banner, lw=3,
              shade_amt=0.25, hi=False)

    # props in the courtyard: rubble, rain puddles, storm braziers (off lanes, nodes, plaza, strikes, walls)
    def free(x, y, d):
        if math.hypot(x - cx, (y - cy) / 0.8) < plaza_r + 40:
            return False
        if lane_d(x, y) < LANE_HALF + d:
            return False
        if any(math.hypot(x - nx, y - ny) < 1.0 * PPU + d for nx, ny in nodes):
            return False
        if any(math.hypot(x - sx_, y - sy_) < 0.9 * PPU + d for sx_, sy_ in strikes):
            return False
        return left_x + T * 0.6 + d < x < right_x - T * 0.6 - d and top_y + 30 + d < y < bot_y - 10 - d

    for _ in range(140):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.uniform(24, 60)
        if not free(x, y, r):
            continue
        pts = _blob(rnd, x, y, r, r * 0.5, n=9)
        flat(ctx, lambda c, pts=pts: smooth_closed(c, pts, 0.5), hex2rgb("#2e3a4c"), 0.55)
        stroke(ctx, lambda c, x=x, y=y, r=r: (c.move_to(x - r * 0.5, y - r * 0.12), c.line_to(x + r * 0.2, y - r * 0.18)), hex2rgb("#a8c8e0"), 3, 0.5)
    rock = hex2rgb("#626a7a")
    for _ in range(90):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.uniform(12, 26)
        if not free(x, y, r + 8):
            continue
        for k in range(rnd.randint(1, 3)):
            ox, oy = rnd.uniform(-r, r), rnd.uniform(-r * 0.5, r * 0.5)
            rr = r * rnd.uniform(0.5, 0.9)
            flat(ctx, lambda c, ox=ox, oy=oy, rr=rr: ellipse_path(c, x + ox + 3, y + oy + rr * 0.45, rr, rr * 0.3), (0.05, 0.06, 0.1), 0.3)
            paint(ctx, lambda c, ox=ox, oy=oy, rr=rr: rrect_path(c, x + ox - rr, y + oy - rr * 0.6, rr * 2, rr * 1.2, 5), rock, lw=4,
                  shade_amt=0.3, hi=False)
    for (wx, wy) in ((-7.0, 5.2), (7.0, -5.2), (-10.4, 3.6), (10.4, -3.6), (-10.0, -4.6), (10.0, 4.6), (-5.0, -5.4), (5.0, 5.4)):
        x, y = to_px(wx, wy)
        if not free(x, y, 30):
            continue
        flat(ctx, lambda c: ellipse_path(c, x + 6, y + 8, 40, 14), (0.05, 0.06, 0.1), 0.3)
        paint(ctx, lambda c: poly_path(c, [(x - 16, y), (x - 24, y - 60), (x + 24, y - 60), (x + 16, y)]), hex2rgb("#4a505e"), lw=5, shade_amt=0.25)
        paint(ctx, lambda c: ellipse_path(c, x, y - 64, 34, 12), hex2rgb("#6a7282"), lw=5, hi=False)
        glow(ctx, x, y - 84, 56, bolt, 0.6)
        paint(ctx, lambda c: smooth_closed(c, [(x - 20, y - 66), (x - 14, y - 92), (x - 4, y - 82), (x + 2, y - 112), (x + 12, y - 86), (x + 20, y - 66)], 0.4),
              hex2rgb("#a8e4ff"), lw=4, hi=False, shade_amt=0)
        flat(ctx, lambda c: smooth_closed(c, [(x - 9, y - 68), (x, y - 92), (x + 9, y - 68)], 0.5), (1, 1, 1), 0.9)

    # dark storm clouds rolling around the peak (outside the walls, never over a lane)
    cloud_dark = hex2rgb("#1c1f28")
    cloud_mid = hex2rgb("#3a3f4e")
    puffs = []
    for _ in range(1400):
        if len(puffs) > 150:
            break
        edge = rnd.choice(("t", "b", "l", "r"))
        if edge in "tb":
            x = rnd.uniform(-60, w + 60)
            y = rnd.uniform(-60, top_y - 50) if edge == "t" else rnd.uniform(bot_y + 50, h + 60)
        else:
            y = rnd.uniform(-60, h + 60)
            x = rnd.uniform(-60, left_x - 60) if edge == "l" else rnd.uniform(right_x + 60, w + 60)
        r = rnd.uniform(50, 110)
        if lane_d(x, y) < r + LANE_HALF + 10:
            continue
        # keep puffs from spilling into the courtyard
        if left_x - r * 0.5 < x < right_x + r * 0.5 and top_y - r * 0.5 < y < bot_y + r * 0.5:
            continue
        puffs.append((x, y, r))
    for (x, y, r) in puffs:
        flat(ctx, lambda c, x=x, y=y, r=r: ellipse_path(c, x + 10, y + 16, r, r * 0.7), (0.03, 0.03, 0.05), 0.35)
    for (x, y, r) in puffs:
        paint(ctx, lambda c, x=x, y=y, r=r: ellipse_path(c, x, y, r, r * 0.7), mix(cloud_dark, cloud_mid, rnd.uniform(0, 0.7)), lw=0,
              shade_amt=0.3, hi=False, outline=False, alpha=0.93)
        stroke(ctx, lambda c, x=x, y=y, r=r: ellipse_path(c, x - r * 0.1, y - r * 0.1, r * 0.75, r * 0.5), hex2rgb("#5a6078"), 3, 0.25)
    # a few bolts inside the clouds
    bolts = 0
    for (x, y, r) in puffs:
        if bolts >= 6 or r < 80 or rnd.random() < 0.6:
            continue
        pts = [(x, y - r * 0.4)]
        for _k in range(5):
            pts.append((pts[-1][0] + rnd.uniform(-18, 18), pts[-1][1] + r * 0.16))
        if lane_d(*pts[-1]) < LANE_HALF + 20:
            continue
        bolts += 1
        glow(ctx, x, y, r * 0.9, bolt, 0.3)
        stroke(ctx, lambda c, pts=pts: poly_path_open(c, pts), bolt, 7, 0.5)
        stroke(ctx, lambda c, pts=pts: poly_path_open(c, pts), (1, 1, 1), 2.5, 0.95)
    # slanting rain
    for _ in range(420):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        L = rnd.uniform(14, 30)
        stroke(ctx, lambda c, x=x, y=y, L=L: (c.move_to(x, y), c.line_to(x - L * 0.35, y + L)), hex2rgb("#b8d0e8"), 1.6, rnd.uniform(0.15, 0.35))

    _portals(ctx, arena, hex2rgb("#5ab0ff"), hex2rgb("#d4ecff"))
    return cv


def poly_path_open(ctx, pts):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)


# ---------------------------------------------------------------------------------------------------
# Sunken Archive: drowned library floor


def _archive_background(arena, biome):
    w, h = int(WORLD_W * PPU), int(WORLD_H * PPU)
    cv = Canvas(w, h)
    ctx = cv.ctx
    rnd = random.Random(2718)
    teal = hex2rgb("#2aa6a4")
    foam = hex2rgb("#c8fff4")
    gold = hex2rgb("#ffd27a")
    _base(ctx, w, h, rnd, hex2rgb("#2c5c66"), hex2rgb("#0e2a34"), hex2rgb("#3c7078"),
          [hex2rgb("#244a56"), hex2rgb("#3e7480"), hex2rgb("#2a5260")], n=500, alpha=0.2)
    lanes = _lane_paths(arena)
    dense = [_dense(ctx, pts) for pts in lanes]
    cx, cy = to_px(0, 0)
    nodes = [to_px(*n) for n in arena["nodes"]]
    surges = [to_px(*p) for hz in biome.get("hazards", []) for p in hz.get("points", [])]
    # lanes that open later in the run are flooded (laneSchedule), falling back to the north/south ids
    flooded = {s["lane"] for s in arena.get("laneSchedule", biome.get("laneSchedule", []))}
    if not flooded:
        flooded = {i for i, lane in enumerate(arena["lanes"]) if lane["id"] in ("north", "south")}

    def lane_d(x, y):
        return min(_poly_dist(x, y, pts) for pts in lanes)

    # drowned marble floor: checker tiles with a mosaic border, seen through the water
    tile = 0.9 * PPU
    for j in range(int(h / tile) + 2):
        for i in range(int(w / tile) + 2):
            x, y = i * tile - 20, j * tile - 30
            col = hex2rgb("#3a6e76") if (i + j) % 2 else hex2rgb("#2e5e68")
            col = mix(col, rnd.choice([hex2rgb("#4a8088"), hex2rgb("#22505a")]), rnd.uniform(0, 0.35))
            flat(ctx, lambda c, x=x, y=y: rrect_path(c, x + 3, y + 3, tile - 6, tile - 6, 6), col, 0.55)
    # silt and algae drifts
    for _ in range(260):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.uniform(30, 90)
        flat(ctx, lambda c, x=x, y=y, r=r: ellipse_path(c, x, y, r, r * 0.6, rnd.uniform(0, 3)),
             rnd.choice([hex2rgb("#1e4450"), hex2rgb("#3a7a6a"), hex2rgb("#2a5a50")]), 0.18)
    # water body over the floor
    flat(ctx, lambda c: c.rectangle(0, 0, w, h), teal, 0.16)

    # flooded walkways first (submerged slabs under deep water), then the dry ones on top
    stone = hex2rgb("#b2a88c")
    for i, d in enumerate(dense):
        if i not in flooded:
            continue
        _paved_lane(ctx, d, hex2rgb("#1e4048"), mix(stone, teal, 0.45), hex2rgb("#1e4048"), 1.7 * PPU, 0.5 * PPU, alpha=0.75)
        stroke(ctx, lambda c, d=d: poly_path_open(c, d), hex2rgb("#0c3a5a"), 1.95 * PPU, 0.5)
        stroke(ctx, lambda c, d=d: poly_path_open(c, d), hex2rgb("#0a2c4a"), 1.2 * PPU, 0.25)
        for k, (x, y, ang) in enumerate(_resample(d, 0.55 * PPU)):
            nx, ny = -math.sin(ang), math.cos(ang)
            off = rnd.uniform(-0.45, 0.45) * PPU
            px, py = x + nx * off, y + ny * off
            stroke(ctx, lambda c, px=px, py=py, ang=ang: (c.save(), c.translate(px, py), c.rotate(ang), c.arc(0, 0, 16, math.pi * 1.15, math.pi * 1.85),
                                                          c.restore()), foam, 2.2, 0.45)
    for i, d in enumerate(dense):
        if i in flooded:
            continue
        stroke(ctx, lambda c, d=d: (c.move_to(d[0][0], d[0][1] + 12), [c.line_to(x, y + 12) for x, y in d[1:]]), hex2rgb("#0a2228"), 1.7 * PPU, 0.4)
        _paved_lane(ctx, d, hex2rgb("#4a4434"), stone, shade(stone, 0.4), 1.7 * PPU, 0.5 * PPU)
    _draw_lanes(ctx, [lanes[i] for i in range(len(lanes)) if i not in flooded], ((light(stone, 0.3), 0.6 * PPU, 0.22),))

    # central reading-room dais
    plaza_r = 2.9 * PPU
    _plaza(ctx, rnd, cx, cy, plaza_r, hex2rgb("#b8b096"), [hex2rgb("#d0c8ac"), hex2rgb("#8a8470")], hex2rgb("#5a5444"),
           hex2rgb("#5af0d8"), hex2rgb("#163a44"))

    # tidal surge markers at hazard points: swirl of foam rings with an eye
    for (x, y) in surges:
        glow(ctx, x, y, 1.2 * PPU, hex2rgb("#5ae8e0"), 0.3)
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 0.75 * PPU, 0.55 * PPU), hex2rgb("#0a3a50"), 0.45)
        for k, rr in enumerate((0.72, 0.52, 0.32)):
            for seg in range(3):
                a0 = seg * 2 * math.pi / 3 + k * 0.7
                stroke(ctx, lambda c, rr=rr, a0=a0: (c.save(), c.translate(x, y), c.scale(1, 0.72), c.arc(0, 0, rr * PPU, a0, a0 + 1.5), c.restore()),
                       foam, 5 - k, 0.8)
        for k in range(3):
            a0 = k * 2 * math.pi / 3
            sp = [(x + math.cos(a0 + t * 2.0) * (0.1 + 0.55 * t) * PPU, y + math.sin(a0 + t * 2.0) * (0.1 + 0.55 * t) * 0.72 * PPU)
                  for t in [q / 6.0 for q in range(7)]]
            stroke(ctx, lambda c, sp=sp: smooth_open(c, sp), hex2rgb("#7af4ec"), 3, 0.7)
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 0.12 * PPU, 0.09 * PPU), hex2rgb("#06222e"), 0.9)
        for k in range(8):
            a = rnd.uniform(0, 2 * math.pi)
            rr = rnd.uniform(0.6, 0.85) * PPU
            flat(ctx, lambda c, a=a, rr=rr: ellipse_path(c, x + math.cos(a) * rr, y + math.sin(a) * rr * 0.72, 4, 4), (1, 1, 1), 0.7)

    # glowing tome lecterns at trait nodes (lectern on the side farthest from the lanes)
    wood = hex2rgb("#6a4a32")
    for t in biome.get("nodeTraits", []):
        x, y = nodes[t["node"]]
        glow(ctx, x, y, 1.25 * PPU, gold, 0.5)
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 0.82 * PPU, 0.6 * PPU), hex2rgb("#3a5a50"), 0.35)
        stroke(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 0.82 * PPU, 0.6 * PPU), gold, 3.5, 0.75)
        for k in range(12):
            a = k * math.pi / 6
            flat(ctx, lambda c, a=a, x=x, y=y: star_path(c, x + math.cos(a) * 0.82 * PPU, y + math.sin(a) * 0.6 * PPU, 7, 2.6, 4), light(gold, 0.4), 0.85)
        lx, ly = _best_spot(x, y, 1.12 * PPU, lane_d)
        glow(ctx, lx, ly - 30, 70, gold, 0.35)
        flat(ctx, lambda c, lx=lx, ly=ly: ellipse_path(c, lx + 4, ly + 8, 28, 9), (0.02, 0.08, 0.1), 0.45)
        paint(ctx, lambda c, lx=lx, ly=ly: poly_path(c, [(lx - 7, ly), (lx - 5, ly - 34), (lx + 5, ly - 34), (lx + 7, ly)]), wood, lw=3.5,
              shade_amt=0.3, hi=False)
        paint(ctx, lambda c, lx=lx, ly=ly: poly_path(c, [(lx - 26, ly - 30), (lx + 26, ly - 30), (lx + 20, ly - 46), (lx - 20, ly - 46)]), wood, lw=3.5,
              shade_amt=0.25, hi=False)
        glow(ctx, lx, ly - 46, 44, gold, 0.7)
        for sgn in (-1, 1):
            paint(ctx, lambda c, lx=lx, ly=ly, sgn=sgn: poly_path(c, [(lx, ly - 36), (lx + sgn * 22, ly - 40), (lx + sgn * 18, ly - 54), (lx, ly - 50)]),
                  hex2rgb("#fff4d8"), lw=2.5, shade_amt=0.12, hi=False)
            for q in range(3):
                stroke(ctx, lambda c, lx=lx, ly=ly, sgn=sgn, q=q: (c.move_to(lx + sgn * 4, ly - 41 - q * 4), c.line_to(lx + sgn * 16, ly - 44 - q * 4)),
                       hex2rgb("#8a6a3a"), 1.5, 0.7)
        sparkle(ctx, lx - 10, ly - 62, 8, light(gold, 0.6), 0.95)
        sparkle(ctx, lx + 14, ly - 70, 6, (1, 1, 1), 0.9)

    # sunken bookshelves and columns around the edges (never over lanes, nodes or surge points)
    def free(x, y, d):
        if math.hypot(x - cx, (y - cy) / 0.8) < plaza_r + 40:
            return False
        if lane_d(x, y) < LANE_HALF + d:
            return False
        if any(math.hypot(x - nx, y - ny) < 1.0 * PPU + d for nx, ny in nodes):
            return False
        if any(math.hypot(x - sx_, y - sy_) < 0.95 * PPU + d for sx_, sy_ in surges):
            return False
        return True

    def edge_zone(x, y):
        wx, wy = x / PPU - WORLD_W / 2, WORLD_H / 2 - y / PPU
        return abs(wx) > 9.6 or abs(wy) > 5.2

    spine_cols = [hex2rgb(c) for c in ("#8a2a2a", "#2a4a8a", "#2a6a3a", "#8a6a2a", "#5a2a6a", "#3a3a3a")]
    placed = []
    for _ in range(3000):
        if len(placed) >= 40:
            break
        x, y = rnd.uniform(-20, w + 20), rnd.uniform(-20, h + 20)
        if not edge_zone(x, y):
            continue
        wx, wy = x / PPU - WORLD_W / 2, WORLD_H / 2 - y / PPU
        horiz = abs(wy) / 8.5 > abs(wx) / 15.0
        kind = "column" if rnd.random() < 0.35 else "shelf"
        if kind == "shelf":
            L, D = rnd.uniform(1.8, 2.8) * PPU, 0.72 * PPU
            sw, sh = (L, D) if horiz else (D, L)
            rad = math.hypot(sw, sh) / 2
        else:
            rad = 0.5 * PPU
            sw = sh = rad * 2
        if not free(x, y, rad + 12):
            continue
        if any(math.hypot(x - px, y - py) < rad + pr + 16 for px, py, pr in placed):
            continue
        placed.append((x, y, rad))
        if kind == "shelf":
            x0, y0 = x - sw / 2, y - sh / 2
            flat(ctx, lambda c: rrect_path(c, x0 + 8, y0 + 12, sw, sh, 6), (0.02, 0.08, 0.1), 0.4)
            paint(ctx, lambda c: rrect_path(c, x0, y0, sw, sh, 6), wood, lw=5, shade_amt=0.25, hi=False)
            inner = 8
            n_sh = 2
            for s in range(n_sh):
                if horiz:
                    by0, bh = y0 + inner + s * (sh - 2 * inner) / n_sh, (sh - 2 * inner) / n_sh - 3
                    xx = x0 + inner
                    while xx < x0 + sw - inner - 6:
                        bw = rnd.uniform(6, 12)
                        bw = min(bw, x0 + sw - inner - xx)
                        flat(ctx, lambda c, xx=xx, by0=by0, bw=bw, bh=bh: rrect_path(c, xx, by0 + rnd.uniform(0, 3), bw - 1.5, bh, 2),
                             rnd.choice(spine_cols), 0.95)
                        xx += bw
                else:
                    bx0, bw = x0 + inner + s * (sw - 2 * inner) / n_sh, (sw - 2 * inner) / n_sh - 3
                    yy = y0 + inner
                    while yy < y0 + sh - inner - 6:
                        bh = rnd.uniform(6, 12)
                        bh = min(bh, y0 + sh - inner - yy)
                        flat(ctx, lambda c, yy=yy, bx0=bx0, bw=bw, bh=bh: rrect_path(c, bx0 + rnd.uniform(0, 3), yy, bw, bh - 1.5, 2),
                             rnd.choice(spine_cols), 0.95)
                        yy += bh
            stroke(ctx, lambda c: rrect_path(c, x0 + inner - 3, y0 + inner - 3, sw - 2 * inner + 6, sh - 2 * inner + 6, 3), shade(wood, 0.4), 3, 0.8)
        else:
            flat(ctx, lambda c: ellipse_path(c, x + 8, y + 12, rad, rad * 0.8), (0.02, 0.08, 0.1), 0.4)
            paint(ctx, lambda c: ellipse_path(c, x, y, rad, rad * 0.86), hex2rgb("#c8c0a4"), lw=5, shade_amt=0.25, hi_size=0.5)
            for k in range(10):
                a = k * math.pi / 5
                stroke(ctx, lambda c, a=a: (c.move_to(x + math.cos(a) * rad * 0.5, y + math.sin(a) * rad * 0.43),
                                            c.line_to(x + math.cos(a) * rad * 0.92, y + math.sin(a) * rad * 0.79)), hex2rgb("#8a846c"), 2.5, 0.7)
            paint(ctx, lambda c: ellipse_path(c, x, y, rad * 0.45, rad * 0.38), hex2rgb("#d8d2b8"), lw=3, hi=False, shade_amt=0.2)
        # water lapping over the sunken prop
        flat(ctx, lambda c: ellipse_path(c, x, y + sh * 0.18, sw * 0.6, sh * 0.36), teal, 0.22)

    # caustic light ripples on the water (off lanes)
    for _ in range(360):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        if lane_d(x, y) < LANE_HALF + 10:
            continue
        L = rnd.uniform(20, 46)
        a = rnd.uniform(-0.4, 0.4)
        pts = [(x + math.cos(a) * L * t, y + math.sin(a) * L * t + math.sin(t * 6) * 4) for t in (0, 0.33, 0.66, 1)]
        stroke(ctx, lambda c, pts=pts: smooth_open(c, pts), hex2rgb("#a8fff0"), 2, rnd.uniform(0.12, 0.3))
    # floating pages (off lanes, nodes, plaza, surge points)
    for _ in range(180):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        if not free(x, y, 20):
            continue
        if rnd.random() < 0.5:
            continue
        a = rnd.uniform(-0.8, 0.8)
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(a)
        flat(ctx, lambda c: rrect_path(c, -12 + 3, -15 + 5, 24, 30, 2), (0.02, 0.1, 0.12), 0.3)
        paint(ctx, lambda c: rrect_path(c, -12, -15, 24, 30, 2), hex2rgb("#f0e6c8"), lw=2, shade_amt=0.12, hi=False, alpha=0.92)
        for q in range(5):
            stroke(ctx, lambda c, q=q: (c.move_to(-7, -9 + q * 5), c.line_to(rnd.uniform(2, 8), -9 + q * 5)), hex2rgb("#6a5a44"), 1.3, 0.6)
        ctx.restore()
    # bubbles
    for _ in range(120):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        if lane_d(x, y) < LANE_HALF:
            continue
        r = rnd.uniform(2.5, 6)
        stroke(ctx, lambda c, x=x, y=y, r=r: ellipse_path(c, x, y, r, r), foam, 1.4, 0.55)

    _portals(ctx, arena, hex2rgb("#2ad0c0"), hex2rgb("#b4fff2"))
    return cv


def crystal(state="intact"):
    """Central crystal on its pedestal. States: intact, cracked, critical."""
    cv = Canvas(320, 400)
    ctx = cv.ctx
    cx = 160
    core = hex2rgb("#7fe8ff") if state != "critical" else hex2rgb("#ff8ab0")
    deep = hex2rgb("#5a6aff") if state != "critical" else hex2rgb("#c03a6a")
    glow(ctx, cx, 170, 170, core, 0.45 if state == "intact" else 0.35)
    flat(ctx, lambda c: ellipse_path(c, cx, 372, 118, 22), (0, 0, 0), 0.3)
    paint(ctx, lambda c: smooth_closed(c, [(60, 330), (80, 300), (240, 300), (260, 330), (230, 368), (90, 368)], 0.3), hex2rgb("#a0a6c0"), lw=7)
    paint(ctx, lambda c: smooth_closed(c, [(86, 304), (100, 278), (220, 278), (234, 304), (200, 318), (120, 318)], 0.3), hex2rgb("#c4c8da"), lw=6)
    for k in range(5):
        x = 96 + k * 32
        glow(ctx, x, 344, 12, core, 0.8)
        flat(ctx, lambda c, x=x: ellipse_path(c, x, 344, 5, 5), light(core, 0.5))
    # main crystal: faceted, slightly floating
    outline = [(cx, 20), (cx + 58, 98), (cx + 70, 200), (cx + 30, 278), (cx - 30, 278), (cx - 70, 200), (cx - 58, 98)]
    paint(ctx, lambda c: poly_path(c, outline), deep, lw=8, shade_amt=0.0, hi=False)
    facets = [
        ([(cx, 20), (cx + 58, 98), (cx + 10, 118)], light(core, 0.45)),
        ([(cx, 20), (cx + 10, 118), (cx - 58, 98)], light(core, 0.15)),
        ([(cx - 58, 98), (cx + 10, 118), (cx - 70, 200)], core),
        ([(cx + 58, 98), (cx + 70, 200), (cx + 10, 118)], mix(core, deep, 0.45)),
        ([(cx + 10, 118), (cx + 70, 200), (cx + 30, 278), (cx - 4, 222)], mix(core, deep, 0.6)),
        ([(cx + 10, 118), (cx - 4, 222), (cx - 70, 200)], mix(core, deep, 0.25)),
        ([(cx - 70, 200), (cx - 4, 222), (cx - 30, 278)], mix(core, deep, 0.4)),
        ([(cx - 4, 222), (cx + 30, 278), (cx - 30, 278)], deep),
    ]
    for pts, col in facets:
        flat(ctx, lambda c, pts=pts: poly_path(c, pts), col)
        stroke(ctx, lambda c, pts=pts: poly_path(c, pts), light(core, 0.6), 2, 0.6)
    stroke(ctx, lambda c: poly_path(c, outline), INK, 8)
    # side shards
    for side in (-1, 1):
        sh = [(cx + side * 84, 180), (cx + side * 108, 214), (cx + side * 92, 270), (cx + side * 70, 236)]
        paint(ctx, lambda c, sh=sh: poly_path(c, sh), core, lw=5, hi_size=0.7)
    sparkle(ctx, cx - 18, 70, 16)
    sparkle(ctx, cx + 30, 150, 9)
    if state in ("cracked", "critical"):
        cracks = [[(cx - 20, 120), (cx - 6, 150), (cx - 24, 176), (cx - 10, 214)], [(cx + 30, 160), (cx + 18, 190), (cx + 36, 222)]]
        if state == "critical":
            cracks += [[(cx - 50, 160), (cx - 30, 196), (cx - 46, 236)], [(cx + 10, 60), (cx, 96), (cx + 16, 124)], [(cx + 46, 110), (cx + 30, 140)]]
        for cr in cracks:
            stroke(ctx, lambda c, cr=cr: (c.move_to(*cr[0]), [c.line_to(*p) for p in cr[1:]]), INK, 6)
            stroke(ctx, lambda c, cr=cr: (c.move_to(*cr[0]), [c.line_to(*p) for p in cr[1:]]), (1, 1, 1), 2, 0.8)
    return cv


def node_pad(state="empty"):
    """Defence node marker. empty / occupied / highlight (valid drop target)."""
    cv = Canvas(192, 128)
    ctx = cv.ctx
    col = {"empty": hex2rgb("#7fe8ff"), "occupied": hex2rgb("#ffd35a"), "highlight": hex2rgb("#7cff9a")}[state]
    glow(ctx, 96, 64, 80, col, 0.35 if state != "empty" else 0.18)
    paint(ctx, lambda c: ellipse_path(c, 96, 64, 76, 46), hex2rgb("#bfc6dc"), lw=6, shade_amt=0.25, alpha=0.95)
    stroke(ctx, lambda c: ellipse_path(c, 96, 64, 58, 34), col, 6, 0.95)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        paint(ctx, lambda c, a=a: star_path(c, 96 + math.cos(a) * 64, 64 + math.sin(a) * 39, 9, 3.5, 4), col, lw=2.5, hi=False)
    return cv


def lane_arrow():
    """Chevron used to telegraph upcoming enemy lanes during preparation."""
    cv = Canvas(128, 128)
    ctx = cv.ctx
    col = hex2rgb("#ff5a6a")
    glow(ctx, 64, 64, 60, col, 0.4)
    paint(ctx, lambda c: poly_path(c, [(20, 30), (64, 64), (20, 98), (40, 98), (90, 64), (40, 30)]), col, lw=6, hi_size=0.6)
    return cv


def shadow():
    """Soft elliptical contact shadow shared by all units (scaled per unit in Unity)."""
    cv = Canvas(128, 48)
    ctx = cv.ctx
    ctx.scale(1, 0.375)
    grad = cairo.RadialGradient(64, 64, 2, 64, 64, 64)
    grad.add_color_stop_rgba(0, 0.05, 0.03, 0.12, 0.55)
    grad.add_color_stop_rgba(0.7, 0.05, 0.03, 0.12, 0.3)
    grad.add_color_stop_rgba(1, 0.05, 0.03, 0.12, 0)
    ctx.arc(64, 64, 64, 0, 2 * math.pi)
    ctx.set_source(grad)
    ctx.fill()
    return cv
