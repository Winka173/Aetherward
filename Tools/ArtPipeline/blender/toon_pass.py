"""Toon pass shared by the Blender generators (art bible v3, Ravenswatch-like comic look).

Cycles renders the passes; the light is cut into three cel bands (violet shadow, mid, warm lit), the albedo is
Kuwahara-flattened, saturated and gradient-mapped per biome, and ink comes from object-id / depth breaks.
Usage inside a generator: toon_pass.configure(scene=sc, out=OUT, scale=SCALE, theme=THEME, biome=BIOME_ID, alpha=False);
toon_pass.toon_setup(); bpy.ops.render.render(); toon_pass.toon_compose(dst).
"""
import math
import os

import bpy
import numpy as np

CFG = {"scene": None, "out": None, "scale": 1.0, "theme": {}, "biome": None, "alpha": False, "combined": False}


def configure(**kw):
    CFG.update(kw)


def lin(hexstr):
    h = hexstr.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c) + (1.0,)


# ----------------------------------------------------------------------------------------------- toon (art bible v3)
# Ravenswatch-like comic look: Cycles renders the passes, then the light is cut into three cel bands with cool
# purple shadows and a warm lit tone, the albedo is flattened (Kuwahara) and pushed saturated, and Freestyle ink
# lines go on top. Thresholds come from the lit-ground percentile, so every biome's sun strength bands the same way.
TOON_SHADOW = (0.30, 0.27, 0.58)
TOON_MID = (0.80, 0.78, 0.88)
TOON_LIT = (1.10, 1.04, 0.90)
INK = "#1b1226"
# per-biome gradient map for the albedo (dark, mid, light) and how much of it replaces the scan's own colour
TOON_RAMPS = {
    "verdant_sanctuary": (("#2c3d2a", "#5f8c3e", "#e3cf9a"), 0.45),
    "molten_crater": (("#2a1a1e", "#8a3a22", "#f0b060"), 0.55),
    "frostfall_bastion": (("#2a3550", "#6f93c0", "#eaf2ff"), 0.55),
    "shattered_aether": (("#2a1c48", "#7a4fb0", "#e6c8ff"), 0.55),
    "stormspire_citadel": (("#232a3c", "#58708f", "#d8e0ea"), 0.5),
    "sunken_archive": (("#14303a", "#2f7f86", "#d8e8d0"), 0.55),
}


def toon_setup():
    sc = CFG["scene"]
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    vl = sc.view_layers[0]
    for attr in ("use_pass_diffuse_color", "use_pass_diffuse_direct", "use_pass_diffuse_indirect", "use_pass_glossy_direct",
                 "use_pass_emit"):
        setattr(vl, attr, True)
    vl.use_pass_z = True
    vl.use_pass_normal = True
    vl.use_pass_object_index = True
    sc.render.use_freestyle = False   # Freestyle's view map runs out of memory on this scene: ink comes from passes instead
    i = 0
    for o in sc.objects:
        if o.type in ("MESH", "CURVE"):
            i += 1
            o.pass_index = i
    # passes -> EXR files (the Kuwahara-flattened albedo is the painted base colour)
    sc.use_nodes = True
    ct = sc.node_tree
    for n_ in list(ct.nodes):
        ct.nodes.remove(n_)
    rl = ct.nodes.new("CompositorNodeRLayers")
    kw = ct.nodes.new("CompositorNodeKuwahara")
    try:
        kw.variation = "ANISOTROPIC"
    except Exception:  # noqa: BLE001
        pass
    if "Size" in kw.inputs:
        kw.inputs["Size"].default_value = max(3, int(13 * CFG["scale"]))
    elif hasattr(kw, "size"):
        kw.size = max(3, int(13 * CFG["scale"]))
    ct.links.new(rl.outputs["DiffCol"], kw.inputs["Image"])
    fo_ = ct.nodes.new("CompositorNodeOutputFile")
    fo_.base_path = os.path.join(CFG["out"], "passes")
    fo_.format.file_format = "OPEN_EXR"
    fo_.format.color_depth = "32"
    fo_.file_slots.clear()
    for name, sock_ in (("albedo", kw.outputs["Image"]), ("diffdir", rl.outputs["DiffDir"]), ("diffind", rl.outputs["DiffInd"]),
                        ("gloss", rl.outputs["GlossDir"]), ("emit", rl.outputs["Emit"]), ("depth", rl.outputs["Depth"]), ("normal", rl.outputs["Normal"]),
                        ("index", rl.outputs["IndexOB"])):
        fo_.file_slots.new(name)
        ct.links.new(sock_, fo_.inputs[name])
    comp_ = ct.nodes.new("CompositorNodeComposite")
    ct.links.new(rl.outputs["Image"], comp_.inputs["Image"])
    if CFG["combined"]:
        fo_.file_slots.new("image")
        ct.links.new(rl.outputs["Image"], fo_.inputs["image"])
    if CFG["alpha"]:
        fo_.file_slots.new("alpha")
        ct.links.new(rl.outputs["Alpha"], fo_.inputs["alpha"])


def _load_pass(name):
    d = os.path.join(CFG["out"], "passes")
    f = sorted(x for x in os.listdir(d) if x.startswith(name) and x.endswith(".exr"))[-1]
    img = bpy.data.images.load(os.path.join(d, f))
    img.colorspace_settings.name = "Non-Color"
    a = np.empty(img.size[0] * img.size[1] * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(img.size[1], img.size[0], 4)


def _step(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _shift_max(m, r):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r + r:
                out = np.maximum(out, np.roll(np.roll(m, dy, 0), dx, 1))
    return out


def ink_lines(depth, normal, index):
    """Comic ink from passes: object-id and depth breaks (silhouettes) everywhere, normal breaks (creases) on props
    only (the ground's bump would scribble), thickened to ~4 px at full size and softened one pixel for AA."""
    def grad(a):
        gx = np.abs(np.roll(a, -1, 1) - a)
        gy = np.abs(np.roll(a, -1, 0) - a)
        return np.maximum(gx, gy)
    obj = (grad(index) > 0.5).astype(np.float32)
    z = np.minimum(depth, 500.0)
    dz = grad(z) / np.maximum(z, 1e-3)
    sil = _step(0.008, 0.02, dz)
    ground = index == (np.bincount(index.astype(np.int64).ravel()).argmax())
    dn = 1.0 - np.einsum("ijk,ijk->ij", normal, np.roll(normal, -1, 1)).clip(-1, 1)
    dn = np.maximum(dn, 1.0 - np.einsum("ijk,ijk->ij", normal, np.roll(normal, -1, 0)).clip(-1, 1))
    crease = _step(0.6, 0.9, dn) * (~ground) * CFG["theme"].get("toon_crease", 0.0)   # creases off by default: displacement speckles
    e = np.maximum(np.maximum(obj, sil), crease)
    r = max(1, int(round(2 * CFG["scale"])))
    e = _shift_max(e, r)
    e = (e + np.roll(e, 1, 0) + np.roll(e, -1, 0) + np.roll(e, 1, 1) + np.roll(e, -1, 1)) / 5.0
    return np.clip(e * 1.15, 0, 1) * 0.92


def toon_compose(dst):
    sc = CFG["scene"]
    alb, ddir, dind, gl, em, dep, nor, idx = (_load_pass(n) for n in ("albedo", "diffdir", "diffind", "gloss", "emit", "depth", "normal",
                                                                      "index"))
    W3 = np.array([0.2126, 0.7152, 0.0722], np.float32)
    L = ddir[..., :3] @ W3
    ref = float(np.percentile(L[L > 1e-3], 80)) if (L > 1e-3).any() else 1.0
    d = L / max(ref, 1e-4)
    s1, s2 = _step(0.17, 0.23, d)[..., None], _step(0.60, 0.68, d)[..., None]
    S0, S1, S2 = (np.array(c, np.float32) for c in (TOON_SHADOW, TOON_MID, TOON_LIT))
    light = S0 + (S1 - S0) * s1 + (S2 - S1) * s2
    # coloured lights (braziers, crystal, lava) keep their hue inside the bands
    chroma = ddir[..., :3] / np.maximum(L[..., None], 1e-4)
    chroma = np.clip(chroma / np.maximum(chroma.max(-1, keepdims=True), 1e-4), 0, 1)
    warmth = _step(0.9, 2.5, d)[..., None]
    light = light * (1 - 0.6 * warmth + 0.6 * warmth * chroma) * (1 + 0.2 * warmth)   # hue kept, not blown to white
    Li = dind[..., :3] @ W3
    refi = float(np.percentile(Li[Li > 1e-4], 70)) if (Li > 1e-4).any() else 1.0
    light *= (0.82 + 0.18 * np.clip(Li / max(refi, 1e-5), 0, 1))[..., None]
    alpha = _load_pass("alpha")[..., 0] if CFG["alpha"] else None
    solid = alpha > 0.5 if alpha is not None else np.ones(alb.shape[:2], bool)
    a = alb[..., :3]
    lum = (a @ W3)[..., None]
    a = np.clip(lum + (a - lum) * CFG["theme"].get("toon_sat", 1.85), 0, 1)
    a *= CFG["theme"].get("toon_albedo", 0.23) / max(float((a @ W3)[solid].mean()), 1e-4)
    ramp, amt = TOON_RAMPS.get(CFG["biome"], (("#303030", "#808080", "#d0d0d0"), 0.0))
    if amt > 0:
        la = (a @ W3)[..., None]
        t = np.clip(la / max(float(np.percentile(la, 97)), 1e-4), 0, 1)
        c0, c1, c2 = (np.array(lin(h)[:3], np.float32) for h in ramp)
        g = np.where(t < 0.5, c0 + (c1 - c0) * (t / 0.5), c1 + (c2 - c1) * ((t - 0.5) / 0.5))
        a = a * (1 - amt) + g * amt
        a *= CFG["theme"].get("toon_albedo", 0.23) / max(float((a @ W3)[solid].mean()), 1e-4)
    # light scans (cobbles, marble) would blow out to white: roll the top of the albedo off softly
    la = (a @ W3)[..., None]
    knee = 0.36
    a *= np.where(la > knee, (knee + (la - knee) / (1 + 2.5 * (la - knee))) / np.maximum(la, 1e-4), 1.0)
    col = a * light + em[..., :3] + 0.22 * gl[..., :3]
    # soft shoulder: lit roads under the Crystal/brazier lights roll off instead of clipping to white (bloom glare)
    lc = (col @ W3)[..., None]
    sh = 0.55
    col *= np.where(lc > sh, (sh + (lc - sh) / (1 + 1.8 * (lc - sh))) / np.maximum(lc, 1e-4), 1.0)
    ia = ink_lines(dep[..., 0], nor[..., :3], idx[..., 0])[..., None]
    col = col * (1 - ia) + lin(INK)[:3] * ia
    al = alpha[..., None] if alpha is not None else np.ones_like(col[..., :1])
    out = np.concatenate([np.clip(col, 0, 64), al], -1).astype(np.float32)
    h, w = out.shape[:2]
    img = bpy.data.images.new("toon", w, h, float_buffer=True, alpha=alpha is not None)
    img.colorspace_settings.name = "Linear Rec.709"
    img.pixels.foreach_set(out.ravel())
    img.save_render(dst, scene=sc)
    print("TOON ref=%.4f ink=%.3f -> %s" % (ref, float((ia > 0.5).mean()), dst))



def toon_compose_combined(dst, bands=(35, 65, 88), keep=0.3):
    """Toon for emissive/glass props (the Crystal): flatten the beauty render's luminance into rank bands, keep its
    hue and some of its glass detail, add the same ink. Writes RGBA when CFG["alpha"]."""
    sc = CFG["scene"]
    img = _load_pass("image")
    dep, nor, idx = (_load_pass(n) for n in ("depth", "normal", "index"))
    alpha = _load_pass("alpha")[..., 0] if CFG["alpha"] else np.ones(img.shape[:2], np.float32)
    solid = alpha > 0.5
    W3 = np.array([0.2126, 0.7152, 0.0722], np.float32)
    rgb = img[..., :3] / np.maximum(alpha[..., None], 1e-4)          # un-premultiply
    L = rgb @ W3
    edges = np.percentile(L[solid], list(bands)) if solid.any() else np.zeros(len(bands))
    k = np.searchsorted(edges, L)
    lv = np.array([float(np.median(L[solid & (k == i)])) if (solid & (k == i)).any() else 0.0 for i in range(len(bands) + 1)])
    flat = rgb * (lv[k] / np.maximum(L, 1e-4))[..., None]
    col = flat * (1 - keep) + rgb * keep
    ia = ink_lines(dep[..., 0], nor[..., :3], idx[..., 0])[..., None]
    # the outer silhouette needs a contour too: alpha edge
    a_edge = np.clip(_shift_max((alpha > 0.5).astype(np.float32), max(1, int(round(2 * CFG["scale"])))) - (alpha > 0.5), 0, 1)
    col = col * (1 - ia) + lin(INK)[:3] * ia
    out_a = np.maximum(alpha, a_edge * 0.95)
    col = np.where(a_edge[..., None] > 0, np.array(lin(INK)[:3], np.float32), col)
    out = np.concatenate([np.clip(col, 0, 64) * out_a[..., None], out_a[..., None]], -1).astype(np.float32)
    h, w = out.shape[:2]
    im = bpy.data.images.new("toonc", w, h, float_buffer=True, alpha=True)
    im.colorspace_settings.name = "Linear Rec.709"
    im.alpha_mode = "PREMUL"
    im.pixels.foreach_set(out.ravel())
    sc.render.image_settings.color_mode = "RGBA"
    im.save_render(dst, scene=sc)
    print("TOONC ink=%.3f -> %s" % (float((ia > 0.5).mean()), dst))
