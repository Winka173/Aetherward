"""Glyph library: small inked symbols composed into element, status, reaction, role, relic and card
icons. Each glyph draws centred at (cx, cy) inside a box of the given size."""
import math
from toolkit import (INK, hex2rgb, mix, shade, light, paint, flat, stroke, glow, sparkle, smooth_closed,
                     smooth_open, ellipse_path, rrect_path, poly_path, star_path, outlined_line)

FIRE, FIRE2 = hex2rgb("#ff5a2c"), hex2rgb("#ffb230")
WATER, WATER2 = hex2rgb("#2f8cff"), hex2rgb("#5fe0ff")
BOLT, BOLT2 = hex2rgb("#8c4dff"), hex2rgb("#ffe14a")
ICE, ICE2 = hex2rgb("#7fd8ff"), hex2rgb("#e8fbff")
WIND, WIND2 = hex2rgb("#2fd39a"), hex2rgb("#c4ffd9")
EARTH, EARTH2 = hex2rgb("#b9773a"), hex2rgb("#8fc24a")
GOLD = hex2rgb("#ffd35a")
STEEL = hex2rgb("#c8d0e0")
WOOD = hex2rgb("#a0703f")
RED = hex2rgb("#e0405a")
PURPLE = hex2rgb("#b07aff")

LW = 5.0


def g_flame(ctx, cx, cy, s, col=FIRE, col2=FIRE2):
    paint(ctx, lambda c: smooth_closed(c, [(cx, cy - s * 0.5), (cx + s * 0.18, cy - s * 0.18), (cx + s * 0.34, cy - s * 0.32),
                                             (cx + s * 0.36, cy + s * 0.12), (cx, cy + s * 0.45), (cx - s * 0.36, cy + s * 0.12),
                                             (cx - s * 0.26, cy - s * 0.2), (cx - s * 0.1, cy - s * 0.06)], 0.5), col, lw=LW)
    paint(ctx, lambda c: smooth_closed(c, [(cx, cy - s * 0.12), (cx + s * 0.16, cy + s * 0.12), (cx, cy + s * 0.32), (cx - s * 0.16, cy + s * 0.12)], 0.6),
          col2, lw=0, outline=False, hi=False)


def g_drop(ctx, cx, cy, s, col=WATER, col2=WATER2):
    paint(ctx, lambda c: smooth_closed(c, [(cx, cy - s * 0.48), (cx + s * 0.3, cy + s * 0.05), (cx + s * 0.22, cy + s * 0.36),
                                             (cx, cy + s * 0.44), (cx - s * 0.22, cy + s * 0.36), (cx - s * 0.3, cy + s * 0.05)], 0.55), col, lw=LW)
    flat(ctx, lambda c: ellipse_path(c, cx - s * 0.1, cy + s * 0.08, s * 0.06, s * 0.12, -0.3), col2, 0.9)


def g_bolt(ctx, cx, cy, s, col=BOLT2, col2=None):
    paint(ctx, lambda c: poly_path(c, [(cx + s * 0.12, cy - s * 0.48), (cx - s * 0.26, cy + s * 0.06), (cx - s * 0.02, cy + s * 0.06),
                                         (cx - s * 0.14, cy + s * 0.48), (cx + s * 0.28, cy - s * 0.08), (cx + s * 0.04, cy - s * 0.08)]), col, lw=LW)


def g_snowflake(ctx, cx, cy, s, col=ICE, col2=ICE2):
    for k in range(3):
        a = k * math.pi / 3
        dx, dy = math.cos(a) * s * 0.44, math.sin(a) * s * 0.44
        outlined_line(ctx, [(cx - dx, cy - dy), (cx + dx, cy + dy)], col2, s * 0.08, s * 0.08 + 7, smooth=False)
    for k in range(6):
        a = k * math.pi / 3
        ex, ey = cx + math.cos(a) * s * 0.3, cy + math.sin(a) * s * 0.3
        for d in (-0.6, 0.6):
            stroke(ctx, lambda c, ex=ex, ey=ey, a=a, d=d: (c.move_to(ex, ey), c.line_to(ex + math.cos(a + d) * s * 0.12, ey + math.sin(a + d) * s * 0.12)), INK, 6)
            stroke(ctx, lambda c, ex=ex, ey=ey, a=a, d=d: (c.move_to(ex, ey), c.line_to(ex + math.cos(a + d) * s * 0.12, ey + math.sin(a + d) * s * 0.12)), col2, 2.5)
    paint(ctx, lambda c: ellipse_path(c, cx, cy, s * 0.1, s * 0.1), col, lw=3.5, hi=False)


def g_swirl(ctx, cx, cy, s, col=WIND, col2=WIND2):
    for i, (r, a0) in enumerate(((0.42, 0.0), (0.3, 2.1), (0.18, 4.2))):
        def arc(c, r=r, a0=a0):
            c.arc(cx, cy, s * r, a0, a0 + 4.2)
        stroke(ctx, arc, INK, s * 0.12 + 6)
        stroke(ctx, arc, col if i % 2 == 0 else col2, s * 0.12)


def g_leaf(ctx, cx, cy, s, col=EARTH2, col2=EARTH):
    paint(ctx, lambda c: smooth_closed(c, [(cx - s * 0.36, cy + s * 0.36), (cx - s * 0.3, cy - s * 0.1), (cx + s * 0.06, cy - s * 0.4),
                                             (cx + s * 0.4, cy - s * 0.42), (cx + s * 0.32, cy - s * 0.04), (cx, cy + s * 0.3)], 0.5), col, lw=LW)
    stroke(ctx, lambda c: (c.move_to(cx - s * 0.32, cy + s * 0.32), c.line_to(cx + s * 0.28, cy - s * 0.3)), shade(col, 0.5), 3.5)


def g_rock(ctx, cx, cy, s, col=EARTH, col2=None):
    paint(ctx, lambda c: poly_path(c, [(cx - s * 0.4, cy + s * 0.3), (cx - s * 0.34, cy - s * 0.1), (cx - s * 0.08, cy - s * 0.38),
                                         (cx + s * 0.3, cy - s * 0.26), (cx + s * 0.42, cy + s * 0.12), (cx + s * 0.2, cy + s * 0.36)]), col, lw=LW)


def g_shield(ctx, cx, cy, s, col=STEEL, col2=None):
    paint(ctx, lambda c: smooth_closed(c, [(cx - s * 0.36, cy - s * 0.38), (cx + s * 0.36, cy - s * 0.38), (cx + s * 0.34, cy + s * 0.06),
                                             (cx, cy + s * 0.46), (cx - s * 0.34, cy + s * 0.06)], 0.3), col, lw=LW)
    if col2:
        paint(ctx, lambda c: smooth_closed(c, [(cx - s * 0.14, cy - s * 0.18), (cx + s * 0.14, cy - s * 0.18), (cx + s * 0.12, cy + s * 0.06),
                                                 (cx, cy + s * 0.22), (cx - s * 0.12, cy + s * 0.06)], 0.3), col2, lw=3, hi=False)


def g_sword(ctx, cx, cy, s, col=STEEL, col2=GOLD):
    paint(ctx, lambda c: poly_path(c, [(cx - s * 0.06, cy + s * 0.14), (cx - s * 0.06, cy - s * 0.36), (cx, cy - s * 0.48), (cx + s * 0.06, cy - s * 0.36),
                                         (cx + s * 0.06, cy + s * 0.14)]), col, lw=LW)
    outlined_line(ctx, [(cx - s * 0.22, cy + s * 0.16), (cx + s * 0.22, cy + s * 0.16)], col2, s * 0.08, s * 0.08 + 7, smooth=False)
    outlined_line(ctx, [(cx, cy + s * 0.2), (cx, cy + s * 0.42)], WOOD, s * 0.08, s * 0.08 + 7, smooth=False)


def g_dagger(ctx, cx, cy, s, col=STEEL, col2=BOLT2):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(0.6)
    g_sword(ctx, 0, 0, s * 0.85, col, col2)
    ctx.restore()


def g_bow(ctx, cx, cy, s, col=WOOD, col2=WIND):
    def bow(c):
        smooth_open(c, [(cx + s * 0.1, cy - s * 0.46), (cx - s * 0.26, cy), (cx + s * 0.1, cy + s * 0.46)])
    stroke(ctx, bow, INK, 13)
    stroke(ctx, bow, col, 7)
    stroke(ctx, lambda c: (c.move_to(cx + s * 0.1, cy - s * 0.46), c.line_to(cx + s * 0.1, cy + s * 0.46)), (1, 1, 1), 2.5)
    outlined_line(ctx, [(cx - s * 0.3, cy), (cx + s * 0.42, cy)], col2, 4, 10, smooth=False)


def g_staff(ctx, cx, cy, s, col=WOOD, col2=PURPLE):
    outlined_line(ctx, [(cx - s * 0.26, cy + s * 0.42), (cx + s * 0.16, cy - s * 0.26)], col, s * 0.08, s * 0.08 + 7, smooth=False)
    glow(ctx, cx + s * 0.22, cy - s * 0.32, s * 0.3, col2, 0.6)
    paint(ctx, lambda c: ellipse_path(c, cx + s * 0.22, cy - s * 0.32, s * 0.14, s * 0.14), col2, lw=4)


def g_star(ctx, cx, cy, s, col=GOLD, col2=None):
    paint(ctx, lambda c: star_path(c, cx, cy, s * 0.46, s * 0.2, 5), col, lw=LW)


def g_heart(ctx, cx, cy, s, col=RED, col2=None):
    def heart(c):
        c.move_to(cx, cy + s * 0.4)
        c.curve_to(cx - s * 0.52, cy + s * 0.02, cx - s * 0.44, cy - s * 0.44, cx, cy - s * 0.18)
        c.curve_to(cx + s * 0.44, cy - s * 0.44, cx + s * 0.52, cy + s * 0.02, cx, cy + s * 0.4)
        c.close_path()
    paint(ctx, heart, col, lw=LW)


def g_crown(ctx, cx, cy, s, col=GOLD, col2=RED):
    paint(ctx, lambda c: poly_path(c, [(cx - s * 0.4, cy + s * 0.28), (cx - s * 0.42, cy - s * 0.24), (cx - s * 0.2, cy), (cx, cy - s * 0.38),
                                         (cx + s * 0.2, cy), (cx + s * 0.42, cy - s * 0.24), (cx + s * 0.4, cy + s * 0.28)]), col, lw=LW)
    paint(ctx, lambda c: ellipse_path(c, cx, cy + s * 0.12, s * 0.07, s * 0.07), col2, lw=2.5, hi=False)


def g_feather(ctx, cx, cy, s, col=FIRE, col2=FIRE2):
    paint(ctx, lambda c: smooth_closed(c, [(cx - s * 0.32, cy + s * 0.42), (cx - s * 0.26, cy), (cx + s * 0.06, cy - s * 0.36), (cx + s * 0.38, cy - s * 0.44),
                                             (cx + s * 0.24, cy - s * 0.08), (cx - s * 0.06, cy + s * 0.24)], 0.5), col, lw=LW)
    stroke(ctx, lambda c: (c.move_to(cx - s * 0.36, cy + s * 0.46), c.line_to(cx + s * 0.3, cy - s * 0.36)), col2, 4)


def g_chain(ctx, cx, cy, s, col=STEEL, col2=None):
    for k in range(3):
        x = cx - s * 0.3 + k * s * 0.3
        y = cy + (s * 0.12 if k % 2 else -s * 0.12)
        stroke(ctx, lambda c, x=x, y=y, k=k: ellipse_path(c, x, y, s * 0.2, s * 0.12, 0.5 if k % 2 else -0.5), INK, 12)
        stroke(ctx, lambda c, x=x, y=y, k=k: ellipse_path(c, x, y, s * 0.2, s * 0.12, 0.5 if k % 2 else -0.5), col, 6)


def g_battery(ctx, cx, cy, s, col=STEEL, col2=BOLT2):
    paint(ctx, lambda c: rrect_path(c, cx - s * 0.22, cy - s * 0.36, s * 0.44, s * 0.78, 8), col, lw=LW)
    paint(ctx, lambda c: rrect_path(c, cx - s * 0.08, cy - s * 0.46, s * 0.16, s * 0.1, 3), col, lw=4, hi=False)
    flat(ctx, lambda c: rrect_path(c, cx - s * 0.14, cy - s * 0.02, s * 0.28, s * 0.36, 4), col2)
    g_bolt(ctx, cx, cy + s * 0.02, s * 0.36, (1, 1, 1))


def g_eye(ctx, cx, cy, s, col=(1, 1, 1), col2=PURPLE):
    paint(ctx, lambda c: smooth_closed(c, [(cx - s * 0.46, cy), (cx, cy - s * 0.28), (cx + s * 0.46, cy), (cx, cy + s * 0.28)], 0.6), col, lw=LW, hi=False)
    paint(ctx, lambda c: ellipse_path(c, cx, cy, s * 0.16, s * 0.16), col2, lw=3.5, hi=False)
    flat(ctx, lambda c: ellipse_path(c, cx, cy, s * 0.07, s * 0.07), INK)


def g_coin(ctx, cx, cy, s, col=GOLD, col2=None):
    paint(ctx, lambda c: ellipse_path(c, cx, cy, s * 0.42, s * 0.42), col, lw=LW, hi_size=0.6)
    stroke(ctx, lambda c: ellipse_path(c, cx, cy, s * 0.28, s * 0.28), shade(col, 0.35), 3.5)
    paint(ctx, lambda c: star_path(c, cx, cy, s * 0.16, s * 0.07, 4, 0), light(col, 0.4), lw=0, outline=False, hi=False)


def g_gem(ctx, cx, cy, s, col=PURPLE, col2=None):
    pts = [(cx, cy - s * 0.44), (cx + s * 0.32, cy - s * 0.12), (cx + s * 0.2, cy + s * 0.38), (cx - s * 0.2, cy + s * 0.38), (cx - s * 0.32, cy - s * 0.12)]
    paint(ctx, lambda c: poly_path(c, pts), col, lw=LW, hi_size=0.8)
    stroke(ctx, lambda c: (c.move_to(cx - s * 0.32, cy - s * 0.12), c.line_to(cx + s * 0.32, cy - s * 0.12), c.move_to(cx, cy - s * 0.44), c.line_to(cx, cy + s * 0.38)),
           light(col, 0.5), 2.5, 0.8)
    sparkle(ctx, cx - s * 0.1, cy - s * 0.2, s * 0.1)


def g_bell(ctx, cx, cy, s, col=GOLD, col2=None):
    paint(ctx, lambda c: smooth_closed(c, [(cx - s * 0.38, cy + s * 0.26), (cx - s * 0.28, cy - s * 0.12), (cx - s * 0.12, cy - s * 0.36),
                                             (cx + s * 0.12, cy - s * 0.36), (cx + s * 0.28, cy - s * 0.12), (cx + s * 0.38, cy + s * 0.26)], 0.4), col, lw=LW)
    paint(ctx, lambda c: ellipse_path(c, cx, cy + s * 0.34, s * 0.09, s * 0.09), shade(col, 0.3), lw=3.5, hi=False)


def g_drum(ctx, cx, cy, s, col=RED, col2=STEEL):
    paint(ctx, lambda c: rrect_path(c, cx - s * 0.36, cy - s * 0.2, s * 0.72, s * 0.5, 10), col, lw=LW)
    paint(ctx, lambda c: ellipse_path(c, cx, cy - s * 0.2, s * 0.36, s * 0.12), light(col2, 0.3), lw=4, hi=False)
    for k in range(4):
        x = cx - s * 0.3 + k * s * 0.2
        stroke(ctx, lambda c, x=x, k=k: (c.move_to(x, cy - s * 0.1), c.line_to(x + s * 0.1, cy + s * 0.24)), GOLD, 3)


def g_book(ctx, cx, cy, s, col=hex2rgb("#5a7ad0"), col2=GOLD):
    paint(ctx, lambda c: rrect_path(c, cx - s * 0.34, cy - s * 0.38, s * 0.68, s * 0.76, 6), col, lw=LW)
    flat(ctx, lambda c: rrect_path(c, cx - s * 0.26, cy - s * 0.3, s * 0.08, s * 0.6, 2), shade(col, 0.4))
    g_star(ctx, cx + s * 0.04, cy - s * 0.04, s * 0.36, col2)


def g_purse(ctx, cx, cy, s, col=hex2rgb("#a0703f"), col2=GOLD):
    paint(ctx, lambda c: smooth_closed(c, [(cx - s * 0.16, cy - s * 0.2), (cx + s * 0.16, cy - s * 0.2), (cx + s * 0.4, cy + s * 0.18), (cx + s * 0.26, cy + s * 0.42),
                                             (cx - s * 0.26, cy + s * 0.42), (cx - s * 0.4, cy + s * 0.18)], 0.5), col, lw=LW)
    stroke(ctx, lambda c: (c.move_to(cx - s * 0.2, cy - s * 0.24), c.line_to(cx + s * 0.2, cy - s * 0.24)), col2, 5)
    g_coin(ctx, cx + s * 0.2, cy - s * 0.32, s * 0.36)


def g_mountain(ctx, cx, cy, s, col=hex2rgb("#9a8f86"), col2=(1, 1, 1)):
    paint(ctx, lambda c: poly_path(c, [(cx - s * 0.46, cy + s * 0.34), (cx - s * 0.1, cy - s * 0.38), (cx + s * 0.08, cy - s * 0.08), (cx + s * 0.2, cy - s * 0.22),
                                         (cx + s * 0.46, cy + s * 0.34)]), col, lw=LW)
    flat(ctx, lambda c: poly_path(c, [(cx - s * 0.1, cy - s * 0.38), (cx - s * 0.2, cy - s * 0.18), (cx, cy - s * 0.18)]), col2)


def g_cloud(ctx, cx, cy, s, col=(0.92, 0.94, 1.0), col2=None):
    paint(ctx, lambda c: smooth_closed(c, [(cx - s * 0.42, cy + s * 0.14), (cx - s * 0.34, cy - s * 0.1), (cx - s * 0.12, cy - s * 0.16), (cx, cy - s * 0.34),
                                             (cx + s * 0.24, cy - s * 0.24), (cx + s * 0.42, cy), (cx + s * 0.38, cy + s * 0.18), (cx, cy + s * 0.2)], 0.5), col, lw=LW)


def g_magnet(ctx, cx, cy, s, col=RED, col2=STEEL):
    def arc(c):
        c.arc(cx, cy - s * 0.04, s * 0.28, math.pi, 0)
    stroke(ctx, arc, INK, s * 0.22 + 7)
    stroke(ctx, arc, col, s * 0.22)
    for side in (-1, 1):
        outlined_line(ctx, [(cx + side * s * 0.28, cy - s * 0.04), (cx + side * s * 0.28, cy + s * 0.3)], col, s * 0.22, s * 0.22 + 7, smooth=False)
        flat(ctx, lambda c, side=side: rrect_path(c, cx + side * s * 0.28 - s * 0.11, cy + s * 0.22, s * 0.22, s * 0.12, 2), col2)


def g_spikes(ctx, cx, cy, s, col=ICE, col2=None):
    for k, (dx, h) in enumerate(((-0.28, 0.5), (0, 0.8), (0.28, 0.6))):
        paint(ctx, lambda c, dx=dx, h=h: poly_path(c, [(cx + s * (dx - 0.13), cy + s * 0.38), (cx + s * dx, cy + s * (0.38 - h)), (cx + s * (dx + 0.13), cy + s * 0.38)]),
              col, lw=4.5, hi_size=0.7)


def g_burst(ctx, cx, cy, s, col=FIRE2, col2=FIRE):
    paint(ctx, lambda c: star_path(c, cx, cy, s * 0.48, s * 0.24, 8), col2, lw=LW)
    paint(ctx, lambda c: star_path(c, cx, cy, s * 0.26, s * 0.14, 8, 0.2), col, lw=0, outline=False, hi=False)


def g_skull(ctx, cx, cy, s, col=(0.95, 0.93, 0.88), col2=None):
    paint(ctx, lambda c: smooth_closed(c, [(cx - s * 0.34, cy), (cx - s * 0.3, cy - s * 0.3), (cx, cy - s * 0.42), (cx + s * 0.3, cy - s * 0.3), (cx + s * 0.34, cy),
                                             (cx + s * 0.2, cy + s * 0.18), (cx + s * 0.16, cy + s * 0.36), (cx - s * 0.16, cy + s * 0.36), (cx - s * 0.2, cy + s * 0.18)], 0.45), col, lw=LW)
    for side in (-1, 1):
        flat(ctx, lambda c, side=side: ellipse_path(c, cx + side * s * 0.14, cy - s * 0.04, s * 0.1, s * 0.11), INK)


def g_mirror(ctx, cx, cy, s, col=hex2rgb("#bfe8ff"), col2=GOLD):
    paint(ctx, lambda c: ellipse_path(c, cx, cy - s * 0.06, s * 0.3, s * 0.38), col2, lw=LW)
    paint(ctx, lambda c: ellipse_path(c, cx, cy - s * 0.06, s * 0.22, s * 0.3), col, lw=3, hi_size=0.8)
    outlined_line(ctx, [(cx, cy + s * 0.32), (cx, cy + s * 0.48)], col2, s * 0.08, s * 0.08 + 7, smooth=False)


def g_scroll(ctx, cx, cy, s, col=hex2rgb("#f4e4c4"), col2=RED):
    paint(ctx, lambda c: rrect_path(c, cx - s * 0.32, cy - s * 0.36, s * 0.64, s * 0.72, 8), col, lw=LW)
    for k in range(3):
        stroke(ctx, lambda c, k=k: (c.move_to(cx - s * 0.2, cy - s * 0.2 + k * s * 0.14), c.line_to(cx + s * 0.2, cy - s * 0.2 + k * s * 0.14)), shade(col, 0.5), 3)
    paint(ctx, lambda c: ellipse_path(c, cx + s * 0.14, cy + s * 0.22, s * 0.12, s * 0.12), col2, lw=3.5, hi=False)


def g_sprout(ctx, cx, cy, s, col=EARTH2, col2=None):
    outlined_line(ctx, [(cx, cy + s * 0.42), (cx, cy - s * 0.04)], shade(col, 0.2), s * 0.07, s * 0.07 + 7, smooth=False)
    for side in (-1, 1):
        paint(ctx, lambda c, side=side: smooth_closed(c, [(cx, cy), (cx + side * s * 0.2, cy - s * 0.32), (cx + side * s * 0.42, cy - s * 0.2),
                                                           (cx + side * s * 0.22, cy + s * 0.04)], 0.5), col, lw=4)


def g_gear(ctx, cx, cy, s, col=STEEL, col2=None):
    paint(ctx, lambda c: star_path(c, cx, cy, s * 0.44, s * 0.34, 8, 0.2), col, lw=LW)
    paint(ctx, lambda c: ellipse_path(c, cx, cy, s * 0.14, s * 0.14), shade(col, 0.4), lw=3.5, hi=False)


def g_arrow_up(ctx, cx, cy, s, col=hex2rgb("#7cff9a"), col2=None):
    paint(ctx, lambda c: poly_path(c, [(cx, cy - s * 0.44), (cx + s * 0.34, cy - s * 0.04), (cx + s * 0.12, cy - s * 0.04), (cx + s * 0.12, cy + s * 0.42),
                                         (cx - s * 0.12, cy + s * 0.42), (cx - s * 0.12, cy - s * 0.04), (cx - s * 0.34, cy - s * 0.04)]), col, lw=LW)


def g_hourglass(ctx, cx, cy, s, col=hex2rgb("#7fd8ff"), col2=GOLD):
    paint(ctx, lambda c: poly_path(c, [(cx - s * 0.26, cy - s * 0.38), (cx + s * 0.26, cy - s * 0.38), (cx + s * 0.04, cy), (cx + s * 0.26, cy + s * 0.38),
                                         (cx - s * 0.26, cy + s * 0.38), (cx - s * 0.04, cy)]), col, lw=LW)
    for y in (-0.42, 0.42):
        outlined_line(ctx, [(cx - s * 0.32, cy + s * y), (cx + s * 0.32, cy + s * y)], col2, s * 0.08, s * 0.08 + 6, smooth=False)


def g_fist(ctx, cx, cy, s, col=hex2rgb("#d99a6c"), col2=None):
    paint(ctx, lambda c: rrect_path(c, cx - s * 0.32, cy - s * 0.26, s * 0.64, s * 0.52, 14), col, lw=LW)
    for k in range(3):
        stroke(ctx, lambda c, k=k: (c.move_to(cx - s * 0.12 + k * s * 0.14, cy - s * 0.26), c.line_to(cx - s * 0.12 + k * s * 0.14, cy - s * 0.06)), INK, 3)


def g_cross(ctx, cx, cy, s, col=hex2rgb("#7cff9a"), col2=None):
    paint(ctx, lambda c: poly_path(c, [(cx - s * 0.12, cy - s * 0.4), (cx + s * 0.12, cy - s * 0.4), (cx + s * 0.12, cy - s * 0.12), (cx + s * 0.4, cy - s * 0.12),
                                         (cx + s * 0.4, cy + s * 0.12), (cx + s * 0.12, cy + s * 0.12), (cx + s * 0.12, cy + s * 0.4), (cx - s * 0.12, cy + s * 0.4),
                                         (cx - s * 0.12, cy + s * 0.12), (cx - s * 0.4, cy + s * 0.12), (cx - s * 0.4, cy - s * 0.12), (cx - s * 0.12, cy - s * 0.12)]), col, lw=LW)


def g_hat(ctx, cx, cy, s, col=PURPLE, col2=GOLD):
    paint(ctx, lambda c: smooth_closed(c, [(cx - s * 0.44, cy + s * 0.3), (cx - s * 0.16, cy + s * 0.16), (cx + s * 0.04, cy - s * 0.44),
                                             (cx + s * 0.18, cy + s * 0.16), (cx + s * 0.44, cy + s * 0.3), (cx, cy + s * 0.38)], 0.35), col, lw=LW)
    paint(ctx, lambda c: star_path(c, cx + s * 0.02, cy - s * 0.02, s * 0.1, s * 0.04, 5), col2, lw=2, hi=False)


def g_quiver(ctx, cx, cy, s, col=WOOD, col2=WIND):
    paint(ctx, lambda c: rrect_path(c, cx - s * 0.18, cy - s * 0.1, s * 0.36, s * 0.52, 8), col, lw=LW)
    for k in range(3):
        x = cx - s * 0.1 + k * s * 0.1
        outlined_line(ctx, [(x, cy - s * 0.1), (x + s * 0.04, cy - s * 0.42)], (0.95, 0.92, 0.85), 3, 8, smooth=False)
        paint(ctx, lambda c, x=x: poly_path(c, [(x - s * 0.04, cy - s * 0.4), (x + s * 0.04, cy - s * 0.48), (x + s * 0.1, cy - s * 0.38)]), col2, lw=2.5, hi=False)


def g_cannon(ctx, cx, cy, s, col=hex2rgb("#5a5470"), col2=FIRE2):
    paint(ctx, lambda c: rrect_path(c, cx - s * 0.38, cy - s * 0.18, s * 0.66, s * 0.3, 10), col, lw=LW)
    paint(ctx, lambda c: ellipse_path(c, cx - s * 0.18, cy + s * 0.22, s * 0.16, s * 0.16), WOOD, lw=4)
    g_burst(ctx, cx + s * 0.36, cy - s * 0.04, s * 0.42, col2, FIRE)


def g_echo(ctx, cx, cy, s, col=PURPLE, col2=None):
    for k in range(3):
        r = s * (0.18 + k * 0.12)
        stroke(ctx, lambda c, r=r: c.arc(cx - s * 0.1, cy, r, -0.9, 0.9), INK, 9)
        stroke(ctx, lambda c, r=r: c.arc(cx - s * 0.1, cy, r, -0.9, 0.9), light(col, k * 0.2), 4.5)
    paint(ctx, lambda c: star_path(c, cx - s * 0.14, cy, s * 0.14, s * 0.06, 4), GOLD, lw=2.5, hi=False)


def g_lens(ctx, cx, cy, s, col=hex2rgb("#bfe8ff"), col2=RED):
    outlined_line(ctx, [(cx + s * 0.16, cy + s * 0.16), (cx + s * 0.42, cy + s * 0.42)], WOOD, s * 0.1, s * 0.1 + 7, smooth=False)
    paint(ctx, lambda c: ellipse_path(c, cx - s * 0.06, cy - s * 0.06, s * 0.3, s * 0.3), col, lw=LW, hi_size=0.8)
    stroke(ctx, lambda c: (c.move_to(cx - s * 0.18, cy - s * 0.06), c.line_to(cx + s * 0.06, cy - s * 0.06), c.move_to(cx - s * 0.06, cy - s * 0.18), c.line_to(cx - s * 0.06, cy + s * 0.06)), col2, 3)


def g_target(ctx, cx, cy, s, col=RED, col2=(1, 1, 1)):
    for k, cc in enumerate((col, col2, col)):
        paint(ctx, lambda c, k=k: ellipse_path(c, cx, cy, s * (0.42 - k * 0.13), s * (0.42 - k * 0.13)), cc, lw=4 if k == 0 else 2.5, hi=False, shade_amt=0)


def g_crack_shield(ctx, cx, cy, s, col=STEEL, col2=None):
    g_shield(ctx, cx, cy, s, col)
    stroke(ctx, lambda c: (c.move_to(cx - s * 0.04, cy - s * 0.38), c.line_to(cx + s * 0.08, cy - s * 0.1), c.line_to(cx - s * 0.06, cy + s * 0.06), c.line_to(cx + s * 0.04, cy + s * 0.32)),
           INK, 4.5)


def g_dots(ctx, cx, cy, s, col=GOLD, col2=None):
    pts = [(cx, cy - s * 0.26), (cx - s * 0.26, cy + s * 0.18), (cx + s * 0.26, cy + s * 0.18)]
    for a, b in ((0, 1), (1, 2), (2, 0)):
        outlined_line(ctx, [pts[a], pts[b]], light(col, 0.3), 4, 9, smooth=False)
    for p in pts:
        paint(ctx, lambda c, p=p: ellipse_path(c, p[0], p[1], s * 0.13, s * 0.13), col, lw=4)


def g_tower(ctx, cx, cy, s, col=STEEL, col2=BOLT2):
    paint(ctx, lambda c: poly_path(c, [(cx - s * 0.14, cy + s * 0.44), (cx - s * 0.06, cy - s * 0.24), (cx + s * 0.06, cy - s * 0.24), (cx + s * 0.14, cy + s * 0.44)]), col, lw=4.5)
    glow(ctx, cx, cy - s * 0.3, s * 0.3, col2, 0.7)
    paint(ctx, lambda c: ellipse_path(c, cx, cy - s * 0.32, s * 0.1, s * 0.1), col2, lw=3.5, hi=False)
    for side in (-1, 1):
        stroke(ctx, lambda c, side=side: (c.move_to(cx + side * s * 0.14, cy - s * 0.34), c.line_to(cx + side * s * 0.3, cy - s * 0.24), c.line_to(cx + side * s * 0.24, cy - s * 0.12),
                                           c.line_to(cx + side * s * 0.4, cy - s * 0.02)), col2, 3.5)


GLYPHS = {
    "flame": g_flame, "drop": g_drop, "bolt": g_bolt, "snowflake": g_snowflake, "swirl": g_swirl, "leaf": g_leaf, "rock": g_rock,
    "shield": g_shield, "sword": g_sword, "dagger": g_dagger, "bow": g_bow, "staff": g_staff, "star": g_star, "heart": g_heart,
    "crown": g_crown, "feather": g_feather, "chain": g_chain, "battery": g_battery, "eye": g_eye, "coin": g_coin, "gem": g_gem,
    "bell": g_bell, "drum": g_drum, "book": g_book, "purse": g_purse, "mountain": g_mountain, "cloud": g_cloud, "magnet": g_magnet,
    "spikes": g_spikes, "burst": g_burst, "skull": g_skull, "mirror": g_mirror, "scroll": g_scroll, "sprout": g_sprout, "gear": g_gear,
    "arrow_up": g_arrow_up, "hourglass": g_hourglass, "fist": g_fist, "cross": g_cross, "hat": g_hat, "quiver": g_quiver,
    "cannon": g_cannon, "echo": g_echo, "lens": g_lens, "target": g_target, "crack_shield": g_crack_shield, "dots": g_dots,
    "tower": g_tower,
}


def glyph(ctx, name, cx, cy, s, col=None, col2=None):
    fn = GLYPHS[name]
    kwargs = {}
    if col is not None:
        kwargs["col"] = col
    if col2 is not None:
        kwargs["col2"] = col2
    fn(ctx, cx, cy, s, **kwargs)
