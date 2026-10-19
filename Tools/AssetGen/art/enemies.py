"""Procedural rift-monster sprites. Each archetype has its own silhouette and colour family so threats
read at a glance: round imps (grunt), long hounds (runner), tiny blobs (swarm), shield walls,
hooded casters with floating orbs, bomb goblins, warded golems, spiked brutes, banner bearers...

Two walk frames (a/b). Normal canvas 256 (feet at y=236), bosses 512 (feet at y=486).
"""
import math
import cairo
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


BIG_IDS = ("siegebreaker_golem", "rift_warden", "ignaroth", "seraphyne", "gravemaw")


def enemy_sprite(eid, frame="a"):
    big = eid in BIG_IDS
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


def mana_leech(ctx, bob, frame):
    body = hex2rgb("#4a3a8a")
    belly = hex2rgb("#8a7ad0")
    siphon = hex2rgb("#ff4ad8")
    mana = hex2rgb("#6ad8ff")
    hov = 8 if frame == "b" else 0
    wig = 6 if frame == "b" else -6
    flat(ctx, lambda c: ellipse_path(c, 132, 234, 54, 8), (0, 0, 0), 0.25)
    glow(ctx, 70, 148 - hov, 60, siphon, 0.45)
    # mana motes being pulled into the mouth
    for i, (x, y) in enumerate(((22, 96), (14, 150), (30, 206))):
        glow(ctx, x, y - hov + (wig if i == 1 else 0), 12, mana, 0.8)
        sparkle(ctx, x, y - hov + (wig if i == 1 else 0), 6, hex2rgb("#e0f8ff"))
    # tail fins
    paint(ctx, lambda c: smooth_closed(c, [(196, 196 - hov), (236, 186 - hov), (244, 214 - hov), (226, 210 - hov), (210, 220 - hov)], 0.5),
          shade(body, 0.15), lw=5, hi=False)
    # hunched segmented body
    paint(ctx, lambda c: smooth_closed(c, [(66, 168 - hov), (78, 112 - hov), (118, 78 - hov), (164, 82 - hov), (196, 120 - hov),
                                             (214, 176 - hov), (204, 212 - hov), (168, 206 - hov), (140, 172 - hov), (110, 186 - hov),
                                             (82, 190 - hov)], 0.5), body, lw=LW)
    flat(ctx, lambda c: smooth_closed(c, [(150, 176 - hov), (178, 140 - hov), (200, 180 - hov), (190, 204 - hov), (166, 200 - hov)], 0.5),
         belly, 0.6)
    for (x1, y1, x2, y2) in ((112, 86, 104, 116), (142, 80, 138, 112), (170, 92, 160, 120), (192, 122, 176, 140)):
        stroke(ctx, lambda c, a=(x1, y1, x2, y2): (c.move_to(a[0], a[1] - hov), c.line_to(a[2], a[3] - hov)), shade(body, 0.4), 4)
    # glowing rune spots
    for (x, y) in ((126, 108), (156, 112), (182, 150)):
        glow(ctx, x, y - hov, 10, siphon, 0.7)
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y - hov, 4, 4), light(siphon, 0.5))
    # siphon tendrils reaching outward
    for (pts) in (((76, 140), (50, 120 + wig), (30, 98)), ((70, 156), (44, 154 - wig), (18, 150 + wig)),
                  ((78, 172), (56, 192 + wig), (34, 204))):
        outlined_line(ctx, [(x, y - hov) for x, y in pts], siphon, 6, 12)
        glow(ctx, pts[-1][0], pts[-1][1] - hov, 9, siphon, 0.9)
    # sucker mouth
    glow(ctx, 76, 156 - hov, 30, siphon, 0.8)
    paint(ctx, lambda c: ellipse_path(c, 80, 156 - hov, 24, 28), shade(body, 0.1), lw=LW, hi=False)
    paint(ctx, lambda c: ellipse_path(c, 78, 156 - hov, 15, 18), siphon, lw=3.5, hi=False, shade_amt=0)
    flat(ctx, lambda c: ellipse_path(c, 77, 156 - hov, 8, 10), hex2rgb("#3a0a30"))
    for k in range(6):
        a = k * math.pi / 3
        flat(ctx, lambda c, a=a: poly_path(c, [(78 + math.cos(a) * 15, 156 - hov + math.sin(a) * 18),
                                               (78 + math.cos(a + 0.25) * 9, 156 - hov + math.sin(a + 0.25) * 11),
                                               (78 + math.cos(a - 0.25) * 9, 156 - hov + math.sin(a - 0.25) * 11)]), (1, 1, 1))
    # beady eyes on the hunch
    for (x, y) in ((100, 112), (114, 102)):
        paint(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y - hov, 7, 6), hex2rgb("#fff0a0"), lw=3, hi=False, shade_amt=0)
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x - 1, y - hov + 1, 3, 3.5), INK)


def crystal_parasite(ctx, bob, frame):
    body = hex2rgb("#3a1f5a")
    leg = hex2rgb("#2a1640")
    crys = hex2rgb("#5ae8ff")
    st = 8 if frame == "b" else -8
    flat(ctx, lambda c: ellipse_path(c, 128, 234, 58, 7), (0, 0, 0), 0.25)
    # many thin legs (three per side, alternating step)
    for i, (hx, fx) in enumerate(((100, 66), (122, 104), (146, 150), (164, 190), (112, 84), (154, 176))):
        s = st if i % 2 == 0 else -st
        outlined_line(ctx, [(hx, 196 + bob), ((hx + fx) / 2 + s * 0.5, 170 + bob), (fx + s, 234)], leg, 4, 9)
    # crystal shards on the back
    shards = [((104, 176), (96, 132), (118, 170)), ((116, 170), (126, 112), (140, 168)), ((138, 170), (160, 128), (156, 178)),
              ((152, 180), (180, 156), (166, 188))]
    for tri in shards:
        paint(ctx, lambda c, tri=tri: poly_path(c, [(x, y + bob) for x, y in tri]), crys, lw=3.5, hi_size=0.7)
    glow(ctx, 128, 140 + bob, 22, crys, 0.5)
    sparkle(ctx, 124, 124 + bob, 7)
    # carapace
    paint(ctx, lambda c: smooth_closed(c, [(84, 200 + bob), (96, 176 + bob), (130, 166 + bob), (168, 176 + bob), (186, 198 + bob),
                                             (164, 216 + bob), (104, 216 + bob)], 0.5), body, lw=5)
    stroke(ctx, lambda c: smooth_open(c, [(110, 184 + bob), (134, 178 + bob), (160, 186 + bob)]), light(body, 0.3), 3)
    # head with mandibles (latching front)
    for s in (-1, 1):
        paint(ctx, lambda c, s=s: smooth_closed(c, [(74, 200 + bob + s * 4), (54, 200 + bob + s * 12), (50, 200 + bob + s * 4),
                                                     (64, 200 + bob)], 0.4), hex2rgb("#c8b8e8"), lw=3, hi=False)
    paint(ctx, lambda c: ellipse_path(c, 80, 200 + bob, 16, 13), shade(body, 0.1), lw=4.5, hi=False)
    for (x, y) in ((76, 194), (86, 196), (80, 204)):
        glow(ctx, x, y + bob, 6, crys, 0.9)
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y + bob, 2.6, 2.6), light(crys, 0.6))


def ash_imp(ctx, bob, frame):
    body = hex2rgb("#2a2426")
    ember = hex2rgb("#ff7a1a")
    hot = hex2rgb("#ffd24a")
    fl = 8 if frame == "b" else 0
    glow(ctx, 128, 150 + bob, 70, ember, 0.35)
    feet(ctx, 128, 236, 16, 11, body, frame)
    # head flame
    paint(ctx, lambda c: smooth_closed(c, [(100, 150 + bob), (98, 112 + bob - fl), (112, 120 + bob), (118, 80 + bob - fl), (134, 108 + bob),
                                             (146, 70 + bob - fl * 0.5), (152, 116 + bob), (160, 104 + bob - fl), (158, 150 + bob)], 0.45),
          ember, lw=4.5, hi=False, shade_amt=0)
    flat(ctx, lambda c: smooth_closed(c, [(112, 148 + bob), (118, 116 + bob - fl * 0.5), (130, 128 + bob), (144, 100 + bob - fl * 0.5),
                                            (146, 148 + bob)], 0.5), hot)
    # tiny arms
    for s in (-1, 1):
        outlined_line(ctx, [(128 + s * 26, 186 + bob), (128 + s * 42, 196 + bob - (fl if s > 0 else 0)), (128 + s * 46, 182 + bob)], body, 7, 13)
    # charcoal body
    paint(ctx, lambda c: smooth_closed(c, [(94, 196 + bob), (98, 152 + bob), (128, 136 + bob), (158, 152 + bob), (162, 196 + bob),
                                             (146, 226 + bob), (110, 226 + bob)], 0.55), body, lw=5)
    for s in (-1, 1):
        paint(ctx, lambda c, s=s: poly_path(c, [(128 + s * 18, 146 + bob), (128 + s * 34, 124 + bob), (128 + s * 28, 152 + bob)]),
              hex2rgb("#4a3a3a"), lw=3.5, hi=False)
    # glowing ember cracks
    for pts in (((108, 196), (118, 206), (112, 218)), ((146, 190), (138, 204), (150, 214)), ((126, 210), (132, 222))):
        stroke(ctx, lambda c, pts=pts: smooth_open(c, [(x, y + bob) for x, y in pts]), ember, 4)
        stroke(ctx, lambda c, pts=pts: smooth_open(c, [(x, y + bob) for x, y in pts]), hot, 1.6)
    angry_eyes(ctx, 128, 172 + bob, 12, 8, color=hot)
    stroke(ctx, lambda c: smooth_open(c, [(116, 192 + bob), (128, 198 + bob), (140, 192 + bob)]), ember, 3)
    sparkle(ctx, 170, 100 + bob - fl, 5, hot)
    sparkle(ctx, 88, 118 + bob + fl * 0.5, 4, hot)


def ignaroth(ctx, bob, frame):
    rock = hex2rgb("#3e2c2a")
    lava = hex2rgb("#ff7a1a")
    hot = hex2rgb("#ffd24a")
    b = bob * 2
    lift = 14 if frame == "b" else 0

    def cracks(pts_list, w=6):
        for pts in pts_list:
            stroke(ctx, lambda c, pts=pts: smooth_open(c, [(x, y + b) for x, y in pts]), lava, w)
            stroke(ctx, lambda c, pts=pts: smooth_open(c, [(x, y + b) for x, y in pts]), hot, w * 0.4)

    glow(ctx, 256, 250, 240, lava, 0.28)
    flat(ctx, lambda c: ellipse_path(c, 256, 488, 150, 18), (0, 0, 0), 0.25)
    # legs (wide stance)
    step = 8 if frame == "b" else -8
    for s in (-1, 1):
        paint(ctx, lambda c, s=s: smooth_closed(c, [(256 + s * 30, 340 + b), (256 + s * 92, 350 + b), (256 + s * 100, 470 + step * s),
                                                     (256 + s * 46, 470 - step * s * 0)], 0.3), shade(rock, 0.1), lw=LW + 2)
        paint(ctx, lambda c, s=s: ellipse_path(c, 256 + s * 76, 470 + min(0, step * s), 50, 22), shade(rock, 0.2), lw=LW + 1, hi=False)
    cracks([((210, 380), (196, 420), (206, 452)), ((300, 384), (318, 420), (310, 450))], 5)
    # back arms (upper arm behind fists)
    for s in (-1, 1):
        outlined_line(ctx, [(256 + s * 110, 190 + b), (256 + s * 160, 250 + b - lift * (s > 0)), (256 + s * 176, 300 + b - lift * (s > 0))],
                      rock, 46, 60)
    # V-shaped torso
    paint(ctx, lambda c: smooth_closed(c, [(118, 186 + b), (160, 150 + b), (256, 136 + b), (352, 150 + b), (394, 186 + b),
                                             (346, 260 + b), (310, 360 + b), (256, 372 + b), (202, 360 + b), (166, 260 + b)], 0.35), rock, lw=LW + 3)
    cracks([((256, 200), (240, 240), (262, 280), (248, 330)), ((180, 210), (210, 236), (220, 270)), ((332, 210), (304, 240), (296, 280)),
            ((262, 280), (290, 300)), ((248, 330), (222, 344))], 7)
    # molten heart
    glow(ctx, 256, 262 + b, 70, lava, 0.85)
    paint(ctx, lambda c: smooth_closed(c, [(256, 236 + b), (280, 262 + b), (256, 294 + b), (232, 262 + b)], 0.4), hot, lw=LW, hi_size=0.7)
    # spiked pauldrons
    for s in (-1, 1):
        for k in range(3):
            paint(ctx, lambda c, s=s, k=k: poly_path(c, [(256 + s * (100 + k * 22), 160 + b), (256 + s * (110 + k * 30), 96 + b + k * 16),
                                                          (256 + s * (122 + k * 22), 162 + b)]), hex2rgb("#2a1c1c"), lw=4.5, hi=False)
        paint(ctx, lambda c, s=s: ellipse_path(c, 256 + s * 132, 184 + b, 58, 44, s * 0.25), shade(rock, 0.05), lw=LW + 2, hi_size=0.6)
        cracks([((256 + s * 112, 170), (256 + s * 140, 186), (256 + s * 158, 176))], 5)
    # magma fists
    for s in (-1, 1):
        fy = 324 + b - (lift if s > 0 else 0)
        glow(ctx, 256 + s * 180, fy, 62, lava, 0.75)
        paint(ctx, lambda c, s=s, fy=fy: smooth_closed(c, [(256 + s * 140, fy - 30), (256 + s * 186, fy - 50), (256 + s * 220, fy - 24),
                                                           (256 + s * 222, fy + 24), (256 + s * 190, fy + 46), (256 + s * 144, fy + 26)], 0.5),
              hex2rgb("#e0501a"), lw=LW + 2, hi_size=0.6)
        for k in range(3):
            stroke(ctx, lambda c, s=s, fy=fy, k=k: (c.move_to(256 + s * (160 + k * 20), fy - 34 + k * 4),
                                                   c.line_to(256 + s * (162 + k * 20), fy - 6)), INK, 4)
        flat(ctx, lambda c, s=s, fy=fy: ellipse_path(c, 256 + s * 186, fy + 12, 22, 16), hot, 0.85)
    # head
    paint(ctx, lambda c: smooth_closed(c, [(212, 160 + b), (214, 110 + b), (256, 92 + b), (298, 110 + b), (300, 160 + b), (256, 180 + b)], 0.45),
          shade(rock, 0.1), lw=LW + 2, hi_size=0.5)
    # crown of horns and flame
    for i, (dx, h) in enumerate(((-44, 46), (-22, 64), (0, 84), (22, 64), (44, 46))):
        glow(ctx, 256 + dx, 104 + b - h * 0.6, 18, lava, 0.8)
        paint(ctx, lambda c, dx=dx, h=h: smooth_closed(c, [(256 + dx - 10, 106 + b), (256 + dx - 4 + dx * 0.25, 106 + b - h * 0.55),
                                                           (256 + dx + dx * 0.4, 106 + b - h), (256 + dx + 10, 106 + b)], 0.3),
              lava if i % 2 else hex2rgb("#2a1c1c"), lw=4.5, hi=i % 2 == 1, hi_size=0.6)
    flat(ctx, lambda c: smooth_closed(c, [(240, 104 + b), (250, 70 + b - lift * 0.5), (262, 86 + b), (272, 104 + b)], 0.5), hot, 0.9)
    for s in (-1, 1):
        glow(ctx, 256 + s * 20, 134 + b, 18, hot, 0.95)
        paint(ctx, lambda c, s=s: poly_path(c, [(256 + s * 8, 128 + b), (256 + s * 34, 122 + b), (256 + s * 28, 140 + b), (256 + s * 10, 138 + b)]),
              hot, lw=3.5, hi=False, shade_amt=0)
    # molten jaw
    paint(ctx, lambda c: smooth_closed(c, [(232, 154 + b), (280, 154 + b), (272, 168 + b), (240, 168 + b)], 0.4), lava, lw=3.5, hi=False, shade_amt=0)
    for k in range(4):
        flat(ctx, lambda c, k=k: poly_path(c, [(238 + k * 12, 154 + b), (246 + k * 12, 154 + b), (242 + k * 12, 162 + b)]), hex2rgb("#fff0c8"))


# ---------------------------------------------------------------------------- expansion roster (factions & bosses)

def _rivets(ctx, pts, r=3.6, col=None):
    col = col or hex2rgb("#c8ccd8")
    for (x, y) in pts:
        paint(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, r, r), col, lw=2, hi=False, shade_amt=0.25)


def _bolt(ctx, pts, col, w=4.0, glow_r=0.0):
    if glow_r:
        mx = sum(p[0] for p in pts) / len(pts)
        my = sum(p[1] for p in pts) / len(pts)
        glow(ctx, mx, my, glow_r, col, 0.5)
    for c_, lw in ((INK, w + 5), (col, w), (light(col, 0.7), w * 0.35)):
        stroke(ctx, lambda c, pts=pts: (c.move_to(*pts[0]), [c.line_to(*p) for p in pts[1:]]), c_, lw)


def _snowflake(ctx, x, y, r, col=(1, 1, 1), alpha=0.9):
    for k in range(3):
        a = k * math.pi / 3
        stroke(ctx, lambda c, a=a: (c.move_to(x - math.cos(a) * r, y - math.sin(a) * r), c.line_to(x + math.cos(a) * r, y + math.sin(a) * r)),
               col, max(1.5, r * 0.28), alpha)


def _chain(ctx, pts, col, link=11.0, glow_col=None):
    """Chain of alternating links sampled along a polyline."""
    samples = []
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L / (link * 1.25)))
        for k in range(n):
            t = k / n
            samples.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, math.atan2(y1 - y0, x1 - x0)))
    samples.append((pts[-1][0], pts[-1][1], samples[-1][2]))
    if glow_col:
        for (x, y, a) in samples[::2]:
            glow(ctx, x, y, link * 1.8, glow_col, 0.35)
    for i, (x, y, a) in enumerate(samples):
        ry = link * (0.45 if i % 2 == 0 else 0.18)
        stroke(ctx, lambda c, x=x, y=y, a=a, ry=ry: ellipse_path(c, x, y, link * 0.75, ry, a), INK, 6.5)
        stroke(ctx, lambda c, x=x, y=y, a=a, ry=ry: ellipse_path(c, x, y, link * 0.75, ry, a), col, 3)


def _wing(ctx, root, tip, width, col, tipcol, n=5, side=1, lw=LW):
    """Feathered wing from root to tip; feathers fan toward the normal side, tips in tipcol."""
    rx, ry = root
    tx, ty = tip
    dx, dy = tx - rx, ty - ry
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy * side, ux * side

    def shape(wf):
        pts = [(rx - nx * width * 0.25, ry - ny * width * 0.25),
               (rx + dx * 0.5 - nx * width * 0.42, ry + dy * 0.5 - ny * width * 0.42),
               (tx, ty)]
        for i in range(n):
            t = 1.0 - (i + 0.5) / n
            bx, by = rx + dx * t, ry + dy * t
            f = width * wf * (0.55 + 0.45 * (1 - t))
            pts.append((bx + nx * f - ux * width * 0.12, by + ny * f - uy * width * 0.12))
            t2 = 1.0 - (i + 1.0) / n
            pts.append((rx + dx * t2 + nx * f * 0.45, ry + dy * t2 + ny * f * 0.45))
        pts.append((rx + nx * width * 0.3, ry + ny * width * 0.3))
        return pts
    outer, inner = shape(1.0), shape(0.68)
    paint(ctx, lambda c: smooth_closed(c, outer, 0.25), tipcol, lw=lw, hi=False, shade_amt=0.2)
    paint(ctx, lambda c: smooth_closed(c, inner, 0.25), col, lw=lw * 0.6, hi_size=0.6)


def goblin_sprinter(ctx, bob, frame):
    skin = hex2rgb("#6ab04a")
    rust = hex2rgb("#b0602e")
    iron = hex2rgb("#7a7c8a")
    cloth = hex2rgb("#5a4632")
    b = frame == "b"
    flat(ctx, lambda c: ellipse_path(c, 124, 234, 54, 7), (0, 0, 0), 0.25)
    # speed lines streaming behind (it runs left)
    for i, (y, x, l) in enumerate(((96, 186, 44), (124, 200, 50), (152, 194, 40), (182, 206, 34))):
        stroke(ctx, lambda c, y=y, x=x, l=l: (c.move_to(x + (6 if b else 0), y), c.line_to(x + l + (6 if b else 0), y)), hex2rgb("#eaf6d8"), 5, 0.8)
    # legs: long stride, swapped per frame
    if b:
        back, front = [(140, 176 + bob), (168, 196 + bob), (176, 230)], [(122, 178 + bob), (104, 200 + bob), (78, 214)]
    else:
        back, front = [(140, 176 + bob), (170, 184 + bob), (196, 206)], [(122, 178 + bob), (98, 196 + bob), (82, 230)]
    outlined_line(ctx, back, shade(skin, 0.35), 11, 18)
    paint(ctx, lambda c: ellipse_path(c, back[-1][0] + 4, back[-1][1] + 2, 14, 7, 0.3), hex2rgb("#4a3a2e"), lw=4, hi=False)
    # back arm (swinging back)
    arm_b = [(116, 124 + bob), (144, 136 + bob), (160, 120 + bob)] if not b else [(116, 124 + bob), (138, 148 + bob), (152, 162 + bob)]
    outlined_line(ctx, arm_b, shade(skin, 0.3), 9, 16)
    # leaning torso
    paint(ctx, lambda c: smooth_closed(c, [(110, 190 + bob), (146, 182 + bob), (140, 146 + bob), (118, 112 + bob), (92, 108 + bob),
                                             (90, 140 + bob)], 0.5), skin, lw=LW)
    # ragged tunic + rusty belt
    paint(ctx, lambda c: poly_path(c, [(98, 150 + bob), (140, 150 + bob), (148, 186 + bob), (136, 180 + bob), (128, 192 + bob),
                                         (118, 182 + bob), (106, 194 + bob), (100, 178 + bob)]), cloth, lw=4.5, hi=False)
    flat(ctx, lambda c: rrect_path(c, 98, 148 + bob, 44, 9, 3), rust)
    stroke(ctx, lambda c: rrect_path(c, 98, 148 + bob, 44, 9, 3), INK, 3)
    # rusty gear pauldron on the back shoulder
    paint(ctx, lambda c: star_path(c, 132, 120 + bob, 24, 18, 9, rot=0.2 if b else 0), rust, lw=4, hi_size=0.6)
    flat(ctx, lambda c: ellipse_path(c, 132, 120 + bob, 7, 7), INK)
    stroke(ctx, lambda c: ellipse_path(c, 132, 120 + bob, 13, 13), shade(rust, 0.35), 3)
    outlined_line(ctx, front, skin, 11, 18)
    paint(ctx, lambda c: ellipse_path(c, front[-1][0] - 4, front[-1][1] + 1, 15, 7, -0.2), hex2rgb("#4a3a2e"), lw=4, hi=False)
    # head (pointed nose forward-left), long swept-back ears
    paint(ctx, lambda c: poly_path(c, [(98, 88 + bob), (150, 62 + bob), (108, 104 + bob)]), skin, lw=4.5, hi=False)
    flat(ctx, lambda c: poly_path(c, [(106, 90 + bob), (138, 72 + bob), (110, 98 + bob)]), hex2rgb("#e89a8a"), 0.8)
    paint(ctx, lambda c: smooth_closed(c, [(60, 104 + bob), (40, 112 + bob), (58, 92 + bob), (72, 74 + bob), (100, 72 + bob),
                                             (110, 96 + bob), (98, 122 + bob), (72, 124 + bob)], 0.45), skin, lw=LW)
    # dented iron cap with rivets
    paint(ctx, lambda c: (c.arc(88, 84 + bob, 22, math.pi * 1.05, math.pi * 1.98), c.close_path()), iron, lw=4.5, hi_size=0.7)
    flat(ctx, lambda c: ellipse_path(c, 98, 72 + bob, 6, 4), rust, 0.8)
    _rivets(ctx, [(72, 80 + bob), (88, 69 + bob), (104, 78 + bob)], 2.6)
    angry_eyes(ctx, 70, 96 + bob, 0, 8, single=True, color=hex2rgb("#fff07a"))
    stroke(ctx, lambda c: (c.move_to(60, 84 + bob), c.line_to(82, 90 + bob)), INK, 4)
    stroke(ctx, lambda c: smooth_open(c, [(54, 112 + bob), (66, 116 + bob), (80, 112 + bob)]), INK, 3.5)
    flat(ctx, lambda c: poly_path(c, [(64, 114 + bob), (70, 115 + bob), (67, 121 + bob)]), (1, 1, 1))
    # front arm pumping forward
    arm_f = [(100, 128 + bob), (78, 144 + bob), (62, 134 + bob)] if not b else [(100, 128 + bob), (84, 150 + bob), (88, 168 + bob)]
    outlined_line(ctx, arm_f, skin, 10, 17)
    paint(ctx, lambda c: ellipse_path(c, arm_f[-1][0], arm_f[-1][1], 8, 8), iron, lw=3.5, hi=False)


def ironback_golem(ctx, bob, frame):
    body = hex2rgb("#7c726a")
    plate = hex2rgb("#5c6476")
    rust = hex2rgb("#b0602e")
    eye = hex2rgb("#ffb23a")
    flat(ctx, lambda c: ellipse_path(c, 130, 236, 96, 9), (0, 0, 0), 0.25)
    feet(ctx, 138, 238, 52, 22, body, frame)
    # squat body
    paint(ctx, lambda c: smooth_closed(c, [(36, 200 + bob), (48, 150 + bob), (96, 118 + bob), (172, 112 + bob), (224, 146 + bob),
                                             (232, 202 + bob), (206, 226 + bob), (60, 226 + bob)], 0.45), body, lw=LW)
    # thick riveted back-plates, overlapping from the rear forward
    for k, x in enumerate((206, 172, 138, 104)):
        top = 100 + abs(k - 1.5) * 8
        pl = [(x - 30, 196 + bob), (x - 32, 140 + bob), (x - 18, top + bob), (x + 18, top - 4 + bob), (x + 32, 138 + bob), (x + 28, 196 + bob)]
        col = mix(plate, rust, 0.18 if k % 2 else 0.0)
        paint(ctx, lambda c, pl=pl: smooth_closed(c, pl, 0.3), col, lw=LW, hi_size=0.55)
        stroke(ctx, lambda c, x=x, top=top: smooth_open(c, [(x - 22, 140 + bob), (x, top + 12 + bob), (x + 22, 136 + bob)]), light(col, 0.35), 3, 0.8)
        _rivets(ctx, [(x - 20, 186 + bob), (x, 190 + bob), (x + 18, 184 + bob), (x - 2, top + 22 + bob)], 3.6)
    flat(ctx, lambda c: ellipse_path(c, 170, 160 + bob, 9, 5, 0.4), rust, 0.7)
    # front head jutting under the first plate (faces left)
    paint(ctx, lambda c: smooth_closed(c, [(28, 190 + bob), (34, 150 + bob), (66, 134 + bob), (94, 148 + bob), (96, 196 + bob),
                                             (62, 208 + bob)], 0.4), light(body, 0.08), lw=LW)
    paint(ctx, lambda c: smooth_closed(c, [(34, 150 + bob), (60, 128 + bob), (92, 136 + bob), (88, 152 + bob), (52, 156 + bob)], 0.3),
          plate, lw=4.5, hi_size=0.6)
    _rivets(ctx, [(48, 146 + bob), (78, 140 + bob)], 2.8)
    glow(ctx, 56, 166 + bob, 22, eye, 0.8)
    flat(ctx, lambda c: rrect_path(c, 40, 162 + bob, 34, 8, 4), hex2rgb("#fff0a0"))
    stroke(ctx, lambda c: smooth_open(c, [(40, 188 + bob), (56, 194 + bob), (74, 190 + bob)]), INK, 4)
    # stubby fist planted forward
    paint(ctx, lambda c: ellipse_path(c, 50, 216 + bob * 0.5, 24, 16), shade(body, 0.1), lw=LW, hi_size=0.6)
    for k in range(3):
        stroke(ctx, lambda c, k=k: (c.move_to(36 + k * 12, 206 + bob * 0.5), c.line_to(38 + k * 12, 222 + bob * 0.5)), INK, 3)


def spirit_splitter(ctx, bob, frame):
    cyan = hex2rgb("#6af0ff")
    vio = hex2rgb("#b07aff")
    fl = 6 if frame == "b" else 0
    g = 9 if frame == "b" else 5
    flat(ctx, lambda c: ellipse_path(c, 128, 234, 40, 6), (0, 0, 0), 0.2)
    glow(ctx, 128, 150 - fl, 96, mix(cyan, vio, 0.5), 0.35)
    body = [(84, 196), (78, 140), (94, 96), (128, 76), (162, 96), (178, 140), (172, 196), (158, 222), (142, 204), (128, 228),
            (114, 204), (98, 222)]
    crack = [(128, 60), (120, 96), (136, 120), (120, 146), (136, 172), (122, 200), (132, 240)]
    body = [(x, y - fl) for x, y in body]
    crack = [(x, y - fl) for x, y in crack]
    for side, col in ((-1, cyan), (1, vio)):
        ctx.save()
        ctx.translate(side * g, 0)
        ctx.new_path()
        far = -40 if side < 0 else 296
        poly_path(ctx, crack + [(far, 240), (far, 40)])
        ctx.clip()
        paint(ctx, lambda c: smooth_closed(c, body, 0.5), col, lw=LW, alpha=0.82, hi_size=0.6)
        stroke(ctx, lambda c: (c.move_to(*crack[0]), [c.line_to(*p) for p in crack[1:]]), INK, 9, 0.9)
        ctx.restore()
    # glowing rift between the halves
    glow(ctx, 128, 150 - fl, 40, (1, 1, 1), 0.45)
    stroke(ctx, lambda c: (c.move_to(*crack[0]), [c.line_to(*p) for p in crack[1:]]), (0.95, 0.9, 1.0), 3, 0.9)
    # one eye per half, opposite moods
    for x, col in ((104 - g, hex2rgb("#e8ffff")), (152 + g, hex2rgb("#f0e0ff"))):
        glow(ctx, x, 128 - fl, 14, col, 0.8)
        paint(ctx, lambda c, x=x, col=col: ellipse_path(c, x, 128 - fl, 9, 11), col, lw=3, hi=False, shade_amt=0)
        flat(ctx, lambda c, x=x: ellipse_path(c, x, 130 - fl, 4, 6), INK)
    stroke(ctx, lambda c: smooth_open(c, [(96 - g, 162 - fl), (108 - g, 156 - fl), (118 - g, 162 - fl)]), INK, 3.5)
    stroke(ctx, lambda c: smooth_open(c, [(138 + g, 160 - fl), (150 + g, 166 - fl), (160 + g, 158 - fl)]), INK, 3.5)
    sparkle(ctx, 128, 64 - fl, 9, (1, 1, 1))


def spirit_wisp(ctx, bob, frame):
    cyan = hex2rgb("#6af0ff")
    vio = hex2rgb("#b07aff")
    fl = 7 if frame == "b" else 0
    flat(ctx, lambda c: ellipse_path(c, 128, 234, 22, 4), (0, 0, 0), 0.2)
    ctx.save()
    ctx.translate(128, 230)
    ctx.scale(1.35, 1.35)
    ctx.translate(-128, -230)
    glow(ctx, 128, 180 - fl * 0.5, 54, cyan, 0.5)
    pts = [(106, 206), (102, 180), (112, 158), (118, 134 - fl), (128, 152), (138, 126 + fl * 0.6), (146, 156), (154, 182), (148, 206),
           (128, 216)]
    paint(ctx, lambda c: smooth_closed(c, pts, 0.5), cyan, lw=5, alpha=0.88, hi_size=0.6)
    flat(ctx, lambda c: smooth_closed(c, [(116, 204), (114, 184), (124, 168), (132, 180), (140, 172), (142, 196), (130, 208)], 0.5), vio, 0.65)
    # jagged torn edge (it is half of a splitter)
    stroke(ctx, lambda c: (c.move_to(150, 166), c.line_to(144, 178), c.line_to(152, 190), c.line_to(146, 204)), (1, 1, 1), 2.5, 0.85)
    angry_eyes(ctx, 124, 186, 0, 7, single=True, color=hex2rgb("#f0ffff"))
    sparkle(ctx, 168, 150 - fl, 6, light(cyan, 0.6))
    sparkle(ctx, 90, 168 + fl, 4.5, light(vio, 0.6))
    flat(ctx, lambda c: ellipse_path(c, 160, 220 - fl, 3, 3), light(cyan, 0.5), 0.9)
    ctx.restore()


def flame_devourer(ctx, bob, frame):
    skin = hex2rgb("#3a3234")
    lava = hex2rgb("#ff6a1a")
    hot = hex2rgb("#ffd24a")
    maw = hex2rgb("#4a0a14")
    open_ = 6 if frame == "b" else 0
    flat(ctx, lambda c: ellipse_path(c, 136, 234, 92, 9), (0, 0, 0), 0.28)
    glow(ctx, 48, 140, 70, lava, 0.45)
    feet(ctx, 176, 238, 30, 18, skin, frame)
    # hulking hunched body
    paint(ctx, lambda c: smooth_closed(c, [(58, 176 + bob), (68, 112 + bob), (118, 72 + bob), (186, 70 + bob), (232, 112 + bob),
                                             (240, 178 + bob), (212, 214 + bob), (90, 214 + bob)], 0.45), skin, lw=LW)
    # back ridge of smouldering spines
    for k in range(5):
        x = 122 + k * 24
        y = 76 + abs(k - 1.5) * 7
        paint(ctx, lambda c, x=x, y=y: poly_path(c, [(x - 10, y + 6 + bob), (x + 6, y - 22 + bob), (x + 12, y + 8 + bob)]), hex2rgb("#2a2224"),
              lw=4, hi=False)
        glow(ctx, x + 6, y - 22 + bob, 8, lava, 0.7)
    # glowing belly: swallowed fire shining through cracks
    glow(ctx, 162, 168 + bob, 52, lava, 0.75)
    for pts in (((140, 150), (156, 166), (148, 188)), ((176, 140), (170, 164), (188, 182)), ((156, 166), (176, 172))):
        stroke(ctx, lambda c, pts=pts: smooth_open(c, [(x, y + bob) for x, y in pts]), lava, 5)
        stroke(ctx, lambda c, pts=pts: smooth_open(c, [(x, y + bob) for x, y in pts]), hot, 2)
    # front legs
    for (x, l) in ((84, -4 if frame == "b" else 4), (116, 4 if frame == "b" else -4)):
        outlined_line(ctx, [(x, 190 + bob), (x + l, 230)], shade(skin, 0.2), 18, 26, smooth=False)
        for k in range(3):
            flat(ctx, lambda c, x=x, l=l, k=k: poly_path(c, [(x + l - 12 + k * 7, 228), (x + l - 16 + k * 7, 238), (x + l - 8 + k * 7, 232)]),
                 hex2rgb("#e8dcc8"))
    # huge gaping maw (faces left)
    paint(ctx, lambda c: smooth_closed(c, [(84, 96 + bob), (40, 82 + bob - open_), (14, 104 + bob - open_), (24, 132 + bob),
                                             (14, 168 + bob + open_), (44, 192 + bob + open_), (92, 184 + bob)], 0.4), skin, lw=LW)
    paint(ctx, lambda c: smooth_closed(c, [(84, 110 + bob), (40, 100 + bob - open_), (26, 134 + bob), (40, 172 + bob + open_),
                                             (84, 170 + bob)], 0.45), maw, lw=4.5, hi=False, shade_amt=0)
    glow(ctx, 70, 138 + bob, 36, hot, 0.8)
    # teeth top and bottom
    for k in range(5):
        x = 36 + k * 11
        flat(ctx, lambda c, x=x: poly_path(c, [(x - 5, 102 + bob - open_ * 0.7 + k * 1.2), (x + 5, 104 + bob - open_ * 0.7 + k * 1.2),
                                               (x + 1, 118 + bob - open_ * 0.5)]), hex2rgb("#fff0d8"))
        flat(ctx, lambda c, x=x: poly_path(c, [(x - 5, 170 + bob + open_ * 0.7 - k * 1.2), (x + 5, 168 + bob + open_ * 0.7 - k * 1.2),
                                               (x + 1, 154 + bob + open_ * 0.5)]), hex2rgb("#fff0d8"))
    # flames being sucked into the maw
    for (y, ln, w) in ((122, 40, 12), (140, 52, 16), (158, 38, 11)):
        y2 = y + bob
        paint(ctx, lambda c, y2=y2, ln=ln, w=w: smooth_closed(c, [(70, y2), (70 - ln * 0.5, y2 - w), (4, y2 - w * 0.4 - open_),
                                                                 (24, y2), (6, y2 + w * 0.5 + open_), (70 - ln * 0.5, y2 + w)], 0.4),
              lava, lw=3.5, hi=False, shade_amt=0)
        flat(ctx, lambda c, y2=y2, ln=ln, w=w: smooth_closed(c, [(68, y2), (68 - ln * 0.45, y2 - w * 0.5), (30, y2), (68 - ln * 0.45, y2 + w * 0.5)], 0.4),
             hot)
    # small burning eyes on the brow
    angry_eyes(ctx, 104, 100 + bob, 12, 7, color=hot)
    sparkle(ctx, 18, 116 - open_, 5, hot)
    sparkle(ctx, 10, 160 + open_, 4, hot)


def frost_wraith(ctx, bob, frame):
    cloak = hex2rgb("#bfe4ff")
    deep = hex2rgb("#6aa8e0")
    ice = hex2rgb("#e8faff")
    fl = 8 if frame == "b" else 0
    flat(ctx, lambda c: ellipse_path(c, 128, 234, 34, 5), (0, 0, 0), 0.18)
    glow(ctx, 124, 120 - fl, 90, hex2rgb("#9ad8ff"), 0.35)
    # phasing lower body: fades out, dashed outline
    tail = [(92, 140 - fl), (156, 136 - fl), (172, 174 - fl), (196, 206), (222, 226), (176, 214), (150, 222), (128, 200), (102, 190)]
    grad = cairo.LinearGradient(0, 130 - fl, 0, 230)
    grad.add_color_stop_rgba(0, *cloak, 0.85)
    grad.add_color_stop_rgba(1, *cloak, 0.05)
    ctx.save()
    ctx.new_path()
    smooth_closed(ctx, tail, 0.5)
    ctx.set_source(grad)
    ctx.fill_preserve()
    ctx.set_dash([10, 9])
    ctx.set_source_rgba(*INK, 0.55)
    ctx.set_line_width(4)
    ctx.stroke()
    ctx.restore()
    # frost trail
    for (x, y, r) in ((184, 196, 6), (206, 214, 5), (226, 204, 7), (164, 222, 4), (238, 228, 4)):
        _snowflake(ctx, x, y - (fl if frame == "a" else 0) * 0.3, r, ice, 0.85)
    # hooded upper body
    paint(ctx, lambda c: smooth_closed(c, [(88, 150 - fl), (90, 96 - fl), (114, 56 - fl), (150, 40 - fl), (146, 66 - fl), (166, 100 - fl),
                                             (162, 150 - fl), (126, 160 - fl)], 0.45), cloak, lw=LW, hi_size=0.6)
    paint(ctx, lambda c: smooth_closed(c, [(100, 112 - fl), (106, 82 - fl), (126, 70 - fl), (140, 86 - fl), (138, 116 - fl),
                                             (118, 124 - fl)], 0.5), hex2rgb("#12203a"), lw=4, hi=False, shade_amt=0)
    for x in (112, 128):
        glow(ctx, x, 98 - fl, 12, hex2rgb("#7ff0ff"), 0.9)
        flat(ctx, lambda c, x=x: ellipse_path(c, x, 98 - fl, 4.5, 3), (1, 1, 1))
    for k in range(4):
        x = 96 + k * 20
        flat(ctx, lambda c, x=x: poly_path(c, [(x, 150 - fl), (x + 10, 150 - fl), (x + 5, 166 - fl)]), ice, 0.9)
    # reaching arm with icicle claws (toward the crystal)
    outlined_line(ctx, [(104, 120 - fl), (76, 128 - fl), (56, 118 - fl)], deep, 11, 18)
    for k, a in enumerate((-0.5, 0.0, 0.5)):
        paint(ctx, lambda c, a=a: poly_path(c, [(58, 114 - fl), (58 - math.cos(a) * 26, 118 - fl + math.sin(a) * 26), (60, 124 - fl)]),
              ice, lw=3, hi=False)
    sparkle(ctx, 30, 112 - fl, 7, ice)


def storm_harpy(ctx, bob, frame):
    feather = hex2rgb("#7a8494")
    tipc = hex2rgb("#ffd84a")
    belly = hex2rgb("#c8ccd8")
    up = frame == "a"
    hy = -6 if frame == "b" else 0
    flat(ctx, lambda c: ellipse_path(c, 132, 234, 30, 5), (0, 0, 0), 0.2)
    # back wing
    _wing(ctx, (140, 92 + hy), (232, 22 + hy) if up else (236, 132 + hy), 54, shade(feather, 0.25), shade(tipc, 0.15), side=1)
    # tail feathers
    for k, a in enumerate((0.15, 0.4, 0.65)):
        paint(ctx, lambda c, a=a: smooth_closed(c, [(150, 126 + hy), (150 + math.cos(a) * 58, 126 + hy + math.sin(a) * 58),
                                                     (146 + math.cos(a) * 50, 136 + hy + math.sin(a) * 50)], 0.4), feather if k != 1 else tipc, lw=4, hi=False)
    # talons dangling
    for x in (112, 132):
        outlined_line(ctx, [(x, 138 + hy), (x - 4, 164 + hy)], hex2rgb("#e0b84a"), 6, 12)
        for k in range(3):
            stroke(ctx, lambda c, x=x, k=k: smooth_open(c, [(x - 4, 164 + hy), (x - 12 + k * 7, 172 + hy), (x - 10 + k * 7, 178 + hy)]), INK, 4)
    # front wing (behind the body so the head stays readable)
    _wing(ctx, (128, 96 + hy), (40, 18 + hy) if up else (34, 150 + hy), 58, feather, tipc, side=-1)
    # body
    paint(ctx, lambda c: smooth_closed(c, [(92, 110 + hy), (110, 80 + hy), (146, 82 + hy), (164, 112 + hy), (148, 142 + hy), (106, 144 + hy)], 0.5),
          feather, lw=LW)
    flat(ctx, lambda c: ellipse_path(c, 120, 120 + hy, 20, 16), belly, 0.9)
    for k in range(3):
        stroke(ctx, lambda c, k=k: smooth_open(c, [(108 + k * 8, 112 + hy + k * 6), (114 + k * 8, 118 + hy + k * 6), (120 + k * 8, 112 + hy + k * 6)]),
               shade(belly, 0.3), 2.5)
    # head with hooked beak facing left and lightning crest
    for k, (dx, h) in enumerate(((8, 26), (20, 34), (32, 24))):
        paint(ctx, lambda c, dx=dx, h=h: poly_path(c, [(80 + dx, 62 + hy), (92 + dx + h * 0.3, 62 + hy - h), (96 + dx, 66 + hy)]),
              tipc, lw=3.5, hi=False)
    paint(ctx, lambda c: smooth_closed(c, [(70, 82 + hy), (78, 62 + hy), (102, 54 + hy), (120, 66 + hy), (118, 92 + hy), (94, 100 + hy)], 0.5),
          light(feather, 0.1), lw=LW)
    paint(ctx, lambda c: smooth_closed(c, [(76, 74 + hy), (52, 80 + hy), (46, 92 + hy), (58, 88 + hy), (76, 88 + hy)], 0.4), tipc, lw=4, hi=False)
    angry_eyes(ctx, 90, 74 + hy, 0, 7, single=True, color=hex2rgb("#fff6a0"))
    stroke(ctx, lambda c: (c.move_to(80, 64 + hy), c.line_to(100, 70 + hy)), INK, 4)
    # lightning crackle
    _bolt(ctx, [(200, 50 + hy), (188, 70 + hy), (204, 74 + hy), (190, 98 + hy)] if up else [(204, 160 + hy), (188, 176 + hy), (204, 184 + hy), (192, 206 + hy)],
          tipc, 3.5, 30)
    _bolt(ctx, [(28, 52 + hy), (40, 70 + hy), (26, 76 + hy), (36, 94 + hy)] if up else [(40, 178 + hy), (54, 190 + hy), (40, 196 + hy), (50, 214 + hy)],
          tipc, 3.5, 26)
    sparkle(ctx, 132, 40 + hy, 6, light(tipc, 0.6))


def stone_burrower(ctx, bob, frame):
    rock = hex2rgb("#8a7a6a")
    dirt = hex2rgb("#7a5634")
    drill = hex2rgb("#a8acb8")
    bone = hex2rgb("#ece0c8")
    spin = 7 if frame == "b" else 0
    flat(ctx, lambda c: ellipse_path(c, 140, 234, 96, 8), (0, 0, 0), 0.25)
    # dirt mound it is ploughing through
    paint(ctx, lambda c: smooth_closed(c, [(60, 234), (78, 208), (120, 198), (190, 196), (236, 212), (244, 234)], 0.4), dirt, lw=LW - 1, hi_size=0.5)
    # rocky hunched back with ridges
    paint(ctx, lambda c: smooth_closed(c, [(84, 214 + bob), (88, 160 + bob), (122, 118 + bob), (178, 112 + bob), (222, 146 + bob),
                                             (232, 212 + bob)], 0.45), rock, lw=LW)
    for k, (x, y) in enumerate(((130, 124), (164, 118), (196, 132), (216, 160))):
        paint(ctx, lambda c, x=x, y=y: poly_path(c, [(x - 14, y + 10 + bob), (x - 2, y - 16 + bob), (x + 14, y + 8 + bob)]),
              shade(rock, 0.15), lw=4, hi=False)
    for pts in (((140, 150), (160, 162), (154, 184)), ((188, 156), (196, 180)), ((112, 168), (126, 180))):
        stroke(ctx, lambda c, pts=pts: smooth_open(c, [(x, y + bob) for x, y in pts]), shade(rock, 0.4), 3.5)
    # drill snout pointing left, grooves rotate per frame
    def cone(c):
        poly_path(c, [(96, 150 + bob), (96, 200 + bob), (22, 178 + bob)])
    paint(ctx, cone, drill, lw=LW, hi_size=0.6)
    ctx.save()
    ctx.new_path()
    cone(ctx)
    ctx.clip()
    for k in range(6):
        x = 100 - k * 14 - spin
        stroke(ctx, lambda c, x=x: (c.move_to(x, 140 + bob), c.line_to(x - 16, 210 + bob)), shade(drill, 0.45), 4)
    ctx.restore()
    stroke(ctx, lambda c: poly_path(c, [(96, 150 + bob), (96, 200 + bob), (22, 178 + bob)]), INK, LW)
    paint(ctx, lambda c: ellipse_path(c, 100, 175 + bob, 10, 28), rock, lw=4.5, hi=False)
    # beady eyes above the drill
    for (x, y) in ((112, 146), (126, 140)):
        glow(ctx, x, y + bob, 9, hex2rgb("#ff5a3a"), 0.8)
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y + bob, 4, 4), hex2rgb("#ffd0a0"))
    # big digging claws
    for (cx, cy, rot) in ((112, 214, 0.0), (150, 218, 0.2)):
        paint(ctx, lambda c, cx=cx, cy=cy: ellipse_path(c, cx, cy + bob * 0.5, 20, 14), shade(rock, 0.1), lw=LW - 1, hi=False)
        for k in range(3):
            paint(ctx, lambda c, cx=cx, cy=cy, k=k: smooth_closed(c, [(cx - 8, cy - 8 + k * 7 + bob * 0.5), (cx - 34, cy - 4 + k * 9),
                                                                     (cx - 42, cy + 4 + k * 9), (cx - 10, cy + k * 7 + bob * 0.5)], 0.3),
                  bone, lw=3.5, hi=False)
    # flying dirt clods
    clods = ((40, 214), (30, 138), (60, 124), (234, 190)) if frame == "a" else ((48, 200), (20, 150), (70, 112), (246, 176))
    for (x, y) in clods:
        paint(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 8, 6, 0.5), dirt, lw=3, hi=False)


def void_priest(ctx, bob, frame):
    robe = hex2rgb("#3a1f5a")
    trim = hex2rgb("#b07aff")
    heal = hex2rgb("#8affc8")
    halo = hex2rgb("#d08aff")
    rot = 0.4 if frame == "b" else 0.0
    flat(ctx, lambda c: ellipse_path(c, 128, 234, 52, 7), (0, 0, 0), 0.25)
    # healing void halo behind the head
    glow(ctx, 136, 78 + bob, 70, halo, 0.5)
    stroke(ctx, lambda c: ellipse_path(c, 136, 78 + bob, 44, 44), INK, 10)
    stroke(ctx, lambda c: ellipse_path(c, 136, 78 + bob, 44, 44), halo, 5)
    for k in range(6):
        a = rot + k * math.pi / 3
        x, y = 136 + math.cos(a) * 44, 78 + bob + math.sin(a) * 44
        for (w, h) in ((14, 5), (5, 14)):
            flat(ctx, lambda c, x=x, y=y, w=w, h=h: rrect_path(c, x - w / 2 - 1.5, y - h / 2 - 1.5, w + 3, h + 3, 2), INK)
        for (w, h) in ((14, 5), (5, 14)):
            flat(ctx, lambda c, x=x, y=y, w=w, h=h: rrect_path(c, x - w / 2, y - h / 2, w, h, 1.5), heal)
    # staff (held forward, toward the crystal)
    outlined_line(ctx, [(70, 232), (62, 52 + bob)], hex2rgb("#2a1a3a"), 8, 15, smooth=False)
    paint(ctx, lambda c: (c.arc(62, 42 + bob, 20, math.pi * 0.85, math.pi * 2.15), c.arc_negative(62, 46 + bob, 12, math.pi * 2.1, math.pi * 0.9),
                          c.close_path()), trim, lw=4, hi=False)
    glow(ctx, 62, 42 + bob, 26, halo, 0.8)
    paint(ctx, lambda c: ellipse_path(c, 62, 42 + bob, 10, 10), hex2rgb("#1a0a2a"), lw=3.5, hi=False)
    sparkle(ctx, 58, 38 + bob, 4, light(halo, 0.6))
    # robe
    paint(ctx, lambda c: smooth_closed(c, [(84, 232), (92, 176 + bob), (98, 120 + bob), (136, 94 + bob), (172, 120 + bob), (178, 176 + bob),
                                             (190, 232)], 0.4), robe, lw=LW)
    stroke(ctx, lambda c: (c.move_to(136, 120 + bob), c.line_to(136, 230)), trim, 5)
    for y in (160, 196):
        stroke(ctx, lambda c, y=y: smooth_open(c, [(100, y + bob * 0.5), (136, y + 8 + bob * 0.5), (178, y + bob * 0.5)]), shade(trim, 0.2), 3, 0.8)
    # void eye sigil on the chest
    paint(ctx, lambda c: smooth_closed(c, [(122, 140 + bob), (136, 130 + bob), (150, 140 + bob), (136, 150 + bob)], 0.6), trim, lw=3, hi=False)
    flat(ctx, lambda c: ellipse_path(c, 136, 140 + bob, 4, 5), INK)
    # hood
    paint(ctx, lambda c: smooth_closed(c, [(110, 128 + bob), (112, 86 + bob), (134, 60 + bob), (160, 84 + bob), (162, 128 + bob),
                                             (136, 136 + bob)], 0.5), shade(robe, 0.12), lw=LW)
    flat(ctx, lambda c: ellipse_path(c, 132, 104 + bob, 17, 18), hex2rgb("#100620"))
    for x in (124, 138):
        glow(ctx, x, 104 + bob, 9, halo, 0.9)
        flat(ctx, lambda c, x=x: ellipse_path(c, x, 104 + bob, 3.5, 2.5), (1, 1, 1))
    # hand on staff
    outlined_line(ctx, [(104, 150 + bob), (82, 146 + bob), (68, 136 + bob)], shade(robe, 0.1), 11, 18)
    paint(ctx, lambda c: ellipse_path(c, 66, 134 + bob, 9, 9), hex2rgb("#9a86b8"), lw=3.5, hi=False)


def hex_binder(ctx, bob, frame):
    robe = hex2rgb("#5a1a52")
    arc = hex2rgb("#ff4ad8")
    metal = hex2rgb("#a89ab8")
    mask = hex2rgb("#ece4dc")
    rot = 0.35 if frame == "b" else 0.0
    fl = 5 if frame == "b" else 0
    flat(ctx, lambda c: ellipse_path(c, 140, 234, 46, 7), (0, 0, 0), 0.25)
    glow(ctx, 48, 102 - fl, 60, arc, 0.45)
    # tall narrow robe with ribbon tails
    paint(ctx, lambda c: smooth_closed(c, [(110, 232), (116, 170 + bob), (118, 118 + bob), (142, 92 + bob), (166, 118 + bob), (170, 170 + bob),
                                             (180, 232), (160, 222), (146, 234), (130, 222)], 0.35), robe, lw=LW)
    # chains coiling around the body
    _chain(ctx, [(116, 150 + bob), (142, 164 + bob), (168, 150 + bob)], metal, 9)
    _chain(ctx, [(116, 194 + bob * 0.5), (146, 206 + bob * 0.5), (174, 190 + bob * 0.5)], metal, 9)
    # high collar + mask with stitched mouth (silence)
    for s in (-1, 1):
        paint(ctx, lambda c, s=s: poly_path(c, [(142 + s * 6, 120 + bob), (142 + s * 34, 80 + bob), (142 + s * 26, 126 + bob)]), shade(robe, 0.1),
              lw=4.5, hi=False)
    paint(ctx, lambda c: smooth_closed(c, [(122, 92 + bob), (126, 62 + bob), (142, 50 + bob), (160, 62 + bob), (162, 92 + bob), (142, 112 + bob)], 0.5),
          mask, lw=LW, hi_size=0.6)
    for x in (134, 152):
        glow(ctx, x, 78 + bob, 9, arc, 0.9)
        flat(ctx, lambda c, x=x: poly_path(c, [(x - 7, 76 + bob), (x + 7, 74 + bob), (x + 2, 82 + bob)]), INK)
    stroke(ctx, lambda c: (c.move_to(132, 96 + bob), c.line_to(152, 96 + bob)), INK, 3)
    for k in range(4):
        x = 134 + k * 6
        stroke(ctx, lambda c, x=x: (c.move_to(x, 91 + bob), c.line_to(x + 2, 101 + bob)), INK, 2.5)
    stroke(ctx, lambda c: (c.move_to(142, 50 + bob), c.line_to(142, 64 + bob)), arc, 3)
    # casting arm thrown forward, chain lashing out to a silence sigil
    outlined_line(ctx, [(124, 130 + bob), (100, 120 + bob), (82, 110 + bob)], robe, 11, 18)
    paint(ctx, lambda c: ellipse_path(c, 80, 110 + bob, 8, 8), mask, lw=3.5, hi=False)
    _chain(ctx, [(78, 108 + bob), (66, 100 - fl), (52, 104 - fl)], metal, 8, glow_col=arc)
    cx, cy = 42, 102 - fl
    stroke(ctx, lambda c: ellipse_path(c, cx, cy, 26, 26), INK, 9)
    stroke(ctx, lambda c: ellipse_path(c, cx, cy, 26, 26), arc, 4.5)
    for k in range(8):
        a = rot + k * math.pi / 4
        flat(ctx, lambda c, a=a: rrect_path(c, cx + math.cos(a) * 26 - 3, cy + math.sin(a) * 26 - 3, 6, 6, 1), light(arc, 0.5))
    # muted mouth glyph with a slash through it
    stroke(ctx, lambda c: smooth_open(c, [(cx - 12, cy - 2), (cx, cy + 6), (cx + 12, cy - 2)]), light(arc, 0.4), 4)
    stroke(ctx, lambda c: (c.move_to(cx - 16, cy + 14), c.line_to(cx + 16, cy - 14)), INK, 8)
    stroke(ctx, lambda c: (c.move_to(cx - 16, cy + 14), c.line_to(cx + 16, cy - 14)), arc, 4)
    # orbiting smaller sigils
    for (x, y) in ((196, 80 + fl), (204, 152 - fl)):
        glow(ctx, x, y, 16, arc, 0.6)
        stroke(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 10, 10), arc, 3.5)
        stroke(ctx, lambda c, x=x, y=y: (c.move_to(x - 6, y + 6), c.line_to(x + 6, y - 6)), arc, 3)


def siege_colossus(ctx, bob, frame):
    wood = hex2rgb("#8a5a34")
    iron = hex2rgb("#5c6070")
    rust = hex2rgb("#b0602e")
    eye = hex2rgb("#ffb23a")
    step = 6 if frame == "b" else -6
    flat(ctx, lambda c: ellipse_path(c, 128, 238, 112, 10), (0, 0, 0), 0.28)
    # far legs
    for x, s in ((92, -1), (196, 1)):
        paint(ctx, lambda c, x=x, s=s: rrect_path(c, x - 14 + step * s * 0.5, 170 + bob, 28, 62 - bob, 8), shade(iron, 0.35), lw=LW, hi=False)
    # mortar on the back, tilted up toward the crystal (left)
    ctx.save()
    ctx.translate(160, 76 + bob)
    ctx.rotate(-0.45)
    paint(ctx, lambda c: rrect_path(c, -22, -64, 44, 76, 10), iron, lw=LW, hi_size=0.6)
    paint(ctx, lambda c: rrect_path(c, -28, -72, 56, 18, 7), shade(iron, 0.1), lw=LW - 1, hi_size=0.6)
    flat(ctx, lambda c: ellipse_path(c, 0, -66, 17, 6), INK)
    for y in (-36, -10):
        stroke(ctx, lambda c, y=y: (c.move_to(-22, y), c.line_to(22, y)), rust, 5)
    ctx.restore()
    if frame == "b":
        for (x, y, r) in ((118, 18, 14), (102, 8, 10), (132, 6, 9)):
            paint(ctx, lambda c, x=x, y=y, r=r: ellipse_path(c, x, y + 4, r, r), hex2rgb("#c8c4cc"), lw=3, hi_size=0.7, alpha=0.9)
        glow(ctx, 124, 24, 22, eye, 0.6)
    paint(ctx, lambda c: ellipse_path(c, 160, 96 + bob, 40, 14), shade(wood, 0.1), lw=LW - 1, hi=False)
    # boxy hull
    paint(ctx, lambda c: rrect_path(c, 24, 96 + bob, 212, 100, 26), wood, lw=LW + 1, hi_size=0.6)
    for x in (70, 116, 162, 208):
        stroke(ctx, lambda c, x=x: (c.move_to(x, 100 + bob), c.line_to(x, 192 + bob)), shade(wood, 0.35), 3)
    # iron banding and plates
    paint(ctx, lambda c: rrect_path(c, 24, 142 + bob, 212, 20, 6), iron, lw=4.5, hi=False)
    _rivets(ctx, [(44 + k * 32, 152 + bob) for k in range(7)], 3.4)
    # armoured ram head at the front (left)
    paint(ctx, lambda c: smooth_closed(c, [(8, 150 + bob), (16, 110 + bob), (56, 96 + bob), (76, 122 + bob), (74, 182 + bob), (30, 186 + bob)], 0.35),
          iron, lw=LW + 1, hi_size=0.6)
    glow(ctx, 36, 136 + bob, 24, eye, 0.85)
    flat(ctx, lambda c: rrect_path(c, 18, 131 + bob, 40, 10, 5), hex2rgb("#fff0a0"))
    for k in range(4):
        flat(ctx, lambda c, k=k: poly_path(c, [(14 + k * 14, 172 + bob), (26 + k * 14, 172 + bob), (20 + k * 14, 186 + bob)]), hex2rgb("#d8d0c8"))
    stroke(ctx, lambda c: (c.move_to(12, 172 + bob), c.line_to(70, 172 + bob)), INK, 4)
    flat(ctx, lambda c: ellipse_path(c, 60, 108 + bob, 8, 5), rust, 0.8)
    # near legs (stomping)
    for x, s in ((60, 1), (164, -1)):
        lx = x + step * s
        paint(ctx, lambda c, lx=lx: rrect_path(c, lx - 18, 176 + bob, 36, 58 - bob - (abs(step) if s > 0 and frame == "b" else 0), 9),
              iron, lw=LW, hi_size=0.6)
        paint(ctx, lambda c, lx=lx: rrect_path(c, lx - 24, 222 - (abs(step) if s > 0 and frame == "b" else 0), 48, 14, 6), shade(iron, 0.2), lw=LW - 1, hi=False)
        _rivets(ctx, [(lx, 190 + bob)], 3.4)


def soul_binder(ctx, bob, frame):
    ghost = hex2rgb("#c8fff0")
    chainc = hex2rgb("#5affc8")
    dark = hex2rgb("#0a2a2a")
    fl = 6 if frame == "b" else 0
    sw = 6 if frame == "b" else -6
    flat(ctx, lambda c: ellipse_path(c, 128, 234, 34, 5), (0, 0, 0), 0.18)
    glow(ctx, 128, 130 - fl, 90, chainc, 0.3)
    # tethers reaching outward to bound souls
    ends = ((20, 80 + sw), (16, 196 - sw), (236, 92 - sw), (238, 196 + sw))
    roots = ((96, 128), (100, 140), (160, 128), (156, 140))
    for (rx, ry), (ex, ey) in zip(roots, ends):
        mx, my = (rx + ex) / 2, (ry - fl + ey) / 2 + 14
        _chain(ctx, [(rx, ry - fl), (mx, my), (ex, ey)], chainc, 9, glow_col=chainc)
        glow(ctx, ex, ey, 18, chainc, 0.8)
        paint(ctx, lambda c, ex=ex, ey=ey: smooth_closed(c, [(ex - 7, ey + 5), (ex - 4, ey - 6), (ex, ey - 13), (ex + 4, ey - 6), (ex + 7, ey + 5),
                                                             (ex, ey + 9)], 0.5), light(chainc, 0.4), lw=3, hi=False)
    # tattered spectral robe
    paint(ctx, lambda c: smooth_closed(c, [(92, 200 - fl), (90, 140 - fl), (104, 100 - fl), (128, 90 - fl), (152, 100 - fl), (166, 140 - fl),
                                             (164, 200 - fl), (150, 188 - fl), (140, 220 - fl), (128, 196 - fl), (116, 222 - fl), (106, 188 - fl)], 0.4),
          ghost, lw=LW, alpha=0.85, hi_size=0.6)
    # shackle collar
    paint(ctx, lambda c: ellipse_path(c, 128, 102 - fl, 24, 8), hex2rgb("#7a8a90"), lw=4, hi=False)
    # skull-like head
    paint(ctx, lambda c: smooth_closed(c, [(108, 80 - fl), (110, 52 - fl), (128, 40 - fl), (146, 52 - fl), (148, 80 - fl), (128, 94 - fl)], 0.5),
          ghost, lw=LW, hi_size=0.6)
    for x in (119, 137):
        flat(ctx, lambda c, x=x: ellipse_path(c, x, 66 - fl, 7, 8), dark)
        glow(ctx, x, 66 - fl, 8, chainc, 0.9)
        flat(ctx, lambda c, x=x: ellipse_path(c, x, 66 - fl, 2.5, 2.5), (1, 1, 1))
    stroke(ctx, lambda c: smooth_open(c, [(120, 82 - fl), (128, 86 - fl), (136, 82 - fl)]), dark, 3)
    # outstretched arms
    for s in (-1, 1):
        outlined_line(ctx, [(128 + s * 26, 116 - fl), (128 + s * 34, 128 - fl), (128 + s * 32, 136 - fl)], ghost, 10, 17)
    stroke(ctx, lambda c: smooth_open(c, [(108, 150 - fl), (128, 160 - fl), (148, 150 - fl)]), chainc, 3.5, 0.8)


def spore_carrier(ctx, bob, frame):
    flesh = hex2rgb("#7a5a6a")
    cap = hex2rgb("#a04a7a")
    sac = hex2rgb("#c8ff5a")
    spore = hex2rgb("#eaff7a")
    pulse = 6 if frame == "b" else 0
    flat(ctx, lambda c: ellipse_path(c, 132, 234, 70, 8), (0, 0, 0), 0.25)
    glow(ctx, 158, 108 + bob, 80 + pulse, sac, 0.4)
    feet(ctx, 124, 236, 34, 16, flesh, frame)
    # bloated body
    paint(ctx, lambda c: smooth_closed(c, [(58, 196 + bob), (64, 150 + bob), (100, 124 + bob), (170, 128 + bob), (206, 168 + bob),
                                             (198, 216 + bob), (76, 220 + bob)], 0.5), flesh, lw=LW)
    for (x, y, r) in ((110, 190, 9), (150, 200, 7), (178, 180, 6)):
        paint(ctx, lambda c, x=x, y=y, r=r: ellipse_path(c, x, y + bob, r, r * 0.8), light(flesh, 0.25), lw=2.5, hi=False)
    # glowing spore sac on its back
    paint(ctx, lambda c: ellipse_path(c, 160, 104 + bob, 54 + pulse * 0.5, 48 + pulse * 0.5), sac, lw=LW, alpha=0.75, hi_size=0.5)
    for (x, y, r) in ((140, 96, 6), (166, 80, 5), (180, 112, 7), (154, 124, 5), (130, 120, 4), (188, 88, 4), (160, 104, 5)):
        glow(ctx, x, y + bob, r * 2.4, spore, 0.8)
        flat(ctx, lambda c, x=x, y=y, r=r: ellipse_path(c, x, y + bob, r, r), light(spore, 0.4))
    stroke(ctx, lambda c: smooth_open(c, [(124, 78 + bob), (140, 66 + bob), (160, 62 + bob)]), (1, 1, 1), 4, 0.6)
    # little mushroom caps on the head
    for (x, y, r) in ((70, 136, 18), (96, 124, 14)):
        outlined_line(ctx, [(x, y + 16 + bob), (x + 2, y + bob)], hex2rgb("#e8dcc8"), 6, 12)
        paint(ctx, lambda c, x=x, y=y, r=r: (c.arc(x, y + 2 + bob, r, math.pi, 2 * math.pi), c.close_path()), cap, lw=4.5, hi_size=0.6)
        for d in (-0.5, 0.3):
            flat(ctx, lambda c, x=x, y=y, r=r, d=d: ellipse_path(c, x + d * r, y - r * 0.4 + bob, 3, 2.5), (1, 0.95, 0.9))
    # small face low at the front
    angry_eyes(ctx, 80, 176 + bob, 10, 7, color=spore)
    fang_mouth(ctx, 82, 198 + bob, 12)
    # drifting spores
    for (x, y) in (((40, 90), (210, 50), (226, 150)) if frame == "a" else ((34, 76), (218, 40), (232, 136))):
        glow(ctx, x, y, 12, spore, 0.7)
        flat(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 4, 4), light(spore, 0.5))


def ice_statue(ctx, bob, frame):
    ice = hex2rgb("#bfe8ff")
    deep = hex2rgb("#6aa8e0")
    stone = hex2rgb("#8a94a8")
    hi_line = (0.95, 1.0, 1.0)
    flat(ctx, lambda c: ellipse_path(c, 128, 236, 70, 8), (0, 0, 0), 0.25)
    glow(ctx, 128, 130, 96, hex2rgb("#9ad8ff"), 0.3)
    # pedestal
    paint(ctx, lambda c: poly_path(c, [(66, 234), (72, 204), (184, 204), (190, 234)]), stone, lw=LW, hi_size=0.6)
    paint(ctx, lambda c: rrect_path(c, 60, 194, 136, 16, 5), light(stone, 0.15), lw=LW - 1, hi=False)
    flat(ctx, lambda c: poly_path(c, [(100, 196), (114, 194), (108, 204)]), (1, 1, 1), 0.7)

    def facet(pts, col, lw=4.5):
        paint(ctx, lambda c: poly_path(c, pts), col, lw=lw, hi=False, shade_amt=0.15, alpha=0.92)
        stroke(ctx, lambda c: (c.move_to(*pts[0]), c.line_to(*pts[1])), hi_line, 2, 0.8)
    # raised crystalline wings
    for s in (-1, 1):
        facet([(128 + s * 18, 110), (128 + s * 70, 30), (128 + s * 104, 46), (128 + s * 94, 96), (128 + s * 70, 140), (128 + s * 30, 140)],
              ice if s < 0 else mix(ice, deep, 0.35))
        for k in range(3):
            stroke(ctx, lambda c, s=s, k=k: (c.move_to(128 + s * 30, 128), c.line_to(128 + s * (74 + k * 10), 46 + k * 26)), deep, 2.5, 0.7)
    # robed guardian body with sword planted
    facet([(100, 196), (106, 140), (128, 112), (150, 140), (156, 196)], ice)
    facet([(128, 112), (150, 140), (156, 196), (128, 196)], mix(ice, deep, 0.45))
    outlined_line(ctx, [(128, 196), (128, 150)], light(ice, 0.4), 7, 13, smooth=False)
    facet([(112, 150), (144, 150), (138, 158), (118, 158)], deep, 3.5)
    # helmeted head
    facet([(114, 104), (118, 82), (128, 70), (138, 82), (142, 104), (128, 114)], ice)
    flat(ctx, lambda c: poly_path(c, [(118, 92), (138, 92), (136, 98), (120, 98)]), deep)
    facet([(128, 70), (124, 50), (132, 56)], light(ice, 0.3), 3)
    # sparkles move between frames (only difference)
    spots = ((84, 44, 9), (150, 126, 7), (198, 82, 6), (118, 176, 5)) if frame == "a" else ((176, 40, 9), (110, 128, 7), (62, 92, 6), (140, 180, 5))
    for (x, y, r) in spots:
        glow(ctx, x, y, r * 2.2, (1, 1, 1), 0.5)
        sparkle(ctx, x, y, r)


def seraphyne(ctx, bob, frame):
    gown = hex2rgb("#8ad0ff")
    deep = hex2rgb("#3a6ad0")
    skin = hex2rgb("#e8f0ff")
    hair = hex2rgb("#f4fbff")
    ice = hex2rgb("#bff0ff")
    b = bob * 2
    sway = 10 if frame == "b" else 0
    glow(ctx, 256, 250, 250, hex2rgb("#9ae0ff"), 0.35)
    flat(ctx, lambda c: ellipse_path(c, 262, 488, 160, 18), (0, 0, 0), 0.25)
    # frost aura motes
    for (x, y, r) in ((70, 120, 12), (440, 160, 14), (60, 330, 10), (452, 360, 11), (110, 40, 8), (400, 60, 9)):
        _snowflake(ctx, x + (sway if frame == "b" else 0) * 0.5, y + (6 if frame == "b" else 0), r, (1, 1, 1), 0.85)
    # flowing hair / cape behind (sweeps right)
    paint(ctx, lambda c: smooth_closed(c, [(280, 120 + b), (330, 150 + b), (380, 250 + b), (430 + sway, 400), (470 + sway, 470), (380, 452),
                                             (330, 330 + b), (290, 220 + b)], 0.45), mix(gown, deep, 0.55), lw=LW + 2, alpha=0.9, hi_size=0.5)
    paint(ctx, lambda c: smooth_closed(c, [(226, 100 + b), (300, 92 + b), (330, 160 + b), (350, 250 + b + sway * 0.5), (316, 230 + b),
                                             (290, 160 + b)], 0.45), hair, lw=LW + 1, hi_size=0.5)
    # icicle collar fan behind the head
    for k in range(7):
        a = math.pi + 0.35 + k * (math.pi - 0.7) / 6
        tip = (256 + math.cos(a) * 110, 200 + b + math.sin(a) * 100)
        paint(ctx, lambda c, a=a, tip=tip: poly_path(c, [(256 + math.cos(a - 0.12) * 40, 200 + b + math.sin(a - 0.12) * 40), tip,
                                                          (256 + math.cos(a + 0.12) * 40, 200 + b + math.sin(a + 0.12) * 40)]),
              ice, lw=4.5, hi_size=0.7)
    # gown: wide bell flowing to the ground, icicle hem
    hem = [(120, 470), (140, 486), (160, 468), (186, 488), (210, 470), (236, 490), (262, 472), (290, 490), (316, 470), (344, 488), (372, 468),
           (396, 484), (410, 462)]
    paint(ctx, lambda c: (c.move_to(226, 250 + b), c.curve_to(200, 320 + b, 140, 380, 120, 470), [c.line_to(*p) for p in hem],
                          c.curve_to(380, 380, 316, 320 + b, 286, 250 + b), c.close_path()), gown, lw=LW + 2, hi_size=0.6)
    for x0, x1 in ((240, 200), (256, 262), (272, 330)):
        stroke(ctx, lambda c, x0=x0, x1=x1: smooth_open(c, [(x0, 270 + b), ((x0 + x1) / 2, 380), (x1, 468)]), deep, 4, 0.5)
    stroke(ctx, lambda c: smooth_open(c, [(150, 440), (256, 456), (380, 440)]), (1, 1, 1), 4, 0.55)
    # bodice with crystal brooch
    paint(ctx, lambda c: smooth_closed(c, [(222, 256 + b), (218, 196 + b), (256, 180 + b), (294, 196 + b), (290, 256 + b), (256, 274 + b)], 0.35),
          deep, lw=LW + 1, hi_size=0.5)
    glow(ctx, 256, 220 + b, 30, ice, 0.8)
    paint(ctx, lambda c: poly_path(c, [(256, 200 + b), (270, 220 + b), (256, 240 + b), (242, 220 + b)]), ice, lw=4, hi_size=0.8)
    # arm with frost magic (right side) and sceptre arm (left, toward crystal)
    outlined_line(ctx, [(290, 206 + b), (318, 250 + b), (334, 286 + b)], skin, 13, 21)
    glow(ctx, 340, 296 + b, 40, ice, 0.7)
    for k in range(3):
        a = k * 2.1 + (0.5 if frame == "b" else 0)
        stroke(ctx, lambda c, a=a: c.arc(340, 296 + b, 22 + k * 8, a, a + 1.6), ice, 4, 0.85)
    outlined_line(ctx, [(196, 470), (176, 70 + b)], hex2rgb("#d8f4ff"), 9, 17, smooth=False)
    glow(ctx, 176, 66 + b, 52, ice, 0.8)
    paint(ctx, lambda c: star_path(c, 176, 62 + b, 34, 10, 6, rot=-math.pi / 2 + (0.2 if frame == "b" else 0)), ice, lw=4.5, hi_size=0.8)
    sparkle(ctx, 172, 56 + b, 10)
    outlined_line(ctx, [(222, 206 + b), (196, 236 + b), (184, 216 + b)], skin, 13, 21)
    paint(ctx, lambda c: ellipse_path(c, 184, 214 + b, 12, 12), skin, lw=4, hi=False)
    # head
    paint(ctx, lambda c: smooth_closed(c, [(222, 140 + b), (226, 104 + b), (256, 90 + b), (286, 104 + b), (288, 140 + b), (256, 170 + b)], 0.5),
          skin, lw=LW + 1, hi_size=0.5)
    # hair framing the face
    paint(ctx, lambda c: smooth_closed(c, [(216, 150 + b), (220, 100 + b), (256, 82 + b), (294, 100 + b), (292, 132 + b), (276, 106 + b),
                                             (244, 104 + b), (232, 130 + b)], 0.45), hair, lw=LW, hi=False)
    # cold glowing eyes, looking left
    for x in (240, 266):
        glow(ctx, x, 132 + b, 12, hex2rgb("#7ff0ff"), 0.9)
        paint(ctx, lambda c, x=x: ellipse_path(c, x, 132 + b, 8, 5), hex2rgb("#e8ffff"), lw=3, hi=False, shade_amt=0)
        flat(ctx, lambda c, x=x: ellipse_path(c, x - 2, 132 + b, 3, 4), deep)
        stroke(ctx, lambda c, x=x: (c.move_to(x - 9, 124 + b), c.line_to(x + 8, 122 + b)), INK, 3)
    stroke(ctx, lambda c: smooth_open(c, [(246, 154 + b), (254, 156 + b), (262, 153 + b)]), hex2rgb("#5a7ad0"), 3)
    # crown of icicles
    for i, (dx, h) in enumerate(((-34, 30), (-22, 46), (-10, 60), (0, 78), (10, 60), (22, 46), (34, 30))):
        paint(ctx, lambda c, dx=dx, h=h: poly_path(c, [(256 + dx - 7, 92 + b), (256 + dx, 92 + b - h), (256 + dx + 7, 92 + b)]),
              ice if i % 2 == 0 else light(ice, 0.4), lw=4, hi_size=0.7)
    paint(ctx, lambda c: rrect_path(c, 218, 86 + b, 76, 12, 6), hex2rgb("#d8f4ff"), lw=4, hi=False)
    glow(ctx, 256, 92 + b, 14, ice, 0.9)
    paint(ctx, lambda c: poly_path(c, [(256, 84 + b), (262, 92 + b), (256, 100 + b), (250, 92 + b)]), hex2rgb("#7ff0ff"), lw=2.5, hi=False)
    sparkle(ctx, 246, 30 + b, 9)


def gravemaw(ctx, bob, frame):
    iron = hex2rgb("#5c6070")
    earth = hex2rgb("#6e5a46")
    rust = hex2rgb("#b0602e")
    maw = hex2rgb("#3a0a14")
    fire = hex2rgb("#ffb23a")
    b = bob * 2
    step = 8 if frame == "b" else -8
    glow(ctx, 256, 280, 240, fire, 0.18)
    flat(ctx, lambda c: ellipse_path(c, 256, 490, 190, 20), (0, 0, 0), 0.3)
    # pillar legs
    for s in (-1, 1):
        lift = step if s > 0 else -step
        paint(ctx, lambda c, s=s, lift=lift: rrect_path(c, 256 + s * 92 - 44, 360 + b, 88, 116 - b + min(0, lift), 18), shade(earth, 0.1), lw=LW + 2,
              hi_size=0.5)
        paint(ctx, lambda c, s=s, lift=lift: rrect_path(c, 256 + s * 92 - 56, 454 + min(0, lift), 112, 32, 12), iron, lw=LW + 1, hi_size=0.5)
        paint(ctx, lambda c, s=s: rrect_path(c, 256 + s * 92 - 48, 384 + b, 96, 30, 10), iron, lw=LW, hi=False)
        _rivets(ctx, [(256 + s * 92 + k * 26, 399 + b) for k in (-1, 0, 1)], 4.5)
    # colossal torso of earth with iron plates
    paint(ctx, lambda c: smooth_closed(c, [(110, 230 + b), (140, 150 + b), (256, 118 + b), (372, 150 + b), (402, 230 + b), (380, 330 + b),
                                             (330, 384 + b), (182, 384 + b), (132, 330 + b)], 0.4), earth, lw=LW + 3, hi_size=0.5)
    for (pts, col) in (([(142, 180), (196, 150), (220, 196), (160, 220)], iron), ([(370, 180), (316, 150), (292, 196), (352, 220)], iron),
                       ([(150, 300), (190, 290), (196, 350), (160, 340)], mix(iron, rust, 0.3)),
                       ([(362, 300), (322, 290), (316, 350), (352, 340)], iron)):
        paint(ctx, lambda c, pts=pts: smooth_closed(c, [(x, y + b) for x, y in pts], 0.25), col, lw=LW, hi_size=0.6)
        _rivets(ctx, [(x + (sum(p[0] for p in pts) / 4 - x) * 0.25, y + b + (sum(p[1] for p in pts) / 4 - y) * 0.25) for x, y in pts], 4)
    # shoulder artillery cannons (aimed up-left toward the crystal)
    for s, (cx, cy) in ((-1, (146, 140)), (1, (366, 140))):
        ctx.save()
        ctx.translate(cx, cy + b)
        ctx.rotate(1.05)
        paint(ctx, lambda c: rrect_path(c, -110, -26, 130, 52, 16), iron, lw=LW + 2, hi_size=0.5)
        paint(ctx, lambda c: rrect_path(c, -122, -32, 26, 64, 10), shade(iron, 0.1), lw=LW + 1, hi=False)
        flat(ctx, lambda c: ellipse_path(c, -122, 0, 7, 22), INK)
        for x in (-70, -30):
            stroke(ctx, lambda c, x=x: (c.move_to(x, -26), c.line_to(x, 26)), rust, 7)
        ctx.restore()
        paint(ctx, lambda c: ellipse_path(c, cx + 6, cy + 20 + b, 46, 40), shade(iron, 0.15), lw=LW + 1, hi_size=0.5)
        _rivets(ctx, [(cx + 6 + math.cos(a) * 30, cy + 20 + b + math.sin(a) * 26) for a in (0.3, 1.6, 2.9, 4.2, 5.5)], 4)
    if frame == "b":
        for (x, y, r) in ((90, 22, 20), (110, 6, 13), (310, 22, 20), (330, 6, 13)):
            paint(ctx, lambda c, x=x, y=y, r=r: ellipse_path(c, x, y + 14, r, r), hex2rgb("#c8c4cc"), lw=4, hi_size=0.7, alpha=0.9)
        for (x, y) in ((96, 40), (316, 40)):
            glow(ctx, x, y, 40, fire, 0.75)
    # gaping maw in the chest
    gape = 10 if frame == "b" else 0
    glow(ctx, 256, 278 + b, 90, fire, 0.55)
    paint(ctx, lambda c: smooth_closed(c, [(184, 240 + b - gape), (256, 214 + b - gape), (328, 240 + b - gape), (318, 316 + b + gape),
                                             (256, 340 + b + gape), (194, 316 + b + gape)], 0.45), maw, lw=LW + 2, hi=False, shade_amt=0)
    glow(ctx, 256, 286 + b, 48, fire, 0.8)
    for k in range(7):
        x = 200 + k * 19
        yt = 234 + b - gape + abs(k - 3) * 3
        yb = 322 + b + gape - abs(k - 3) * 3
        paint(ctx, lambda c, x=x, yt=yt: poly_path(c, [(x - 9, yt), (x + 9, yt), (x, yt + 28)]), hex2rgb("#f0e8d8"), lw=3, hi=False)
        paint(ctx, lambda c, x=x, yb=yb: poly_path(c, [(x - 9, yb), (x + 9, yb), (x, yb - 24)]), hex2rgb("#f0e8d8"), lw=3, hi=False)
    # massive fists
    for s in (-1, 1):
        fy = 350 + b + (6 if (s > 0) == (frame == "b") else 0)
        outlined_line(ctx, [(256 + s * 140, 210 + b), (256 + s * 176, 290 + b), (256 + s * 180, fy - 20)], earth, 50, 64)
        paint(ctx, lambda c, s=s, fy=fy: rrect_path(c, 256 + s * 180 - 44, fy - 34, 88, 76, 22), iron, lw=LW + 2, hi_size=0.6)
        for k in range(3):
            stroke(ctx, lambda c, s=s, fy=fy, k=k: (c.move_to(256 + s * 180 - 22 + k * 22, fy - 30), c.line_to(256 + s * 180 - 22 + k * 22, fy - 6)), INK, 4)
    # small helmeted head sunk between the cannons
    paint(ctx, lambda c: smooth_closed(c, [(220, 160 + b), (222, 112 + b), (256, 96 + b), (290, 112 + b), (292, 160 + b), (256, 172 + b)], 0.4),
          iron, lw=LW + 2, hi_size=0.6)
    glow(ctx, 256, 136 + b, 30, fire, 0.9)
    flat(ctx, lambda c: rrect_path(c, 228, 130 + b, 56, 12, 6), hex2rgb("#fff0a0"))
    paint(ctx, lambda c: poly_path(c, [(246, 98 + b), (256, 70 + b), (266, 98 + b)]), rust, lw=4, hi=False)
    _rivets(ctx, [(232, 116 + b), (280, 116 + b), (256, 160 + b)], 4)


DRAWERS = {
    "grunt": grunt, "runner": runner, "swarmling": swarmling, "shieldbearer": shieldbearer, "hexcaster": hexcaster,
    "sapper": sapper, "warded": warded, "juggernaut": juggernaut, "summoner": summoner, "banner": banner,
    "mimic": mimic, "ravager": ravager, "riftling": riftling, "siegebreaker_golem": golem, "rift_warden": warden,
    "mana_leech": mana_leech, "crystal_parasite": crystal_parasite, "ash_imp": ash_imp, "ignaroth": ignaroth,
    "goblin_sprinter": goblin_sprinter, "ironback_golem": ironback_golem, "spirit_splitter": spirit_splitter, "spirit_wisp": spirit_wisp,
    "flame_devourer": flame_devourer, "frost_wraith": frost_wraith, "storm_harpy": storm_harpy, "stone_burrower": stone_burrower,
    "void_priest": void_priest, "hex_binder": hex_binder, "siege_colossus": siege_colossus, "soul_binder": soul_binder,
    "spore_carrier": spore_carrier, "ice_statue": ice_statue, "seraphyne": seraphyne, "gravemaw": gravemaw,
}
