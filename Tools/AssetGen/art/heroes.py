"""Procedural hero sprites: 12 humanoid heroes x (idle, cast, downed, evolution A, evolution B) + portraits.

Each hero is assembled from parametric parts (body build, outfit, hair/headgear, face, prop) so the
silhouettes differ by more than colour: hoods vs spikes vs crowns vs helmets, robes vs armour vs
cloaks, staffs vs swords vs shields vs bows. Canvas 320x320, feet at y=292.
"""
import math
import cairo
from toolkit import (INK, Canvas, hex2rgb, mix, shade, light, grey, paint, flat, stroke, glow, sparkle,
                     smooth_closed, smooth_open, ellipse_path, rrect_path, poly_path, star_path, outlined_line)

W = H = 320
GROUND = 292
CX = 160

SKIN = {
    "fair": hex2rgb("#ffe0c8"), "light": hex2rgb("#f6c9a4"), "tan": hex2rgb("#d99a6c"),
    "brown": hex2rgb("#a8693f"), "deep": hex2rgb("#6e4127"),
}

ELEMENT = {
    "fire": (hex2rgb("#ff5a2c"), hex2rgb("#ffb230")),
    "water": (hex2rgb("#2f8cff"), hex2rgb("#5fe0ff")),
    "lightning": (hex2rgb("#8c4dff"), hex2rgb("#ffe14a")),
    "ice": (hex2rgb("#7fd8ff"), hex2rgb("#e8fbff")),
    "wind": (hex2rgb("#2fd39a"), hex2rgb("#c4ffd9")),
    "earth": (hex2rgb("#b9773a"), hex2rgb("#8fc24a")),
}

HEROES = {
    "ignis": dict(element="fire", skin="light", build="slim", outfit="robe", head="hood_point", hair="#5a2a1c",
                  main="#d8322a", second="#ffb13b", trim="#ffd75e", prop="ember_staff", eyes="#3a1a10"),
    "cinder": dict(element="fire", skin="tan", build="broad", outfit="plate", head="spiky", hair="#ff4b26",
                   main="#3b3446", second="#ff7a2a", trim="#ffc04a", prop="flame_greatsword", eyes="#2a120a"),
    "marina": dict(element="water", skin="fair", build="slim", outfit="robe", head="long_flow", hair="#2a6fe8",
                   main="#f2fbff", second="#36b6e8", trim="#7ce9ff", prop="wave_staff", eyes="#163a74"),
    "tidal": dict(element="water", skin="brown", build="normal", outfit="tunic", head="hood_round", hair="#13314a",
                  main="#1f8fa0", second="#0f4e66", trim="#7ff3ff", prop="water_whips", eyes="#0b2a3a", mask=True),
    "volt": dict(element="lightning", skin="light", build="slim", outfit="coat", head="spiky_tall", hair="#ffe04a",
                 main="#5b2fb0", second="#2a1a5c", trim="#ffe04a", prop="conductor_rods", eyes="#2a1050"),
    "raiden": dict(element="lightning", skin="tan", build="lean", outfit="tunic", head="short_messy", hair="#262038",
                   main="#232a52", second="#8c4dff", trim="#ffd23a", prop="twin_daggers", eyes="#1a1230", scarf="#ffd23a"),
    "freya": dict(element="ice", skin="fair", build="slim", outfit="gown", head="long_straight", hair="#e6f3ff",
                  main="#8fd6ff", second="#4a7fd6", trim="#ffffff", prop="ice_wand", eyes="#2a4a8a", crown=True, cape="#4a7fd6"),
    "glacius": dict(element="ice", skin="light", build="broad", outfit="heavy_armor", head="helm_visor", hair="#3a5a7a",
                    main="#b9d8f0", second="#5f8fc0", trim="#e8fbff", prop="tower_shield", eyes="#1a2a4a"),
    "zephyr": dict(element="wind", skin="deep", build="slim", outfit="mantle", head="bun", hair="#9ff2cf",
                   main="#e9fff4", second="#2fbf86", trim="#c4ffd9", prop="fan", eyes="#13352a"),
    "sylph": dict(element="wind", skin="light", build="lean", outfit="cloak", head="ponytail", hair="#3d8f4a",
                  main="#4fc98a", second="#2a5a3a", trim="#d6ffe6", prop="longbow", eyes="#173a22"),
    "terra": dict(element="earth", skin="brown", build="broad", outfit="stone_armor", head="helm_horn", hair="#4a2f1c",
                  main="#8a6a4a", second="#5a8a3a", trim="#d9b56a", prop="hammer", eyes="#2a1a0e"),
    "magnus": dict(element="earth", skin="tan", build="huge", outfit="belted", head="mohawk", hair="#c97a2a",
                   main="#6a4a2e", second="#9ac24a", trim="#e0b060", prop="gauntlets", eyes="#2a160a"),
}

EVOLUTIONS = {
    # branch -> (accent override, emblem, aura colour hint)
    "A": dict(accent="#ffd35a", emblem="crown"),
    "B": dict(accent=None, emblem="wings"),
}

LW = 6.0  # main ink width


# ============================================================================ body parts

def build_metrics(build):
    return {
        "slim": dict(shoulder=46, waist=36, hip=40, arm=15, leg=14, neck=0),
        "lean": dict(shoulder=48, waist=36, hip=38, arm=15, leg=15, neck=0),
        "normal": dict(shoulder=52, waist=42, hip=42, arm=16, leg=16, neck=0),
        "broad": dict(shoulder=62, waist=48, hip=46, arm=19, leg=18, neck=0),
        "huge": dict(shoulder=70, waist=52, hip=48, arm=22, leg=19, neck=0),
    }[build]


def draw_legs(ctx, spec, m, pose):
    boot = shade(hex2rgb(spec["second"]), 0.35)
    pants = shade(hex2rgb(spec["main"]), 0.45)
    for side in (-1, 1):
        x = CX + side * (m["hip"] * 0.45)
        top = 236
        def leg(c, x=x):
            rrect_path(c, x - m["leg"], top, m["leg"] * 2, GROUND - top - 8, m["leg"])
        paint(ctx, leg, pants, lw=LW, hi=False)
        def foot(c, x=x, side=side):
            ellipse_path(c, x + side * 4, GROUND - 8, m["leg"] + 7, 11)
        paint(ctx, foot, boot, lw=LW, hi_size=0.5)


def torso_path(spec, m, lean=0.0):
    s, w, hp = m["shoulder"], m["waist"], m["hip"]
    top, bottom = 164, 250
    o = spec["outfit"]
    if o in ("robe", "gown"):
        bottom = GROUND - 6
        flare = hp + (26 if o == "gown" else 18)
        pts = [(CX - s * 0.62 + lean, top), (CX + s * 0.62 + lean, top), (CX + s + lean * 0.6, top + 16),
               (CX + w + 2, 214), (CX + flare, bottom - 4), (CX, bottom + 4), (CX - flare, bottom - 4),
               (CX - w - 2, 214), (CX - s + lean * 0.6, top + 16)]
    elif o in ("cloak", "mantle"):
        bottom = 262
        pts = [(CX - s * 0.6 + lean, top - 2), (CX + s * 0.6 + lean, top - 2), (CX + s + 8 + lean * 0.6, top + 22),
               (CX + hp + 16, bottom), (CX, bottom + 8), (CX - hp - 16, bottom), (CX - s - 8 + lean * 0.6, top + 22)]
    else:
        pts = [(CX - s * 0.6 + lean, top), (CX + s * 0.6 + lean, top), (CX + s + lean * 0.6, top + 14),
               (CX + w, 212), (CX + hp, bottom), (CX, bottom + 6), (CX - hp, bottom), (CX - w, 212),
               (CX - s + lean * 0.6, top + 14)]
    return lambda c: smooth_closed(c, pts, 0.42)


def draw_torso(ctx, spec, m, lean=0.0):
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    o = spec["outfit"]
    path = torso_path(spec, m, lean)
    paint(ctx, path, main, lw=LW, shade_dir=(0.45, 0.25), hi_pos=(-0.25, -0.35))
    ctx.save()
    ctx.new_path()
    path(ctx)
    ctx.clip()
    # outfit-specific detail inside the torso silhouette
    if o in ("robe", "gown"):
        flat(ctx, lambda c: rrect_path(c, CX - 13 + lean * 0.3, 168, 26, 140, 10), second)
        stroke(ctx, lambda c: (c.move_to(CX - 13 + lean * 0.3, 175), c.line_to(CX - 13 + lean * 0.3, 300)), INK, 3)
        stroke(ctx, lambda c: (c.move_to(CX + 13 + lean * 0.3, 175), c.line_to(CX + 13 + lean * 0.3, 300)), INK, 3)
        flat(ctx, lambda c: rrect_path(c, CX - 60, 218, 120, 14, 7), trim)
        stroke(ctx, lambda c: rrect_path(c, CX - 60, 218, 120, 14, 7), INK, 3)
    elif o in ("plate", "heavy_armor", "stone_armor"):
        plate = second if o != "heavy_armor" else light(main, 0.25)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 34, 176), (CX + 34, 176), (CX + 30, 222), (CX, 236), (CX - 30, 222)], 0.4),
              plate, lw=4, hi_size=0.6)
        if o == "plate":
            for i in range(3):
                stroke(ctx, lambda c, i=i: (c.move_to(CX - 20 + i * 20, 188), c.line_to(CX - 14 + i * 14, 222)), trim, 3)
        if o == "stone_armor":
            for (x, y) in ((CX - 14, 196), (CX + 12, 206), (CX - 4, 220)):
                stroke(ctx, lambda c, x=x, y=y: (c.move_to(x - 6, y), c.line_to(x + 5, y + 4)), INK, 3)
        flat(ctx, lambda c: rrect_path(c, CX - 56, 232, 112, 12, 5), trim)
        stroke(ctx, lambda c: rrect_path(c, CX - 56, 232, 112, 12, 5), INK, 3)
    elif o == "coat":
        flat(ctx, lambda c: poly_path(c, [(CX - 4, 166), (CX + 4, 166), (CX + 26, 260), (CX - 26, 260)]), second)
        stroke(ctx, lambda c: (c.move_to(CX - 4, 166), c.line_to(CX - 26, 262)), INK, 3)
        stroke(ctx, lambda c: (c.move_to(CX + 4, 166), c.line_to(CX + 26, 262)), INK, 3)
        for i in range(3):
            paint(ctx, lambda c, i=i: ellipse_path(c, CX + 14, 190 + i * 18, 4, 4), hex2rgb(spec["trim"]), lw=2, hi=False, shade_amt=0)
        # lightning trim zigzag on hem
        stroke(ctx, lambda c: smooth_open(c, [(CX - 60, 244), (CX - 40, 236), (CX - 26, 248)], 0), trim, 4)
    elif o in ("tunic", "belted"):
        flat(ctx, lambda c: rrect_path(c, CX - 60, 222, 120, 14, 6), second if o == "tunic" else hex2rgb("#4a3020"))
        stroke(ctx, lambda c: rrect_path(c, CX - 60, 222, 120, 14, 6), INK, 3)
        paint(ctx, lambda c: rrect_path(c, CX - 11, 220, 22, 18, 4), trim, lw=3, hi=False)
        if o == "tunic":
            stroke(ctx, lambda c: (c.move_to(CX - 18, 168), c.line_to(CX, 196), c.line_to(CX + 18, 168)), trim, 4)
    elif o in ("cloak", "mantle"):
        stroke(ctx, lambda c: smooth_open(c, [(CX - 30, 190), (CX - 24, 240), (CX - 28, 262)]), shade(main, 0.4), 4)
        stroke(ctx, lambda c: smooth_open(c, [(CX + 30, 190), (CX + 24, 240), (CX + 28, 262)]), shade(main, 0.4), 4)
        if o == "mantle":
            # feather layer across the shoulders
            for i in range(9):
                x = CX - 64 + i * 16
                paint(ctx, lambda c, x=x: smooth_closed(c, [(x - 9, 168), (x + 9, 168), (x + 6, 200), (x, 210), (x - 6, 200)], 0.5),
                      second if i % 2 else light(second, 0.25), lw=3, hi=False)
    ctx.restore()


def draw_arm(ctx, spec, m, shoulder, hand, sleeve_color, skin, behind=False):
    """Arm as a thick tapered stroke with ink border; sleeve over the upper part, round hand."""
    sx, sy = shoulder
    hx, hy = hand
    mx, my = (sx + hx) / 2 + (6 if hx > sx else -6), (sy + hy) / 2
    width = m["arm"] * 2
    outlined_line(ctx, [(sx, sy), (mx, my), (hx, hy)], sleeve_color, width, width + LW * 1.6)
    # cuff
    ex, ey = (mx * 0.4 + hx * 0.6), (my * 0.4 + hy * 0.6)
    paint(ctx, lambda c: ellipse_path(c, ex, ey, m["arm"] + 2, m["arm"] * 0.75, math.atan2(hy - my, hx - mx) + math.pi / 2),
          light(sleeve_color, 0.15), lw=3.5, hi=False)
    paint(ctx, lambda c: ellipse_path(c, hx, hy, m["arm"] * 0.85, m["arm"] * 0.85), skin, lw=4.5, hi_size=0.6)


def head_path(cx=CX, cy=112, rx=54, ry=50):
    def p(c):
        smooth_closed(c, [(cx - rx, cy - 6), (cx - rx * 0.72, cy - ry * 0.9), (cx, cy - ry), (cx + rx * 0.72, cy - ry * 0.9),
                          (cx + rx, cy - 6), (cx + rx * 0.82, cy + ry * 0.62), (cx + rx * 0.3, cy + ry * 0.98),
                          (cx - rx * 0.3, cy + ry * 0.98), (cx - rx * 0.82, cy + ry * 0.62)], 0.55)
    return p


def draw_face(ctx, spec, cx=CX, cy=118, mood="calm", downed=False):
    eye = hex2rgb(spec["eyes"])
    if downed:
        for side in (-1, 1):
            x = cx + side * 19
            stroke(ctx, lambda c, x=x: (c.move_to(x - 7, cy - 7), c.line_to(x + 7, cy + 7), c.move_to(x + 7, cy - 7), c.line_to(x - 7, cy + 7)), INK, 4)
        stroke(ctx, lambda c: smooth_open(c, [(cx - 8, cy + 24), (cx, cy + 20), (cx + 8, cy + 24)]), INK, 3.5)
        return
    for side in (-1, 1):
        x = cx + side * 19
        if mood == "focus":
            paint(ctx, lambda c, x=x: ellipse_path(c, x, cy + 2, 8.5, 10), eye, lw=3, hi=False, shade_amt=0)
        else:
            paint(ctx, lambda c, x=x: ellipse_path(c, x, cy, 9, 13), eye, lw=3, hi=False, shade_amt=0)
        flat(ctx, lambda c, x=x: ellipse_path(c, x - 3, cy - 5, 3.6, 4.4), (1, 1, 1))
        flat(ctx, lambda c, x=x: ellipse_path(c, x + 3, cy + 4, 1.8, 1.8), (1, 1, 1), 0.85)
        # brows
        tilt = 4 if mood == "focus" else 0
        stroke(ctx, lambda c, x=x, side=side: (c.move_to(x - 9, cy - 18 - (tilt if side < 0 else 0)),
                                               c.line_to(x + 9, cy - 18 - (tilt if side > 0 else 0))), INK, 3.2)
    blush = mix(SKIN[spec["skin"]], hex2rgb("#ff6a7a"), 0.55)
    for side in (-1, 1):
        flat(ctx, lambda c, side=side: ellipse_path(c, cx + side * 33, cy + 14, 9, 5), blush, 0.55)
    if spec.get("mask"):
        return
    if mood == "focus":
        paint(ctx, lambda c: ellipse_path(c, cx, cy + 22, 6, 5), hex2rgb("#7a2a3a"), lw=3, hi=False, shade_amt=0)
    else:
        stroke(ctx, lambda c: smooth_open(c, [(cx - 7, cy + 20), (cx, cy + 25), (cx + 7, cy + 20)]), INK, 3.2)


# ============================================================================ hair & headgear

def draw_hair_back(ctx, spec):
    hair = hex2rgb(spec["hair"])
    h = spec["head"]
    if h == "long_flow":
        paint(ctx, lambda c: smooth_closed(c, [(CX - 58, 96), (CX + 58, 96), (CX + 70, 170), (CX + 82, 236), (CX + 50, 226),
                                                 (CX + 30, 196), (CX - 30, 196), (CX - 52, 230), (CX - 80, 232), (CX - 68, 168)], 0.5),
              hair, lw=LW)
    elif h == "long_straight":
        paint(ctx, lambda c: rrect_path(c, CX - 64, 84, 128, 150, 40), hair, lw=LW)
    elif h == "ponytail":
        paint(ctx, lambda c: smooth_closed(c, [(CX + 40, 74), (CX + 74, 80), (CX + 94, 130), (CX + 84, 186), (CX + 70, 160), (CX + 62, 110)], 0.5),
              hair, lw=LW)
    elif h == "bun":
        paint(ctx, lambda c: ellipse_path(c, CX, 52, 26, 22), hair, lw=LW)
    elif h == "hood_point" or h == "hood_round":
        hood = hex2rgb(spec["main"]) if h == "hood_point" else hex2rgb(spec["second"])
        paint(ctx, lambda c: smooth_closed(c, [(CX - 70, 150), (CX - 72, 100), (CX - 50, 60), (CX, 44), (CX + 50, 60),
                                                 (CX + 72, 100), (CX + 70, 150), (CX, 160)], 0.5), shade(hood, 0.2), lw=LW)


def draw_hair_front(ctx, spec, element_color):
    hair = hex2rgb(spec["hair"])
    h = spec["head"]
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    if h == "hood_point":
        def hood(c):
            smooth_closed(c, [(CX - 64, 120), (CX - 62, 76), (CX - 30, 50), (CX + 6, 6), (CX + 18, 2), (CX + 30, 40),
                              (CX + 60, 70), (CX + 66, 120), (CX + 46, 92), (CX, 78), (CX - 46, 92)], 0.45)
        paint(ctx, hood, main, lw=LW, hi_pos=(-0.2, -0.2))
        stroke(ctx, lambda c: smooth_open(c, [(CX - 60, 108), (CX - 40, 90), (CX, 80), (CX + 40, 90), (CX + 60, 108)]), trim, 5)
        # flame tip
        paint(ctx, lambda c: smooth_closed(c, [(CX + 10, 6), (CX + 26, -2), (CX + 22, 12), (CX + 34, 10), (CX + 20, 26)], 0.6),
              hex2rgb("#ffb230"), lw=3.5, hi=False)
    elif h == "hood_round":
        hood = second
        paint(ctx, lambda c: smooth_closed(c, [(CX - 64, 124), (CX - 60, 72), (CX - 20, 52), (CX + 20, 52), (CX + 60, 72),
                                                 (CX + 64, 124), (CX + 44, 92), (CX, 82), (CX - 44, 92)], 0.5), hood, lw=LW)
    elif h in ("spiky", "spiky_tall"):
        tall = 1.4 if h == "spiky_tall" else 1.0
        pts = [(CX - 58, 118), (CX - 70, 86), (CX - 54, 82), (CX - 62, 46 - 10 * tall), (CX - 34, 62), (CX - 26, 18 - 20 * tall),
               (CX - 4, 54), (CX + 12, 10 - 24 * tall), (CX + 24, 56), (CX + 50, 26 - 14 * tall), (CX + 48, 66), (CX + 74, 60),
               (CX + 60, 88), (CX + 64, 118), (CX + 40, 92), (CX + 16, 102), (CX - 8, 86), (CX - 30, 100), (CX - 44, 90)]
        paint(ctx, lambda c: poly_path(c, pts), hair, lw=LW, hi_pos=(-0.25, -0.3))
    elif h == "short_messy":
        pts = [(CX - 60, 116), (CX - 64, 76), (CX - 40, 52), (CX - 10, 44), (CX + 26, 46), (CX + 56, 64), (CX + 64, 100),
               (CX + 58, 116), (CX + 46, 92), (CX + 30, 104), (CX + 18, 86), (CX - 4, 100), (CX - 18, 84), (CX - 40, 96)]
        paint(ctx, lambda c: smooth_closed(c, pts, 0.35), hair, lw=LW)
    elif h in ("long_flow", "long_straight"):
        pts = [(CX - 62, 124), (CX - 60, 80), (CX - 30, 56), (CX + 10, 52), (CX + 48, 62), (CX + 64, 92), (CX + 64, 126),
               (CX + 50, 100), (CX + 30, 82), (CX + 4, 92), (CX - 22, 80), (CX - 46, 98)]
        paint(ctx, lambda c: smooth_closed(c, pts, 0.45), hair, lw=LW)
    elif h == "ponytail":
        pts = [(CX - 60, 116), (CX - 58, 76), (CX - 24, 54), (CX + 22, 52), (CX + 56, 70), (CX + 62, 112), (CX + 44, 88),
               (CX + 10, 84), (CX - 20, 92), (CX - 44, 98)]
        paint(ctx, lambda c: smooth_closed(c, pts, 0.45), hair, lw=LW)
        paint(ctx, lambda c: ellipse_path(c, CX + 58, 82, 8, 8), hex2rgb(spec["trim"]), lw=3.5, hi=False)
    elif h == "bun":
        pts = [(CX - 60, 112), (CX - 56, 76), (CX - 20, 58), (CX + 20, 58), (CX + 56, 76), (CX + 60, 112), (CX + 40, 86),
               (CX, 80), (CX - 40, 86)]
        paint(ctx, lambda c: smooth_closed(c, pts, 0.5), hair, lw=LW)
        # feather pin
        paint(ctx, lambda c: smooth_closed(c, [(CX + 18, 40), (CX + 50, 12), (CX + 44, 36)], 0.6), hex2rgb(spec["second"]), lw=3.5, hi=False)
    elif h == "helm_visor":
        helm = light(main, 0.1)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 66, 130), (CX - 64, 70), (CX - 30, 46), (CX + 30, 46), (CX + 64, 70),
                                                 (CX + 66, 130), (CX + 50, 108), (CX - 50, 108)], 0.5), helm, lw=LW, hi_size=0.7)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 8, 46), (CX + 8, 46), (CX + 12, 18), (CX, 6), (CX - 12, 18)], 0.5), trim, lw=4)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 56, 100), (CX, 92), (CX + 56, 100)]), second, 6)
    elif h == "helm_horn":
        helm = shade(main, 0.15)
        for side in (-1, 1):
            paint(ctx, lambda c, side=side: smooth_closed(c, [(CX + side * 46, 78), (CX + side * 82, 54), (CX + side * 90, 24),
                                                               (CX + side * 68, 52), (CX + side * 50, 64)], 0.5), hex2rgb("#efe0c0"), lw=4.5)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 64, 112), (CX - 60, 70), (CX - 24, 50), (CX + 24, 50), (CX + 60, 70),
                                                 (CX + 64, 112), (CX + 40, 94), (CX - 40, 94)], 0.5), helm, lw=LW)
        flat(ctx, lambda c: rrect_path(c, CX - 56, 86, 112, 10, 5), hex2rgb(spec["trim"]))
        stroke(ctx, lambda c: rrect_path(c, CX - 56, 86, 112, 10, 5), INK, 3)
    elif h == "mohawk":
        pts = [(CX - 16, 70), (CX - 12, 30), (CX - 2, 8), (CX + 12, 2), (CX + 22, 22), (CX + 18, 60), (CX + 14, 74)]
        paint(ctx, lambda c: smooth_closed(c, pts, 0.5), hair, lw=LW)
    if spec.get("crown"):
        def crown(c):
            poly_path(c, [(CX - 40, 70), (CX - 34, 36), (CX - 20, 58), (CX - 8, 24), (CX, 50), (CX + 8, 24), (CX + 20, 58),
                          (CX + 34, 36), (CX + 40, 70), (CX, 78)])
        paint(ctx, crown, hex2rgb("#bff4ff"), lw=4.5, hi_size=0.7)
        sparkle(ctx, CX + 8, 34, 7)


def draw_scarf(ctx, spec, flutter=0):
    col = hex2rgb(spec["scarf"])
    paint(ctx, lambda c: smooth_closed(c, [(CX - 46, 154), (CX + 46, 154), (CX + 40, 176), (CX - 40, 176)], 0.4), col, lw=4.5)
    paint(ctx, lambda c: smooth_closed(c, [(CX + 30, 166), (CX + 86 + flutter, 168), (CX + 104 + flutter, 158), (CX + 92 + flutter, 184),
                                             (CX + 40, 182)], 0.5), col, lw=4.5)


def draw_cape(ctx, spec, lean=0):
    col = hex2rgb(spec["cape"])
    paint(ctx, lambda c: smooth_closed(c, [(CX - 50, 164), (CX + 50, 164), (CX + 84, 270), (CX + 50, 284), (CX, 276),
                                             (CX - 50, 284), (CX - 84, 270)], 0.5), shade(col, 0.15), lw=LW)


# ============================================================================ props

def draw_prop(ctx, spec, hand, pose, element):
    kind = spec["prop"]
    ec, ec2 = ELEMENT[element]
    hx, hy = hand
    trim = hex2rgb(spec["trim"])
    wood = hex2rgb("#8a5a34")
    metal = hex2rgb("#cfd6e6")
    if kind in ("ember_staff", "wave_staff", "ice_wand"):
        top = (hx + 10, hy - (150 if kind != "ice_wand" else 104))
        bottom = (hx - 4, hy + (40 if kind != "ice_wand" else 12))
        outlined_line(ctx, [bottom, top], wood if kind != "ice_wand" else hex2rgb("#a8c8f0"), 9, 16, smooth=False)
        if kind == "ember_staff":
            glow(ctx, top[0], top[1] - 6, 46, ec2, 0.7 if pose == "cast" else 0.45)
            paint(ctx, lambda c: smooth_closed(c, [(top[0] - 14, top[1] + 4), (top[0] + 14, top[1] + 4), (top[0] + 10, top[1] - 4),
                                                     (top[0], top[1] + 6)], 0.5), trim, lw=4, hi=False)
            paint(ctx, lambda c: ellipse_path(c, top[0], top[1] - 12, 16, 16), ec2, lw=4.5, hi_size=0.8)
            paint(ctx, lambda c: smooth_closed(c, [(top[0] - 8, top[1] - 14), (top[0], top[1] - 40), (top[0] + 9, top[1] - 16),
                                                     (top[0], top[1] - 4)], 0.6), ec, lw=3, hi=False)
        elif kind == "wave_staff":
            glow(ctx, top[0], top[1] - 6, 44, ec2, 0.55)
            paint(ctx, lambda c: smooth_closed(c, [(top[0] - 6, top[1] + 6), (top[0] - 22, top[1] - 12), (top[0] - 8, top[1] - 34),
                                                     (top[0] + 18, top[1] - 30), (top[0] + 22, top[1] - 10), (top[0] + 8, top[1] - 4),
                                                     (top[0] + 6, top[1] - 18), (top[0] - 4, top[1] - 14), (top[0] + 4, top[1] + 4)], 0.55),
                  ec, lw=4.5, hi_size=0.7)
            paint(ctx, lambda c: ellipse_path(c, top[0] + 1, top[1] - 18, 6, 6), ec2, lw=2.5, hi=False)
        else:
            glow(ctx, top[0], top[1], 38, ec2, 0.6)
            paint(ctx, lambda c: poly_path(c, [(top[0], top[1] - 26), (top[0] + 12, top[1]), (top[0], top[1] + 14), (top[0] - 12, top[1])]),
                  ec, lw=4, hi_size=0.8)
            sparkle(ctx, top[0] - 2, top[1] - 6, 7)
    elif kind == "flame_greatsword":
        ang = -1.1 if pose != "cast" else -0.35
        L = 150
        tip = (hx + math.cos(ang) * L, hy + math.sin(ang) * L)
        nx, ny = -math.sin(ang), math.cos(ang)
        base = (hx + math.cos(ang) * 22, hy + math.sin(ang) * 22)
        blade = [(base[0] + nx * 15, base[1] + ny * 15), (tip[0] + nx * 8, tip[1] + ny * 8), (tip[0] + math.cos(ang) * 22, tip[1] + math.sin(ang) * 22),
                 (tip[0] - nx * 8, tip[1] - ny * 8), (base[0] - nx * 15, base[1] - ny * 15)]
        glow(ctx, (base[0] + tip[0]) / 2, (base[1] + tip[1]) / 2, 70, ec, 0.35)
        paint(ctx, lambda c: poly_path(c, blade), hex2rgb("#3a3240"), lw=LW, hi_size=0.5)
        inner = [(base[0] + nx * 6, base[1] + ny * 6), (tip[0], tip[1]), (base[0] - nx * 6, base[1] - ny * 6)]
        flat(ctx, lambda c: poly_path(c, inner), ec2, 0.95)
        guard = [(base[0] + nx * 26, base[1] + ny * 26), (base[0] - nx * 26, base[1] - ny * 26)]
        outlined_line(ctx, guard, trim, 10, 17, smooth=False)
        outlined_line(ctx, [(hx - math.cos(ang) * 18, hy - math.sin(ang) * 18), base], wood, 9, 16, smooth=False)
    elif kind == "water_whips":
        for side, (sx, sy) in ((1, hand), (-1, (2 * CX - hx, hy))):
            pts = [(sx, sy), (sx + side * 22, sy + 12), (sx + side * 40, sy - 14), (sx + side * 52, sy + 8), (sx + side * 64, sy - 20)]
            if pose == "cast":
                pts = [(sx, sy), (sx + side * 18, sy - 28), (sx + side * 44, sy - 40), (sx + side * 58, sy - 70), (sx + side * 70, sy - 66)]
            outlined_line(ctx, pts, ec, 10, 17)
            outlined_line(ctx, pts[:-1], ec2, 4, 4)
            glow(ctx, pts[-1][0], pts[-1][1], 22, ec2, 0.6)
    elif kind == "conductor_rods":
        for i, (ox, oy) in enumerate(((-82, -40), (84, -60))):
            x, y = CX + ox, 170 + oy + (-20 if pose == "cast" else 0)
            glow(ctx, x, y - 30, 34, ec2, 0.55)
            outlined_line(ctx, [(x, y), (x + 4, y - 64)], metal, 9, 16, smooth=False)
            paint(ctx, lambda c, x=x, y=y: ellipse_path(c, x + 4, y - 70, 9, 9), ec2, lw=3.5, hi=False)
            paint(ctx, lambda c, x=x, y=y: rrect_path(c, x - 6, y - 4, 20, 10, 4), trim, lw=3, hi=False)
            stroke(ctx, lambda c, x=x, y=y: (c.move_to(x + 4, y - 80), c.line_to(x - 6, y - 92), c.line_to(x + 8, y - 100), c.line_to(x - 2, y - 114)),
                   ec2, 3.5)
    elif kind == "twin_daggers":
        for side, (sx, sy) in ((1, hand), (-1, (2 * CX - hx, hy))):
            ang = -0.9 if side > 0 else -2.25
            if pose == "cast":
                ang = -0.3 if side > 0 else -2.85
            tip = (sx + math.cos(ang) * 60, sy + math.sin(ang) * 60)
            nx, ny = -math.sin(ang), math.cos(ang)
            paint(ctx, lambda c, sx=sx, sy=sy, tip=tip, nx=nx, ny=ny: poly_path(c, [(sx + nx * 7, sy + ny * 7), tip, (sx - nx * 7, sy - ny * 7)]),
                  metal, lw=4.5, hi_size=0.6)
            stroke(ctx, lambda c, sx=sx, sy=sy, tip=tip: (c.move_to(sx, sy), c.line_to(tip[0], tip[1])), ec2, 2.5)
    elif kind == "tower_shield":
        sx, sy = 2 * CX - hx - 8, hy - 40
        glow(ctx, sx, sy, 80, ec2, 0.35)
        def shield(c):
            smooth_closed(c, [(sx - 38, sy - 62), (sx + 38, sy - 62), (sx + 44, sy + 20), (sx, sy + 72), (sx - 44, sy + 20)], 0.35)
        paint(ctx, shield, mix(ec, (1, 1, 1), 0.35), lw=LW, alpha=0.95, hi_size=0.8)
        paint(ctx, lambda c: smooth_closed(c, [(sx - 14, sy - 30), (sx + 14, sy - 30), (sx + 18, sy + 6), (sx, sy + 30), (sx - 18, sy + 6)], 0.4),
              ec2, lw=3.5, hi=False)
        sparkle(ctx, sx - 18, sy - 40, 9)
    elif kind == "fan":
        fx, fy = hx + 4, hy - 30 if pose != "cast" else hy - 50
        def fan(c):
            c.move_to(fx, fy + 34)
            c.arc(fx, fy + 34, 66, -math.pi * 0.95, -math.pi * 0.05)
            c.close_path()
        paint(ctx, fan, hex2rgb(spec["second"]), lw=LW, hi_size=0.6)
        for i in range(6):
            a = -math.pi * 0.95 + i * math.pi * 0.9 / 5
            stroke(ctx, lambda c, a=a: (c.move_to(fx, fy + 34), c.line_to(fx + math.cos(a) * 62, fy + 34 + math.sin(a) * 62)), INK, 2.5)
        flat(ctx, lambda c: (c.arc(fx, fy + 34, 26, -math.pi * 0.95, -math.pi * 0.05), c.line_to(fx, fy + 34), c.close_path()), ec2, 0.9)
    elif kind == "longbow":
        bx = 2 * CX - hx - 14
        top, bottom = (bx + 10, hy - 126), (bx + 10, hy + 56)
        def bow(c):
            smooth_open(c, [top, (bx - 30, hy - 40), (bx - 34, hy - 30), (bx - 30, hy - 20), bottom])
        stroke(ctx, bow, INK, 15)
        stroke(ctx, bow, wood, 8)
        stroke(ctx, lambda c: (c.move_to(*top), c.line_to(*bottom) if pose != "cast" else c.line_to(bx + 34, hy - 34)), hex2rgb("#f0f0f0"), 2.5)
        if pose == "cast":
            stroke(ctx, lambda c: (c.move_to(bx + 34, hy - 34), c.line_to(*bottom)), hex2rgb("#f0f0f0"), 2.5)
            outlined_line(ctx, [(bx + 36, hy - 34), (bx - 70, hy - 34)], hex2rgb("#e8e0d0"), 4, 9, smooth=False)
            glow(ctx, bx - 74, hy - 34, 26, ec2, 0.8)
    elif kind == "hammer":
        ang = -1.25 if pose != "cast" else -2.2
        head = (hx + math.cos(ang) * 112, hy + math.sin(ang) * 112)
        outlined_line(ctx, [(hx - math.cos(ang) * 22, hy - math.sin(ang) * 22), head], wood, 10, 17, smooth=False)
        ctx.save()
        ctx.translate(*head)
        ctx.rotate(ang + math.pi / 2)
        paint(ctx, lambda c: rrect_path(c, -40, -24, 80, 46, 10), hex2rgb("#8f8a86"), lw=LW, hi_size=0.6)
        paint(ctx, lambda c: rrect_path(c, -14, -26, 28, 50, 6), ec2, lw=3.5, hi=False)
        ctx.restore()
    elif kind == "gauntlets":
        for side, (sx, sy) in ((1, hand), (-1, (2 * CX - hx, hy))):
            glow(ctx, sx, sy, 34, ec2, 0.35 if pose != "cast" else 0.6)
            paint(ctx, lambda c, sx=sx, sy=sy: smooth_closed(c, [(sx - 26, sy - 18), (sx + 26, sy - 18), (sx + 30, sy + 14), (sx, sy + 28), (sx - 30, sy + 14)], 0.5),
                  hex2rgb("#8a8478"), lw=LW, hi_size=0.7)
            for k in range(3):
                paint(ctx, lambda c, sx=sx, sy=sy, k=k: ellipse_path(c, sx - 14 + k * 14, sy - 16, 6, 5), ec2, lw=2.5, hi=False)


# ============================================================================ assembly

def hero_sprite(hero_id, pose="idle", evo=None, size=W):
    spec = dict(HEROES[hero_id])
    element = spec["element"]
    ec, ec2 = ELEMENT[element]
    if evo == "A":
        spec["trim"] = "#ffd35a"
    elif evo == "B":
        spec["trim"] = "#%02x%02x%02x" % tuple(int(v * 255) for v in ec2)
    cv = Canvas(size, size, size / W)
    ctx = cv.ctx
    m = build_metrics(spec["build"])
    skin = SKIN[spec["skin"]]
    downed = pose == "downed"
    if downed:
        # lying on the ground: rotate the figure about its centre and shrink to fit the canvas
        ctx.translate(CX, 236)
        ctx.rotate(-1.45)
        ctx.scale(0.72, 0.72)
        ctx.translate(-CX, -180)
    lean = 6 if pose == "cast" else 0

    if evo:
        aura = ec2 if evo == "B" else hex2rgb("#ffd35a")
        glow(ctx, CX, 180, 150, aura, 0.38)
        if evo == "B":
            for side in (-1, 1):
                wing = [(CX + side * 30, 176), (CX + side * 120, 112), (CX + side * 142, 150), (CX + side * 118, 176),
                        (CX + side * 132, 206), (CX + side * 92, 210), (CX + side * 56, 214)]
                paint(ctx, lambda c, wing=wing: smooth_closed(c, wing, 0.45), mix(ec2, (1, 1, 1), 0.35), lw=4.5, alpha=0.9, hi_size=0.7)
        else:
            stroke(ctx, lambda c: ellipse_path(c, CX, 42, 48, 12), hex2rgb("#ffd35a"), 6)
            stroke(ctx, lambda c: ellipse_path(c, CX, 42, 48, 12), INK, 2)

    if spec.get("cape"):
        draw_cape(ctx, spec, lean)
    draw_hair_back(ctx, spec)

    # arms behind/in front depending on pose
    sleeve = hex2rgb(spec["main"]) if spec["outfit"] not in ("belted",) else skin
    if spec["outfit"] == "heavy_armor" or spec["outfit"] == "stone_armor":
        sleeve = shade(hex2rgb(spec["main"]), 0.1)
    left_sh = (CX - m["shoulder"] + 8 + lean, 182)
    right_sh = (CX + m["shoulder"] - 8 + lean, 182)
    if pose == "cast":
        left_hand = (CX - m["shoulder"] - 32, 150)
        right_hand = (CX + m["shoulder"] + 26, 124)
    else:
        left_hand = (CX - m["shoulder"] - 10, 236)
        right_hand = (CX + m["shoulder"] + 12, 230)

    draw_legs(ctx, spec, m, pose)
    draw_torso(ctx, spec, m, lean)
    if spec["prop"] in ("tower_shield", "longbow"):
        draw_arm(ctx, spec, m, left_sh, left_hand, sleeve, skin)
        draw_prop(ctx, spec, right_hand, pose, element)
        draw_arm(ctx, spec, m, right_sh, right_hand, sleeve, skin)
    else:
        draw_arm(ctx, spec, m, left_sh, left_hand, sleeve, skin)
        draw_arm(ctx, spec, m, right_sh, right_hand, sleeve, skin)

    # shoulder pads for armoured builds
    if spec["outfit"] in ("plate", "heavy_armor", "stone_armor"):
        pad = hex2rgb(spec["second"]) if spec["outfit"] != "heavy_armor" else light(hex2rgb(spec["main"]), 0.2)
        if spec["outfit"] == "stone_armor":
            pad = hex2rgb("#8f8a86")
        for side in (-1, 1):
            paint(ctx, lambda c, side=side: smooth_closed(c, [(CX + side * (m["shoulder"] - 30) + lean, 162), (CX + side * (m["shoulder"] + 14) + lean, 166),
                                                               (CX + side * (m["shoulder"] + 16) + lean, 196), (CX + side * (m["shoulder"] - 14) + lean, 192)], 0.5),
                  pad, lw=LW, hi_size=0.6)
    if spec.get("scarf"):
        draw_scarf(ctx, spec, 10 if pose == "cast" else 0)

    # head
    hx = CX + lean * 0.6
    ctx.save()
    ctx.translate(lean * 0.6, 0)
    paint(ctx, head_path(), skin, lw=LW, shade_dir=(0.5, 0.3), shade_amt=0.22, hi_pos=(-0.25, -0.25))
    if spec["head"] not in ("helm_visor",):
        draw_face(ctx, spec, mood="focus" if pose == "cast" else "calm", downed=downed)
    else:
        # visor slit with glowing eyes
        flat(ctx, lambda c: rrect_path(c, CX - 44, 108, 88, 22, 10), hex2rgb("#1b2440"))
        for side in (-1, 1):
            glow(ctx, CX + side * 18, 119, 14, ec2, 0.9)
            flat(ctx, lambda c, side=side: ellipse_path(c, CX + side * 18, 119, 6, 3.5), (1, 1, 1))
        paint(ctx, lambda c: smooth_closed(c, [(CX - 60, 130), (CX + 60, 130), (CX + 50, 158), (CX - 50, 158)], 0.4), light(hex2rgb(spec["main"]), 0.1), lw=LW)
    if spec.get("mask"):
        paint(ctx, lambda c: smooth_closed(c, [(CX - 50, 128), (CX + 50, 128), (CX + 40, 160), (CX, 166), (CX - 40, 160)], 0.4),
              hex2rgb(spec["main"]), lw=LW - 1)
    draw_hair_front(ctx, spec, ec)
    ctx.restore()

    if spec["prop"] not in ("tower_shield", "longbow"):
        draw_prop(ctx, spec, right_hand, pose, element)

    if pose == "cast":
        glow(ctx, left_hand[0], left_hand[1], 40, ec2, 0.75)
        sparkle(ctx, left_hand[0] - 12, left_hand[1] - 18, 10)
        sparkle(ctx, left_hand[0] + 16, left_hand[1] - 6, 6)
    if evo:
        emblem_col = hex2rgb("#ffd35a") if evo == "A" else ec2
        paint(ctx, lambda c: star_path(c, CX + lean, 196, 13, 6, 5) if evo == "A" else poly_path(c, [(CX + lean, 182), (CX + 10 + lean, 196), (CX + lean, 210), (CX - 10 + lean, 196)]),
              emblem_col, lw=3.5, hi=False)
    if downed:
        ctx.identity_matrix()
        for i in range(3):
            a = i * 2.1 + 0.4
            sparkle(ctx, 96 + math.cos(a) * 30, 214 + math.sin(a) * 10, 9, hex2rgb("#ffe46a"))
        # desaturate the whole sprite for a clear "downed" read
        img = cv.surface
        desaturate(img, 0.55)
    return cv


def desaturate(surface, amount):
    import array
    surface.flush()
    w, h, stride = surface.get_width(), surface.get_height(), surface.get_stride()
    buf = surface.get_data()
    for y in range(h):
        row = y * stride
        for x in range(w):
            i = row + x * 4
            b, g, r, a = buf[i], buf[i + 1], buf[i + 2], buf[i + 3]
            if a == 0:
                continue
            l = int(0.3 * r + 0.59 * g + 0.11 * b)
            buf[i] = int(b + (l * 0.9 - b) * amount)
            buf[i + 1] = int(g + (l * 0.9 - g) * amount)
            buf[i + 2] = int(r + (l - r) * amount)
    surface.mark_dirty()


def portrait(hero_id, size=192):
    """Head-and-shoulders badge from the idle pose, framed with the element colour."""
    src = hero_sprite(hero_id, "idle", None, 320).surface
    ec, ec2 = ELEMENT[HEROES[hero_id]["element"]]
    cv = Canvas(size, size)
    ctx = cv.ctx
    r = size / 2 - 6
    grad = cairo.RadialGradient(size / 2, size * 0.35, 4, size / 2, size / 2, r)
    grad.add_color_stop_rgb(0, *light(ec2, 0.3))
    grad.add_color_stop_rgb(1, *shade(ec, 0.35))
    ctx.arc(size / 2, size / 2, r, 0, 2 * math.pi)
    ctx.set_source(grad)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    s = size / 210.0
    ctx.scale(s, s)
    ctx.set_source_surface(src, -(160 - 105), -20)
    ctx.paint()
    ctx.restore()
    ctx.arc(size / 2, size / 2, r, 0, 2 * math.pi)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(8)
    ctx.stroke()
    ctx.arc(size / 2, size / 2, r - 6, 0, 2 * math.pi)
    ctx.set_source_rgba(*ec2, 0.9)
    ctx.set_line_width(3)
    ctx.stroke()
    return cv
