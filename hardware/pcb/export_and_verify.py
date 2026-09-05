from pathlib import Path
import subprocess,os,json,sys,textwrap
R=Path(__file__).resolve().parents[1];D=R/'pcb'/'NOT-FOR-FAB';K=R/'tools/mount-kicad/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
sys.path.insert(0,str(R/'pcb'));from sexpr import parse,dump
p=D/'lingban_carrier.kicad_sch';a=parse(p.read_text())
for e in a:
 if isinstance(e,list) and e[0]=='text':
  msg=e[1][1:-1].replace(chr(92)+'n',' ');e[1]='"'+(chr(92)+'n').join(textwrap.wrap(msg,135))+'"'
p.write_text(dump(a))
# D1 deliberately not fitted. Mark DNP in the actual PCB as well as BOM/schematic.
p=D/'lingban_carrier.kicad_pcb';a=parse(p.read_text())
for e in a:
 if isinstance(e,list) and e[0]=='footprint' and e[1]=='"LINGBAN:D1"':
  att=next(x for x in e if isinstance(x,list) and x[0]=='attr')
  if 'dnp' not in att:att.append('dnp')
p.write_text(dump(a))
# Geometry-only DRC is separately recorded; parity DRC remains mandatory.
# This process inherits environment without inspecting secret values; only task-local KiCad config is set.
os.environ['KICAD_CONFIG_HOME']=str(R/'tools/kicad-config')
(D/'gerber-review-only').mkdir(exist_ok=True);(D/'plots').mkdir(exist_ok=True)
base=str(D/'lingban_carrier.kicad_pcb');sch=str(D/'lingban_carrier.kicad_sch')
commands=[['pcb','drc','--schematic-parity','--format','json','--exit-code-violations','-o',str(R/'validation/pcb-drc.json'),base],['sch','erc','--format','json','--exit-code-violations','-o',str(R/'validation/sch-erc.json'),sch],['sch','export','netlist','-o',str(D/'lingban_carrier.net'),sch],['sch','export','netlist','--format','kicadxml','-o',str(D/'lingban_carrier.xml'),sch],['sch','export','svg','-o',str(D/'plots')+'/',sch],['pcb','export','gerbers','-l','F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,B.Paste,Edge.Cuts','-o',str(D/'gerber-review-only')+'/',base],['pcb','export','drill','--excellon-separate-th','--generate-map','--map-format','svg','-o',str(D/'gerber-review-only')+'/',base],['pcb','export','pos','--format','csv','--units','mm','--smd-only','--exclude-dnp','-o',str(D/'PnP-kicad.csv'),base],['pcb','export','svg','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','-l','F.Cu,B.Cu,F.SilkS,Edge.Cuts','-o',str(D/'plots/pcb-routed.svg'),base]]
commands.insert(1,['pcb','drc','--format','json','--exit-code-violations','-o',str(R/'validation/pcb-geometric-drc.json'),base])
results=[]
with (R/'validation/kicad-export.log').open('w') as log:
 for c in commands:
  r=subprocess.run([str(K)]+c,capture_output=True,text=True);log.write('$ kicad-cli '+' '.join(c)+'\n'+r.stdout+r.stderr+'\n');results.append({'command':c,'exit_code':r.returncode});print(c[:3],r.returncode,flush=True)
(R/'validation/kicad-command-results.json').write_text(json.dumps(results,indent=2))
if any(x['exit_code'] for x in results):raise SystemExit(1)
