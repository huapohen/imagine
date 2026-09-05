"""Read-only integration audit. Writes only this task's hardware validation report."""
from pathlib import Path
import hashlib,json,sys,re,ast
R=Path(__file__).resolve().parents[2];ROOT=R.parent
sys.path.insert(0,str(R/'pcb'));from sexpr import parse,dump
baseline=json.loads((R/'validation/integration/baseline.json').read_text())
changed=[n for n,h in baseline['preserved_files'].items() if not (ROOT/n).is_file() or hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=h]
board=parse((R/'pcb/NOT-FOR-FAB/lingban_carrier.kicad_pcb').read_text())
def physical(e):
 if not isinstance(e,list):return e
 return [physical(v) for v in e if not isinstance(v,list) or v[0] not in ['net','net_name','uuid','attr','path','sheetname','sheetfile','pinfunction','pintype']]
geom=[e for e in board if isinstance(e,list) and e[0] in ['segment','via','gr_rect','zone','footprint']]
geometry_same=hashlib.sha256(dump(physical(geom)).encode()).hexdigest()==baseline['pcb_geometry_sha256']
holes=[]
for fp in board:
 if not isinstance(fp,list) or fp[0]!='footprint':continue
 ref=next(x[2].strip('"') for x in fp if isinstance(x,list) and x[0]=='property' and x[1]=='"Reference"')
 if ref.startswith('H'):
  attrs=next(x[1:] for x in fp if isinstance(x,list) and x[0]=='attr')
  assert {'board_only','exclude_from_bom','exclude_from_pos_files'}<=set(attrs)
  holes.append(ref)
assert sorted(holes)==['H1','H2','H3','H4']
proj=json.loads((R/'pcb/NOT-FOR-FAB/lingban_carrier.kicad_pro').read_text())
assert not proj['board']['design_settings'].get('drc_exclusions',[])
# Compare the handoff to installed source configuration without importing or executing software.
sources=['docs/software/serial-protocol.md','firmware/serial-protocol.md','firmware/platformio.ini','firmware/include/board_config.hpp','firmware/include/controller.hpp','software/lingban/serial_protocol.py','docs/product/DECISIONS.md','docs/manufacturing-commercial/bom-cost-estimate.csv','docs/manufacturing-commercial/acceptance-and-schedule.md']
hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in sources}
profile=(ROOT/'firmware/platformio.ini').read_text();handoff=json.loads((R/'specs/pin-map.json').read_text())
names={'rgb_r':'LED_R','rgb_g':'LED_G','rgb_b':'LED_B','touch':'TOUCH','i2c_sda':'SDA','i2c_scl':'SCL','privacy_allow_n':'PRIVACY'}
for logical,flag in names.items():
 v=int(re.search(r'-DLB_PIN_'+flag+r'=(\d+)',profile)[1]);assert handoff['pins'][logical]['gpio']==v
assert 'board_upload.flash_size = 8MB' in profile and 'board_build.arduino.memory_type = qio_opi' in profile and 'board_build.psram_type = opi' in profile
assert '-DARDUINO_USB_CDC_ON_BOOT=0' in profile and 'monitor_speed = 115200' in profile and '-DLB_SCREEN_ADDRESS=0x3C' in profile
assert handoff['serial']['protocol']=='LB1' and handoff['serial']['baud']==115200
mod=ast.parse((ROOT/'software/lingban/serial_protocol.py').read_text())
constants={n.targets[0].id:ast.literal_eval(n.value) for n in mod.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['MAX_FRAME','TYPES']}
assert constants['MAX_FRAME']==handoff['serial']['max_frame_bytes_including_lf']==256
assert set(handoff['serial']['host_requests'])<=constants['TYPES'] and not handoff['serial']['per_message_ttl_supported'] and not handoff['serial']['push_events_supported']
assert handoff['firmware_profile']['touch_threshold']==0 and handoff['firmware_profile']['configured_caps']=={'led':1,'touch':0,'privacy':1,'screen':1}
assert '#define LB_TOUCH_THRESHOLD 0' in (ROOT/'firmware/include/board_config.hpp').read_text()
assert handoff['constraints']['display_address']==0x3c and handoff['constraints']['common_anode_off_duty']==255
cad=json.loads((R/'validation/cad-intersections.json').read_text());assert cad==[]
drc=json.loads((R/'validation/pcb-drc.json').read_text());erc=json.loads((R/'validation/sch-erc.json').read_text());geo=json.loads((R/'validation/pcb-geometric-drc.json').read_text())
assert 'schematic_parity' in drc
summary={'preserved_cad_render_file_count':len(baseline['preserved_files']),'changed_cad_render_files':changed,'pcb_geometry_unchanged':geometry_same,'mechanical_board_only':holes,'parity_issues':len(drc['schematic_parity']),'drc_violations':len(drc['violations']),'unconnected_items':len(drc['unconnected_items']),'geometric_drc_violations':len(geo['violations']),'erc_violations':sum(len(s['violations']) for s in erc['sheets']),'cad_intersections':cad,'source_read_only_hashes':hashes,'pin_profile_protocol_alignment':'PASS','firmware_tests':'Master reports two-target compile and mock HAL pass; not rerun by hardware session','render_reference_sha256':{n:baseline['preserved_files']['hardware/renders/'+n] for n in ['lingban_hero.png','lingban_exploded.png','lingban_turntable_concept.mp4']}}
(R/'validation/integration/result.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
assert not changed and geometry_same and all(summary[n]==0 for n in ['parity_issues','drc_violations','unconnected_items','geometric_drc_violations','erc_violations'])
print(json.dumps({k:v for k,v in summary.items() if k not in ['source_read_only_hashes','render_reference_sha256']},ensure_ascii=False,indent=2))
