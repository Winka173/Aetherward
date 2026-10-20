"""Visual-direction benchmark scene (art direction reset). Blender 4.x headless, Cycles CPU.

One shared gameplay layout, three looks, rendered from the SAME scene and camera:
  mythic     Dark Mythic Fantasy: physically lit materials, moonlight key + crystal light + braziers, rim light, thin fog, AgX high contrast
  painterly  Painterly 2.5D: same scene, softer warm/cool light, then Kuwahara brush filter (Blender compositor) + grade
  pixel      Dark Fantasy Pixel Art: low-res render (640x360) with depth-edge outlines; palette quantised + 3x nearest upscale in Python

Usage (repo root):
  blender --background --factory-startup --python Tools/ArtPipeline/blender/direction_benchmark.py -- --look mythic --out Reports/ArtDirection/raw/mythic.png [--res 1280 720] [--samples 128]

Everything is procedural and original (no external assets). Layout = Aetherward gameplay: crystal at the centre of a
stone arena, 6 heroes on formation nodes, 4 enemy archetypes on lanes, 1 boss with a ground telegraph, elemental VFX.
"""
import math
import random
import sys

import bmesh
import bpy
from mathutils import Euler, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default, n=1):
    if name in argv:
        i = argv.index(name)
        return argv[i + 1] if n == 1 else argv[i + 1:i + 1 + n]
    return default


LOOK = arg("--look", "mythic")
OUT = arg("--out", "/tmp/bench.png")
RES = [int(v) for v in arg("--res", ["1280", "720"], 2)]
SAMPLES = int(arg("--samples", "96"))
SOLO = arg("--solo", None)          # render one unit alone (closeup sheet): hero/enemy/boss id
RNG = random.Random(7)


# ----------------------------------------------------------------------------- helpers

def srgb(h, a=1.0):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c) + (a,)


MATS = {}


def mat(name, color, rough=0.6, metal=0.0, emit=None, emit_strength=0.0, noise=0.0, noise_scale=6.0, subsurface=0.0, alpha=1.0):
    key = (name, color, rough, metal, emit, emit_strength, noise)
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb(color)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
    if emit:
        bsdf.inputs["Emission Color"].default_value = srgb(emit)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    if noise > 0:
        # Material breakup: noise-driven value variation (worn stone, cloth, metal scratches).
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = noise_scale
        tex.inputs["Detail"].default_value = 8.0
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        c = srgb(color)
        ramp.color_ramp.elements[0].color = tuple(v * (1 - noise) for v in c[:3]) + (1,)
        ramp.color_ramp.elements[1].color = tuple(min(1, v * (1 + noise * 0.6)) for v in c[:3]) + (1,)
        nt.links.new(tex.outputs["Fac"], ramp.inputs[0])
        nt.links.new(ramp.outputs[0], bsdf.inputs["Base Color"])
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.25
        nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    MATS[key] = m
    return m


def link(ob, coll=None):
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob


def prim(kind, loc, scale=(1, 1, 1), rot=(0, 0, 0), material=None, smooth=True, bevel=0.0, **kw):
    ops = {"cube": bpy.ops.mesh.primitive_cube_add, "sphere": bpy.ops.mesh.primitive_uv_sphere_add,
           "cyl": bpy.ops.mesh.primitive_cylinder_add, "cone": bpy.ops.mesh.primitive_cone_add,
           "ico": bpy.ops.mesh.primitive_ico_sphere_add, "torus": bpy.ops.mesh.primitive_torus_add}
    ops[kind](location=loc, rotation=rot, **kw)
    ob = bpy.context.active_object
    ob.scale = scale
    if material:
        ob.data.materials.append(material)
    if smooth and kind in ("sphere", "cyl", "cone", "torus"):
        bpy.ops.object.shade_smooth()
    if bevel:
        m = ob.modifiers.new("bevel", "BEVEL")
        m.width, m.segments = bevel, 2
    return ob


def parent_all(objs, root):
    for o in objs:
        o.parent = root


def group(name, loc, rot_z=0.0, scale=1.0):
    e = bpy.data.objects.new(name, None)
    link(e)
    e.location = loc
    e.rotation_euler = (0, 0, rot_z)
    e.scale = (scale, scale, scale)
    return e


def limb(a, b, r, material, r2=None):
    """Tapered cylinder from point a to b (arms, legs, weapons shafts)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cone_add(vertices=14, radius1=r, radius2=r2 if r2 is not None else r * 0.85, depth=d.length,
                                    location=(a + b) / 2)
    ob = bpy.context.active_object
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    ob.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return ob


def cape(points_top, length, width, material, sway=0.15):
    """Cloth panel: subdivided plane bent down and back with a little sway (cloaks, banners, tabards)."""
    bpy.ops.mesh.primitive_plane_add(size=1)
    ob = bpy.context.active_object
    ob.scale = (width, length, 1)
    bpy.ops.object.transform_apply(scale=True)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=8, use_grid_fill=True)
    for v in bm.verts:
        t = (0.5 - v.co.y / length)          # 0 at top, 1 at bottom
        v.co = Vector((v.co.x * (1 + 0.35 * t), -0.12 * t - math.sin(v.co.x * 9) * sway * t, -t * length + length * 0.5))
    bm.to_mesh(ob.data)
    bm.free()
    ob.location = points_top
    s = ob.modifiers.new("thick", "SOLIDIFY")
    s.thickness = 0.02
    ob.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return ob


# ----------------------------------------------------------------------------- characters (heroic proportions, ~1.7 m)

STEEL = None


def humanoid(name, loc, rot_z, palette, build=1.0, pose="stand"):
    """Body: legs, torso, head, arms. Returns (root, parts, hand_r, hand_l, head_pos)."""
    root = group(name, loc, rot_z)
    skin = mat("skin", palette.get("skin", "#c99a7a"), 0.55, subsurface=0.1)
    cloth = mat(name + "_cloth", palette["cloth"], 0.85, noise=0.25, noise_scale=14)
    armor = mat(name + "_armor", palette.get("armor", palette["cloth"]), palette.get("armor_rough", 0.35), palette.get("armor_metal", 0.0), noise=0.15, noise_scale=20)
    trim = mat(name + "_trim", palette.get("trim", "#b08a3a"), 0.3, 0.9)
    w = 0.13 * build
    parts = []
    crouch = 0.12 if pose == "crouch" else 0.0
    # legs
    for s in (-1, 1):
        parts.append(limb((s * w, 0, 0.82 - crouch), (s * w * 1.1, 0.06 * s, 0.05), 0.075 * build, cloth))
        parts.append(prim("cube", (s * w * 1.1, -0.04, 0.06), (0.09 * build, 0.15, 0.06), material=armor, bevel=0.02))
    # torso (tapered) + belt
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.17 * build, radius2=0.23 * build, depth=0.62, location=(0, 0, 1.13 - crouch))
    torso = bpy.context.active_object
    torso.scale = (1, 0.72, 1)
    torso.data.materials.append(armor)
    bpy.ops.object.shade_smooth()
    parts.append(torso)
    parts.append(prim("torus", (0, 0, 0.86 - crouch), (0.19 * build, 0.14 * build, 0.5), material=trim, major_radius=1, minor_radius=0.18))
    # head + neck
    head = (0, 0.02, 1.62 - crouch)
    parts.append(limb((0, 0, 1.42 - crouch), (0, 0.01, 1.52 - crouch), 0.055, skin))
    parts.append(prim("sphere", head, (0.1, 0.11, 0.125), material=skin, segments=24, ring_count=16))
    # arms (shoulders -> hands), pose dependent
    sh_r, sh_l = Vector((0.24 * build, 0, 1.38 - crouch)), Vector((-0.24 * build, 0, 1.38 - crouch))
    hand_r = Vector(palette.get("hand_r", (0.34 * build, -0.18, 1.0 - crouch)))
    hand_l = Vector(palette.get("hand_l", (-0.34 * build, -0.16, 1.02 - crouch)))
    for sh, hd in ((sh_r, hand_r), (sh_l, hand_l)):
        elbow = (sh + hd) / 2 + Vector((0, 0.06, -0.05))
        parts.append(limb(sh, elbow, 0.06 * build, cloth))
        parts.append(limb(elbow, hd, 0.055 * build, armor if palette.get("gauntlets") else skin))
        parts.append(prim("sphere", sh, (0.09 * build, 0.09 * build, 0.08 * build), material=armor, segments=16, ring_count=10))
    parent_all(parts, root)
    return root, parts, hand_r, hand_l, Vector(head), {"cloth": cloth, "armor": armor, "trim": trim, "skin": skin}


def weapon_blade(root, hand, length, material, glow=None, angle=(0.3, 0, 0)):
    g = []
    tip = hand + Vector((0, -0.05, length)).__class__((0, math.sin(angle[0]) * -length, math.cos(angle[0]) * length))
    bpy.ops.mesh.primitive_cube_add(location=(hand + tip) / 2)
    b = bpy.context.active_object
    b.scale = (0.035, 0.008, length / 2)
    b.rotation_euler = ((tip - hand).to_track_quat("Z", "Y").to_euler())
    b.data.materials.append(material if not glow else mat("glowblade", "#d8e4ff", 0.2, 0.8, glow, 3.0))
    g.append(b)
    g.append(prim("cube", hand + Vector((0, 0, 0.02)), (0.12, 0.03, 0.025), material=mat("guard", "#8a6a2a", 0.3, 1.0)))
    parent_all(g, root)
    return g


def hero_knight(loc, rot):
    p = {"cloth": "#2a3348", "armor": "#9aa3b5", "armor_metal": 1.0, "armor_rough": 0.28, "trim": "#c9a24a", "gauntlets": True,
         "hand_r": (0.36, -0.22, 1.05), "hand_l": (-0.3, -0.3, 1.0)}
    root, parts, hr, hl, head, m = humanoid("knight", loc, rot, p, build=1.15)
    o = []
    o.append(prim("sphere", head + Vector((0, 0, 0.02)), (0.13, 0.14, 0.15), material=m["armor"], segments=20, ring_count=12))   # great helm
    o.append(prim("cube", head + Vector((0, -0.12, 0.0)), (0.08, 0.02, 0.012), material=mat("visor", "#0a0a10", 0.4)))
    o.append(cape(head + Vector((0, 0.0, 0.28)), 0.28, 0.06, mat("plume", "#b0262e", 0.8), sway=0.05))                          # plume
    shield = prim("cube", hl + Vector((-0.05, -0.12, 0.05)), (0.05, 0.36, 0.5), material=mat("shield", "#2e4a8a", 0.4, 0.4, noise=0.2), bevel=0.04)
    shield.rotation_euler = (0, 0, 0.35)
    o.append(shield)
    o.append(prim("cyl", hl + Vector((-0.11, -0.2, 0.08)), (0.13, 0.13, 0.02), rot=(0, math.pi / 2, 0.35), material=m["trim"]))
    o += weapon_blade(root, hr, 1.0, mat("steel", "#c8ceda", 0.2, 1.0))
    o.append(cape(Vector((0, 0.12, 1.42)), 1.15, 0.5, mat("knight_cape", "#5a1520", 0.9, noise=0.2)))
    parent_all(o, root)
    return root


def hero_mage(loc, rot):
    p = {"cloth": "#3a1f5a", "armor": "#3a1f5a", "trim": "#d0a040", "hand_r": (0.32, -0.15, 1.15), "hand_l": (-0.38, -0.25, 1.25)}
    root, parts, hr, hl, head, m = humanoid("mage", loc, rot, p, build=0.95)
    o = []
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.42, radius2=0.18, depth=1.0, location=(0, 0, 0.5))          # long robe
    robe = bpy.context.active_object
    robe.data.materials.append(mat("robe", "#2c1748", 0.9, noise=0.3, noise_scale=10))
    bpy.ops.object.shade_smooth()
    o.append(robe)
    hat = prim("cone", head + Vector((0, 0.05, 0.22)), (0.2, 0.2, 0.42), rot=(0.35, 0, 0), material=mat("hat", "#241238", 0.85), vertices=20)
    o.append(hat)
    o.append(prim("torus", head + Vector((0, 0, 0.06)), (0.26, 0.26, 0.4), material=mat("hat", "#241238", 0.85), major_radius=1, minor_radius=0.25))
    o.append(limb(hr + Vector((0, 0, -1.0)), hr + Vector((0.05, -0.05, 0.75)), 0.025, mat("wood", "#4a2e1a", 0.7, noise=0.3)))  # staff
    orb = prim("ico", hr + Vector((0.05, -0.05, 0.85)), (0.11, 0.11, 0.11), material=mat("fireorb", "#ff7a2a", 0.2, emit="#ff6a1a", emit_strength=12), subdivisions=2)
    o.append(orb)
    l = bpy.data.lights.new("mage_light", "POINT")
    l.energy, l.color, l.shadow_soft_size = 60, (1.0, 0.45, 0.15), 0.2
    lo = bpy.data.objects.new("mage_light", l)
    link(lo)
    lo.location = hr + Vector((0.05, -0.05, 0.85))
    o.append(lo)
    o.append(prim("ico", hl, (0.07, 0.07, 0.07), material=mat("spark", "#ffb050", 0.2, emit="#ff9a3a", emit_strength=20), subdivisions=1))
    parent_all(o, root)
    return root


def hero_ranger(loc, rot):
    p = {"cloth": "#2f3d26", "armor": "#5a4630", "trim": "#8a7a5a", "hand_r": (0.2, -0.35, 1.25), "hand_l": (-0.42, -0.35, 1.3)}
    root, parts, hr, hl, head, m = humanoid("ranger", loc, rot, p, build=0.95)
    o = []
    o.append(prim("cone", head + Vector((0, 0.06, 0.04)), (0.17, 0.19, 0.24), rot=(0.25, 0, 0), material=mat("hood", "#26331f", 0.9, noise=0.25), vertices=18))
    o.append(cape(Vector((0, 0.12, 1.45)), 1.05, 0.45, mat("rcloak", "#1f2a1a", 0.95, noise=0.3)))
    # longbow: arc of a torus segment
    bow = prim("torus", hl + Vector((0, 0, 0)), (0.1, 0.6, 0.6), rot=(0, math.pi / 2, 0), material=mat("bow", "#5a3a1e", 0.6, noise=0.2),
               major_radius=1, minor_radius=0.05)
    o.append(bow)
    o.append(limb(hl + Vector((0, 0.05, 0.58)), hl + Vector((0, 0.05, -0.58)), 0.006, mat("string", "#e8e0c8", 0.5)))
    o.append(limb(hr, hl + Vector((-0.05, -0.02, 0)), 0.01, mat("arrow", "#c8b090", 0.6)))
    o.append(prim("cyl", (0.1, 0.18, 1.2), (0.06, 0.06, 0.28), rot=(0.25, 0, 0), material=mat("quiver", "#4a3020", 0.7)))
    parent_all(o, root)
    return root


def hero_cleric(loc, rot):
    p = {"cloth": "#e8e2d0", "armor": "#d8c89a", "armor_metal": 0.6, "armor_rough": 0.3, "trim": "#e0b84a",
         "hand_r": (0.34, -0.15, 1.1), "hand_l": (-0.3, -0.25, 1.32)}
    root, parts, hr, hl, head, m = humanoid("cleric", loc, rot, p, build=1.0)
    o = []
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.38, radius2=0.2, depth=0.95, location=(0, 0, 0.48))
    robe = bpy.context.active_object
    robe.data.materials.append(mat("crobe", "#ece6d6", 0.85, noise=0.2, noise_scale=12))
    bpy.ops.object.shade_smooth()
    o.append(robe)
    o.append(prim("torus", head + Vector((0, 0.08, 0.22)), (0.2, 0.2, 0.2), rot=(1.3, 0, 0), material=mat("halo", "#ffe6a0", 0.2, emit="#ffd060", emit_strength=8),
                  major_radius=1, minor_radius=0.08))
    o.append(limb(hr + Vector((0, 0, -0.1)), hr + Vector((0, -0.05, 0.45)), 0.03, mat("gold", "#d0a040", 0.25, 1.0)))
    o.append(prim("ico", hr + Vector((0, -0.05, 0.5)), (0.09, 0.09, 0.09), material=mat("gold", "#d0a040", 0.25, 1.0), subdivisions=2))
    o.append(prim("ico", hl + Vector((0, 0, 0.1)), (0.1, 0.1, 0.1), material=mat("holy", "#fff2c0", 0.2, emit="#ffe39a", emit_strength=15), subdivisions=2))
    l = bpy.data.lights.new("cleric_light", "POINT")
    l.energy, l.color = 40, (1.0, 0.85, 0.5)
    lo = bpy.data.objects.new("cleric_light", l)
    link(lo)
    lo.location = hl + Vector((0, 0, 0.1))
    o.append(lo)
    parent_all(o, root)
    return root


def hero_rogue(loc, rot):
    p = {"cloth": "#1c1a22", "armor": "#2e2a36", "trim": "#7a2a3a", "hand_r": (0.38, -0.3, 0.95), "hand_l": (-0.38, -0.25, 0.95)}
    root, parts, hr, hl, head, m = humanoid("rogue", loc, rot, p, build=0.9, pose="crouch")
    o = []
    o.append(prim("cone", head + Vector((0, 0.05, 0.03)), (0.15, 0.17, 0.22), rot=(0.3, 0, 0), material=mat("rhood", "#18161e", 0.9), vertices=16))
    o.append(prim("cube", head + Vector((0, -0.1, -0.03)), (0.09, 0.02, 0.04), material=mat("mask", "#5a1a2a", 0.7)))
    o.append(cape(Vector((0, 0.1, 1.3)), 0.9, 0.42, mat("scarf", "#6a1a2a", 0.9, noise=0.2), sway=0.3))
    for h in (hr, hl):
        o += weapon_blade(root, h, 0.38, None, glow="#9a5aff", angle=(-0.6, 0, 0))
    parent_all(o, root)
    return root


def hero_berserker(loc, rot):
    p = {"skin": "#b07a5a", "cloth": "#4a3020", "armor": "#5a4a3a", "armor_metal": 0.3, "trim": "#8a6a3a", "gauntlets": True,
         "hand_r": (0.3, -0.25, 1.45), "hand_l": (-0.2, -0.28, 1.3)}
    root, parts, hr, hl, head, m = humanoid("berserker", loc, rot, p, build=1.3)
    o = []
    for s in (-1, 1):
        o.append(prim("cone", head + Vector((s * 0.13, 0, 0.08)), (0.04, 0.04, 0.2), rot=(0, s * -0.9, 0), material=mat("horn", "#e8dcc0", 0.5), vertices=12))
    o.append(prim("sphere", head + Vector((0, 0, 0.04)), (0.115, 0.125, 0.1), material=mat("helm", "#6a5a4a", 0.4, 0.8)))
    o.append(prim("cube", (0, 0.05, 1.35), (0.34, 0.2, 0.08), material=mat("fur", "#6a5a48", 0.95, noise=0.4, noise_scale=30)))
    # great axe over the shoulder
    shaft_a, shaft_b = hr + Vector((0.05, 0.35, -0.5)), hr + Vector((-0.05, -0.2, 0.5))
    o.append(limb(shaft_a, shaft_b, 0.03, mat("wood", "#4a2e1a", 0.7, noise=0.3)))
    axe = prim("cylinder" if False else "cyl", shaft_b + Vector((0.18, 0, -0.05)), (0.32, 0.03, 0.22), rot=(math.pi / 2, 0, 0), material=mat("axe", "#8a8e98", 0.3, 1.0, noise=0.2),
               vertices=3)
    o.append(axe)
    parent_all(o, root)
    return root


def enemy_ghoul(loc, rot):
    root = group("ghoul", loc, rot, 0.9)
    flesh = mat("ghoul", "#6a7a5a", 0.7, noise=0.4, noise_scale=18)
    o = [prim("sphere", (0, 0, 0.75), (0.28, 0.22, 0.32), rot=(0.6, 0, 0), material=flesh),
         prim("sphere", (0, -0.25, 1.0), (0.13, 0.14, 0.14), material=flesh)]
    for s in (-1, 1):
        o.append(limb((s * 0.2, -0.05, 0.85), (s * 0.3, -0.45, 0.35), 0.05, flesh))
        o.append(limb((s * 0.12, 0.05, 0.5), (s * 0.18, 0, 0.0), 0.06, flesh))
        o.append(prim("ico", (s * 0.05, -0.37, 1.02), (0.022, 0.022, 0.022), material=mat("eye", "#c8ff60", 0.2, emit="#b0ff40", emit_strength=25), subdivisions=1))
    parent_all(o, root)
    return root


def enemy_brute(loc, rot):
    root = group("brute", loc, rot, 1.25)
    iron = mat("iron", "#4a4a52", 0.35, 0.9, noise=0.3)
    o = [prim("cube", (0, 0, 0.95), (0.36, 0.26, 0.42), material=iron, bevel=0.06),
         prim("sphere", (0, -0.05, 1.5), (0.16, 0.17, 0.16), material=iron)]
    for s in (-1, 1):
        o.append(limb((s * 0.18, 0, 0.6), (s * 0.2, 0, 0.0), 0.11, iron))
        o.append(prim("cone", (s * 0.4, 0, 1.33), (0.1, 0.1, 0.2), rot=(0, s * -0.8, 0), material=mat("spike", "#2a2a30", 0.4, 0.8)))
    o.append(prim("cube", (0.15, -0.38, 0.9), (0.42, 0.06, 0.55), material=mat("towershield", "#3a2a2a", 0.5, 0.6, noise=0.3), bevel=0.05))
    o.append(prim("cube", (0, -0.2, 1.5), (0.1, 0.03, 0.02), material=mat("slit", "#ff3a20", 0.2, emit="#ff2a10", emit_strength=20)))
    parent_all(o, root)
    return root


def enemy_wraith(loc, rot):
    root = group("wraith", loc, rot, 1.0)
    shroud = mat("shroud", "#2a3440", 0.9, noise=0.3, alpha=0.9)
    o = [cape(Vector((0, 0, 1.75)), 1.3, 0.55, shroud, sway=0.35),
         prim("sphere", (0, -0.04, 1.65), (0.15, 0.15, 0.17), material=mat("skull", "#c8c4b0", 0.6))]
    for s in (-1, 1):
        o.append(prim("ico", (s * 0.05, -0.17, 1.66), (0.025, 0.025, 0.025), material=mat("weye", "#80e0ff", 0.2, emit="#70d8ff", emit_strength=30), subdivisions=1))
    root.location.z += 0.35                 # hovers
    parent_all(o, root)
    return root


def enemy_cultist(loc, rot):
    p = {"cloth": "#2a1830", "armor": "#2a1830", "trim": "#8a2a8a", "hand_r": (0.3, -0.3, 1.35), "hand_l": (-0.3, -0.2, 1.0)}
    root, parts, hr, hl, head, m = humanoid("cultist", loc, rot, p, build=0.95)
    o = []
    bpy.ops.mesh.primitive_cone_add(vertices=20, radius1=0.4, radius2=0.18, depth=0.95, location=(0, 0, 0.47))
    robe = bpy.context.active_object
    robe.data.materials.append(mat("crobe2", "#24142a", 0.9, noise=0.3))
    o.append(robe)
    o.append(prim("cone", head + Vector((0, 0.04, 0.05)), (0.16, 0.18, 0.3), rot=(0.2, 0, 0), material=mat("chood", "#1a0e20", 0.9), vertices=16))
    o.append(prim("ico", hr + Vector((0, 0, 0.12)), (0.1, 0.1, 0.1), material=mat("voidorb", "#b040ff", 0.2, emit="#a030ff", emit_strength=18), subdivisions=2))
    parent_all(o, root)
    return root


def boss_colossus(loc, rot):
    """Molten obsidian colossus: ~4.2 m, horns, cracked emissive veins, siege fists."""
    root = group("boss", loc, rot, 1.0)
    rock = mat("obsidian", "#1a1418", 0.45, 0.2, emit="#ff4a10", emit_strength=0.0, noise=0.5, noise_scale=5)
    veins = mat("magma", "#ff6a20", 0.3, emit="#ff4a10", emit_strength=14)
    o = []
    torso = prim("ico", (0, 0, 2.6), (1.0, 0.75, 1.15), material=rock, subdivisions=2, smooth=False)
    d = torso.modifiers.new("disp", "DISPLACE")
    tex = bpy.data.textures.new("bossnoise", "VORONOI")
    tex.noise_scale = 0.5
    d.texture, d.strength = tex, 0.25
    o.append(torso)
    o.append(prim("ico", (0, -0.5, 3.75), (0.45, 0.42, 0.42), material=rock, subdivisions=2, smooth=False))
    for s in (-1, 1):
        o.append(prim("cone", (s * 0.45, -0.4, 4.25), (0.12, 0.12, 0.6), rot=(0.5, s * -0.7, 0), material=mat("bhorn", "#2a2024", 0.5), vertices=10))
        o.append(prim("ico", (s * 0.18, -0.85, 3.8), (0.07, 0.05, 0.05), material=mat("beye", "#ffd060", 0.2, emit="#ffb020", emit_strength=40), subdivisions=1))
        o.append(limb((s * 1.0, 0, 3.1), (s * 1.45, -0.6, 1.7), 0.3, rock))
        o.append(prim("ico", (s * 1.5, -0.7, 1.45), (0.48, 0.45, 0.45), material=rock, subdivisions=2, smooth=False))
        o.append(limb((s * 0.45, 0, 1.6), (s * 0.6, 0, 0.0), 0.36, rock))
        for k in range(3):
            o.append(prim("cone", (s * (0.4 + 0.25 * k), 0.4, 3.3 - 0.3 * k), (0.12, 0.12, 0.45), rot=(-0.6, s * -0.4, 0), material=mat("bspike", "#120e10", 0.5), vertices=8))
    for k in range(9):
        a = k * 0.7
        o.append(limb((math.cos(a) * 0.6, -0.6 - 0.1 * math.sin(a), 2.0 + 0.2 * k), (math.cos(a + 0.6) * 0.75, -0.7, 2.2 + 0.2 * k), 0.035, veins))
    l = bpy.data.lights.new("boss_light", "POINT")
    l.energy, l.color = 900, (1.0, 0.35, 0.1)
    lo = bpy.data.objects.new("boss_light", l)
    link(lo)
    lo.location = (0, -1.6, 2.6)
    o.append(lo)
    parent_all(o, root)
    return root


# ----------------------------------------------------------------------------- environment & VFX

def environment():
    # ground: displaced, dark earth/stone
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
    g = bpy.context.active_object
    g.modifiers.new("sub", "SUBSURF").levels = 4
    g.modifiers["sub"].subdivision_type = "SIMPLE"
    d = g.modifiers.new("disp", "DISPLACE")
    t = bpy.data.textures.new("groundnoise", "CLOUDS")
    t.noise_scale = 1.5
    d.texture, d.strength = t, 0.25
    g.data.materials.append(mat("ground", "#3a342a", 0.95, noise=0.45, noise_scale=3))
    # four lanes (worn paths)
    for ang in (0.15, math.pi / 2 + 0.1, math.pi + 0.15, 3 * math.pi / 2 + 0.1):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(math.cos(ang) * 11, math.sin(ang) * 11, 0.08))
        p = bpy.context.active_object
        p.scale = (14, 1.6, 1)
        p.rotation_euler = (0, 0, ang)
        p.data.materials.append(mat("path", "#4a3e30", 0.95, noise=0.4, noise_scale=8))
    # arena: raised stone platform with ring trim and glowing runes
    prim("cyl", (0, 0, 0.12), (5.2, 5.2, 0.14), material=mat("stone", "#5a5650", 0.8, noise=0.45, noise_scale=4), vertices=64, bevel=0.06)
    prim("torus", (0, 0, 0.27), (5.15, 5.15, 0.5), material=mat("stonetrim", "#6a645a", 0.7, noise=0.3), major_radius=1, minor_radius=0.03)
    prim("torus", (0, 0, 0.27), (2.6, 2.6, 0.3), material=mat("runes", "#5ae0ff", 0.3, emit="#3ad0ff", emit_strength=2), major_radius=1, minor_radius=0.012)
    for k in range(12):
        a = k * math.pi / 6
        prim("cube", (math.cos(a) * 3.6, math.sin(a) * 3.6, 0.27), (0.05, 0.2, 0.005), rot=(0, 0, a),
             material=mat("runes2", "#3ab8e0", 0.3, emit="#2ab0e0", emit_strength=1.2))
    # ruined pillars, rocks, braziers on the arena edge
    for k in range(10):
        a = k * 2 * math.pi / 10 + 0.31
        if any(abs((a - la + math.pi) % (2 * math.pi) - math.pi) < 0.32 for la in (0.15, math.pi / 2 + 0.1, math.pi + 0.15, 3 * math.pi / 2 + 0.1)):
            continue
        r = 7.0 + RNG.uniform(-0.3, 0.6)
        h = RNG.uniform(1.4, 3.2)
        prim("cyl", (math.cos(a) * r, math.sin(a) * r, h / 2), (0.42, 0.42, h / 2), material=mat("pillar", "#6a6258", 0.8, noise=0.4), vertices=12, bevel=0.04)
        prim("cube", (math.cos(a) * r, math.sin(a) * r, h + 0.1), (0.55, 0.55, 0.12), rot=(0, RNG.uniform(-0.2, 0.2), a), material=mat("pillar", "#6a6258", 0.8, noise=0.4), bevel=0.03)
    for k in range(40):
        a, r = RNG.uniform(0, 2 * math.pi), RNG.uniform(6, 16)
        s = RNG.uniform(0.2, 0.7)
        rk = prim("ico", (math.cos(a) * r, math.sin(a) * r, s * 0.3), (s, s * 0.8, s * 0.6), material=mat("rock", "#3a3630", 0.85, noise=0.4), subdivisions=1, smooth=False)
        rk.rotation_euler = (RNG.uniform(0, 1), RNG.uniform(0, 1), RNG.uniform(0, 3))
    for a in (0.8, 2.4, 3.9, 5.5):
        x, y = math.cos(a) * 5.6, math.sin(a) * 5.6
        prim("cyl", (x, y, 0.5), (0.18, 0.18, 0.5), material=mat("brazier", "#2a2420", 0.4, 0.8), vertices=10)
        prim("ico", (x, y, 1.12), (0.18, 0.18, 0.25), material=mat("fire", "#ffb040", 0.2, emit="#ff8a20", emit_strength=25), subdivisions=2)
        l = bpy.data.lights.new("brazier", "POINT")
        l.energy, l.color, l.shadow_soft_size = 220, (1.0, 0.55, 0.2), 0.3
        lo = bpy.data.objects.new("brazier", l)
        link(lo)
        lo.location = (x, y, 1.5)
    # dead trees at the far edges
    for k in range(7):
        a, r = RNG.uniform(0, 2 * math.pi), RNG.uniform(10, 15)
        base = Vector((math.cos(a) * r, math.sin(a) * r, 0))
        bark = mat("bark", "#2a221c", 0.9, noise=0.4)
        limb(base, base + Vector((0.2, 0.1, 3.2)), 0.22, bark)
        for j in range(4):
            st = base + Vector((0.1, 0.05, 1.6 + j * 0.45))
            limb(st, st + Vector((RNG.uniform(-1.3, 1.3), RNG.uniform(-1.3, 1.3), RNG.uniform(0.4, 1.0))), 0.07, bark)


def crystal():
    glass = mat("crystal", "#5ad8ff", 0.08, 0.0, emit="#1aa8e8", emit_strength=1.4, noise=0.35, noise_scale=2.5)
    bm = bmesh.new()
    rings = [(0.25, 0.0), (0.6, 0.55), (2.3, 0.75), (3.5, 0.0)]
    loops = []
    for z, r in rings:
        if r == 0:
            loops.append([bm.verts.new((0, 0, z))])
        else:
            loops.append([bm.verts.new((r * math.cos(i * math.pi / 3 + 0.3), r * math.sin(i * math.pi / 3 + 0.3), z)) for i in range(6)])
    for a, b in zip(loops, loops[1:]):
        n = 6
        if len(a) == 1:
            for i in range(n):
                bm.faces.new((a[0], b[(i + 1) % n], b[i]))
        elif len(b) == 1:
            for i in range(n):
                bm.faces.new((a[i], a[(i + 1) % n], b[0]))
        else:
            for i in range(n):
                bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    me = bpy.data.meshes.new("crystal")
    bm.to_mesh(me)
    ob = bpy.data.objects.new("crystal", me)
    link(ob)
    ob.location = (0, 0, 0.6)
    ob.data.materials.append(glass)
    # pedestal + orbiting shards
    prim("cyl", (0, 0, 0.45), (1.1, 1.1, 0.2), material=mat("altar", "#4a4640", 0.6, 0.3, noise=0.3), vertices=8, bevel=0.05)
    for k in range(5):
        a = k * 2 * math.pi / 5
        sh = prim("cone", (math.cos(a) * 1.5, math.sin(a) * 1.5, 1.6 + 0.4 * math.sin(a * 2)), (0.12, 0.12, 0.35), rot=(0.3, 0.2, a),
                  material=glass, vertices=6, smooth=False)
    l = bpy.data.lights.new("crystal_light", "POINT")
    l.energy, l.color, l.shadow_soft_size = 1800, (0.35, 0.85, 1.0), 0.6
    lo = bpy.data.objects.new("crystal_light", l)
    link(lo)
    lo.location = (0, 0, 2.2)


def vfx_and_telegraph(boss_pos):
    # boss telegraph: red ring decal on the ground (highest VFX priority)
    prim("torus", (boss_pos[0] * 0.75, boss_pos[1] - 2.3, 0.3), (1.25, 1.25, 0.2), material=mat("telegraph", "#ff2a2a", 0.3, emit="#ff1a1a", emit_strength=10), major_radius=1, minor_radius=0.04)
    bpy.ops.mesh.primitive_circle_add(vertices=48, radius=1.25, fill_type="NGON", location=(boss_pos[0] * 0.75, boss_pos[1] - 2.3, 0.29))
    disc = bpy.context.active_object
    disc.data.materials.append(mat("telefill", "#ff2020", 0.5, emit="#ff1010", emit_strength=0.5, alpha=0.22))
    # reaction: fire + lightning burst on an enemy cluster (medium priority)
    for k in range(14):
        p = Vector((5.6 + RNG.uniform(-0.6, 0.6), -3.0 + RNG.uniform(-0.6, 0.6), 0.8 + RNG.uniform(0, 1.2)))
        prim("ico", p, (0.12, 0.12, 0.12), material=mat("ember", "#ffb040", 0.2, emit="#ff7a20", emit_strength=30), subdivisions=1)
    pts = [Vector((4.2, -1.8, 2.4))]
    for k in range(7):
        pts.append(pts[-1] + Vector((0.3 + RNG.uniform(-0.1, 0.2), -0.2 + RNG.uniform(-0.3, 0.3), -0.3 + RNG.uniform(-0.2, 0.2))))
    for a, b in zip(pts, pts[1:]):
        limb(a, b, 0.025, mat("bolt", "#e0d0ff", 0.2, emit="#b090ff", emit_strength=40))
    # ice shards (frost reaction) on the west lane
    for k in range(7):
        a = k * 0.9
        prim("cone", (-6.5 + math.cos(a) * 0.5, 0.6 + math.sin(a) * 0.5, 0.4), (0.1, 0.1, 0.55), rot=(math.cos(a) * 0.5, math.sin(a) * 0.5, 0),
             material=mat("ice", "#bff4ff", 0.1, emit="#7ad8ff", emit_strength=3), vertices=5, smooth=False)


def lights_and_world(look):
    sc = bpy.context.scene
    world = bpy.data.worlds.new("w")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    if look == "painterly":
        bg.inputs[0].default_value, bg.inputs[1].default_value = srgb("#28304a"), 0.55
    else:
        bg.inputs[0].default_value, bg.inputs[1].default_value = srgb("#1a2238"), 0.9
    key = bpy.data.lights.new("moon", "SUN")
    key.energy = 5.0 if look != "painterly" else 3.6
    key.color = (0.55, 0.65, 1.0) if look != "painterly" else (1.0, 0.62, 0.38)
    key.angle = math.radians(8)
    ko = bpy.data.objects.new("moon", key)
    link(ko)
    ko.rotation_euler = Euler((math.radians(52 if look != "painterly" else 68), 0, math.radians(-35 if look != "painterly" else -60)))
    rim = bpy.data.lights.new("rim", "SUN")
    rim.energy, rim.color = (4.5, (0.75, 0.6, 1.0)) if look != "painterly" else (2.5, (0.55, 0.7, 1.0))
    ro = bpy.data.objects.new("rim", rim)
    link(ro)
    ro.rotation_euler = Euler((math.radians(70), 0, math.radians(160)))
    if look == "mythic":
        vol = world.node_tree.nodes.new("ShaderNodeVolumePrincipled")
        vol.inputs["Density"].default_value = 0.004
        vol.inputs["Color"].default_value = srgb("#7a8aa8")
        world.node_tree.links.new(vol.outputs[0], world.node_tree.nodes["World Output"].inputs["Volume"])


def camera():
    cam = bpy.data.cameras.new("cam")
    cam.type = "ORTHO"
    cam.ortho_scale = 19.0              # 3/4 view framed on the arena + lanes; heroes ~12% of screen height like the game
    co = bpy.data.objects.new("cam", cam)
    link(co)
    elev = math.radians(38)
    target = Vector((0, 2.4, 1.0))
    co.location = target + Vector((0, -math.cos(elev) * 40, math.sin(elev) * 40))
    co.rotation_euler = Euler((math.pi / 2 - elev, 0, 0))
    bpy.context.scene.camera = co
    return co


def build_scene(look):
    environment()
    crystal()
    heroes = [(hero_knight, (1.9, -1.6, 0.27), 0.4), (hero_mage, (-2.6, -1.9, 0.27), -0.3), (hero_ranger, (-3.4, 1.4, 0.27), -1.2),
              (hero_cleric, (-0.6, -3.0, 0.27), 0.1), (hero_rogue, (3.4, 1.0, 0.27), 1.0), (hero_berserker, (0.7, 3.2, 0.27), 2.8)]
    ring_cols = ["#4a8aff", "#ff7a2a", "#5adf6a", "#ffe08a", "#c070ff", "#ff4a3a"]
    for (fn, loc, rot), col in zip(heroes, ring_cols):
        fn(loc, rot).scale = (1.2, 1.2, 1.2)       # gameplay exaggeration: readable at mobile scale
        prim("torus", (loc[0], loc[1], loc[2] + 0.02), (0.55, 0.55, 0.3), material=mat("heroring_" + col, col, 0.4, emit=col, emit_strength=2.5), major_radius=1, minor_radius=0.04)
    enemies = [(enemy_ghoul, (6.2, -2.6, 0.05), 1.9), (enemy_ghoul, (5.4, -3.6, 0.05), 1.6), (enemy_ghoul, (7.0, -3.3, 0.05), 1.7),
               (enemy_brute, (-7.4, 0.9, 0.05), -1.5), (enemy_wraith, (-2.4, 6.2, 0.05), 3.0), (enemy_wraith, (-3.6, 7.0, 0.05), 3.1),
               (enemy_cultist, (8.0, 2.3, 0.05), 1.3)]
    for fn, loc, rot in enemies:
        r = fn(loc, rot)
        r.scale = tuple(v * 1.15 for v in r.scale)
    boss_pos = (1.8, 6.4, 0.0)
    boss_colossus(boss_pos, 3.3).scale = (0.85, 0.85, 0.85)
    vfx_and_telegraph(boss_pos)
    lights_and_world(look)
    camera()


# ----------------------------------------------------------------------------- render settings per look

def setup_render(look):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = False
    sc.cycles.seed = 7
    sc.cycles.max_bounces = 4
    sc.cycles.sample_clamp_indirect = 2.0   # no denoiser in this build: clamp fireflies instead
    sc.cycles.sample_clamp_direct = 8.0
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    for attr in ("use_stamp_date", "use_stamp_time", "use_stamp_render_time"):
        setattr(sc.render, attr, False)
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.exposure = {"mythic": 1.2, "painterly": 0.5, "pixel": 1.3}[look]
    sc.view_settings.look = {"mythic": "AgX - High Contrast", "painterly": "AgX - Base Contrast", "pixel": "AgX - Punchy"}[look]
    if look == "pixel":
        sc.render.filter_size = 0.01      # crisp pixels, no AA blur
        sc.view_layers[0].use_pass_z = True
    if look in ("painterly", "pixel"):
        sc.use_nodes = True
        nt = sc.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        rl = nt.nodes.new("CompositorNodeRLayers")
        comp = nt.nodes.new("CompositorNodeComposite")
        if look == "painterly":
            k = nt.nodes.new("CompositorNodeKuwahara")
            k.variation = "ANISOTROPIC"
            k.size = 7 if RES[0] >= 1280 else 4
            nt.links.new(rl.outputs["Image"], k.inputs["Image"])
            nt.links.new(k.outputs["Image"], comp.inputs["Image"])
        else:
            # depth-discontinuity outline: Sobel on normalised Z, thresholded, multiplied over the image
            norm = nt.nodes.new("CompositorNodeNormalize")
            sob = nt.nodes.new("CompositorNodeFilter")
            sob.filter_type = "SOBEL"
            ramp = nt.nodes.new("CompositorNodeValToRGB")
            ramp.color_ramp.elements[0].position = 0.0
            ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
            ramp.color_ramp.elements[1].position = 0.06
            ramp.color_ramp.elements[1].color = (0.08, 0.06, 0.1, 1)
            ramp.color_ramp.interpolation = "CONSTANT"
            mul = nt.nodes.new("CompositorNodeMixRGB")
            mul.blend_type = "MULTIPLY"
            nt.links.new(rl.outputs["Depth"], norm.inputs[0])
            nt.links.new(norm.outputs[0], sob.inputs["Image"])
            nt.links.new(sob.outputs[0], ramp.inputs[0])
            nt.links.new(rl.outputs["Image"], mul.inputs[1])
            nt.links.new(ramp.outputs[0], mul.inputs[2])
            nt.links.new(mul.outputs[0], comp.inputs["Image"])


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    build_scene(LOOK)
    setup_render(LOOK)
    bpy.context.scene.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
    print("AW_BENCH " + OUT)


main()
