"""Run using Blender -b -t 8 --python hardware/renders/render_scene.py -- [hero|exploded|turntable]."""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;CAD=R.parent/'cad';MODE=sys.argv[-1] if sys.argv[-1] in ['hero','exploded','turntable'] else 'hero'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True
scene.cycles.max_bounces=12;scene.cycles.transmission_bounces=8
scene.render.resolution_x=1800;scene.render.resolution_y=1500;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.world.color=(.10,.10,.10);scene.view_settings.view_transform='AgX'
scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='MILLIMETERS';scene.unit_settings.scale_length=1
colors={'graphite':(.022,.03,.048,1),'pearl':(.74,.82,.91,1),'pcb':(.016,.18,.12,1),'darkpcb':(.02,.04,.06,1),'metal':(.5,.58,.68,1),'crystal':(.29,.71,.94,1),'ice':(.62,.87,1,1),'display':(.003,.03,.05,1),'clear':(.86,.96,1,1)}
mats={}
for key,col in colors.items():
 m=bpy.data.materials.new(key);m.diffuse_color=col;m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=col;p.inputs['Roughness'].default_value=.26
 if key=='clear':p.inputs['Transmission Weight'].default_value=1;p.inputs['IOR'].default_value=1.46;p.inputs['Roughness'].default_value=.065
 if key in ['crystal','ice']:p.inputs['Metallic'].default_value=.18;p.inputs['Roughness'].default_value=.14;p.inputs['Coat Weight'].default_value=.6;p.inputs['Emission Color'].default_value=col;p.inputs['Emission Strength'].default_value=.12
 if key=='metal':p.inputs['Metallic'].default_value=.9
 mats[key]=m
root=bpy.data.objects.new('LINGBAN_TURNTABLE',None);scene.collection.objects.link(root)
parts=json.loads((CAD/'parts.json').read_text())
for name,data in parts.items():
 bpy.ops.wm.stl_import(filepath=str(CAD/'exports'/(name+'.stl')));obj=bpy.context.object;obj.name=name;obj.scale=(.001,)*3;obj.data.materials.append(mats[data['material']]);obj.parent=root
 # Smooth only shallow angle transitions, preserving geometric crystal facets.
 if data['material']=='clear':
  bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35),keep_sharp_edges=True)
 if MODE=='exploded':
  dz=0
  if name.startswith('02'):dz=.105
  elif name.startswith(('11','12')):dz=.07
  elif name.startswith(('13','14','15')):dz=.043
  elif name.startswith(('06','07','08','09')):dz=.036
  elif name.startswith('05'):dz=.016
  obj.location.z+=dz
# RGB light diffuser arcs represented as underside optical effects, separate from PCB design.
def mat_emit(n,c,power):
 m=bpy.data.materials.new(n);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Emission Color'].default_value=(*c,1);p.inputs['Emission Strength'].default_value=power;return m
cyan=mat_emit('ICE BLUE status',(.025,.55,1),3);gold=mat_emit('Warm castle windows',(1,.48,.12),2)
# Small warm window inserts purely decorative visualization.
for x,y,z in [(17,14.9,27),(17,14.9,32),(25,21.8,25),(11,24.2,23)]:
 bpy.ops.mesh.primitive_cube_add(size=1,location=(x*.001,(y+5)*.001,z*.001+.002+(.07 if MODE=='exploded' else 0)));o=bpy.context.object;o.name='decorative_window';o.dimensions=(.0016,.0004,.0026);o.data.materials.append(gold);o.parent=root
# Light guide is visual concept; not counted as manufactured geometry.
curve=bpy.data.curves.new('lightguide_visual_concept','CURVE');curve.dimensions='3D';curve.bevel_depth=.00045;curve.bevel_resolution=3
sp=curve.splines.new('POLY');sp.points.add(160)
for i,p in enumerate(sp.points):
 a=2*math.pi*i/160;p.co=(.0385*math.cos(a),.061*math.sin(a),.0035,1)
o=bpy.data.objects.new('RGB_LIGHTGUIDE_VISUAL_ONLY',curve);scene.collection.objects.link(o);o.data.materials.append(cyan);o.parent=root
# Display content is synthetic, no live data.
bpy.ops.object.text_add(location=(.007,-.014,.01805+(.043 if MODE=='exploded' else 0)))
o=bpy.context.object;o.name='SYNTHETIC_SCREEN';o.data.body='FOCUS 25m';o.data.size=.0027;o.data.extrude=0;o.data.materials.append(cyan);o.parent=root
# Studio.
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.001));floor=bpy.context.object;floor.name='Studio';floor.data.materials.append(mats['graphite'])
def area(name,pos,power,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=power*.16;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.04))-o.location).to_track_quat('-Z','Y').to_euler()
area('Large softbox',(.10,-.12,.22),10,.17,(.80,.91,1));area('Rim',(-.14,.06,.15),14,.10,(.35,.67,1));area('Warm fill',(.13,.16,.11),9,.12,(1,.74,.46));area('Front strip',(-.03,-.16,.06),3,.08,(1,1,1))
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam
if MODE=='exploded':cam.location=(.19,-.26,.20);target=(0,0,.078);cam.data.ortho_scale=.25
else:cam.location=(.17,-.22,.175);target=(0,0,.024);cam.data.ortho_scale=.19
cam.data.type='ORTHO';cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=55
# Saved animation source, one full rotation, constant angular speed.
root.rotation_euler.z=0;root.keyframe_insert(data_path='rotation_euler',frame=1);root.rotation_euler.z=2*math.pi;root.keyframe_insert(data_path='rotation_euler',frame=121)
if root.animation_data:
 for f in root.animation_data.action.fcurves:
  for k in f.keyframe_points:k.interpolation='LINEAR'
scene.frame_start=1;scene.frame_end=120;scene.render.fps=24;scene.frame_set(1)
scene['disclaimer']='AI CONCEPT / DIGITAL ENGINEERING PROTOTYPE. Not a hardware photograph; no board test or certification.'
scene['units']='CAD meshes imported mm -> meters, scale 0.001. Lightguide/windows are visual-only effects.'
scene.render.filepath=str(R/(MODE+'_raw.png'))
bpy.ops.wm.save_as_mainfile(filepath=str(R/('lingban_'+MODE+'.blend')))
if MODE=='turntable':
 scene.render.resolution_x=720;scene.render.resolution_y=720;scene.cycles.samples=16;scene.render.image_settings.file_format='PNG';(R/'frames').mkdir(exist_ok=True)
 for frame in range(1,121,4):scene.frame_set(frame);scene.render.filepath=str(R/'frames'/f'{frame:04}.png');bpy.ops.render.render(write_still=True)
else:bpy.ops.render.render(write_still=True)
