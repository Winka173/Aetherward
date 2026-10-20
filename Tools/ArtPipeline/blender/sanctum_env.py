"""Aetherward battlefield environment — Blender 4.5 headless, Cycles (OPTIX), real geometry, lights and shadows.

  blender -b --factory-startup --python Tools/ArtPipeline/blender/sanctum_env.py -- \
      --arena Assets/_Aetherward/Resources/Content/arena.json --out Temp/Env/verdant [--samples 256] [--scale 1.0]

Camera contract (matches the game, see ArtProduction/ART_BIBLE.md §3):
  orthographic, elevation 38.3 deg (sin = 0.62), 34 x 19.2 world units on screen, output 4080 x 2304 (PPU 120).
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
OUT = os.path.abspath(arg("--out", "Temp/Env/verdant"))
SAMPLES = int(arg("--samples", "256"))
SCALE = float(arg("--scale", "1.0"))          # render-size multiplier for quick previews (0.25 = draft)
SEED = int(arg("--seed", "7"))
SIN = 0.62
ELEV = math.asin(SIN)
COS = math.cos(ELEV)
VIEW_W, VIEW_H = 34.0, 19.2
RES_X, RES_Y = 4080, 2304
random.seed(SEED)
np.random.seed(SEED)
os.makedirs(os.path.join(OUT, "layers"), exist_ok=True)


def jsonc(path):
    t = open(path, encoding="utf-8").read()
    return json.loads(re.sub(r"^\s*//.*$", "", t, flags=re.M))


arena = jsonc(ARENA)
if "--biome" in ARGS:    # biome arenas are inline in biomes.json
    biomes = jsonc(os.path.join(os.path.dirname(ARENA), "biomes.json"))["biomes"]
    b = next(b for b in biomes if b["id"] == arg("--biome"))
    if isinstance(b.get("arena"), dict):
        arena = b["arena"]


def G(x, y, z=0.0):
    """Game (screen) position -> Blender ground position."""
    return Vector((x, y / SIN, z))


def lin(hexstr):
    h = hexstr.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c) + (1.0,)


# ----------------------------------------------------------------------------------------------- scene
bpy.ops.wm.read_factory_settings(use_empty=True)
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
bg.inputs[0].default_value = lin("#1a2a44")
bg.inputs[1].default_value = 0.35

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
for lane in arena["lanes"]:
    pts = [(x, y / SIN) for x, y in lane["points"]] + [(0.0, 0.0)]
    # extend the spawn end beyond the screen so roads run off the image
    (x0, y0), (x1, y1) = pts[0], pts[1]
    ext = (x0 + (x0 - x1) * 0.6, y0 + (y0 - y1) * 0.6)
    pts = [ext] + pts
    for a, b in zip(pts, pts[1:]):
        lane_d = np.minimum(lane_d, seg_dist(gx, gy, a, b))
DAIS_R = 5.9
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
moss = smooth(0.52, 0.72, fbm(5, 4, 2)) * (1 - road) * (1 - dais) * 0.85
sx, sy = gx, gy * SIN                                           # screen coords
edge = np.maximum(smooth(VIEW_W / 2 - 3.2, VIEW_W / 2 + 0.5, np.abs(sx)), smooth(VIEW_H / 2 - 2.4, VIEW_H / 2 + 0.5, sy))
ridge = edge * (1 - smooth(0.9, 2.4, lane_d)) * (0.6 + 0.8 * fbm(4, 4, 3))
near_drop = smooth(VIEW_H / 2 - 2.6, VIEW_H / 2 + 0.4, -sy) * (1 - smooth(0.9, 2.2, lane_d))
rift = (1 - smooth(0.0, 0.9, lane_d)) * smooth(VIEW_W / 2 - 7.5, VIEW_W / 2 - 1.0, np.maximum(np.abs(sx), np.abs(sy) * 1.7))
height = ridge * 2.6 - near_drop * 1.2 + (fbm(14, 4, 4) - 0.5) * 0.12 * (1 - road) - road * 0.04
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


def sock(n, name, kind="RGBA", out=False):
    """Mix/MapRange nodes have one socket per data type with the same name; pick the one of `kind`."""
    for x in (n.outputs if out else n.inputs):
        if x.name == name and x.type == kind:
            return x
    raise KeyError(name)


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


ter.data.materials.append(terrain_material())

# ----------------------------------------------------------------------------------------------- the sanctum dais
MAT_DAIS = stone_material("Dais", "#5b5650", "#2a2826", 3.0, bump=0.25)
MAT_STONE = stone_material("Ruin", "#68625a", "#24221f", 2.2, bump=0.5)
MAT_DARK = stone_material("Basalt", "#3a3a3f", "#121215", 3.5, bump=0.6)


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
for r_ in (DAIS_R - 0.8, 4.2, 3.6, 2.2):
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
    add_cyl("BrazierStand", 0.16, 0.9, (b.x, b.y, z + 0.45), MAT_DARK, verts=8)
    bowl = add_cyl("BrazierBowl", 0.42, 0.22, (b.x, b.y, z + 0.95), MAT_DARK, verts=16, bevel=0.06)
    del bowl
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(b.x, b.y, z + 1.12))
    f = bpy.context.object
    f.scale = (1, 1, 1.6)
    fm = bpy.data.materials.new("Fire")
    fm.use_nodes = True
    em = fm.node_tree.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = lin("#5fd7c8")
    em.inputs["Strength"].default_value = 12.0
    fm.node_tree.links.new(em.outputs[0], fm.node_tree.nodes["Material Output"].inputs["Surface"])
    f.data.materials.append(fm)
    light = bpy.data.lights.new("BrazierLight", "POINT")
    light.energy = 260
    light.color = lin("#62e0cf")[:3]
    light.shadow_soft_size = 0.2
    lo = bpy.data.objects.new("BrazierLight", light)
    lo.location = (b.x, b.y, z + 1.5)
    sc.collection.objects.link(lo)
    BRAZIERS.append((x, y + (z + 1.12) * COS))


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
    bpy.ops.mesh.primitive_torus_add(major_radius=span / 2, minor_radius=0.28, major_segments=40, minor_segments=8,
                                     location=(b.x, b.y, z + h), rotation=(math.pi / 2, 0, 0))
    t = bpy.context.object
    bpy.ops.mesh.primitive_cube_add(size=1, location=(b.x + span * 0.35, b.y, z + h + span * 0.45))
    cut = bpy.context.object
    cut.scale = (1.0, 1.5, 1.2)
    cut.rotation_euler = (0, 0.5, 0)
    cut.hide_render = True
    bl = t.modifiers.new("broken", "BOOLEAN")
    bl.object = cut
    bl.operation = "DIFFERENCE"
    t.data.materials.append(MAT_STONE)
    bpy.ops.object.shade_smooth()
    for k in range(4):
        rock(G(x + span * 0.5 + random.uniform(0, 0.8), y + random.uniform(-0.4, 0.2), z), random.uniform(0.12, 0.3), MAT_STONE)


# candidate prop spots in screen space, filtered by lane / dais clearance
spots = [(x, y) for x in np.linspace(-15.5, 15.5, 23) for y in np.linspace(-8.6, 8.6, 13)]
random.shuffle(spots)
placed = []
kinds = ["arch"] * 2 + ["brazier"] * 2 + ["crystals"] * 4 + ["pillar"] * 5 + ["broken"] * 7 + ["fallen"] * 3 + ["tree"] * 3 + ["rocks"] * 10
for x, y in spots:
    if not kinds:
        break
    need = 2.6 if kinds[0] == "arch" else 1.7
    if not lane_clear(x, y, need) or any(math.hypot(x - px, y - py) < 2.4 for px, py in placed):
        continue
    kind = kinds.pop(0)
    placed.append((x, y))
    if kind == "pillar":
        pillar(x, y, random.uniform(1.6, 2.6), broken=False)
    elif kind == "broken":
        pillar(x, y, random.uniform(0.5, 1.4), broken=True)
    elif kind == "brazier":
        brazier(x, y)
    elif kind == "tree":
        dead_tree(x, y)
    elif kind == "arch":
        arch(x, y)
    elif kind == "crystals":
        crystal_cluster(x, y)
    elif kind == "fallen":
        fallen_pillar(x, y)
    else:
        for k in range(random.randint(2, 5)):
            rock(G(x + random.uniform(-0.7, 0.7), y + random.uniform(-0.4, 0.4), ground_z(x, y)), random.uniform(0.15, 0.5), MAT_DARK)
# rubble along the road edges
for _ in range(260):
    x, y = random.uniform(-16.5, 16.5), random.uniform(-9.2, 9.2)
    gy_ = y / SIN
    vi = int((gy_ - GY0) / (GY1 - GY0) * (MH - 1))
    ui = int((x - GX0) / (GX1 - GX0) * (MW - 1))
    d = lane_d[min(max(vi, 0), MH - 1), min(max(ui, 0), MW - 1)]
    if 0.85 < d < 1.25 and math.hypot(x, (y + 0.55) / SIN) > DAIS_R:
        rock(G(x, y, ground_z(x, y)), random.uniform(0.05, 0.14), MAT_STONE)

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
sun.energy = 2.6
sun.color = lin("#dfe6ff")[:3]
sun.angle = math.radians(4)
so = bpy.data.objects.new("Moon", sun)
sc.collection.objects.link(so)
# from the upper-left FRONT: the light travels toward +x (right) and +y (away from the camera), downward
light_dir = Vector((0.55, 0.62, -0.75)).normalized()
so.rotation_euler = light_dir.to_track_quat("-Z", "Y").to_euler()
crys = bpy.data.lights.new("CrystalLight", "POINT")
crys.energy = 2200
crys.color = lin("#8fe3ff")[:3]
crys.shadow_soft_size = 0.25
co_ = bpy.data.objects.new("CrystalLight", crys)
co_.location = (dais_c.x, dais_c.y, z0 + 1.6)
sc.collection.objects.link(co_)
fill = bpy.data.lights.new("Fill", "AREA")
fill.energy = 900
fill.size = 30
fill.color = lin("#3c5c9a")[:3]
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
    "aetherCrystalsScreen": [[round(a, 3), round(b, 3)] for a, b in CRYSTALS],
    "samples": SAMPLES,
}
json.dump(meta, open(os.path.join(OUT, "env_meta.json"), "w"), indent=1)
print("ENV DONE", OUT)
