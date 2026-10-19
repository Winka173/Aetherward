"""Procedural hero sprites: 20 humanoid heroes x (idle, cast, downed, evolution A, evolution B) + portraits.

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
    "light": (hex2rgb("#ffd84a"), hex2rgb("#fff7cc")),
    "shadow": (hex2rgb("#a3306b"), hex2rgb("#3a0f2c")),
    "nature": (hex2rgb("#3fa34d"), hex2rgb("#b6ec6a")),
    "poison": (hex2rgb("#a8e030"), hex2rgb("#6a2a9a")),
    "arcane": (hex2rgb("#ff5fd2"), hex2rgb("#ffd6f6")),
    "void": (hex2rgb("#5146d9"), hex2rgb("#140c38")),
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
    # ---- expansion heroes (parts defined in the "expansion parts" section at the end of this file)
    "seren": dict(element="light", skin="tan", build="broad", outfit="tabard", head="sun_helm", hair="#7a4a24",
                  main="#c3cadb", second="#e8b730", trim="#fff1b8", prop="sun_shield_sword", eyes="#6a4a10", tabard="#fff6dc"),
    "nyxara": dict(element="shadow", skin="fair", build="slim", outfit="long_cloak", head="crescent_hood", hair="#2a1030",
                   main="#2e1d40", second="#a3306b", trim="#f0cfe2", prop="chain_staff", eyes="#c0204a"),
    "ashara": dict(element="fire", skin="brown", build="broad", outfit="phoenix_plate", head="plume_helm", hair="#3a1a10",
                   main="#8a2228", second="#ff8a2a", trim="#ffd24a", prop="flame_sabre", eyes="#3a1408"),
    "nerissa": dict(element="water", skin="deep", build="slim", outfit="sea_robe", head="pearl_veil", hair="#2c2c66",
                    main="#3fc2a2", second="#1f7a8c", trim="#fff4ea", prop="conch_staff", eyes="#1a4a5a"),
    "voltrix": dict(element="lightning", skin="light", build="normal", outfit="engineer", head="goggles_messy", hair="#ff8a2a",
                    main="#3c4a6c", second="#ffd23a", trim="#ffe14a", prop="wrench_staff", eyes="#2a2050", backpack="coils"),
    "eirwen": dict(element="ice", skin="brown", build="broad", outfit="frost_plate", head="winged_helm", hair="#f2f6ff",
                   main="#e4f1ff", second="#6fa6e0", trim="#bff4ff", prop="crystal_shield_mace", eyes="#1a3a6a"),
    "kael": dict(element="wind", skin="light", build="lean", outfit="wraps", head="topknot", hair="#1c1c28",
                 main="#2c3c4c", second="#e9e3cf", trim="#2fd39a", prop="war_fans", eyes="#173a22", sash="#2fd39a"),
    "borun": dict(element="earth", skin="deep", build="huge", outfit="apron", head="flat_cap", hair="#b0582a",
                  main="#5a7a9a", second="#7a5030", trim="#e0b060", prop="stone_gauntlet", eyes="#2a160a",
                  cap="#6e6a5c", backpack="plans"),
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
    if o in EXT_TORSO_SHAPES:
        return ext_torso_path(o, s, w, hp, top, lean)
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
    elif o in EXT_OUTFITS:
        ext_torso_detail(ctx, spec, m, lean)
    ctx.restore()
    if o in EXT_OUTFITS:
        ext_torso_overlay(ctx, spec, m, lean)


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
    elif h in EXT_HEADS:
        ext_hair_back(ctx, spec)


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
    elif h in EXT_HEADS:
        ext_hair_front(ctx, spec, element_color)
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
    elif kind in EXT_PROPS:
        ext_prop(ctx, spec, hand, pose, element)


# ============================================================================ assembly

BETWEEN_ARMS_PROPS = ("tower_shield", "longbow", "sun_shield_sword", "crystal_shield_mace")


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
    ext_back_items(ctx, spec, pose, lean)
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
    if spec["prop"] in BETWEEN_ARMS_PROPS:
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
    elif spec["outfit"] in EXT_OUTFITS:
        ext_shoulders(ctx, spec, m, lean)
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

    if spec["prop"] not in BETWEEN_ARMS_PROPS:
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


# ============================================================================ expansion parts
# New head / outfit / prop / back-item kinds used by the expansion heroes (seren, nyxara, ashara, nerissa,
# voltrix, eirwen, kael, borun). The original drawing functions dispatch here through the EXT_* sets.

EXT_HEADS = ("sun_helm", "crescent_hood", "plume_helm", "pearl_veil", "goggles_messy", "winged_helm", "topknot", "flat_cap")
EXT_OUTFITS = ("tabard", "long_cloak", "phoenix_plate", "sea_robe", "engineer", "frost_plate", "wraps", "apron")
EXT_TORSO_SHAPES = ("long_cloak", "sea_robe")
EXT_PROPS = ("sun_shield_sword", "chain_staff", "flame_sabre", "conch_staff", "wrench_staff", "crystal_shield_mace",
             "war_fans", "stone_gauntlet")

STONE = hex2rgb("#8f8a86")
BRASS = hex2rgb("#d9a441")
COPPER = hex2rgb("#d9803a")


def hands_for(spec, pose):
    """(left_hand, right_hand) exactly as hero_sprite places them."""
    m = build_metrics(spec["build"])
    if pose == "cast":
        return (CX - m["shoulder"] - 32, 150), (CX + m["shoulder"] + 26, 124)
    return (CX - m["shoulder"] - 10, 236), (CX + m["shoulder"] + 12, 230)


def ext_torso_path(o, s, w, hp, top, lean):
    if o == "long_cloak":
        bottom = GROUND - 10
        pts = [(CX - s * 0.6 + lean, top - 4), (CX + s * 0.6 + lean, top - 4), (CX + s + 10 + lean * 0.6, top + 22),
               (CX + hp + 22, bottom - 20), (CX + hp + 34, bottom + 2), (CX + 20, bottom - 4), (CX - 6, bottom + 4),
               (CX - hp - 30, bottom), (CX - hp - 22, bottom - 22), (CX - s - 10 + lean * 0.6, top + 22)]
        return lambda c: smooth_closed(c, pts, 0.4)
    # sea_robe: flowing robe with a scalloped, wave-like hem that trails to one side
    bottom = GROUND - 6
    pts = [(CX - s * 0.62 + lean, top), (CX + s * 0.62 + lean, top), (CX + s + lean * 0.6, top + 16), (CX + w + 2, 214),
           (CX + hp + 22, bottom - 18), (CX + hp + 40, bottom + 2), (CX + hp + 10, bottom - 6), (CX + 22, bottom + 4),
           (CX + 4, bottom - 6), (CX - 18, bottom + 4), (CX - hp - 18, bottom - 4), (CX - hp - 8, bottom - 22),
           (CX - w - 2, 214), (CX - s + lean * 0.6, top + 16)]
    return lambda c: smooth_closed(c, pts, 0.45)


def ext_torso_detail(ctx, spec, m, lean):
    """Detail painted inside the torso clip."""
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    o = spec["outfit"]
    if o == "tabard":
        # plate under the tabard: segmented chest plates showing at the sides
        for side in (-1, 1):
            for i in range(3):
                y = 186 + i * 16
                stroke(ctx, lambda c, side=side, y=y: (c.move_to(CX + side * 26, y), c.line_to(CX + side * 56, y + 4)), shade(main, 0.35), 3)
        flat(ctx, lambda c: rrect_path(c, CX - 60, 232, 120, 12, 5), second)
        stroke(ctx, lambda c: rrect_path(c, CX - 60, 232, 120, 12, 5), INK, 3)
    elif o == "long_cloak":
        # crimson lining showing through the front split, and a dark inner dress
        flat(ctx, lambda c: poly_path(c, [(CX - 8 + lean, 168), (CX + 8 + lean, 168), (CX + 40, 300), (CX - 40, 300)]), second)
        flat(ctx, lambda c: poly_path(c, [(CX - 2 + lean, 176), (CX + 2 + lean, 176), (CX + 24, 300), (CX - 24, 300)]), shade(main, 0.4))
        for side in (-1, 1):
            stroke(ctx, lambda c, side=side: (c.move_to(CX + side * 8 + lean, 168), c.line_to(CX + side * 40, 300)), INK, 3.5)
        # sigil stitching on the cloak edge
        stroke(ctx, lambda c: smooth_open(c, [(CX - 70, 270), (CX - 30, 282), (CX + 10, 278), (CX + 60, 288)]), trim, 3, 0.7)
    elif o == "phoenix_plate":
        paint(ctx, lambda c: smooth_closed(c, [(CX - 34, 176), (CX + 34, 176), (CX + 30, 222), (CX, 236), (CX - 30, 222)], 0.4),
              shade(main, 0.25), lw=4, hi_size=0.6)
        # flame emblem on the breastplate
        paint(ctx, lambda c: smooth_closed(c, [(CX, 186), (CX + 10, 202), (CX + 14, 214), (CX, 226), (CX - 14, 214),
                                                 (CX - 8, 200)], 0.5), second, lw=3, hi=False)
        flat(ctx, lambda c: smooth_closed(c, [(CX, 202), (CX + 6, 214), (CX, 222), (CX - 6, 214)], 0.5), trim)
        flat(ctx, lambda c: rrect_path(c, CX - 60, 232, 120, 12, 5), trim)
        stroke(ctx, lambda c: rrect_path(c, CX - 60, 232, 120, 12, 5), INK, 3)
    elif o == "sea_robe":
        flat(ctx, lambda c: poly_path(c, [(CX - 10 + lean * 0.3, 166), (CX + 10 + lean * 0.3, 166), (CX + 34, 300), (CX - 26, 300)]), second)
        stroke(ctx, lambda c: (c.move_to(CX - 10 + lean * 0.3, 166), c.line_to(CX - 26, 300)), INK, 3)
        stroke(ctx, lambda c: (c.move_to(CX + 10 + lean * 0.3, 166), c.line_to(CX + 34, 300)), INK, 3)
        # foam-wave pattern around the hem
        for k, y in enumerate((258, 272)):
            pts = [(CX - 90 + i * 15, y + (-5 if (i + k) % 2 else 5)) for i in range(13)]
            stroke(ctx, lambda c, pts=pts: smooth_open(c, pts), light(main, 0.55), 4)
        flat(ctx, lambda c: rrect_path(c, CX - 60, 214, 120, 12, 6), trim)
        stroke(ctx, lambda c: rrect_path(c, CX - 60, 214, 120, 12, 6), INK, 3)
        paint(ctx, lambda c: ellipse_path(c, CX + 4, 220, 8, 8), hex2rgb("#ffffff"), lw=3, hi_size=0.6)
    elif o == "engineer":
        # backpack straps, toolbelt with pouches
        for side in (-1, 1):
            flat(ctx, lambda c, side=side: rrect_path(c, CX + side * 26 - 6, 160, 12, 70, 4), hex2rgb("#3a2a20"))
            stroke(ctx, lambda c, side=side: rrect_path(c, CX + side * 26 - 6, 160, 12, 70, 4), INK, 2.5)
            paint(ctx, lambda c, side=side: rrect_path(c, CX + side * 26 - 7, 192, 14, 9, 3), BRASS, lw=2.5, hi=False)
        flat(ctx, lambda c: rrect_path(c, CX - 60, 222, 120, 14, 6), hex2rgb("#6a4428"))
        stroke(ctx, lambda c: rrect_path(c, CX - 60, 222, 120, 14, 6), INK, 3)
        for x in (CX - 36, CX + 24):
            paint(ctx, lambda c, x=x: rrect_path(c, x - 2, 230, 18, 20, 4), hex2rgb("#8a5a34"), lw=3, hi=False)
        paint(ctx, lambda c: rrect_path(c, CX - 10, 220, 20, 18, 4), BRASS, lw=3, hi=False)
        # lightning-bolt patch
        paint(ctx, lambda c: poly_path(c, [(CX - 4, 176), (CX + 10, 176), (CX + 2, 192), (CX + 12, 192), (CX - 6, 212),
                                             (CX - 1, 196), (CX - 10, 196)]), second, lw=2.5, hi=False, shade_amt=0)
    elif o == "frost_plate":
        paint(ctx, lambda c: smooth_closed(c, [(CX - 36, 176), (CX + 36, 176), (CX + 32, 224), (CX, 238), (CX - 32, 224)], 0.4),
              light(second, 0.35), lw=4, hi_size=0.6)
        # frost facets on the breastplate
        for (a, b) in (((CX, 182), (CX, 232)), ((CX - 30, 196), (CX, 210)), ((CX + 30, 196), (CX, 210))):
            stroke(ctx, lambda c, a=a, b=b: (c.move_to(*a), c.line_to(*b)), (1, 1, 1), 3, 0.8)
        flat(ctx, lambda c: rrect_path(c, CX - 60, 234, 120, 12, 5), second)
        stroke(ctx, lambda c: rrect_path(c, CX - 60, 234, 120, 12, 5), INK, 3)
    elif o == "wraps":
        # light cloth wraps crossing the chest
        wrap = second
        for side in (-1, 1):
            flat(ctx, lambda c, side=side: poly_path(c, [(CX + side * 40, 164), (CX + side * 24, 164), (CX - side * 34, 226),
                                                          (CX - side * 18, 226)]), wrap)
            stroke(ctx, lambda c, side=side: (c.move_to(CX + side * 40, 164), c.line_to(CX - side * 18, 226)), INK, 2.5)
            stroke(ctx, lambda c, side=side: (c.move_to(CX + side * 24, 164), c.line_to(CX - side * 34, 226)), INK, 2.5)
    elif o == "apron":
        # rolled shirt with a button placket
        stroke(ctx, lambda c: (c.move_to(CX, 166), c.line_to(CX, 200)), shade(main, 0.4), 3)


def ext_torso_overlay(ctx, spec, m, lean):
    """Garment parts that hang outside the torso silhouette (drawn over it)."""
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    o = spec["outfit"]
    x0 = CX + lean * 0.3
    if o == "tabard":
        tab = hex2rgb(spec.get("tabard", "#fff6dc"))
        paint(ctx, lambda c: smooth_closed(c, [(x0 - 24, 172), (x0 + 24, 172), (x0 + 26, 270), (x0, 280), (x0 - 26, 270)], 0.2),
              tab, lw=LW - 1, hi_size=0.5)
        stroke(ctx, lambda c: smooth_closed(c, [(x0 - 16, 180), (x0 + 16, 180), (x0 + 18, 262), (x0, 270), (x0 - 18, 262)], 0.2), second, 3.5)
        flat(ctx, lambda c: rrect_path(c, x0 - 26, 232, 52, 12, 4), second)
        stroke(ctx, lambda c: rrect_path(c, x0 - 26, 232, 52, 12, 4), INK, 3)
        paint(ctx, lambda c: star_path(c, x0, 204, 15, 9, 8), hex2rgb("#ffd84a"), lw=3, hi=False)
        paint(ctx, lambda c: ellipse_path(c, x0, 204, 7, 7), hex2rgb("#fff7cc"), lw=2.5, hi=False, shade_amt=0)
    elif o == "long_cloak":
        # tall collar points + moon clasp
        for side in (-1, 1):
            paint(ctx, lambda c, side=side: smooth_closed(c, [(CX + side * 8 + lean, 168), (CX + side * 44 + lean, 156),
                                                               (CX + side * 58 + lean, 172), (CX + side * 34 + lean, 184)], 0.4),
                  shade(main, 0.15), lw=4.5, hi=False)
        paint(ctx, lambda c: ellipse_path(c, CX + lean, 174, 10, 10), trim, lw=3.5, hi_size=0.6)
        flat(ctx, lambda c: ellipse_path(c, CX + 4 + lean, 171, 7, 7), shade(main, 0.15))
    elif o == "sea_robe":
        # shell pendant
        paint(ctx, lambda c: smooth_closed(c, [(x0 - 10, 176), (x0 + 10, 176), (x0 + 6, 190), (x0, 194), (x0 - 6, 190)], 0.5),
              hex2rgb("#ffc8c0"), lw=3, hi_size=0.6)
    elif o == "frost_plate":
        # fluffy snow-fur collar
        fur = hex2rgb("#f6fbff")
        for i in range(7):
            t = i / 6.0
            x = CX - 48 + 96 * t + lean
            y = 168 + 6 * math.sin(t * math.pi)
            paint(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 16, 13), fur if i % 2 == 0 else light(hex2rgb("#cfe8ff"), 0.4),
                  lw=4, hi=False, shade_amt=0.15)
        # armoured faulds below the belt
        for side in (-1, 1):
            paint(ctx, lambda c, side=side: smooth_closed(c, [(CX + side * 8, 244), (CX + side * 50, 244), (CX + side * 54, 266),
                                                               (CX + side * 12, 270)], 0.3), light(main, 0.1), lw=4.5, hi=False)
    elif o == "wraps":
        sash = hex2rgb(spec.get("sash", spec["trim"]))
        # neck scarf wrap
        paint(ctx, lambda c: smooth_closed(c, [(CX - 40 + lean, 156), (CX + 40 + lean, 156), (CX + 36 + lean, 176), (CX - 36 + lean, 176)], 0.4),
              sash, lw=4.5)
        # waist sash with a side knot
        paint(ctx, lambda c: smooth_closed(c, [(CX - 40, 222), (CX + 40, 222), (CX + 42, 240), (CX - 42, 240)], 0.3), sash, lw=4.5)
        paint(ctx, lambda c: ellipse_path(c, CX - 30, 232, 9, 9), light(sash, 0.2), lw=3.5, hi=False)
    elif o == "apron":
        leather = second
        for side in (-1, 1):
            outlined_line(ctx, [(x0 + side * 28, 194), (x0 + side * 22, 164)], shade(leather, 0.2), 6, 11, smooth=False)
        paint(ctx, lambda c: rrect_path(c, x0 - 38, 190, 76, 90, 12), leather, lw=LW - 1, hi_size=0.5)
        stroke(ctx, lambda c: rrect_path(c, x0 - 32, 196, 64, 78, 9), trim, 2.2, 0.8)
        paint(ctx, lambda c: rrect_path(c, x0 - 22, 230, 44, 26, 6), shade(leather, 0.25), lw=3.5, hi=False)
        # chisel and pencil poking out of the pocket
        outlined_line(ctx, [(x0 - 10, 232), (x0 - 14, 214)], hex2rgb("#cfd6e6"), 5, 10, smooth=False)
        outlined_line(ctx, [(x0 + 8, 232), (x0 + 12, 218)], hex2rgb("#ffd23a"), 5, 10, smooth=False)
        flat(ctx, lambda c: rrect_path(c, x0 - 56, 222, 18, 12, 4), shade(leather, 0.3))


def ext_shoulders(ctx, spec, m, lean):
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    o = spec["outfit"]
    s = m["shoulder"]
    if o in ("tabard", "frost_plate"):
        pad = second if o == "tabard" else light(main, 0.15)
        for side in (-1, 1):
            if o == "frost_plate":
                # ice shard spikes rising off the pauldron
                for k, (dx, h) in enumerate(((-6, 30), (8, 40), (20, 26))):
                    bx = CX + side * (s - 6 + dx) + lean
                    paint(ctx, lambda c, bx=bx, h=h: poly_path(c, [(bx - 7, 172), (bx + side * 4, 172 - h), (bx + 7, 172)]),
                          light(hex2rgb("#7fd8ff"), 0.3 + 0.2 * (k % 2)), lw=3.5, hi=False)
            paint(ctx, lambda c, side=side: smooth_closed(c, [(CX + side * (s - 32) + lean, 160), (CX + side * (s + 16) + lean, 164),
                                                               (CX + side * (s + 20) + lean, 198), (CX + side * (s - 14) + lean, 194)], 0.5),
                  pad, lw=LW, hi_size=0.6)
            if o == "tabard":
                stroke(ctx, lambda c, side=side: smooth_open(c, [(CX + side * (s - 22) + lean, 172), (CX + side * (s + 12) + lean, 178)]),
                       light(pad, 0.5), 3)
    elif o == "phoenix_plate":
        ec, ec2 = ELEMENT[spec["element"]]
        for side in (-1, 1):
            ox, oy = CX + side * (s - 8) + lean, 172
            glow(ctx, ox + side * 30, oy - 20, 50, ec2, 0.35)
            # fan of flame feathers sweeping up and out
            for k in range(4):
                a = -math.pi / 2 + side * (0.45 + k * 0.32)
                L = 92 - k * 12
                tip = (ox + math.cos(a) * L, oy + math.sin(a) * L)
                nx, ny = -math.sin(a), math.cos(a)
                mid = (ox + math.cos(a) * L * 0.5, oy + math.sin(a) * L * 0.5)
                pts = [(ox + nx * 7, oy + ny * 7), (mid[0] + nx * 15, mid[1] + ny * 15), tip,
                       (mid[0] - nx * 15, mid[1] - ny * 15), (ox - nx * 7, oy - ny * 7)]
                col = ec if k % 2 == 0 else second
                paint(ctx, lambda c, pts=pts: smooth_closed(c, pts, 0.45), col, lw=4, hi=False)
                flat(ctx, lambda c, mid=mid, tip=tip, nx=nx, ny=ny: poly_path(c, [(mid[0] + nx * 5, mid[1] + ny * 5), tip,
                                                                                   (mid[0] - nx * 5, mid[1] - ny * 5)]), ec2, 0.9)
            paint(ctx, lambda c, side=side: smooth_closed(c, [(CX + side * (s - 30) + lean, 160), (CX + side * (s + 12) + lean, 164),
                                                               (CX + side * (s + 16) + lean, 196), (CX + side * (s - 14) + lean, 192)], 0.5),
                  shade(main, 0.1), lw=LW, hi_size=0.6)
            stroke(ctx, lambda c, side=side: smooth_open(c, [(CX + side * (s - 24) + lean, 174), (CX + side * (s + 10) + lean, 178)]), trim, 4)


def ext_back_items(ctx, spec, pose, lean):
    """Things worn on the back / trailing behind the body (drawn before hair-back and torso)."""
    ec, ec2 = ELEMENT[spec["element"]]
    bp = spec.get("backpack")
    if bp == "coils":
        paint(ctx, lambda c: rrect_path(c, CX - 52, 150, 104, 72, 14), hex2rgb("#4a4a58"), lw=LW)
        for side in (-1, 1):
            x = CX + side * 92
            if pose == "cast":
                glow(ctx, x, 70, 46, ec2, 0.7)
            else:
                glow(ctx, x, 70, 30, ec2, 0.45)
            outlined_line(ctx, [(CX + side * 40, 170), (x, 150), (x, 78)], hex2rgb("#5a5a6a"), 10, 17, smooth=False)
            for k in range(5):
                y = 140 - k * 12
                paint(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 13, 5), COPPER, lw=3, hi=False)
            paint(ctx, lambda c, x=x: ellipse_path(c, x, 70, 11, 11), ec2, lw=3.5, hi_size=0.6)
            zig = [(x + side * 4, 60), (x - side * 6, 50), (x + side * 8, 42), (x, 30)]
            stroke(ctx, lambda c, zig=zig: (c.move_to(*zig[0]), [c.line_to(*p) for p in zig[1:]]), ec2, 3.5)
        if pose == "cast":
            # arc jumping between the two coil tips, over the head
            pts = [(CX - 92, 66), (CX - 62, 40), (CX - 30, 54), (CX, 22), (CX + 30, 50), (CX + 62, 34), (CX + 92, 66)]
            stroke(ctx, lambda c: (c.move_to(*pts[0]), [c.line_to(*p) for p in pts[1:]]), ec, 7)
            stroke(ctx, lambda c: (c.move_to(*pts[0]), [c.line_to(*p) for p in pts[1:]]), ec2, 3)
    elif bp == "plans":
        # rolled blueprints in a leather tube, slung diagonally across the back
        a, b = (CX + 40, 222), (CX - 98, 74)
        outlined_line(ctx, [a, b], hex2rgb("#7a5030"), 26, 34, smooth=False)
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        ex, ey = b[0] - math.cos(ang) * 4, b[1] - math.sin(ang) * 4
        paint(ctx, lambda c: ellipse_path(c, ex, ey, 15, 10, ang + math.pi / 2), hex2rgb("#f0e4c4"), lw=4, hi=False)
        # rolled-paper spiral peeking out of the open end
        stroke(ctx, lambda c: ellipse_path(c, ex, ey, 7, 4.5, ang + math.pi / 2), hex2rgb("#4a7ac8"), 2.5)
        for t in (0.72, 0.5):
            px, py = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            outlined_line(ctx, [(px - math.sin(ang) * 15, py + math.cos(ang) * 15), (px + math.sin(ang) * 15, py - math.cos(ang) * 15)],
                          BRASS, 5, 10, smooth=False)
    if spec.get("sash"):
        sash = hex2rgb(spec["sash"])
        fl = 14 if pose == "cast" else 0
        # long scarf tail streaming off the neck in the wind
        paint(ctx, lambda c: smooth_closed(c, [(CX - 20, 158), (CX - 70, 142 - fl), (CX - 112, 112 - fl * 1.5), (CX - 146, 118 - fl * 2),
                                                 (CX - 128, 132 - fl), (CX - 138, 150 - fl), (CX - 96, 148 - fl), (CX - 56, 174),
                                                 (CX - 20, 176)], 0.45), sash, lw=4.5, hi_size=0.6)
        # two sash ends trailing from the waist knot
        for k in range(2):
            dy = k * 18
            paint(ctx, lambda c, dy=dy: smooth_closed(c, [(CX - 40, 226 + dy * 0.3), (CX - 80, 236 + dy - fl * 0.5),
                                                           (CX - 118 + dy, 222 + dy * 1.4 - fl), (CX - 108 + dy, 240 + dy * 1.4 - fl),
                                                           (CX - 76, 252 + dy), (CX - 40, 240 + dy * 0.3)], 0.45),
                  shade(sash, 0.1 * k), lw=4.5, hi=False)


def ext_hair_back(ctx, spec):
    hair = hex2rgb(spec["hair"])
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    ec, ec2 = ELEMENT[spec["element"]]
    h = spec["head"]
    if h == "sun_helm":
        # radiant sun disc standing behind the helm
        glow(ctx, CX, 106, 124, ec, 0.45)
        paint(ctx, lambda c: star_path(c, CX, 106, 100, 78, 12, rot=-math.pi / 2), ec, lw=4.5, hi=False)
        paint(ctx, lambda c: star_path(c, CX, 106, 92, 74, 12, rot=-math.pi / 2 + math.pi / 12), light(ec, 0.35), lw=3.5, hi=False)
        paint(ctx, lambda c: ellipse_path(c, CX, 106, 80, 80), ec2, lw=LW, hi_size=0.6)
        stroke(ctx, lambda c: ellipse_path(c, CX, 106, 71, 71), ec, 4)
    elif h == "crescent_hood":
        paint(ctx, lambda c: smooth_closed(c, [(CX - 72, 162), (CX - 78, 100), (CX - 62, 56), (CX, 44), (CX + 62, 56),
                                                 (CX + 78, 100), (CX + 72, 162), (CX, 172)], 0.5), shade(main, 0.25), lw=LW)
    elif h == "pearl_veil":
        veil = light(ec2, 0.55)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 52, 70), (CX + 52, 70), (CX + 84, 150), (CX + 98, 240), (CX + 70, 232),
                                                 (CX + 40, 250), (CX - 40, 250), (CX - 72, 234), (CX - 98, 240), (CX - 84, 150)], 0.5),
              veil, lw=4, alpha=0.6, hi=False)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 60, 96), (CX + 60, 96), (CX + 72, 150), (CX + 80, 206), (CX + 58, 196),
                                                 (CX + 66, 220), (CX + 36, 206), (CX - 36, 206), (CX - 64, 222), (CX - 58, 196),
                                                 (CX - 80, 206), (CX - 72, 150)], 0.5), hair, lw=LW)
    elif h == "topknot":
        # ribbon tails, then the knot itself (its base is hidden by the front hair)
        for k, dy in enumerate((0, 14)):
            paint(ctx, lambda c, dy=dy: smooth_closed(c, [(CX + 8, 46), (CX + 50, 34 + dy), (CX + 86, 46 + dy * 1.6), (CX + 70, 56 + dy * 1.4),
                                                           (CX + 44, 50 + dy), (CX + 10, 58)], 0.5), shade(trim, 0.12 * k), lw=4, hi=False)
        paint(ctx, lambda c: ellipse_path(c, CX, 40, 20, 18), hair, lw=LW)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 8, 26), (CX - 2, 6), (CX + 10, 2), (CX + 8, 24)], 0.5), hair, lw=4.5)


def ext_hair_front(ctx, spec, element_color):
    hair = hex2rgb(spec["hair"])
    main, second, trim = hex2rgb(spec["main"]), hex2rgb(spec["second"]), hex2rgb(spec["trim"])
    ec, ec2 = ELEMENT[spec["element"]]
    h = spec["head"]
    if h == "sun_helm":
        # short hair at the temples, open-faced gilded helm with a sun gem
        for side in (-1, 1):
            paint(ctx, lambda c, side=side: smooth_closed(c, [(CX + side * 64, 124), (CX + side * 58, 92), (CX + side * 40, 96),
                                                               (CX + side * 50, 120)], 0.4), hair, lw=4.5, hi=False)
        helm = hex2rgb(spec["main"])
        paint(ctx, lambda c: smooth_closed(c, [(CX - 64, 112), (CX - 60, 68), (CX - 26, 48), (CX + 26, 48), (CX + 60, 68),
                                                 (CX + 64, 112), (CX + 42, 94), (CX - 42, 94)], 0.5), helm, lw=LW, hi_size=0.7)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 56, 98), (CX - 30, 86), (CX, 82), (CX + 30, 86), (CX + 56, 98)]), second, 6)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 6, 50), (CX + 6, 50), (CX + 8, 30), (CX, 20), (CX - 8, 30)], 0.5), second, lw=4)
        paint(ctx, lambda c: star_path(c, CX, 70, 14, 7, 8), ec, lw=3, hi=False)
        paint(ctx, lambda c: ellipse_path(c, CX, 70, 6, 6), ec2, lw=2.5, hi=False, shade_amt=0)
    elif h == "crescent_hood":
        def hood(c):
            smooth_closed(c, [(CX - 64, 126), (CX - 68, 82), (CX - 72, 46), (CX - 60, 20), (CX - 26, 8), (CX - 42, 24),
                              (CX - 46, 42), (CX - 22, 56), (CX, 58), (CX + 22, 56), (CX + 46, 42), (CX + 42, 20),
                              (CX + 26, 8), (CX + 60, 20), (CX + 72, 46), (CX + 68, 82),
                              (CX + 64, 126), (CX + 46, 94), (CX, 82), (CX - 46, 94)], 0.35)
        paint(ctx, hood, main, lw=LW, hi_pos=(-0.2, -0.25))
        stroke(ctx, lambda c: smooth_open(c, [(CX - 60, 110), (CX - 40, 92), (CX, 84), (CX + 40, 92), (CX + 60, 110)]), second, 5)
        for side in (-1, 1):
            # pale moon-edge along each horn
            stroke(ctx, lambda c, side=side: smooth_open(c, [(CX + side * 62, 70), (CX + side * 62, 34), (CX + side * 48, 18),
                                                              (CX + side * 30, 11)]), trim, 3.5, 0.9)
            glow(ctx, CX + side * 28, 12, 22, ec, 0.85)
        # oath sigil on the brow
        paint(ctx, lambda c: poly_path(c, [(CX, 60), (CX + 8, 70), (CX, 80), (CX - 8, 70)]), ec, lw=3, hi=False)
    elif h == "plume_helm":
        # flame plume crest, then the crimson helm with a nasal guard
        paint(ctx, lambda c: smooth_closed(c, [(CX + 18, 60), (CX + 26, 34), (CX + 14, 6), (CX + 2, 24), (CX - 10, 6),
                                                 (CX - 24, 26), (CX - 46, 16), (CX - 48, 42), (CX - 72, 46), (CX - 54, 62),
                                                 (CX - 20, 62)], 0.45), ec, lw=LW, hi=False)
        flat(ctx, lambda c: smooth_closed(c, [(CX + 10, 58), (CX + 14, 36), (CX + 4, 30), (CX - 8, 38), (CX - 30, 36),
                                                (CX - 40, 54), (CX - 14, 60)], 0.5), ec2, 0.95)
        helm = shade(main, 0.1)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 66, 126), (CX - 64, 72), (CX - 30, 50), (CX + 30, 50), (CX + 64, 72),
                                                 (CX + 66, 126), (CX + 48, 100), (CX + 12, 92), (CX - 12, 92), (CX - 48, 100)], 0.5),
              helm, lw=LW, hi_size=0.7)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 58, 96), (CX, 82), (CX + 58, 96)]), trim, 5)
        paint(ctx, lambda c: rrect_path(c, CX - 5, 80, 10, 30, 5), trim, lw=3.5, hi=False)
    elif h == "pearl_veil":
        pts = [(CX - 62, 126), (CX - 60, 80), (CX - 30, 56), (CX, 60), (CX + 30, 56), (CX + 60, 80), (CX + 62, 126),
               (CX + 50, 100), (CX + 28, 82), (CX, 90), (CX - 28, 82), (CX - 50, 100)]
        paint(ctx, lambda c: smooth_closed(c, pts, 0.45), hair, lw=LW)
        # pearl circlet
        stroke(ctx, lambda c: smooth_open(c, [(CX - 58, 86), (CX - 30, 74), (CX, 70), (CX + 30, 74), (CX + 58, 86)]), INK, 7)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 58, 86), (CX - 30, 74), (CX, 70), (CX + 30, 74), (CX + 58, 86)]), hex2rgb("#e8d3a0"), 3)
        for (x, y) in ((CX - 44, 79), (CX - 22, 72), (CX + 22, 72), (CX + 44, 79)):
            paint(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 5.5, 5.5), hex2rgb("#fffaf4"), lw=2.5, hi_size=0.6, shade_amt=0.2)
        paint(ctx, lambda c: smooth_closed(c, [(CX, 62), (CX + 9, 76), (CX, 88), (CX - 9, 76)], 0.6), hex2rgb("#fffaf4"), lw=3, hi_size=0.7)
        flat(ctx, lambda c: ellipse_path(c, CX, 77, 4, 5), light(ec2, 0.3), 0.8)
        # veil drapes at the sides of the face
        for side in (-1, 1):
            paint(ctx, lambda c, side=side: smooth_closed(c, [(CX + side * 56, 84), (CX + side * 72, 120), (CX + side * 80, 176),
                                                               (CX + side * 62, 168), (CX + side * 58, 120)], 0.5),
                  light(ec2, 0.6), lw=3, alpha=0.55, hi=False)
    elif h == "goggles_messy":
        pts = [(CX - 60, 118), (CX - 74, 98), (CX - 62, 92), (CX - 78, 70), (CX - 52, 66), (CX - 50, 40), (CX - 24, 50),
               (CX - 14, 26), (CX + 6, 46), (CX + 26, 26), (CX + 34, 52), (CX + 62, 44), (CX + 56, 66), (CX + 80, 74),
               (CX + 62, 92), (CX + 72, 110), (CX + 58, 118), (CX + 46, 96), (CX + 24, 104), (CX + 10, 90),
               (CX - 10, 102), (CX - 26, 90), (CX - 44, 100)]
        paint(ctx, lambda c: smooth_closed(c, pts, 0.25), hair, lw=LW, hi_pos=(-0.25, -0.3))
        # goggles pushed up on the forehead
        stroke(ctx, lambda c: smooth_open(c, [(CX - 62, 90), (CX, 80), (CX + 62, 90)]), INK, 12)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 62, 90), (CX, 80), (CX + 62, 90)]), hex2rgb("#4a3a30"), 6)
        for side in (-1, 1):
            paint(ctx, lambda c, side=side: ellipse_path(c, CX + side * 21, 80, 17, 15), BRASS, lw=4.5, hi_size=0.6)
            paint(ctx, lambda c, side=side: ellipse_path(c, CX + side * 21, 80, 10, 9), hex2rgb("#9fe8ff"), lw=3, hi=False, shade_amt=0.2)
            flat(ctx, lambda c, side=side: ellipse_path(c, CX + side * 21 - 3, 77, 3.5, 3), (1, 1, 1))
    elif h == "winged_helm":
        for side in (-1, 1):
            wing = [(CX + side * 54, 100), (CX + side * 64, 64), (CX + side * 90, 20), (CX + side * 102, 40), (CX + side * 92, 58),
                    (CX + side * 108, 64), (CX + side * 94, 82), (CX + side * 104, 94), (CX + side * 70, 108)]
            paint(ctx, lambda c, wing=wing: smooth_closed(c, wing, 0.35), light(ec, 0.45), lw=4.5, hi_size=0.6)
            stroke(ctx, lambda c, side=side: smooth_open(c, [(CX + side * 64, 90), (CX + side * 84, 54)]), ec, 3)
        helm = light(main, 0.05)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 66, 146), (CX - 66, 76), (CX - 30, 48), (CX + 30, 48), (CX + 66, 76),
                                                 (CX + 66, 146), (CX + 50, 138), (CX + 48, 100), (CX, 90), (CX - 48, 100),
                                                 (CX - 50, 138)], 0.4), helm, lw=LW, hi_size=0.7)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 56, 94), (CX, 82), (CX + 56, 94)]), second, 6)
        paint(ctx, lambda c: poly_path(c, [(CX, 54), (CX + 10, 70), (CX, 84), (CX - 10, 70)]), trim, lw=3.5, hi_size=0.6)
    elif h == "topknot":
        pts = [(CX - 60, 112), (CX - 58, 74), (CX - 26, 54), (CX + 20, 54), (CX + 56, 72), (CX + 62, 110), (CX + 48, 90),
               (CX + 30, 98), (CX + 22, 80), (CX - 6, 88), (CX - 26, 80), (CX - 44, 94)]
        paint(ctx, lambda c: smooth_closed(c, pts, 0.45), hair, lw=LW)
        paint(ctx, lambda c: rrect_path(c, CX - 13, 50, 26, 10, 4), trim, lw=3.5, hi=False)
        # headband
        stroke(ctx, lambda c: smooth_open(c, [(CX - 60, 98), (CX, 86), (CX + 60, 98)]), INK, 10)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 60, 98), (CX, 86), (CX + 60, 98)]), trim, 5)
    elif h == "flat_cap":
        cap = hex2rgb(spec.get("cap", "#6e6a5c"))
        # thick beard and moustache (over the mouth), then the flat cap
        paint(ctx, lambda c: smooth_closed(c, [(CX - 58, 110), (CX - 52, 150), (CX - 32, 182), (CX, 196), (CX + 32, 182),
                                                 (CX + 52, 150), (CX + 58, 110), (CX + 44, 128), (CX + 24, 138), (CX, 136),
                                                 (CX - 24, 138), (CX - 44, 128)], 0.45), hair, lw=LW, hi_pos=(-0.2, 0.1))
        for side in (-1, 1):
            paint(ctx, lambda c, side=side: smooth_closed(c, [(CX, 132), (CX + side * 14, 128), (CX + side * 28, 136),
                                                               (CX + side * 20, 144), (CX + side * 4, 140)], 0.5), shade(hair, 0.1), lw=3.5, hi=False)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 8, 152), (CX, 156), (CX + 8, 152)]), INK, 3)
        paint(ctx, lambda c: smooth_closed(c, [(CX - 64, 98), (CX - 70, 74), (CX - 44, 56), (CX + 6, 50), (CX + 54, 56),
                                                 (CX + 74, 74), (CX + 66, 96), (CX, 92)], 0.45), cap, lw=LW, hi_size=0.6)
        stroke(ctx, lambda c: smooth_open(c, [(CX - 40, 60), (CX - 6, 76), (CX + 30, 92)]), shade(cap, 0.3), 3)
        paint(ctx, lambda c: smooth_closed(c, [(CX + 10, 92), (CX + 60, 84), (CX + 94, 90), (CX + 72, 102), (CX + 14, 102)], 0.4),
              shade(cap, 0.2), lw=LW - 1, hi=False)
        paint(ctx, lambda c: ellipse_path(c, CX + 6, 54, 7, 4), shade(cap, 0.25), lw=3, hi=False)


def ext_prop(ctx, spec, hand, pose, element):
    kind = spec["prop"]
    ec, ec2 = ELEMENT[element]
    hx, hy = hand
    lh, rh = hands_for(spec, pose)
    trim = hex2rgb(spec["trim"])
    second = hex2rgb(spec["second"])
    wood = hex2rgb("#8a5a34")
    metal = hex2rgb("#cfd6e6")
    cast = pose == "cast"

    def blade_at(x, y, ang, L, half, col, edge=None):
        tip = (x + math.cos(ang) * L, y + math.sin(ang) * L)
        nx, ny = -math.sin(ang), math.cos(ang)
        b = (x + math.cos(ang) * 16, y + math.sin(ang) * 16)
        pts = [(b[0] + nx * half, b[1] + ny * half), (tip[0] - math.cos(ang) * 16 + nx * half * 0.9, tip[1] - math.sin(ang) * 16 + ny * half * 0.9),
               tip, (tip[0] - math.cos(ang) * 16 - nx * half * 0.9, tip[1] - math.sin(ang) * 16 - ny * half * 0.9),
               (b[0] - nx * half, b[1] - ny * half)]
        paint(ctx, lambda c: poly_path(c, pts), col, lw=4.5, hi_size=0.6)
        if edge:
            stroke(ctx, lambda c: (c.move_to(*b), c.line_to(*tip)), edge, 2.5)
        return b, tip, (nx, ny)

    if kind == "sun_shield_sword":
        # short sword in the right hand (drawn first so the hand grips it)
        ang = -1.3 if not cast else -0.95
        if cast:
            glow(ctx, hx + math.cos(ang) * 60, hy + math.sin(ang) * 60, 56, ec, 0.6)
        b, tip, (nx, ny) = blade_at(hx, hy, ang, 96, 8, metal, light(ec2, 0.2) if not cast else ec)
        outlined_line(ctx, [(b[0] + nx * 18, b[1] + ny * 18), (b[0] - nx * 18, b[1] - ny * 18)], second, 8, 15, smooth=False)
        paint(ctx, lambda c: ellipse_path(c, hx - math.cos(ang) * 16, hy - math.sin(ang) * 16, 6, 6), second, lw=3, hi=False)
        if cast:
            sparkle(ctx, tip[0], tip[1], 12)
        # kite shield on the left arm with a sun emblem
        sx, sy = (lh[0] + 4, lh[1] - 24) if not cast else (lh[0] + 6, lh[1] - 36)
        kite = [(sx - 40, sy - 50), (sx, sy - 60), (sx + 40, sy - 50), (sx + 36, sy + 8), (sx, sy + 68), (sx - 36, sy + 8)]
        inner = [(sx + (x - sx) * 0.78, sy - 3 + (y - sy) * 0.78) for (x, y) in kite]
        paint(ctx, lambda c: smooth_closed(c, kite, 0.3), second, lw=LW, hi_size=0.7)
        paint(ctx, lambda c: smooth_closed(c, inner, 0.3), hex2rgb(spec.get("tabard", "#fff6dc")), lw=3.5, hi_size=0.6)
        if cast:
            glow(ctx, sx, sy - 6, 50, ec2, 0.7)
        paint(ctx, lambda c: star_path(c, sx, sy - 6, 24, 14, 10), ec, lw=3.5, hi=False)
        paint(ctx, lambda c: ellipse_path(c, sx, sy - 6, 11, 11), light(ec, 0.5), lw=3, hi=False, shade_amt=0.1)
        sparkle(ctx, sx - 20, sy - 36, 8)
    elif kind in ("chain_staff", "conch_staff", "wrench_staff"):
        reach = {"chain_staff": 150, "conch_staff": 132, "wrench_staff": 140}[kind]
        if cast:
            reach -= 46 if kind != "chain_staff" else 80
        top = (hx + 10, hy - reach)
        bottom = (hx - 4, hy + 40)
        shaft = {"chain_staff": hex2rgb("#2a1e34"), "conch_staff": hex2rgb("#c8a27a"), "wrench_staff": hex2rgb("#7a8090")}[kind]
        outlined_line(ctx, [bottom, top], shaft, 9, 16, smooth=False)
        tx, ty = top
        if kind == "chain_staff":
            glow(ctx, tx, ty - 18, 60 if cast else 44, ec, 0.8 if cast else 0.55)
            # floating chain links drifting up beside the shaft
            for k in range(4):
                lx = tx - 26 + (k % 2) * 6 - k * 3
                ly = ty + 34 + k * 26 - (10 if cast else 0)
                rot = 0.3 if k % 2 else -0.3
                rx, ry = (10, 5) if k % 2 else (5, 10)
                stroke(ctx, lambda c, lx=lx, ly=ly, rot=rot, rx=rx, ry=ry: ellipse_path(c, lx, ly, rx, ry, rot), INK, 8)
                stroke(ctx, lambda c, lx=lx, ly=ly, rot=rot, rx=rx, ry=ry: ellipse_path(c, lx, ly, rx, ry, rot), hex2rgb("#c9c3d6"), 3.5)
            # oath sigil: crimson ring holding a crescent
            stroke(ctx, lambda c: ellipse_path(c, tx, ty - 18, 22, 22), INK, 12)
            stroke(ctx, lambda c: ellipse_path(c, tx, ty - 18, 22, 22), ec, 6)
            for k in range(4):
                a = k * math.pi / 2 + math.pi / 4
                paint(ctx, lambda c, a=a: poly_path(c, [(tx + math.cos(a) * 20, ty - 18 + math.sin(a) * 20),
                                                        (tx + math.cos(a) * 32, ty - 18 + math.sin(a) * 32),
                                                        (tx + math.cos(a + 0.25) * 22, ty - 18 + math.sin(a + 0.25) * 22)]),
                      ec, lw=2.5, hi=False)
            def crescent(c):
                c.new_sub_path()
                c.arc(tx, ty - 18, 13, math.pi * 0.3, math.pi * 1.7)
                c.arc_negative(tx + 6, ty - 18, 10, math.pi * 1.6, math.pi * 0.4)
                c.close_path()
            paint(ctx, crescent, light(ec, 0.6), lw=3, hi=False)
            if cast:
                sparkle(ctx, tx + 18, ty - 44, 10, light(ec, 0.6))
        elif kind == "conch_staff":
            glow(ctx, tx, ty - 22, 56 if cast else 42, ec2, 0.75 if cast else 0.5)
            conch = [(tx - 18, ty + 4), (tx - 24, ty - 16), (tx - 12, ty - 36), (tx + 4, ty - 56), (tx + 16, ty - 34),
                     (tx + 24, ty - 12), (tx + 14, ty + 6)]
            paint(ctx, lambda c: smooth_closed(c, conch, 0.5), hex2rgb("#ffe0cc"), lw=4.5, hi_size=0.6)
            for k in range(3):
                y = ty - 12 - k * 13
                stroke(ctx, lambda c, y=y, k=k: smooth_open(c, [(tx - 20 + k * 5, y + 4), (tx, y - 4), (tx + 20 - k * 5, y + 2)]), INK, 2.5)
            # spikes on the shell shoulder and the pink opening
            for (px, py) in ((tx - 24, ty - 20), (tx + 22, ty - 22)):
                paint(ctx, lambda c, px=px, py=py: poly_path(c, [(px, py - 6), (px + (8 if px > tx else -8), py - 2), (px, py + 6)]),
                      hex2rgb("#ffe0cc"), lw=3, hi=False)
            paint(ctx, lambda c: ellipse_path(c, tx + 4, ty + 2, 13, 8, -0.2), hex2rgb("#ff9fb4"), lw=3.5, hi=False)
            if cast:
                for (bx, by, r) in ((tx - 30, ty - 50, 7), (tx + 30, ty - 60, 5), (tx - 6, ty - 74, 6), (tx + 22, ty - 84, 4)):
                    stroke(ctx, lambda c, bx=bx, by=by, r=r: ellipse_path(c, bx, by, r, r), (1, 1, 1), 2.5)
                    paint(ctx, lambda c, bx=bx, by=by, r=r: ellipse_path(c, bx, by, r, r), ec2, lw=0, hi=False, alpha=0.5)
        else:
            glow(ctx, tx, ty - 22, 60 if cast else 40, ec2, 0.8 if cast else 0.5)
            # open-ended wrench jaw
            def jaw(c):
                c.new_sub_path()
                c.arc(tx, ty - 20, 24, -math.pi * 0.3, math.pi * 1.3)
                c.arc_negative(tx, ty - 20, 11, math.pi * 1.3, -math.pi * 0.3)
                c.close_path()
            paint(ctx, jaw, metal, lw=LW - 1, hi_size=0.6)
            paint(ctx, lambda c: rrect_path(c, tx - 8, ty - 4, 16, 18, 4), BRASS, lw=3.5, hi=False)
            zig = [(tx - 8, ty - 36), (tx + 4, ty - 26), (tx - 4, ty - 20), (tx + 8, ty - 12)] if not cast else \
                  [(tx - 6, ty - 26), (tx + 8, ty - 44), (tx - 6, ty - 56), (tx + 12, ty - 72), (tx + 2, ty - 84)]
            stroke(ctx, lambda c: (c.move_to(*zig[0]), [c.line_to(*p) for p in zig[1:]]), ec, 7)
            stroke(ctx, lambda c: (c.move_to(*zig[0]), [c.line_to(*p) for p in zig[1:]]), ec2, 3)
            sparkle(ctx, tx + 20, ty - 44, 8, ec2)
    elif kind == "flame_sabre":
        ang = -1.1 if not cast else -1.95
        ctx.save()
        ctx.translate(hx, hy)
        ctx.rotate(ang)
        glow(ctx, 70, -10, 70, ec, 0.45 if not cast else 0.7)
        # flame tongues licking off the curved back edge
        for k, (x, L) in enumerate(((44, 22), (68, 26), (92, 24), (112, 18))):
            paint(ctx, lambda c, x=x, L=L: smooth_closed(c, [(x - 10, -10 - x * 0.12), (x - 4, -18 - L - x * 0.12), (x + 4, -24 - x * 0.12),
                                                               (x + 12, -12 - L * 0.6 - x * 0.12), (x + 10, -6 - x * 0.12)], 0.5),
                  ec if k % 2 == 0 else hex2rgb(spec["second"]), lw=3.5, hi=False)
        blade = [(16, -9), (60, -16), (100, -24), (130, -40), (112, -14), (70, 0), (16, 7)]
        paint(ctx, lambda c: smooth_closed(c, blade, 0.3), metal, lw=4.5, hi_size=0.6)
        stroke(ctx, lambda c: smooth_open(c, [(22, -5), (70, -10), (112, -24)]), ec2, 3)
        outlined_line(ctx, [(14, -20), (14, 20)], trim, 9, 16, smooth=False)
        outlined_line(ctx, [(-20, 0), (12, 0)], hex2rgb("#4a2a1a"), 9, 16, smooth=False)
        paint(ctx, lambda c: ellipse_path(c, -22, 0, 6, 6), trim, lw=3, hi=False)
        ctx.restore()
        if cast:
            sparkle(ctx, hx + math.cos(ang) * 132, hy + math.sin(ang) * 132, 12)
    elif kind == "crystal_shield_mace":
        # flanged mace in the right hand
        ang = -1.25 if not cast else -1.9
        head = (hx + math.cos(ang) * 78, hy + math.sin(ang) * 78)
        outlined_line(ctx, [(hx - math.cos(ang) * 16, hy - math.sin(ang) * 16), head], hex2rgb("#5f6f8a"), 9, 16, smooth=False)
        if cast:
            glow(ctx, head[0], head[1], 52, ec2, 0.75)
        paint(ctx, lambda c: star_path(c, head[0], head[1], 28, 18, 8, rot=ang), metal, lw=4.5, hi_size=0.6)
        paint(ctx, lambda c: ellipse_path(c, head[0], head[1], 11, 11), ec, lw=3.5, hi=False)
        # hexagonal faceted crystal greatshield on the left arm
        sx, sy = (lh[0] + 6, lh[1] - 32) if not cast else (lh[0] + 8, lh[1] - 42)
        hexa = [(sx, sy - 78), (sx + 46, sy - 48), (sx + 46, sy + 42), (sx, sy + 76), (sx - 46, sy + 42), (sx - 46, sy - 48)]
        glow(ctx, sx, sy, 96, ec2, 0.4 if not cast else 0.7)
        paint(ctx, lambda c: poly_path(c, hexa), mix(ec, (1, 1, 1), 0.25), lw=LW, alpha=0.95, hi_size=0.8)
        inner = [(sx + (x - sx) * 0.5, sy + (y - sy) * 0.5) for (x, y) in hexa]
        paint(ctx, lambda c: poly_path(c, inner), ec2, lw=3.5, hi=False, shade_amt=0.15)
        for (ox, oy), (ix, iy) in zip(hexa, inner):
            stroke(ctx, lambda c, ox=ox, oy=oy, ix=ix, iy=iy: (c.move_to(ox, oy), c.line_to(ix, iy)), (1, 1, 1), 2.5, 0.8)
        sparkle(ctx, sx - 18, sy - 44, 10)
        sparkle(ctx, sx + 16, sy + 30, 6)
    elif kind == "war_fans":
        for side, (fx, fy) in ((1, rh), (-1, lh)):
            r = 46 if not cast else 54
            if cast:
                a0, a1 = -math.pi / 2 - 1.2, -math.pi / 2 + 1.2
            else:
                a0, a1 = (-1.75, -0.2) if side > 0 else (-math.pi + 0.2, -math.pi + 1.75)
            n = 6
            pts = [(fx, fy)]
            for i in range(n * 2 + 1):
                a = a0 + (a1 - a0) * i / (n * 2)
                rr = r + 8 if i % 2 == 0 else r - 2
                pts.append((fx + math.cos(a) * rr, fy + math.sin(a) * rr))
            if cast:
                glow(ctx, fx, fy - 26, 58, ec2, 0.65)
            paint(ctx, lambda c, pts=pts: poly_path(c, pts), ec, lw=LW - 1, hi_size=0.6)
            flat(ctx, lambda c, fx=fx, fy=fy, a0=a0, a1=a1, r=r: (c.move_to(fx, fy), c.arc(fx, fy, r * 0.45, a0, a1), c.close_path()),
                 hex2rgb("#2c3c4c"), 0.9)
            for i in range(n + 1):
                a = a0 + (a1 - a0) * i / n
                stroke(ctx, lambda c, a=a, fx=fx, fy=fy, r=r: (c.move_to(fx, fy), c.line_to(fx + math.cos(a) * (r + 6), fy + math.sin(a) * (r + 6))),
                       INK, 2.5)
            paint(ctx, lambda c, fx=fx, fy=fy: ellipse_path(c, fx, fy, 6, 6), metal, lw=3, hi=False)
            if cast:
                for k in range(2):
                    rr = r + 18 + k * 12
                    stroke(ctx, lambda c, fx=fx, fy=fy, rr=rr: c.arc(fx, fy - 4, rr, -math.pi / 2 - 0.9, -math.pi / 2 - 0.2), ec2, 4 - k)
    elif kind == "stone_gauntlet":
        ox, oy = (hx + 2, hy - 2) if not cast else (hx + 2, hy - 8)
        glow(ctx, ox, oy, 56, ec2, 0.35 if not cast else 0.75)
        paint(ctx, lambda c: rrect_path(c, ox - 36, oy - 30, 72, 66, 9), STONE, lw=LW, hi_size=0.6)
        for k in range(4):
            paint(ctx, lambda c, k=k: rrect_path(c, ox - 32 + k * 16, oy - 38, 15, 16, 4), light(STONE, 0.15), lw=3.5, hi=False)
        # cracks and a glowing rune square
        stroke(ctx, lambda c: (c.move_to(ox - 30, oy + 20), c.line_to(ox - 20, oy + 14), c.line_to(ox - 22, oy + 4)), INK, 2.5)
        stroke(ctx, lambda c: (c.move_to(ox + 32, oy + 26), c.line_to(ox + 22, oy + 24)), INK, 2.5)
        paint(ctx, lambda c: rrect_path(c, ox - 11, oy - 6, 22, 22, 4), ec2, lw=3, hi=False, shade_amt=0.15)
        stroke(ctx, lambda c: (c.move_to(ox - 5, oy), c.line_to(ox + 5, oy + 10), c.move_to(ox + 5, oy), c.line_to(ox - 5, oy + 10)),
               shade(ec2, 0.5), 2.5)
        if cast:
            for (px, py, r) in ((ox - 42, oy - 44, 7), (ox + 44, oy - 36, 6), (ox + 4, oy - 58, 5)):
                paint(ctx, lambda c, px=px, py=py, r=r: poly_path(c, [(px - r, py), (px, py - r), (px + r, py + 2), (px, py + r)]),
                      STONE, lw=3, hi=False)
