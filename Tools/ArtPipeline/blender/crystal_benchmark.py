"""Blender 4.x headless benchmark: the Crystal (3 damage states) as stylized 3D -> 2D sprites.

Run through the pipeline (never by hand into Assets/):
    python3 Tools/ArtPipeline/ap.py render --stage Temp/ArtStageBlender --only crystal
or directly:
    blender --background --factory-startup --python Tools/ArtPipeline/blender/crystal_benchmark.py -- <stage Art dir>

Deterministic: fixed geometry, fixed sample count and seed, Standard view transform, no denoiser.
Style match with the 2D set (Docs/Enhancement/ART_BIBLE.md): flat cel bands via an emission colour ramp
driven by a fixed light direction (no physically based shading), ink outline via Freestyle, soft ground
shadow via a shadow catcher. Engine: Cycles CPU (EEVEE needs libEGL, unavailable in this container).
Each output prints one "AW_OUTPUT {json}" line consumed by ap.py.
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else os.path.abspath("Temp/ArtStageBlender/Art")
W, H, PPU, PIVOT_Y = 320, 400, 160, 0.07
INK_SRGB = (0.11, 0.09, 0.19)
INK = tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in INK_SRGB)   # Freestyle colours are linear
MODEL_SCALE = 0.64   # crystal ~1.6 world units tall, same as the 2D sprite
LIGHT_DIR = Vector((-0.55, -0.75, 0.45)).normalized()

PALETTES = {
    "intact": ["#4f58e8", "#6f9bff", "#82d8ff", "#c8f6ff"],
    "cracked": ["#4f58e8", "#6f9bff", "#82d8ff", "#c8f6ff"],
    "critical": ["#b02a5c", "#e05a8a", "#ff8fb4", "#ffd0e0"],
}
CRACKS = {"intact": 0, "cracked": 2, "critical": 4}


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c) + (1.0,)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 48
    sc.cycles.seed = 7
    sc.cycles.use_denoising = False
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.render.use_freestyle = False
    # Byte-identical reruns: single render thread (sampling order) and no time/date metadata in the PNG.
    sc.render.threads_mode = "FIXED"
    sc.render.threads = 1
    for attr in ("use_stamp_date", "use_stamp_time", "use_stamp_render_time", "use_stamp_frame", "use_stamp_frame_range",
                 "use_stamp_memory", "use_stamp_hostname", "use_stamp_camera", "use_stamp_lens", "use_stamp_scene",
                 "use_stamp_marker", "use_stamp_filename", "use_stamp_sequencer_strip", "use_stamp_note"):
        if hasattr(sc.render, attr):
            setattr(sc.render, attr, False)
    sc.render.use_stamp = False
    bpy.data.collections.new("no_outline")
    return sc


def toon_material(name, palette, emit_strength=1.0):
    """Emission colour ramp on dot(normal, light): 4 constant bands = cel shade + highlight like the 2D set."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = LIGHT_DIR
    remap = nt.nodes.new("ShaderNodeMapRange")
    remap.inputs[1].default_value, remap.inputs[2].default_value = -1.0, 1.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, srgb(palette[0])
    els[1].position, els[1].color = 0.55, srgb(palette[1])
    for pos, col in ((0.74, palette[2]), (0.9, palette[3])):
        e = els.new(pos)
        e.color = srgb(col)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[1].default_value = emit_strength
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(geo.outputs["Normal"], dot.inputs[0])
    nt.links.new(dot.outputs["Value"], remap.inputs[0])
    nt.links.new(remap.outputs[0], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], em.inputs[0])
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def flat_material(name, rgba, strength=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = rgba
    em.inputs[1].default_value = strength
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


OUTLINE_WORLD = 0.032   # ~5 px at PPU 160 (2D set uses ~6 px ink at 320 canvas)


def outline_material():
    m = bpy.data.materials.get("outline")
    if m:
        return m
    m = bpy.data.materials.new("outline")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    lp = nt.nodes.new("ShaderNodeNewGeometry")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = INK + (1.0,)
    mix = nt.nodes.new("ShaderNodeMixShader")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(lp.outputs["Backfacing"], mix.inputs[0])
    # Inverted hull: the shell's near side faces away from the camera (back-facing) -> transparent ("culled");
    # its far side faces the camera and only shows as a rim around the silhouette -> ink.
    nt.links.new(em.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    return m


def add_outline(ob, thickness=OUTLINE_WORLD):
    ob.data.materials.append(outline_material())
    mod = ob.modifiers.new("outline", "SOLIDIFY")
    mod.thickness = thickness / max(ob.scale)
    mod.offset = 1.0
    mod.use_flip_normals = True
    mod.material_offset = len(ob.data.materials) - 1
    mod.use_rim = False


def bipyramid(name, rings, sides, mat, loc=(0, 0, 0), rot=(0, 0, 0)):
    """rings: [(z, radius)] bottom->top; apexes at the first/last entries with radius 0."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    loops = []
    for z, r in rings:
        if r == 0:
            loops.append([bm.verts.new((0, 0, z))])
        else:
            loops.append([bm.verts.new((r * math.cos(2 * math.pi * i / sides + 0.4), r * 0.82 * math.sin(2 * math.pi * i / sides + 0.4), z)) for i in range(sides)])
    for a, b in zip(loops, loops[1:]):
        if len(a) == 1:
            for i in range(sides):
                bm.faces.new((a[0], b[(i + 1) % sides], b[i]))
        elif len(b) == 1:
            for i in range(sides):
                bm.faces.new((a[i], a[(i + 1) % sides], b[0]))
        else:
            for i in range(sides):
                bm.faces.new((a[i], a[(i + 1) % sides], b[(i + 1) % sides], b[i]))
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.location, ob.rotation_euler = loc, rot
    ob.data.materials.append(mat)
    add_outline(ob)
    return ob


def build(state):
    sc = reset()
    pal = PALETTES[state]
    crystal = toon_material("crystal", pal, 1.0)
    bipyramid("core", [(0.35, 0), (0.55, 0.42), (1.35, 0.6), (2.25, 0)], 6, crystal)
    for s in (-1, 1):
        bipyramid("shard%d" % s, [(0.0, 0), (0.25, 0.14), (0.62, 0)], 4, crystal, loc=(s * 0.95, -0.05, 0.62), rot=(0, s * -0.22, 0))
    metal = toon_material("metal", ["#7c8098", "#a3a8be", "#c9cddc", "#eceef6"])
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.86, depth=0.3, location=(0, 0, 0.15))
    ped = bpy.context.active_object
    ped.scale = (1, 0.62, 1)
    bev = ped.modifiers.new("bevel", "BEVEL")
    bev.width, bev.segments = 0.08, 3
    ped.data.materials.append(metal)
    add_outline(ped)
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=0.52, depth=0.16, location=(0, 0, 0.38))
    top = bpy.context.active_object
    top.scale = (1, 0.62, 1)
    top.data.materials.append(metal)
    add_outline(top)
    lamp_col = srgb("#9ff0ff" if state != "critical" else "#ffa8c8")
    dots = flat_material("dots", lamp_col, 2.0)
    for i in range(5):
        a = math.pi * (0.62 + 0.19 * i)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.055, segments=12, ring_count=8,
                                             location=(0.84 * math.cos(a) * -1, 0.62 * 0.84 * math.sin(a) * -1 - 0.02, 0.15))
        bpy.context.active_object.data.materials.append(dots)
    ink = flat_material("ink", srgb("#1c1730"))
    for k in range(CRACKS[state]):
        x0 = -0.18 + 0.2 * k
        pts = [(x0, -0.5, 1.05 + 0.18 * k), (x0 + 0.12, -0.52, 1.25 + 0.12 * k), (x0 - 0.02, -0.53, 1.45 + 0.1 * k), (x0 + 0.1, -0.5, 1.68 + 0.05 * k)]
        cu = bpy.data.curves.new("crack%d" % k, "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = 0.018
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for p, c in zip(sp.points, pts):
            p.co = (*c, 1)
        ob = bpy.data.objects.new("crack%d" % k, cu)
        bpy.context.collection.objects.link(ob)
        ob.data.materials.append(ink)
    # Ground shadow (shadow catcher) under a soft sun.
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.is_shadow_catcher = True
    for c in plane.users_collection:
        c.objects.unlink(plane)
    bpy.context.scene.collection.objects.link(plane)
    # Scale the whole model about the ground origin (shadow catcher and camera stay put).
    for ob in list(bpy.context.scene.objects):
        if ob.type in ("MESH", "CURVE") and ob is not plane:
            ob.location = ob.location * MODEL_SCALE
            ob.scale = ob.scale * MODEL_SCALE
            for mod in ob.modifiers:
                if mod.type == "SOLIDIFY":
                    mod.thickness = OUTLINE_WORLD / max(ob.scale)
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy, sun.angle = 3.0, math.radians(18)
    so = bpy.data.objects.new("sun", sun)
    bpy.context.collection.objects.link(so)
    so.rotation_euler = (math.radians(12), math.radians(-10), 0)
    # Orthographic camera: 15° above the horizon; ground origin lands on the sprite pivot row.
    cam = bpy.data.cameras.new("cam")
    cam.type = "ORTHO"
    cam.ortho_scale = H / PPU
    co = bpy.data.objects.new("cam", cam)
    bpy.context.collection.objects.link(co)
    e = math.radians(15)
    pivot_off = (H / 2 - PIVOT_Y * H) / PPU          # world units between image centre and pivot row
    target = Vector((0, 0, pivot_off / math.cos(e)))
    co.location = target + Vector((0, -math.cos(e), math.sin(e))) * 20
    co.rotation_euler = (math.pi / 2 - e, 0, 0)
    sc.camera = co
    rel = "World/crystal_%s.png" % state
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("AW_OUTPUT " + json.dumps({"rel": rel, "blender": bpy.app.version_string,
                                     "settings": {"sprite": True, "ppu": PPU, "pivot": [0.5, PIVOT_Y], "border": [0, 0, 0, 0], "filter": 1, "maxSize": 2048}}))


for st in ("intact", "cracked", "critical"):
    build(st)
