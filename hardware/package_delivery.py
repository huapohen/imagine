"""Explicit review-artifact allowlist. Exclude tools, caches, secrets and local application state."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parent.parent;R=ROOT/'hardware';OUT=R/'delivery';OUT.mkdir(exist_ok=True)
checks=json.loads((R/'validation/artifact-check-summary.json').read_text())
assert checks['mesh_files']==20 and not checks['mesh_failures'] and checks['pin_failures']==0 and checks['netlist_mismatches']==0
assert checks['functional_pads']==49 and checks['nc_pads']==33
assert json.loads((R/'validation/cad-intersections.json').read_text())==[]
drc=json.loads((R/'validation/pcb-drc.json').read_text())
assert 'schematic_parity' in drc and drc['schematic_parity']==[] and drc['violations']==[] and drc['unconnected_items']==[]
erc=json.loads((R/'validation/sch-erc.json').read_text());assert all(not s['violations'] for s in erc['sheets'])
assert all(c['exit_code']==0 for c in json.loads((R/'validation/kicad-command-results.json').read_text()))
integration=json.loads((R/'validation/integration/result.json').read_text())
assert integration['changed_cad_render_files']==[] and integration['pcb_geometry_unchanged']
for p in ['renders/lingban_hero.png','renders/lingban_exploded.png','renders/lingban_turntable_concept.mp4','cad/exports/lingban_exploded.step']:
 assert (R/p).is_file(),p

def prohibited(rel):
 p=Path(rel);parts={x.lower() for x in p.parts};n=p.name.lower()
 return (bool(parts & {'tools','cache','caches','uv-cache','__pycache__','downloads','venv','.venv','.git','node_modules'})
         or any(x.startswith(('mount-','.')) for x in p.parts)
         or n.startswith(('.env','~')) or n.endswith(('.pyc','.blend1','.lck','.lock','.kicad_prl','.bak','.tmp','.dmg'))
         and n!='requirements.lock')
allowed_suffixes={'.md','.py','.json','.csv','.stl','.step','.dxf','.pdf','.txt','.kicad_pro','.kicad_sch','.kicad_pcb','.kicad_mod','.kicad_sym','.net','.xml','.svg','.png','.gbl','.gbs','.gbp','.gbo','.gm1','.gtl','.gts','.gto','.drl','.gbrjob'}
files=set()
def add(p):
 rel=str(p.relative_to(ROOT))
 if p.is_file() and not p.is_symlink() and not prohibited(rel):files.add(p)
for folder in ['specs','cad','pcb']:
 for p in (R/folder).rglob('*'):
  if p.suffix in allowed_suffixes or p.name in ['fp-lib-table','sym-lib-table']:add(p)
# Only current evidence, not scratch schematics, installer logs, caches or old local sessions.
reports=['README.md','validate_artifacts.py','artifact-check-summary.json','assembly-envelope.json','cad-brep.json','cad-intersections.json','stl-mesh-check.json','routing-summary.json','pcb-drc.json','pcb-geometric-drc.json','sch-erc.json','kicad-command-results.json','netlist-pinmap-check.json','media-probe.json','tool-integrity.json','kicad-export.log']
for name in reports:add(R/'validation'/name)
for name in ['baseline.json','result.json','parity-before.json','check_integration.py','README.md']:add(R/'validation/integration'/name)
for name in ['README.md','COMPLETION.md','package_delivery.py','requirements.lock']:add(R/name)
for name in ['README.md','render_scene.py','finish_media.py','lingban_hero.png','lingban_exploded.png','lingban_turntable_concept.mp4','lingban_hero.blend','lingban_exploded.blend','lingban_turntable.blend']:add(R/'renders'/name)
for p in (ROOT/'docs/hardware').glob('*.md'):add(p)
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
(OUT/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
archive=OUT/'lingban_evt_a_review.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(files):z.write(p,str(p.relative_to(ROOT)))
 z.write(OUT/'artifact-manifest.json','hardware/delivery/artifact-manifest.json')
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 forbidden=[n for n in z.namelist() if prohibited(n)];assert not forbidden
 mismatches=[n for n,h in manifest.items() if hashlib.sha256(z.read(n)).hexdigest()!=h];assert not mismatches
 assert 'hardware/pcb/sexpr.py' in z.namelist() and 'hardware/requirements.lock' in z.namelist()
 entries=len(z.namelist())
h=hashlib.sha256(archive.read_bytes()).hexdigest();(OUT/'SHA256SUMS.txt').write_text(h+'  '+archive.name+'\n')
audit={'archive':str(archive.relative_to(ROOT)),'files':entries,'bytes':archive.stat().st_size,'sha256':h,'zip_crc':'PASS','manifest_verified_files':len(manifest),'manifest_mismatches':mismatches,'forbidden_entries':forbidden,'excluded':'tools / caches / downloads / .env and all dotfiles / KiCad local state / locks / symlinks','parity_issues':0,'erc_violations':0,'geometric_drc_violations':0,'status':'NOT-FOR-FAB; electronic/mechanical engineer and physical review required'}
(OUT/'package-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n');print(json.dumps(audit,ensure_ascii=False,indent=2))
