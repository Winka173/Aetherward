"""Clay pose-reference mannequins for the art specialist — Blender 4.5 + MPFB (MakeHuman) extension, headless.

  blender -b --python Tools/ArtPipeline/blender/pose_mannequins.py -- --out ArtCache/Poses [--only guardian_idle] [--probe]

Renders, at the game camera (orthographic, 38.3 deg elevation, body turned 25 deg toward screen-right, feet on the
pivot row 0.07 of the canvas, figure inside the 0.1/0.2/0.8 icon box), a grey clay human holding a clay prop in each key
pose the game uses (idle / attack / cast / downed) for each body build and weapon kind. Codex attaches these as pose and
camera references to its image generation so every hero shares one view, scale and ground contact.
Output: <out>/<build>_<weapon>_<pose>.png, 800x800 RGBA (the 2x master of the art canvas).
"""
import math
import os
import sys

import bpy
from mathutils import Euler, Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(ARGS[ARGS.index("--out") + 1] if "--out" in ARGS else "ArtCache/Poses")
ONLY = ARGS[ARGS.index("--only") + 1] if "--only" in ARGS else None
PROBE = "--probe" in ARGS
SIN = 0.62
ELEV = math.asin(SIN)
os.makedirs(OUT, exist_ok=True)

from bl_ext.blender_org.mpfb.services.humanservice import HumanService  # noqa: E402

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
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
sc.cycles.samples = 48
sc.cycles.use_denoising = True
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = 800
sc.render.image_settings.color_mode = "RGBA"

basemesh = HumanService.create_human()
rig = HumanService.add_builtin_rig(basemesh, "default")
clay = bpy.data.materials.new("Clay")
clay.use_nodes = True
clay.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.55, 0.55, 0.57, 1)
clay.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.6
basemesh.data.materials.clear()
basemesh.data.materials.append(clay)
for m in basemesh.modifiers:
    if m.type == "MASK":
        pass                       # keep MPFB's helper masks: they hide the clothes-fitting helper geometry

# measure the rest height (feet on z = 0)
bpy.context.view_layer.update()
zs = [(basemesh.matrix_world @ v.co).z for v in basemesh.data.vertices]
HEIGHT = max(zs) - min(zs)
rig.location.z -= min(zs)

# camera: head top at ~0.62 of the 800 canvas above the feet row (0.07)
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = "ORTHO"
screen_h = HEIGHT * math.cos(ELEV)
cam.data.ortho_scale = screen_h / 0.62
d = Vector((0, math.cos(ELEV), -SIN))
up = Vector((0, SIN, math.cos(ELEV)))
cam.location = -d * 40 + up * (cam.data.ortho_scale * (0.5 - 0.07))
cam.rotation_euler = (math.pi / 2 - ELEV, 0, 0)
sun = bpy.data.objects.new("Key", bpy.data.lights.new("Key", "SUN"))
sun.data.energy = 3.0
sun.rotation_euler = Vector((0.55, 0.62, -0.75)).normalized().to_track_quat("-Z", "Y").to_euler()
sc.collection.objects.link(sun)
rim = bpy.data.objects.new("Rim", bpy.data.lights.new("Rim", "AREA"))
rim.data.energy = 400
rim.data.size = 3
rim.location = (2.5, 3.0, 2.5)
rim.rotation_euler = (-rim.location).to_track_quat("-Z", "Y").to_euler()
sc.collection.objects.link(rim)
world = bpy.data.worlds.new("W")
sc.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[1].default_value = 0.6
rig.rotation_euler = (0, 0, math.radians(25))   # body turned toward screen-right


def pose(rotations):
    for pb in rig.pose.bones:
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (0, 0, 0)
        pb.location = (0, 0, 0)
    for name, deg in rotations.items():
        if name in rig.pose.bones:
            rig.pose.bones[name].rotation_euler = Euler([math.radians(v) for v in deg])
    bpy.context.view_layer.update()


def render(name):
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("POSE", name)


if PROBE:
    # one render per axis for the arm, to read this rig's bone conventions from the images
    for ax in range(3):
        for sgn in (1, -1):
            r = [0, 0, 0]
            r[ax] = 60 * sgn
            pose({"upperarm01.L": r, "upperarm01.R": r})
            render("probe_arm_%s%s" % ("xyz"[ax], "+" if sgn > 0 else "-"))
    pose({})
    render("probe_rest")
    sys.exit(0)

# ------------------------------------------------------------------------------------------------ builds, props, poses
BUILDS = {
    "slim": {"gender": 0.5, "muscle": 0.55, "weight": 0.4, "proportions": 1.0, "height": 0.6},
    "heavy": {"gender": 0.85, "muscle": 0.95, "weight": 0.75, "proportions": 1.0, "height": 0.7},
}
# rotations in degrees per bone (MPFB default rig; .L = the figure's left = the arm toward screen-right/front)
POSES = {
    "idle": {"upperarm01.L": (0, 0, -28), "upperarm01.R": (0, 0, 28), "lowerarm01.L": (0, 0, -10), "lowerarm01.R": (0, 0, 10)},
    "attack": {"spine03": (0, 0, -15), "upperarm01.L": (35, 0, 55), "lowerarm01.L": (0, 0, 5), "upperarm01.R": (-20, 0, 30),
               "upperleg01.L": (-25, 0, 0), "lowerleg01.L": (15, 0, 0), "upperleg01.R": (15, 0, 0)},
    "cast": {"upperarm01.L": (15, 0, 105), "upperarm01.R": (0, 0, -70), "lowerarm01.L": (0, 0, 15), "lowerarm01.R": (0, 0, -25),
             "spine03": (-8, 0, 0)},
    "downed": {"spine03": (25, 0, 0), "spine02": (10, 0, 0), "neck01": (20, 0, 0),
               "upperleg01.L": (-70, 0, 0), "lowerleg01.L": (75, 0, 0), "upperleg01.R": (15, 0, 0), "lowerleg01.R": (100, 0, 0),
               "upperarm01.L": (25, 0, -20), "upperarm01.R": (25, 0, 20)},
}
DOWNED_DROP = 0.27   # the kneel lowers the pelvis (fraction of the body height)


def set_build(name):
    """Replace the human with one created from this build's macros (gender/muscle/weight/proportions/height)."""
    global basemesh, rig, zs, HEIGHT
    from bl_ext.blender_org.mpfb.services.targetservice import TargetService
    for o in (basemesh, rig):
        bpy.data.objects.remove(o, do_unlink=True)
    macro = TargetService.get_default_macro_info_dict()
    macro.update(BUILDS[name])
    basemesh = HumanService.create_human(macro_detail_dict=macro)
    rig = HumanService.add_builtin_rig(basemesh, "default")
    basemesh.data.materials.clear()
    basemesh.data.materials.append(clay)
    bpy.context.view_layer.update()
    zs = [(basemesh.matrix_world @ v.co).z for v in basemesh.data.vertices]
    rig.location.z -= min(zs)
    rig.rotation_euler = (0, 0, math.radians(25))


def make_prop(kind):
    """Clay prop parented to the front hand: staff, bow, sword, hammer, shield."""
    objs = []
    hand = rig.pose.bones.get("wrist.L")
    if kind == "staff":
        bpy.ops.mesh.primitive_cylinder_add(radius=0.018, depth=1.7)
    elif kind == "sword":
        bpy.ops.mesh.primitive_cube_add(size=1)
        bpy.context.object.scale = (0.03, 0.008, 0.55)
    elif kind == "hammer":
        bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=1.1)
        objs.append(bpy.context.object)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.55))
        bpy.context.object.scale = (0.12, 0.22, 0.14)
    elif kind == "bow":
        bpy.ops.mesh.primitive_torus_add(major_radius=0.6, minor_radius=0.012, major_segments=48)
        bpy.context.object.scale = (0.35, 1.0, 1.0)
    elif kind == "shield":
        bpy.ops.mesh.primitive_cylinder_add(radius=0.33, depth=0.04, vertices=6)
    else:
        return []
    objs.append(bpy.context.object)
    for o in objs:
        o.data.materials.append(clay)
        o.parent = rig
        o.parent_type = "BONE"
        o.parent_bone = hand.name
        o.location = Vector((0, 0.05, 0)) + o.location
    return objs


KITS = {"slim": ["staff", "bow", "sword"], "heavy": ["hammer", "shield", "sword"]}
for build, kits in KITS.items():
    set_build(build)
    for kit in kits:
        props = make_prop(kit)
        for pname, rot in POSES.items():
            name = "%s_%s_%s" % (build, kit, pname)
            if ONLY and ONLY not in name:
                continue
            pose(rot)
            rig.location.z = -min(zs) - (HEIGHT * DOWNED_DROP if pname == "downed" else 0.0)
            render(name)
        for o in props:
            bpy.data.objects.remove(o, do_unlink=True)
print("POSES DONE", OUT)
