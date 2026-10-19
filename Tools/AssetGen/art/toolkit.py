"""Vector drawing toolkit for Aetherward's procedural cartoon art.

Style rules (Docs/ART_DIRECTION.md): thick dark ink outline, flat base colour, one cel shade on the
lower/right side, one soft highlight on the upper/left, saturated element accents, chunky readable
silhouettes. Everything is deterministic so assets can be regenerated bit-for-bit.
"""
import math
import cairo

INK = (0.11, 0.09, 0.19)          # outline colour (deep violet-black)
INK_SOFT = (0.20, 0.16, 0.30)


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def shade(c, amount=0.28):
    """Cel shade: darker and slightly cooler/more saturated."""
    cool = (0.18, 0.14, 0.36)
    return mix(c, cool, amount)


def light(c, amount=0.45):
    return mix(c, (1.0, 0.98, 0.92), amount)


def grey(c, amount=0.75):
    g = 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
    return mix(c, (g * 0.85, g * 0.85, g * 0.95), amount)


class Canvas:
    def __init__(self, w, h, scale=1.0):
        self.w, self.h = w, h
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        self.ctx = cairo.Context(self.surface)
        self.ctx.scale(scale, scale)
        self.ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        self.ctx.set_line_cap(cairo.LINE_CAP_ROUND)

    def save(self, path):
        self.surface.write_to_png(path)


# ---------------------------------------------------------------------------- paths

def smooth_closed(ctx, pts, tension=0.5):
    """Closed Catmull-Rom spline through points (organic blobby shapes)."""
    n = len(pts)
    ctx.move_to(*pts[0])
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) * tension / 3.0, p1[1] + (p2[1] - p0[1]) * tension / 3.0)
        c2 = (p2[0] - (p3[0] - p1[0]) * tension / 3.0, p2[1] - (p3[1] - p1[1]) * tension / 3.0)
        ctx.curve_to(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    ctx.close_path()


def smooth_open(ctx, pts, tension=0.5):
    n = len(pts)
    ctx.move_to(*pts[0])
    for i in range(n - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < n else pts[i + 1]
        c1 = (p1[0] + (p2[0] - p0[0]) * tension / 3.0, p1[1] + (p2[1] - p0[1]) * tension / 3.0)
        c2 = (p2[0] - (p3[0] - p1[0]) * tension / 3.0, p2[1] - (p3[1] - p1[1]) * tension / 3.0)
        ctx.curve_to(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])


def ellipse_path(ctx, cx, cy, rx, ry, rot=0.0):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(rot)
    ctx.scale(max(rx, 0.01), max(ry, 0.01))
    ctx.new_sub_path()
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


def rrect_path(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def poly_path(ctx, pts):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()


def star_path(ctx, cx, cy, r_out, r_in, n, rot=-math.pi / 2):
    pts = []
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = rot + i * math.pi / n
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    poly_path(ctx, pts)


# ---------------------------------------------------------------------------- painting

def paint(ctx, path_fn, color, lw=6.0, shade_dir=(0.35, 0.45), shade_amt=0.30, hi=True,
          hi_pos=(-0.3, -0.35), hi_size=0.45, outline=True, alpha=1.0, ink=INK):
    """Fill a shape with base colour + cel shade + highlight, then ink outline.

    path_fn(ctx) builds the path. The shade is the same path offset toward shade_dir (fraction of
    the shape's extent) and subtracted, which produces a crisp crescent like hand-inked cel art.
    """
    ctx.save()
    ctx.new_path()
    path_fn(ctx)
    x0, y0, x1, y1 = ctx.fill_extents()
    w, h = max(x1 - x0, 1), max(y1 - y0, 1)
    ctx.clip_preserve()
    ctx.set_source_rgba(*color, alpha)
    ctx.fill()
    if shade_amt > 0:
        # crescent shade: everything not covered by the shifted shape
        ctx.push_group()
        ctx.set_source_rgba(*shade(color, shade_amt), alpha)
        ctx.paint()
        ctx.set_operator(cairo.OPERATOR_CLEAR)
        ctx.translate(-shade_dir[0] * w * 0.22, -shade_dir[1] * h * 0.22)
        ctx.new_path()
        path_fn(ctx)
        ctx.fill()
        ctx.pop_group_to_source()
        ctx.paint()
    if hi:
        cx, cy = (x0 + x1) / 2 + hi_pos[0] * w, (y0 + y1) / 2 + hi_pos[1] * h
        grad = cairo.RadialGradient(cx, cy, 0, cx, cy, max(w, h) * hi_size)
        lc = light(color, 0.55)
        grad.add_color_stop_rgba(0, *lc, 0.55 * alpha)
        grad.add_color_stop_rgba(1, *lc, 0.0)
        ctx.set_source(grad)
        ctx.paint()
    ctx.restore()
    if outline and lw > 0:
        ctx.save()
        ctx.new_path()
        path_fn(ctx)
        ctx.set_source_rgba(*ink, alpha)
        ctx.set_line_width(lw)
        ctx.stroke()
        ctx.restore()


def flat(ctx, path_fn, color, alpha=1.0):
    ctx.save()
    ctx.new_path()
    path_fn(ctx)
    ctx.set_source_rgba(*color, alpha)
    ctx.fill()
    ctx.restore()


def stroke(ctx, path_fn, color=INK, lw=4.0, alpha=1.0):
    ctx.save()
    ctx.new_path()
    path_fn(ctx)
    ctx.set_source_rgba(*color, alpha)
    ctx.set_line_width(lw)
    ctx.stroke()
    ctx.restore()


def glow(ctx, cx, cy, r, color, alpha=0.6):
    grad = cairo.RadialGradient(cx, cy, 0, cx, cy, r)
    grad.add_color_stop_rgba(0, *color, alpha)
    grad.add_color_stop_rgba(0.45, *color, alpha * 0.45)
    grad.add_color_stop_rgba(1, *color, 0)
    ctx.save()
    ctx.set_source(grad)
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()


def sparkle(ctx, cx, cy, r, color=(1, 1, 1), alpha=0.95):
    ctx.save()
    ctx.new_path()
    star_path(ctx, cx, cy, r, r * 0.22, 4, rot=0)
    ctx.set_source_rgba(*color, alpha)
    ctx.fill()
    ctx.restore()


def outlined_line(ctx, pts, color, width, ink_width=None, smooth=True):
    """A thick coloured stroke with an ink border (for straps, whips, staff shafts)."""
    ink_width = ink_width if ink_width is not None else width + 7
    for col, lw in ((INK, ink_width), (color, width)):
        ctx.save()
        ctx.new_path()
        if smooth and len(pts) > 2:
            smooth_open(ctx, pts)
        else:
            ctx.move_to(*pts[0])
            for p in pts[1:]:
                ctx.line_to(*p)
        ctx.set_source_rgb(*col)
        ctx.set_line_width(lw)
        ctx.stroke()
        ctx.restore()
