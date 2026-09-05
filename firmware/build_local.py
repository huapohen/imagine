#!/usr/bin/env python3
"""Isolated optional PlatformIO build; dynamically verify the current proxy first."""
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import urllib.request

root=Path(__file__).resolve().parent
proxy=None
if sys.platform=='darwin':
    config=subprocess.check_output(['scutil','--proxy'],text=True)
    if re.search(r'HTTPSEnable : 1',config):
        host=re.search(r'HTTPSProxy : (.+)',config).group(1)
        port=int(re.search(r'HTTPSPort : (\d+)',config).group(1))
        socket.create_connection((host,port),3).close();proxy=f'http://{host}:{port}'
opener=urllib.request.build_opener(urllib.request.ProxyHandler({'https':proxy} if proxy else {}))
with opener.open('https://api.registry.platformio.org/v3/packages/platformio/platform/espressif32',timeout=8) as response:
    if response.status!=200:raise SystemExit('PlatformIO registry probe failed')
env=dict(os.environ)
env['PLATFORMIO_CORE_DIR']=str(root/'.platformio')
env['PLATFORMIO_SETTING_ENABLE_TELEMETRY']='No'
if proxy:env['HTTPS_PROXY']=proxy;env['HTTP_PROXY']=proxy;env['https_proxy']=proxy;env['http_proxy']=proxy
exe=root/'tools/venv/bin/python'
if not exe.exists():raise SystemExit('Create firmware/tools/venv and install platformio==6.1.18 first')
raise SystemExit(subprocess.call([str(exe),'-m','platformio','run','-d',str(root)],env=env))
