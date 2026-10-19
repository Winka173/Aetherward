"""Combat VFX sprites. Each element has its own projectile and impact silhouette (not just a tint) so
effects stay readable with reduced VFX or colour-vision deficits. White/greyscale textures (ring,
glow, telegraph) are tinted at runtime."""
import math
import random
import zlib
import cairo
from toolkit import (INK, Canvas, hex2rgb, mix, shade, light, paint, flat, stroke, glow, sparkle, smooth_closed, smooth_open,
                     ellipse_path, rrect_path, poly_path, star_path, outlined_line)
from glyphs import FIRE, FIRE2, WATER, WATER2, BOLT, BOLT2, ICE, ICE2, WIND, WIND2, EARTH, EARTH2, PURPLE

EL = {"fire": (FIRE, FIRE2), "water": (WATER, WATER2), "lightning": (BOLT, BOLT2), "ice": (ICE, ICE2), "wind": (WIND, WIND2), "earth": (EARTH, EARTH2)}


def projectile(el, s=128):
    """Points to +x (right). Rotated by velocity at runtime."""
    cv = Canvas(s, s)
    ctx = cv.ctx
    a, b = EL[el]
    c = s / 2
    glow(ctx, c, c, s * 0.42, b, 0.55)
    if el == "fire":
        paint(ctx, lambda x: smooth_closed(x, [(c + 34, c), (c + 6, c - 20), (c - 30, c - 12), (c - 44, c), (c - 30, c + 12), (c + 6, c + 20)], 0.5), a, lw=4.5)
        flat(ctx, lambda x: smooth_closed(x, [(c + 26, c), (c + 4, c - 10), (c - 16, c), (c + 4, c + 10)], 0.5), b)
    elif el == "water":
        paint(ctx, lambda x: ellipse_path(x, c + 6, c, 24, 22), a, lw=4.5, hi_size=0.7)
        for k in range(3):
            flat(ctx, lambda x, k=k: ellipse_path(x, c - 26 - k * 12, c + (k % 2) * 8 - 4, 6 - k, 6 - k), b, 0.9)
        flat(ctx, lambda x: ellipse_path(x, c, c - 8, 7, 5, -0.4), (1, 1, 1), 0.9)
    elif el == "lightning":
        stroke(ctx, lambda x: (x.move_to(c - 44, c + 4), x.line_to(c - 20, c - 10), x.line_to(c - 8, c + 8), x.line_to(c + 14, c - 8), x.line_to(c + 36, c)), INK, 12)
        stroke(ctx, lambda x: (x.move_to(c - 44, c + 4), x.line_to(c - 20, c - 10), x.line_to(c - 8, c + 8), x.line_to(c + 14, c - 8), x.line_to(c + 36, c)), b, 6)
        paint(ctx, lambda x: star_path(x, c + 34, c, 14, 6, 4, 0), b, lw=3.5, hi=False)
    elif el == "ice":
        paint(ctx, lambda x: poly_path(x, [(c + 40, c), (c + 4, c - 14), (c - 38, c - 6), (c - 30, c), (c - 38, c + 6), (c + 4, c + 14)]), a, lw=4.5, hi_size=0.8)
        stroke(ctx, lambda x: (x.move_to(c - 30, c), x.line_to(c + 34, c)), b, 3)
    elif el == "wind":
        for k in range(2):
            def cres(x, k=k):
                x.arc(c - 8 - k * 18, c, 28 - k * 6, -1.2, 1.2)
            stroke(ctx, cres, INK, 12 - k * 2)
            stroke(ctx, cres, b if k == 0 else a, 6 - k)
    elif el == "earth":
        paint(ctx, lambda x: poly_path(x, [(c + 26, c - 4), (c + 10, c - 22), (c - 14, c - 20), (c - 24, c + 2), (c - 8, c + 22), (c + 18, c + 16)]), a, lw=4.5)
        for k in range(3):
            flat(ctx, lambda x, k=k: ellipse_path(x, c - 34 - k * 10, c + (k - 1) * 8, 4, 4), shade(a, 0.3), 0.8)
    return cv


def arrow(s=192):
    cv = Canvas(s, s // 2)
    ctx = cv.ctx
    c = s / 4
    glow(ctx, s * 0.62, c, s * 0.34, WIND2, 0.5)
    outlined_line(ctx, [(s * 0.12, c), (s * 0.8, c)], hex2rgb("#e8e0d0"), 5, 11, smooth=False)
    paint(ctx, lambda x: poly_path(x, [(s * 0.92, c), (s * 0.76, c - 12), (s * 0.79, c), (s * 0.76, c + 12)]), (0.9, 0.95, 1.0), lw=4)
    for d in (-1, 1):
        paint(ctx, lambda x, d=d: poly_path(x, [(s * 0.12, c), (s * 0.04, c + d * 14), (s * 0.24, c + d * 4)]), WIND, lw=3, hi=False)
    return cv


def fireball(s=192):
    cv = Canvas(s, s)
    ctx = cv.ctx
    c = s / 2
    glow(ctx, c, c, s * 0.48, FIRE2, 0.7)
    paint(ctx, lambda x: smooth_closed(x, [(c + 40, c), (c + 20, c - 34), (c - 20, c - 38), (c - 64, c - 18), (c - 50, c), (c - 70, c + 16),
                                             (c - 20, c + 38), (c + 20, c + 34)], 0.5), FIRE, lw=6)
    paint(ctx, lambda x: ellipse_path(x, c + 10, c, 26, 24), FIRE2, lw=0, outline=False, hi=False)
    flat(ctx, lambda x: ellipse_path(x, c + 14, c - 4, 12, 10), (1, 0.97, 0.8))
    return cv


def impact(el, s=192):
    """Distinct burst silhouette per element (spiky flame, splash ring, forked star, shards, gust arcs, rubble)."""
    cv = Canvas(s, s)
    ctx = cv.ctx
    a, b = EL[el]
    c = s / 2
    rnd = random.Random(zlib.crc32(el.encode()) & 0xffff)  # stable across runs (str hash is salted)
    glow(ctx, c, c, s * 0.45, b, 0.6)
    if el == "fire":
        paint(ctx, lambda x: star_path(x, c, c, 78, 34, 9), a, lw=5)
        paint(ctx, lambda x: star_path(x, c, c, 44, 22, 9, 0.3), b, lw=0, outline=False, hi=False)
    elif el == "water":
        stroke(ctx, lambda x: ellipse_path(x, c, c, 62, 62), INK, 14)
        stroke(ctx, lambda x: ellipse_path(x, c, c, 62, 62), b, 8)
        for k in range(8):
            ang = k * math.pi / 4
            paint(ctx, lambda x, ang=ang: ellipse_path(x, c + math.cos(ang) * 72, c + math.sin(ang) * 72, 10, 10), a, lw=3.5, hi=False)
    elif el == "lightning":
        for k in range(6):
            ang = k * math.pi / 3 + 0.2
            pts = [(c, c)]
            r = 0
            for j in range(4):
                r += 20
                jit = rnd.uniform(-0.4, 0.4)
                pts.append((c + math.cos(ang + jit) * r, c + math.sin(ang + jit) * r))
            stroke(ctx, lambda x, pts=pts: (x.move_to(*pts[0]), [x.line_to(*p) for p in pts[1:]]), INK, 10)
            stroke(ctx, lambda x, pts=pts: (x.move_to(*pts[0]), [x.line_to(*p) for p in pts[1:]]), b, 5)
        paint(ctx, lambda x: star_path(x, c, c, 30, 12, 4, 0), (1, 1, 1), lw=4, hi=False)
    elif el == "ice":
        for k in range(7):
            ang = k * 2 * math.pi / 7
            tip = (c + math.cos(ang) * 80, c + math.sin(ang) * 80)
            nx, ny = -math.sin(ang) * 12, math.cos(ang) * 12
            paint(ctx, lambda x, ang=ang, tip=tip, nx=nx, ny=ny: poly_path(x, [(c + nx, c + ny), tip, (c - nx, c - ny)]), a, lw=4, hi_size=0.7)
        paint(ctx, lambda x: ellipse_path(x, c, c, 22, 22), b, lw=4, hi=False)
    elif el == "wind":
        for k in range(4):
            a0 = k * math.pi / 2
            def arc(x, a0=a0):
                x.arc(c, c, 60, a0, a0 + 1.1)
            stroke(ctx, arc, INK, 14)
            stroke(ctx, arc, b, 8)
            def arc2(x, a0=a0):
                x.arc(c, c, 36, a0 + 0.8, a0 + 1.8)
            stroke(ctx, arc2, INK, 10)
            stroke(ctx, arc2, a, 5)
    elif el == "earth":
        for k in range(7):
            ang = k * 2 * math.pi / 7 + 0.3
            d = rnd.uniform(46, 72)
            x0, y0 = c + math.cos(ang) * d, c + math.sin(ang) * d
            r = rnd.uniform(10, 16)
            paint(ctx, lambda x, x0=x0, y0=y0, r=r: poly_path(x, [(x0 - r, y0), (x0 - r * 0.3, y0 - r), (x0 + r, y0 - r * 0.4), (x0 + r * 0.6, y0 + r)]), a, lw=4)
        paint(ctx, lambda x: ellipse_path(x, c, c, 36, 24), shade(a, 0.3), lw=4, hi=False, alpha=0.8)
    return cv


ZONE_COL = {
    "magma": (hex2rgb("#ff5a2c"), hex2rgb("#ffb230")), "mud": (hex2rgb("#8a6a3a"), hex2rgb("#b49067")),
    "thunderstorm": (hex2rgb("#6a5aa0"), hex2rgb("#ffe14a")), "blizzard": (hex2rgb("#8fd6ff"), hex2rgb("#ffffff")),
    "healing_rain": (hex2rgb("#2f8cff"), hex2rgb("#7cff9a")), "vortex": (hex2rgb("#2fd39a"), hex2rgb("#c4ffd9")),
    "burning_ground": (hex2rgb("#ff7a2a"), hex2rgb("#ffd35a")), "storm_trail": (hex2rgb("#8c4dff"), hex2rgb("#ffe14a")),
    "tempest_link": (hex2rgb("#5a8aff"), hex2rgb("#ffe14a")),
}


def zone(kind, s=256):
    """Top-down ground effect, drawn to fill a unit circle (scaled to the zone radius at runtime)."""
    cv = Canvas(s, s)
    ctx = cv.ctx
    a, b = ZONE_COL[kind]
    c = s / 2
    r = s / 2 - 8
    rnd = random.Random(len(kind) * 31)
    grad = cairo.RadialGradient(c, c, 4, c, c, r)
    strong = 1.4 if kind == "mud" else 1.0
    grad.add_color_stop_rgba(0, *a, 0.55 * strong)
    grad.add_color_stop_rgba(0.75, *a, 0.38 * strong)
    grad.add_color_stop_rgba(1, *a, 0.0)
    ctx.arc(c, c, r, 0, 2 * math.pi)
    ctx.set_source(grad)
    ctx.fill()
    stroke(ctx, lambda x: ellipse_path(x, c, c, r - 6, r - 6), b, 5, 0.75)
    if kind in ("magma", "burning_ground"):
        for _ in range(9):
            x0, y0 = c + rnd.uniform(-r * 0.6, r * 0.6), c + rnd.uniform(-r * 0.6, r * 0.6)
            rr = rnd.uniform(10, 24)
            paint(ctx, lambda x, x0=x0, y0=y0, rr=rr: ellipse_path(x, x0, y0, rr, rr * 0.7), b, lw=3, hi=False, alpha=0.85)
    elif kind == "mud":
        for _ in range(10):
            x0, y0 = c + rnd.uniform(-r * 0.6, r * 0.6), c + rnd.uniform(-r * 0.6, r * 0.6)
            stroke(ctx, lambda x, x0=x0, y0=y0: ellipse_path(x, x0, y0, rnd.uniform(8, 18), rnd.uniform(5, 10)), shade(a, 0.4), 3, 0.8)
    elif kind in ("thunderstorm", "storm_trail", "tempest_link"):
        for _ in range(5):
            x0, y0 = c + rnd.uniform(-r * 0.5, r * 0.5), c + rnd.uniform(-r * 0.5, r * 0.5)
            stroke(ctx, lambda x, x0=x0, y0=y0: (x.move_to(x0, y0 - 18), x.line_to(x0 - 8, y0), x.line_to(x0 + 6, y0 + 2), x.line_to(x0 - 4, y0 + 20)), b, 4, 0.9)
    elif kind == "blizzard":
        for _ in range(16):
            x0, y0 = c + rnd.uniform(-r * 0.7, r * 0.7), c + rnd.uniform(-r * 0.7, r * 0.7)
            sparkle(ctx, x0, y0, rnd.uniform(5, 10), b, 0.9)
    elif kind == "healing_rain":
        for _ in range(16):
            x0, y0 = c + rnd.uniform(-r * 0.7, r * 0.7), c + rnd.uniform(-r * 0.7, r * 0.7)
            stroke(ctx, lambda x, x0=x0, y0=y0: (x.move_to(x0, y0), x.line_to(x0 - 4, y0 + 14)), WATER2, 3, 0.9)
        for k in range(4):
            ang = k * math.pi / 2 + 0.6
            x0, y0 = c + math.cos(ang) * r * 0.45, c + math.sin(ang) * r * 0.45
            paint(ctx, lambda x, x0=x0, y0=y0: poly_path(x, [(x0 - 3, y0 - 9), (x0 + 3, y0 - 9), (x0 + 3, y0 - 3), (x0 + 9, y0 - 3), (x0 + 9, y0 + 3), (x0 + 3, y0 + 3),
                                                           (x0 + 3, y0 + 9), (x0 - 3, y0 + 9), (x0 - 3, y0 + 3), (x0 - 9, y0 + 3), (x0 - 9, y0 - 3), (x0 - 3, y0 - 3)]),
                  b, lw=2.5, hi=False)
    elif kind == "vortex":
        for k in range(3):
            a0 = k * 2 * math.pi / 3
            pts = [(c + math.cos(a0 + t * 0.5) * (r * 0.85 - t * 9), c + math.sin(a0 + t * 0.5) * (r * 0.85 - t * 9)) for t in range(10)]
            stroke(ctx, lambda x, pts=pts: smooth_open(x, pts), b, 6, 0.85)
    return cv


def ring(s=256):
    cv = Canvas(s, s)
    stroke(cv.ctx, lambda x: ellipse_path(x, s / 2, s / 2, s / 2 - 10, s / 2 - 10), (1, 1, 1), 10)
    return cv


def soft_glow(s=128):
    cv = Canvas(s, s)
    glow(cv.ctx, s / 2, s / 2, s / 2, (1, 1, 1), 1.0)
    return cv


def telegraph(s=256):
    """Danger telegraph: dashed ring + translucent fill (tinted red at runtime)."""
    cv = Canvas(s, s)
    ctx = cv.ctx
    c, r = s / 2, s / 2 - 8
    flat(ctx, lambda x: ellipse_path(x, c, c, r, r), (1, 1, 1), 0.22)
    ctx.set_dash([18, 12])
    stroke(ctx, lambda x: ellipse_path(x, c, c, r - 4, r - 4), (1, 1, 1), 8)
    ctx.set_dash([])
    stroke(ctx, lambda x: ellipse_path(x, c, c, r * 0.35, r * 0.35), (1, 1, 1), 4, 0.6)
    return cv


def slash(s=256):
    """Melee swing arc (tinted per element)."""
    cv = Canvas(s, s)
    ctx = cv.ctx
    c = s / 2
    for w, al in ((26, 0.35), (14, 0.8), (6, 1.0)):
        stroke(ctx, lambda x: x.arc(c, c, s * 0.38, -1.3, 1.3), (1, 1, 1), w, al)
    return cv


def spark_particle(s=48):
    cv = Canvas(s, s)
    glow(cv.ctx, s / 2, s / 2, s / 2, (1, 1, 1), 0.8)
    sparkle(cv.ctx, s / 2, s / 2, s * 0.34, (1, 1, 1))
    return cv


def coin_particle(s=48):
    cv = Canvas(s, s)
    from glyphs import g_coin
    g_coin(cv.ctx, s / 2, s / 2, s * 0.9)
    return cv
