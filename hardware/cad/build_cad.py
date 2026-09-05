"""Parametric BREP engineering concept. All coordinates mm, +Y rear, +Z up."""
from pathlib import Path
import cadquery as cq,json,math
R=Path(__file__).resolve().parent
P=json.loads((R/'parameters.json').read_text()); OUT=R/'exports';OUT.mkdir(exist_ok=True)
parts={};meta={}
def add(name,obj,kind='part',color='white'):
 parts[name]=obj;meta[name]={'kind':kind,'material':color}
def box(w,l,h,x=0,y=0,z=0):return cq.Workplane('XY').box(w,l,h,centered=(True,True,False)).translate((x,y,z))
def ellipse(rx,ry,z,h):return cq.Workplane('XY',origin=(0,0,z)).ellipse(rx,ry).extrude(h)
def cyl(r,h,x,y,z):return cq.Workplane('XY',origin=(x,y,z)).circle(r).extrude(h)
w=P['width']/2;l=P['length']/2;t=P['base_thickness']
base=ellipse(w,l,0,t).union(ellipse(w,l,t,3).cut(ellipse(w-P['wall_target'],l-P['wall_target'],t,4)))
base=base.cut(box(*P['optical_aperture'],10,0,-10,-1))
# OEM reference mounting slots; not optical design. Four adjustable seats.
for x in [-19,19]:
 for y in [-25,20]:
  base=base.union(cyl(4,3,x,y,t)).cut(cq.Workplane('XY',origin=(x,y,-1)).slot2D(7,2.3,90).extrude(9))
screw_xy=[(-34,-12),(34,-12),(-23,47),(23,47)]
for x,y in screw_xy:
 base=base.union(cyl(P['post_outer_diameter']/2,7,x,y,t)).cut(cyl(P['insert_pilot']/2,7,x,y,4))
# Two cable outlets from front, clear 6x6 each, preserve individual OEM/ESP connections.
for x in [-7,7]:base=base.cut(box(6,18,6,x,-59,2))
# Right hand external switch slot. Remote switch PCB/header remains inside.
base=base.cut(box(10,10,4,35,4,3))
add('01_base',base,color='graphite')
def loft(sections):
 wires=[]
 for z,rx,ry,cy in sections:
  wires.append(cq.Workplane('XY',origin=(0,cy*P['length']/126,z)).ellipse(rx*P['width']/80,ry*P['length']/126).val())
 return cq.Workplane('XY').newObject([cq.Solid.makeLoft(wires,ruled=False)])
outer=loft([(6.35,40,63,0),(14,40,61,2),(29,38,54,7),(43,29,39,12),(51,13,20,13),(54,2,4,13)])
inner=loft([(4,37.65,60.65,0),(14,37.8,58.8,2),(29,35.8,51.8,7),(42,26.5,36,12),(48.5,11,17,13),(51.5,1,2,13)])
shell=outer.cut(inner).cut(box(160,80,100,0,-67,5))
for x,y in screw_xy:
 # Rib from mounting boss toward outer side; boss clearance is printable through-hole.
 boss=cyl(3.2,3,x,y,10.35).cut(cyl(P['screw_clearance']/2,7,x,y,5))
 rib=box(8,3,3,x+(3 if x>0 else -3),y,10.35).intersect(outer)
 shell=shell.union(boss).union(rib).cut(cyl(P['screw_clearance']/2,12,x,y,4))
for x,y in screw_xy:shell=shell.cut(cyl(3.55,10.35,x,y,0))
add('02_clear_canopy',shell,color='clear')
# Independently detachable OEM actuator covers; linkage positions are placeholders.
for x,n in [(-18,'left'),(18,'right')]:
 b=box(23,28,3,x,-44,15).edges('|Z').fillet(5)
 add('03_button_'+n,b,color='pearl')
add('04_oem_wheel_placeholder',cq.Workplane('XZ',origin=(0,-43,14)).circle(6).extrude(4).translate((0,2,0)),kind='placeholder',color='graphite')
# Carrier mounting feet clear the adjustable OEM seats.
for x in [-25,5]:
 for y in [-31,37]:
  base=base.union(cyl(3,9,x,y,t)).cut(cyl(1.15,11,x,y,t))
# Printed insulating seats support display PCB and removable castle sled.
for x,y in [(12,30),(24,30),(29,-16),(30,0)]:base=base.union(cyl(2,11,x,y,3))
parts['01_base']=base
carrier=box(36,76,1.6,-10,2,12)
for x in [-25,5]:
 for y in [-31,37]:carrier=carrier.cut(cyl(1.25,3,x,y,11))
add('05_carrier_placeholder',carrier,'placeholder','pcb')
add('06_devkit_placeholder',box(25.4,62.74,1.6,-10,6.63,23),'placeholder','pcb')
for x in [-21.43,1.43]:add('07_socket_'+str(x),box(2.5,55.88,9,x,3.33,13.6),'placeholder','graphite')
add('08_esp_module_placeholder',box(18,25.5,3.2,-10,25.25,24.6),'placeholder','metal')
add('09_usb_uart_placeholder',box(8,6,3,-10,-26,24.6),'placeholder','metal')
oem=box(44,68,5,0,-12,6).cut(box(14,14,10,0,-43,5))
for x in [-25,5]:
 for y in [-31,37]:oem=oem.cut(cyl(3.35,20,x,y,0))
add('10_oem_placeholder',oem,'placeholder','darkpcb')
# Decorative architecture occupies a separate right-side island; no antenna metallization.
plinth=box(23,30,2,18,20,15).edges('|Z').fillet(4)
for x,y in [(12,12),(24,28)]:plinth=plinth.union(cyl(1.4,3,x,y,12))
castle=plinth
for x,y,rad,height in [(17,20,5.5,20),(25,25,3.4,14),(11,27,3.1,11)]:
 tower=cq.Workplane('XY',origin=(x,y,17)).polygon(6,rad*2).extrude(height-5)
 roof=cq.Workplane('XY',origin=(x,y,17+height-5)).polygon(6,rad*2.5).workplane(offset=8).polygon(6,0.8).loft()
 castle=castle.union(tower).union(roof)
# Original cantilevered cloud steps.
for i in range(4):castle=castle.union(box(9,4,1.6+i*2.2,20,5+i*3.1,17))
add('11_cloud_stair_castle',castle.translate((0,5,2)),color='crystal')
# Standalone sixfold snow crystal, removable peg. Design intentionally geometric.
snow=cyl(1.7,1.5,18,-7,27)
for a in range(0,360,60):
 arm=box(1.1,14,1.5,0,0,27).rotate((0,0,0),(0,0,1),a).translate((18,-7,0));snow=snow.union(arm)
 for sg in [-1,1]:
  branch=box(.9,4.4,1.5,0,0,27).rotate((0,0,0),(0,0,1),sg*45).translate((sg*1.5,4.3,0)).rotate((0,0,0),(0,0,1),a).translate((18,-7,0));snow=snow.union(branch)
snow=snow.union(cyl(1.4,7,18,-7,20));add('12_snowflake',snow.translate((8,7,-1)),color='ice')
frame=box(30,30,3,18.1,-6,16).cut(box(25,14,5,18.1,-11,15)).cut(box(27.7,27.7,1.6,18.1,-6,15.9))
frame=frame.union(cyl(2.6,3,26,0,19)).cut(cyl(1.75,5,26,0,18.5))
add('13_screen_frame',frame,color='graphite')
add('14_display_placeholder',box(27,27,2,18.1,-6,14),'placeholder','darkpcb')
add('15_display_glass',box(24.5,13.5,.6,18.1,-11,17.2),'placeholder','display')
# Sled for castle peg receptacles, detachable screws to base.
sled=box(22,29,2,18,25,14).edges('|Z').fillet(4)
for x,y in [(12,12),(24,28)]:sled=sled.cut(cyl(1.75,7,x,y+5,13))
add('16_castle_socket_sled',sled,color='pearl')
for x in [-7,7]:add('17_usb_cable_'+str(x),cq.Workplane('XZ',origin=(x,-55,5)).circle(2).extrude(40),'placeholder','graphite')
assembly=cq.Assembly(name='LINGBAN_EVT_A')
colors={'clear':(0.75,.94,1,.24),'graphite':(.035,.045,.07,1),'pearl':(.86,.91,.97,1),'pcb':(.05,.3,.2,1),'darkpcb':(.04,.08,.1,1),'metal':(.6,.65,.7,1),'crystal':(.55,.85,1,.8),'ice':(.85,.97,1,.8),'display':(.01,.07,.1,1)}
report={}
for name,obj in parts.items():
 cq.exporters.export(obj,str(OUT/(name+'.step')))
 cq.exporters.export(obj,str(OUT/(name+'.stl')),tolerance=.06,angularTolerance=.08)
 bb=obj.val().BoundingBox();report[name]={'valid_brep':obj.val().isValid(),'solids':len(obj.solids().vals()),'bbox_mm':[round(bb.xlen,3),round(bb.ylen,3),round(bb.zlen,3)],'volume_mm3':round(obj.val().Volume(),3),**meta[name]}
 assembly.add(obj,name=name,color=cq.Color(*colors[meta[name]['material']]))
assembly.export(str(OUT/'lingban_assembly.step'))
(R/'parts.json').write_text(json.dumps(report,indent=2))
(R.parent/'validation'/'cad-brep.json').write_text(json.dumps(report,indent=2))
# Pairwise positive-volume intersections, explicit engineering issue list, including placeholders.
collisions=[]
for i,(a,aa) in enumerate(parts.items()):
 for b,bb in list(parts.items())[i+1:]:
  v=aa.intersect(bb).val().Volume() if aa.intersect(bb).vals() else 0
  if v>.05:collisions.append({'a':a,'b':b,'intersection_mm3':round(v,3)})
(R.parent/'validation'/'cad-intersections.json').write_text(json.dumps(collisions,indent=2))
print('Exported',len(parts),'parts; valid',all(v['valid_brep'] for v in report.values()),'intersections',len(collisions),flush=True)
