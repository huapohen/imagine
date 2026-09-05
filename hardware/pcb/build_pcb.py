"""Deterministic editable KiCad schematic + genuinely routed two-layer carrier.
No library installation required: embedded symbols / self-contained footprints.
Digital prototype only: NOT-FOR-FAB until physical connector and power review.
"""
from pathlib import Path
import json,uuid,math,heapq,csv,collections,sys
R=Path(__file__).resolve().parent
OUT=R/'NOT-FOR-FAB';OUT.mkdir(exist_ok=True)
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'lingban/evt-a/'+s))
components=[]
def comp(ref,value,xy,pins,style='header',desc=''):
 # pins list: (number, local x, local y, net)
 components.append(dict(ref=ref,value=value,x=xy[0],y=xy[1],pins=pins,style=style,desc=desc))
left={1:'3V3',2:'3V3',4:'PWM_R',5:'PWM_G',6:'PWM_B',7:'TOUCH_IN',12:'SDA',15:'SCL',16:'PRIVACY_N',22:'GND'}
right={1:'GND',21:'GND',22:'GND'}
comp('J1','DevKitC1_LEFT_1x22',(6.57,10),[(i,0,(i-1)*2.54,left.get(i,'')) for i in range(1,23)],desc='Female socket 2.54mm; official J1 order; width pending DXF')
comp('J3','DevKitC1_RIGHT_1x22',(29.43,10),[(i,0,(i-1)*2.54,right.get(i,'')) for i in range(1,23)],desc='Female socket 2.54mm; official J3 order')
def smd(ref,val,x,y,a,b,style='0805'):comp(ref,val,(x,y),[(1,-1,0,a),(2,1,0,b)],style)
smd('R1','470R',14,18,'PWM_R','LED_R');smd('R2','470R',14,23,'PWM_G','LED_G');smd('R3','470R',14,28,'PWM_B','LED_B')
smd('R4','1k',14,33,'TOUCH_IN','ELECTRODE');smd('R5','4.7k',18,39,'SW3V3','SDA');smd('R6','4.7k',18,44,'SW3V3','SCL');smd('R7','10k',14,49,'3V3','PRIVACY_N')
smd('C1','100nF_16V_X7R',23,18,'3V3','GND');smd('C2','10uF_10V_X5R',23,24,'SW3V3','GND');smd('C3','100nF_16V_X7R',23,30,'SW3V3','GND')
smd('D1','ESD_DNI_REVIEW',23,50,'ELECTRODE','GND',style='0805')
def header(ref,val,x,y,nets):comp(ref,val,(x,y),[(i+1,i*2.54,0,n) for i,n in enumerate(nets)])
header('J4','OLED_GND_VCC_SCL_SDA',12,58,['GND','SW3V3','SCL','SDA'])
header('J5','REMOTE_RGB_COMMON_ANODE',11,65.5,['SW3V3','LED_R','LED_G','LED_B'])
header('J6','TOUCH_ELECTRODE_GND',23,55,['ELECTRODE','GND'])
header('J7','DPDT_HARNESS_6',10,71,['SW3V3','3V3','','PRIVACY_N','GND',''])
# Mechanical holes 30 x 68mm, no copper.
for i,(x,y) in enumerate([(3,3),(33,3),(3,71),(33,71)]):comp('H'+str(i+1),'M2_CLEARANCE',(x,y),[(1,0,0,'')],'hole')
nets=sorted({p[3] for c in components for p in c['pins'] if p[3]});NI={n:i+1 for i,n in enumerate(nets)}
# Metadata-only repair mode preserves the already verified copper and schematic.
if '--sync-existing' in sys.argv:
 from semantic_sync import apply
 print(apply(OUT,components));raise SystemExit(0)
# 0.2mm dual layer maze router with explicit clearance inflation and through pad obstacles.
STEP=.2;NX=181;NY=381
pads=[]
for c in components:
 for num,dx,dy,n in c['pins']:
  pads.append(dict(ref=c['ref'],num=num,x=c['x']+dx,y=c['y']+dy,net=n,through=c['style'] in ['header','hole'],radius=1.25 if c['style']=='hole' else ((1.21 if num==1 else .87) if c['style']=='header' else .93),style=c['style']))
# Each cell stores occupied net identities; '' is an unconnected physical obstacle.
occupied=[collections.defaultdict(set),collections.defaultdict(set)]
def disk(cx,cy,r):
 ix=round(cx/STEP);iy=round(cy/STEP);rr=math.ceil(r/STEP)
 for x in range(max(0,ix-rr),min(NX,ix+rr+1)):
  for y in range(max(0,iy-rr),min(NY,iy+rr+1)):
   if math.hypot(x*STEP-cx,y*STEP-cy)<=r:yield (x,y)
for p in pads:
 for layer in ([0,1] if p['through'] else [1]):
  for xy in disk(p['x'],p['y'],p['radius']+.20+.125):occupied[layer][xy].add(p['net'] or '!'+p['ref']+str(p['num']))
# copper-free antenna region y<8, except no pads there; margin to edge 0.6mm.
def valid(x,y,z,net):
 if x<3 or x>NX-4 or y<40 or y>NY-4:return False
 return not (occupied[z].get((x,y),set())-{net})
def route(a,b,net):
 starts=[(round(a['x']/STEP),round(a['y']/STEP),z) for z in ([0,1] if a['through'] else [1])]
 ends={(round(b['x']/STEP),round(b['y']/STEP),z) for z in ([0,1] if b['through'] else [1])}
 tx,ty=next(iter(ends))[:2]
 def heuristic(q):return abs(q[0]-tx)+abs(q[1]-ty)
 heap=[];cost={};prev={}
 for s in starts:cost[s]=0;heapq.heappush(heap,(heuristic(s),0,s))
 while heap:
  _,g,q=heapq.heappop(heap)
  if g!=cost[q]:continue
  if q in ends:
   path=[q]
   while q in prev:q=prev[q];path.append(q)
   return path[::-1]
  x,y,z=q
  for dx,dy,dz,dc in [(1,0,0,1),(-1,0,0,1),(0,1,0,1),(0,-1,0,1),(0,0,1,32)]:
   zz=1-z if dz else z;v=(x+dx,y+dy,zz)
   if not valid(*v,net):continue
   if dz:
    # Via copper clearance on both layers, exclude nearby unrelated inflated objects.
    if any(occupied[l].get(xy,set())-{net} for l in (0,1) for xy in disk(x*STEP,y*STEP,.36)):continue
   ng=g+dc
   if ng<cost.get(v,1e12):cost[v]=ng;prev[v]=q;heapq.heappush(heap,(ng+heuristic(v),ng,v))
 return None
routes=[];fail=[]
# Route shortest nets first, leave GND and supply spanning trees until last.
order=sorted(nets,key=lambda n:(n in ['GND','3V3','SW3V3'],len([p for p in pads if p['net']==n])))
for net in order:
 ns=[p for p in pads if p['net']==net];connected=[ns.pop(0)]
 while ns:
  _,ia,ib=min((math.hypot(a['x']-b['x'],a['y']-b['y']),ia,ib) for ia,a in enumerate(connected) for ib,b in enumerate(ns))
  a=connected[ia];b=ns.pop(ib);path=route(a,b,net)
  if path is None:fail.append([net,a['ref'],a['num'],b['ref'],b['num']]);connected.append(b);continue
  for x,y,z in path:
   for xy in disk(x*STEP,y*STEP,.20+.25):occupied[z][xy].add(net)
  for i,q in enumerate(path[1:]):
   if q[2]!=path[i][2]:
    for l in [0,1]:
     for xy in disk(q[0]*STEP,q[1]*STEP,.325+.20+.125):occupied[l][xy].add(net)
  routes.append(dict(net=net,a=a,b=b,path=path));connected.append(b)
 print('routed',net,flush=True)
# Board file, standard KiCad 8+ s-expression.
lines=['(kicad_pcb (version 20241229) (generator "lingban_parametric")','(general (thickness 1.6))','(paper "A4")','(layers (0 "F.Cu" signal) (31 "B.Cu" signal) (32 "B.Adhes" user "B.Adhesive") (33 "F.Adhes" user "F.Adhesive") (34 "B.Paste" user) (35 "F.Paste" user) (36 "B.SilkS" user "B.Silkscreen") (37 "F.SilkS" user "F.Silkscreen") (38 "B.Mask" user) (39 "F.Mask" user) (44 "Edge.Cuts" user) (46 "B.CrtYd" user "B.Courtyard") (47 "F.CrtYd" user "F.Courtyard") (48 "B.Fab" user) (49 "F.Fab" user))','(setup (pad_to_mask_clearance 0))']
for n,k in NI.items():lines.append(f'(net {k} "{n}")')
for c in components:
 ref=c['ref'];sty=c['style'];layer='B.Cu' if sty=='0805' else 'F.Cu'
 lines.append(f'(footprint "LINGBAN:{ref}" (layer "{layer}") (at {c["x"]} {c["y"]}) (uuid "{uid(ref)}") (property "Reference" "{ref}" (at 0 -2) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12)))) (property "Value" "{c["value"]}" (at 0 2) (layer "F.Fab") (effects (font (size 0.7 0.7) (thickness 0.1)))) (attr {"smd" if sty=="0805" else "through_hole"})')
 for num,dx,dy,n in c['pins']:
  net=f'(net {NI[n]} "{n}")' if n else ''
  if sty=='hole':p=f'np_thru_hole circle (at {dx} {dy}) (size 2.5 2.5) (drill 2.5) (layers "*.Cu" "*.Mask")'
  elif sty=='header':p=f'thru_hole {"rect" if num==1 else "circle"} (at {dx} {dy}) (size 1.7 1.7) (drill 1) (layers "*.Cu" "*.Mask")'
  else:p=f'smd roundrect (at {dx} {dy}) (size 1.2 1.4) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.2)'
  lines.append(f'(pad "{num}" {p} {net} (uuid "{uid(ref+str(num))}"))')
 lines.append(')')
segments=[];vias=[]
def seg(a,b,z,n):
 if math.dist(a,b)<.0001:return
 segments.append((a,b,z,n));lines.append(f'(segment (start {a[0]:.4f} {a[1]:.4f}) (end {b[0]:.4f} {b[1]:.4f}) (width 0.25) (layer "{["F.Cu","B.Cu"][z]}") (net {NI[n]}) (uuid "{uid("seg"+str(len(segments)))}"))')
for r in routes:
 path=r['path'];n=r['net'];a=r['a'];b=r['b']
 seg((a['x'],a['y']),(path[0][0]*STEP,path[0][1]*STEP),path[0][2],n)
 start=path[0];last=start;direction=None
 for q in path[1:]:
  d=(q[0]-last[0],q[1]-last[1],q[2]-last[2])
  if q[2]!=last[2]:
   seg((start[0]*STEP,start[1]*STEP),(last[0]*STEP,last[1]*STEP),last[2],n)
   pos=(q[0]*STEP,q[1]*STEP)
   if (pos,n) not in vias:
    vias.append((pos,n));lines.append(f'(via (at {pos[0]} {pos[1]}) (size 0.65) (drill 0.3) (layers "F.Cu" "B.Cu") (net {NI[n]}) (uuid "{uid("via"+str(len(vias)))}"))')
   start=q;direction=None
  elif direction is not None and d!=direction:
   seg((start[0]*STEP,start[1]*STEP),(last[0]*STEP,last[1]*STEP),last[2],n);start=last
  direction=d;last=q
 seg((start[0]*STEP,start[1]*STEP),(last[0]*STEP,last[1]*STEP),last[2],n)
 seg((path[-1][0]*STEP,path[-1][1]*STEP),(b['x'],b['y']),path[-1][2],n)
lines.append('(gr_rect (start 0 0) (end 36 76) (stroke (width 0.05) (type default)) (fill none) (layer "Edge.Cuts"))')
lines.append('(gr_text "LINGBAN EVT-A / NOT-FOR-FAB" (at 18 7) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))')
lines.append('(gr_text "ANTENNA KEEP CLEAR" (at 18 3) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))')
# Rule area over antenna, forbids copper on both layers.
lines.append('(zone (net 0) (net_name "") (layers "F.Cu" "B.Cu") (uuid "'+uid('antenna')+'") (hatch edge 0.5) (connect_pads (clearance 0.2)) (min_thickness 0.25) (keepout (tracks not_allowed) (vias not_allowed) (pads not_allowed) (copperpour not_allowed) (footprints allowed)) (polygon (pts (xy 7 0) (xy 29 0) (xy 29 8) (xy 7 8))))')
lines.append(')');(OUT/'lingban_carrier.kicad_pcb').write_text('\n'.join(lines))
# Embedded generic passive symbols: carrier is only connectors and passive devices.
# Direct net labels at short wire stubs, unused pins explicitly NC; all pin types passive intentionally.
SCHID=uid('schematic');sl=['(kicad_sch (version 20250114) (generator "eeschema") (uuid "'+SCHID+'") (paper "A3") (lib_symbols']
used=[c for c in components if c['style']!='hole']
for c in used:
 ref=c['ref'];n=len(c['pins']);h=(n+1)*2.54
 sl.append(f'(symbol "LINGBAN:{ref}" (pin_names (offset 0.5)) (in_bom yes) (on_board yes) (property "Reference" "{ref}" (at 2.54 2.54 0) (effects (font (size 1.27 1.27)))) (property "Value" "{c["value"]}" (at 2.54 0 0) (effects (font (size 1 1)))) (symbol "{ref}_0_1" (rectangle (start 0 -1.27) (end 12.7 {-h}) (stroke (width 0.254) (type default)) (fill (type background)))) (symbol "{ref}_1_1"')
 for i,(num,dx,dy,nm) in enumerate(c['pins']):
  sl.append(f'(pin passive line (at -5.08 {-(i+1)*2.54} 0) (length 5.08) (name "{nm or "NC"}" (effects (font (size 0.9 0.9)))) (number "{num}" (effects (font (size 0.9 0.9)))))')
 sl.append('))')
sl.append(')')
for index,c in enumerate(used):
 ref=c['ref'];n=len(c['pins']);x=35+(index%5)*76;y=35+(index//5)*63
 # Long devkit headers occupy first row; row spacing >=61mm.
 if index<2:x=35+index*100
 elif index<5:x=235+(index-2)*53
 x=round(x/1.27)*1.27;y=round(y/1.27)*1.27
 symid=uid('sch'+ref)
 sl.append(f'(symbol (lib_id "LINGBAN:{ref}") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp {"yes" if ref=="D1" else "no"}) (uuid "{symid}") (property "Reference" "{ref}" (at {x+6} {y-4} 0) (effects (font (size 1.27 1.27)))) (property "Value" "{c["value"]}" (at {x+6} {y-1} 0) (effects (font (size 1 1)))) (property "Footprint" "LINGBAN:{ref}" (at {x} {y} 0) (effects (font (size 1 1)) (hide yes))) (instances (project "lingban_carrier" (path "/{SCHID}" (reference "{ref}") (unit 1)))))')
 for i,(num,dx,dy,nm) in enumerate(c['pins']):
  xx=x-5.08;yy=y+(i+1)*2.54
  if not nm:sl.append(f'(no_connect (at {xx} {yy}) (uuid "{uid("nc"+ref+str(num))}"))');continue
  sl.append(f'(wire (pts (xy {xx} {yy}) (xy {xx-5.08} {yy})) (stroke (width 0) (type default)) (uuid "{uid("w"+ref+str(num))}"))')
  sl.append(f'(label "{nm}" (at {xx-5.08} {yy} 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{uid("lab"+ref+str(num))}"))')
sl.append('(text "LINGBAN EVT-A: PASSIVE CARRIER ONLY / NOT-FOR-FAB / J7: 1=SW3V3 common, 2=3V3 allow throw, 3=NC privacy throw; 4=PRIVACY_N common, 5=GND allow throw, 6=NC. / External DPDT switch, OLED and RGB LED require harness drawing. D1 is DNI pending low-capacitance ESD part review. / All MCU pins are socket contacts: ERC validates net connectivity, not ESP32 electrical behavior. See specs/pin-map.md." (at 22 275 0) (effects (font (size 1.2 1.2)) (justify left top)) (uuid "'+uid('note')+'"))')
sl.append(')');(OUT/'lingban_carrier.kicad_sch').write_text('\n'.join(sl))
proj={'board':{'design_settings':{'rules':{'min_clearance':.2,'min_track_width':.2,'min_via_diameter':.6,'min_through_hole_diameter':.3,'min_hole_clearance':.25,'min_copper_edge_clearance':.3}}},'net_settings':{'classes':[{'name':'Default','clearance':.2,'track_width':.25,'via_diameter':.65,'via_drill':.3}]},'meta':{'filename':'lingban_carrier.kicad_pro','version':1}}
(OUT/'lingban_carrier.kicad_pro').write_text(json.dumps(proj,indent=2))
with (OUT/'BOM.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['Reference','Value','Footprint','Qty','Assembly','Qualification'])
 for c in components:w.writerow([c['ref'],c['value'],'LINGBAN:'+c['style'],1,'DNI' if c['ref']=='D1' else ('mechanical' if c['style']=='hole' else 'fit'),'unqualified engineering estimate; verify exact supplier drawing'])
with (OUT/'PnP.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['Ref','Value','X_mm','Y_mm','Rotation_deg','Side','Fit'])
 for c in components:
  if c['style']=='0805':w.writerow([c['ref'],c['value'],c['x'],c['y'],0,'bottom','DNI' if c['ref']=='D1' else 'yes'])
(R/'design-data.json').write_text(json.dumps({'components':components,'nets':NI},indent=2))
(R.parent/'validation'/'routing-summary.json').write_text(json.dumps({'segments':len(segments),'vias':len(vias),'connections_routed':len(routes),'failed_connections':fail,'trace_width_mm':.25,'via_mm':[.65,.3],'grid_mm':STEP,'status':'NOT-FOR-FAB; run KiCad DRC/ERC'},indent=2))
print('DONE',len(segments),'segments',len(vias),'vias; failures',fail)

# Standard KiCad local label names, explicit NC nets and board-only holes.
from semantic_sync import apply
apply(OUT,components)
