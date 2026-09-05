#!/usr/bin/env python3
"""Offline edit of the positively matched successful QA browser recording only."""
import datetime, hashlib, json, pathlib, shutil, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont
ROOT=pathlib.Path(__file__).resolve().parents[2]; OUT=ROOT/'media/demo'; FONT='/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
EMP=ROOT/'.local/qa-recording/page@69599f6eb1e6de31e93728e8ee1cacb9.webm'
ENT=ROOT/'.local/qa-recording/page@c66339f90bb24ee53379e2f4e372741b.webm'
REV=OUT/'enterprise_revoked_verified.png';REPORT=OUT/'qa-report-snapshot.json'
def run(cmd):subprocess.run(cmd,check=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))
def main():
 OUT.mkdir(exist_ok=True)
 if not REPORT.exists():shutil.copyfile(ROOT/'docs/verification/browser/report.json',REPORT)
 r=json.loads(REPORT.read_text());assert len(r.get('checks',[]))==14 and all(x['pass'] for x in r['checks']) and not r.get('errors') and r.get('status')!='failed'
 if not REV.exists():shutil.copyfile(ROOT/'docs/verification/browser/enterprise-revoked.png',REV)
 scenes=[
 {'source':EMP,'start':.2,'end':3.2,'duration':6,'caption':'01 员工提醒 → 本人批准 → 只写入本地 outbox','voice':'会议提醒后，由本人批准。记录只保存在本地，没有对外发送。'},
 {'source':EMP,'start':7.2,'end':10.34,'cuts':[[7.2,8.7],[8.84,10.34]],'duration':6,'caption':'02 模拟隐私开关开启：模拟触摸被禁用','voice':'打开模拟隐私开关，模拟触摸随即停用。这里没有实测硬件。'},
 {'source':ENT,'start':.2,'end':2.2,'duration':4,'caption':'03 企业仅见明确授权的业务汇总，不见个人状态','voice':'企业只看授权的业务汇总。'},
 {'source':EMP,'start':10.2,'end':12.7,'duration':5,'caption':'04 员工撤销分享，已有共享数据删除','voice':'员工可以随时撤销分享，共享数据随即删除。'},
 {'source':REV,'duration':7,'caption':'05 同次成功验证截图定格：不足 5 人，企业结果隐藏','voice':'同次验证截图显示，分享人数不足五人，结果已隐藏。全部使用合成数据和离线规则。','still':True},
 ]
 timeline=[];elapsed=0
 with tempfile.TemporaryDirectory(prefix='lingban-real-demo-') as td:
  td=pathlib.Path(td);parts=[]
  for i,s in enumerate(scenes):
   layer=Image.new('RGBA',(1920,1080));d=ImageDraw.Draw(layer);d.rectangle((0,0,1920,60),fill='#0b2928');d.rectangle((0,1020,1920,1080),fill='#0b2928');d.text((38,10),'真实软件浏览器录屏 · 合成数据 · 设备模拟 · 离线规则',font=ImageFont.truetype(FONT,36),fill='white');d.text((38,1032),s['caption'],font=ImageFont.truetype(FONT,29),fill='white');d.text((1695,1035),'截图定格' if s.get('still') else '0.5× 慢放',font=ImageFont.truetype(FONT,25),fill='#b2e0ca');overlay=td/f'{i}.png';layer.save(overlay)
   text=OUT/f'narration_{i+1:02d}.txt';text.write_text(s['voice']+'\n');voice=OUT/f'narration_{i+1:02d}.aiff'
   if not voice.exists():run(['say','-v','Tingting','-r','175','-f',str(text),'-o',str(voice)])
   dur=float(probe(voice)['format']['duration']);tempo=max(1.,dur/(s['duration']-.4))
   cmd=['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y']
   if s.get('still'):cmd+=['-loop','1','-i',str(s['source'])];vf=f'[0:v]scale=1440:960:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0xf5f8f6,trim=duration={s["duration"]},setpts=PTS-STARTPTS[base]'
   else:
    cmd+=['-i',str(s['source'])]
    if s.get('cuts'):
     (a,b),(c,d)=s['cuts'];vf=f'[0:v]split=2[x][y];[x]trim=start={a}:end={b},setpts=PTS-STARTPTS[xx];[y]trim=start={c}:end={d},setpts=PTS-STARTPTS[yy];[xx][yy]concat=n=2:v=1:a=0,setpts=2*(PTS-STARTPTS),pad=1920:1080:240:60:color=0xf5f8f6[base]'
    else:vf=f'[0:v]trim=start={s["start"]}:end={s["end"]},setpts=2*(PTS-STARTPTS),pad=1920:1080:240:60:color=0xf5f8f6[base]'
   cmd+=['-loop','1','-i',str(overlay),'-i',str(voice)]
   filters=vf+';[base][1:v]overlay=0:0[v];'+f'[2:a]atempo={tempo},aresample=48000,loudnorm=I=-16:TP=-1.5:LRA=7,adelay=200|200,apad,atrim=duration={s["duration"]}[a]'
   part=td/f'{i}.mp4';cmd+=['-filter_complex',filters,'-map','[v]','-map','[a]','-t',str(s['duration']),'-r','25','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-ar','48000','-b:a','160k','-map_metadata','-1',str(part)];run(cmd);parts.append(part)
   timeline.append({'output_start':elapsed,'output_end':elapsed+s['duration'],'source':str(s['source'].relative_to(ROOT)),'source_start':s.get('start'),'source_end':s.get('end'),'source_cuts':s.get('cuts'),'speed':0 if s.get('still') else .5,'caption':s['caption'],'kind':'same successful QA screenshot freeze' if s.get('still') else 'actual isolated Chrome recording','source_sha256':sha(s['source'])});elapsed+=s['duration']
  listing=td/'concat.txt';listing.write_text(''.join("file '"+str(p)+"'\n" for p in parts));raw=td/'raw.mp4';run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-f','concat','-safe','0','-i',str(listing),'-c','copy',str(raw)])
  st=float(next(s for s in probe(raw)['streams'] if s['codec_type']=='video').get('start_time',0));out=OUT/'lingban-software-demo.mp4';run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-itsoffset',str(-st),'-i',str(raw),'-i',str(raw),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','160k','-ar','48000','-af','apad','-t',str(elapsed),'-metadata','comment=Actual isolated browser recording with synthetic data, device simulation and offline rules. Includes explicitly labelled same-run verification screenshot freeze.','-movflags','+faststart',str(out)])
 info=probe(out);assert info['format']['duration']=='28.000000';frames=[]
 for second in [1,5,9,14,19,24]:
  path=OUT/f'frame_{second:02d}s.jpg';run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-ss',str(second),'-i',str(out),'-frames:v','1','-vf','scale=960:540',str(path)]);frames.append(Image.open(path).convert('RGB'))
 sheet=Image.new('RGB',(1920,1620))
 for i,im in enumerate(frames):sheet.paste(im,((i%2)*960,(i//2)*540))
 sheet.save(OUT/'contact-sheet.jpg',quality=92)
 (OUT/'provenance.json').write_text(json.dumps({'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'kind':'actual software browser recording edit; not AI concept footage and not real hardware','matched_success_report_sha256':sha(REPORT),'successful_checks':14,'selected_source_mtimes':'2026-09-06 01:50:09 Asia/Shanghai; report 01:50:08, successful screenshots 01:49:56–01:50:08','excluded_recordings':'All earlier recordings including the 01:49:20 one-second recording excluded','timeline':timeline,'output_duration_seconds':28,'output_size':[1920,1080],'source_recording_size':[1440,960],'voice':'Existing local macOS Tingting / say; no paid services','token_handling':'Selected only authenticated workspace intervals; no login field or browser chrome included. Login input verified type=password. No credentials loaded or read by edit script.','output_sha256':sha(out)},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'output':str(out),'duration':28,'contact_sheet':str(OUT/'contact-sheet.jpg')}))
if __name__=='__main__':main()
