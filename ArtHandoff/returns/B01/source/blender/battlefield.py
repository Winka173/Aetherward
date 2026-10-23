"""B01 Warded Sanctum: exact arena paths, eight source layers. Blender 4.5."""
import bpy, math, random, json, re, sys
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REPO=ROOT.parents[2];random.seed(101)
arena=json.loads(re.sub(r'//[^\n]*','',(REPO/'Assets/_Aetherward/Resources/Content/arena.json').read_text()))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='OPTIX'
sc.cycles.device='GPU';sc.render.film_transparent=True;sc.render.resolution_x=2400;sc.render.resolution_y=1360;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.view_settings.view_transform='AgX'
names=['01_base_terrain','02_path_traffic_wear','03_ruins_structure','04_cliffs_height_planes','05_cracks_decals','06_ambient_particles_fog','07_static_props','08_occlusion_shadows']
cols=[]
for name in names:c=bpy.data.collections.new(name);sc.collection.children.link(c);cols.append(c)
active=cols[0]
def put(o,name,mat):
    o.name=name
    for c in list(o.users_collection):c.objects.unlink(o)
    active.objects.link(o)
    if mat:o.data.materials.append(mat)
    return o
def lin(h):
    v=[int(h[i:i+2],16)/255 for i in (1,3,5)];return tuple(x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4 for x in v)
def material(name,a,b,scale=2,metal=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=.82
    tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=2;tex.inputs['Roughness'].default_value=.7
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*lin(a),1);ramp.color_ramp.elements[1].color=(*lin(b),1);l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
    tc=n.new('ShaderNodeTexCoord');l.new(tc.outputs['Object'],tex.inputs['Vector'])
    micro=n.new('ShaderNodeTexNoise');micro.inputs['Scale'].default_value=15;micro.inputs['Detail'].default_value=2;l.new(tc.outputs['Object'],micro.inputs['Vector'])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.42;bump.inputs['Distance'].default_value=.045;l.new(micro.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal']);return m
basalt=material('basalt broad brush masses','#1d1f24','#3b3a3d',1.2)
road=material('worn flagstone','#3b3a3d','#625c55',3.5)
stone=material('carved weathered stone','#35383e','#625c55',5)
dark=material('cliff fracture faces','#171b24','#3b3a3d',2)
moss=material('desaturated teal lichen','#2e4a47','#3f5f5a',5)
bronze=material('cold aged bronze','#403b35','#716752',3,.5)
wine=material('quiet rift scar','#301f2b','#6b2734',4)
def cube(name,loc,size,mat,bevel=.04):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);put(o,name,mat)
    if bevel:mod=o.modifiers.new('chipped edge','BEVEL');mod.width=bevel;mod.segments=1;o.modifiers.new('weighted normals','WEIGHTED_NORMAL')
    return o
def cyl(name,x,y,r,depth,z,mat,verts=64):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=(x,y,z));return put(bpy.context.object,name,mat)
def line(name,pts,mat,r=.02):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=1;sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
    for p,v in zip(sp.points,pts):p.co=(*v,1)
    ob=bpy.data.objects.new(name,cu);active.objects.link(ob);ob.data.materials.append(mat);return ob
def g(x,y,z=0):return (x,y/.62,z)
def distance_lane(x,y):
    pp=Vector((x,y));best=999
    for lane in arena['lanes']:
        for a,b in zip(lane['points'],lane['points'][1:]):
            aa=Vector(a);bb=Vector(b);v=bb-aa;t=max(0,min(1,(pp-aa).dot(v)/v.length_squared));best=min(best,(pp-aa-v*t).length)
    return best
cube('continuous basalt plateau',(0,0,-.22),(31,29,.4),basalt)
for i in range(100):
    x=random.uniform(-15,15);y=random.uniform(-8.5,8.5)
    if distance_lane(x,y)>1.2 and x*x+(y/.62)**2>30:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=random.uniform(.25,.7),location=g(x,y,-.01));o=put(bpy.context.object,'low lichen stone',moss if i%3==0 else basalt);o.scale=(1,1,.12)
active=cols[1]
for lane in arena['lanes']:
    for a,b in zip(lane['points'],lane['points'][1:]):
        aa=Vector(g(*a));bb=Vector(g(*b));v=bb-aa;length=v.length;forward=v.normalized();side=Vector((-forward.y,forward.x,0));count=int(length/.60)+1
        for k in range(count):
            t=(k+.5)/count;c=aa+v*t
            if c.x*c.x+c.y*c.y<22:continue
            for j in [-1,0,1]:
                if random.random()<.07:continue
                loc=c+side*(j*.39+random.uniform(-.04,.04));loc.z=.012+random.uniform(-.008,.008)
                o=cube('processional road flagstone',loc,(random.uniform(.35,.43),length/count*.93,.055),road,.025);o.rotation_euler.z=math.atan2(v.y,v.x)-math.pi/2
            if k%2==0:
                for j in [-1,1]:
                    loc=c+side*(j*.82);loc.z=.03;o=cube('broken road edge',loc,(.18,.43,.11),stone,.035);o.rotation_euler.z=math.atan2(v.y,v.x)-math.pi/2
active=cols[2]
cyl('outer worn dais step',0,0,5.65,.06,-.025,stone,96);cyl('inner dais surface',0,0,5.38,.04,.005,road,96)
for radius in [1.08,2.65,4.95,5.42]:
    pts=[(math.cos(i*math.tau/128)*radius,math.sin(i*math.tau/128)*radius,.035) for i in range(129)];line('concentric engraved dark groove',pts,dark,.026)
for i in range(24):
    a=math.tau*i/24;line('radial carved joint',[(math.cos(a)*2.7,math.sin(a)*2.7,.034),(math.cos(a)*5.32,math.sin(a)*5.32,.034)],dark,.018)
# Node sockets are shallow geometry at exact arena coordinates; runtime node sprites overlay these.
for i,(x,y) in enumerate(arena['nodes']):
    pts=[(x+math.cos(k*math.tau/48)*.58,y/.62+math.sin(k*math.tau/48)*.58,.045) for k in range(49)];line('node socket '+str(i),pts,bronze,.025)
for x,y in [(-7,3.9),(6.5,-3.5),(-9,3.1),(10,-3.8)]:
    if distance_lane(x,y)>1.5:
        cyl('broken pillar base',x,y/.62,.60,.20,.10,stone,8);cyl('broken pillar shaft',x,y/.62,.30,random.uniform(.5,1.6),.55,stone,8)
# Fallen arch segments in outer northwest, clear of ingress.
for i in range(7):cube('fallen arch voussoir',g(-8.5+i*.36,4.8+math.sin(i*.4)*.25,.20),(.4,.65,.4),stone,.08)
active=cols[3]
for i in range(44):
    x=-15.2+i*.71;y=8.4+random.uniform(-.25,.25)
    for sign in [-1,1]:
        if distance_lane(x,sign*y)<1.5:continue
        o=cube('outer cliff layered face',g(x,sign*y,-.7),(random.uniform(.7,1.2),2.2,1.6),dark,.14);o.rotation_euler.z=random.uniform(-.2,.2)
active=cols[4]
for lane in arena['lanes']:
    aa=lane['points'][0];bb=lane['points'][1]
    for side in [-1,1]:
        pts=[g(aa[0]*(1-t)+bb[0]*t+side*.55+random.uniform(-.13,.13),aa[1]*(1-t)+bb[1]*t+random.uniform(-.1,.1),.07) for t in [0,.15,.3,.5,.7]];line('muted wine rift fracture',pts,wine,.018)
for i in range(40):
    a=math.tau*i/40;r=4.7;c=Vector((math.cos(a)*r,math.sin(a)*r,.047));t=Vector((-math.sin(a),math.cos(a),0));line('abstract dais glyph notch',[c-t*.06,c+Vector((0,0,.005)),c+t*.07+Vector((-.05,.04,0))],bronze,.018)
def haze_material(name,color,alpha):
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');trans=n.new('ShaderNodeBsdfTransparent');emit=n.new('ShaderNodeEmission');emit.inputs[0].default_value=(*lin(color),1);mix=n.new('ShaderNodeMixShader');tc=n.new('ShaderNodeTexCoord');dist=n.new('ShaderNodeVectorMath');dist.operation='DISTANCE';dist.inputs[1].default_value=(.5,.5,0);l.new(tc.outputs['Generated'],dist.inputs[0]);r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.05;r.color_ramp.elements[0].color=(alpha,alpha,alpha,1);r.color_ramp.elements[1].position=.5;r.color_ramp.elements[1].color=(0,0,0,1);l.new(dist.outputs['Value'],r.inputs[0]);l.new(r.outputs[0],mix.inputs[0]);l.new(trans.outputs[0],mix.inputs[1]);l.new(emit.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs[0]);return m
def plane(name,x,y,z,sx,sy,material):
    bpy.ops.mesh.primitive_plane_add(size=1,location=(x,y,z));o=put(bpy.context.object,name,material);o.scale=(sx,sy,1);return o
active=cols[5];fog=haze_material('low cold outer fog','#779398',.12)
fog.node_tree.nodes.get('Vector Math').inputs[1].default_value=(.5,.5,.5)
for x,y in [(-11,4),(10,-5),(-12,-5),(11,7)]:plane('outer fog patch',*g(x,y,.09),5,2.5,fog)
active=cols[6]
for x,y in [(-6.4,3.9),(6.4,-3.9)]:
    cyl('cold brazier foot',x,y/.62,.35,.18,.09,stone,8);cyl('cold brazier stem',x,y/.62,.12,.6,.45,bronze,8);cyl('cold brazier bowl',x,y/.62,.34,.15,.82,bronze,8)
    flame=material('restrained teal coal','#294e50','#4a8c91',2);p=flame.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(*lin('#468c93'),1);p.inputs['Emission Strength'].default_value=.5
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.18,location=g(x,y,.98));o=put(bpy.context.object,'small cold fire',flame);o.scale=(.65,.65,1.6)
for x,y in [(-11,2.7),(10,-2.8),(-5,6.6)]:
    if distance_lane(x,y)<1.6:continue
    base=Vector(g(x,y));line('dead ivy tree trunk',[base,base+Vector((.14,0,.8)),base+Vector((-.08,0,1.6))],dark,.08)
    for j in [-1,1]:line('dead bare branch',[base+Vector((.08,0,.7)),base+Vector((j*.4,.05,1.2)),base+Vector((j*.62,.1,1.45))],dark,.035)
active=cols[7];ao=haze_material('soft contact AO','#10151e',.40);pool=haze_material('small crystal cyan pool','#7399ad',.20)
for hm in [ao,pool]:hm.node_tree.nodes.get('Vector Math').inputs[1].default_value=(.5,.5,.5)
for x,y in [(-7,3.9),(6.5,-3.5),(-9,3.1),(10,-3.8),(-6.4,3.9),(6.4,-3.9)]:plane('prop contact shadow',*g(x+.25,y-.13,.06),1.6,1.1,ao)
plane('restrained crystal pool',0,-.55/.62,.065,2.1,2.1,pool)
world=bpy.data.worlds.new('night ambient');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(*lin('#16233a'),1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;sc.world=world
for loc,col,power,size in [((-8,-10,18),'#ffe9d0',6500,15),((9,8,12),'#9fe8ff',2400,12)]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.color=lin(col);o.data.shape='DISK';o.data.size=size;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
theta=math.asin(.62);bpy.ops.object.camera_add(location=(0,-math.cos(theta)*40,math.sin(theta)*40));cam=bpy.context.object;cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=30;sc.camera=cam
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/blender/battlefield.blend'))
out=ROOT/'source/battlefield/renders';out.mkdir(parents=True,exist_ok=True)
for c in cols:
    if 'haze_only' in sys.argv and c not in [cols[5],cols[7]]:continue
    if 'cliffs_only' in sys.argv and c!=cols[3]:continue
    for other in cols:other.hide_render=other!=c
    sc.render.filepath=str(out/(c.name+'.png'));bpy.ops.render.render(write_still=True)
