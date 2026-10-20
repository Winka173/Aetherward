"""Post-MVP expansion art: glyphs, icons, VFX and field sprites for the six new elements
(Light, Shadow, Nature, Poison, Arcane, Void) and the declarative reactions/fields.

Same style rules as the launch set (thick ink outline, cel shading, distinct silhouettes per element
so colour is never the only cue). Everything is generated; nothing is traced or downloaded."""
import math
import random
import cairo
from toolkit import (INK, Canvas, hex2rgb, mix, shade, light, paint, flat, stroke, glow, sparkle, smooth_closed, smooth_open,
                     ellipse_path, rrect_path, poly_path, star_path, outlined_line)
import glyphs
from glyphs import (glyph, GLYPHS, FIRE, FIRE2, WATER, WATER2, BOLT, BOLT2, ICE, ICE2, WIND, WIND2, EARTH, EARTH2, GOLD, STEEL, RED, PURPLE)
import icons

LIGHT, LIGHT2 = hex2rgb("#ffd84a"), hex2rgb("#fff7cc")
SHADOW, SHADOW2 = hex2rgb("#a3306b"), hex2rgb("#3a0f2c")
NATURE, NATURE2 = hex2rgb("#3fa34d"), hex2rgb("#b6ec6a")
POISON, POISON2 = hex2rgb("#a8e030"), hex2rgb("#6a2a9a")
ARCANE, ARCANE2 = hex2rgb("#ff5fd2"), hex2rgb("#ffd6f6")
VOID, VOID2 = hex2rgb("#5146d9"), hex2rgb("#140c38")
LW = 5.0

NEW_ELEMENTS = {
    "light": (LIGHT, LIGHT2), "shadow": (SHADOW, SHADOW2), "nature": (NATURE, NATURE2),
    "poison": (POISON, POISON2), "arcane": (ARCANE, ARCANE2), "void": (VOID, VOID2),
}
ALL_ELEMENTS = dict(icons.ELEMENT_COLORS)
ALL_ELEMENTS.update(NEW_ELEMENTS)


# ============================================================================ glyphs

def g_sun(ctx, cx, cy, s, col=LIGHT, col2=LIGHT2):
    for k in range(8):
        a = k * math.pi / 4
        tip = (cx + math.cos(a) * s * 0.48, cy + math.sin(a) * s * 0.48)
        l = (cx + math.cos(a - 0.22) * s * 0.28, cy + math.sin(a - 0.22) * s * 0.28)
        r = (cx + math.cos(a + 0.22) * s * 0.28, cy + math.sin(a + 0.22) * s * 0.28)
        paint(ctx, lambda c, tip=tip, l=l, r=r: poly_path(c, [l, tip, r]), col, lw=4, hi=False)
    paint(ctx, lambda c: ellipse_path(c, cx, cy, s * 0.26, s * 0.26), col2, lw=LW, hi_size=0.7)
    flat(ctx, lambda c: ellipse_path(c, cx, cy, s * 0.14, s * 0.14), col, 0.8)


def g_moon(ctx, cx, cy, s, col=SHADOW, col2=SHADOW2):
    def crescent(c):
        c.arc(cx, cy, s * 0.42, math.radians(-60), math.radians(240))
        c.arc_negative(cx + s * 0.16, cy - s * 0.12, s * 0.32, math.radians(220), math.radians(-40))
        c.close_path()
    paint(ctx, crescent, col, lw=LW)
    sparkle(ctx, cx + s * 0.22, cy - s * 0.22, s * 0.1, LIGHT2, 0.9)


def g_vial(ctx, cx, cy, s, col=POISON, col2=POISON2):
    def body(c):
        smooth_closed(c, [(cx - s * 0.1, cy - s * 0.3), (cx + s * 0.1, cy - s * 0.3), (cx + s * 0.12, cy - s * 0.08), (cx + s * 0.34, cy + s * 0.26),
                          (cx, cy + s * 0.44), (cx - s * 0.34, cy + s * 0.26), (cx - s * 0.12, cy - s * 0.08)], 0.3)
    paint(ctx, body, (0.86, 0.95, 0.98), lw=LW, hi=False)
    ctx.save()
    ctx.new_path()
    body(ctx)
    ctx.clip()
    flat(ctx, lambda c: rrect_path(c, cx - s * 0.5, cy + s * 0.04, s, s * 0.5, 2), col)
    for k in range(3):
        flat(ctx, lambda c, k=k: ellipse_path(c, cx - s * 0.12 + k * s * 0.12, cy + s * 0.2 - (k % 2) * s * 0.1, s * 0.05, s * 0.05), light(col, 0.5), 0.9)
    ctx.restore()
    stroke(ctx, body, INK, LW)
    paint(ctx, lambda c: rrect_path(c, cx - s * 0.14, cy - s * 0.44, s * 0.28, s * 0.14, 4), col2, lw=4, hi=False)


def g_rune(ctx, cx, cy, s, col=ARCANE, col2=ARCANE2):
    stroke(ctx, lambda c: ellipse_path(c, cx, cy, s * 0.42, s * 0.42), INK, 11)
    stroke(ctx, lambda c: ellipse_path(c, cx, cy, s * 0.42, s * 0.42), col, 6)
    tri = [(cx + math.cos(a) * s * 0.34, cy + math.sin(a) * s * 0.34) for a in (-math.pi / 2, math.pi / 6, 5 * math.pi / 6)]
    stroke(ctx, lambda c: poly_path(c, tri), INK, 9)
    stroke(ctx, lambda c: poly_path(c, tri), col2, 4.5)
    for p in tri:
        paint(ctx, lambda c, p=p: ellipse_path(c, p[0], p[1], s * 0.07, s * 0.07), col, lw=3, hi=False)
    paint(ctx, lambda c: star_path(c, cx, cy + s * 0.02, s * 0.12, s * 0.05, 4), GOLD, lw=2.5, hi=False)


def g_void_ring(ctx, cx, cy, s, col=VOID, col2=VOID2):
    for k in range(3):
        r = s * (0.44 - k * 0.1)
        a0 = k * 1.3
        stroke(ctx, lambda c, r=r, a0=a0: c.arc(cx, cy, r, a0, a0 + 4.4), INK, 10)
        stroke(ctx, lambda c, r=r, a0=a0: c.arc(cx, cy, r, a0, a0 + 4.4), light(col, k * 0.25), 5)
    paint(ctx, lambda c: ellipse_path(c, cx, cy, s * 0.15, s * 0.15), col2, lw=4, hi=False)
    glow(ctx, cx, cy, s * 0.12, light(col, 0.6), 0.5)


def g_root(ctx, cx, cy, s, col=NATURE, col2=hex2rgb("#7a5230")):
    for k, dx in enumerate((-0.22, 0.0, 0.22)):
        pts = [(cx + s * dx, cy - s * 0.1), (cx + s * dx * 1.4 - s * 0.06, cy + s * 0.14), (cx + s * dx * 1.9 + s * 0.04, cy + s * 0.42)]
        outlined_line(ctx, pts, col2, s * 0.07, s * 0.07 + 7)
    glyphs.g_sprout(ctx, cx, cy - s * 0.12, s * 0.62, col)


for _name, _fn in (("sun", g_sun), ("moon", g_moon), ("vial", g_vial), ("rune", g_rune), ("void_ring", g_void_ring), ("root", g_root)):
    GLYPHS[_name] = _fn

ELEMENT_GLYPH = {"light": ("sun", LIGHT, LIGHT2), "shadow": ("moon", SHADOW, SHADOW2), "nature": ("leaf", NATURE, NATURE2),
                 "poison": ("vial", POISON, POISON2), "arcane": ("rune", ARCANE, ARCANE2), "void": ("void_ring", hex2rgb("#7a70ff"), VOID2)}


# ============================================================================ icons

def element_icon(el, s=128):
    cv = Canvas(s, s)
    a, b = NEW_ELEMENTS[el]
    icons.badge(cv.ctx, s, shade(a, 0.35) if el != "void" else hex2rgb("#2a2470"), "circle")
    g, c1, c2 = ELEMENT_GLYPH[el]
    glyph(cv.ctx, g, s / 2, s / 2, s * 0.68, c1, c2)
    return cv


STATUS_NEW = {
    # id: (glyph, badge colour, glyph colour, glyph colour 2, shape)
    "illuminated": ("sun", hex2rgb("#a07a1a"), LIGHT, LIGHT2, "circle"),
    "doom": ("skull", hex2rgb("#6a1a40"), (0.96, 0.9, 0.92), None, "diamond"),
    "rooted": ("root", hex2rgb("#2a5a2a"), NATURE2, None, "circle"),
    "poisoned": ("vial", hex2rgb("#3a2a5a"), POISON, POISON2, "circle"),
    "resonant": ("rune", hex2rgb("#7a2a6a"), ARCANE, ARCANE2, "hex"),
    "unstable": ("void_ring", hex2rgb("#241c60"), hex2rgb("#8a80ff"), VOID2, "diamond"),
    # corroded shared armor_crack's cracked shield; sealed shared stun's star (validator "icon_shape_confusable").
    "corroded": ("drop", hex2rgb("#4a5a1a"), POISON, None, "hex"),
    # brittle used the frozen snowflake on the same diamond badge (validator "icon_shape_confusable"): shard + hex badge.
    "brittle": ("shatter", hex2rgb("#3a5a7a"), ICE2, ICE, "hex"),
    "silenced": ("staff", hex2rgb("#4a2a4a"), STEEL, RED, "circle"),
    "leeched": ("battery", hex2rgb("#2a3a5a"), STEEL, ARCANE, "circle"),
    "fever": ("heart", hex2rgb("#6a3a1a"), RED, None, "circle"),
    "marked": ("flame", hex2rgb("#6a2a1a"), FIRE, FIRE2, "diamond"),
    "sealed": ("chain", hex2rgb("#2a2a5a"), LIGHT2, None, "hex"),
}


def status_icon(sid, s=96):
    cv = Canvas(s, s)
    g, col, gcol, gcol2, shape = STATUS_NEW[sid]
    icons.badge(cv.ctx, s, col, shape)
    glyph(cv.ctx, g, s / 2, s / 2, s * 0.6, gcol, gcol2)
    return cv


REACTION_ART = {
    # id: (element a, element b, glyph, glyph colour)
    "eclipse": ("light", "shadow", "moon", None), "hallowed_bulwark": ("earth", "light", "shield", LIGHT2),
    "solar_flare": ("fire", "light", "sun", None), "glimmer_tide": ("water", "light", "drop", LIGHT2),
    "hellfire": ("fire", "shadow", "flame", SHADOW), "black_tide": ("water", "shadow", "drop", hex2rgb("#2a1030")),
    "wildfire": ("fire", "nature", "flame", None), "overgrowth": ("water", "nature", "sprout", None),
    "toxic_shock": ("lightning", "poison", "bolt", POISON), "venom_shards": ("ice", "poison", "spikes", POISON),
    "sanctuary": ("light", "nature", "cross", LIGHT2), "plague": ("shadow", "poison", "skull", POISON),
    "blight_garden": ("nature", "poison", "sprout", POISON), "toxic_combustion": ("fire", "poison", "burst", POISON),
    "venom_flow": ("water", "poison", "vial", None), "frost_roots": ("ice", "nature", "root", ICE2),
    "overcharge": ("lightning", "arcane", "battery", ARCANE2), "spellflare": ("fire", "arcane", "rune", FIRE2),
    "mana_tide": ("water", "arcane", "echo", ARCANE2), "singularity": ("wind", "void", "void_ring", None),
    "gravemaw": ("earth", "void", "mountain", hex2rgb("#8a80ff")), "abyss_mark": ("shadow", "void", "target", SHADOW),
    "prism_chant": ("light", "arcane", "gem", LIGHT2), "astral_seal": ("light", "void", "star", LIGHT2),
    "paradox": ("arcane", "void", "hourglass", ARCANE2),
}


def _split_hex(ctx, s, ca, cb):
    m = 6
    hexpath = lambda c: poly_path(c, [(s / 2 + math.cos(t) * (s / 2 - m), s / 2 + math.sin(t) * (s / 2 - m)) for t in [k * math.pi / 3 for k in range(6)]])
    ctx.save()
    ctx.new_path()
    hexpath(ctx)
    ctx.clip()
    flat(ctx, lambda c: poly_path(c, [(0, 0), (s * 0.62, 0), (s * 0.38, s), (0, s)]), shade(ca, 0.2))
    flat(ctx, lambda c: poly_path(c, [(s * 0.62, 0), (s, 0), (s, s), (s * 0.38, s)]), shade(cb, 0.2))
    glow(ctx, s / 2, s / 2, s * 0.45, (1, 1, 1), 0.25)
    ctx.restore()
    stroke(ctx, hexpath, INK, 7)


def reaction_icon(rid, s=128):
    cv = Canvas(s, s)
    a, b, g, gcol = REACTION_ART[rid]
    _split_hex(cv.ctx, s, ALL_ELEMENTS[a][0], ALL_ELEMENTS[b][0])
    glyph(cv.ctx, g, s / 2, s / 2, s * 0.62, gcol)
    return cv


def generic_reaction_icon(s=128):
    """Shared icon for auto-named generic interactions: neutral split + clash burst."""
    cv = Canvas(s, s)
    _split_hex(cv.ctx, s, hex2rgb("#8a90a8"), hex2rgb("#5a6078"))
    glyph(cv.ctx, "burst", s / 2, s / 2, s * 0.6, (0.95, 0.95, 1.0), hex2rgb("#c8d0e8"))
    return cv


# ============================================================================ VFX

def projectile(el, s=128):
    """Points to +x. Distinct silhouette per element."""
    cv = Canvas(s, s)
    ctx = cv.ctx
    a, b = NEW_ELEMENTS[el]
    c = s / 2
    glow(ctx, c, c, s * 0.42, light(a, 0.3), 0.55)
    if el == "light":
        paint(ctx, lambda x: poly_path(x, [(c + 44, c), (c + 4, c - 10), (c - 40, c), (c + 4, c + 10)]), a, lw=4.5, hi=False)
        flat(ctx, lambda x: poly_path(x, [(c + 30, c), (c + 4, c - 4), (c - 24, c), (c + 4, c + 4)]), (1, 1, 1))
        sparkle(ctx, c + 40, c, 12, b, 1.0)
    elif el == "shadow":
        for k in range(3):
            stroke(ctx, lambda x, k=k: smooth_open(x, [(c + 10, c + (k - 1) * 6), (c - 18, c + (k - 1) * 14), (c - 44, c + (k - 1) * 10)]), a, 6 - k, 0.8)
        paint(ctx, lambda x: ellipse_path(x, c + 14, c, 18, 16), b, lw=4.5, hi=False)
        flat(ctx, lambda x: ellipse_path(x, c + 18, c - 2, 7, 6), a, 0.9)
    elif el == "nature":
        paint(ctx, lambda x: smooth_closed(x, [(c + 38, c), (c + 6, c - 16), (c - 30, c - 4), (c - 34, c + 2), (c + 6, c + 16)], 0.5), a, lw=4.5)
        stroke(ctx, lambda x: (x.move_to(c - 30, c), x.line_to(c + 34, c)), shade(a, 0.5), 3)
        flat(ctx, lambda x: ellipse_path(x, c - 40, c + 6, 5, 5), b, 0.9)
    elif el == "poison":
        paint(ctx, lambda x: smooth_closed(x, [(c + 30, c), (c + 12, c - 18), (c - 14, c - 14), (c - 20, c), (c - 14, c + 14), (c + 12, c + 18)], 0.6), a, lw=4.5, hi_size=0.6)
        for k in range(3):
            paint(ctx, lambda x, k=k: ellipse_path(x, c - 30 - k * 10, c + (k % 2) * 10 - 5, 6 - k, 7 - k), b, lw=3, hi=False)
    elif el == "arcane":
        paint(ctx, lambda x: ellipse_path(x, c + 8, c, 22, 22), a, lw=4.5, hi=False)
        paint(ctx, lambda x: star_path(x, c + 8, c, 16, 7, 4, 0.4), b, lw=3, hi=False)
        for k in range(3):
            sparkle(ctx, c - 22 - k * 12, c + (k % 2) * 10 - 5, 7 - k, b, 0.9)
    elif el == "void":
        stroke(ctx, lambda x: ellipse_path(x, c + 6, c, 26, 26), hex2rgb("#8a80ff"), 6, 0.9)
        paint(ctx, lambda x: ellipse_path(x, c + 6, c, 18, 18), b, lw=4.5, hi=False)
        for k in range(2):
            stroke(ctx, lambda x, k=k: x.arc(c - 18 - k * 14, c, 16 - k * 4, -1.0, 1.0), a, 5 - k, 0.8)
    return cv


def impact(el, s=192):
    cv = Canvas(s, s)
    ctx = cv.ctx
    a, b = NEW_ELEMENTS[el]
    c = s / 2
    rnd = random.Random(sum(map(ord, el)))
    glow(ctx, c, c, s * 0.45, light(a, 0.3), 0.6)
    if el == "light":
        for k in range(12):
            ang = k * math.pi / 6
            ln = 82 if k % 2 == 0 else 54
            paint(ctx, lambda x, ang=ang, ln=ln: poly_path(x, [(c + math.cos(ang - 0.08) * 20, c + math.sin(ang - 0.08) * 20),
                                                               (c + math.cos(ang) * ln, c + math.sin(ang) * ln),
                                                               (c + math.cos(ang + 0.08) * 20, c + math.sin(ang + 0.08) * 20)]), a, lw=3.5, hi=False)
        paint(ctx, lambda x: ellipse_path(x, c, c, 24, 24), b, lw=4, hi=False)
    elif el == "shadow":
        for k in range(5):
            ang = k * 2 * math.pi / 5 + 0.3
            def cres(x, ang=ang):
                x.arc(c + math.cos(ang) * 30, c + math.sin(ang) * 30, 34, ang - 1.1, ang + 1.1)
            stroke(ctx, cres, INK, 14)
            stroke(ctx, cres, a, 7)
        paint(ctx, lambda x: ellipse_path(x, c, c, 22, 22), b, lw=4, hi=False)
    elif el == "nature":
        for k in range(7):
            ang = k * 2 * math.pi / 7
            glyphs.g_leaf(ctx, c + math.cos(ang) * 52, c + math.sin(ang) * 52, 40, a)
        paint(ctx, lambda x: ellipse_path(x, c, c, 18, 18), b, lw=4, hi=False)
    elif el == "poison":
        for _ in range(9):
            ang = rnd.uniform(0, 2 * math.pi)
            d = rnd.uniform(30, 74)
            r = rnd.uniform(8, 16)
            paint(ctx, lambda x, ang=ang, d=d, r=r: ellipse_path(x, c + math.cos(ang) * d, c + math.sin(ang) * d, r, r * 0.85), a, lw=3.5, hi=False)
        paint(ctx, lambda x: ellipse_path(x, c, c, 30, 26), b, lw=4, hi=False, alpha=0.9)
    elif el == "arcane":
        stroke(ctx, lambda x: ellipse_path(x, c, c, 66, 66), INK, 12)
        stroke(ctx, lambda x: ellipse_path(x, c, c, 66, 66), a, 6)
        for k in range(6):
            ang = k * math.pi / 3
            sparkle(ctx, c + math.cos(ang) * 66, c + math.sin(ang) * 66, 12, b, 1.0)
        g_rune(ctx, c, c, 70)
    elif el == "void":
        for k in range(4):
            r = 78 - k * 18
            stroke(ctx, lambda x, r=r: ellipse_path(x, c, c, r, r), INK, 10)
            stroke(ctx, lambda x, r=r, k=k: ellipse_path(x, c, c, r, r), light(a, 0.15 * k), 5)
        paint(ctx, lambda x: ellipse_path(x, c, c, 16, 16), b, lw=4, hi=False)
    return cv


FIELD_STYLE = {
    # field id: (base colour, accent colour, pattern)
    "eclipse": (hex2rgb("#5a1a40"), LIGHT, "eclipse"),
    "hallowed_ward": (hex2rgb("#c9a040"), LIGHT2, "rays"),
    "wildfire": (FIRE, hex2rgb("#7ad04a"), "flames"),
    "overgrowth": (NATURE, NATURE2, "leaves"),
    "sanctuary": (hex2rgb("#7ac060"), LIGHT2, "crosses"),
    "blight_garden": (hex2rgb("#6a8a1a"), POISON2, "bubbles"),
    "frost_roots": (hex2rgb("#6ab0d0"), NATURE2, "roots"),
    "ember_patch": (hex2rgb("#ff7a2a"), ARCANE, "flames"),
    "singularity": (VOID, hex2rgb("#a8a0ff"), "spiral"),
    "gravity_well": (hex2rgb("#3a2e8a"), hex2rgb("#8a80ff"), "rings"),
    # Phase 2 enemy/biome fields
    "spore_cloud": (hex2rgb("#7a8a3a"), hex2rgb("#d0e070"), "bubbles"),
    "ice_cover": (hex2rgb("#8ad0f0"), hex2rgb("#e8fbff"), "cracks"),
}


# Fields owned by hero skills (heroes.json "fields"); filled in as heroes are added.
HERO_FIELD_STYLE = {
    "pylon": (hex2rgb("#5a4ab0"), BOLT2, "rings"), "pylon_network": (hex2rgb("#6a5ad0"), BOLT2, "rays"),
    "pylon_charger": (hex2rgb("#3a6ad0"), hex2rgb("#7cff9a"), "rings"),
    "stone_wall": (hex2rgb("#8a6a4a"), hex2rgb("#d9b56a"), "cracks"), "stone_bastion": (hex2rgb("#7a6a5a"), STEEL, "cracks"),
    "spike_wall": (hex2rgb("#9a6a3a"), hex2rgb("#ffd35a"), "cracks"),
}


def field(fid, s=256, style=None):
    """Top-down field sprite filling a unit circle (scaled at runtime to the field radius)."""
    a, b, pattern = style or FIELD_STYLE[fid]
    cv = Canvas(s, s)
    ctx = cv.ctx
    c = s / 2
    r = s / 2 - 8
    rnd = random.Random(sum(map(ord, fid)) * 13)
    grad = cairo.RadialGradient(c, c, 4, c, c, r)
    grad.add_color_stop_rgba(0, *a, 0.55)
    grad.add_color_stop_rgba(0.75, *a, 0.38)
    grad.add_color_stop_rgba(1, *a, 0.0)
    ctx.arc(c, c, r, 0, 2 * math.pi)
    ctx.set_source(grad)
    ctx.fill()
    stroke(ctx, lambda x: ellipse_path(x, c, c, r - 6, r - 6), b, 5, 0.75)
    if pattern == "eclipse":
        flat(ctx, lambda x: ellipse_path(x, c, c, r * 0.42, r * 0.42), hex2rgb("#1a0612"), 0.7)
        stroke(ctx, lambda x: ellipse_path(x, c, c, r * 0.46, r * 0.46), b, 6, 0.85)
    elif pattern == "rays":
        for k in range(10):
            ang = k * math.pi / 5
            stroke(ctx, lambda x, ang=ang: (x.move_to(c + math.cos(ang) * r * 0.2, c + math.sin(ang) * r * 0.2),
                                            x.line_to(c + math.cos(ang) * r * 0.8, c + math.sin(ang) * r * 0.8)), b, 5, 0.7)
    elif pattern == "flames":
        for _ in range(9):
            x0, y0 = c + rnd.uniform(-r * 0.6, r * 0.6), c + rnd.uniform(-r * 0.6, r * 0.6)
            glyphs.g_flame(ctx, x0, y0, rnd.uniform(26, 40), a, b)
    elif pattern == "leaves":
        for _ in range(10):
            x0, y0 = c + rnd.uniform(-r * 0.6, r * 0.6), c + rnd.uniform(-r * 0.6, r * 0.6)
            glyphs.g_leaf(ctx, x0, y0, rnd.uniform(22, 34), b)
    elif pattern == "crosses":
        for k in range(5):
            ang = k * 2 * math.pi / 5 + 0.4
            glyphs.g_cross(ctx, c + math.cos(ang) * r * 0.5, c + math.sin(ang) * r * 0.5, 30, b)
        glyphs.g_leaf(ctx, c, c, 40, NATURE2)
    elif pattern == "bubbles":
        for _ in range(14):
            x0, y0 = c + rnd.uniform(-r * 0.65, r * 0.65), c + rnd.uniform(-r * 0.65, r * 0.65)
            rr = rnd.uniform(6, 14)
            paint(ctx, lambda x, x0=x0, y0=y0, rr=rr: ellipse_path(x, x0, y0, rr, rr), POISON, lw=2.5, hi=False, alpha=0.9)
        for _ in range(4):
            x0, y0 = c + rnd.uniform(-r * 0.5, r * 0.5), c + rnd.uniform(-r * 0.5, r * 0.5)
            glyphs.g_sprout(ctx, x0, y0, 30, b)
    elif pattern == "roots":
        for k in range(6):
            ang = k * math.pi / 3 + 0.2
            pts = [(c + math.cos(ang + t * 0.15) * r * (0.15 + t * 0.13), c + math.sin(ang + t * 0.15) * r * (0.15 + t * 0.13)) for t in range(6)]
            outlined_line(ctx, pts, b, 5, 11)
        for _ in range(8):
            sparkle(ctx, c + rnd.uniform(-r * 0.6, r * 0.6), c + rnd.uniform(-r * 0.6, r * 0.6), rnd.uniform(5, 9), ICE2, 0.9)
    elif pattern == "spiral":
        for k in range(4):
            a0 = k * math.pi / 2
            pts = [(c + math.cos(a0 + t * 0.55) * (r * 0.9 - t * 11), c + math.sin(a0 + t * 0.55) * (r * 0.9 - t * 11)) for t in range(10)]
            stroke(ctx, lambda x, pts=pts: smooth_open(x, pts), b, 6, 0.85)
        flat(ctx, lambda x: ellipse_path(x, c, c, r * 0.16, r * 0.16), VOID2, 0.9)
    elif pattern == "cracks":
        for _ in range(7):
            x0, y0 = c + rnd.uniform(-r * 0.6, r * 0.6), c + rnd.uniform(-r * 0.6, r * 0.6)
            pts = [(x0, y0)]
            for k in range(3):
                pts.append((pts[-1][0] + rnd.uniform(-18, 18), pts[-1][1] + rnd.uniform(-18, 18)))
            stroke(ctx, lambda x, pts=pts: (x.move_to(*pts[0]), [x.line_to(*q) for q in pts[1:]]), b, 4, 0.85)
        for _ in range(6):
            x0, y0 = c + rnd.uniform(-r * 0.55, r * 0.55), c + rnd.uniform(-r * 0.55, r * 0.55)
            glyphs.g_rock(ctx, x0, y0, rnd.uniform(18, 28), a)
    elif pattern == "rings":
        for k in range(4):
            rr = r * (0.85 - k * 0.2)
            stroke(ctx, lambda x, rr=rr: ellipse_path(x, c, c, rr, rr), b, 4, 0.75)
    return cv


# ============================================================================ traits

TRAIT_ART = {
    # id: (glyph, badge colour, glyph colour)
    "pyromaniac": ("flame", hex2rgb("#7a2a1a"), FIRE), "twin_caster": ("echo", hex2rgb("#4a2a7a"), ARCANE),
    "elementalist": ("gem", hex2rgb("#2a4a7a"), None), "guardians_soul": ("shield", hex2rgb("#2a4a6a"), STEEL),
    "quick_channel": ("hourglass", hex2rgb("#2a5a6a"), None), "steadfast": ("rock", hex2rgb("#5a4a3a"), None),
    "fragile_genius": ("book", hex2rgb("#5a2a5a"), None), "efficient_ward": ("cross", hex2rgb("#2a6a4a"), None),
    "last_stand": ("heart", hex2rgb("#6a1a2a"), RED), "executioner": ("dagger", hex2rgb("#3a2a3a"), STEEL),
    "tactician": ("dots", hex2rgb("#4a4a2a"), GOLD), "arcane_reservoir": ("battery", hex2rgb("#3a2a6a"), ARCANE),
}


def trait_icon(tid, s=96):
    cv = Canvas(s, s)
    g, col, gcol = TRAIT_ART[tid]
    icons.badge(cv.ctx, s, col, "hex")
    stroke(cv.ctx, lambda c: poly_path(c, [(s / 2 + math.cos(t) * (s / 2 - 14), s / 2 + math.sin(t) * (s / 2 - 14))
                                            for t in [k * math.pi / 3 + math.pi / 6 for k in range(6)]]), GOLD, 3, 0.8)
    glyph(cv.ctx, g, s / 2, s / 2, s * 0.56, gcol)
    return cv


# New relic icons reuse the launch relic badge (family frame + rarity ring + glyph).
icons.RELIC_ART.update({
    "dawnstone": ("sun", LIGHT, None), "nightfall_censer": ("moon", SHADOW, None), "verdict_scale": ("skull", (0.95, 0.9, 0.92), SHADOW),
    "sunforged_aegis": ("shield", LIGHT, None), "prism_of_dusk": ("gem", ARCANE, None), "pyre_heart": ("heart", FIRE, None),
    "overclock_coil": ("battery", STEEL, BOLT2), "tidecaller_pearl": ("drop", WATER2, None), "glacier_plate": ("shield", ICE, None),
    "zephyr_sash": ("swirl", WIND, None), "masons_level": ("tower", hex2rgb("#9a8f86"), GOLD), "radiant_lens": ("lens", LIGHT2, LIGHT),
    "shadow_contract": ("scroll", hex2rgb("#3a1a2a"), SHADOW), "eclipse_engine": ("moon", LIGHT, None), "warding_bell": ("bell", ICE2, None),
    "executioners_oath": ("dagger", STEEL, RED), "kite_banner": ("shield", hex2rgb("#4a6aa0"), GOLD), "focus_crystal": ("gem", hex2rgb("#7fe8ff"), None),
    "twilight_hourglass": ("hourglass", SHADOW, LIGHT), "cleansing_chime": ("bell", LIGHT, None),
    "twilight_crown": ("crown", SHADOW, LIGHT), "aegis_of_ages": ("shield", GOLD, None),
})
icons.RELIC_EXTRA.update({"eclipse_engine": "gear", "twilight_crown": "moon", "aegis_of_ages": "star"})

# Expansion Phase 2: Nature/Poison relics, cards and hero skill fields.
icons.RELIC_ART.update({
    "verdant_seed": ("sprout", NATURE2, None), "venom_vial": ("drop", POISON, None), "thornmail": ("shield", NATURE, NATURE2),
    "plague_bell": ("bell", POISON, None), "blight_lantern": ("lens", POISON, NATURE2), "gardeners_trowel": ("sprout", hex2rgb("#a0703f"), NATURE2),
    "antidote_flask": ("drop", hex2rgb("#7cff9a"), None), "worldroot_heart": ("heart", NATURE, None), "rot_bloom": ("leaf", POISON, NATURE),
})
icons.RELIC_EXTRA.update({"plague_bell": "skull", "worldroot_heart": "sprout", "rot_bloom": "skull"})
icons.CARD_ART.update({
    "wild_growth": ("sprout", NATURE2), "toxic_pact": ("drop", POISON), "overgrowth_theory": ("leaf", NATURE),
    "toxic_shock_theory": ("bolt", POISON), "spec_liora_bramble": ("sprout", NATURE), "spec_thalen_heartwood": ("shield", NATURE),
    "spec_vesper_potency": ("drop", POISON), "spec_sable_triage": ("cross", POISON),
})
HERO_FIELD_STYLE.update({
    "toxic_patch": (hex2rgb("#7a9a2a"), POISON, "bubbles"), "lingering_miasma": (hex2rgb("#5a3a7a"), POISON, "bubbles"),
    "spore_garden": (NATURE, NATURE2, "leaves"),
})


# Expansion Phase 3: hero skill fields (Arcane/Void and the remaining specialists).
HERO_FIELD_STYLE.update({
    "rune_circle": (ARCANE, ARCANE2, "rings"), "grand_rune": (ARCANE, GOLD, "rays"), "sigil_ward": (ARCANE, LIGHT2, "crosses"),
    "rift": (VOID, VOID2, "spiral"), "deep_rift": (hex2rgb("#1a1440"), VOID2, "spiral"),
    "void_ward": (VOID, hex2rgb("#a8a0ff"), "rings"), "null_bastion": (hex2rgb("#2a2060"), LIGHT2, "rings"),
    "portal_ward": (VOID, ARCANE2, "spiral"), "river_stream": (WATER, WATER2, "bubbles"), "flood_stream": (hex2rgb("#2a5aa0"), WATER2, "bubbles"),
    "healing_stream": (WATER2, NATURE2, "crosses"), "gale_snare": (WIND, WIND2, "spiral"),
    "gloom_mire": (SHADOW, SHADOW2, "bubbles"), "dread_mire": (hex2rgb("#2a0a20"), SHADOW2, "eclipse"),
})

# Expansion Phase 3 relics.
icons.RELIC_ART.update({
    "echo_prism": ("mirror", ARCANE, None), "rune_inkwell": ("book", ARCANE, ARCANE2), "void_lodestone": ("gem", VOID, None),
    "null_shard": ("crack_shield", VOID, None), "scribe_quill": ("feather", FIRE, None), "river_pearl": ("drop", WATER2, None),
    "copper_quiver": ("quiver", hex2rgb("#c87a3a"), BOLT2), "frostbreaker_hammer": ("fist", ICE, None), "tempest_chime": ("bell", WIND, None),
    "granite_knuckles": ("fist", EARTH, None), "sun_hymnal": ("book", LIGHT, None), "gloom_lantern": ("eye", SHADOW, None),
    "infinite_codex": ("book", ARCANE, GOLD), "event_horizon_core": ("gem", hex2rgb("#140c38"), VOID), "ember_codex": ("scroll", FIRE, GOLD),
    "tidal_engine": ("gear", WATER, ARCANE), "astral_compass": ("target", LIGHT, VOID),
    "grand_grimoire": ("book", GOLD, ARCANE), "event_singularity": ("gem", VOID, ARCANE), "ember_testament": ("scroll", FIRE, RED),
    "ocean_heart": ("heart", WATER, None), "dusk_hymn": ("book", SHADOW, LIGHT),
})
icons.RELIC_EXTRA.update({"infinite_codex": "star", "event_horizon_core": "star", "ember_codex": "flame", "tidal_engine": "drop",
                          "astral_compass": "star", "grand_grimoire": "echo", "event_singularity": "star", "dusk_hymn": "moon"})

icons.CARD_ART.update({"arcane_accord": ("rune", ARCANE), "void_covenant": ("void_ring", VOID)})
