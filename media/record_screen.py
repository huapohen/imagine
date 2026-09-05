#!/usr/bin/env python3
"""Record an explicitly selected macOS screen. Never capture microphone audio."""
import argparse,pathlib,subprocess,json
p=argparse.ArgumentParser();p.add_argument('--list',action='store_true');p.add_argument('--screen-index',type=int);p.add_argument('--output',type=pathlib.Path);p.add_argument('--seconds',type=int,default=15);a=p.parse_args()
if a.list:
 subprocess.run(['ffmpeg','-hide_banner','-f','avfoundation','-list_devices','true','-i','']);raise SystemExit(0)
if a.screen_index is None or not a.output or not 1<=a.seconds<=60: p.error('Use --list, then set explicit screen index/output; seconds 1..60')
a.output.parent.mkdir(parents=True,exist_ok=True)
subprocess.run(['ffmpeg','-hide_banner','-nostdin','-n','-f','avfoundation','-framerate','30','-capture_cursor','1','-i',str(a.screen_index)+':none','-t',str(a.seconds),'-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(a.output)],check=True,timeout=a.seconds+15)
a.output.with_suffix('.recording.json').write_text(json.dumps({'type':'actual_mac_screen_recording','audio_captured':False,'screen_index':a.screen_index,'seconds':a.seconds,'note':'Verify screen contains only intended local synthetic demo before distribution'},indent=2))
