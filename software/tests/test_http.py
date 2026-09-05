import concurrent.futures
import http.client
import json
import os
from pathlib import Path
import subprocess
import threading
import time
import unittest
from lingban.core import Store
from lingban.server import Server

class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=Store();cls.tokens=cls.s.seed();cls.b=cls.s.person('bob');cls.btoken=cls.s.issue_token('bob')
        cls.server=Server(('127.0.0.1',0),cls.s);cls.port=cls.server.server_port
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start();cls.server.worker.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.worker.stop();cls.server.shutdown();cls.server.server_close();cls.thread.join();cls.s.close()
    def request(self,path,body=None,token='employee',headers=None,raw=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
        h={}
        if token: h['Authorization']='Bearer '+self.tokens.get(token,token)
        if body is not None or raw is not None:h['Content-Type']='application/json'
        h.update(headers or {})
        conn.request('POST' if body is not None or raw is not None else 'GET',path,body=raw if raw is not None else None if body is None else json.dumps(body),headers=h)
        response=conn.getresponse();data=response.read();status=response.status;rh=dict(response.getheaders());conn.close()
        try:data=json.loads(data)
        except ValueError:pass
        return status,data,rh
    def test_health_assets_csp_static_path_and_no_tokens(self):
        status,data,headers=self.request('/',token=None);self.assertEqual(status,200);self.assertIn('script-src',headers['Content-Security-Policy']);self.assertIn('合成'.encode(),data)
        for path in ('/../lingban/core.py','/%2e%2e/lingban/core.py','/data/lingban.sqlite3','/.env','/web/../../AGENTS.md'):
            status,_,_=self.request(path);self.assertEqual(status,404,path)
        self.assertEqual(self.request('/health',token=None)[0],200)
    def test_missing_invalid_token_and_cross_origin(self):
        self.assertEqual(self.request('/api/state',token=None)[0],401)
        self.assertEqual(self.request('/api/state',token='invalid')[0],401)
        self.assertEqual(self.request('/api/state',headers={'Origin':'https://evil.example'})[0],403)
        self.assertEqual(self.request('/api/state',headers={'Host':'evil.example'})[0],403)
        self.assertEqual(self.request('/api/state',headers={'Sec-Fetch-Site':'cross-site'})[0],403)
    def test_employee_enterprise_server_enforcement(self):
        for path,body in [('/api/state',None),('/api/events',{'idempotency_key':'e','type':'task.upsert','payload':{'id':'e','title':'blocked'}}),('/api/actions',{'title':'x','body':'y'}),('/api/consent',{'enabled':True}),('/api/hardware',{'led':'teal'}),('/api/scenarios',{'name':'meeting'}),('/api/plugins',{'id':'e','name':'e','version':'1','permissions':[]})]:
            self.assertEqual(self.request(path,body,token='enterprise')[0],403,path)
        self.assertEqual(self.request('/api/enterprise/summary')[0],403)
        self.assertEqual(self.request('/api/enterprise/summary',token='enterprise')[0],200)
    def test_input_limits_invalid_json_and_unknown_fields(self):
        self.assertEqual(self.request('/api/events',raw=b'x'*32769)[0],413)
        self.assertEqual(self.request('/api/events',raw=b'{broken')[0],400)
        self.assertEqual(self.request('/api/events',raw=b'[]')[0],400)
        self.assertEqual(self.request('/api/events',raw=b'{}',headers={'Content-Type':'text/plain'})[0],415)
        self.assertEqual(self.request('/api/events',{'idempotency_key':'bad','type':'task.upsert','owner':'bob','payload':{}})[0],400)
    def test_event_worker_and_idempotency_over_http(self):
        body={'idempotency_key':'http-one','type':'task.upsert','payload':{'id':'http-task','title':'合成 HTTP 阻塞','state':'blocked'}}
        one=self.request('/api/events',body)[1];two=self.request('/api/events',body)[1];self.assertEqual(one['id'],two['id']);self.assertTrue(two['duplicate'])
        deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            alerts=self.request('/api/state')[1]['alerts']
            if any(a['subject']=='http-task' for a in alerts):break
            time.sleep(.05)
        self.assertTrue(any(a['subject']=='http-task' for a in alerts))
        self.assertFalse(any(t['id']=='http-task' for t in self.request('/api/state',token=self.btoken)[1]['tasks']))
    def test_concurrent_approval_http_and_cross_owner_denied(self):
        act=self.request('/api/actions',{'title':'合成审批','body':'保存，不外发'})[1]
        self.assertEqual(self.request('/api/actions/decide',{'id':act['id'],'decision':'approve'},token=self.btoken)[0],404)
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            replies=list(pool.map(lambda _:self.request('/api/actions/decide',{'id':act['id'],'decision':'approve'}),range(8)))
        self.assertTrue(all(r[0]==200 for r in replies));self.assertEqual(sum(not r[1]['duplicate'] for r in replies),1)
        outbox=self.request('/api/state')[1]['outbox'];self.assertEqual(sum(r['action']==act['id'] for r in outbox),1)
    def test_plugin_cannot_omit_scope_or_use_privileged_endpoints(self):
        m={'id':'http-calendar','name':'合成日历','version':'1','permissions':['events:write'],'event_types':['meeting.upsert']}
        self.assertEqual(self.request('/api/plugins',m)[0],200)
        plugin=self.request('/api/plugins/token',{'id':m['id']})[1]['token']
        self.assertEqual(self.request('/api/state',token=plugin)[0],403)
        self.assertEqual(self.request('/api/actions',{'title':'逃逸','body':'禁止'},token=plugin)[0],403)
        self.assertEqual(self.request('/api/events',{'idempotency_key':'pe','type':'task.upsert','payload':{'id':'escape','title':'越权'}},token=plugin)[0],403)
        self.assertEqual(self.request('/api/events',{'idempotency_key':'pm','type':'meeting.upsert','payload':{'id':'allowed','title':'允许的合成日程'}},token=plugin)[0],200)
        self.assertEqual(self.request('/api/events',{'idempotency_key':'spoof','plugin_id':'another','type':'meeting.upsert','payload':{'id':'spoof','title':'身份冒用'}},token=plugin)[0],403)
    def test_a2a_wire_errors_card_and_lifecycle(self):
        self.assertEqual(self.request('/.well-known/agent-card.json',token=None)[1]['protocolVersion'],'0.3.0')
        self.assertEqual(self.request('/a2a',raw=b'{')[1]['error']['code'],-32700)
        req={'jsonrpc':'2.0','id':1,'method':'message/send','params':{'message':{'kind':'message','role':'user','messageId':'http-a2a','parts':[{'kind':'text','text':'摘要'}]}}}
        task=self.request('/a2a',req)[1]['result'];self.assertEqual(task['status']['state'],'completed')
        get={'jsonrpc':'2.0','id':2,'method':'tasks/get','params':{'id':task['id']}}
        self.assertEqual(self.request('/a2a',get)[1]['result']['id'],task['id'])
        self.assertEqual(self.request('/a2a',get,token=self.btoken)[1]['error']['code'],-32001)
        self.assertEqual(self.request('/a2a',get,token='enterprise')[1]['error']['code'],-32001)
    def test_mcp_stdio_calls_real_http_auth(self):
        messages=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'live-test','version':'1'}}},{'jsonrpc':'2.0','method':'notifications/initialized'},{'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'tasks_list'}},{'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'enterprise_summary'}}]
        process=subprocess.run([os.sys.executable,'-m','lingban.mcp','--url','http://127.0.0.1:'+str(self.port)],input='\n'.join(json.dumps(x) for x in messages)+'\n',capture_output=True,text=True,timeout=5,cwd=Path(__file__).resolve().parents[1],env={'PATH':'/usr/bin:/bin','LINGBAN_TOKEN':self.tokens['employee']})
        self.assertEqual(process.returncode,0,process.stderr);rows=[json.loads(x) for x in process.stdout.splitlines()]
        self.assertFalse(rows[1]['result']['isError']);self.assertTrue(rows[2]['result']['isError'])

    def test_serial_bridge_simulator_to_real_http(self):
        process=subprocess.run([os.sys.executable,'-m','lingban.serial_protocol','--url','http://127.0.0.1:'+str(self.port),'--once'],capture_output=True,text=True,timeout=5,cwd=Path(__file__).resolve().parents[1],env={'PATH':'/usr/bin:/bin','LINGBAN_TOKEN':self.tokens['employee']})
        self.assertEqual(process.returncode,0,process.stderr)
        rows=[json.loads(x) for x in process.stdout.splitlines()]
        self.assertEqual(rows[0]['capabilities']['version'],'1');self.assertTrue(rows[1]['simulated'])
        self.assertIn('led',rows[1]['state']);self.assertNotIn(self.tokens['employee'],process.stdout)

    def test_nonlocal_bind_requires_explicit_opt_in(self):
        result=subprocess.run([os.sys.executable,'-m','lingban.server','--host','0.0.0.0'],capture_output=True,text=True,timeout=5,cwd=Path(__file__).resolve().parents[1],env={'PATH':'/usr/bin:/bin'})
        self.assertEqual(result.returncode,2);self.assertIn('--allow-network',result.stderr)
