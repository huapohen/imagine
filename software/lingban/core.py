import hashlib
import json
import secrets
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager

MAX_TEXT = 500
EVENT_TYPES = {'meeting.upsert', 'task.upsert', 'focus.set', 'break.due'}
PERMISSIONS = {'events:write', 'tasks:read', 'hardware:write'}

class Problem(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message
        super().__init__(message)

def obj(value):
    if not isinstance(value, dict): raise Problem(400, '需要 JSON 对象')
    return value

def text(value, key, limit=MAX_TEXT):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise Problem(400, key + ' 必须为非空字符串，长度上限 ' + str(limit))
    return value.strip()

def number(value, key, low=0, high=4102444800):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high:
        raise Problem(400, key + ' 超出允许范围')
    return value

def exact(data, allowed):
    obj(data)
    if set(data) - set(allowed): raise Problem(400, '不支持的字段: ' + ', '.join(sorted(set(data) - set(allowed))))

def dump(value): return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
def uid(): return uuid.uuid4().hex

def require(p, role, allow_plugin=False):
    if not p or p['role'] != role or (p.get('plugin_id') and not allow_plugin): raise Problem(403, '此角色没有该接口权限')

class Store:
    def __init__(self, path=':memory:', clock=time.time):
        self.clock = clock
        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
        PRAGMA foreign_keys=ON;
        PRAGMA secure_delete=ON;
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS people(id TEXT PRIMARY KEY, role TEXT NOT NULL, org TEXT NOT NULL, name TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS tokens(hash TEXT PRIMARY KEY, person TEXT REFERENCES people(id), plugin TEXT);
        CREATE TABLE IF NOT EXISTS prefs(owner TEXT PRIMARY KEY REFERENCES people(id), focus_until REAL DEFAULT 0, cooldown INTEGER DEFAULT 300, rest_due REAL DEFAULT 0, rest_version INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, owner TEXT NOT NULL, idem TEXT NOT NULL, digest TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL, created REAL NOT NULL, UNIQUE(owner,idem));
        CREATE TABLE IF NOT EXISTS tasks(id TEXT NOT NULL, owner TEXT NOT NULL, title TEXT NOT NULL, state TEXT NOT NULL, kind TEXT NOT NULL, due REAL NOT NULL, project TEXT NOT NULL, version INTEGER NOT NULL, evidence TEXT NOT NULL, PRIMARY KEY(owner,id));
        CREATE TABLE IF NOT EXISTS alerts(id TEXT PRIMARY KEY, owner TEXT NOT NULL, rule TEXT NOT NULL, subject TEXT NOT NULL, fingerprint TEXT NOT NULL, title TEXT NOT NULL, explanation TEXT NOT NULL, created REAL NOT NULL, feedback TEXT, UNIQUE(owner,rule,subject,fingerprint));
        CREATE TABLE IF NOT EXISTS rule_marks(owner TEXT, rule TEXT, subject TEXT, fingerprint TEXT NOT NULL, last_sent REAL NOT NULL, PRIMARY KEY(owner,rule,subject));
        CREATE TABLE IF NOT EXISTS actions(id TEXT PRIMARY KEY, owner TEXT NOT NULL, title TEXT NOT NULL, body TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS outbox(id TEXT PRIMARY KEY, action TEXT NOT NULL UNIQUE REFERENCES actions(id), owner TEXT NOT NULL, payload TEXT NOT NULL, created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT, owner TEXT NOT NULL, kind TEXT NOT NULL, detail TEXT NOT NULL, created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS consent(owner TEXT PRIMARY KEY, org TEXT NOT NULL, enabled INTEGER NOT NULL, generation INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS shared(owner TEXT PRIMARY KEY, org TEXT NOT NULL, completed INTEGER NOT NULL, blocked INTEGER NOT NULL, generation INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS plugins(owner TEXT NOT NULL, id TEXT NOT NULL, manifest TEXT NOT NULL, PRIMARY KEY(owner,id));
        CREATE TABLE IF NOT EXISTS hardware(owner TEXT PRIMARY KEY, state TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS a2a(id TEXT PRIMARY KEY, owner TEXT NOT NULL, message_id TEXT NOT NULL, digest TEXT NOT NULL, task TEXT NOT NULL, UNIQUE(owner,message_id));
        ''')
        if 'plugin' not in {r['name'] for r in self.db.execute('PRAGMA table_info(tokens)')}:
            self.db.execute('ALTER TABLE tokens ADD COLUMN plugin TEXT')
    @contextmanager
    def tx(self):
        with self.lock:
            self.db.execute('BEGIN IMMEDIATE')
            try:
                yield self.db
                self.db.execute('COMMIT')
            except BaseException:
                self.db.execute('ROLLBACK')
                raise
    def close(self):
        with self.lock: self.db.close()
    def person(self, ident, role='employee', org='demo-co', name='合成员工'):
        with self.tx() as db:
            db.execute('INSERT OR IGNORE INTO people VALUES(?,?,?,?)', (ident, role, org, name))
            if role == 'employee': db.execute('INSERT OR IGNORE INTO prefs(owner) VALUES(?)', (ident,))
        return dict(self.db.execute('SELECT * FROM people WHERE id=?',(ident,)).fetchone())
    def issue_token(self, ident, plugin=None):
        token = secrets.token_urlsafe(32)
        with self.tx() as db: db.execute('INSERT INTO tokens(hash,person,plugin) VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(), ident, plugin))
        return token
    def authenticate(self, token):
        if not isinstance(token, str) or len(token)>256: raise Problem(401,'访问令牌无效')
        with self.lock:
            row=self.db.execute('SELECT p.*,t.plugin AS plugin_id FROM people p JOIN tokens t ON t.person=p.id WHERE t.hash=?',(hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
        if not row: raise Problem(401, '需要有效的 Bearer 访问令牌')
        return dict(row)
    def log(self, db, owner, kind, detail):
        db.execute('INSERT INTO audit(owner,kind,detail,created) VALUES(?,?,?,?)',(owner,kind,dump(detail),self.clock()))
    def ingest(self, p, data):
        require(p,'employee',True); exact(data, {'idempotency_key','type','payload','plugin_id'})
        if p.get('plugin_id'):
            if data.get('plugin_id',p['plugin_id'])!=p['plugin_id']: raise Problem(403,'插件不能冒用其他插件身份')
            data=dict(data,plugin_id=p['plugin_id'])
        idem=text(data.get('idempotency_key'),'idempotency_key',128)
        kind=text(data.get('type'),'type',40); payload=obj(data.get('payload'))
        if kind not in EVENT_TYPES: raise Problem(400,'事件类型不支持；禁止音频、生理、键盘或员工评分输入')
        clean={}
        if kind in ('task.upsert','meeting.upsert'):
            exact(payload, {'id','title','state','due_at','project'})
            clean={'id':text(payload.get('id'),'id',100),'title':text(payload.get('title'),'title',160), 'state':payload.get('state','open'), 'due_at':number(payload.get('due_at',0),'due_at'), 'project':text(payload.get('project','晶鼠试点'),'project',80)}
            if clean['state'] not in ('open','blocked','done'): raise Problem(400,'state 无效')
        elif kind=='focus.set':
            exact(payload,{'until','cooldown_seconds'})
            clean={'until':number(payload.get('until',0),'until',0,self.clock()+86400), 'cooldown_seconds':number(payload.get('cooldown_seconds',300),'cooldown_seconds',10,86400)}
        else:
            exact(payload,{'due_at'}); clean={'due_at':number(payload.get('due_at'),'due_at')}
        digest=hashlib.sha256(dump({'type':kind,'payload':clean,'plugin_id':data.get('plugin_id')}).encode()).hexdigest()
        with self.tx() as db:
            if 'plugin_id' in data:
                plugin_id=text(data['plugin_id'],'plugin_id',80)
                self.plugin_permission(db,p,plugin_id,'events:write',kind)
            old=db.execute('SELECT * FROM events WHERE owner=? AND idem=?',(p['id'],idem)).fetchone()
            if old:
                if old['digest']!=digest: raise Problem(409,'相同幂等键对应不同内容')
                return {'id':old['id'],'duplicate':True}
            eid=uid(); db.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?)',(eid,p['id'],idem,digest,kind,dump(clean),self.clock()))
            if kind in ('task.upsert','meeting.upsert'):
                task_kind='meeting' if kind=='meeting.upsert' else 'task'
                old=db.execute('SELECT * FROM tasks WHERE owner=? AND id=?',(p['id'],clean['id'])).fetchone()
                values=(clean['title'],clean['state'],task_kind,clean['due_at'],clean['project'])
                if not old:
                    db.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?)',(clean['id'],p['id'],*values,1,eid))
                elif tuple(old[k] for k in ('title','state','kind','due','project')) != values:
                    db.execute('UPDATE tasks SET title=?,state=?,kind=?,due=?,project=?,version=version+1,evidence=? WHERE owner=? AND id=?',(*values,eid,p['id'],clean['id']))
            elif kind=='focus.set':
                db.execute('UPDATE prefs SET focus_until=?,cooldown=? WHERE owner=?',(clean['until'],clean['cooldown_seconds'],p['id']))
            else:
                db.execute('UPDATE prefs SET rest_version=rest_version+CASE WHEN rest_due!=? THEN 1 ELSE 0 END,rest_due=? WHERE owner=?',(clean['due_at'],clean['due_at'],p['id']))
            self.log(db,p['id'],'event.accepted',{'event':eid,'type':kind})
        return {'id':eid,'duplicate':False}
    def tick(self):
        now=self.clock(); count=0
        with self.tx() as db:
            for pref in db.execute('SELECT * FROM prefs').fetchall():
                owner=pref['owner']; candidates=[]
                for task in db.execute('SELECT * FROM tasks WHERE owner=?',(owner,)).fetchall():
                    rule=None
                    if task['state']=='blocked': rule='blocked'
                    elif task['kind']=='meeting' and task['state']=='open' and now<=task['due']<=now+900: rule='meeting'
                    if rule:
                        fp=str(task['version'])
                        title=('会议将近 · ' if rule=='meeting' else '项目需要你推动 · ')+task['title']
                        explanation={'rule':rule,'evidence_id':task['evidence'],'task_version':task['version'],'state':task['state'],'due_at':task['due'],'reason':'日程将在 15 分钟内开始' if rule=='meeting' else '任务状态明确变为阻塞','decision':'离线确定性规则；无情绪、绩效或医疗推断'}
                        candidates.append((rule,task['id'],fp,title,explanation))
                if 0 < pref['rest_due'] <= now:
                    candidates.append(('rest','rest',str(pref['rest_version']),'给自己两分钟，松开肩膀',{'rule':'rest','scheduled_at':pref['rest_due'],'reason':'你设置的休息时间已到；仅为非医疗舒适度建议','decision':'用户设置的计时器'}))
                active={(c[0],c[1]) for c in candidates}
                # Keep last_sent across resolution for cooldown; signature records resolved state.
                for mark in db.execute('SELECT * FROM rule_marks WHERE owner=?',(owner,)).fetchall():
                    if (mark['rule'],mark['subject']) not in active:
                        db.execute("UPDATE rule_marks SET fingerprint='resolved' WHERE owner=? AND rule=? AND subject=?",(owner,mark['rule'],mark['subject']))
                for rule,subject,fp,title,why in candidates:
                    mark=db.execute('SELECT * FROM rule_marks WHERE owner=? AND rule=? AND subject=?',(owner,rule,subject)).fetchone()
                    if pref['focus_until']>now or (mark and (mark['fingerprint']==fp or now-mark['last_sent']<pref['cooldown'])): continue
                    changed=db.execute('INSERT OR IGNORE INTO alerts VALUES(?,?,?,?,?,?,?,?,NULL)',(uid(),owner,rule,subject,fp,title,dump(why),now)).rowcount
                    if changed:
                        count+=1
                        db.execute('INSERT OR REPLACE INTO rule_marks VALUES(?,?,?,?,?)',(owner,rule,subject,fp,now))
                        self.log(db,owner,'agent.reminded',{'rule':rule,'subject':subject,'evidence':why})
                        self.set_hardware_db(db,owner,{'led':'teal' if rule!='blocked' else 'amber','screen':title[:48]}, 'agent')
        return count
    def feedback(self,p,ident,value):
        require(p,'employee')
        if value not in ('useful','dismissed','snooze'): raise Problem(400,'反馈类型无效')
        with self.tx() as db:
            if not db.execute('SELECT 1 FROM alerts WHERE id=? AND owner=?',(ident,p['id'])).fetchone(): raise Problem(404,'提醒不存在')
            db.execute('UPDATE alerts SET feedback=? WHERE id=?',(value,ident))
            if value=='snooze': db.execute('UPDATE prefs SET focus_until=? WHERE owner=?',(self.clock()+600,p['id']))
            self.log(db,p['id'],'alert.feedback',{'alert':ident,'feedback':value})
        return {'ok':True}
    def propose(self,p,data):
        require(p,'employee'); exact(data,{'title','body'})
        title_=text(data.get('title'),'title',160); body=text(data.get('body'),'body',2000)
        ident=uid()
        with self.tx() as db:
            db.execute('INSERT INTO actions VALUES(?,?,?,?,?,?)',(ident,p['id'],title_,body,'pending',self.clock()))
            self.log(db,p['id'],'action.proposed',{'action':ident,'title':title_})
        return {'id':ident,'status':'pending'}
    def decide(self,p,ident,decision):
        require(p,'employee')
        if decision not in ('approve','reject'): raise Problem(400,'只能 approve 或 reject')
        with self.tx() as db:
            row=db.execute('SELECT * FROM actions WHERE id=? AND owner=?',(ident,p['id'])).fetchone()
            if not row: raise Problem(404,'动作不存在')
            target='approved' if decision=='approve' else 'rejected'
            if row['status']!='pending':
                if row['status']!=target: raise Problem(409,'动作已结束，不能改变决定')
                return {'id':ident,'status':target,'duplicate':True}
            db.execute('UPDATE actions SET status=? WHERE id=?',(target,ident))
            if decision=='approve':
                db.execute('INSERT INTO outbox VALUES(?,?,?,?,?)',(uid(),ident,p['id'],dump({'title':row['title'],'body':row['body'],'delivery':'local-only'}),self.clock()))
            self.log(db,p['id'],'action.'+target,{'action':ident,'delivery':'local-only'})
        return {'id':ident,'status':target,'duplicate':False}
    def set_consent(self,p,enabled):
        require(p,'employee')
        if not isinstance(enabled,bool): raise Problem(400,'enabled 需要布尔值')
        with self.tx() as db:
            old=db.execute('SELECT * FROM consent WHERE owner=?',(p['id'],)).fetchone()
            gen=(old['generation']+1) if old else 1
            db.execute('INSERT OR REPLACE INTO consent VALUES(?,?,?,?)',(p['id'],p['org'],int(enabled),gen))
            # Regrant also requires a fresh explicit share; no historical resurrection.
            deleted=db.execute('DELETE FROM shared WHERE owner=?',(p['id'],)).rowcount
            db.execute("DELETE FROM a2a WHERE owner IN (SELECT id FROM people WHERE role='enterprise' AND org=?)",(p['org'],))
            self.log(db,p['id'],'consent.granted' if enabled else 'consent.revoked',{'scope':'business.result','shared_rows_removed':deleted,'generation':gen})
        return {'enabled':enabled,'shared_rows_removed':deleted,'scope':'business.result'}
    def share(self,p,data):
        require(p,'employee'); exact(data,{'completed','blocked'})
        a=number(data.get('completed'),'completed',0,10000); b=number(data.get('blocked'),'blocked',0,10000)
        if not isinstance(a,int) or not isinstance(b,int): raise Problem(400,'业务结果必须为整数')
        with self.tx() as db:
            c=db.execute('SELECT * FROM consent WHERE owner=?',(p['id'],)).fetchone()
            if not c or not c['enabled']: raise Problem(403,'尚未明确授权业务结果分享')
            db.execute('INSERT OR REPLACE INTO shared VALUES(?,?,?,?,?)',(p['id'],p['org'],a,b,c['generation']))
            self.log(db,p['id'],'business.shared',{'scope':'business.result','generation':c['generation']})
        return {'shared':True}
    def enterprise(self,p):
        require(p,'enterprise')
        with self.lock:
            rows=self.db.execute('SELECT s.completed,s.blocked FROM shared s JOIN consent c ON s.owner=c.owner AND s.org=c.org AND s.generation=c.generation WHERE s.org=? AND c.enabled=1',(p['org'],)).fetchall()
        if len(rows)<5: return {'available':False,'minimum_people':5,'reason':'明确授权的分享人数不足 5 人，聚合结果已隐藏','synthetic':True}
        # Cohort size buckets reduce disclosure; no per-person, filters, rankings or history endpoints.
        return {'available':True,'minimum_people':5,'cohort':'5–9 人' if len(rows)<10 else '10 人及以上','completed':sum(r['completed'] for r in rows),'blocked':sum(r['blocked'] for r in rows),'scope':'员工明确分享的业务结果','synthetic':True}
    def register_plugin(self,p,data):
        require(p,'employee'); exact(data,{'id','name','version','permissions','event_types'})
        ident=text(data.get('id'),'id',80); text(data.get('name'),'name',80); text(data.get('version'),'version',30)
        perms=data.get('permissions'); kinds=data.get('event_types',[])
        if not isinstance(perms,list) or not all(isinstance(x,str) for x in perms) or not set(perms)<=PERMISSIONS: raise Problem(403,'插件权限包含不允许的能力')
        if not isinstance(kinds,list) or not all(isinstance(x,str) for x in kinds) or not set(kinds)<=EVENT_TYPES: raise Problem(403,'插件事件范围不允许')
        if kinds and 'events:write' not in perms: raise Problem(403,'事件类型需要 events:write')
        with self.tx() as db:
            db.execute('INSERT OR REPLACE INTO plugins VALUES(?,?,?)',(p['id'],ident,dump(data)))
            self.log(db,p['id'],'plugin.registered',{'id':ident,'permissions':perms})
        return {'id':ident,'enabled':True,'execution':'manifest-only; no third-party code execution'}
    def plugin_permission(self,db,p,ident,permission,kind=None):
        row=db.execute('SELECT manifest FROM plugins WHERE owner=? AND id=?',(p['id'],ident)).fetchone()
        if not row: raise Problem(403,'插件未注册')
        manifest=json.loads(row['manifest'])
        if permission not in manifest['permissions'] or (kind and kind not in manifest.get('event_types',[])): raise Problem(403,'插件缺少该操作权限')
    def plugin_token(self,p,ident):
        require(p,'employee')
        with self.lock:
            if not self.db.execute('SELECT 1 FROM plugins WHERE owner=? AND id=?',(p['id'],ident)).fetchone(): raise Problem(404,'插件不存在')
        return {'token':self.issue_token(p['id'],ident),'plugin_id':ident,'scope':'registered-manifest'}
    def plugin_read(self,p,ident):
        require(p,'employee',True)
        if p.get('plugin_id') and p['plugin_id']!=ident: raise Problem(403,'插件身份不匹配')
        with self.lock:
            self.plugin_permission(self.db,p,ident,'tasks:read')
            return [dict(r) for r in self.db.execute('SELECT * FROM tasks WHERE owner=?',(p['id'],))]
    def set_hardware_db(self,db,owner,patch,source):
        row=db.execute('SELECT state FROM hardware WHERE owner=?',(owner,)).fetchone()
        state=json.loads(row['state']) if row else {'led':'off','screen':'灵伴已就绪','privacy':False,'touch':False,'transport':'simulated','protocol':'LB1/1.0'}
        was_private=state['privacy']
        state.update(patch)
        state['protocol']='LB1/1.0'
        if state['privacy']: state.update(led='off',screen='隐私已启用（仅电脑 UI）',touch=False)
        elif was_private:
            state.update(led=patch.get('led','off'),screen=patch.get('screen','灵伴已就绪'),touch=False)
        state['source']=source
        db.execute('INSERT OR REPLACE INTO hardware VALUES(?,?)',(owner,dump(state)))
        return state
    def hardware(self,p,data):
        require(p,'employee',True); exact(data,{'led','screen','privacy','touch','plugin_id'})
        if p.get('plugin_id'):
            if data.get('plugin_id',p['plugin_id'])!=p['plugin_id']: raise Problem(403,'插件身份不匹配')
            data=dict(data,plugin_id=p['plugin_id'])
        patch={k:v for k,v in data.items() if k!='plugin_id'}
        if 'led' in patch and patch['led'] not in ('off','teal','amber','blue'): raise Problem(400,'灯光值无效')
        if 'screen' in patch: text(patch['screen'],'screen',48)
        for key in ('privacy','touch'):
            if key in patch and not isinstance(patch[key],bool): raise Problem(400,key+' 必须为布尔值')
        with self.tx() as db:
            if 'plugin_id' in data:
                self.plugin_permission(db,p,text(data['plugin_id'],'plugin_id',80),'hardware:write')
                if 'privacy' in patch: raise Problem(403,'插件不能改变隐私开关')
            result=self.set_hardware_db(db,p['id'],patch,'simulator')
            self.log(db,p['id'],'hardware.simulated',{'privacy':result['privacy'],'led':result['led']})
        return result
    def state(self,p):
        require(p,'employee')
        with self.lock:
            def rows(table,order='rowid DESC',limit=100):
                return [dict(x) for x in self.db.execute('SELECT * FROM '+table+' WHERE owner=? ORDER BY '+order+' LIMIT ?',(p['id'],limit))]
            pref=dict(self.db.execute('SELECT * FROM prefs WHERE owner=?',(p['id'],)).fetchone())
            c=self.db.execute('SELECT enabled FROM consent WHERE owner=?',(p['id'],)).fetchone()
            hw=self.db.execute('SELECT state FROM hardware WHERE owner=?',(p['id'],)).fetchone()
            return {'person':p,'synthetic':True,'tasks':rows('tasks'),'alerts':rows('alerts'),'actions':rows('actions'),'outbox':rows('outbox'),'audit':rows('audit'),'plugins':rows('plugins'),'preferences':pref,'consent':bool(c and c['enabled']),'hardware':json.loads(hw['state']) if hw else {'led':'off','privacy':False,'screen':'灵伴已就绪','touch':False,'transport':'simulated'}}
    def scenario(self,p,name):
        require(p,'employee'); now=self.clock(); key=uid()
        if name=='meeting':
            self.ingest(p,{'idempotency_key':key,'type':'meeting.upsert','payload':{'id':'demo-meeting','title':'晶鼠 · 透明城堡方案评审','due_at':now+600}})
            self.propose(p,{'title':'准备会议要点','body':'合成演示：整理透明城堡结构、USB HID 底座与独立交互模块的评审要点。批准后仅保存至本地 outbox。'})
        elif name=='blocked':
            self.ingest(p,{'idempotency_key':key,'type':'task.upsert','payload':{'id':'demo-blocked','title':'等待主板接口与引脚确认','state':'blocked'}})
        elif name=='focus':
            self.ingest(p,{'idempotency_key':key,'type':'focus.set','payload':{'until':now+25*60}})
            self.ingest(p,{'idempotency_key':key+'-rest','type':'break.due','payload':{'due_at':now}})
        elif name=='resume': self.ingest(p,{'idempotency_key':key,'type':'focus.set','payload':{'until':0}})
        elif name=='revoke': return self.set_consent(p,False)
        else: raise Problem(400,'场景不存在')
        self.tick(); return {'scenario':name,'synthetic':True}
    def seed(self):
        alice=self.person('demo-alice',name='林小伴 · 合成用户')
        self.person('demo-enterprise','enterprise',name='灵伴试点 · 合成企业')
        # Idempotent initialization. Never re-enable a user's revoked consent on restart.
        with self.lock: exists=self.db.execute("SELECT 1 FROM audit WHERE kind='demo.seeded'").fetchone()
        if not exists:
            for i in range(5):
                p=alice if i==0 else self.person('demo-person-'+str(i),name='合成成员 '+str(i))
                self.set_consent(p,True); self.share(p,{'completed':i+2,'blocked':int(i%2==0)})
            self.ingest(alice,{'idempotency_key':'seed-task','type':'task.upsert','payload':{'id':'castle','title':'完成原创天空城堡结构草图','state':'done'}})
            with self.tx() as db: self.log(db,alice['id'],'demo.seeded',{'synthetic':True})
        return {'employee':self.issue_token('demo-alice'),'enterprise':self.issue_token('demo-enterprise')}

class Worker:
    def __init__(self,store,interval=1):
        self.store=store; self.interval=interval; self.stop_event=threading.Event(); self.error=None
        self.thread=threading.Thread(target=self.run,name='lingban-evidence-worker',daemon=True)
    def run(self):
        while not self.stop_event.is_set():
            try: self.store.tick(); self.error=None
            except Exception as e: self.error=type(e).__name__
            self.stop_event.wait(self.interval)
    def start(self): self.thread.start()
    def stop(self): self.stop_event.set(); self.thread.join(timeout=5)
