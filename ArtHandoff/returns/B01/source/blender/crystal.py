"""Blender 4.5 headless: registered Crystal states, Cycles OPTIX."""
import bpy, math, random
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
random.seed(101)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
for dev in prefs.devices:dev.use=dev.type=='OPTIX'
scene.cycles.device='GPU';scene.render.film_transparent=True
scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8'
scene.view_settings.view_transform='AgX'
def linear(h):
    v=[int(h[i:i+2],16)/255 for i in (1,3,5)];return tuple(x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4 for x in v)
def mat(name,col,metal=0,emit=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;p=n.get('Principled BSDF');c=linear(col);p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=.38
    p.inputs['Emission Color'].default_value=(*c,1);p.inputs['Emission Strength'].default_value=emit
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=12;noise.inputs['Detail'].default_value=2
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.15;bump.inputs['Distance'].default_value=.025;m.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal']);return m
stone=mat('worn basalt brush planes','#625c55',.25);bronze=mat('aged bronze','#7d6650',.7)
blue=mat('aether blue edge','#2b5cff',.38,.6);cyan=mat('cyan refraction','#8fe3ff',.35,1.4);white=mat('holy white core','#e7faff',.25,2)
for material in [blue,cyan,white]:
    n=material.node_tree.nodes; links=material.node_tree.links;p=n.get('Principled BSDF')
    tc=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');links.new(tc.outputs['Generated'],sep.inputs[0])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.05;ramp.color_ramp.elements[0].color=(*linear('#172b79'),1)
    ramp.color_ramp.elements[1].position=.92;ramp.color_ramp.elements[1].color=(*linear('#eefbff'),1)
    mid=ramp.color_ramp.elements.new(.53);mid.color=(*linear('#58b8ef'),1)
    links.new(sep.outputs['Z'],ramp.inputs[0]);links.new(ramp.outputs[0],p.inputs['Base Color']);links.new(ramp.outputs[0],p.inputs['Emission Color'])
    p.inputs['Coat Weight'].default_value=.8;p.inputs['Coat Roughness'].default_value=.13;p.inputs['Roughness'].default_value=.20
crack=mat('fracture emission','#aeeeff',.1,5);critical=mat('unstable red violet','#ff4a7a',.25,3)
dim=mat('spent crown shard','#344863',.35,.03)
def cylinder(name,r,depth,z,material,vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=(0,0,z));o=bpy.context.object;o.name=name;o.data.materials.append(material)
    bevel=o.modifiers.new('worn bevel','BEVEL');bevel.width=.035;bevel.segments=2;o.modifiers.new('weighted facets','WEIGHTED_NORMAL');return o
cylinder('lower carved twelve-sided foot',.83,.15,.075,stone)
cylinder('bronze collar lower rim',.78,.07,.19,bronze)
cylinder('carved collar',.70,.26,.34,stone)
cylinder('upper collar',.74,.07,.49,bronze)
def shard(name,loc,scale):
    vs=[(0,0,-.55)]+[(math.cos(i*math.tau/6)*.48,math.sin(i*math.tau/6)*.40,-.12+(i%2)*.06) for i in range(6)]+[(math.cos(i*math.tau/6)*.31,math.sin(i*math.tau/6)*.28,.66+(i%2)*.10) for i in range(6)]+[(.07,-.02,1.2)]
    fs=[]
    for i in range(6):j=(i+1)%6;fs.extend([(0,1+j,1+i),(1+i,1+j,7+j),(1+i,7+j,7+i),(7+i,7+j,13)])
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);scene.collection.objects.link(o);o.location=loc;o.scale=scale
    for m in [blue,cyan,white]:me.materials.append(m)
    for p in me.polygons:p.material_index=[0,1,1,2,1,0][p.index%6]
    return o
main=shard('faceted asymmetric relic',(0,0,1.11),(1,1,1.13))
sat=[]
for i,(x,y,z,s) in enumerate([(-.59,.04,1.82,.35),(.55,.10,1.55,.28),(.30,.12,2.37,.22)]):sat.append(shard('restrained crown shard '+str(i),(x,y,z),(s,s,s)))
def line(name,pts,material,r=.008):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=1;sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
    for p,v in zip(sp.points,pts):p.co=(*v,1)
    ob=bpy.data.objects.new(name,cu);scene.collection.objects.link(ob);ob.data.materials.append(material);return ob
glyphs=[]
for i in range(12):
    a=math.tau*i/12;v=Vector((math.cos(a),math.sin(a),0));t=Vector((-math.sin(a),math.cos(a),0));c=v*.706+Vector((0,0,.34))
    glyphs.append(line('abstract collar notch '+str(i),[c-t*.035+Vector((0,0,.055)),c,c+t*.035+Vector((0,0,-.055))],cyan,.012))
fractures=[]
for pts in [[(-.25,-.32,1.95),(-.10,-.39,1.72),(-.19,-.41,1.49),(.02,-.40,1.22),(-.05,-.33,.90)],[(.30,-.29,1.85),(.17,-.37,1.62),(.25,-.38,1.40),(.02,-.40,1.22)]]:fractures.append(line('fracture seam',pts,crack,.012))
world=bpy.data.worlds.new('night ambient');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(*linear('#16233a'),1);world.node_tree.nodes['Background'].inputs[1].default_value=.45;scene.world=world
def area(name,loc,col,power,size):
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.color=linear(col);o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
area('warm upper-left-front',(-3,-4,6),'#ffe9d0',520,4)
area('cool back-right rim',(3,2,4),'#9fe8ff',750,3)
target=Vector((0,0,1.23));theta=math.asin(.62)
bpy.ops.object.camera_add(location=target+Vector((0,-math.cos(theta)*8,math.sin(theta)*8)));cam=bpy.context.object;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=3.35;scene.camera=cam
out=ROOT/'source/masters/World';out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/blender/crystal.blend'))
for state in ['intact','cracked','critical']:
    for f in fractures:f.hide_render=state=='intact'
    for i,g in enumerate(glyphs):g.hide_render=state=='critical' and i%2==0
    for o in [main]+sat:
        for k in range(3):o.data.materials[k]=[blue,cyan,white][k] if state!='critical' else [blue,critical,critical][k]
    sat[0].location.z=1.82 if state=='intact' else (1.67 if state=='cracked' else .72)
    sat[1].location.z=1.55 if state!='critical' else .65
    if state=='critical':
        for o in sat[:2]:
            for k in range(3):o.data.materials[k]=dim
    # Highest crown and pedestal extremities remain fixed for strict pixel registration.
    scene.render.filepath=str(out/f'crystal_{state}_render@2x.png');bpy.ops.render.render(write_still=True)
