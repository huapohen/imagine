"""Hardware-neutral negotiated ASCII protocol, CRC16-CCITT-FALSE. No dependencies."""
import argparse
from collections import OrderedDict
import json
import os
import re
import select
import secrets
import sys
import time
from .mcp import Client

MAX_FRAME=256
TYPES={'HELLO','CAPS','SET','GET','STATE','ACK','ERR','PING'}

def crc16(data):
    crc=0xffff
    for byte in data:
        crc^=byte<<8
        for _ in range(8): crc=((crc<<1)^0x1021)&0xffff if crc&0x8000 else (crc<<1)&0xffff
    return crc

def encode(seq,kind,payload=''):
    if type(seq)!=int or not 1<=seq<=65535 or kind not in TYPES: raise ValueError('invalid header')
    if not re.fullmatch(r'[A-Za-z0-9_=;,.-]*',payload): raise ValueError('invalid payload')
    base=f'LB1|{seq}|{kind}|{payload}'.encode('ascii')
    frame=base+f'|{crc16(base):04X}\n'.encode()
    if len(frame)>MAX_FRAME: raise ValueError('frame too long')
    return frame

def decode(frame):
    if not isinstance(frame,bytes) or len(frame)>MAX_FRAME or not frame.endswith(b'\n'): raise ValueError('invalid framing')
    try:
        raw=frame[:-1].decode('ascii'); parts=raw.split('|')
        if len(parts)!=5 or parts[0]!='LB1' or not re.fullmatch(r'[1-9][0-9]{0,4}',parts[1]) or not re.fullmatch(r'[0-9A-F]{4}',parts[4]): raise ValueError('invalid header')
        seq=int(parts[1]); kind=parts[2]; payload=parts[3]
        if encode(seq,kind,payload)!=frame: raise ValueError('checksum or canonical framing mismatch')
        return seq,kind,payload
    except (UnicodeError,ValueError): raise ValueError('invalid frame or CRC')

def fields(payload):
    out={}
    if not payload: return out
    for pair in payload.split(';'):
        if pair.count('=')!=1: raise ValueError('fields')
        k,v=pair.split('=')
        if not k or k in out: raise ValueError('fields')
        out[k]=v
    return out

def valid_utf8hex(value):
    if len(value)>160 or len(value)%2 or not re.fullmatch('[0-9a-f]*',value): return False
    try: bytes.fromhex(value).decode('utf-8',errors='strict'); return True
    except (ValueError,UnicodeError): return False

class Simulator:
    def __init__(self,clock=time.monotonic,privacy=False,simulated=True,capabilities=None):
        self.clock=clock; self.ready=False; self.privacy=privacy; self.led='off'; self.screen=''; self.touch=False
        self.cache=OrderedDict(); self.applied=0; self.session=''; self.last_heartbeat=0
        self.simulated=simulated; self.capabilities=capabilities or dict(led=True,touch=True,privacy=True,screen=True)
    def clear_outputs(self): self.led='off'; self.screen=''; self.touch=False
    def poll(self,now=None):
        now=self.clock() if now is None else now
        if self.ready and now-self.last_heartbeat>=5:
            self.ready=False; self.session=''; self.cache.clear(); self.clear_outputs()
    def physical_privacy(self,value):
        value=bool(value)
        if self.privacy!=value: self.cache.clear(); self.clear_outputs()
        self.privacy=value
        if value: self.clear_outputs()
    def physical_touch(self,value): self.touch=bool(value) and not self.privacy and self.ready
    def status(self): return f'link={"online" if self.ready else "offline"};led={self.led};privacy={int(self.privacy)};touch={int(self.touch)};text={self.screen}'
    def receive(self,frame,now=None):
        now=self.clock() if now is None else now; self.poll(now)
        try: seq,kind,payload=decode(frame)
        except ValueError: return None
        try: data=fields(payload); parsed=True
        except ValueError: data={}; parsed=False
        hello=(parsed and data.get('versions')=='1' and set(data)<={'versions','session'} and ('session' not in data or bool(re.fullmatch('[0-9a-f]{16}',data['session']))))
        if kind=='HELLO' and hello:
            session=data.get('session','')
            if not self.ready or session!=self.session:
                self.cache.clear(); self.clear_outputs(); self.session=session; self.ready=False
        if seq in self.cache:
            old,response=self.cache[seq]
            if frame!=old: return encode(seq,'ERR','code=sequence_conflict')
            if not (kind in ('GET','PING') and parsed and not data): return response
        try:
            if not parsed: raise ValueError('fields')
            if kind=='HELLO':
                if not hello: raise ValueError('version')
                self.ready=True; self.last_heartbeat=now
                response=encode(seq,'CAPS','version=1;'+ ';'.join(f'{k}={int(self.capabilities[k])}' for k in ('led','touch','privacy','screen'))+f';simulated={int(self.simulated)}')
            elif kind in ('GET','PING'):
                if data: raise ValueError('fields')
                if self.ready: self.last_heartbeat=now
                response=encode(seq,'STATE',self.status()) if kind=='GET' else encode(seq,'ACK',f'alive={int(self.ready)}')
            elif kind=='SET':
                if not self.ready: raise ValueError('handshake_required')
                if self.privacy: raise ValueError('privacy_active')
                if not data or not set(data)<={'led','text'}: raise ValueError('fields')
                if 'led' in data and data['led'] not in ('off','teal','amber','blue'): raise ValueError('led')
                if 'text' in data and not valid_utf8hex(data['text']): raise ValueError('text')
                self.led=data.get('led',self.led); self.screen=data.get('text',self.screen); self.applied+=1
                response=encode(seq,'ACK','applied=1')
            else: raise ValueError('unsupported')
        except ValueError as e: response=encode(seq,'ERR','code='+str(e))
        self.cache[seq]=(frame,response)
        if len(self.cache)>16: self.cache.popitem(last=False)
        return response

class PosixSerial:
    def __init__(self,path):
        import termios
        if not path.startswith('/dev/'): raise ValueError('设备路径必须显式为 /dev/...')
        self.fd=os.open(path,os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK)
        self.termios=termios; self.old=termios.tcgetattr(self.fd)
        attrs=termios.tcgetattr(self.fd); attrs[0]=0; attrs[1]=0; attrs[2]=termios.CS8|termios.CREAD|termios.CLOCAL; attrs[3]=0; attrs[4]=termios.B115200; attrs[5]=termios.B115200; attrs[6][termios.VMIN]=0; attrs[6][termios.VTIME]=0
        termios.tcsetattr(self.fd,termios.TCSANOW,attrs); self.buf=b''
    def exchange(self,frame):
        wanted=decode(frame)[0]
        for _ in range(3):
            pending=frame; deadline=time.monotonic()+1
            while pending and time.monotonic()<deadline:
                if select.select([], [self.fd], [], .1)[1]: pending=pending[os.write(self.fd,pending):]
            if pending: raise TimeoutError('serial write timeout')
            while time.monotonic()<deadline:
                if select.select([self.fd],[],[],.1)[0]: self.buf+=os.read(self.fd,512)
                while b'\n' in self.buf:
                    line,self.buf=self.buf.split(b'\n',1)
                    try:
                        result=decode(line+b'\n')
                        if result[0]==wanted: return line+b'\n'
                    except ValueError: pass
                if len(self.buf)>512: self.buf=b''
        raise TimeoutError('serial reply timeout after 3 identical retries')
    def close(self):
        self.termios.tcsetattr(self.fd,self.termios.TCSANOW,self.old); os.close(self.fd)

def main():
    parser=argparse.ArgumentParser(description='灵伴串口协议模拟器 / 显式设备桥')
    parser.add_argument('--device',help='显式 /dev/...；未指定时只使用模拟器，不扫描硬件')
    parser.add_argument('--url',default='http://127.0.0.1:8765')
    parser.add_argument('--once',action='store_true'); parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.self_test:
        s=Simulator(); assert crc16(b'123456789')==0x29b1
        assert decode(s.receive(encode(1,'HELLO','versions=1')))[1]=='CAPS'
        frame=encode(2,'SET','led=teal;text=e781b5e4bcb4')
        assert s.receive(frame)==s.receive(frame) and s.applied==1
        s.physical_privacy(True); assert decode(s.receive(encode(3,'SET','led=amber')))[1]=='ERR'
        print('serial self-test PASS: CRC, negotiation, retry, privacy'); return
    token=os.environ.get('LINGBAN_TOKEN','')
    if not token: parser.error('请显式传入 LINGBAN_TOKEN；不会读取 .env 或自动发现凭据')
    api=Client(args.url,token); serial=PosixSerial(args.device) if args.device else None; sim=Simulator(); seq=0
    def exchange(kind,payload=''):
        nonlocal seq
        seq=seq%65535+1
        reply=serial.exchange(encode(seq,kind,payload)) if serial else sim.receive(encode(seq,kind,payload))
        if reply is None: raise TimeoutError('no reply')
        result=decode(reply)
        if result[1]=='ERR': raise ValueError(result[2])
        return fields(result[2])
    try:
        caps=exchange('HELLO','versions=1;session='+secrets.token_hex(8)); print(json.dumps({'capabilities':caps,'simulated':serial is None},ensure_ascii=False),flush=True)
        if caps.get('version')!='1': raise ValueError('unsupported negotiated version')
        while True:
            state=api.call('/api/state')['hardware']
            if not serial: sim.physical_privacy(state['privacy']); sim.physical_touch(state['touch'])
            current=exchange('GET')
            if current.get('link')=='offline':
                exchange('HELLO','versions=1;session='+secrets.token_hex(8))
                current=exchange('GET')
            if serial:
                api.call('/api/hardware',{'privacy':current.get('privacy')=='1','touch':current.get('touch')=='1'})
            if current.get('privacy')!='1':
                # Screen payload is at most 80 bytes; truncate at UTF-8 character boundary.
                screen=state['screen'].encode()[:80].decode('utf-8','ignore').encode().hex()
                led=state['led'] if state['led'] in ('off','teal','amber','blue') else 'off'
                exchange('SET','led='+led+';text='+screen)
            print(json.dumps({'state':exchange('GET'),'simulated':serial is None},ensure_ascii=False),flush=True)
            if args.once: break
            time.sleep(1)
    except KeyboardInterrupt: pass
    finally:
        if serial: serial.close()

if __name__=='__main__': main()
