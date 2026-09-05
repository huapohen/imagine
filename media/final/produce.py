#!/usr/bin/env python3
"""Offline postproduction only: local say + ffmpeg. Never uses API/credentials."""
import argparse, datetime, hashlib, json, pathlib, re, subprocess, tempfile, time, textwrap
from PIL import Image, ImageDraw, ImageFont
ROOT=pathlib.Path(__file__).resolve().parent.parent
FINAL=ROOT/'final'; QA=ROOT/'qa'; VO=ROOT/'voiceover'
FONT='/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
def run(args,**kw):return subprocess.run(args,check=True,**kw)
def probe(path):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],text=True))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def timestamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def box(draw,xy,text,font,fill='white'):
 b=draw.multiline_textbbox(xy,text,font=font,spacing=12);draw.rounded_rectangle((b[0]-20,b[1]-12,b[2]+20,b[3]+12),radius=14,fill=(9,16,28,215));draw.multiline_text(xy,text,font=font,fill=fill,spacing=12)
def contact(video,id):
 frames=[]
 for second in [1,5,9,13]:
  path=QA/f'{id}_{second:02d}s.jpg'
  run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-ss',str(second),'-i',str(video),'-frames:v','1','-vf','scale=960:-2',str(path)])
  im=Image.open(path).convert('RGB');d=ImageDraw.Draw(im);d.rectangle((0,0,75,26),fill='#08121c');d.text((8,4),f'{second:02d}s',font=ImageFont.truetype(FONT,18),fill='white');frames.append(im)
 sheet=Image.new('RGB',(1920,1080),'#0b1420')
 for i,im in enumerate(frames):sheet.paste(im,((i%2)*960,(i//2)*540))
 sheet.save(QA/f'{id}_contact.jpg',quality=90)
def produce(row):
 id=row['id'];source=ROOT/'generated'/f'{id}.mp4';out=FINAL/f'{id}.mp4';manifest=FINAL/f'{id}.provenance.json'
 if not source.exists():return False
 if out.exists() and manifest.exists() and (QA/f'{id}_contact.jpg').exists():return True
 info=probe(source);v=next(s for s in info['streams'] if s['codec_type']=='video');w,h=v['width'],v['height'];duration=float(info['format']['duration'])
 if (w,h)!=(2560,1440) or not 14.95<=duration<=15.25:raise ValueError(f'{id}: source must be native 2560x1440 approximately 15s; no upscaling or padding')
 narration=row['voiceover_zh'];textfile=VO/f'{id}.txt';textfile.write_text(narration+'\n');speech=VO/f'{id}.aiff'
 if not speech.exists():run(['say','-v','Tingting','-r','140','-f',str(textfile),'-o',str(speech)])
 sd=float(probe(speech)['format']['duration']);tempo=max(1.,sd/11.5)
 if tempo>1.5:raise ValueError('Narration too long; rewrite manually')
 with tempfile.TemporaryDirectory(prefix='lingban-post-') as tmp:
  tmp=pathlib.Path(tmp);label=Image.new('RGBA',(w,h));draw=ImageDraw.Draw(label);font=ImageFont.truetype(FONT,44);small=ImageFont.truetype(FONT,34);title=ImageFont.truetype(FONT,48)
  box(draw,(66,52),'AI概念演示 · 非已生产实机',font)
  box(draw,(66,119),row['title'],title)
  box(draw,(66,h-78),'灵伴 LINGBAN  |  外观与功能待工程验证  |  屏幕内容为合成示意',small)
  layer=tmp/'labels.png';label.save(layer)
  cap=Image.new('RGBA',(w,h));draw=ImageDraw.Draw(cap);lines=textwrap.wrap(narration,width=29);caption='\n'.join(lines);cf=ImageFont.truetype(FONT,48);bbox=draw.multiline_textbbox((0,0),caption,font=cf,spacing=12);cx=(w-(bbox[2]-bbox[0]))//2;box(draw,(cx,h-260),caption,cf);cp=tmp/'caption.png';cap.save(cp)
  af=f'[1:a]atempo={tempo:.6f},aresample=48000,loudnorm=I=-18:TP=-2:LRA=7,adelay=1800|1800,apad,atrim=duration=15[voice]'
  has_audio=any(s['codec_type']=='audio' for s in info['streams'])
  af+=';[0:a]aresample=48000,volume=0.10,atrim=duration=15,apad[ambient]' if has_audio else ';anullsrc=r=48000:cl=stereo,atrim=duration=15[ambient]'
  af+=';[voice][ambient]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=7,aresample=48000,atrim=duration=15[audio]'
  vf="[0:v][2:v]overlay=0:0[v1];[v1][3:v]overlay=0:0:enable='between(t,1.5,13.5)',trim=duration=15,setpts=PTS-STARTPTS[video]"
  staging=FINAL/f'{id}.working.mp4'
  run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-i',str(source),'-i',str(speech),'-loop','1','-i',str(layer),'-loop','1','-i',str(cp),'-filter_complex',vf+';'+af,'-map','[video]','-map','[audio]','-t','15','-r','24','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-map_metadata','-1','-metadata','comment=AI-generated LINGBAN concept; not manufactured hardware; Chinese narration synthesized locally; edited from native MiniMax-H3 2K 15-second source.','-movflags','+faststart',str(staging)])
  staging.replace(out)
 finfo=probe(out);fv=next(s for s in finfo['streams'] if s['codec_type']=='video');fd=float(finfo['format']['duration'])
 if abs(fd-15)>.05 or (fv['width'],fv['height'])!=(w,h):raise ValueError('Output verification failed')
 loud=subprocess.run(['ffmpeg','-hide_banner','-nostdin','-i',str(out),'-af','loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True,check=True).stderr
 measure=json.JSONDecoder().raw_decode(loud[loud.rfind('{'):])[0];write(QA/f'{id}_loudness.json',measure)
 if float(measure['input_tp'])>-.1:raise ValueError('Output peak too high')
 write(manifest,{'created_at':timestamp(),'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'source_width':w,'source_height':h,'source_duration_seconds':duration,'source_kind':'MiniMax-H3 native 2K requested-15-second AI generation','source_aigc_metadata_present':'AIGC' in info.get('format',{}).get('tags',{}),'source_signed_metadata_note':'Original provider metadata remains in unchanged source. Reencoded output does not assert original cryptographic binding.','edit':'Trim source to exact 15 seconds; no temporal padding, no resolution scaling; burn Chinese concept labels and narration captions; mix original ambience at gain 0.10 with local narration.','voice':'macOS installed Tingting; local say; no paid or downloaded voice','voice_duration_seconds':sd,'voice_tempo':tempo,'narration':narration,'output_duration_seconds':fd,'output_width':w,'output_height':h,'output_sha256':sha(out),'loudness':measure,'concept_disclaimer':'AI概念演示 · 非已生产实机','visual_review':'Contact sheet generated; inspect geometry and interaction before presenting as a concept.'})
 contact(out,id);print(json.dumps({'finished':id,'duration':fd,'size':[w,h],'loudness_lufs':measure['input_i'],'true_peak_dbtp':measure['input_tp']},ensure_ascii=False),flush=True);return True

def compilation(rows):
 paths=[FINAL/(r['id']+'.mp4') for r in rows]
 if len(paths)!=8 or not all(p.exists() for p in paths):return False
 out=FINAL/'LINGBAN_8_concepts_2min.mp4'
 if out.exists():return True
 listing=FINAL/'concat.txt';listing.write_text(''.join("file '"+p.name+"'\n" for p in paths))
 with tempfile.TemporaryDirectory(prefix='lingban-concat-') as td:
  raw=pathlib.Path(td)/'raw.mp4'
  run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-f','concat','-safe','1','-i',str(listing),'-c','copy',str(raw)])
  video_start=float(next(s for s in probe(raw)['streams'] if s['codec_type']=='video').get('start_time',0))
  run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-itsoffset',str(-video_start),'-i',str(raw),'-i',str(raw),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-af','apad','-t','120','-movflags','+faststart',str(out)])
 info=probe(out);duration=float(info['format']['duration'])
 if abs(duration-120)>.001:raise ValueError('Compilation duration mismatch')
 write(FINAL/'LINGBAN_8_concepts_2min.provenance.json',{'ordered_sources':[p.name for p in paths],'duration_seconds':duration,'sha256':sha(out),'labels':'All source segments retain burned AI concept and non-production hardware disclosures.'});return True

def report(rows):
 ready=[r for r in rows if (FINAL/(r['id']+'.mp4')).exists()];missing=[r['id'] for r in rows if r not in ready]
 lines=['# 灵伴 LINGBAN 视频交付','',f'本地后期完成 **{len(ready)}/8** 条。更新时间：{timestamp()}。','', '全部成片来自MiniMax-H3原生2560×1440、请求15秒的AI概念片；原片实际约15.08秒，后期裁为精确15秒，无放大、无补静帧。不得作为已量产/已验证实机证据。','', '统一常驻中文标签「AI概念演示 · 非已生产实机」，中文旁白及字幕由macOS已有婷婷声线本地合成，不下载、不调用付费语音；原片环境音以0.10增益混入，成片测量音量见qa/*_loudness.json。源AI生成标记保留于未修改原片，重编码成片不冒称原始签名仍有效。','', '| 成片 | 时长/尺寸 | QA |','|---|---|---|']
 for r in ready:lines.append(f"| [ {r['title']} ](final/{r['id']}.mp4) | 15秒 / 2560×1440 | [联系表](qa/{r['id']}_contact.jpg)、[来源记录](final/{r['id']}.provenance.json) |")
 if missing:lines+=['','待下载或处理：'+', '.join(missing)]
 if (FINAL/'LINGBAN_8_concepts_2min.mp4').exists():lines+=['','[按01–08排序的2分钟合集](final/LINGBAN_8_concepts_2min.mp4)']
 lines+=['','复现：`python3 media/final/produce.py`（从项目根运行，处理已下载且尚未成片的全部视频，八条齐备后自动合并）；单条 `--id 03_keyboard_sidecar`；最多监看30分钟 `--watch-seconds 1800`。此脚本只读requests与generated，不接触API/Key/账本，不能付费重做。','', '字幕语义仅为概念叙事，屏幕数据为合成示意；健康仅休息/舒适度建议。原片动作或几何可能存在生成误差，抽帧不等同于真实硬件或功能验证。']
 (ROOT/'VIDEO_DELIVERY.md').write_text('\n'.join(lines)+'\n')
def main():
 p=argparse.ArgumentParser();p.add_argument('--id');p.add_argument('--watch-seconds',type=int,default=0);a=p.parse_args()
 if not 0<=a.watch_seconds<=1800:p.error('Watch bounded to 0..1800 seconds')
 rows=json.loads((ROOT/'requests.json').read_text());deadline=time.monotonic()+a.watch_seconds
 while True:
  for row in rows:
   if not a.id or row['id']==a.id:produce(row)
  complete=compilation(rows);report(rows)
  if complete or not a.watch_seconds or time.monotonic()>=deadline:break
  time.sleep(min(15,max(0,deadline-time.monotonic())))
if __name__=='__main__':main()
