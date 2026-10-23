"""Aetherward battlefield environment — Blender 4.5 headless, Cycles (OPTIX), real geometry, lights and shadows.

  blender -b --factory-startup --python Tools/ArtPipeline/blender/sanctum_env.py -- \
      --arena Assets/_Aetherward/Resources/Content/arena.json --out ArtCache/Env/verdant [--samples 256] [--scale 1.0]

Camera contract (matches the game, see ArtProduction/ART_BIBLE.md §3):
  orthographic, elevation 38.3 deg (sin = 0.62), 34 x 17 world units, output 4096 x 2048 (PPU ~120.5, power of two).
  A ground point at game position (x, y) sits at Blender (x, y / 0.62, 0); height z rises on screen by z * cos(38.3).
Lighting contract (shared with the painted units):
  key = moon/sun from the upper-left FRONT (shadows fall up-right on screen, behind units), cool rim/fill, the
  Crystal as the strongest emissive (point light at the Crystal), warm braziers.
Outputs in --out: flat.png (RGB, final), layers/<NN_name>.png (RGBA passes for animation in Unity), env_meta.json
(light direction on screen for unit shadows, brazier/crystal screen positions for Unity glows and particles).
"""
import json
import math
import os
import random
import re
import sys

import bpy
import numpy as np
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default


ARENA = arg("--arena")
OUT = os.path.abspath(arg("--out", "ArtCache/Env/verdant"))
SAMPLES = int(arg("--samples", "256"))
SCALE = float(arg("--scale", "1.0"))          # render-size multiplier for quick previews (0.25 = draft)
SEED = int(arg("--seed", "7"))
SIN = 0.62
ELEV = math.asin(SIN)
COS = math.cos(ELEV)
VIEW_W, VIEW_H = float(arg("--view-w", "40")), float(arg("--view-h", "20"))   # 40 x 20 at 4096 x 2048 = PPU 102.4 (game sprite)
RES_X, RES_Y = int(arg("--res-x", "4096")), int(arg("--res-y", "2048"))   # R04 layout reference: 36 x 20.25 at 3344 x 1882
random.seed(SEED)
np.random.seed(SEED)
os.makedirs(os.path.join(OUT, "layers"), exist_ok=True)


def jsonc(path):
    t = open(path, encoding="utf-8").read()
    return json.loads(re.sub(r"^\s*//.*$", "", t, flags=re.M))


arena = jsonc(ARENA)
BIOME_ID = arg("--biome", "verdant_sanctuary")
BIOME = next(b for b in jsonc(os.path.join(os.path.dirname(ARENA), "biomes.json"))["biomes"] if b["id"] == BIOME_ID)
if isinstance(BIOME.get("arena"), dict):     # biome arenas are inline in biomes.json
    arena = BIOME["arena"]

# Same widening as the simulation (ContentDatabase.WorldScale): lanes, spawns, start nodes, hazards and covers.
WORLD_SCALE = float(arg("--world-scale", str(arena.get("scale", 1.3))))


def _scale_pts(pts):
    return [[p_[0] * WORLD_SCALE, p_[1] * WORLD_SCALE] for p_ in pts]


arena = dict(arena)
arena["lanes"] = [dict(l_, points=_scale_pts(l_["points"])) for l_ in arena["lanes"]]
arena["nodes"] = _scale_pts(arena["nodes"])
BIOME = dict(BIOME)
BIOME["hazards"] = [dict(h_, points=_scale_pts(h_.get("points", []))) for h_ in BIOME.get("hazards", [])]
BIOME["covers"] = [dict(c_, pos=_scale_pts([c_["pos"]])[0]) for c_ in BIOME.get("covers", [])]

# Per-biome look. "special" is the second terrain mask channel (moss in the sanctum): how it is drawn, how deep it
# sinks the ground, where it appears (fbm blobs, bands along some lanes, pools at the hazard points).
THEMES = {
    "verdant_sanctuary": dict(ground="burned_ground_01", rock="aerial_ground_rock", road="cobblestone_large_01", cliff="cliff_side",
                              dais="castle_wall_slates", ruin="broken_wall", dark="Rock064", special="moss", special_amount=0.85, special_scan="Moss002", hdri="kloppenheim_02_puresky",
                              special_depth=0.0, world=("#1a2a44", 0.35), sun=("#dfe6ff", 2.6), brazier="#62e0cf", rift="#c0304a",
                              tint="#c9ccd6", kinds=None),
    "molten_crater": dict(ground="cracked_red_ground", rock="dark_rock_02", road="patterned_slate_tiles", cliff="rock_boulder_cracked",
                          dais="castle_wall_slates", ruin="rock_boulder_cracked", dark="dark_rock_02", special="lava", special_amount=1.0,
                          special_depth=0.35, special_lanes=[0, 1], special_lo=0.7, special_hi=0.76, special_scan="Lava004", vent_scan="Lava001", hdri="dikhololo_night", world=("#2a1410", 0.3),
                          sun=("#ffd9b8", 2.0), brazier="#ff7a2a", rift="#ff5a1f", tint="#b8aca8",
                          kinds=["obsidian"] * 6 + ["pillar"] * 3 + ["broken"] * 6 + ["boulder"] * 6 + ["deadtree"] * 2 + ["tree"] * 2 + ["brazier"] * 2 + ["rocks"] * 8),
    "frostfall_bastion": dict(ground="rock_ground", rock="castle_wall_varriation", road="large_floor_tiles_02", cliff="marble_cliff_01",
                              dais="castle_wall_slates", ruin="castle_wall_varriation", dark="dark_rock", special="snow", special_amount=0.6, value=0.5, special_scan="Snow015", snowcap="Snow010A", frozen_scan="Ice003", hdri="kloppenheim_02_puresky",
                              special_depth=-0.04, special_lo=0.5, special_hi=0.74, world=("#2a3a55", 0.55), sun=("#e6eeff", 2.8),
                              brazier="#ffb35c", rift="#7fd8ff", tint="#d4d8e0",
                              kinds=["icecrystals"] * 6 + ["pillar"] * 5 + ["statue"] * 2 + ["arch"] * 2 + ["brazier"] * 3 + ["broken"] * 5 + ["boulder"] * 4 + ["tree"] * 2),
    "shattered_aether": dict(ground="Ground068", rock="rocks_ground_02", hdri="dikhololo_night", road="herringbone_pavement", cliff="dark_rock_02",
                             dais="castle_wall_slates", ruin="broken_wall", dark="dark_rock_02", special="void", special_amount=1.0,
                             special_depth=3.5, special_lo=0.55, special_hi=0.6, world=("#140c28", 0.4), sun=("#e8dcff", 2.4),
                             brazier="#b07cff", rift="#ff5fd2", tint="#c4c0d4",
                             kinds=["crystals"] * 8 + ["floatrock"] * 8 + ["statue"] * 2 + ["broken"] * 5 + ["pillar"] * 3 + ["brazier"] * 2),
    "stormspire_citadel": dict(ground="rocks_ground_05", rock="castle_wall_varriation", road="herringbone_pavement_02", cliff="Rock058",
                               dais="PavingStones138", ruin="Bricks097", hdri="moonless_golf", dark="dark_rock", special="puddle", special_amount=0.8,
                               special_depth=0.02, special_lo=0.6, special_hi=0.68, world=("#1c2230", 0.45), sun=("#d8e4ff", 2.2),
                               brazier="#9adcff", rift="#b06cff", tint="#c4c8d2",
                               kinds=["battlement"] * 6 + ["pillar"] * 6 + ["statue"] * 2 + ["brazier"] * 3 + ["broken"] * 5 + ["boulder"] * 3),
    "sunken_archive": dict(ground="marble_tiles", rock="floor_tiles_06" if False else "large_floor_tiles_02", road="old_planks_02",
                           cliff="castle_wall_varriation", dais="Marble012", ruin="castle_wall_varriation", dark="dark_wooden_planks", hdri="moonless_golf",
                           special="water", special_amount=1.0, special_depth=0.18, special_lanes=[2, 3], special_lo=0.55, special_hi=0.62,
                           world=("#0e2a34", 0.45), sun=("#d8f4ff", 2.2), brazier="#ffd27a", rift="#2aa6a4", tint="#c4ccd0",
                           kinds=["shelves"] * 8 + ["pillar"] * 6 + ["statue"] * 2 + ["brazier"] * 3 + ["broken"] * 4 + ["fallen"] * 3),
}
THEME = THEMES[BIOME_ID]


def G(x, y, z=0.0):
    """Game (screen) position -> Blender ground position."""
    return Vector((x, y / SIN, z))


def lin(hexstr):
    h = hexstr.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c) + (1.0,)


# ----------------------------------------------------------------------------------------------- scene
bpy.ops.wm.read_factory_settings(use_empty=True)
import addon_utils  # noqa: E402
EXT = {}
for _m in ("sapling_tree_gen", "ivygen", "cell_fracture", "archimesh", "extra_mesh_objects"):
    try:
        EXT[_m] = addon_utils.enable("bl_ext.blender_org." + _m, default_set=True) is not None
    except Exception:  # noqa: BLE001  (missing extension: the builders below fall back to primitives)
        EXT[_m] = False
print("EXTENSIONS", EXT)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
for kind in ("OPTIX", "CUDA"):
    try:
        prefs.compute_device_type = kind
        prefs.get_devices()
        if any(d.type == kind for d in prefs.devices):
            break
    except TypeError:
        continue
for d in prefs.devices:
    d.use = d.type != "CPU"
sc.cycles.device = "GPU"
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 6
sc.render.resolution_x = int(RES_X * SCALE)
sc.render.resolution_y = int(RES_Y * SCALE)
sc.render.resolution_percentage = 100
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Base Contrast"
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_depth = "16"
sc.render.image_settings.color_mode = "RGB"

world = bpy.data.worlds.new("Night")
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = lin(THEME["world"][0])
bg.inputs[1].default_value = THEME["world"][1]
_hdr = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                    "ArtCache", "polyhaven", THEME.get("hdri", "kloppenheim_02_puresky"), THEME.get("hdri", "kloppenheim_02_puresky") + "_2k.hdr")
if os.path.exists(_hdr) and not arena.get("walls"):   # soft, directional sky light (haven: flat sky, its sun casts a second shadow set) instead of a flat colour; the biome colour tints it
    wnt = world.node_tree
    env = wnt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(_hdr, check_existing=True)
    tintw = wnt.nodes.new("ShaderNodeMix")
    tintw.data_type = "RGBA"
    tintw.blend_type = "MULTIPLY"
    tintw.inputs["Factor"].default_value = 1.0
    wnt.links.new(env.outputs["Color"], [x for x in tintw.inputs if x.name == "A" and x.type == "RGBA"][0])
    [x for x in tintw.inputs if x.name == "B" and x.type == "RGBA"][0].default_value = tuple(min(1.0, c * 3.0) for c in lin(THEME["world"][0])[:3]) + (1.0,)
    wnt.links.new([x for x in tintw.outputs if x.name == "Result" and x.type == "RGBA"][0], bg.inputs[0])
    bg.inputs[1].default_value = THEME["world"][1] * 1.1

cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = "ORTHO"
cam.data.ortho_scale = VIEW_W
cam.data.clip_end = 400
D = 60.0
cam.location = (0, -D * COS, D * SIN)
cam.rotation_euler = (math.pi / 2 - ELEV, 0, 0)

# ----------------------------------------------------------------------------------------------- masks (ground space)
MARGIN = 2.0
GX0, GX1 = -VIEW_W / 2 - MARGIN, VIEW_W / 2 + MARGIN
GY0, GY1 = (-VIEW_H / 2 - MARGIN) / SIN, (VIEW_H / 2 + MARGIN) / SIN
MW, MH = 2048, int(2048 * (GY1 - GY0) / (GX1 - GX0))
gx = np.linspace(GX0, GX1, MW)[None, :].repeat(MH, 0)
gy = np.linspace(GY0, GY1, MH)[:, None].repeat(MW, 1)


def seg_dist(px, py, a, b):
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    vx, vy = bx - ax, by - ay
    t = np.clip(((px - ax) * vx + (py - ay) * vy) / max(vx * vx + vy * vy, 1e-9), 0, 1)
    return np.hypot(px - (ax + t * vx), py - (ay + t * vy))


lane_d = np.full((MH, MW), 1e9)
LANE_DS = []
for lane in arena["lanes"]:
    one = np.full((MH, MW), 1e9)
    pts = [(x, y / SIN) for x, y in lane["points"]] + [(0.0, 0.0)]
    # extend the spawn end beyond the screen so roads run off the image
    (x0, y0), (x1, y1) = pts[0], pts[1]
    ext = (x0 + (x0 - x1) * 0.6, y0 + (y0 - y1) * 0.6)
    pts = [ext] + pts
    for a, b in zip(pts, pts[1:]):
        one = np.minimum(one, seg_dist(gx, gy, a, b))
    LANE_DS.append(one)
    lane_d = np.minimum(lane_d, one)
HAVEN = bool(arena.get("walls"))   # walled keep layout (owner 2026-10-21): walls, gates, courtyard
DAIS_R = 2.8 if HAVEN else 3.9     # inner ring: Defensive holds on it, Balanced at its edge, Aggressive out on the field
dais_d = np.hypot(gx, gy + 0.887)          # centred on the Crystal (game y -0.55 -> ground -0.887)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def fbm(scale, octaves=4, seed=0):
    rng = np.random.RandomState(SEED + seed)
    acc = np.zeros((MH, MW))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        n = max(4, int(scale * 2 ** o))
        g = rng.rand(n + 1, int(n * MW / MH) + 2)
        yy = np.linspace(0, n, MH)
        xx = np.linspace(0, g.shape[1] - 1.001, MW)
        y0, x0 = yy.astype(int).clip(0, n - 1), xx.astype(int)
        fy, fx = (yy - y0)[:, None], (xx - x0)[None, :]
        fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
        v = (g[y0][:, x0] * (1 - fx) + g[y0][:, x0 + 1] * fx) * (1 - fy) + (g[y0 + 1][:, x0] * (1 - fx) + g[y0 + 1][:, x0 + 1] * fx) * fy
        acc += v * amp
        tot += amp
        amp *= 0.5
    return acc / tot


wobble = (fbm(6, 3, 1) - 0.5) * 0.55
road = 1 - smooth(0.62, 0.98, lane_d + wobble)                 # 1 on the processional roads
road_edge = smooth(0.45, 0.8, lane_d + wobble) * (1 - smooth(0.8, 1.15, lane_d + wobble))
dais = 1 - smooth(DAIS_R - 0.05, DAIS_R + 0.05, dais_d)
special = smooth(THEME.get("special_lo", 0.52), THEME.get("special_hi", 0.72), fbm(5, 4, 2))
for li in THEME.get("special_lanes", []):            # bands beside chosen lanes: lava under the bridges, flooded stairs
    if li < len(LANE_DS):
        dd = LANE_DS[li]
        wob = (fbm(9, 3, 11) - 0.5) * 0.8
        special = np.maximum(special, smooth(0.8, 1.15, dd + wob) * (1 - smooth(1.9, 2.6, dd + wob)) * smooth(DAIS_R + 0.5, DAIS_R + 1.5, np.hypot(gx, gy + 0.887)))
for hz in BIOME.get("hazards", []):                  # pools at the hazard points (vents, rifts, surges)
    for hx, hy in hz.get("points", []):
        r_ = hz.get("radius", 1.0)
        special = np.maximum(special, 1 - smooth(r_ * 0.55, r_ * 0.95, np.hypot(gx - hx, gy - hy / SIN)))
keep_clear = smooth(0.62, 1.0, lane_d) * (1 - dais)  # never on the roads or the dais
if THEME["special"] == "void":                        # floating islands: the abyss opens away from roads and the dais
    keep_clear = smooth(1.4, 2.4, lane_d) * (1 - smooth(DAIS_R + 0.6, DAIS_R + 0.4, np.hypot(gx, gy + 0.887)))
moss = special * keep_clear * THEME.get("special_amount", 0.85)
sx, sy = gx, gy * SIN                                           # screen coords
edge = np.maximum(smooth(VIEW_W / 2 - 3.2, VIEW_W / 2 + 0.5, np.abs(sx)), smooth(VIEW_H / 2 - 2.4, VIEW_H / 2 + 0.5, sy))
ridge = edge * smooth(0.9, 2.4, lane_d) * (0.6 + 0.8 * fbm(4, 4, 3))        # border ridges, cut open by every lane
near_drop = smooth(VIEW_H / 2 - 2.6, VIEW_H / 2 + 0.4, -sy) * smooth(0.9, 2.2, lane_d)
rift = (1 - smooth(0.0, 0.9, lane_d)) * smooth(VIEW_W / 2 - 7.5, VIEW_W / 2 - 1.0, np.maximum(np.abs(sx), np.abs(sy) * 1.7))
height = ridge * 2.6 - near_drop * 1.2 + (fbm(14, 4, 4) - 0.5) * 0.12 * (1 - road) - moss * THEME.get("special_depth", 0.0)
mask_rgb = np.stack([road, moss, rift, dais], -1)


def to_image(name, arr, channels=4):
    img = bpy.data.images.new(name, MW, MH, alpha=True, float_buffer=True)
    a = arr if arr.ndim == 3 else np.stack([arr] * 3 + [np.ones_like(arr)], -1)
    if a.shape[2] == 3:
        a = np.concatenate([a, np.ones(a.shape[:2] + (1,))], -1)
    img.colorspace_settings.name = "Non-Color"
    img.pixels.foreach_set(a.astype(np.float32).ravel())
    img.update()
    img.pack()          # keep the buffer for Cycles (generated images are otherwise re-filled on load)
    return img


IMG_MASK = to_image("masks", mask_rgb)
IMG_EDGE = to_image("road_edge", road_edge)

# ----------------------------------------------------------------------------------------------- terrain mesh (true displacement)
NX, NY = 1100, int(1100 * (GY1 - GY0) / (GX1 - GX0))
bpy.ops.mesh.primitive_grid_add(x_subdivisions=NX, y_subdivisions=NY, size=1)
ter = bpy.context.object
ter.name = "Terrain"
ter.scale = (GX1 - GX0, GY1 - GY0, 1)
bpy.ops.object.transform_apply(scale=True)
me = ter.data
co = np.empty(len(me.vertices) * 3)
me.vertices.foreach_get("co", co)
co = co.reshape(-1, 3)
u = ((co[:, 0] - GX0) / (GX1 - GX0) * (MW - 1)).astype(int).clip(0, MW - 1)
v = ((co[:, 1] - GY0) / (GY1 - GY0) * (MH - 1)).astype(int).clip(0, MH - 1)
co[:, 2] = height[v, u]
me.vertices.foreach_set("co", co.ravel())
me.update()
bpy.ops.object.shade_smooth()
uvl = me.uv_layers.active.data
loops_v = np.empty(len(me.loops), dtype=np.int64)
me.loops.foreach_get("vertex_index", loops_v)
uv = np.stack([(co[loops_v, 0] - GX0) / (GX1 - GX0), (co[loops_v, 1] - GY0) / (GY1 - GY0)], -1)
uvl.foreach_set("uv", uv.astype(np.float32).ravel())


def node(nt, kind, loc, **inputs):
    n = nt.nodes.new(kind)
    n.location = loc
    for k, val in inputs.items():
        if k in n.inputs:
            n.inputs[k].default_value = val
        else:
            setattr(n, k, val)
    return n


def sock(n, name, kind="RGBA", out=False):  # noqa: E302
    """Mix/MapRange nodes have one socket per data type with the same name; pick the one of `kind`."""
    for x in (n.outputs if out else n.inputs):
        if x.name == name and x.type == kind:
            return x
    raise KeyError(name)


PH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "ArtCache", "polyhaven")


ACG = os.path.join(os.path.dirname(PH), "ambientcg")


def acg_tex(mid, kind):
    """ambientCG CC0 map (Tools/ArtPipeline/fetch_ambientcg.py): kind = Color / Roughness / NormalGL / Displacement / Emission."""
    f = os.path.join(ACG, mid, "%s_2K-JPG_%s.jpg" % (mid, kind))
    if not os.path.exists(f):
        raise FileNotFoundError("run Tools/ArtPipeline/fetch_ambientcg.py first: %s %s" % (mid, kind))
    return f


def acg_image(nt, mid, kind, vec, loc, colorspace="sRGB"):
    n = nt.nodes.new("ShaderNodeTexImage")
    n.location = loc
    n.image = bpy.data.images.load(acg_tex(mid, kind), check_existing=True)
    n.image.colorspace_settings.name = colorspace
    nt.links.new(vec, n.inputs["Vector"])
    return n


def ph_tex(tid, kind):
    for ext in ("jpg", "png"):
        f = os.path.join(PH, tid, "%s_%s.%s" % (tid, kind, ext))
        if os.path.exists(f):
            return f
    raise FileNotFoundError("run Tools/ArtPipeline/fetch_polyhaven.py first: %s %s" % (tid, kind))


def scan_file(tid, kind):
    """Poly Haven (snake_case ids) or ambientCG (CamelCase ids) map of a given kind: diff / rough / nor_gl / disp."""
    if os.path.isdir(os.path.join(ACG, tid)):
        return acg_tex(tid, {"diff": "Color", "rough": "Roughness", "nor_gl": "NormalGL", "disp": "Displacement"}[kind])
    return ph_tex(tid, kind)


def pbr_nodes(nt, tid, vec, loc, projection="FLAT", blend=0.0):
    """Image nodes for a scan texture set: returns (colour socket, roughness socket, normal map node, height socket)."""
    out = {}
    for i, (kind, cs) in enumerate((("diff", "sRGB"), ("rough", "Non-Color"), ("nor_gl", "Non-Color"), ("disp", "Non-Color"))):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.location = (loc[0], loc[1] - i * 280)
        n.image = bpy.data.images.load(scan_file(tid, kind), check_existing=True)
        n.image.colorspace_settings.name = cs
        n.projection = projection
        n.projection_blend = blend
        nt.links.new(vec, n.inputs["Vector"])
        out[kind] = n
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.location = (loc[0] + 300, loc[1] - 560)
    nt.links.new(out["nor_gl"].outputs["Color"], nm.inputs["Color"])
    return out["diff"].outputs["Color"], out["rough"].outputs["Color"], nm, out["disp"].outputs["Color"]


def pbr_material(name, tid, scale, tint=None, value=1.0, projection="BOX", blend=0.25, normal=1.0, snow=True):
    """Props/dais: box-projected scan texture in object space, tinted toward the art-bible palette."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = node(nt, "ShaderNodeTexCoord", (-1400, 0))
    mp = node(nt, "ShaderNodeMapping", (-1200, 0))
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    col, rough, nm, _h = pbr_nodes(nt, tid, mp.outputs["Vector"], (-950, 300), projection, blend)
    hsv = node(nt, "ShaderNodeHueSaturation", (-500, 300))
    hsv.inputs["Saturation"].default_value = 0.55
    hsv.inputs["Value"].default_value = value
    nt.links.new(col, hsv.inputs["Color"])
    if tint:
        mix = node(nt, "ShaderNodeMix", (-250, 300), data_type="RGBA", blend_type="MULTIPLY")
        mix.inputs["Factor"].default_value = 1.0
        nt.links.new(hsv.outputs["Color"], sock(mix, "A"))
        sock(mix, "B").default_value = lin(tint)
        nt.links.new(sock(mix, "Result", out=True), bsdf.inputs["Base Color"])
    else:
        nt.links.new(hsv.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(rough, bsdf.inputs["Roughness"])
    nm.inputs["Strength"].default_value = normal
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    if THEME.get("snowcap") and snow:
        geo_ = node(nt, "ShaderNodeNewGeometry", (-500, -400))
        sz = node(nt, "ShaderNodeSeparateXYZ", (-300, -400))
        nt.links.new(geo_.outputs["Normal"], sz.inputs["Vector"])
        up_ = node(nt, "ShaderNodeMapRange", (-100, -400), **{"From Min": 0.55, "From Max": 0.8})
        nt.links.new(sz.outputs["Z"], up_.inputs["Value"])
        snow_img = acg_image(nt, THEME["snowcap"], "Color", mp.outputs["Vector"], (-300, -700))
        sm = node(nt, "ShaderNodeMix", (100, 100), data_type="RGBA")
        nt.links.new(up_.outputs["Result"], sm.inputs["Factor"])
        nt.links.new(bsdf.inputs["Base Color"].links[0].from_socket, sock(sm, "A"))
        nt.links.new(snow_img.outputs["Color"], sock(sm, "B"))
        nt.links.new(sock(sm, "Result", out=True), bsdf.inputs["Base Color"])
    return m


def stone_material(name, base, dark, scale, rough=0.85, bump=0.35):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = node(nt, "ShaderNodeTexCoord", (-1200, 0))
    nz = node(nt, "ShaderNodeTexNoise", (-900, 200), Scale=scale, Detail=8.0, Roughness=0.62)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = node(nt, "ShaderNodeValToRGB", (-650, 200))
    ramp.color_ramp.elements[0].color = lin(dark)
    ramp.color_ramp.elements[1].color = lin(base)
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = rough
    bp = node(nt, "ShaderNodeBump", (-300, -200), Strength=bump, Distance=0.05)
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def terrain_material():
    m = bpy.data.materials.new("Ground")
    m.use_nodes = True
    nt = m.node_tree
    L = nt.links
    bsdf = nt.nodes["Principled BSDF"]
    out = nt.nodes["Material Output"]
    uvn = node(nt, "ShaderNodeUVMap", (-1800, 0))
    mask = node(nt, "ShaderNodeTexImage", (-1550, 300), image=IMG_MASK, interpolation="Cubic")
    L.new(uvn.outputs["UV"], mask.inputs["Vector"])
    sep = node(nt, "ShaderNodeSeparateColor", (-1250, 300))
    L.new(mask.outputs["Color"], sep.inputs["Color"])
    geo = node(nt, "ShaderNodeTexCoord", (-1800, -400))
    # basalt / ash ground
    n1 = node(nt, "ShaderNodeTexNoise", (-1250, -100), Scale=1.6, Detail=10.0, Roughness=0.66)
    L.new(geo.outputs["Object"], n1.inputs["Vector"])
    r1 = node(nt, "ShaderNodeValToRGB", (-1000, -100))
    r1.color_ramp.elements[0].color = lin("#121317")
    r1.color_ramp.elements[1].color = lin("#3a3836")
    r1.color_ramp.elements.new(0.55).color = lin("#26272b")
    macro = node(nt, "ShaderNodeTexNoise", (-1500, -250), Scale=0.18, Detail=3.0)
    L.new(geo.outputs["Object"], macro.inputs["Vector"])
    madd = node(nt, "ShaderNodeMath", (-1150, -250), operation="MULTIPLY_ADD")
    L.new(n1.outputs["Fac"], madd.inputs[0])
    madd.inputs[1].default_value = 0.7
    L.new(macro.outputs["Fac"], madd.inputs[2])
    mul = node(nt, "ShaderNodeMath", (-1050, -150), operation="MULTIPLY")
    L.new(madd.outputs["Value"], mul.inputs[0])
    mul.inputs[1].default_value = 0.72
    L.new(mul.outputs["Value"], r1.inputs["Fac"])
    # cracks in the ground (voronoi edges)
    vc = node(nt, "ShaderNodeTexVoronoi", (-1250, -420), Scale=2.2, feature="DISTANCE_TO_EDGE")
    L.new(geo.outputs["Object"], vc.inputs["Vector"])
    crk = node(nt, "ShaderNodeMapRange", (-1000, -420), **{"From Min": 0.0, "From Max": 0.03, "To Min": 0.35, "To Max": 1.0})
    L.new(vc.outputs["Distance"], crk.inputs["Value"])
    g_col = node(nt, "ShaderNodeMix", (-750, -150), data_type="RGBA", blend_type="MULTIPLY")
    g_col.inputs["Factor"].default_value = 1.0
    L.new(r1.outputs["Color"], sock(g_col, "A"))
    L.new(crk.outputs["Result"], sock(g_col, "B"))
    # flagstone road: voronoi slabs with joints, worn lighter
    vs = node(nt, "ShaderNodeTexVoronoi", (-1250, 700), Scale=1.9, feature="DISTANCE_TO_EDGE", Randomness=0.75)
    L.new(geo.outputs["Object"], vs.inputs["Vector"])
    joint = node(nt, "ShaderNodeMapRange", (-1000, 700), **{"From Min": 0.0, "From Max": 0.045, "To Min": 0.0, "To Max": 1.0})
    L.new(vs.outputs["Distance"], joint.inputs["Value"])
    vcol = node(nt, "ShaderNodeTexVoronoi", (-1250, 950), Scale=1.9, feature="F1", Randomness=0.75)
    L.new(geo.outputs["Object"], vcol.inputs["Vector"])
    r2 = node(nt, "ShaderNodeValToRGB", (-1000, 950))
    r2.color_ramp.elements[0].color = lin("#3c3a37")
    r2.color_ramp.elements[1].color = lin("#5e5850")
    L.new(vcol.outputs["Color"], r2.inputs["Fac"])
    jmix = node(nt, "ShaderNodeMix", (-750, 800), data_type="RGBA")
    L.new(joint.outputs["Result"], jmix.inputs["Factor"])
    sock(jmix, "A").default_value = lin("#17171a")
    L.new(r2.outputs["Color"], sock(jmix, "B"))
    m_road = node(nt, "ShaderNodeMix", (-450, 300), data_type="RGBA")
    L.new(sep.outputs["Red"], m_road.inputs["Factor"])
    L.new(sock(g_col, "Result", out=True), sock(m_road, "A"))
    L.new(sock(jmix, "Result", out=True), sock(m_road, "B"))
    # moss
    mz = node(nt, "ShaderNodeTexNoise", (-750, 500), Scale=9.0, Detail=6.0)
    L.new(geo.outputs["Object"], mz.inputs["Vector"])
    r3 = node(nt, "ShaderNodeValToRGB", (-500, 550))
    r3.color_ramp.elements[0].color = lin("#1f2a27")
    r3.color_ramp.elements[1].color = lin("#3a4a43")
    L.new(mz.outputs["Fac"], r3.inputs["Fac"])
    m_moss = node(nt, "ShaderNodeMix", (-200, 300), data_type="RGBA")
    L.new(sep.outputs["Green"], m_moss.inputs["Factor"])
    L.new(sock(m_road, "Result", out=True), sock(m_moss, "A"))
    L.new(r3.outputs["Color"], sock(m_moss, "B"))
    L.new(sock(m_moss, "Result", out=True), bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.9
    # rift cracks: faint wine emission near the lane entrances
    rv = node(nt, "ShaderNodeTexVoronoi", (-750, -700), Scale=5.0, feature="DISTANCE_TO_EDGE")
    L.new(geo.outputs["Object"], rv.inputs["Vector"])
    rl = node(nt, "ShaderNodeMapRange", (-500, -700), **{"From Min": 0.0, "From Max": 0.012, "To Min": 1.0, "To Max": 0.0})
    L.new(rv.outputs["Distance"], rl.inputs["Value"])
    rm = node(nt, "ShaderNodeMath", (-250, -700), operation="MULTIPLY")
    L.new(rl.outputs["Result"], rm.inputs[0])
    L.new(sep.outputs["Blue"], rm.inputs[1])
    bsdf.inputs["Emission Color"].default_value = lin("#c0304a")
    L.new(rm.outputs["Value"], bsdf.inputs["Emission Strength"])
    # bump: cracks + slab joints + fine grit
    grit = node(nt, "ShaderNodeTexNoise", (-750, -950), Scale=60.0, Detail=4.0)
    L.new(geo.outputs["Object"], grit.inputs["Vector"])
    hsum = node(nt, "ShaderNodeMath", (-450, -900), operation="ADD")
    jb = node(nt, "ShaderNodeMath", (-600, -1100), operation="MULTIPLY")
    L.new(joint.outputs["Result"], jb.inputs[0])
    L.new(sep.outputs["Red"], jb.inputs[1])
    L.new(grit.outputs["Fac"], hsum.inputs[0])
    L.new(jb.outputs["Value"], hsum.inputs[1])
    hsum2 = node(nt, "ShaderNodeMath", (-300, -1000), operation="MULTIPLY")
    L.new(hsum.outputs["Value"], hsum2.inputs[0])
    L.new(crk.outputs["Result"], hsum2.inputs[1])
    bp = node(nt, "ShaderNodeBump", (-100, -600), Strength=0.55, Distance=0.04)
    L.new(hsum2.outputs["Value"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    del out
    return m


def terrain_pbr():
    m = bpy.data.materials.new("GroundPBR")
    m.use_nodes = True
    # bump only: the scans' height maps have different mid-levels, and true displacement sank the ground below the
    # roads (soft shadow bands along every lane). Large relief (ridges, drops) is real mesh geometry.
    m.cycles.displacement_method = "BUMP"
    nt = m.node_tree
    L = nt.links
    bsdf = nt.nodes["Principled BSDF"]
    out = nt.nodes["Material Output"]
    uvn = node(nt, "ShaderNodeUVMap", (-2200, 400))
    mask = node(nt, "ShaderNodeTexImage", (-1950, 600), image=IMG_MASK, interpolation="Cubic")
    L.new(uvn.outputs["UV"], mask.inputs["Vector"])
    sep = node(nt, "ShaderNodeSeparateColor", (-1650, 600))
    L.new(mask.outputs["Color"], sep.inputs["Color"])
    tc = node(nt, "ShaderNodeTexCoord", (-2200, 0))

    def mapped(scale, rot=0.0):
        mp = node(nt, "ShaderNodeMapping", (-1950, 0))
        mp.inputs["Scale"].default_value = (scale, scale, scale)
        mp.inputs["Rotation"].default_value = (0, 0, rot)
        L.new(tc.outputs["Object"], mp.inputs["Vector"])
        return mp.outputs["Vector"]
    g_col, g_r, g_n, g_h = pbr_nodes(nt, THEME["ground"], mapped(0.22), (-1600, 200))
    road_lift = node(nt, "ShaderNodeHueSaturation", (-1300, -2200))
    road_lift.inputs["Value"].default_value = 1.45
    # tiled densely: at large scale the aerial scan has dark linear features that read as stripes
    a_col, a_r, a_n, a_h = pbr_nodes(nt, THEME["rock"], mapped(0.42, 0.7), (-1600, -1000))
    r_col0, r_r, r_n, r_h = pbr_nodes(nt, THEME["road"], mapped(0.34, 0.3), (-1600, -2200))
    L.new(r_col0, road_lift.inputs["Color"])
    r_col = road_lift.outputs["Color"]
    c_col, c_r, c_n, c_h = pbr_nodes(nt, THEME["cliff"], mapped(0.16), (-1600, -3400))
    # ground = ash/burned soil broken up by rocky patches (macro noise)
    mac = node(nt, "ShaderNodeTexNoise", (-1250, 900), Scale=0.12, Detail=4.0)
    L.new(tc.outputs["Object"], mac.inputs["Vector"])
    macr = node(nt, "ShaderNodeMapRange", (-1050, 900), **{"From Min": 0.52, "From Max": 0.64, "To Max": 0.7})
    L.new(mac.outputs["Fac"], macr.inputs["Value"])
    # cliffs where the terrain is steep (ridges at the image border)
    geo = node(nt, "ShaderNodeNewGeometry", (-1250, 1150))
    sepn = node(nt, "ShaderNodeSeparateXYZ", (-1050, 1150))
    L.new(geo.outputs["Normal"], sepn.inputs["Vector"])
    steep = node(nt, "ShaderNodeMapRange", (-850, 1150), **{"From Min": 0.93, "From Max": 0.8})
    L.new(sepn.outputs["Z"], steep.inputs["Value"])

    def mixc(fac, a, b, loc):
        mx = node(nt, "ShaderNodeMix", loc, data_type="RGBA")
        L.new(fac, mx.inputs["Factor"])
        L.new(a, sock(mx, "A"))
        L.new(b, sock(mx, "B"))
        return sock(mx, "Result", out=True)

    def mixf(fac, a, b, loc):
        mx = node(nt, "ShaderNodeMix", loc, data_type="FLOAT")
        L.new(fac, mx.inputs["Factor"])
        L.new(a, sock(mx, "A", "VALUE"))
        L.new(b, sock(mx, "B", "VALUE"))
        return sock(mx, "Result", "VALUE", out=True)

    def mixv(fac, a, b, loc):
        mx = node(nt, "ShaderNodeMix", loc, data_type="VECTOR")
        L.new(fac, mx.inputs["Factor"])
        L.new(a, sock(mx, "A", "VECTOR"))
        L.new(b, sock(mx, "B", "VECTOR"))
        return sock(mx, "Result", "VECTOR", out=True)
    col = mixc(macr.outputs["Result"], g_col, a_col, (-600, 600))
    col = mixc(sep.outputs["Red"], col, r_col, (-400, 600))
    col = mixc(steep.outputs["Result"], col, c_col, (-200, 600))
    rough = mixf(sep.outputs["Red"], mixf(macr.outputs["Result"], g_r, a_r, (-600, 300)), r_r, (-400, 300))
    nrm = mixv(sep.outputs["Red"], mixv(macr.outputs["Result"], g_n.outputs["Normal"], a_n.outputs["Normal"], (-600, 0)), r_n.outputs["Normal"], (-400, 0))
    nrm = mixv(steep.outputs["Result"], nrm, c_n.outputs["Normal"], (-200, 0))
    # roads stay level with the ground (their scan's height map sits lower and made a shadowed trench): normals only
    flat = node(nt, "ShaderNodeValue", (-700, -450))
    flat.outputs[0].default_value = 0.5
    hgt = mixf(sep.outputs["Red"], mixf(macr.outputs["Result"], g_h, a_h, (-600, -300)), flat.outputs[0], (-400, -300))
    # the special layer (green channel): moss / snow / lava crust / void / puddles / flood water
    kind = THEME["special"]
    blend = {"moss": "MULTIPLY", "snow": "MIX", "lava": "MIX", "void": "MIX", "puddle": "MULTIPLY", "water": "MIX"}[kind]
    paint = {"moss": "#6f8a7c", "snow": "#dfe6ef", "lava": "#1c0f0b", "void": "#07040f", "puddle": "#5a6470", "water": "#0d2a33"}[kind]
    moss_c = node(nt, "ShaderNodeMix", (0, 750), data_type="RGBA", blend_type=blend)
    L.new(sep.outputs["Green"], moss_c.inputs["Factor"])
    L.new(col, sock(moss_c, "A"))
    sock(moss_c, "B").default_value = lin(paint)
    scan = THEME.get("special_scan")
    scan_emit = None
    if scan:
        sv = mapped(0.28 if kind == "lava" else 0.35, 0.4)
        sc_col = acg_image(nt, scan, "Color", sv, (-300, 1000))
        dark = node(nt, "ShaderNodeMix", (-100, 1000), data_type="RGBA", blend_type="MULTIPLY")
        dark.inputs["Factor"].default_value = 1.0
        L.new(sc_col.outputs["Color"], sock(dark, "A"))
        sock(dark, "B").default_value = lin("#4a2a20") if kind == "lava" else (1, 1, 1, 1)   # lava crust is dark rock
        L.new(sock(dark, "Result", out=True), sock(moss_c, "B"))
        if kind == "lava":
            scan_emit = acg_image(nt, scan, "Emission", sv, (-300, 1300))
    if kind in ("puddle", "water", "snow"):           # wet surfaces are glossy, snow is soft
        gloss = node(nt, "ShaderNodeMix", (0, 300), data_type="FLOAT")
        L.new(sep.outputs["Green"], gloss.inputs["Factor"])
        L.new(rough, sock(gloss, "A", "VALUE"))
        sock(gloss, "B", "VALUE").default_value = 0.6 if kind == "snow" else 0.04
        rough = sock(gloss, "Result", "VALUE", out=True)
    # palette pull toward cold basalt + a darker value (art bible: ground value 15-45 %)
    hsv = node(nt, "ShaderNodeHueSaturation", (200, 750))
    hsv.inputs["Saturation"].default_value = 0.5
    hsv.inputs["Value"].default_value = THEME.get("value", 0.72)
    L.new(sock(moss_c, "Result", out=True), hsv.inputs["Color"])
    tint = node(nt, "ShaderNodeMix", (400, 750), data_type="RGBA", blend_type="MULTIPLY")
    tint.inputs["Factor"].default_value = 1.0
    L.new(hsv.outputs["Color"], sock(tint, "A"))
    sock(tint, "B").default_value = lin(THEME["tint"])
    L.new(sock(tint, "Result", out=True), bsdf.inputs["Base Color"])
    L.new(rough, bsdf.inputs["Roughness"])
    L.new(nrm, bsdf.inputs["Normal"])
    # rift cracks (emission) near the lane entrances, as before
    rv = node(nt, "ShaderNodeTexVoronoi", (0, -700), Scale=5.0, feature="DISTANCE_TO_EDGE")
    L.new(tc.outputs["Object"], rv.inputs["Vector"])
    rl = node(nt, "ShaderNodeMapRange", (200, -700), **{"From Min": 0.0, "From Max": 0.012, "To Min": 1.0, "To Max": 0.0})
    L.new(rv.outputs["Distance"], rl.inputs["Value"])
    rm = node(nt, "ShaderNodeMath", (400, -700), operation="MULTIPLY")
    L.new(rl.outputs["Result"], rm.inputs[0])
    L.new(sep.outputs["Blue"], rm.inputs[1])
    rm2 = node(nt, "ShaderNodeMath", (550, -700), operation="MULTIPLY")
    L.new(rm.outputs["Value"], rm2.inputs[0])
    rm2.inputs[1].default_value = 2.5
    bsdf.inputs["Emission Color"].default_value = lin(THEME["rift"])
    if kind in ("lava", "void"):
        # lava glows through an irregular crust (voronoi warped by noise); the void is dark with sparse star specks
        warp = node(nt, "ShaderNodeTexNoise", (-300, -1200), Scale=0.6, Detail=6.0)
        L.new(tc.outputs["Object"], warp.inputs["Vector"])
        wv = node(nt, "ShaderNodeVectorMath", (-100, -1200), operation="MULTIPLY_ADD")
        L.new(warp.outputs["Color"], wv.inputs[0])
        wv.inputs[1].default_value = (1.6, 1.6, 1.6)
        L.new(tc.outputs["Object"], wv.inputs[2])
        if kind == "lava":
            pv = node(nt, "ShaderNodeTexVoronoi", (0, -1000), Scale=1.1, feature="DISTANCE_TO_EDGE", Randomness=1.0)
            L.new(wv.outputs["Vector"], pv.inputs["Vector"])
            pr = node(nt, "ShaderNodeMapRange", (200, -1000), **{"From Min": 0.0, "From Max": 0.07, "To Min": 1.0, "To Max": 0.03})
            L.new(pv.outputs["Distance"], pr.inputs["Value"])
        else:
            pv = node(nt, "ShaderNodeTexNoise", (0, -1000), Scale=60.0, Detail=1.0)
            L.new(tc.outputs["Object"], pv.inputs["Vector"])
            pr = node(nt, "ShaderNodeMapRange", (200, -1000), **{"From Min": 0.68, "From Max": 0.74, "To Min": 0.02, "To Max": 1.0})
            L.new(pv.outputs["Fac"], pr.inputs["Value"])
        pm = node(nt, "ShaderNodeMath", (400, -1000), operation="MULTIPLY")
        L.new(pr.outputs["Result"], pm.inputs[0])
        L.new(sep.outputs["Green"], pm.inputs[1])
        pm2 = node(nt, "ShaderNodeMath", (550, -1000), operation="MULTIPLY")
        L.new(pm.outputs["Value"], pm2.inputs[0])
        pm2.inputs[1].default_value = 3.5 if kind == "lava" else 0.9
        tot = node(nt, "ShaderNodeMath", (700, -850), operation="ADD")
        L.new(rm2.outputs["Value"], tot.inputs[0])
        L.new(pm2.outputs["Value"], tot.inputs[1])
        bsdf.inputs["Emission Color"].default_value = lin("#ff5a1f" if kind == "lava" else "#9f8cff")
        if scan_emit is not None:
            # emission colour: rift red on the cracks, the lava scan's own emission inside the lava mask
            ec = node(nt, "ShaderNodeMix", (900, -700), data_type="RGBA")
            L.new(sep.outputs["Green"], ec.inputs["Factor"])
            sock(ec, "A").default_value = lin(THEME["rift"])
            hot = node(nt, "ShaderNodeMix", (750, -1300), data_type="RGBA", blend_type="MULTIPLY")
            hot.inputs["Factor"].default_value = 1.0
            L.new(scan_emit.outputs["Color"], sock(hot, "A"))
            sock(hot, "B").default_value = lin("#ff6a1f")         # the scan's emission is pale: push it to molten orange
            L.new(sock(hot, "Result", out=True), sock(ec, "B"))
            L.new(sock(ec, "Result", out=True), bsdf.inputs["Emission Color"])
            lv = node(nt, "ShaderNodeMath", (700, -1100), operation="MULTIPLY")
            L.new(sep.outputs["Green"], lv.inputs[0])
            lv.inputs[1].default_value = 2.4
            tot2 = node(nt, "ShaderNodeMath", (850, -1000), operation="ADD")
            L.new(rm2.outputs["Value"], tot2.inputs[0])
            L.new(lv.outputs["Value"], tot2.inputs[1])
            tot = tot2
        L.new(tot.outputs["Value"], bsdf.inputs["Emission Strength"])
    else:
        L.new(rm2.outputs["Value"], bsdf.inputs["Emission Strength"])
    disp = node(nt, "ShaderNodeDisplacement", (600, -300), Midlevel=0.5, Scale=0.09)
    L.new(hgt, disp.inputs["Height"])
    L.new(disp.outputs["Displacement"], out.inputs["Displacement"])
    return m


ter.data.materials.append(terrain_pbr())

# ----------------------------------------------------------------------------------------------- the sanctum dais
MAT_DAIS = pbr_material("Dais", THEME["dais"], 0.35, tint="#b9b6b0", value=0.9, snow=False)   # the play area stays clear
MAT_STONE = pbr_material("Ruin", THEME["ruin"], 0.45, tint="#c2bcb2", value=0.95)
MAT_DARK = pbr_material("Basalt", THEME["dark"], 0.6, tint="#8a8c95", value=0.7)
MAT_MOSSY = pbr_material("MossyRock", "mossy_rock", 0.5, tint="#a4b0a8", value=0.85)


def add_cyl(name, r, depth, loc, mat, verts=96, bevel=0.03):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc)
    o = bpy.context.object
    o.name = name
    b = o.modifiers.new("bevel", "BEVEL")
    b.width = bevel
    b.segments = 3
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return o


dais_c = G(0, -0.55)
z0 = float(height[np.abs(np.linspace(GY0, GY1, MH) - dais_c.y).argmin(), MW // 2])
add_cyl("Dais", DAIS_R, 0.22, (dais_c.x, dais_c.y, z0 + 0.06), MAT_DAIS)
add_cyl("DaisInner", 3.0, 0.1, (dais_c.x, dais_c.y, z0 + 0.2), MAT_DAIS)
add_cyl("CrystalPlinth", 1.15, 0.18, (dais_c.x, dais_c.y, z0 + 0.3), MAT_DARK, verts=12, bevel=0.05)
for r_ in (DAIS_R - 0.8, DAIS_R + 0.3, DAIS_R - 0.3, 2.2 * DAIS_R / 3.9):
    bpy.ops.mesh.primitive_torus_add(major_radius=r_, minor_radius=0.035, major_segments=160, minor_segments=6,
                                     location=(dais_c.x, dais_c.y, z0 + (0.17 if r_ > 3.1 else 0.25)))
    bpy.context.object.data.materials.append(MAT_DARK)
for lane in arena["lanes"]:
    px_, py_ = lane["points"][-2]
    a = math.atan2(py_ / SIN - dais_c.y, px_ - dais_c.x)
    for k, (rr, hh) in enumerate(((DAIS_R + 0.35, 0.1), (DAIS_R + 0.7, 0.05))):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(dais_c.x + math.cos(a) * rr, dais_c.y + math.sin(a) * rr, z0 + hh / 2))
        o = bpy.context.object
        o.scale = (0.45, 1.9, hh)
        o.rotation_euler = (0, 0, a)
        b_ = o.modifiers.new("bevel", "BEVEL")
        b_.width = 0.03
        o.data.materials.append(MAT_DAIS)
# carved glyph ring: small blocks around the dais rim
for i in range(72):
    a = i / 72 * math.tau
    bpy.ops.mesh.primitive_cube_add(size=1, location=(dais_c.x + math.cos(a) * (DAIS_R - 0.35), dais_c.y + math.sin(a) * (DAIS_R - 0.35), z0 + 0.18))
    o = bpy.context.object
    o.scale = (0.1, 0.32, 0.03)
    o.rotation_euler = (0, 0, a)
    o.data.materials.append(MAT_DARK)


# ----------------------------------------------------------------------------------------------- props (off the lanes and the dais)
def ground_z(x, y):
    gy_ = y / SIN
    vi = int((gy_ - GY0) / (GY1 - GY0) * (MH - 1))
    ui = int((x - GX0) / (GX1 - GX0) * (MW - 1))
    return float(height[min(max(vi, 0), MH - 1), min(max(ui, 0), MW - 1)])


def lane_clear(x, y, need):
    gy_ = y / SIN
    vi = int((gy_ - GY0) / (GY1 - GY0) * (MH - 1))
    ui = int((x - GX0) / (GX1 - GX0) * (MW - 1))
    return lane_d[min(max(vi, 0), MH - 1), min(max(ui, 0), MW - 1)] > need and math.hypot(x, (y + 0.55) / SIN) > DAIS_R + 0.9


def rock(loc, size, mat):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=size, location=loc)
    o = bpy.context.object
    o.scale = (1.0, 0.8 + random.random() * 0.5, 0.55 + random.random() * 0.4)
    o.rotation_euler = (random.random(), random.random(), random.random() * 6)
    tex = bpy.data.textures.new("rk", "VORONOI")
    tex.noise_scale = 0.4 + random.random() * 0.3
    d = o.modifiers.new("disp", "DISPLACE")
    d.texture = tex
    d.strength = size * 0.45
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return o


def pillar(x, y, h, broken=True):
    z = ground_z(x, y)
    base = G(x, y, z)
    add_cyl("PillarBase", 0.55, 0.3, (base.x, base.y, z + 0.15), MAT_STONE, verts=8, bevel=0.05)
    p = add_cyl("Pillar", 0.38, h, (base.x, base.y, z + 0.3 + h / 2), MAT_STONE, verts=20, bevel=0.02)
    sm = p.modifiers.new("flutes", "DISPLACE")
    t = bpy.data.textures.new("fl", "STUCCI")
    t.noise_scale = 0.15
    sm.texture = t
    sm.strength = 0.04
    if broken:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(base.x, base.y, z + 0.3 + h))
        cut = bpy.context.object
        cut.scale = (1.2, 1.2, 0.6)
        cut.rotation_euler = (0.35 * random.random() + 0.2, 0.3 * random.random(), random.random())
        bl = p.modifiers.new("break", "BOOLEAN")
        bl.object = cut
        bl.operation = "DIFFERENCE"
        cut.hide_render = True
        for k in range(3):
            rock(G(x + random.uniform(-0.9, 0.9), y + random.uniform(-0.5, 0.5), z + 0.1), random.uniform(0.12, 0.25), MAT_STONE)
    else:
        add_cyl("Capital", 0.55, 0.25, (base.x, base.y, z + 0.3 + h + 0.12), MAT_STONE, verts=8, bevel=0.05)


BRAZIERS = []


def brazier(x, y):
    z = ground_z(x, y)
    b = G(x, y, z)
    add_cyl("BrazierStand", 0.2, 0.8, (b.x, b.y, z + 0.4), MAT_DARK, verts=8)
    model("stone_fire_pit", x, y + 0.8 * COS * 0 , 0.75, rot=0.0)
    for o in [o for o in sc.collection.objects if o.name.startswith("stone_fire_pit")][-len(MODEL_CACHE["stone_fire_pit"]):]:
        o.location.z += 0.8
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(b.x, b.y, z + 1.12))
    f = bpy.context.object
    f.scale = (1, 1, 1.6)
    fm = bpy.data.materials.new("Fire")
    fm.use_nodes = True
    em = fm.node_tree.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = lin(THEME["brazier"])
    em.inputs["Strength"].default_value = 12.0
    fm.node_tree.links.new(em.outputs[0], fm.node_tree.nodes["Material Output"].inputs["Surface"])
    f.data.materials.append(fm)
    light = bpy.data.lights.new("BrazierLight", "POINT")
    light.energy = 140
    light.color = lin(THEME["brazier"])[:3]
    light.shadow_soft_size = 0.2
    lo = bpy.data.objects.new("BrazierLight", light)
    lo.location = (b.x, b.y, z + 1.5)
    sc.collection.objects.link(lo)
    BRAZIERS.append((x, y + (z + 1.12) * COS))


def sapling_tree(x, y):
    """Dead/corrupted tree from Sapling Tree Gen (falls back to the curve tree)."""
    if not EXT.get("sapling_tree_gen"):
        return dead_tree(x, y)
    z = ground_z(x, y)
    before = set(bpy.data.objects.keys())
    bpy.ops.curve.tree_add(do_update=True, bevel=True, levels=3, length=(1.0, 0.45, 0.55, 0.4), branches=(0, 18, 9, 6),
                           shape="7", baseSize=0.25, ratio=0.03, scale=random.uniform(2.6, 3.4), prune=False, showLeaves=False,
                           seed=random.randint(0, 9999), curve=(0, -20, -10, 0), curveV=(25, 40, 60, 30), downAngle=(90, 60, 45, 45),
                           rotate=(99.5, 137.5, 137.5, 137.5), handleType="0", resU=2)
    for nm in set(bpy.data.objects.keys()) - before:
        o = bpy.data.objects[nm]
        o.location = G(x, y, z)
        if o.type == "CURVE":
            o.data.materials.append(MAT_DARK)


def grow_ivy(target, x, y):
    """IvyGen creepers climbing a placed pillar or statue (verdant and archive)."""
    if not EXT.get("ivygen") or THEME["special"] not in ("moss", "water"):
        return
    props = bpy.context.window_manager.ivy_gen_props
    props.randomSeed = random.randint(0, 999)
    props.maxIvyLength = random.uniform(1.2, 2.4)
    props.ivySize = 0.012
    props.growLeaves = True
    props.ivyLeafSize = 0.03
    bpy.context.scene.cursor.location = G(x + 0.3, y - 0.2, ground_z(x, y) + 0.05)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    before = set(bpy.data.objects.keys())
    try:
        bpy.ops.curve.ivy_gen(updateIvy=True)
    except Exception as e:  # noqa: BLE001
        print("ivy skipped:", e)
        return
    for nm in set(bpy.data.objects.keys()) - before:
        o = bpy.data.objects[nm]
        o.data.materials.clear()
        o.data.materials.append(MAT_IVY)


def fractured_pillar(x, y, h):
    """A column shattered by Cell Fracture: the stump stays, the upper cells lie toppled around it."""
    if not EXT.get("cell_fracture"):
        return pillar(x, y, h, broken=True)
    z = ground_z(x, y)
    b = G(x, y, z)
    add_cyl("PillarBase", 0.55, 0.3, (b.x, b.y, z + 0.15), MAT_STONE, verts=8, bevel=0.05)
    col_ = add_cyl("PillarF", 0.38, h, (b.x, b.y, z + 0.3 + h / 2), MAT_STONE, verts=20, bevel=0.02)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    col_.select_set(True)
    bpy.context.view_layer.objects.active = col_
    before = set(bpy.data.objects.keys())
    bpy.ops.object.add_fracture_cell_objects(source={"VERT_OWN"}, source_limit=14, source_noise=0.8, recursion=0, use_smooth_faces=False,
                                             use_sharp_edges=True, margin=0.002, use_recenter=True, use_remove_original=True, use_island_split=True,
                                             collection_name="")
    cut = z + 0.3 + h * random.uniform(0.35, 0.6)
    for nm in set(bpy.data.objects.keys()) - before:
        o = bpy.data.objects[nm]
        if o.location.z > cut:   # this cell fell: lay it on the ground nearby
            o.location = G(x + random.uniform(-1.3, 1.3), y + random.uniform(-0.7, 0.4), ground_z(x, y) + 0.12)
            o.rotation_euler = (random.uniform(0, 3), random.uniform(0, 3), random.uniform(0, 6))


def archive_shelves(x, y):
    """Archimesh shelving filled with Archimesh books (falls back to boxes)."""
    if not EXT.get("archimesh"):
        return shelves(x, y)
    z = ground_z(x, y)
    a_ = random.choice([0.0, 0.4, -0.4])
    before = set(bpy.data.objects.keys())
    bpy.ops.mesh.archimesh_shelves()
    sh_new = set(bpy.data.objects.keys()) - before
    for nm in sh_new:
        o = bpy.data.objects[nm]
        if o.parent is None:
            o.location = G(x, y, z)
            o.rotation_euler = (random.uniform(-0.12, 0.12), 0, a_)
            o.scale = (1.4, 1.4, 1.4)
        if o.type == "MESH":
            o.data.materials.clear()
            o.data.materials.append(MAT_DARK)
    for row in range(3):
        before = set(bpy.data.objects.keys())
        try:
            bpy.ops.mesh.archimesh_books()
        except Exception:  # noqa: BLE001
            break
        for nm in set(bpy.data.objects.keys()) - before:
            o = bpy.data.objects[nm]
            if o.parent is None:
                o.location = G(x - 0.6, y, z + 0.28 + row * 0.55)
                o.rotation_euler = (0, 0, a_)
                o.scale = (1.3, 1.3, 1.3)


def dead_tree(x, y):
    z = ground_z(x, y)
    b = G(x, y, z)
    cu = bpy.data.curves.new("tree", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.09
    cu.bevel_resolution = 3
    cu.use_fill_caps = True

    def branch(p, d, length, radius, depth):
        sp = cu.splines.new("NURBS")
        n = 5
        sp.points.add(n - 1)
        q = Vector(p)
        for i in range(n):
            sp.points[i].co = (q.x, q.y, q.z, 1)
            sp.points[i].radius = radius * (1 - i / n * 0.8)
            q = q + d * (length / n) + Vector((random.uniform(-.08, .08), random.uniform(-.08, .08), 0))
        sp.use_endpoint_u = True
        if depth > 0:
            for _ in range(2 + (depth > 1)):
                nd = (d + Vector((random.uniform(-.9, .9), random.uniform(-.9, .9), random.uniform(-.1, .5)))).normalized()
                branch(q - d * length * random.uniform(0.1, 0.5), nd, length * 0.62, radius * 0.6, depth - 1)

    branch(b, Vector((0.1, 0.05, 1)).normalized(), 2.4, 1.0, 3)
    o = bpy.data.objects.new("DeadTree", cu)
    sc.collection.objects.link(o)
    o.data.materials.append(MAT_DARK)


MAT_AETHER = bpy.data.materials.new("Aether")
MAT_AETHER.use_nodes = True
_ab = MAT_AETHER.node_tree.nodes["Principled BSDF"]
_ab.inputs["Base Color"].default_value = lin("#4fb7d8")
_ab.inputs["Roughness"].default_value = 0.08
_ab.inputs["Transmission Weight"].default_value = 0.6
_ab.inputs["Emission Color"].default_value = lin("#6fe2ff")
_ab.inputs["Emission Strength"].default_value = 1.6
CRYSTALS = []


def crystal_cluster(x, y):
    z = ground_z(x, y)
    for k in range(random.randint(3, 6)):
        h = random.uniform(0.35, 1.1)
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=h * 0.22, radius2=0.0, depth=h,
                                        location=G(x + random.uniform(-0.35, 0.35), y + random.uniform(-0.2, 0.2), z + h * 0.4))
        o = bpy.context.object
        o.rotation_euler = (random.uniform(-0.45, 0.45), random.uniform(-0.45, 0.45), random.random() * 6)
        o.data.materials.append(MAT_AETHER)
    rock(G(x, y, z), 0.3, MAT_DARK)
    CRYSTALS.append((x, y + (z + 0.5) * COS))


def fallen_pillar(x, y):
    z = ground_z(x, y)
    b = G(x, y, z)
    for k in range(random.randint(2, 3)):
        seg = add_cyl("Drum", 0.36, random.uniform(0.5, 0.9), (b.x + k * 0.85, b.y + random.uniform(-0.2, 0.2), z + 0.33), MAT_STONE, verts=20)
        seg.rotation_euler = (math.pi / 2 + random.uniform(-.1, .1), 0, random.uniform(-0.5, 0.5) + math.pi / 2)


def arch(x, y):
    z = ground_z(x, y)
    b = G(x, y, z)
    span, h = 2.2, 2.4
    for dx in (-span / 2, span / 2):
        add_cyl("ArchLeg", 0.32, h, (b.x + dx, b.y, z + h / 2), MAT_STONE, verts=8, bevel=0.04)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(b.x, b.y, z + h + 0.22))
    t = bpy.context.object
    t.scale = (span + 0.9, 0.55, 0.42)
    t.rotation_euler = (0, math.radians(random.uniform(-4, 4)), 0)
    bv = t.modifiers.new("bevel", "BEVEL")
    bv.width = 0.05
    bv.segments = 2
    bpy.ops.mesh.primitive_cube_add(size=1, location=(b.x + span * 0.55, b.y, z + h + 0.3))
    cut = bpy.context.object
    cut.scale = (0.7, 1.2, 0.9)
    cut.rotation_euler = (0, 0.6, 0.2)
    cut.hide_render = True
    bl = t.modifiers.new("broken", "BOOLEAN")
    bl.object = cut
    bl.operation = "DIFFERENCE"
    t.data.materials.append(MAT_STONE)
    for k in range(4):
        rock(G(x + span * 0.5 + random.uniform(0, 0.8), y + random.uniform(-0.4, 0.2), z), random.uniform(0.12, 0.3), MAT_STONE)


MODEL_CACHE = {}
MODEL_SCALE = 0.72          # Poly Haven is in metres; a hero is ~1.3 units for ~1.8 m


GRADED = set()


def grade_material(m, sat=0.45, value=0.8, tint="#b8bcc8"):
    """Scan models come in warm daylight colours: desaturate, darken and cool them toward the art-bible basalt."""
    if m is None or m.name in GRADED or not m.use_nodes:
        return
    GRADED.add(m.name)
    nt = m.node_tree
    for b in [n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"]:
        inp = b.inputs["Base Color"]
        if not inp.is_linked:
            continue
        src = inp.links[0].from_socket
        nt.links.remove(inp.links[0])
        hsv = nt.nodes.new("ShaderNodeHueSaturation")
        hsv.inputs["Saturation"].default_value = sat
        hsv.inputs["Value"].default_value = value
        nt.links.new(src, hsv.inputs["Color"])
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.blend_type = "MULTIPLY"
        mx.inputs["Factor"].default_value = 1.0
        nt.links.new(hsv.outputs["Color"], sock(mx, "A"))
        sock(mx, "B").default_value = lin(tint)
        nt.links.new(sock(mx, "Result", out=True), inp)


def model(mid, x, y, size=1.0, rot=None, axis="z"):
    """Append (once) and instance a Poly Haven model standing on the terrain at a game position.
    size = target height in world units (axis 'z') or target footprint width (axis 'xy') for rock sets."""
    if mid not in MODEL_CACHE:
        path = os.path.join(PH, mid, "%s_2k.blend" % mid)
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            dst.objects = [n for n in src.objects]
        objs = [o for o in dst.objects if o is not None and o.type == "MESH"]
        for o in objs:
            for slot in o.material_slots:
                grade_material(slot.material)
        bpy.context.view_layer.update()
        pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        MODEL_CACHE[mid] = (objs, lo, hi)
    objs, lo, hi = MODEL_CACHE[mid]
    ext = (hi.z - lo.z) if axis == "z" else max(hi.x - lo.x, hi.y - lo.y)
    k = size / max(ext, 1e-4)
    centre = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    z = ground_z(x, y)
    b = G(x, y, z)
    r = random.random() * math.tau if rot is None else rot
    from mathutils import Matrix
    place = Matrix.Translation((b.x, b.y, z - 0.02)) @ Matrix.Rotation(r, 4, "Z") @ Matrix.Scale(k, 4) @ Matrix.Translation(-centre)
    for o in objs:
        c = o.copy()
        sc.collection.objects.link(c)
        c.matrix_world = place @ o.matrix_world


def glow_material(name, base, emit, strength, transmission=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b_ = m.node_tree.nodes["Principled BSDF"]
    b_.inputs["Base Color"].default_value = lin(base)
    b_.inputs["Roughness"].default_value = 0.1
    b_.inputs["Transmission Weight"].default_value = transmission
    b_.inputs["Emission Color"].default_value = lin(emit)
    b_.inputs["Emission Strength"].default_value = strength
    return m


MAT_ICE = glow_material("Ice", "#cfefff", "#9fe8ff", 0.4, 0.85)


def scan_glow(name, mid, emit_strength=0.0, tint="#ffffff"):
    """Flat scan material for decals: ambientCG colour (+ its emission map when it has one)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt_ = m.node_tree
    tc_ = nt_.nodes.new("ShaderNodeTexCoord")
    col_ = acg_image(nt_, mid, "Color", tc_.outputs["Object"], (-400, 200))
    b_ = nt_.nodes["Principled BSDF"]
    nt_.links.new(col_.outputs["Color"], b_.inputs["Base Color"])
    if emit_strength > 0:
        em_ = acg_image(nt_, mid, "Emission", tc_.outputs["Object"], (-400, -200))
        mx_ = node(nt_, "ShaderNodeMix", (-150, -200), data_type="RGBA", blend_type="MULTIPLY")
        mx_.inputs["Factor"].default_value = 1.0
        nt_.links.new(em_.outputs["Color"], sock(mx_, "A"))
        sock(mx_, "B").default_value = lin(tint)
        nt_.links.new(sock(mx_, "Result", out=True), b_.inputs["Emission Color"])
        b_.inputs["Emission Strength"].default_value = emit_strength
    return m


MAT_FROZEN = scan_glow("Frozen", THEME["frozen_scan"]) if THEME.get("frozen_scan") else MAT_ICE
MAT_VENT = scan_glow("Vent", THEME["vent_scan"], 2.6, "#ff6a1f") if THEME.get("vent_scan") else None
try:
    _nt = MAT_ICE.node_tree
    _tc = _nt.nodes.new("ShaderNodeTexCoord")
    _im = acg_image(_nt, "Ice002", "Color", _tc.outputs["Object"], (-400, 200))
    _im.projection = "BOX"
    _nt.links.new(_im.outputs["Color"], _nt.nodes["Principled BSDF"].inputs["Base Color"])
except FileNotFoundError:
    pass
MAT_OBSIDIAN = glow_material("Obsidian", "#120c10", "#ff5a1f", 0.8, 0.0)
MAT_VIOLET = glow_material("AetherViolet", "#8a6cff", "#b07cff", 2.0, 0.5)
MAT_COPPER = pbr_material("Copper", THEME["dark"], 0.8, tint="#c07a4a", value=1.0)
MAT_BOOKS = glow_material("Books", "#5a2a24", "#000000", 0.0, 0.0)
MAT_IVY = glow_material("Ivy", "#1d3a2c", "#000000", 0.0, 0.0)
MAT_WATER = glow_material("Water", "#0d2a33", "#2aa6a4", 0.05, 0.0)


def shard_cluster(x, y, mat, lo=0.35, hi=1.1, count=(3, 6), lift=0.0):
    z = ground_z(x, y) + lift
    for k in range(random.randint(*count)):
        h = random.uniform(lo, hi)
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=h * 0.22, radius2=0.0, depth=h,
                                        location=G(x + random.uniform(-0.35, 0.35), y + random.uniform(-0.2, 0.2), z + h * 0.4))
        o = bpy.context.object
        o.rotation_euler = (random.uniform(-0.45, 0.45), random.uniform(-0.45, 0.45), random.random() * 6)
        o.data.materials.append(mat)


def float_rock(x, y):
    o = rock(G(x, y, ground_z(x, y) + random.uniform(1.0, 2.2)), random.uniform(0.35, 0.7), MAT_DARK)
    o.scale = (1.2, 1.0, 0.7)
    shard_cluster(x, y, MAT_VIOLET, 0.2, 0.5, (1, 3), lift=0.0)


def battlement(x, y):
    z = ground_z(x, y)
    b_ = G(x, y, z)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(b_.x, b_.y, z + 0.7))
    w = bpy.context.object
    w.scale = (2.4, 0.5, 1.4)
    w.rotation_euler = (0, 0, random.choice([0.0, 0.5, -0.5]))
    w.data.materials.append(MAT_STONE)
    for k in (-0.9, -0.3, 0.3, 0.9):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(b_.x + k * math.cos(w.rotation_euler.z), b_.y + k * math.sin(w.rotation_euler.z), z + 1.6))
        m_ = bpy.context.object
        m_.scale = (0.35, 0.5, 0.4)
        m_.rotation_euler = w.rotation_euler
        m_.data.materials.append(MAT_STONE)


def shelves(x, y):
    z = ground_z(x, y)
    b_ = G(x, y, z)
    a_ = random.choice([0.0, 0.4, -0.4])
    bpy.ops.mesh.primitive_cube_add(size=1, location=(b_.x, b_.y, z + 0.9))
    f = bpy.context.object
    f.scale = (1.8, 0.45, 1.8)
    f.rotation_euler = (random.uniform(-0.15, 0.15), 0, a_)
    f.data.materials.append(MAT_DARK)
    for row in range(3):
        for k in range(9):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(b_.x - 0.75 + k * 0.18, b_.y - 0.25, z + 0.35 + row * 0.55))
            bk = bpy.context.object
            bk.scale = (0.12, 0.3, random.uniform(0.3, 0.45))
            bk.rotation_euler = (0, random.uniform(-0.2, 0.2), a_)
            bk.data.materials.append(MAT_BOOKS)


def disc(x, y, r, mat, dz=0.03):
    z = ground_z(x, y)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=r, depth=0.04, location=(G(x, y).x, G(x, y).y, z + dz))
    bpy.context.object.data.materials.append(mat)
    return bpy.context.object


def biome_features():
    """Things the data says are there: hazard spots, special nodes, covers."""
    traits = {t["node"]: t["trait"] for t in BIOME.get("nodeTraits", [])}
    for i, tr in traits.items():
        nx, ny = arena["nodes"][i]
        bx, by = nx + 0.75, ny + 0.45       # beside the node, never on it (heroes stand on the node)
        if tr == "heated_bridge":
            disc(nx, ny, 0.75, MAT_OBSIDIAN, 0.02)
        elif tr == "frozen_tile":
            disc(nx, ny, 0.8, MAT_FROZEN, 0.02)
        elif tr == "aether_node":
            shard_cluster(bx, by, MAT_VIOLET, 0.3, 0.7, (2, 4))
        elif tr == "lightning_rod":
            z = ground_z(bx, by)
            add_cyl("Rod", 0.05, 2.4, (G(bx, by).x, G(bx, by).y, z + 1.2), MAT_COPPER, verts=8)
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(G(bx, by).x, G(bx, by).y, z + 2.45))
            bpy.context.object.data.materials.append(MAT_VIOLET)
        elif tr == "archive_tome":
            z = ground_z(bx, by)
            add_cyl("Lectern", 0.12, 0.9, (G(bx, by).x, G(bx, by).y, z + 0.45), MAT_DARK, verts=8)
            bpy.ops.mesh.primitive_cube_add(size=1, location=(G(bx, by).x, G(bx, by).y, z + 0.95))
            bk = bpy.context.object
            bk.scale = (0.45, 0.32, 0.08)
            bk.rotation_euler = (0.4, 0, 0)
            bk.data.materials.append(glow_material("Tome", "#3a2a5a", "#ffd27a", 2.5, 0.0))
    for hz in BIOME.get("hazards", []):
        for hx, hy in hz.get("points", []):
            r_ = hz.get("radius", 1.0)
            if hz["kind"] == "lava_vents":
                if THEME.get("vent_scan"):
                    disc(hx, hy, r_ * 0.5, MAT_VENT, 0.02)
                for k in range(10):
                    a_ = k / 10 * math.tau
                    rock(G(hx + math.cos(a_) * r_ * 0.75, hy + math.sin(a_) * r_ * 0.75 * SIN, ground_z(hx, hy)), random.uniform(0.15, 0.3), MAT_OBSIDIAN)
            elif hz["kind"] == "lightning_strikes":
                pass   # the game's telegraph marks strike spots; a painted decal read as a sticker
    for cv in BIOME.get("covers", []):
        shard_cluster(cv["pos"][0], cv["pos"][1], MAT_ICE, 0.6, 1.4, (5, 8))


biome_features()
if THEME.get("kinds"):
    pass


# candidate prop spots in screen space, filtered by lane / dais clearance
# ----------------------------------------------------------------------------------------------- haven keep
def flagstone_material(name, base, dark, grout, cells=1.6):
    """Clean painted flagstones: voronoi slabs with dark grout lines and a little per-slab tone variation."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = node(nt, "ShaderNodeTexCoord", (-1200, 0))
    vo = node(nt, "ShaderNodeTexVoronoi", (-900, 200), Scale=cells)
    vo.feature = "DISTANCE_TO_EDGE"
    nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    vc = node(nt, "ShaderNodeTexVoronoi", (-900, -100), Scale=cells)
    nt.links.new(tc.outputs["Object"], vc.inputs["Vector"])
    tone = node(nt, "ShaderNodeValToRGB", (-650, -100))
    tone.color_ramp.elements[0].color = lin(dark)
    tone.color_ramp.elements[1].color = lin(base)
    nt.links.new(vc.outputs["Distance"], tone.inputs["Fac"])
    edge = node(nt, "ShaderNodeValToRGB", (-650, 200))
    edge.color_ramp.elements[0].position, edge.color_ramp.elements[1].position = 0.02, 0.06
    edge.color_ramp.elements[0].color = lin(grout)
    edge.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(vo.outputs["Distance"], edge.inputs["Fac"])
    mix = node(nt, "ShaderNodeMix", (-350, 0))
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    nt.links.new(tone.outputs["Color"], [x for x in mix.inputs if x.name == "A" and x.type == "RGBA"][0])
    nt.links.new(edge.outputs["Color"], [x for x in mix.inputs if x.name == "B" and x.type == "RGBA"][0])
    nt.links.new([x for x in mix.outputs if x.name == "Result" and x.type == "RGBA"][0], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.9
    return m


def brazier_simple(x, y, h=1.0):
    z = ground_z(x, y)
    b = G(x, y, z)
    add_cyl("BrazierStand", 0.12, h, (b.x, b.y, z + h / 2), MAT_DARK, verts=8, bevel=0.02)
    add_cyl("BrazierBowl", 0.34, 0.16, (b.x, b.y, z + h + 0.05), MAT_DARK, verts=16, bevel=0.03)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(b.x, b.y, z + h + 0.2))
    bpy.context.object.data.materials.append(glow_material("BrazierFire", "#ff8a2a", "#ffb04a", 6.0, 0.0))
    BRAZIERS.append((x, y + (z + h + 0.2) * COS))


KEEP = None
if HAVEN:
    MAT_FLAG = flagstone_material("Flagstone", "#b8ad98", "#8c826f", "#3a3330")
    MAT_WALL = flagstone_material("WallStone", "#8e93a3", "#6a6e7c", "#24222c", cells=2.6)   # cool grey: walls must read apart from the warm courtyard
    sca = arena.get("scale", 1.0)
    walls = [[v * sca for v in r_] for r_ in arena["walls"]]
    KEEP = (min(r_[0] for r_ in walls) - 0.6, min(r_[1] for r_ in walls) - 0.6, max(r_[2] for r_ in walls) + 0.6, max(r_[3] for r_ in walls) + 0.6)
    inner = [r_ for r_ in arena["walk"]][0]
    ix0, iy0, ix1, iy1 = [v * sca for v in inner]
    zs = [ground_z(x, y) for x in np.linspace(KEEP[0], KEEP[2], 12) for y in np.linspace(KEEP[1], KEEP[3], 12)]
    zk = max(zs) + 0.25          # above every ground bump: terrain poking through reads as ink speckles
    # courtyard flagstones (between the walls) and a low step under the gate passages
    c0, c1 = G(KEEP[0] + 0.6, KEEP[1] + 0.6), G(KEEP[2] - 0.6, KEEP[3] - 0.6)
    bpy.ops.mesh.primitive_cube_add(size=1, location=((c0.x + c1.x) / 2, (c0.y + c1.y) / 2, zk - 0.2))
    floor = bpy.context.object
    floor.name = "Courtyard"
    floor.scale = (c1.x - c0.x, c1.y - c0.y, 0.42)
    floor.data.materials.append(MAT_FLAG)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)   # slab size in real units
    # the dais and its rings sit on the courtyard floor now
    for o in list(sc.objects):
        if o.name.startswith(("Dais", "CrystalPlinth", "Torus", "Cube")) and o is not floor and o.location.z < zk + 0.1:
            o.location.z += zk + 0.02 - z0
    WALL_H = 2.0
    for x0, y0, x1, y1 in walls:
        # render the wall thinner than its footprint (the footprint is the gameplay keep-out band)
        if x1 - x0 >= y1 - y0:
            y0, y1 = y0 + 0.3, y1 - 0.3
        else:
            x0, x1 = x0 + 0.3, x1 - 0.3
        a_, b_ = G(x0, y0), G(x1, y1)
        bpy.ops.mesh.primitive_cube_add(size=1, location=((a_.x + b_.x) / 2, (a_.y + b_.y) / 2, zk + WALL_H / 2 - 0.2))
        w_ = bpy.context.object
        w_.name = "Wall"
        w_.scale = (abs(b_.x - a_.x), abs(b_.y - a_.y), WALL_H + 0.4)
        w_.data.materials.append(MAT_WALL)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bv = w_.modifiers.new("bevel", "BEVEL")
        bv.width, bv.segments = 0.06, 2
        # battlements along the long side
        horiz = abs(b_.x - a_.x) >= abs(b_.y - a_.y)
        length = abs(b_.x - a_.x) if horiz else abs(b_.y - a_.y)
        n_ = max(1, int(length / 0.7))
        for k in range(n_):
            t = (k + 0.5) / n_
            cx_ = a_.x + (b_.x - a_.x) * t if horiz else (a_.x + b_.x) / 2
            cy_ = (a_.y + b_.y) / 2 if horiz else a_.y + (b_.y - a_.y) * t
            for side in (-1, 1):
                off = (abs(b_.y - a_.y) / 2 - 0.12) * side if horiz else (abs(b_.x - a_.x) / 2 - 0.12) * side
                bpy.ops.mesh.primitive_cube_add(size=1, location=(cx_ + (0 if horiz else off), cy_ + (off if horiz else 0), zk + WALL_H + 0.18))
                m_ = bpy.context.object
                m_.scale = (0.36 if horiz else 0.24, 0.24 if horiz else 0.36, 0.38)
                m_.data.materials.append(MAT_WALL)
    # gate towers on both sides of every gate
    gates = []
    for lane in arena["lanes"]:
        g_ = lane.get("gate")
        if g_ and all(math.hypot(g_[0] * sca - q[0], g_[1] * sca - q[1]) > 2.5 for q in gates):
            gates.append((g_[0] * sca, g_[1] * sca))
    for gx_, gy_ in gates:
        vertical_wall = abs(gx_) > abs(gy_)
        for side in (-1, 1):
            tx, ty = (gx_, gy_ + 2.05 * side) if vertical_wall else (gx_ + 2.25 * side, gy_)
            tp = G(tx, ty)
            add_cyl("GateTower", 0.85, WALL_H + 1.2, (tp.x, tp.y, zk + (WALL_H + 1.2) / 2 - 0.2), MAT_WALL, verts=16, bevel=0.05)
            add_cyl("GateTowerCap", 1.1, 0.3, (tp.x, tp.y, zk + WALL_H + 1.2), MAT_DARK, verts=16, bevel=0.04)
    # braziers in the courtyard corners
    for bx_, by_ in ((ix0 + 1.2, iy0 + 1.0), (ix1 - 1.2, iy0 + 1.0), (ix0 + 1.2, iy1 - 1.1), (ix1 - 1.2, iy1 - 1.1)):
        brazier_simple(bx_, by_)


def in_keep(x, y):
    return KEEP is not None and KEEP[0] - 0.8 <= x <= KEEP[2] + 0.8 and KEEP[1] - 1.5 <= y <= KEEP[3] + 0.8


spots = [(x, y) for x in np.linspace(-VIEW_W / 2 + 1.5, VIEW_W / 2 - 1.5, 27) for y in np.linspace(-VIEW_H / 2 + 0.9, VIEW_H / 2 - 0.9, 15)]
random.shuffle(spots)
placed = []
kinds = THEME.get("kinds") or (["statue"] * 2 + ["arch"] * 2 + ["brazier"] * 2 + ["crystals"] * 4 + ["pillar"] * 4 + ["broken"] * 6
                               + ["fallen"] * 3 + ["deadtree"] * 2 + ["tree"] * 2 + ["roots"] * 2 + ["mossrocks"] * 6 + ["boulder"] * 4 + ["stump"] * 2)
kinds = list(kinds)
kinds = kinds + random.sample(kinds, int(len(kinds) * 0.35))     # a third more props for the wider field
for x, y in spots:
    if not kinds:
        break
    need = {"arch": 2.8, "deadtree": 2.6, "statue": 2.2, "mossrocks": 2.4, "roots": 2.2, "boulder": 2.0}.get(kinds[0], 1.7)
    if math.hypot(x, y + 0.55) < 5.8 or in_keep(x, y):   # the intercept field / the keep stay open for the party
        continue
    if not lane_clear(x, y, need) or any(math.hypot(x - px, y - py) < 2.4 for px, py in placed):
        continue
    kind = kinds.pop(0)
    placed.append((x, y))
    if kind == "pillar":
        pillar(x, y, random.uniform(1.6, 2.6), broken=False)
        if random.random() < 0.6:
            grow_ivy(bpy.data.objects.get("Pillar") if False else [o for o in sc.objects if o.name.startswith("Pillar")][-1], x, y)
    elif kind == "broken":
        fractured_pillar(x, y, random.uniform(1.4, 2.4))
    elif kind == "brazier":
        brazier(x, y)
    elif kind == "tree":
        sapling_tree(x, y)
    elif kind == "obsidian":
        shard_cluster(x, y, MAT_OBSIDIAN, 0.5, 1.6, (3, 6))
    elif kind == "icecrystals":
        shard_cluster(x, y, MAT_ICE, 0.5, 1.5, (3, 6))
    elif kind == "floatrock":
        float_rock(x, y)
    elif kind == "battlement":
        battlement(x, y)
    elif kind == "shelves":
        archive_shelves(x, y)
    elif kind == "statue":
        add_cyl("StatuePlinth", 0.6, 0.45, (G(x, y).x, G(x, y).y, ground_z(x, y) + 0.22), MAT_STONE, verts=8, bevel=0.05)
        model("gothic_statue", x, y, 2.3, rot=math.radians(180 + random.uniform(-30, 30)))
    elif kind == "deadtree":
        if random.random() < 0.5:
            model("dead_quiver_trunk", x, y, random.uniform(2.6, 3.2))                  # standing
        else:
            model("dead_tree_trunk_02", x, y, random.uniform(1.8, 2.3), axis="xy")     # fallen log
    elif kind == "roots":
        model("root_cluster_01", x, y, 1.6, axis="xy")
    elif kind == "mossrocks":
        model(random.choice(["rock_moss_set_01", "rock_moss_set_02"]), x, y, random.uniform(1.6, 2.4), axis="xy")
    elif kind == "boulder":
        model(random.choice(["namaqualand_boulder_02", "namaqualand_boulder_05"]), x, y, random.uniform(0.9, 1.4))
    elif kind == "stump":
        model("tree_stump_01", x, y, 0.7)
    elif kind == "arch":
        arch(x, y)
    elif kind == "crystals":
        crystal_cluster(x, y)
    elif kind == "fallen":
        fallen_pillar(x, y)
    else:
        for k in range(random.randint(2, 5)):
            rock(G(x + random.uniform(-0.7, 0.7), y + random.uniform(-0.4, 0.4), ground_z(x, y)), random.uniform(0.15, 0.5), MAT_MOSSY)
# rubble along the road edges
for _ in range(420):
    x, y = random.uniform(-16.5, 16.5), random.uniform(-9.2, 9.2)
    gy_ = y / SIN
    vi = int((gy_ - GY0) / (GY1 - GY0) * (MH - 1))
    ui = int((x - GX0) / (GX1 - GX0) * (MW - 1))
    d = lane_d[min(max(vi, 0), MH - 1), min(max(ui, 0), MW - 1)]
    if 0.85 < d < 1.25 and math.hypot(x, (y + 0.55) / SIN) > DAIS_R:
        rock(G(x, y, ground_z(x, y)), random.uniform(0.05, 0.16), random.choice([MAT_STONE, MAT_MOSSY, MAT_DARK]))

grass_tex = bpy.data.textures.new("mossden", "IMAGE")
grass_tex.image = to_image("mossden", np.stack([moss * (1 - road_edge)] * 3, -1))
ps_mod = ter.modifiers.new("grass", "PARTICLE_SYSTEM")
pset = ps_mod.particle_system.settings
pset.type = "HAIR"
pset.count = 90000
pset.hair_length = 0.22
pset.use_advanced_hair = True
pset.brownian_factor = 0.05
pset.child_type = "INTERPOLATED"
pset.rendered_child_count = 6
pset.root_radius = 0.02
pset.tip_radius = 0.0
slot = pset.texture_slots.add()
slot.texture = grass_tex
slot.texture_coords = "UV"
slot.use_map_time = False
slot.use_map_density = True
slot.density_factor = 1.0
gm = bpy.data.materials.new("Grass")
gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = lin("#4a5a48")
gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
ter.data.materials.append(gm)
pset.material = len(ter.data.materials)

# ----------------------------------------------------------------------------------------------- lights
sun = bpy.data.lights.new("Moon", "SUN")
sun.energy = THEME["sun"][1]
sun.color = lin(THEME["sun"][0])[:3]
sun.angle = math.radians(4)
so = bpy.data.objects.new("Moon", sun)
sc.collection.objects.link(so)
# from the upper-left FRONT: the light travels toward +x (right) and +y (away from the camera), downward
light_dir = Vector((0.55, 0.62, -0.75)).normalized()
so.rotation_euler = light_dir.to_track_quat("-Z", "Y").to_euler()
crys = bpy.data.lights.new("CrystalLight", "POINT")
crys.energy = 2200 if "--painterly" in ARGS else 750   # toon bands blow a strong point light out to white
crys.color = lin("#8fe3ff")[:3]
crys.shadow_soft_size = 0.25
crys.use_shadow = False          # its shadows from the lane-mouth steps would darken the roads radially
co_ = bpy.data.objects.new("CrystalLight", crys)
co_.location = (dais_c.x, dais_c.y, z0 + 1.6)
sc.collection.objects.link(co_)
fill = bpy.data.lights.new("Fill", "AREA")
fill.energy = 900
fill.size = 30
fill.color = lin("#3c5c9a")[:3]
fill.use_shadow = not HAVEN     # its huge soft shadows cross the courtyard in an X
fo = bpy.data.objects.new("Fill", fill)
fo.location = (6, 26, 14)
fo.rotation_euler = (-(fo.location - Vector((0, 0, 0)))).to_track_quat("-Z", "Y").to_euler()
sc.collection.objects.link(fo)


# ----------------------------------------------------------------------------------------------- render
sc.use_nodes = True
ct = sc.node_tree
for n_ in list(ct.nodes):
    ct.nodes.remove(n_)
rl = ct.nodes.new("CompositorNodeRLayers")
kw = ct.nodes.new("CompositorNodeKuwahara")
try:
    kw.variation = "ANISOTROPIC"
except Exception:
    pass
if "Size" in kw.inputs:
    kw.inputs["Size"].default_value = max(2, int(5 * SCALE))
elif hasattr(kw, "size"):
    kw.size = max(2, int(5 * SCALE))
mixk = ct.nodes.new("CompositorNodeMixRGB")
mixk.inputs[0].default_value = 0.55          # keep some of the crisp render under the brush pass
comp = ct.nodes.new("CompositorNodeComposite")
ct.links.new(rl.outputs["Image"], kw.inputs["Image"])
ct.links.new(rl.outputs["Image"], mixk.inputs[1])
ct.links.new(kw.outputs["Image"], mixk.inputs[2])
ct.links.new(mixk.outputs["Image"], comp.inputs["Image"])
if "--nodisp" in ARGS:
    for m in bpy.data.materials:
        m.cycles.displacement_method = "BUMP"
if "--nofill" in ARGS:
    fill.energy = 0.0
if "--clay" in ARGS:     # diagnostics: one grey material everywhere, to tell geometry/light problems from texture ones
    clay = bpy.data.materials.new("Clay")
    clay.use_nodes = True
    clay.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.35, 0.35, 0.35, 1)
    bpy.context.view_layer.material_override = clay
TOON = "--painterly" not in ARGS and "--clay" not in ARGS
if TOON:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import toon_pass  # noqa: E402
    toon_pass.configure(scene=sc, out=OUT, scale=SCALE, theme=THEME, biome=BIOME_ID, alpha=False)
    toon_pass.toon_setup()
    bpy.ops.render.render(write_still=False)
    toon_pass.toon_compose(os.path.join(OUT, "flat_raw.png"))
else:
    sc.render.filepath = os.path.join(OUT, "flat_raw.png")
    bpy.ops.render.render(write_still=True)

# shadow direction on screen for unit shadows in Unity: project the light travel direction onto the ground
gdir = Vector((light_dir.x, light_dir.y))
scr = Vector((gdir.x, gdir.y * SIN)).normalized()
shadow_len = 1.0 / math.tan(math.asin(-light_dir.z))          # ground length per unit of height
meta = {
    "camera": {"elevationDeg": math.degrees(ELEV), "viewUnits": [VIEW_W, VIEW_H], "resolution": [sc.render.resolution_x, sc.render.resolution_y], "ppu": sc.render.resolution_x / VIEW_W},
    "shadowDirScreen": [round(scr.x, 4), round(scr.y, 4)],
    "shadowLengthPerHeight": round(shadow_len * math.hypot(gdir.normalized().x, gdir.normalized().y * SIN), 4),
    "crystalScreen": [0.0, -0.55],
    "braziersScreen": [[round(a, 3), round(b, 3)] for a, b in BRAZIERS],
    "braziersFlat": [round(v, 3) for p_ in BRAZIERS for v in p_],
    "aetherCrystalsFlat": [round(v, 3) for p_ in CRYSTALS for v in p_],
    "aetherCrystalsScreen": [[round(a, 3), round(b, 3)] for a, b in CRYSTALS],
    "biome": BIOME_ID,
    "samples": SAMPLES,
}
json.dump(meta, open(os.path.join(OUT, "env_meta.json"), "w"), indent=1)
print("ENV DONE", OUT)
