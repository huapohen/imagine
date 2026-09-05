"""Checks actual exported meshes and KiCad netlist against independent official pin assignments."""
from pathlib import Path
import json,sys,xml.etree.ElementTree as ET
import trimesh
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'pcb'));from sexpr import parse
mesh_report={};meshes={}
for p in sorted((R/'cad/exports').glob('*.stl')):
 m=trimesh.load_mesh(p,process=True);meshes[p.stem]=m;mesh_report[p.stem]={'watertight':bool(m.is_watertight),'winding_consistent':bool(m.is_winding_consistent),'positive_volume':bool(m.volume>0),'components':len(m.split()),'faces':len(m.faces)}
(R/'validation/stl-mesh-check.json').write_text(json.dumps(mesh_report,indent=2))
parts=json.loads((R/'cad/parts.json').read_text());bounds=np.array([m.bounds for n,m in meshes.items() if not n.startswith('17')]);lo=bounds[:,0,:].min(axis=0);hi=bounds[:,1,:].max(axis=0)
(R/'validation/assembly-envelope.json').write_text(json.dumps({'units':'mm','excludes':'USB cable extensions','mesh_assembly_min':lo.tolist(),'mesh_assembly_max':hi.tolist(),'mesh_assembly_bbox':(hi-lo).tolist(),'volume_of_manufactured_parts_mm3':sum(v['volume_mm3'] for v in parts.values() if v['kind']=='part'),'note':'Nominal 126x80x54; BREP bounding boxes are conservative.'},indent=2))
D=R/'pcb/NOT-FOR-FAB';nettree=ET.parse(D/'lingban_carrier.xml');actual={}
for n in nettree.findall('.//nets/net'):
 for pin in n.findall('node'):actual[(pin.attrib['ref'],pin.attrib['pin'])]=n.attrib['name']
expected={('J1','1'):'3V3',('J1','2'):'3V3',('J1','4'):'PWM_R',('J1','5'):'PWM_G',('J1','6'):'PWM_B',('J1','7'):'TOUCH_IN',('J1','12'):'SDA',('J1','15'):'SCL',('J1','16'):'PRIVACY_N',('J1','22'):'GND',('J3','1'):'GND',('J3','21'):'GND',('J3','22'):'GND',('J4','1'):'GND',('J4','2'):'SW3V3',('J4','3'):'SCL',('J4','4'):'SDA',('J7','1'):'SW3V3',('J7','2'):'3V3',('J7','4'):'PRIVACY_N',('J7','5'):'GND'}
# Local-label prefix is significant: never strip it when comparing PCB to schematic.
expected={k:'/'+v for k,v in expected.items()}
checks=[{'ref':r,'pin':p,'expected':n,'actual':actual.get((r,p)),'pass':actual.get((r,p))==n} for (r,p),n in expected.items()]
board=parse((D/'lingban_carrier.kicad_pcb').read_text());boardpins={}
for fp in board:
 if not isinstance(fp,list) or fp[0]!='footprint':continue
 ref=next(x[2].strip('"') for x in fp if isinstance(x,list) and x[0]=='property' and x[1]=='"Reference"')
 for pad in fp:
  if isinstance(pad,list) and pad[0]=='pad':
   n=next((x[2].strip('"') for x in pad if isinstance(x,list) and x[0]=='net'),None)
   if n:boardpins[(ref,pad[1].strip('"'))]=n
mismatches=[{'ref':r,'pin':p,'board':boardpins.get((r,p)),'schematic':actual.get((r,p))} for r,p in sorted(set(boardpins)|set(actual)) if boardpins.get((r,p))!=actual.get((r,p))]
functional={k:v for k,v in boardpins.items() if not v.startswith('unconnected-')}
nc={k:v for k,v in boardpins.items() if v.startswith('unconnected-')}
net_codes={e[2].strip(chr(34)):e[1] for e in board if isinstance(e,list) and e[0]=='net'}
copper_codes={next(x[1] for x in e if isinstance(x,list) and x[0]=='net') for e in board if isinstance(e,list) and e[0] in ['segment','via']}
nc_integrity=all(list(boardpins.values()).count(n)==1 and net_codes[n] not in copper_codes for n in nc.values())
assert len(functional)==49 and len(nc)==33 and nc_integrity, 'NC must be 33 isolated singleton nets; 49 functional pads'
# No 5V, native USB, UART, flash/PSRAM or boot strap connections on carrier.
for ref,pins in [('J1',[3,13,14,21]),('J3',[2,3,10,11,12,13,14,15,16,19,20])]:
 for pin in pins:checks.append({'ref':ref,'pin':str(pin),'expected':'unconnected','pass':boardpins.get((ref,str(pin)))==f'unconnected-({ref}-NC-Pad{pin})'})
report={'pin_checks':checks,'board_to_schematic_mismatches':mismatches,'compared_connected_pads':len(functional),'compared_explicit_nc_pads':len(nc),'compared_all_pads':len(boardpins),'nc_singleton_without_copper':nc_integrity,'exact_names_no_prefix_normalization':True,'source':'Espressif v1.1 user guide J1/J3 pin tables; cached references/esp32-official-text.txt'}
(R/'validation/netlist-pinmap-check.json').write_text(json.dumps(report,indent=2))
failed=[k for k,v in mesh_report.items() if not(v['watertight'] and v['winding_consistent'] and v['positive_volume'] and v['components']==1)]
report={'mesh_files':len(mesh_report),'mesh_failures':failed,'pin_checks':len(checks),'pin_failures':sum(not c['pass'] for c in checks),'netlist_mismatches':len(mismatches),'functional_pads':len(functional),'nc_pads':len(nc)}
(R/'validation/artifact-check-summary.json').write_text(json.dumps(report,indent=2));print(report)
if failed or mismatches or not all(c['pass'] for c in checks):raise SystemExit(1)
