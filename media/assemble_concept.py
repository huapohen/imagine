#!/usr/bin/env python3
"""Burn honest labels, optional still tail + narration into an exact 15s film."""
import argparse, hashlib, json, pathlib, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont
FONT='/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
def run(args): subprocess.run(args,check=True)
def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],text=True))
def main():
    p=argparse.ArgumentParser();p.add_argument('--video',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--still',type=pathlib.Path);p.add_argument('--voiceover',type=pathlib.Path);p.add_argument('--title',default='灵伴 LINGBAN');p.add_argument('--software-recording',action='store_true');a=p.parse_args()
    info=probe(a.video);v=next(s for s in info['streams'] if s['codec_type']=='video');w,h=v['width'],v['height'];duration=float(info['format']['duration'])
    if duration<14.9 and not a.still: raise ValueError('Clip shorter than 15s: provide --still, never silently clone a frame')
    if a.video.resolve()==a.output.resolve():raise ValueError('Preserve original input')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='lingban-edit-') as td:
        temp=pathlib.Path(td); layer=Image.new('RGBA',(w,h));draw=ImageDraw.Draw(layer);fs=max(18,int(h*.026));font=ImageFont.truetype(FONT,fs);margin=int(w*.025)
        label='软件实录 · 合成演示数据' if a.software_recording else 'AI概念演示 · 非已生产实机'
        for y,text in [(margin,label),(h-margin-fs*2,a.title+'  |  功能/外观待工程验证')]:
            box=draw.textbbox((margin,y),text,font=font);draw.rounded_rectangle((box[0]-10,box[1]-7,box[2]+10,box[3]+7),radius=8,fill=(10,18,30,215));draw.text((margin,y),text,font=font,fill='white')
        overlay=temp/'labels.png';layer.save(overlay)
        cmd=['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-i',str(a.video)]
        filters=[];current='0:v';index=1
        if duration<14.9:
            cmd+=['-loop','1','-i',str(a.still)];tail=15-duration
            filters += [f'[0:v]trim=duration={duration},setpts=PTS-STARTPTS,fps=30,setsar=1[v0]',f'[{index}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,trim=duration={tail},setpts=PTS-STARTPTS,fps=30,setsar=1[v1]','[v0][v1]concat=n=2:v=1:a=0[base]'];current='base';index+=1
        cmd+=['-loop','1','-i',str(overlay)];filters.append(f'[{current}][{index}:v]overlay=0:0:shortest=1,trim=duration=15,setpts=PTS-STARTPTS[outv]');index+=1
        if a.voiceover:
            cmd+=['-i',str(a.voiceover)];filters.append(f'[{index}:a]apad,atrim=duration=15[outa]')
        else:
            cmd+=['-f','lavfi','-i','anullsrc=r=48000:cl=stereo'];filters.append(f'[{index}:a]atrim=duration=15[outa]')
        cmd+=['-filter_complex',';'.join(filters),'-map','[outv]','-map','[outa]','-t','15','-r','30','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart',str(a.output)];run(cmd)
    final=probe(a.output);fv=next(s for s in final['streams'] if s['codec_type']=='video');fd=float(final['format']['duration'])
    assert abs(fd-15)<.12 and (fv['width'],fv['height'])==(w,h)
    a.output.with_suffix('.provenance.json').write_text(json.dumps({'source':str(a.video),'source_duration_seconds':duration,'source_sha256':hashlib.sha256(a.video.read_bytes()).hexdigest(),'still':str(a.still) if a.still else None,'source_type':'actual_software_recording' if a.software_recording else 'AI_generated_concept','output_duration_seconds':fd,'width':w,'height':h,'native_15s_ai_claim':not a.software_recording and duration>=14.9,'label':label,'voiceover':str(a.voiceover) if a.voiceover else None,'output_sha256':hashlib.sha256(a.output.read_bytes()).hexdigest()},ensure_ascii=False,indent=2))
    print(json.dumps({'output':str(a.output),'duration':fd,'width':w,'height':h}))
if __name__=='__main__':main()
