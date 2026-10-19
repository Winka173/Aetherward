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

    theme "verdant" is the original Arcane Sanctuary (default arena.json); "molten" and "frost" are the
    biome arenas from biomes.json (biome supplies hazards / nodeTraits for markers).
    """
    if arena is None:
        arena = load_arena()
    if theme == "molten":
        return _molten_background(arena, biome or {})
    if theme == "frost":
        return _frost_background(arena, biome or {})
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
