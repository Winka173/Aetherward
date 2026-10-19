"""Procedural rift-monster sprites. Each archetype has its own silhouette and colour family so threats
read at a glance: round imps (grunt), long hounds (runner), tiny blobs (swarm), shield walls,
hooded casters with floating orbs, bomb goblins, warded golems, spiked brutes, banner bearers...

Two walk frames (a/b). Normal canvas 256 (feet at y=236), bosses 512 (feet at y=486).
"""
import math
from toolkit import (INK, Canvas, hex2rgb, mix, shade, light, paint, flat, stroke, glow, sparkle,
                     smooth_closed, smooth_open, ellipse_path, rrect_path, poly_path, star_path, outlined_line)

LW = 6.0


def angry_eyes(ctx, cx, cy, spread, size, color=(1.0, 0.95, 0.5), pupil=INK, single=False):
    xs = [cx] if single else [cx - spread, cx + spread]
    for i, x in enumerate(xs):
        paint(ctx, lambda c, x=x: ellipse_path(c, x, cy, size, size * 0.85), color, lw=3.5, hi=False, shade_amt=0)
        flat(ctx, lambda c, x=x: ellipse_path(c, x + (2 if i == 0 else -2), cy + 1, size * 0.45, size * 0.55), pupil)
        flat(ctx, lambda c, x=x: ellipse_path(c, x - size * 0.25, cy - size * 0.3, size * 0.18, size * 0.18), (1, 1, 1))
        # angry brow
        if not single:
            side = -1 if i == 0 else 1
            stroke(ctx, lambda c, x=x, side=side: (c.move_to(x - side * size * 1.1, cy - size * 1.25), c.line_to(x + side * size * 0.6, cy - size * 0.75)), INK, 4)


def fang_mouth(ctx, cx, cy, w):
    paint(ctx, lambda c: smooth_closed(c, [(cx - w, cy), (cx + w, cy), (cx + w * 0.6, cy + w * 0.5), (cx - w * 0.6, cy + w * 0.5)], 0.5),
          hex2rgb("#3a1030"), lw=3, hi=False, shade_amt=0)
    for s in (-1, 1):
        flat(ctx, lambda c, s=s: poly_path(c, [(cx + s * w * 0.55, cy), (cx + s * w * 0.3, cy), (cx + s * w * 0.42, cy + w * 0.35)]), (1, 1, 1))


def feet(ctx, cx, ground, spread, size, color, frame):
    off = 5 if frame == "b" else -5
    for i, s in enumerate((-1, 1)):
        lift = off * (1 if i == 0 else -1)
        paint(ctx, lambda c, s=s, lift=lift: ellipse_path(c, cx + s * spread, ground - size * 0.6 + min(0, lift), size * 1.2, size * 0.7),
              shade(color, 0.35), lw=LW - 1, hi=False)


def horns(ctx, cx, top, spread, length, color):
    for s in (-1, 1):
        paint(ctx, lambda c, s=s: smooth_closed(c, [(cx + s * spread, top + 8), (cx + s * (spread + length * 0.4), top - length * 0.7),
                                                     (cx + s * (spread + length * 0.15), top - length), (cx + s * (spread - 8), top + 2)], 0.5),
              color, lw=4.5, hi_size=0.6)


def enemy_sprite(eid, frame="a"):
    big = eid in ("siegebreaker_golem", "rift_warden")
    size = 512 if big else 256
    cv = Canvas(size, size)
    ctx = cv.ctx
    bob = -4 if frame == "b" else 0
    fn = DRAWERS[eid]
    fn(ctx, bob, frame)
    return cv


# ---------------------------------------------------------------------------- archetypes

def grunt(ctx, bob, frame):
    body = hex2rgb("#7b4fd0")
    feet(ctx, 128, 236, 26, 18, body, frame)
    # club
    outlined_line(ctx, [(176, 200 + bob), (214, 120 + bob)], hex2rgb("#8a5a34"), 10, 17, smooth=False)
    paint(ctx, lambda c: ellipse_path(c, 216, 112 + bob, 20, 26, 0.4), hex2rgb("#a0703f"), lw=LW)
    horns(ctx, 128, 92 + bob, 30, 34, hex2rgb("#f0e0c8"))
    paint(ctx, lambda c: smooth_closed(c, [(70, 160 + bob), (90, 100 + bob), (128, 84 + bob), (166, 100 + bob), (186, 160 + bob),
                                             (170, 222 + bob), (128, 230 + bob), (86, 222 + bob)], 0.55), body, lw=LW)
    flat(ctx, lambda c: ellipse_path(c, 128, 190 + bob, 34, 26), light(body, 0.35))
    angry_eyes(ctx, 128, 136 + bob, 22, 13)
    fang_mouth(ctx, 128, 168 + bob, 18)
    paint(ctx, lambda c: ellipse_path(c, 182, 196 + bob, 14, 14), shade(body, 0.1), lw=4.5, hi=False)


def runner(ctx, bob, frame):
    body = hex2rgb("#e05a8a")
    leg = 8 if frame == "b" else -8
    for x, l in ((92, leg), (114, -leg), (160, -leg), (182, leg)):
        outlined_line(ctx, [(x, 176 + bob), (x + l, 232)], shade(body, 0.3), 11, 18)
    # tail
    outlined_line(ctx, [(70, 160 + bob), (40, 130 + bob), (34, 108 + bob)], body, 10, 17)
    paint(ctx, lambda c: smooth_closed(c, [(60, 168 + bob), (90, 140 + bob), (160, 136 + bob), (200, 126 + bob), (222, 150 + bob),
                                             (206, 186 + bob), (150, 194 + bob), (88, 196 + bob)], 0.5), body, lw=LW)
    # head
    for s in (-1, 1):
        paint(ctx, lambda c, s=s: poly_path(c, [(194 + s * 14, 112 + bob), (198 + s * 24, 70 + bob), (210 + s * 6, 108 + bob)]), body, lw=4.5, hi=False)
    paint(ctx, lambda c: smooth_closed(c, [(176, 140 + bob), (190, 104 + bob), (222, 100 + bob), (242, 128 + bob), (226, 152 + bob)], 0.5),
          light(body, 0.1), lw=LW)
    angry_eyes(ctx, 210, 122 + bob, 10, 7)
    stroke(ctx, lambda c: smooth_open(c, [(212, 142 + bob), (226, 140 + bob), (236, 134 + bob)]), INK, 3)
    # speed streaks
    for i in range(3):
        stroke(ctx, lambda c, i=i: (c.move_to(30 - i * 4, 176 + i * 14), c.line_to(56 - i * 4, 176 + i * 14)), light(body, 0.5), 4, 0.8)


def swarmling(ctx, bob, frame):
    body = hex2rgb("#b07aff")
    feet(ctx, 128, 236, 14, 10, body, frame)
    paint(ctx, lambda c: smooth_closed(c, [(92, 200 + bob), (100, 160 + bob), (128, 146 + bob), (156, 160 + bob), (164, 200 + bob),
                                             (148, 228 + bob), (108, 228 + bob)], 0.55), body, lw=5)
    angry_eyes(ctx, 128, 184 + bob, 0, 13, single=True)
    for s in (-1, 1):
        paint(ctx, lambda c, s=s: smooth_closed(c, [(128 + s * 12, 152 + bob), (128 + s * 20, 128 + bob), (128 + s * 4, 150 + bob)], 0.5),
              light(body, 0.3), lw=3.5, hi=False)


def shieldbearer(ctx, bob, frame):
    body = hex2rgb("#5a6a8a")
    feet(ctx, 128, 236, 28, 20, body, frame)
    paint(ctx, lambda c: smooth_closed(c, [(74, 170 + bob), (94, 110 + bob), (128, 96 + bob), (162, 110 + bob), (182, 170 + bob),
                                             (166, 226 + bob), (90, 226 + bob)], 0.5), body, lw=LW)
    # helmet
    paint(ctx, lambda c: smooth_closed(c, [(86, 120 + bob), (96, 72 + bob), (128, 58 + bob), (160, 72 + bob), (170, 120 + bob),
                                             (150, 108 + bob), (106, 108 + bob)], 0.5), hex2rgb("#9aa6bc"), lw=LW, hi_size=0.7)
    flat(ctx, lambda c: rrect_path(c, 100, 104 + bob, 56, 16, 8), hex2rgb("#1b1830"))
    for s in (-1, 1):
        flat(ctx, lambda c, s=s: ellipse_path(c, 128 + s * 13, 112 + bob, 6, 4), hex2rgb("#ff6a5a"))
    # tower shield (front)
    def shield(c):
        rrect_path(c, 70, 128 + bob, 116, 104, 18)
    paint(ctx, shield, hex2rgb("#7a86a0"), lw=LW, hi_size=0.6)
    stroke(ctx, lambda c: rrect_path(c, 82, 140 + bob, 92, 80, 12), hex2rgb("#c8d0e0"), 4)
    paint(ctx, lambda c: star_path(c, 128, 180 + bob, 22, 9, 4), hex2rgb("#b07aff"), lw=3.5, hi=False)


def hexcaster(ctx, bob, frame):
    robe = hex2rgb("#3a2a6a")
    glowc = hex2rgb("#7cff6a")
    fl = 6 if frame == "b" else 0
    glow(ctx, 128, 96 + bob - fl, 46, glowc, 0.6)
    paint(ctx, lambda c: smooth_closed(c, [(84, 230), (96, 180 + bob), (100, 124 + bob), (128, 96 + bob), (156, 124 + bob), (160, 180 + bob),
                                             (172, 230), (152, 216), (140, 234), (128, 218), (114, 234), (102, 216)], 0.4), robe, lw=LW)
    paint(ctx, lambda c: smooth_closed(c, [(96, 150 + bob), (106, 100 + bob), (128, 80 + bob), (150, 100 + bob), (160, 150 + bob),
                                             (128, 160 + bob)], 0.5), shade(robe, 0.15), lw=LW)
    flat(ctx, lambda c: ellipse_path(c, 128, 128 + bob, 22, 20), hex2rgb("#120a24"))
    for s in (-1, 1):
        glow(ctx, 128 + s * 9, 128 + bob, 10, glowc, 0.9)
        flat(ctx, lambda c, s=s: ellipse_path(c, 128 + s * 9, 128 + bob, 4, 3), (1, 1, 1))
    for s in (-1, 1):
        paint(ctx, lambda c, s=s: ellipse_path(c, 128 + s * 40, 176 + bob, 11, 11), hex2rgb("#8a7ab0"), lw=4, hi=False)
    paint(ctx, lambda c: ellipse_path(c, 128, 58 + bob - fl, 15, 15), glowc, lw=4, hi_size=0.8)
    sparkle(ctx, 122, 52 + bob - fl, 6)


def sapper(ctx, bob, frame):
    skin = hex2rgb("#6aa04a")
    feet(ctx, 118, 236, 20, 15, skin, frame)
    # bomb carried overhead
    paint(ctx, lambda c: ellipse_path(c, 150, 92 + bob, 44, 42), hex2rgb("#2a2838"), lw=LW, hi_size=0.5)
    stroke(ctx, lambda c: smooth_open(c, [(176, 60 + bob), (190, 40 + bob), (204, 36 + bob)]), hex2rgb("#c8a070"), 5)
    glow(ctx, 206, 34 + bob, 22, hex2rgb("#ffb23a"), 0.9)
    sparkle(ctx, 206, 34 + bob, 10, hex2rgb("#fff0a0"))
    flat(ctx, lambda c: rrect_path(c, 128, 84 + bob, 44, 12, 4), hex2rgb("#d04a3a"))
    paint(ctx, lambda c: smooth_closed(c, [(80, 190 + bob), (88, 150 + bob), (118, 136 + bob), (148, 150 + bob), (156, 190 + bob),
                                             (140, 226 + bob), (96, 226 + bob)], 0.55), hex2rgb("#7a5a3a"), lw=LW)
    paint(ctx, lambda c: smooth_closed(c, [(84, 142 + bob), (86, 110 + bob), (118, 96 + bob), (150, 110 + bob), (152, 142 + bob),
                                             (118, 158 + bob)], 0.5), skin, lw=LW)
    for s in (-1, 1):
        paint(ctx, lambda c, s=s: poly_path(c, [(118 + s * 28, 118 + bob), (118 + s * 56, 106 + bob), (118 + s * 30, 132 + bob)]), skin, lw=4, hi=False)
    angry_eyes(ctx, 118, 124 + bob, 13, 8)
    stroke(ctx, lambda c: smooth_open(c, [(106, 144 + bob), (118, 140 + bob), (130, 146 + bob)]), INK, 3)
    outlined_line(ctx, [(144, 150 + bob), (160, 128 + bob)], skin, 10, 17)


def warded(ctx, bob, frame):
    body = hex2rgb("#4a8a9a")
    ward = hex2rgb("#ffe58a")
    stroke(ctx, lambda c: ellipse_path(c, 128, 150 + bob, 92, 92), ward, 5, 0.7)
    for i in range(6):
        a = i * math.pi / 3 + (0.3 if frame == "b" else 0)
        paint(ctx, lambda c, a=a: star_path(c, 128 + math.cos(a) * 92, 150 + bob + math.sin(a) * 92, 9, 4, 4), ward, lw=2.5, hi=False)
    feet(ctx, 128, 236, 26, 18, body, frame)
    paint(ctx, lambda c: poly_path(c, [(80, 120 + bob), (104, 84 + bob), (152, 84 + bob), (176, 120 + bob), (170, 214 + bob), (128, 230 + bob),
                                         (86, 214 + bob)]), body, lw=LW)
    for (x, y) in ((106, 170), (146, 180), (126, 204)):
        stroke(ctx, lambda c, x=x, y=y: (c.move_to(x - 8, y + bob), c.line_to(x + 8, y + bob + 6)), shade(body, 0.4), 4)
    paint(ctx, lambda c: poly_path(c, [(128, 118 + bob), (148, 140 + bob), (128, 162 + bob), (108, 140 + bob)]), ward, lw=3.5, hi=False)
    angry_eyes(ctx, 128, 104 + bob, 18, 9)


def juggernaut(ctx, bob, frame):
    body = hex2rgb("#a43a3a")
    armor = hex2rgb("#4a3a48")
    feet(ctx, 128, 238, 40, 24, armor, frame)
    paint(ctx, lambda c: smooth_closed(c, [(44, 160 + bob), (70, 86 + bob), (128, 66 + bob), (186, 86 + bob), (212, 160 + bob),
                                             (190, 228 + bob), (66, 228 + bob)], 0.45), body, lw=LW)
    paint(ctx, lambda c: smooth_closed(c, [(66, 150 + bob), (88, 104 + bob), (168, 104 + bob), (190, 150 + bob), (168, 212 + bob),
                                             (88, 212 + bob)], 0.4), armor, lw=LW, hi_size=0.6)
    for x in (82, 128, 174):
        paint(ctx, lambda c, x=x: poly_path(c, [(x - 12, 96 + bob), (x, 54 + bob), (x + 12, 96 + bob)]), hex2rgb("#d8d0c8"), lw=4, hi=False)
    for s in (-1, 1):
        paint(ctx, lambda c, s=s: ellipse_path(c, 128 + s * 86, 182 + bob, 26, 26), armor, lw=LW, hi_size=0.6)
    angry_eyes(ctx, 128, 132 + bob, 22, 11, color=hex2rgb("#ffb070"))
    fang_mouth(ctx, 128, 168 + bob, 22)


def summoner(ctx, bob, frame):
    robe = hex2rgb("#b04ad0")
    portal = hex2rgb("#5affd6")
    a = 0.4 if frame == "b" else 0
    glow(ctx, 196, 86 + bob, 40, portal, 0.6)
    outlined_line(ctx, [(176, 228), (196, 92 + bob)], hex2rgb("#5a3a2a"), 9, 16, smooth=False)
    for i in range(3):
        stroke(ctx, lambda c, i=i: (c.arc(196, 80 + bob, 10 + i * 8, a + i, a + i + 4.0)), portal, 4)
    paint(ctx, lambda c: smooth_closed(c, [(80, 232), (92, 170 + bob), (100, 116 + bob), (128, 92 + bob), (156, 116 + bob), (164, 170 + bob),
                                             (176, 232)], 0.4), robe, lw=LW)
    paint(ctx, lambda c: smooth_closed(c, [(98, 136 + bob), (106, 96 + bob), (128, 78 + bob), (150, 96 + bob), (158, 136 + bob)], 0.5),
          shade(robe, 0.2), lw=LW)
    flat(ctx, lambda c: ellipse_path(c, 128, 118 + bob, 18, 16), hex2rgb("#1a0a24"))
    for s in (-1, 1):
        flat(ctx, lambda c, s=s: ellipse_path(c, 128 + s * 7, 118 + bob, 4, 3), portal)
    stroke(ctx, lambda c: smooth_open(c, [(104, 180 + bob), (128, 196 + bob), (152, 180 + bob)]), light(robe, 0.4), 5)


def banner(ctx, bob, frame):
    body = hex2rgb("#d08a2a")
    flag = hex2rgb("#b07aff")
    wave = 8 if frame == "b" else 0
    outlined_line(ctx, [(170, 232), (176, 34)], hex2rgb("#5a3a2a"), 8, 15, smooth=False)
    paint(ctx, lambda c: smooth_closed(c, [(178, 40), (236, 48 + wave), (230, 84), (240, 118 - wave), (178, 110)], 0.3), flag, lw=LW - 1)
    paint(ctx, lambda c: star_path(c, 206, 78, 14, 6, 5), hex2rgb("#ffe58a"), lw=3, hi=False)
    feet(ctx, 116, 236, 22, 16, body, frame)
    paint(ctx, lambda c: smooth_closed(c, [(70, 170 + bob), (84, 116 + bob), (116, 100 + bob), (148, 116 + bob), (162, 170 + bob),
                                             (148, 226 + bob), (84, 226 + bob)], 0.55), body, lw=LW)
    horns(ctx, 116, 108 + bob, 24, 24, hex2rgb("#f0e0c8"))
    angry_eyes(ctx, 116, 146 + bob, 18, 10)
    fang_mouth(ctx, 116, 176 + bob, 14)
    outlined_line(ctx, [(150, 180 + bob), (172, 150)], body, 12, 19)


def mimic(ctx, bob, frame):
    body = hex2rgb("#40c0b0")
    feet(ctx, 128, 236, 28, 18, body, frame)
    facets = [(70, 170), (96, 104), (128, 86), (160, 104), (186, 170), (160, 224), (96, 224)]
    paint(ctx, lambda c: poly_path(c, [(x, y + bob) for x, y in facets]), body, lw=LW)
    cols = [hex2rgb("#ff7a5a"), hex2rgb("#5ab0ff"), hex2rgb("#ffe05a")]
    for i, (a, b2) in enumerate(((0, 1), (2, 3), (4, 5))):
        flat(ctx, lambda c, a=a, b2=b2: poly_path(c, [(128, 160 + bob), (facets[a][0], facets[a][1] + bob), (facets[b2][0], facets[b2][1] + bob)]),
             cols[i], 0.5)
    stroke(ctx, lambda c: poly_path(c, [(x, y + bob) for x, y in facets]), INK, LW)
    angry_eyes(ctx, 128, 150 + bob, 0, 20, single=True, color=hex2rgb("#ffffff"))
    fang_mouth(ctx, 128, 186 + bob, 20)


def ravager(ctx, bob, frame):
    body = hex2rgb("#c03a5a")
    glow(ctx, 128, 140, 120, hex2rgb("#ff4a6a"), 0.3)
    feet(ctx, 128, 238, 44, 24, shade(body, 0.2), frame)
    horns(ctx, 128, 74 + bob, 46, 56, hex2rgb("#f4e8d8"))
    paint(ctx, lambda c: smooth_closed(c, [(36, 170 + bob), (62, 92 + bob), (128, 70 + bob), (194, 92 + bob), (220, 170 + bob),
                                             (200, 230 + bob), (56, 230 + bob)], 0.45), body, lw=LW)
    flat(ctx, lambda c: ellipse_path(c, 128, 190 + bob, 56, 32), light(body, 0.35))
    for s in (-1, 1):
        for k in range(3):
            paint(ctx, lambda c, s=s, k=k: poly_path(c, [(128 + s * (78 + k * 12), 200 + bob), (128 + s * (90 + k * 12), 236 + bob),
                                                          (128 + s * (70 + k * 12), 214 + bob)]), hex2rgb("#f4e8d8"), lw=3.5, hi=False)
    angry_eyes(ctx, 128, 128 + bob, 30, 15, color=hex2rgb("#ffe14a"))
    fang_mouth(ctx, 128, 164 + bob, 30)
    paint(ctx, lambda c: star_path(c, 128, 60 + bob, 18, 8, 5), hex2rgb("#ffd35a"), lw=3.5, hi=False)


def riftling(ctx, bob, frame):
    body = hex2rgb("#8a5aff")
    fl = 6 if frame == "b" else 0
    glow(ctx, 128, 170, 60, body, 0.55)
    paint(ctx, lambda c: smooth_closed(c, [(96, 200 - fl), (98, 160 - fl), (114, 128 - fl), (128, 96 - fl), (142, 128 - fl), (158, 160 - fl),
                                             (160, 200 - fl), (146, 222 - fl), (128, 210 - fl), (110, 222 - fl)], 0.5), body, lw=5)
    angry_eyes(ctx, 128, 176 - fl, 12, 8, color=hex2rgb("#e8d8ff"))


def golem(ctx, bob, frame):
    stone = hex2rgb("#8a7f78")
    core = hex2rgb("#b07aff")
    s = 2.0
    def P(pts):
        return [(x * s, y * s + bob * 2) for x, y in pts]
    glow(ctx, 256, 260, 220, core, 0.25)
    feet(ctx, 256, 486, 70, 34, stone, frame)
    for side in (-1, 1):
        paint(ctx, lambda c, side=side: smooth_closed(c, P([(128 + side * 70, 120), (128 + side * 108, 132), (128 + side * 114, 196),
                                                            (128 + side * 98, 222), (128 + side * 74, 200)]), 0.45), shade(stone, 0.1), lw=LW + 2)
        paint(ctx, lambda c, side=side: ellipse_path(c, 256 + side * 196, 452 + bob * 2, 44, 38), stone, lw=LW + 2)
    paint(ctx, lambda c: smooth_closed(c, P([(56, 150), (74, 92), (128, 70), (182, 92), (200, 150), (184, 224), (72, 224)]), 0.4), stone, lw=LW + 3)
    for (x1, y1, x2, y2) in ((96, 110, 112, 140), (160, 120, 146, 152), (90, 190, 112, 200)):
        stroke(ctx, lambda c, a=(x1, y1, x2, y2): (c.move_to(a[0] * s, a[1] * s + bob * 2), c.line_to(a[2] * s, a[3] * s + bob * 2)), core, 6)
    glow(ctx, 256, 330 + bob * 2, 70, core, 0.9)
    paint(ctx, lambda c: poly_path(c, P([(128, 148), (146, 166), (128, 186), (110, 166)])), core, lw=LW, hi_size=0.8)
    paint(ctx, lambda c: smooth_closed(c, P([(98, 96), (104, 58), (128, 48), (152, 58), (158, 96), (128, 104)]), 0.5), light(stone, 0.1), lw=LW + 2)
    for side in (-1, 1):
        glow(ctx, 256 + side * 26, 160 + bob * 2, 22, hex2rgb("#ffb23a"), 0.9)
        flat(ctx, lambda c, side=side: rrect_path(c, 256 + side * 26 - 12, 154 + bob * 2, 24, 12, 6), hex2rgb("#fff0a0"))


def warden(ctx, bob, frame):
    armor = hex2rgb("#2a2448")
    cloak = hex2rgb("#5a2a8a")
    rift = hex2rgb("#ff4ad8")
    hov = (10 if frame == "b" else 0)
    glow(ctx, 256, 250, 240, rift, 0.28)
    flat(ctx, lambda c: ellipse_path(c, 256, 488, 120, 18), (0, 0, 0), 0.25)
    paint(ctx, lambda c: smooth_closed(c, [(130, 450 - hov), (150, 300 - hov), (180, 190 - hov), (256, 150 - hov), (332, 190 - hov),
                                             (362, 300 - hov), (382, 450 - hov), (330, 420 - hov), (300, 462 - hov), (256, 430 - hov),
                                             (212, 462 - hov), (182, 420 - hov)], 0.4), cloak, lw=LW + 2)
    paint(ctx, lambda c: smooth_closed(c, [(180, 280 - hov), (196, 196 - hov), (256, 170 - hov), (316, 196 - hov), (332, 280 - hov),
                                             (300, 360 - hov), (212, 360 - hov)], 0.4), armor, lw=LW + 2, hi_size=0.6)
    paint(ctx, lambda c: poly_path(c, [(256, 220 - hov), (286, 268 - hov), (256, 318 - hov), (226, 268 - hov)]), rift, lw=LW, hi_size=0.8)
    glow(ctx, 256, 268 - hov, 60, rift, 0.7)
    # floating hands
    for side in (-1, 1):
        paint(ctx, lambda c, side=side: smooth_closed(c, [(256 + side * 150, 300 - hov * 2), (256 + side * 190, 290 - hov * 2),
                                                           (256 + side * 200, 330 - hov * 2), (256 + side * 170, 350 - hov * 2)], 0.5), armor, lw=LW + 1)
        glow(ctx, 256 + side * 180, 320 - hov * 2, 40, rift, 0.6)
    # head + shard crown
    paint(ctx, lambda c: smooth_closed(c, [(206, 150 - hov), (212, 96 - hov), (256, 76 - hov), (300, 96 - hov), (306, 150 - hov), (256, 168 - hov)], 0.5),
          armor, lw=LW + 2, hi_size=0.6)
    for i in range(5):
        x = 210 + i * 23
        h = 70 if i == 2 else (52 if i in (1, 3) else 36)
        paint(ctx, lambda c, x=x, h=h: poly_path(c, [(x - 10, 92 - hov), (x, 92 - hov - h), (x + 10, 92 - hov)]), rift, lw=4.5, hi_size=0.8)
    glow(ctx, 256, 124 - hov, 30, rift, 1.0)
    flat(ctx, lambda c: ellipse_path(c, 256, 124 - hov, 20, 13), (1, 1, 1))
    flat(ctx, lambda c: ellipse_path(c, 256, 124 - hov, 8, 11), hex2rgb("#2a0a30"))


DRAWERS = {
    "grunt": grunt, "runner": runner, "swarmling": swarmling, "shieldbearer": shieldbearer, "hexcaster": hexcaster,
    "sapper": sapper, "warded": warded, "juggernaut": juggernaut, "summoner": summoner, "banner": banner,
    "mimic": mimic, "ravager": ravager, "riftling": riftling, "siegebreaker_golem": golem, "rift_warden": warden,
}
