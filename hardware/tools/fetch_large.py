import subprocess,pathlib,time,concurrent.futures,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def proxy():
 s=subprocess.check_output(['scutil','--proxy'],text=True)
 def v(k):return next((l.split(' : ')[1].strip() for l in s.splitlines() if l.strip().startswith(k+' : ')),None)
 return 'http://'+v('HTTPProxy')+':'+v('HTTPPort') if v('HTTPEnable')=='1' else ''
def download(name,url):
 dest=ROOT/'downloads'/name
 for attempt in range(12):
  route='' if attempt%3!=2 else proxy()
  # Refresh dynamic proxy at each bounded 45s chunk; retain partial data.
  r=subprocess.run(['curl','-fL','-sS','-C','-','--connect-timeout','6','--max-time','45','--speed-limit','50000','--speed-time','12','--proxy',route,url,'-o',str(dest)],capture_output=True,text=True)
  print(name,attempt,dest.stat().st_size if dest.exists() else 0,r.returncode,r.stderr[-150:],flush=True)
  if r.returncode==0:return
 raise RuntimeError('download incomplete '+name)
with concurrent.futures.ThreadPoolExecutor() as ex:
 jobs=[ex.submit(download,'blender.dmg','https://mirrors.tuna.tsinghua.edu.cn/blender/release/Blender4.5/blender-4.5.3-macos-arm64.dmg'),ex.submit(download,'kicad.dmg','https://mirrors.tuna.tsinghua.edu.cn/kicad/osx/stable/kicad-unified-universal-9.0.7.dmg')]
 for j in jobs:j.result()
