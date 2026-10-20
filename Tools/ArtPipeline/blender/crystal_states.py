"""The holy Crystal in three registered damage states — Blender 4.5 headless, Cycles, same camera and lights as
sanctum_env.py (orthographic, 38.3 deg elevation, moon from the upper-left front).

  blender -b --factory-startup --python Tools/ArtPipeline/blender/crystal_states.py -- --out ArtCache/Crystal [--samples 192]

Output: <out>/crystal_<state>@2x.png (640x800 RGBA, transparent) for intact / cracked / critical. The game contract is
320x400 at PPU 160 with the feet on row 372 (pivot y 0.07): the camera is framed so the ground point under the Crystal
lands on that row at 2x (744). Downscale with Tools/ArtPipeline/env_finish.py --crystal (Lanczos) or any Lanczos resize.
Design (ArtProduction/ART_BIBLE.md §7): a tall faceted relic with an asymmetric crown of shards in a carved stone collar
with glyphs, three suspended shards; fractures glow when cracked; critical = shards dimmed/fallen, red-violet core.
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(ARGS[ARGS.index("--out") + 1] if "--out" in ARGS else "ArtCache/Crystal")
SAMPLES = int(ARGS[ARGS.index("--samples") + 1]) if "--samples" in ARGS else 192
SIN = 0.62
ELEV = math.asin(SIN)
os.makedirs(OUT, exist_ok=True)


def lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c) + (1.0,)


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
sc.cycles.transmission_bounces = 12
sc.render.film_transparent = True
sc.render.resolution_x, sc.render.resolution_y = 640, 800
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Base Contrast"
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGBA"
world = bpy.data.worlds.new("Night")
sc.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = lin("#1a2a44")
world.node_tree.nodes["Background"].inputs[1].default_value = 0.35

# camera: 2.0 x 2.5 units; the ground origin sits 0.07 * 2.5 above the bottom edge
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = "ORTHO"
cam.data.ortho_scale = 2.5            # the larger side (height 800 px = 2.5 units)
d = Vector((0, math.cos(ELEV), -SIN))
up = Vector((0, SIN, math.cos(ELEV)))
# the front of the 0.62-radius collar projects 0.62 * sin(elev) below the ground origin: that lowest edge is the
# sprite's "feet" (pivot row), so the origin sits that much higher in the frame
COLLAR_R = 0.62
cam.location = Vector((0, 0, 0)) - d * 40 + up * (1.25 - 0.07 * 2.5 - COLLAR_R * SIN)
cam.rotation_euler = (math.pi / 2 - ELEV, 0, 0)


def mat_glass(name, tint, emit, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lin(tint)
    b.inputs["Roughness"].default_value = 0.06
    b.inputs["Transmission Weight"].default_value = 0.85
    b.inputs["IOR"].default_value = 1.55
    b.inputs["Emission Color"].default_value = lin(emit)
    b.inputs["Emission Strength"].default_value = strength
    return m, b


PH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "ArtCache", "polyhaven")


def mat_scan(name, tid, scale, tint="#b8bcc8", value=0.8):
    """Box-projected CC0 scan (Tools/ArtPipeline/fetch_polyhaven.py), cooled toward the basalt palette."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    imgs = {}
    for kind, cs in (("diff", "sRGB"), ("rough", "Non-Color"), ("nor_gl", "Non-Color")):
        f = os.path.join(PH, tid, "%s_%s.jpg" % (tid, kind))
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(f, check_existing=True)
        n.image.colorspace_settings.name = cs
        n.projection = "BOX"
        n.projection_blend = 0.3
        nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
        imgs[kind] = n
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    hsv.inputs["Saturation"].default_value = 0.45
    hsv.inputs["Value"].default_value = value
    nt.links.new(imgs["diff"].outputs["Color"], hsv.inputs["Color"])
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    mx.blend_type = "MULTIPLY"
    mx.inputs["Factor"].default_value = 1.0
    nt.links.new(hsv.outputs["Color"], [x for x in mx.inputs if x.name == "A" and x.type == "RGBA"][0])
    [x for x in mx.inputs if x.name == "B" and x.type == "RGBA"][0].default_value = lin(tint)
    nt.links.new([x for x in mx.outputs if x.name == "Result" and x.type == "RGBA"][0], b.inputs["Base Color"])
    nt.links.new(imgs["rough"].outputs["Color"], b.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(imgs["nor_gl"].outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m, b


def mat_stone(name, base, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 18.0
    nz.inputs["Detail"].default_value = 8.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = lin("#1a1a1e")
    ramp.color_ramp.elements[1].color = lin(base)
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.6
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.85
    if emit:
        b.inputs["Emission Color"].default_value = lin(emit)
        b.inputs["Emission Strength"].default_value = strength
    return m, b


def crystal_mesh(name, radius, height, tip, sides=6, jitter=0.12, seed=0):
    rnd = random.Random(seed)
    bm = bmesh.new()
    ring0, ring1 = [], []
    for i in range(sides):
        a = i / sides * math.tau + rnd.uniform(-0.15, 0.15)
        r = radius * (1 + rnd.uniform(-jitter, jitter))
        ring0.append(bm.verts.new((math.cos(a) * r * 0.82, math.sin(a) * r * 0.82, 0)))
        ring1.append(bm.verts.new((math.cos(a) * r, math.sin(a) * r, height * (1 + rnd.uniform(-0.05, 0.05)))))
    top = bm.verts.new((rnd.uniform(-0.04, 0.04) * radius, rnd.uniform(-0.04, 0.04) * radius, height + tip))
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((ring0[i], ring0[j], ring1[j], ring1[i]))
        bm.faces.new((ring1[i], ring1[j], top))
    bm.faces.new(list(reversed(ring0)))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    return o


M_GLASS, B_GLASS = mat_glass("Crystal", "#a9e6ff", "#6fd2ff", 0.7)
M_CORE, B_CORE = mat_glass("Core", "#ffffff", "#d6f6ff", 3.0)
M_SHARD, B_SHARD = mat_glass("Shard", "#bfefff", "#8fe3ff", 3.0)
M_COLLAR, B_COLLAR = mat_scan("Collar", "castle_wall_slates", 2.2, tint="#c4c2be", value=0.85)
M_TOOTH, B_TOOTH = mat_scan("Tooth", "dark_rock", 3.0, tint="#a6a9b4", value=0.8)
M_GLYPH, B_GLYPH = mat_stone("Glyph", "#2a2a2e", "#8fe3ff", 6.0)
# fracture network (emission) on the crystal surface, faded in for the damaged states
nt = M_GLASS.node_tree
vor = nt.nodes.new("ShaderNodeTexVoronoi")
vor.feature = "DISTANCE_TO_EDGE"
vor.inputs["Scale"].default_value = 3.2
mr = nt.nodes.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = 0.0
mr.inputs["From Max"].default_value = 0.02
mr.inputs["To Min"].default_value = 1.0
mr.inputs["To Max"].default_value = 0.0
nt.links.new(vor.outputs["Distance"], mr.inputs["Value"])
FRACT = nt.nodes.new("ShaderNodeMath")
FRACT.operation = "MULTIPLY"
FRACT.inputs[1].default_value = 0.0
nt.links.new(mr.outputs["Result"], FRACT.inputs[0])
emit_mix = nt.nodes.new("ShaderNodeMath")
emit_mix.operation = "ADD"
emit_mix.inputs[1].default_value = 0.7
nt.links.new(FRACT.outputs["Value"], emit_mix.inputs[0])
nt.links.new(emit_mix.outputs["Value"], B_GLASS.inputs["Emission Strength"])

# collar: carved stone ring with standing teeth and a glowing glyph groove
bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.62, depth=0.26, location=(0, 0, 0.13))
collar = bpy.context.object
bv = collar.modifiers.new("bevel", "BEVEL")
bv.width = 0.04
bv.segments = 3
collar.data.materials.append(M_COLLAR)
bpy.ops.mesh.primitive_torus_add(major_radius=0.6, minor_radius=0.018, major_segments=64, minor_segments=6, location=(0, 0, 0.2))
bpy.context.object.data.materials.append(M_GLYPH)
TEETH = []
for i in range(8):
    a = i / 8 * math.tau + 0.2
    h = 0.24 + 0.12 * ((i * 37) % 5) / 4
    bpy.ops.mesh.primitive_cube_add(size=1, location=(math.cos(a) * 0.52, math.sin(a) * 0.52, 0.26 + h / 2))
    t = bpy.context.object
    t.scale = (0.12, 0.2, h)
    t.rotation_euler = (math.radians(8 + 6 * (i % 3)) * math.sin(a), -math.radians(8 + 6 * (i % 3)) * math.cos(a), a + 0.2 * (i % 2))
    bv_ = t.modifiers.new("bevel", "BEVEL")
    bv_.width = 0.025
    bv_.segments = 2
    sub = t.modifiers.new("sub", "SUBSURF")
    sub.levels = sub.render_levels = 2
    sub.subdivision_type = "SIMPLE"
    dsp = t.modifiers.new("chip", "DISPLACE")
    dsp.texture = bpy.data.textures.new("chip%d" % i, "VORONOI")
    dsp.texture.noise_scale = 0.08
    dsp.strength = 0.03
    t.data.materials.append(M_TOOTH)
    TEETH.append(t)

# the relic: main crystal + asymmetric crown + inner core + suspended shards
main = crystal_mesh("Main", 0.26, 1.05, 0.42, seed=1)
main.location = (0, 0, 0.24)
main.data.materials.append(M_GLASS)
core = crystal_mesh("CoreMesh", 0.1, 0.7, 0.25, seed=2)
core.location = (0, 0, 0.36)
core.data.materials.append(M_CORE)
CROWN = []
for i, (a, tilt, h) in enumerate(((0.4, 22, 0.55), (2.1, 28, 0.42), (3.6, 18, 0.62), (5.0, 30, 0.35))):
    c = crystal_mesh("Crown%d" % i, 0.09, h, 0.18, seed=10 + i)
    c.location = (math.cos(a) * 0.18, math.sin(a) * 0.18, 0.95)
    c.rotation_euler = (math.radians(tilt) * -math.sin(a), math.radians(tilt) * math.cos(a), a)
    c.data.materials.append(M_GLASS)
    CROWN.append(c)
SHARDS = []
for i, (a, z) in enumerate(((0.9, 1.25), (2.9, 0.95), (4.7, 1.55))):
    s_ = crystal_mesh("Shard%d" % i, 0.06, 0.18, 0.1, seed=20 + i)
    s_.location = (math.cos(a) * 0.62, math.sin(a) * 0.62, z)
    s_.rotation_euler = (0.4, 0.2, a)
    s_.data.materials.append(M_SHARD)
    SHARDS.append(s_)

# lights (same rig as the battlefield)
sun = bpy.data.lights.new("Moon", "SUN")
sun.energy = 2.6
sun.color = lin("#dfe6ff")[:3]
so = bpy.data.objects.new("Moon", sun)
sc.collection.objects.link(so)
so.rotation_euler = Vector((0.55, 0.62, -0.75)).normalized().to_track_quat("-Z", "Y").to_euler()
rim = bpy.data.lights.new("Rim", "AREA")
rim.energy = 140
rim.size = 2.0
rim.color = lin("#9fe8ff")[:3]
ro = bpy.data.objects.new("Rim", rim)
ro.location = (2.2, 2.6, 2.4)
ro.rotation_euler = (-ro.location).to_track_quat("-Z", "Y").to_euler()
sc.collection.objects.link(ro)
inner = bpy.data.lights.new("Inner", "POINT")
inner.energy = 25
inner.color = lin("#8fe3ff")[:3]
inner.shadow_soft_size = 0.05
io = bpy.data.objects.new("Inner", inner)
io.location = (0, 0, 0.75)
sc.collection.objects.link(io)

STATES = {
    "intact": dict(fract=0.0, core="#d6f6ff", core_s=3.0, glyph=6.0, shard_s=3.0, fallen=[], drop=[], inner="#8fe3ff"),
    "cracked": dict(fract=10.0, core="#d6f6ff", core_s=2.6, glyph=4.0, shard_s=2.5, fallen=[], drop=[1], inner="#8fe3ff"),
    "critical": dict(fract=16.0, core="#ff4a7a", core_s=2.6, glyph=0.6, shard_s=0.4, fallen=[0], drop=[1, 2], inner="#ff6a90"),
}
base_loc = {s_.name: s_.location.copy() for s_ in SHARDS}
for state, st in STATES.items():
    FRACT.inputs[1].default_value = st["fract"]
    B_CORE.inputs["Emission Color"].default_value = lin(st["core"])
    B_CORE.inputs["Emission Strength"].default_value = st["core_s"]
    B_GLYPH.inputs["Emission Strength"].default_value = st["glyph"]
    B_SHARD.inputs["Emission Strength"].default_value = st["shard_s"]
    inner.color = lin(st["inner"])[:3]
    for i, s_ in enumerate(SHARDS):
        s_.location = base_loc[s_.name].copy()
        if i in st["drop"]:
            s_.location.z -= 0.28
    for i, c in enumerate(CROWN):
        c.hide_render = i in st["fallen"] or (state == "critical" and i == 2)
    sc.render.filepath = os.path.join(OUT, "crystal_%s@2x.png" % state)
    bpy.ops.render.render(write_still=True)
    print("CRYSTAL", state)
# ------------------------------------------------------------------ Crystal Evolution overlays (drawn over any state)
if "--paths" in ARGS:
    base_objs = [o for o in sc.objects if o.type == "MESH"]
    for o in base_objs:
        o.is_holdout = True            # hides overlay parts behind the crystal/collar; the overlay PNG is the addition only
    for i, s_ in enumerate(SHARDS):
        s_.location = base_loc[s_.name].copy()
    for c in CROWN:
        c.hide_render = False
    M_GOLD = bpy.data.materials.new("Gold")
    M_GOLD.use_nodes = True
    gb = M_GOLD.node_tree.nodes["Principled BSDF"]
    gb.inputs["Base Color"].default_value = lin("#a8843a")
    gb.inputs["Metallic"].default_value = 1.0
    gb.inputs["Roughness"].default_value = 0.35
    # shield shell: emission only at grazing angles (fresnel), fully transparent where it faces the camera
    M_SHELL = bpy.data.materials.new("Shell")
    M_SHELL.use_nodes = True
    st = M_SHELL.node_tree
    for n_ in list(st.nodes):
        if n_.type != "OUTPUT_MATERIAL":
            st.nodes.remove(n_)
    lw = st.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.2
    pw = st.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 3.0
    st.links.new(lw.outputs["Facing"], pw.inputs[0])
    em = st.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = lin("#8fe3ff")
    em.inputs["Strength"].default_value = 2.2
    tr = st.nodes.new("ShaderNodeBsdfTransparent")
    mx = st.nodes.new("ShaderNodeMixShader")
    st.links.new(pw.outputs["Value"], mx.inputs["Fac"])
    st.links.new(tr.outputs["BSDF"], mx.inputs[1])
    st.links.new(em.outputs["Emission"], mx.inputs[2])
    st.links.new(mx.outputs["Shader"], st.nodes["Material Output"].inputs["Surface"])
    M_RUNE, B_RUNE = mat_glass("Rune", "#ffd6f6", "#ff5fd2", 4.0)
    M_THORN, B_THORN = mat_scan("Thorn", "dark_rock", 3.0, tint="#a08a6a", value=0.75)

    def group(build):
        objs = build()
        sc.render.filepath = os.path.join(OUT, "crystal_path_%s@2x.png" % build.__name__[6:])
        bpy.ops.render.render(write_still=True)
        for o in objs:
            bpy.data.objects.remove(o, do_unlink=True)
        print("PATH", build.__name__[6:])

    def build_bastion():
        out = []
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.8, depth=0.2, location=(0, 0, 0.1))
        ring = bpy.context.object
        ring.modifiers.new("solid", "SOLIDIFY").thickness = -0.12
        ring.data.materials.append(M_TOOTH)
        out.append(ring)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.8, minor_radius=0.025, location=(0, 0, 0.22))
        bpy.context.object.data.materials.append(M_GOLD)
        out.append(bpy.context.object)
        for k in range(4):
            a = k / 4 * math.tau + 0.4
            bpy.ops.mesh.primitive_cube_add(size=1, location=(math.cos(a) * 0.82, math.sin(a) * 0.82, 0.35))
            b_ = bpy.context.object
            b_.scale = (0.18, 0.26, 0.7)
            b_.rotation_euler = (0, 0, a)
            b_.data.materials.append(M_TOOTH)
            out.append(b_)
            bpy.ops.mesh.primitive_cube_add(size=1, location=(math.cos(a) * 0.82, math.sin(a) * 0.82, 0.73))
            cap = bpy.context.object
            cap.scale = (0.2, 0.28, 0.04)
            cap.rotation_euler = (0, 0, a)
            cap.data.materials.append(M_GOLD)
            out.append(cap)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=0.95, location=(0, 0, 0.22))
        dome = bpy.context.object
        bm_ = bmesh.new()
        bm_.from_mesh(dome.data)
        bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if v.co.z < -0.01], context="VERTS")   # upper hemisphere only
        bm_.to_mesh(dome.data)
        bm_.free()
        dome.scale = (1, 1, 1.2)
        bpy.ops.object.shade_smooth()
        dome.data.materials.append(M_SHELL)
        out.append(dome)
        return out

    def build_pulse():
        out = []
        for k in range(12):
            a = k / 12 * math.tau
            bpy.ops.mesh.primitive_cube_add(size=1, location=(math.cos(a) * 0.72, math.sin(a) * 0.72, 1.05 + 0.06 * math.sin(a * 3)))
            r_ = bpy.context.object
            r_.scale = (0.03, 0.13, 0.18)
            r_.rotation_euler = (0, 0, a)
            r_.data.materials.append(M_RUNE)
            out.append(r_)
        for rad, z, th in ((0.72, 1.05, 0.012), (0.88, 1.05, 0.008)):
            bpy.ops.mesh.primitive_torus_add(major_radius=rad, minor_radius=th, major_segments=96, location=(0, 0, z))
            bpy.context.object.data.materials.append(M_RUNE)
            out.append(bpy.context.object)
        return out

    def build_thorn():
        out = []
        rnd = random.Random(5)
        for k in range(14):
            a = k / 14 * math.tau + rnd.uniform(-0.15, 0.15)
            h = rnd.uniform(0.35, 0.75)
            bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=0.07, radius2=0.0, depth=h,
                                            location=(math.cos(a) * 0.68, math.sin(a) * 0.68, 0.2 + h * 0.35))
            t_ = bpy.context.object
            tilt = rnd.uniform(0.35, 0.7)
            t_.rotation_euler = (-math.sin(a) * tilt, math.cos(a) * tilt, a)
            t_.data.materials.append(M_THORN)
            out.append(t_)
        return out

    for b_ in (build_bastion, build_pulse, build_thorn):
        group(b_)
print("CRYSTAL DONE", OUT)
