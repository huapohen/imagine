import subprocess,pathlib,concurrent.futures,json,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
def proxy():
 s=subprocess.check_output(['scutil','--proxy'],text=True)
 def v(k):return next((l.split(' : ')[1].strip() for l in s.splitlines() if l.strip().startswith(k+' : ')),None)
 return 'http://'+v('HTTPProxy')+':'+v('HTTPPort') if v('HTTPEnable')=='1' else ''
def get(name,url,route=''):
 r=subprocess.run(['curl','-fL','--connect-timeout','8','--max-time','45','--proxy',route,'-sS',url,'-o',str(ROOT/'downloads'/name)],capture_output=True,text=True);print(name,r.returncode,r.stderr,flush=True)
items=[('blender.sha256','https://download.blender.org/release/Blender4.5/blender-4.5.3.sha256',proxy()),('kicad-download.html','https://downloads.kicad.org/kicad/macos/explore/stable/download/kicad-unified-universal-9.0.7.dmg',''),('esp32-official.html','https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/index.html',proxy())]
with concurrent.futures.ThreadPoolExecutor() as ex:list(ex.map(lambda a:get(*a),items))
