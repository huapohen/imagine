import concurrent.futures
import json
from pathlib import Path
import tempfile
import time
import unittest
from lingban.core import Store, Worker, Problem
from lingban.protocols import A2A

class Clock:
    def __init__(self): self.now=1800000000
    def __call__(self): return self.now
    def advance(self,n): self.now+=n

class CoreTests(unittest.TestCase):
    def test_leaving_simulated_privacy_clears_stale_privacy_screen(self):
        store=Store()
        try:
            person=store.person('privacy-ui-regression')
            store.hardware(person,{'privacy':True})
            state=store.hardware(person,{'privacy':False})
            self.assertFalse(state['privacy'])
            self.assertEqual(state['screen'],'灵伴已就绪')
            self.assertEqual(state['led'],'off')
            self.assertFalse(state['touch'])
        finally:store.close()
    def setUp(self):
        self.clock=Clock();self.s=Store(clock=self.clock)
        self.a=self.s.person('alice',name='合成甲');self.b=self.s.person('bob',name='合成乙')
        self.e=self.s.person('enterprise','enterprise');self.e2=self.s.person('other-enterprise','enterprise','other-org')
    def tearDown(self):self.s.close()
    def event(self,idem='one',kind='task.upsert',**payload):
        return self.s.ingest(self.a,{'idempotency_key':idem,'type':kind,'payload':{'id':'t1','title':'合成任务','state':'blocked',**payload} if kind=='task.upsert' else payload})
    def alerts(self):return self.s.state(self.a)['alerts']
    def test_idempotency_and_conflicting_payload(self):
        first=self.event();again=self.event();self.assertEqual(first['id'],again['id']);self.assertTrue(again['duplicate'])
        with self.assertRaises(Problem) as cm:self.event(title='不同内容')
        self.assertEqual(cm.exception.status,409)
        self.assertEqual(self.s.db.execute('SELECT COUNT(*) FROM events').fetchone()[0],1)
    def test_idempotency_scoped_to_employee(self):
        self.event();result=self.s.ingest(self.b,{'idempotency_key':'one','type':'task.upsert','payload':{'id':'t1','title':'乙的任务'}})
        self.assertFalse(result['duplicate']);self.assertEqual(len(self.s.state(self.b)['tasks']),1)
        self.assertNotEqual(self.s.state(self.a)['tasks'][0]['title'],self.s.state(self.b)['tasks'][0]['title'])
    def test_new_evidence_triggers_once_and_no_time_only_repeat(self):
        self.event();self.assertEqual(self.s.tick(),1);self.assertEqual(self.s.tick(),0)
        self.clock.advance(3600);self.assertEqual(self.s.tick(),0)
        self.event('same-state');self.assertEqual(self.s.tick(),0)
        why=json.loads(self.alerts()[0]['explanation']);self.assertEqual(why['task_version'],1);self.assertIn('evidence_id',why)
    def test_cooldown_defers_changed_evidence(self):
        self.event();self.s.tick();self.event('two',title='新的阻塞依据');self.assertEqual(self.s.tick(),0)
        self.clock.advance(301);self.assertEqual(self.s.tick(),1);self.assertEqual(len(self.alerts()),2)
    def test_resolved_and_reblocked(self):
        self.event();self.s.tick();self.event('resolve',state='done');self.s.tick();self.clock.advance(301)
        self.event('again',state='blocked');self.assertEqual(self.s.tick(),1)
    def test_resolved_during_quiet_never_notifies(self):
        self.event(kind='focus.set',until=self.clock()+600)
        self.event('blocked');self.s.tick();self.event('fixed',state='done');self.clock.advance(601)
        self.assertEqual(self.s.tick(),0)
    def test_focus_and_rest_deferred(self):
        self.event(kind='focus.set',until=self.clock()+1500)
        self.event('rest',kind='break.due',due_at=self.clock());self.assertEqual(self.s.tick(),0)
        self.event('end',kind='focus.set',until=0);self.assertEqual(self.s.tick(),1)
        self.assertEqual(self.alerts()[0]['rule'],'rest');self.assertEqual(self.s.tick(),0)
    def test_meeting_enters_window_once_and_expires(self):
        self.event(kind='meeting.upsert',id='m',title='合成会议',due_at=self.clock()+1800)
        self.assertEqual(self.s.tick(),0);self.clock.advance(901);self.assertEqual(self.s.tick(),1)
        self.clock.advance(1000);self.assertEqual(self.s.tick(),0)
    def test_background_worker_without_scenario_tick(self):
        worker=Worker(self.s,.01);worker.start()
        try:
            self.event();deadline=time.monotonic()+2
            while not self.alerts() and time.monotonic()<deadline:time.sleep(.01)
            self.assertEqual(len(self.alerts()),1);self.assertIsNone(worker.error)
        finally:worker.stop()
    def test_feedback_owned_and_snooze(self):
        self.event();self.s.tick();ident=self.alerts()[0]['id']
        with self.assertRaises(Problem):self.s.feedback(self.b,ident,'useful')
        self.s.feedback(self.a,ident,'snooze');self.assertGreater(self.s.state(self.a)['preferences']['focus_until'],self.clock())
    def test_atomic_approve_once_under_concurrency(self):
        act=self.s.propose(self.a,{'title':'拟定合成摘要','body':'仅本地'})
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(lambda _:self.s.decide(self.a,act['id'],'approve'),range(16)))
        self.assertEqual(sum(not r['duplicate'] for r in results),1)
        self.assertEqual(len(self.s.state(self.a)['outbox']),1)
        self.assertEqual(sum(a['kind']=='action.approved' for a in self.s.state(self.a)['audit']),1)
    def test_reject_never_outbox_and_terminal_decisions(self):
        act=self.s.propose(self.a,{'title':'合成动作','body':'不要外发'})
        self.s.decide(self.a,act['id'],'reject');self.assertTrue(self.s.decide(self.a,act['id'],'reject')['duplicate'])
        with self.assertRaises(Problem):self.s.decide(self.a,act['id'],'approve')
        self.assertEqual(self.s.state(self.a)['outbox'],[])
    def test_action_and_alert_isolation(self):
        act=self.s.propose(self.a,{'title':'甲的动作','body':'合成内容'})
        for person in (self.b,self.e):
            with self.assertRaises(Problem):self.s.decide(person,act['id'],'approve')
        self.assertEqual(self.s.state(self.b)['actions'],[])
    def seed_cohort(self,n=5):
        people=[self.a]+[self.s.person('synthetic-'+str(i)) for i in range(1,n)]
        for p in people:self.s.set_consent(p,True);self.s.share(p,{'completed':2,'blocked':1})
        return people
    def test_enterprise_threshold_and_org_isolation(self):
        self.seed_cohort(4);self.assertFalse(self.s.enterprise(self.e)['available'])
        self.s.set_consent(self.b,True);self.s.share(self.b,{'completed':2,'blocked':1})
        result=self.s.enterprise(self.e);self.assertTrue(result['available']);self.assertEqual(result['completed'],10)
        self.assertNotIn('owner',json.dumps(result));self.assertFalse(self.s.enterprise(self.e2)['available'])
        with self.assertRaises(Problem):self.s.enterprise(self.a)
        with self.assertRaises(Problem):self.s.state(self.e)
    def test_revoke_deletes_shared_and_historical_a2a_snapshots(self):
        self.seed_cohort();a2a=A2A(self.s)
        reply=a2a.send(self.e,{'message':{'kind':'message','role':'user','messageId':'agg','parts':[{'kind':'text','text':'摘要'}]}})
        self.assertIn('completed',reply['artifacts'][0]['parts'][0]['text'])
        self.s.set_consent(self.a,False)
        self.assertEqual(self.s.db.execute('SELECT COUNT(*) FROM shared WHERE owner=?',('alice',)).fetchone()[0],0)
        self.assertFalse(self.s.enterprise(self.e)['available'])
        with self.assertRaises(Problem):a2a.get(self.e,{'id':reply['id']})
        self.s.set_consent(self.a,True);self.assertFalse(self.s.enterprise(self.e)['available'])
        self.s.share(self.a,{'completed':1,'blocked':0});self.assertTrue(self.s.enterprise(self.e)['available'])
    def test_consent_required_and_private_fields_rejected(self):
        with self.assertRaises(Problem):self.s.share(self.a,{'completed':1,'blocked':0})
        self.s.set_consent(self.a,True)
        for key in ('audio','physiology','employee_score','keyboard'):
            with self.assertRaises(Problem):self.s.share(self.a,{'completed':1,'blocked':0,key:'x'})
            with self.assertRaises(Problem):self.s.ingest(self.a,{'idempotency_key':key,'type':key,'payload':{}})
    def test_plugin_permissions_and_scoped_token(self):
        manifest={'id':'calendar','name':'合成日历','version':'1.0','permissions':['events:write'],'event_types':['meeting.upsert']}
        self.s.register_plugin(self.a,manifest)
        pp=self.s.authenticate(self.s.plugin_token(self.a,'calendar')['token'])
        self.assertEqual(pp['plugin_id'],'calendar')
        self.s.ingest(pp,{'idempotency_key':'plugin','type':'meeting.upsert','payload':{'id':'pm','title':'插件会议','due_at':self.clock()+600}})
        with self.assertRaises(Problem):self.s.ingest(pp,{'idempotency_key':'escape','type':'task.upsert','payload':{'id':'pm','title':'逃逸'}})
        with self.assertRaises(Problem):self.s.state(pp)
        with self.assertRaises(Problem):self.s.propose(pp,{'title':'逃逸','body':'不能执行'})
        with self.assertRaises(Problem):self.s.plugin_read(pp,'calendar')
        with self.assertRaises(Problem):self.s.register_plugin(self.b,{**manifest,'permissions':['audio:read']})
        with self.assertRaises(Problem):self.s.register_plugin(self.b,{**manifest,'permissions':['tasks:read'],'event_types':['meeting.upsert']})
    def test_plugin_owner_scope_and_hardware_privacy(self):
        m={'id':'light','name':'灯光','version':'1','permissions':['hardware:write','tasks:read'],'event_types':[]}
        self.s.register_plugin(self.a,m);pp=self.s.authenticate(self.s.plugin_token(self.a,'light')['token'])
        self.event();self.assertEqual(len(self.s.plugin_read(pp,'light')),1)
        with self.assertRaises(Problem):self.s.plugin_read(self.b,'light')
        with self.assertRaises(Problem):self.s.hardware(pp,{'privacy':False})
        self.s.hardware(self.a,{'privacy':True});r=self.s.hardware(pp,{'led':'teal','touch':True})
        self.assertEqual(r['led'],'off');self.assertEqual(r['protocol'],'LB1/1.0');self.assertFalse(r['touch'])
    def test_input_validation(self):
        cases=[{'idempotency_key':'x','type':'task.upsert','payload':{'id':'t','title':'x'*161}}, {'idempotency_key':'x','type':'focus.set','payload':{'until':float('nan')}}, {'idempotency_key':'x','type':'task.upsert','payload':{'id':'t','title':'x','owner':'bob'}}]
        for c in cases:
            with self.assertRaises(Problem):self.s.ingest(self.a,c)
    def test_persistence_and_seed_no_regrant(self):
        root=Path(__file__).resolve().parents[1]/'test-output';root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as d:
            path=str(Path(d)/'memory.db');s=Store(path);s.seed();p=s.person('demo-alice');s.set_consent(p,False)
            s.propose(p,{'title':'持久动作','body':'合成'});s.close();s=Store(path)
            try:s.seed();self.assertFalse(s.state(p)['consent']);self.assertEqual(len(s.state(p)['actions']),1)
            finally:s.close()
    def test_quiet_ten_minutes_is_not_a_repeat_promise(self):
        self.event();self.s.tick();ident=self.alerts()[0]['id'];self.s.feedback(self.a,ident,'snooze')
        self.clock.advance(601);self.assertEqual(self.s.tick(),0);self.assertEqual(len(self.alerts()),1)
        self.event('changed-after-quiet',title='合成新证据');self.assertEqual(self.s.tick(),1)
    def test_revoked_a2a_message_replay_recomputes_all_content(self):
        self.seed_cohort();a=A2A(self.s)
        message={'kind':'message','role':'user','messageId':'same-revoked-message','parts':[{'kind':'text','text':'摘要'}]}
        old=a.send(self.e,{'message':message});self.s.set_consent(self.a,False)
        with self.assertRaises(Problem):a.get(self.e,{'id':old['id']})
        new=a.send(self.e,{'message':message});self.assertNotEqual(old['id'],new['id'])
        containers=[new['artifacts'][0]['parts'][0]['text'],new['history'][-1]['parts'][0]['text'],new['status']['message']['parts'][0]['text']]
        for value in containers:
            aggregate=json.loads(value);self.assertFalse(aggregate['available']);self.assertNotIn('completed',aggregate);self.assertNotIn('blocked',aggregate)
