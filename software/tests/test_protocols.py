import json
import os
from pathlib import Path
import subprocess
import unittest
from lingban.core import Store, Problem
from lingban.mcp import MCP
from lingban.protocols import A2A, agent_card
from lingban.serial_protocol import crc16, encode, decode, Simulator

class FakeClient:
    def call(self,path,data=None):
        if path=='/api/state':return {'tasks':[]}
        raise Problem(403,'角色无权访问')

class MCPTests(unittest.TestCase):
    def setUp(self):self.m=MCP(FakeClient())
    def req(self,method,params=None):return self.m.handle({'jsonrpc':'2.0','id':1,'method':method,'params':params or {}})
    def init(self):
        result=self.req('initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'test','version':'1'}})
        self.assertEqual(result['result']['protocolVersion'],'2025-06-18')
        self.assertIsNone(self.m.handle({'jsonrpc':'2.0','method':'notifications/initialized'}))
    def test_handshake_enforced_and_list(self):
        self.assertEqual(self.req('tools/list')['error']['code'],-32002);self.init();self.assertEqual(len(self.req('tools/list')['result']['tools']),4)
        self.assertEqual(self.req('initialize')['error']['code'],-32600)
    def test_initialized_notification_required(self):
        self.req('initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'t','version':'1'}})
        self.assertIn('error',self.req('tools/list'))
    def test_protocol_and_tool_errors(self):
        self.assertEqual(self.m.handle([])['error']['code'],-32600);self.init()
        self.assertEqual(self.req('unknown')['error']['code'],-32601)
        self.assertEqual(self.req('tools/call',{'name':'unknown'})['error']['code'],-32602)
        self.assertFalse(self.req('tools/call',{'name':'tasks_list'})['result']['isError'])
        self.assertTrue(self.req('tools/call',{'name':'enterprise_summary'})['result']['isError'])
        self.assertEqual(self.req('tools/call',{'name':'tasks_list','arguments':{'owner':'bob'}})['error']['code'],-32602)
    def test_stdio_actual_process_parse_errors_and_framing(self):
        requests=[b'{broken\n',json.dumps({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'test','version':'1'}}}).encode()+b'\n',b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n',b'{"jsonrpc":"2.0","id":2,"method":"tools/list"}\n',b'x'*33000+b'\n',b'{"jsonrpc":"2.0","id":3,"method":"ping"}\n']
        # Child gets only explicit local demo token, no credential discovery.
        run=subprocess.run([os.sys.executable,'-m','lingban.mcp'],input=b''.join(requests),stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={'PATH':'/usr/bin:/bin','LINGBAN_TOKEN':'synthetic-test-token'},cwd=Path(__file__).resolve().parents[1],timeout=5)
        self.assertEqual(run.returncode,0,run.stderr);rows=[json.loads(x) for x in run.stdout.splitlines()]
        self.assertEqual(len(rows),5);self.assertEqual(rows[0]['error']['code'],-32700);self.assertEqual(rows[3]['error']['code'],-32600);self.assertEqual(rows[4]['result'],{})

class A2ATests(unittest.TestCase):
    def setUp(self):
        self.s=Store();self.a=self.s.person('a');self.b=self.s.person('b');self.a2a=A2A(self.s)
    def tearDown(self):self.s.close()
    def send(self,params=None,p=None):
        return self.a2a.handle(p or self.a,{'jsonrpc':'2.0','id':'req','method':'message/send','params':params or {'message':{'kind':'message','role':'user','messageId':'mid','parts':[{'kind':'text','text':'合成摘要'}]}}})
    def test_lifecycle_persistence_ownership_and_retries(self):
        task=self.send()['result'];self.assertEqual(task['status']['state'],'completed');self.assertEqual(task['kind'],'task')
        self.assertEqual(self.send()['result']['id'],task['id'])
        got=self.a2a.get(self.a,{'id':task['id'],'historyLength':0});self.assertEqual(got['history'],[])
        with self.assertRaises(Problem):self.a2a.get(self.b,{'id':task['id']})
        audit=[a['kind'] for a in self.s.state(self.a)['audit'] if a['kind'].startswith('a2a.')]
        self.assertEqual(audit,['a2a.completed','a2a.working','a2a.submitted'])
    def test_a2a_errors(self):
        self.assertEqual(self.a2a.handle(self.a,[])['error']['code'],-32600)
        self.assertEqual(self.a2a.handle(self.a,{'jsonrpc':'2.0','id':1,'method':'tasks/cancel'})['error']['code'],-32601)
        self.assertEqual(self.a2a.handle(self.a,{'jsonrpc':'2.0','id':1,'method':'tasks/get','params':{'id':'unknown'}})['error']['code'],-32001)
        m={'kind':'message','role':'user','messageId':'file','parts':[{'kind':'file','file':{'uri':'https://example.invalid/private'}}]}
        self.assertEqual(self.send({'message':m})['error']['code'],-32005)
        m['parts']=[{'kind':'text','text':'合成'}]
        self.assertEqual(self.send({'message':m,'configuration':{'blocking':False}})['error']['code'],-32602)
    def test_official_schema_required_fields(self):
        schema=json.loads((Path(__file__).resolve().parents[1]/'reference/a2a-v0.3.0.json').read_text())['definitions']
        def check(name,value):
            for k in schema[name].get('required',[]):self.assertIn(k,value,name)
            for k,v in value.items():
                prop=schema[name]['properties'].get(k,{})
                if 'const' in prop:self.assertEqual(v,prop['const'])
                if 'enum' in prop:self.assertIn(v,prop['enum'])
        check('AgentCard',agent_card('http://127.0.0.1:8765'));task=self.send()['result'];check('Task',task);check('TaskStatus',task['status'])
        for m in task['history']:check('Message',m)

class SerialTests(unittest.TestCase):
    def test_crc_and_corruption(self):
        self.assertEqual(crc16(b'123456789'),0x29b1)
        f=encode(1,'HELLO','versions=1');self.assertEqual(decode(f),(1,'HELLO','versions=1'))
        for damaged in (f.replace(b'1|HELLO',b'2|HELLO'),f[:-1],b'x'*300,b'LB1|01|GET||1234\n'):
            with self.assertRaises(ValueError):decode(damaged)
    def test_negotiation_dedup_and_privacy(self):
        s=Simulator();self.assertIn(b'handshake_required',s.receive(encode(1,'SET','led=teal')))
        self.assertIn(b'version',s.receive(encode(2,'HELLO','versions=2')))
        s.receive(encode(3,'HELLO','versions=1'));f=encode(4,'SET','led=teal');self.assertEqual(s.receive(f),s.receive(f));self.assertEqual(s.applied,1)
        self.assertIn(b'sequence_conflict',s.receive(encode(4,'SET','led=amber')))
        s.physical_touch(True);s.physical_privacy(True);self.assertFalse(s.touch);self.assertEqual(s.led,'off')
        self.assertIn(b'privacy_active',s.receive(encode(5,'SET','led=amber')))
        self.assertIsNone(s.receive(b'bad\n'))
    def test_reconnect_with_new_session(self):
        s=Simulator();s.receive(encode(1,'HELLO','versions=1;session=aaaaaaaaaaaaaaaa'));s.receive(encode(2,'SET','led=teal'))
        self.assertEqual(decode(s.receive(encode(1,'HELLO','versions=1;session=bbbbbbbbbbbbbbbb')))[1],'CAPS')
        self.assertEqual(decode(s.receive(encode(2,'SET','led=amber')))[1],'ACK');self.assertEqual(s.led,'amber')
    def test_bad_fields_and_size(self):
        s=Simulator();s.receive(encode(1,'HELLO','versions=1'))
        for n,payload in enumerate(('led=teal;led=blue','text=abc','privacy=0','text=zz','led=purple'),2):self.assertEqual(decode(s.receive(encode(n,'SET',payload)))[1],'ERR')
        with self.assertRaises(ValueError):encode(2,'SET','text='+'a'*300)
    def test_cpp_python_protocol_interop(self):
        root=Path(__file__).resolve().parents[2];binary=root/'firmware/build/protocol_test'
        if not binary.exists():self.skipTest('先运行 firmware/test.sh 以启用 C++ 交叉验证')
        frames=[encode(1,'HELLO','versions=1'),encode(2,'SET','led=teal;text=e781b5e4bcb4'),encode(2,'SET','led=teal;text=e781b5e4bcb4'),encode(3,'GET'),encode(4,'SET','text=abc'),encode(5,'GET','bad=1'),encode(1,'HELLO','versions=1;session=cccccccccccccccc'),encode(2,'SET','led=blue')]
        result=subprocess.run([str(binary),'--echo'],input=b''.join(frames),stdout=subprocess.PIPE,check=True,timeout=5)
        replies=result.stdout.splitlines(keepends=True);s=Simulator()
        for i,(frame,reply) in enumerate(zip(frames,replies)):
            decode(reply)
            if i and decode(frame)[1]!='HELLO': self.assertEqual(reply,s.receive(frame))
            else:s.receive(frame);self.assertEqual(decode(reply)[1],'CAPS')
        self.assertEqual(len(replies),len(frames))

class IntegrationProtocolTests(unittest.TestCase):
    def test_shared_frozen_golden_vectors(self):
        import csv
        root=Path(__file__).resolve().parents[2]
        rows=list(csv.reader((root/'docs/software/serial-golden-vectors.tsv').read_text().splitlines(),delimiter='\t'))
        s=None;count=0
        for row in rows:
            if not row or row[0].startswith('#'):continue
            name,op,stamp,arg,expected=row;now=int(stamp)/1000
            if op=='RESET':s=Simulator(clock=lambda:0,privacy=True,simulated=False);out=s.status().encode()
            elif op=='PRIVACY':s.physical_privacy(arg=='1');out=s.status().encode()
            elif op=='TOUCH':s.physical_touch(arg=='1');out=s.status().encode()
            elif op=='POLL':s.poll(now);out=s.status().encode()
            else:out=s.receive(bytes.fromhex(arg),now) or b''
            self.assertEqual(out,b'' if expected=='-' else bytes.fromhex(expected),name);count+=1
        self.assertEqual(count,104)
        binary=root/'firmware/build/protocol_test'
        self.assertTrue(binary.exists(),'先运行 software/test.sh 构建 C++ golden runner')
        run=subprocess.run([str(binary),'--golden',str(root/'docs/software/serial-golden-vectors.tsv')],capture_output=True,text=True,timeout=5)
        self.assertEqual(run.returncode,0,run.stderr);self.assertIn('104 rows',run.stdout)
    def test_mock_hal_controller_binary(self):
        binary=Path(__file__).resolve().parents[2]/'firmware/build/controller_test'
        self.assertTrue(binary.exists(),'先运行 software/test.sh 构建 mock HAL')
        run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=5)
        self.assertEqual(run.returncode,0,run.stderr);self.assertIn('controller mock HAL PASS',run.stdout)
    def test_a2a_content_errors_match_official_030(self):
        schema=json.loads((Path(__file__).resolve().parents[1]/'reference/a2a-v0.3.0.json').read_text())['definitions']
        code=schema['ContentTypeNotSupportedError']['properties']['code']['const']
        self.assertEqual(code,-32005)
        store=Store();p=store.person('content-test');a=A2A(store)
        try:
            for kind in ('file','data'):
                request={'jsonrpc':'2.0','id':1,'method':'message/send','params':{'message':{'kind':'message','role':'user','messageId':kind,'parts':[{'kind':kind,kind:{}}]}}}
                self.assertEqual(a.handle(p,request)['error']['code'],code)
            request['params']['message']['parts']=[{'kind':'text','text':'合成'}]
            request['params']['configuration']={'acceptedOutputModes':['application/json']}
            self.assertEqual(a.handle(p,request)['error']['code'],code)
        finally:store.close()
