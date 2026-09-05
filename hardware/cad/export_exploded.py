from pathlib import Path
import cadquery as cq,json
R=Path(__file__).resolve().parent;a=cq.Assembly(name='LINGBAN_EVT_A_EXPLODED')
for name,info in json.loads((R/'parts.json').read_text()).items():
 dz=105 if name.startswith('02') else 70 if name.startswith(('11','12')) else 43 if name.startswith(('13','14','15')) else 36 if name.startswith(('06','07','08','09')) else 16 if name.startswith('05') else 0
 o=cq.importers.importStep(str(R/'exports'/(name+'.step'))).translate((0,0,dz));a.add(o,name=name)
a.export(str(R/'exports/lingban_exploded.step'))
print('Exploded STEP exported in mm')
