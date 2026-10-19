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


def background():
    arena = load_arena()
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
