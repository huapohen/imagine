"""Keep KiCad's local-label/NC semantics in the generator without rerouting copper.
No ignore rules or error exclusions. Existing schematic uses local labels and explicit NC flags.
"""
from pathlib import Path
import sys,json,uuid,csv
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pcb'))
from sexpr import parse,dump

def apply(out,components):
 out=Path(out);p=out/'lingban_carrier.kicad_pcb';board=parse(p.read_text())
 byref={c['ref']:c for c in components};nets={}
 for e in board:
  if isinstance(e,list) and e[0]=='net':
   code=int(e[1]);name=e[2].strip('"')
   if name and not name.startswith(('unconnected-','/')):e[2]='"/'+name+'"'
   nets[e[2].strip('"')]=code
 def net_for(name):
  if name not in nets:
   code=max(nets.values(),default=0)+1;nets[name]=code
   index=next(i for i,e in enumerate(board) if isinstance(e,list) and e[0]=='footprint')
   board.insert(index,['net',str(code),json.dumps(name)])
  return ['net',str(nets[name]),json.dumps(name)]
 def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'lingban/evt-a/'+s))
 for fp in [e for e in board if isinstance(e,list) and e[0]=='footprint']:
  ref=next(x[2].strip('"') for x in fp if isinstance(x,list) and x[0]=='property' and x[1]=='"Reference"');c=byref[ref]
  fp[:]=[x for x in fp if not isinstance(x,list) or x[0] not in ['attr','path']]
  if c['style']=='hole':
   fp.append(['attr','board_only','exclude_from_bom','exclude_from_pos_files'])
   continue
  fp.append(['attr','smd' if c['style']=='0805' else 'through_hole']+(['dnp'] if ref=='D1' else []))
  fp.append(['path',json.dumps('/'+uid('schematic')+'/'+uid('sch'+ref))])
  cp={str(v[0]):v[3] for v in c['pins']}
  for pad in [x for x in fp if isinstance(x,list) and x[0]=='pad']:
   number=pad[1].strip('"');name=cp[number]
   pad[:]=[x for x in pad if not isinstance(x,list) or x[0] not in ['net','pinfunction','pintype']]
   pad.append(net_for('/'+name if name else f'unconnected-({ref}-NC-Pad{number})'))
   pad.extend([['pinfunction',json.dumps(name or 'NC')],['pintype',json.dumps('passive' if name else 'passive+no_connect')]])
 # Each routed net keeps its code. Segment/via coordinates are not touched.
 p.write_text(dump(board))
 # Follow the declared BOM exclusion; mechanical holes stay in PCB, not procurement BOM.
 bom=out/'BOM.csv'
 if bom.exists():
  with bom.open() as f:rows=list(csv.DictReader(f))
  for row in rows:row['Footprint']='LINGBAN:'+row['Reference']
  with bom.open('w') as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(row for row in rows if byref[row['Reference']]['style']!='hole')
 return {'functional_nets':sum(n.startswith('/') for n in nets),'nc_nets':sum(n.startswith('unconnected-') for n in nets),'mechanical_board_only':4}
