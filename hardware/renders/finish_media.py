from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import subprocess,json
R=Path(__file__).resolve().parent
CJK='/System/Library/Fonts/STHeiti Light.ttc';LAT='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
def font(n,cjk=True):return ImageFont.truetype(CJK if cjk else LAT,n)
def finish(name):
 im=Image.open(R/(name+'_raw.png')).convert('RGB');d=ImageDraw.Draw(im)
 d.text((80,55),'灵伴 LINGBAN',font=font(64),fill='#edf8ff')
 d.text((83,139),'CRYSTAL MOUSE  /  EVT-A',font=font(28,False),fill='#afddf5')
 if name=='hero':d.text((83,186),'双 USB · 电脑运行 Agent · 可拆原创晶堡',font=font(25),fill='#d1e5ef')
 else:
  for x,y,txt,ex,ey in [(75,380,'透明上壳',590,440),(1280,610,'独立晶堡 / 雪花',1150,690),(75,835,'ESP32-S3 / 屏框',635,900),(1290,1010,'交互载板占位',1090,1060),(75,1250,'OEM 总成 / 底壳',520,1300)]:
   d.text((x,y),txt,font=font(26),fill='#d2edfc');sx=x+200 if x<500 else x;d.line([(sx,y+36),(ex,ey)],fill='#7097ac',width=2)
 d.rectangle((0,im.height-59,im.width,im.height),fill='#111d2b')
 d.text((65,im.height-45),'AI概念展示 · 数字工程原型 · 非实物照片 · 未打样 / 未认证',font=font(24),fill='#cee5f3')
 im.save(R/('lingban_'+name+'.png'))
for name in ['hero','exploded']:finish(name)
F=R/'frames';A=R/'frames-labeled';A.mkdir(exist_ok=True)
frames=sorted(F.glob('*.png'))
for i,p in enumerate(frames,1):
 im=Image.open(p).convert('RGB');d=ImageDraw.Draw(im);d.text((25,23),'灵伴 LINGBAN / Crystal Mouse',font=font(24),fill='#e7f7ff');d.rectangle((0,676,720,720),fill='#111d2b');d.text((20,689),'AI概念展示 · 数字工程原型 · 非实物',font=font(20),fill='#cee5f3');im.save(A/f'{i:04}.png')
if frames:
 cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-framerate','6','-i',str(A/'%04d.png'),'-c:v','libx264','-crf','19','-r','24','-pix_fmt','yuv420p','-movflags','+faststart','-metadata','title=LINGBAN EVT-A AI concept digital prototype',str(R/'lingban_turntable_concept.mp4')]
 subprocess.run(cmd,check=True)
 r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration,size:stream=codec_name,width,height,r_frame_rate','-of','json',str(R/'lingban_turntable_concept.mp4')],capture_output=True,text=True,check=True)
 (R.parent/'validation/media-probe.json').write_text(r.stdout)
print('Labeled PNGs and',len(frames),'turntable frames finished')
