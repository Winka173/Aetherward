"""UI skin textures (9-slice). Text is never baked into images (localization); the IMGUI skin draws
labels on top. Borders are documented in import_settings.json for Unity's sprite border and used
by GUIStyle.border at runtime."""
import math
import cairo
from toolkit import INK, Canvas, hex2rgb, mix, shade, light, paint, flat, stroke, glow, sparkle, rrect_path, ellipse_path, poly_path, star_path

NAVY = hex2rgb("#1d2140")
NAVY2 = hex2rgb("#2a3060")
GOLD = hex2rgb("#ffd35a")
TEAL = hex2rgb("#5fe0d0")


def panel(kind="dark", s=128):
    cv = Canvas(s, s)
    ctx = cv.ctx
    m = 6
    if kind == "dark":
        top, bottom, rim, inner = NAVY2, NAVY, GOLD, TEAL
    elif kind == "light":
        top, bottom, rim, inner = hex2rgb("#fbf3df"), hex2rgb("#ead8b2"), hex2rgb("#8a5a34"), hex2rgb("#ffffff")
    elif kind == "glass":
        top, bottom, rim, inner = hex2rgb("#2a3060"), hex2rgb("#151830"), hex2rgb("#7fe8ff"), hex2rgb("#7fe8ff")
    else:  # danger
        top, bottom, rim, inner = hex2rgb("#5a1a2a"), hex2rgb("#2a0a14"), hex2rgb("#ff5a6a"), hex2rgb("#ff9aa8")
    grad = cairo.LinearGradient(0, 0, 0, s)
    grad.add_color_stop_rgb(0, *top)
    grad.add_color_stop_rgb(1, *bottom)
    rrect_path(ctx, m, m, s - 2 * m, s - 2 * m, 22)
    ctx.set_source(grad)
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(8)
    ctx.stroke()
    stroke(ctx, lambda c: rrect_path(c, m + 7, m + 7, s - 2 * m - 14, s - 2 * m - 14, 16), rim, 3.5, 0.95)
    stroke(ctx, lambda c: (c.move_to(m + 24, m + 12), c.line_to(s - m - 24, m + 12)), inner, 2, 0.35)
    for (x, y) in ((m + 7, m + 7), (s - m - 7, m + 7), (m + 7, s - m - 7), (s - m - 7, s - m - 7)):
        paint(ctx, lambda c, x=x, y=y: star_path(c, x, y, 7, 3, 4, 0), rim, lw=2, hi=False)
    if kind == "glass":
        # translucent centre for HUD
        cv2 = Canvas(s, s)
        c2 = cv2.ctx
        c2.set_source_surface(cv.surface, 0, 0)
        c2.paint_with_alpha(0.88)
        return cv2
    return cv


def button(state="normal", kind="primary", w=192, h=96):
    cv = Canvas(w, h)
    ctx = cv.ctx
    base = {"primary": hex2rgb("#ffb23a"), "secondary": hex2rgb("#5a8aff"), "danger": hex2rgb("#ff5a6a"), "ghost": hex2rgb("#3a4270")}[kind]
    if state == "hover":
        base = light(base, 0.18)
    elif state == "pressed":
        base = shade(base, 0.2)
    elif state == "disabled":
        g = 0.3 * base[0] + 0.59 * base[1] + 0.11 * base[2]
        base = (g * 0.7, g * 0.7, g * 0.78)
    m = 6
    drop = 0 if state == "pressed" else 8
    flat(ctx, lambda c: rrect_path(c, m, m + 8, w - 2 * m, h - 2 * m - 8, 26), shade(base, 0.55))
    y0 = m + 8 - drop
    grad = cairo.LinearGradient(0, y0, 0, y0 + h - 2 * m - 8)
    grad.add_color_stop_rgb(0, *light(base, 0.25))
    grad.add_color_stop_rgb(1, *base)
    rrect_path(ctx, m, y0, w - 2 * m, h - 2 * m - 8, 26)
    ctx.set_source(grad)
    ctx.fill()
    flat(ctx, lambda c: rrect_path(c, m + 12, y0 + 6, w - 2 * m - 24, (h - 2 * m - 8) * 0.34, 14), (1, 1, 1), 0.22)
    stroke(ctx, lambda c: rrect_path(c, m, m, w - 2 * m, h - 2 * m, 26), INK, 7)
    return cv


def card_frame(rarity, w=256, h=360):
    cols = {"common": hex2rgb("#a8b0c0"), "rare": hex2rgb("#4aa0ff"), "epic": hex2rgb("#b07aff"), "legendary": hex2rgb("#ffc23a"),
            "cursed": hex2rgb("#ff3a5a")}
    rc = cols[rarity]
    cv = Canvas(w, h)
    ctx = cv.ctx
    m = 8
    if rarity in ("legendary", "epic", "cursed"):
        glow(ctx, w / 2, h / 2, w * 0.7, rc, 0.35)
    grad = cairo.LinearGradient(0, 0, 0, h)
    grad.add_color_stop_rgb(0, *mix(NAVY2, rc, 0.18))
    grad.add_color_stop_rgb(1, *NAVY)
    rrect_path(ctx, m, m, w - 2 * m, h - 2 * m, 24)
    ctx.set_source(grad)
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(8)
    ctx.stroke()
    stroke(ctx, lambda c: rrect_path(c, m + 8, m + 8, w - 2 * m - 16, h - 2 * m - 16, 18), rc, 5)
    # header band for title
    flat(ctx, lambda c: rrect_path(c, m + 16, m + 18, w - 2 * m - 32, 46, 12), shade(rc, 0.45), 0.9)
    for (x, y) in ((m + 8, m + 8), (w - m - 8, m + 8), (m + 8, h - m - 8), (w - m - 8, h - m - 8)):
        paint(ctx, lambda c, x=x, y=y: ellipse_path(c, x, y, 8, 8), rc, lw=3, hi=False)
    return cv


def bar(kind="bg", w=128, h=40):
    cv = Canvas(w, h)
    ctx = cv.ctx
    if kind == "bg":
        flat(ctx, lambda c: rrect_path(c, 3, 3, w - 6, h - 6, (h - 6) / 2), hex2rgb("#141428"))
        stroke(ctx, lambda c: rrect_path(c, 3, 3, w - 6, h - 6, (h - 6) / 2), INK, 5)
    else:
        grad = cairo.LinearGradient(0, 0, 0, h)
        grad.add_color_stop_rgb(0, 1, 1, 1)
        grad.add_color_stop_rgb(1, 0.78, 0.78, 0.82)
        rrect_path(ctx, 6, 6, w - 12, h - 12, (h - 12) / 2)
        ctx.set_source(grad)
        ctx.fill()
        flat(ctx, lambda c: rrect_path(c, 12, 8, w - 24, (h - 12) * 0.35, 6), (1, 1, 1), 0.5)
    return cv


def tooltip(s=96):
    cv = Canvas(s, s)
    ctx = cv.ctx
    flat(ctx, lambda c: rrect_path(c, 4, 4, s - 8, s - 8, 14), hex2rgb("#0f1124"), 0.94)
    stroke(ctx, lambda c: rrect_path(c, 4, 4, s - 8, s - 8, 14), GOLD, 3, 0.8)
    return cv


def vignette(w=512, h=288):
    cv = Canvas(w, h)
    ctx = cv.ctx
    grad = cairo.RadialGradient(w / 2, h / 2, h * 0.3, w / 2, h / 2, w * 0.62)
    grad.add_color_stop_rgba(0, 0, 0, 0, 0)
    grad.add_color_stop_rgba(1, 0.03, 0.02, 0.08, 0.65)
    ctx.set_source(grad)
    ctx.paint()
    return cv


def title_logo(w=1024, h=320):
    """Game logo artwork WITHOUT text glyph rendering dependency: crystal emblem + ribbon. The title
    text itself is drawn by the UI with the localized font so the brand name stays editable."""
    cv = Canvas(w, h)
    ctx = cv.ctx
    cx = w / 2
    glow(ctx, cx, h / 2, h * 0.9, hex2rgb("#7fe8ff"), 0.35)
    paint(ctx, lambda c: poly_path(c, [(cx - 420, h * 0.62), (cx - 380, h * 0.42), (cx + 380, h * 0.42), (cx + 420, h * 0.62),
                                         (cx + 380, h * 0.82), (cx - 380, h * 0.82)]), hex2rgb("#3a2a7a"), lw=8, hi_size=0.8)
    stroke(ctx, lambda c: poly_path(c, [(cx - 400, h * 0.62), (cx - 366, h * 0.46), (cx + 366, h * 0.46), (cx + 400, h * 0.62),
                                          (cx + 366, h * 0.78), (cx - 366, h * 0.78)]), GOLD, 3.5)
    pts = [(cx, h * 0.04), (cx + 52, h * 0.3), (cx + 34, h * 0.5), (cx, h * 0.58), (cx - 34, h * 0.5), (cx - 52, h * 0.3)]
    paint(ctx, lambda c: poly_path(c, pts), hex2rgb("#7fe8ff"), lw=8, hi_size=0.9)
    sparkle(ctx, cx - 14, h * 0.18, 16)
    return cv
