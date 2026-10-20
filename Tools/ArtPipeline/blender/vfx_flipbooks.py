"""VFX flipbooks for Unity — Blender 4.5 headless: Mantaflow fire/smoke/steam, procedural lightning and splashes.

  blender -b --factory-startup --python Tools/ArtPipeline/blender/vfx_flipbooks.py -- --out ArtCache/Vfx [--only fire_burst]

Each effect renders FRAMES transparent frames at CELL px, seen from the game camera (orthographic, 38.3 deg elevation),
centred on the effect origin; Tools/ArtPipeline/vfx_sheets.py packs them into a 4x4 sheet (1024 px, power of two).
Lighting is emissive (fire, lightning) or the shared moon key (smoke, steam, water) so effects sit in the battlefield light.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(ARGS[ARGS.index("--out") + 1] if "--out" in ARGS else "ArtCache/Vfx")
ONLY = ARGS[ARGS.index("--only") + 1] if "--only" in ARGS else None
FRAMES, CELL = 16, 256
SIN = 0.62
ELEV = math.asin(SIN)


def lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c) + (1.0,)


def fresh_scene(extent):
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
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.cycles.volume_bounces = 2
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = CELL
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.new("W")
    sc.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = lin("#1a2a44")
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.3
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = extent
    d = Vector((0, math.cos(ELEV), -SIN))
    cam.location = Vector((0, 0, extent * 0.42)) - d * 30
    cam.rotation_euler = (math.pi / 2 - ELEV, 0, 0)
    key = bpy.data.objects.new("Key", bpy.data.lights.new("Key", "SUN"))
    key.data.energy = 2.5
    key.rotation_euler = Vector((0.55, 0.62, -0.75)).normalized().to_track_quat("-Z", "Y").to_euler()
    sc.collection.objects.link(key)
    return sc


def render_frames(sc, name, start, step):
    os.makedirs(os.path.join(OUT, name), exist_ok=True)
    for i in range(FRAMES):
        sc.frame_set(start + i * step)
        sc.render.filepath = os.path.join(OUT, name, "%02d.png" % i)
        bpy.ops.render.render(write_still=True)
    print("FLIPBOOK", name)


def mantaflow(name, kind, color_fire="#ff6a1f", smoke_color="#3a3634", flame_rate=1.0, smoke_density=1.0, size=2.0,
              burst=6, res=96, start=4, step=2, temp=1.0, vorticity=0.25, fuel=1.0, blackbody=1.0, smoke_emit=0.0):
    """A short burst from a sphere emitter inside a gas domain; the emitter switches off after `burst` frames."""
    sc = fresh_scene(size * 0.9)
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, size * 0.42))
    dom = bpy.context.object
    mod = dom.modifiers.new("Fluid", "FLUID")
    mod.fluid_type = "DOMAIN"
    ds = mod.domain_settings
    ds.domain_type = "GAS"
    ds.resolution_max = res
    ds.use_adaptive_domain = False
    ds.vorticity = vorticity
    ds.alpha = 1.0 if kind != "steam" else 0.4
    ds.beta = 1.5 * temp
    ds.cache_directory = os.path.join(OUT, "_cache", name)
    ds.cache_frame_start, ds.cache_frame_end = 1, start + FRAMES * step + 2
    ds.cache_type = "ALL"
    ds.use_dissolve_smoke = True
    ds.dissolve_speed = 18 if kind == "steam" else 26
    ds.burning_rate = 0.45
    ds.flame_smoke = smoke_density
    ds.flame_vorticity = 0.9
    ds.use_noise = True                 # wavelet upres: small-scale flame and smoke detail
    ds.noise_scale = 2
    ds.noise_strength = 1.2
    bpy.ops.mesh.primitive_ico_sphere_add(radius=size * 0.12, location=(0, 0, size * 0.12))
    em = bpy.context.object
    m2 = em.modifiers.new("Fluid", "FLUID")
    m2.fluid_type = "FLOW"
    fs = m2.flow_settings
    fs.flow_type = {"fire": "BOTH", "smoke": "SMOKE", "steam": "SMOKE"}[kind]
    fs.flow_behavior = "INFLOW"
    fs.flow_source = "MESH"
    fs.fuel_amount = fuel
    fs.temperature = temp
    fs.smoke_color = lin(smoke_color)[:3]
    fs.use_initial_velocity = True
    fs.velocity_normal = 2.0 if kind != "smoke" else 1.0
    fs.velocity_coord = (0, 0, 1.5)
    em.hide_render = True
    # emitter on for `burst` frames only
    fs.surface_distance = 1.5
    m2.show_viewport = True
    for f, on in ((1, True), (burst, True), (burst + 1, False)):
        sc.frame_set(f)
        fs.flow_behavior = "INFLOW" if on else "GEOMETRY"
        fs.keyframe_insert("flow_behavior") if hasattr(fs, "keyframe_insert") else None
        m2.show_render = on
        em.keyframe_insert("hide_viewport")
    # bake
    sc.frame_set(1)
    bpy.context.view_layer.objects.active = dom
    with bpy.context.temp_override(object=dom, active_object=dom):
        bpy.ops.fluid.bake_all()
    # volume shader: principled volume with blackbody flame
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Color"].default_value = lin(smoke_color)
    pv.inputs["Density"].default_value = 3.0 * smoke_density
    if kind == "fire":
        # the flame field drives a blackbody emission: white-hot core, orange body, red tips
        fa = nt.nodes.new("ShaderNodeAttribute")
        fa.attribute_name = "flame"
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = 12.0 * blackbody
        nt.links.new(fa.outputs["Fac"], mul.inputs[0])
        nt.links.new(mul.outputs["Value"], pv.inputs["Blackbody Intensity"])
        pv.inputs["Blackbody Tint"].default_value = lin(color_fire)
        # Principled Volume reads the "temperature" attribute by default in 4.5
        pv.inputs["Temperature"].default_value = 1300
        pv.inputs["Emission Strength"].default_value = 0.0
    if smoke_emit > 0:
        pv.inputs["Emission Strength"].default_value = smoke_emit
        pv.inputs["Emission Color"].default_value = lin(color_fire)
    nt.links.new(pv.outputs["Volume"], nt.nodes["Material Output"].inputs["Volume"])
    dom.data.materials.append(mat)
    render_frames(sc, name, start, step)


def lightning(name="lightning_arc", color="#b06cff", core="#fff4c8"):
    """A forking bolt redrawn every frame (random walk), fading over the last frames; emissive tube curves."""
    sc = fresh_scene(2.4)
    rnd = random.Random(7)
    mat = bpy.data.materials.new("Bolt")
    mat.use_nodes = True
    nt = mat.node_tree
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = lin(core)
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    glow = bpy.data.materials.new("BoltGlow")
    glow.use_nodes = True
    g = glow.node_tree
    for n in list(g.nodes):
        if n.type != "OUTPUT_MATERIAL":
            g.nodes.remove(n)
    ve = g.nodes.new("ShaderNodeEmission")
    ve.inputs["Color"].default_value = lin(color)
    tr = g.nodes.new("ShaderNodeBsdfTransparent")
    mx = g.nodes.new("ShaderNodeMixShader")
    mx.inputs[0].default_value = 0.6
    g.links.new(tr.outputs[0], mx.inputs[1])
    g.links.new(ve.outputs[0], mx.inputs[2])
    g.links.new(mx.outputs[0], g.nodes["Material Output"].inputs["Surface"])
    os.makedirs(os.path.join(OUT, name), exist_ok=True)
    for i in range(FRAMES):
        for o in list(sc.objects):
            if o.type == "CURVE":
                bpy.data.objects.remove(o, do_unlink=True)
        life = 1.0 - max(0, i - 9) / 6.0
        for branch in range(1 + (i % 3 == 0) + rnd.randint(0, 2)):
            cu = bpy.data.curves.new("b", "CURVE")
            cu.dimensions = "3D"
            sp = cu.splines.new("POLY")
            pts = []
            p = Vector((rnd.uniform(-0.15, 0.15), 0, 2.0)) if branch == 0 else Vector((rnd.uniform(-0.3, 0.3), 0, rnd.uniform(0.8, 1.6)))
            end = Vector((rnd.uniform(-0.2, 0.2), 0, 0.0)) if branch == 0 else p + Vector((rnd.uniform(-0.8, 0.8), 0, -rnd.uniform(0.4, 0.8)))
            n = 14
            for k in range(n + 1):
                t = k / n
                q = p.lerp(end, t) + Vector((rnd.uniform(-0.12, 0.12), rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05))) * (1 - abs(0.5 - t))
                pts.append(q)
            sp.points.add(len(pts) - 1)
            for k, q in enumerate(pts):
                sp.points[k].co = (q.x, q.y, q.z, 1)
            for mat_, depth in ((mat, 0.012 * life), (glow, 0.05 * life)):
                c2 = cu.copy()
                c2.bevel_depth = max(depth, 0.001)
                o = bpy.data.objects.new("bolt", c2)
                sc.collection.objects.link(o)
                o.data.materials.append(mat_)
        em.inputs["Strength"].default_value = 30 * life
        ve.inputs["Strength"].default_value = 8 * life
        sc.render.filepath = os.path.join(OUT, name, "%02d.png" % i)
        bpy.ops.render.render(write_still=True)
    print("FLIPBOOK", name)


def splash(name="water_splash", color="#2f8cff"):
    """Droplets thrown up and falling (particles instancing small spheres), with a ring of spray; glossy water."""
    sc = fresh_scene(2.2)
    sc.frame_end = 40
    water = bpy.data.materials.new("Water")
    water.use_nodes = True
    b = water.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lin(color)
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["Transmission Weight"].default_value = 0.6
    b.inputs["Emission Color"].default_value = lin("#5fe0ff")
    b.inputs["Emission Strength"].default_value = 0.6
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=(0, 0, -20))
    drop = bpy.context.object
    drop.data.materials.append(water)
    bpy.ops.mesh.primitive_circle_add(radius=0.18, fill_type="NGON", location=(0, 0, 0.05))
    emit = bpy.context.object
    emit.hide_render = True
    ps = emit.modifiers.new("ps", "PARTICLE_SYSTEM").particle_system.settings
    ps.count = 260
    ps.frame_start, ps.frame_end = 1, 5
    ps.lifetime = 40
    ps.normal_factor = 3.2
    ps.factor_random = 1.6
    ps.render_type = "OBJECT"
    ps.instance_object = drop
    ps.particle_size = 1.0
    ps.size_random = 0.7
    ps.effector_weights.gravity = 1.0
    sc.frame_set(1)
    render_frames(sc, name, 2, 2)


EFFECTS = {
    "fire_burst": lambda: mantaflow("fire_burst", "fire", burst=9, temp=1.6, smoke_density=0.7, smoke_color="#2a2220", start=3, step=1,
                                    color_fire="#ff4a12"),
    "smoke_puff": lambda: mantaflow("smoke_puff", "smoke", burst=4, temp=0.6, smoke_density=0.8, smoke_color="#7a7470", size=1.8, start=2, step=2),
    "steam_burst": lambda: mantaflow("steam_burst", "steam", burst=5, temp=1.2, smoke_density=0.5, smoke_color="#dfe8f0", smoke_emit=0.25,
                                     color_fire="#bfe8ff", size=2.0),
    "rift_mist": lambda: mantaflow("rift_mist", "smoke", burst=8, temp=0.5, smoke_density=0.5, smoke_color="#3a1428", smoke_emit=0.8,
                                   color_fire="#c0304a", size=1.8),
    "lightning_arc": lightning,
    "water_splash": splash,
}
for name, fn in EFFECTS.items():
    if ONLY and ONLY != name:
        continue
    fn()
print("VFX DONE", OUT)
