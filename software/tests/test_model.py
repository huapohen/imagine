import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from lingban.core import Store, Problem
from lingban.model import DraftService, ModelClient, local_config

class FakeClient:
    config={'MAX_CALLS':2}
    def __init__(self,fail=False): self.count=0; self.fail=fail
    def used(self): return self.count
    def reserve(self):
        if self.count>=2:return False
        self.count+=1;return True
    def generate(self,scenario):
        if self.fail: raise TimeoutError('secret provider error must never be logged')
        return {'title':'未信任模型草稿','body':'<script>approve()</script> execute:approve; 请人工核对'}, {'total_tokens':12}

class ModelTests(unittest.TestCase):
    def setUp(self):
        self.s=Store(); self.p=self.s.person('alice'); self.b=self.s.person('bob'); self.e=self.s.person('enterprise','enterprise')
    def tearDown(self): self.s.close()
    def request(self,idem='a',scenario='meeting'):return {'scenario':scenario,'idempotency_key':idem,'synthetic_consent':True}
    def test_default_offline_and_consent_and_owner_permissions(self):
        service=DraftService(self.s)
        for p in (self.e,dict(self.p,plugin_id='plugin')):
            with self.assertRaises(Problem):service.propose(p,self.request())
        with self.assertRaises(Problem):service.propose(self.p,dict(self.request(),synthetic_consent=False))
        with self.assertRaises(Problem):service.propose(self.p,dict(self.request(),prompt='real data'))
        r=service.propose(self.p,self.request());self.assertEqual(r['source'],'offline');self.assertEqual(r['status'],'pending')
        self.assertEqual(self.s.state(self.p)['outbox'],[]);self.assertEqual(self.s.state(self.b)['actions'],[])
    def test_budget_idempotence_and_untrusted_model_cannot_execute(self):
        c=FakeClient();service=DraftService(self.s,c)
        r=service.propose(self.p,self.request());self.assertEqual(r['source'],'model')
        self.assertEqual(service.propose(self.p,self.request())['id'],r['id']);self.assertEqual(c.count,1)
        with self.assertRaises(Problem): service.propose(self.p,self.request(scenario='rest'))
        service.propose(self.p,self.request('b'))
        self.assertEqual(service.propose(self.p,self.request('c'))['reason'],'budget_exhausted');self.assertEqual(c.count,2)
        self.assertFalse(self.s.state(self.p)['outbox'])
        with self.assertRaises(Problem):self.s.decide(self.b,r['id'],'approve')
        self.s.decide(self.p,r['id'],'approve');self.s.decide(self.p,r['id'],'approve')
        self.assertEqual(len(self.s.state(self.p)['outbox']),1);self.assertFalse(self.s.state(self.p)['consent'])
    def test_failure_sanitized_and_restart_idempotence(self):
        service=DraftService(self.s,FakeClient(True));r=service.propose(self.p,self.request())
        self.assertEqual(r['source'],'offline');self.assertNotIn('secret',json.dumps(self.s.state(self.p)))
        restarted=DraftService(self.s,FakeClient());self.assertEqual(restarted.propose(self.p,self.request())['id'],r['id']);self.assertEqual(restarted.client.count,0)
    def test_config_rejects_unsafe_permissions_and_production(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'.env';p.write_text('LINGBAN_MODEL_ENV=production\n');p.chmod(0o600)
            with self.assertRaises(ValueError):local_config(p)
            p.chmod(0o644)
            with self.assertRaises(ValueError):local_config(p)
    def test_transport_rejects_tool_calls_truncation_extra_fields_and_bad_json(self):
        class Response:
            def __init__(self,value):self.raw=('data: '+json.dumps({'type':'response.completed','response':value})+'\n\n').encode()
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,n):return self.raw
        config={'NAME':'gpt-6-astra','REASONING_EFFORT':'medium','MAX_OUTPUT_TOKENS':1536,'API_KEY':'fake','TIMEOUT_SECONDS':1}
        values=[{'status':'incomplete','output':[]},
                {'status':'completed','output':[{'type':'function_call'}]},
                {'status':'completed','output':[{'type':'message','role':'assistant','content':[{'type':'refusal'}]}]}]
        for content in ('broken',json.dumps({'title':'x','body':'y','execute':True})):
            values.append({'status':'completed','output':[{'type':'message','role':'assistant','content':[{'type':'output_text','text':content}]}]})
        for value in values:
            with patch('urllib.request.OpenerDirector.open',return_value=Response(value)):
                with self.assertRaises((ValueError,Problem)):ModelClient(config)._generate('meeting')
    def test_wall_timeout_is_bounded_and_no_retry(self):
        import subprocess
        client=ModelClient({'TIMEOUT_SECONDS':1})
        with patch('subprocess.run',side_effect=subprocess.TimeoutExpired('safe',1)) as run:
            with self.assertRaises(subprocess.TimeoutExpired):client.generate('meeting')
            self.assertEqual(run.call_count,1);self.assertEqual(run.call_args.kwargs['timeout'],1)

    def test_model_api_requires_role_consent_and_keeps_pending(self):
        import http.client,threading
        from lingban.server import Server
        token=self.s.issue_token(self.p['id']);etoken=self.s.issue_token(self.e['id'])
        server=Server(('127.0.0.1',0),self.s,FakeClient());thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        def call(token,body):
            conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=5)
            conn.request('POST','/api/model/propose',json.dumps(body),{'Content-Type':'application/json','Authorization':'Bearer '+token})
            r=conn.getresponse();v=json.loads(r.read());conn.close();return r.status,v
        try:
            self.assertEqual(call(etoken,self.request())[0],403)
            self.assertEqual(call(token,dict(self.request(),synthetic_consent=False))[0],403)
            status,value=call(token,self.request());self.assertEqual(status,200);self.assertEqual(value['status'],'pending')
            self.assertFalse(self.s.state(self.p)['outbox'])
        finally: server.shutdown();server.server_close();thread.join()
    def test_valid_sse_draft_and_request_contract(self):
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,n):
                return ('event: response.completed\ndata: '+json.dumps({'type':'response.completed','response':{'status':'completed','output':[{'type':'reasoning'},{'type':'message','role':'assistant','content':[{'type':'output_text','text':json.dumps({'title':'合成','body':'等待人工审批'})}]}],'usage':{'input_tokens':20,'output_tokens':30,'total_tokens':50,'private':'never log'}}})+'\n\n').encode()
        c={'NAME':'gpt-6-astra','REASONING_EFFORT':'medium','MAX_OUTPUT_TOKENS':1536,'API_KEY':'fake','TIMEOUT_SECONDS':1}
        with patch('urllib.request.OpenerDirector.open',return_value=Response()) as opened:
            draft,usage=ModelClient(c)._generate('rest')
            request=opened.call_args.args[0];payload=json.loads(request.data)
            self.assertTrue(request.full_url.endswith('/responses'));self.assertTrue(payload['stream']);self.assertFalse(payload['store'])
            self.assertEqual(payload['reasoning'],{'effort':'medium'});self.assertEqual(payload['max_output_tokens'],1536)
            self.assertEqual(draft['title'],'合成');self.assertEqual(usage,{'input_tokens':20,'output_tokens':30,'total_tokens':50})
    def test_gateway_completed_event_without_output_uses_done_item(self):
        item={'type':'message','role':'assistant','content':[{'type':'output_text','text':'```json\n{"title":"合成","body":"待审批"}\n```'}]}
        raw=''.join('data: '+json.dumps(e)+'\n\n' for e in [
            {'type':'response.output_item.done','item':item},
            {'type':'response.completed','response':{'status':'completed','output':[],'usage':{'total_tokens':30}}}])
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,n):return raw.encode()
        config={'NAME':'gpt-6-astra','REASONING_EFFORT':'medium','MAX_OUTPUT_TOKENS':1536,'API_KEY':'fake','TIMEOUT_SECONDS':1}
        with patch('urllib.request.OpenerDirector.open',return_value=Response()):
            draft,usage=ModelClient(config)._generate('meeting')
            self.assertEqual(draft,{'title':'合成','body':'待审批'});self.assertEqual(usage,{'total_tokens':30})
    def test_budget_is_shared_across_clients_and_persists(self):
        with tempfile.TemporaryDirectory() as d,patch('lingban.model.__file__',str(Path(d)/'lingban'/'model.py')):
            a=ModelClient({'MAX_CALLS':2});b=ModelClient({'MAX_CALLS':2})
            self.assertTrue(a.reserve());self.assertTrue(b.reserve());self.assertFalse(a.reserve())
            self.assertEqual(ModelClient({'MAX_CALLS':2}).used(),2)
