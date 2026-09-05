from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pcb'))
from sexpr import parse,dump
R=Path(__file__).resolve().parent/'NOT-FOR-FAB'
p=R/'lingban_carrier.kicad_pcb';a=parse(p.read_text());lib=R/'LINGBAN.pretty';lib.mkdir(exist_ok=True)
for fp in [x for x in a if isinstance(x,list) and x[0]=='footprint']:
 name=fp[1].strip('"').split(':')[-1]
 # Preserve geometry and reference/value while removing board-only absolute location and all nets/UUIDs.
 def clean(x):
  if not isinstance(x,list):return x
  return [clean(e) for e in x if not isinstance(e,list) or e[0] not in ['net','uuid','path']]
 b=clean(fp);b[1]='"'+name+'"';b=[e for e in b if not isinstance(e,list) or e[0]!='at']
 b.insert(2,['version','20241229']);b.insert(3,['generator','"pcbnew"'])
 (lib/(name+'.kicad_mod')).write_text(dump(b))
(R/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "LINGBAN") (type "KiCad") (uri "${KIPRJMOD}/LINGBAN.pretty") (options "") (descr "Self-contained engineering footprints; NOT-FOR-FAB")))')
a=parse((R/'lingban_carrier.kicad_sch').read_text());libs=next(x for x in a if isinstance(x,list) and x[0]=='lib_symbols')
symbols=[]
for s in libs[1:]:
 b=s.copy();b[1]='"'+s[1].strip('"').split(':')[-1]+'"';symbols.append(b)
(R/'LINGBAN.kicad_sym').write_text(dump(['kicad_symbol_lib',['version','20241209'],['generator','"kicad_symbol_editor"']]+symbols))
(R/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "LINGBAN") (type "KiCad") (uri "${KIPRJMOD}/LINGBAN.kicad_sym") (options "") (descr "Passive carrier socket and discrete component symbols")))')
print('Project footprint and symbol libraries written')
