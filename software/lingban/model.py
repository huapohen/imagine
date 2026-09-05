"""Opt-in, synthetic-only draft assistance. Never executes model instructions."""
import json
import os
from pathlib import Path
import stat
import sqlite3
import subprocess
import sys
import threading
import urllib.request
from .core import Problem, require, exact, text, dump, uid

SCENARIOS = {
    'meeting': ('准备合成会议要点', '合成场景：评审透明城堡结构、USB HID 底座与独立 ESP32-S3 模块。列出待确认事项。'),
    'blocked': ('推进合成阻塞任务', '合成场景：主板接口和引脚尚未确认。整理需要核对的资料与下一步，不联系任何人。'),
    'rest': ('安排合成休息建议', '合成场景：用户设置的休息计时器已到。给出两分钟非医疗舒适度建议，不判断情绪或健康。'),
}
BASE = 'https://wanapi-dev.wanmol.com:29527/v1'


def local_config(path):
    """No shell evaluation; only a fixed whitelist, owner-only regular local file."""
    path = Path(path)
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('模型配置必须是当前用户拥有的 0600 普通文件')
    allowed = {'ENABLED', 'PROVIDER', 'BASE_URL', 'NAME', 'REASONING_EFFORT', 'API_KEY',
               'MAX_CALLS', 'MAX_OUTPUT_TOKENS', 'TIMEOUT_SECONDS', 'ENV'}
    values = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line: continue
        key, value = line.split('=', 1)
        if key == 'LINGBAN_ENV': values['ENV'] = value.strip().strip('\"\'')
        if key.startswith('LINGBAN_MODEL_') and key[14:] in allowed:
            values[key[14:]] = value.strip().strip('\"\'')
    if values.get('ENV') != 'local-test' or values.get('ENABLED') != 'true':
        raise ValueError('模型必须显式启用 local-test 配置')
    if values.get('BASE_URL') != BASE or values.get('PROVIDER') != 'wanapi' or values.get('NAME') != 'gpt-6-astra' or values.get('REASONING_EFFORT') != 'medium':
        raise ValueError('模型配置不属于本次授权范围')
    if not values.get('API_KEY'): raise ValueError('缺少模型凭据')
    for key, maximum in [('MAX_CALLS',20), ('MAX_OUTPUT_TOKENS',1536), ('TIMEOUT_SECONDS',45)]:
        values[key] = int(values.get(key, maximum))
        if not 1 <= values[key] <= maximum: raise ValueError('模型预算超出授权范围')
    return values


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): return None


class ModelClient:
    def __init__(self, config): self.config = config
    def reserve(self):
        path=Path(__file__).resolve().parents[1]/'data'/'model-budget.sqlite3'
        path.parent.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(path,timeout=5,isolation_level=None) as db:
            os.chmod(path,0o600)
            db.execute('CREATE TABLE IF NOT EXISTS calls(id INTEGER PRIMARY KEY, created TEXT DEFAULT CURRENT_TIMESTAMP)')
            db.execute('BEGIN IMMEDIATE')
            count=db.execute('SELECT COUNT(*) FROM calls').fetchone()[0]
            if count>=self.config['MAX_CALLS']:
                db.execute('ROLLBACK'); return False
            db.execute('INSERT INTO calls DEFAULT VALUES'); db.execute('COMMIT')
        return True
    def used(self):
        path=Path(__file__).resolve().parents[1]/'data'/'model-budget.sqlite3'
        if not path.exists(): return 0
        with sqlite3.connect(path) as db: return db.execute('SELECT COUNT(*) FROM calls').fetchone()[0]
    def generate(self, scenario):
        # Wall deadline covers DNS/TLS and slow streaming, with no retries.
        result=subprocess.run([sys.executable,'-m','lingban.model'],
            input=dump({'config':self.config,'scenario':scenario}),capture_output=True,text=True,
            timeout=self.config['TIMEOUT_SECONDS'],check=True)
        draft,usage=json.loads(result.stdout)
        return draft,usage
    def _generate(self, scenario):
        c = self.config
        payload = {'model': c['NAME'], 'reasoning': {'effort': c['REASONING_EFFORT']},
                   'max_output_tokens': c['MAX_OUTPUT_TOKENS'], 'stream': True, 'store': False,
                   'instructions':'仅为固定合成演示生成中文待审批草稿。只输出 JSON 对象，字段 title、body，均为字符串；title 最多160字，body 最多2000字。不得发消息、执行工具、批准动作、评分员工或作医疗推断；不要声称已执行。',
                   'input': [{'role':'user','content':[{'type':'input_text','text':SCENARIOS[scenario][1]}]}]}
        request = urllib.request.Request(BASE + '/responses', data=dump(payload).encode(),
                     headers={'Authorization':'Bearer '+c['API_KEY'],'Content-Type':'application/json'})
        # Direct TLS was preflighted; ignore ambient proxy variables, forbid redirects.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        value = None
        total=0; buffer=b''; completed_items=[]; completed_text=[]
        with opener.open(request, timeout=c['TIMEOUT_SECONDS']) as response:
            read=getattr(response,'read1',response.read)
            while value is None:
                chunk=read(65536)
                if not chunk: break
                total+=len(chunk)
                if total>2097152: raise ValueError('oversized_response')
                buffer+=chunk
                while b'\n' in buffer:
                    line,buffer=buffer.split(b'\n',1)
                    if not line.startswith(b'data:'): continue
                    data=line[5:].strip()
                    if data==b'[DONE]': continue
                    event=json.loads(data)
                    if event.get('type')=='response.output_item.done': completed_items.append(event['item'])
                    if event.get('type')=='response.output_text.done': completed_text.append(event['text'])
                    if event.get('type')=='response.completed': value=event.get('response')
                    if event.get('type') in {'error','response.failed','response.incomplete'}: raise ValueError('provider_stream_error')
        if value is None: raise ValueError('missing_completed_response')
        if value.get('status') != 'completed': raise ValueError('incomplete_response')
        content=[]
        output=value.get('output') or completed_items
        if not output and completed_text:
            output=[{'type':'message','role':'assistant','content':[{'type':'output_text','text':t} for t in completed_text]}]
        for item in output:
            if item.get('type') == 'reasoning': continue
            if item.get('type') != 'message' or item.get('role') != 'assistant': raise ValueError('unsupported_response')
            for part in item.get('content',[]):
                if part.get('type') != 'output_text': raise ValueError('unsupported_response')
                content.append(part['text'])
        draft_text=''.join(content).strip()
        if draft_text.startswith('```json\n') and draft_text.endswith('\n```'):
            draft_text=draft_text[8:-4]
        draft = json.loads(draft_text)
        exact(draft, {'title','body'})
        draft = {'title':text(draft.get('title'),'title',160),'body':text(draft.get('body'),'body',2000)}
        # Usage is the only provider response data allowed in diagnostics.
        usage = {k:v for k,v in value.get('usage',{}).items() if k in {'input_tokens','output_tokens','total_tokens'} and type(v) is int and v>=0}
        return draft, usage


class DraftService:
    def __init__(self, store, client=None):
        self.store, self.client, self.lock = store, client, threading.Lock()
        with store.tx() as db:
            db.execute('CREATE TABLE IF NOT EXISTS model_drafts(owner TEXT, idem TEXT, scenario TEXT, result TEXT, PRIMARY KEY(owner,idem))')
            db.execute('CREATE TABLE IF NOT EXISTS model_calls(id TEXT PRIMARY KEY, created REAL NOT NULL)')
    def status(self, p):
        require(p,'employee')
        count=self.client.used() if self.client else 0
        return {'enabled':bool(self.client),'mode':'synthetic-local-test' if self.client else 'offline',
                'calls_used':count,'max_calls':self.client.config['MAX_CALLS'] if self.client else 0,
                'model':'gpt-6-astra' if self.client else None,'reasoning_effort':'medium' if self.client else None}
    def propose(self, p, data):
        require(p,'employee'); exact(data, {'scenario','idempotency_key','synthetic_consent'})
        idem=text(data.get('idempotency_key'),'idempotency_key',128)
        scenario=data.get('scenario')
        if not isinstance(scenario,str) or scenario not in SCENARIOS: raise Problem(400,'只支持固定合成场景')
        if data.get('synthetic_consent') is not True: raise Problem(403,'需要明确同意处理本次固定合成场景')
        s=self.store
        with self.lock:
            with s.tx() as db:
                old=db.execute('SELECT * FROM model_drafts WHERE owner=? AND idem=?',(p['id'],idem)).fetchone()
                if old:
                    if old['scenario']!=scenario: raise Problem(409,'相同幂等键对应不同场景')
                    if old['result'] is None: raise Problem(409,'该请求曾中断；请使用新幂等键')
                    return dict(json.loads(old['result']),duplicate=True)
                db.execute('INSERT INTO model_drafts VALUES(?,?,?,NULL)',(p['id'],idem,scenario))
                live=bool(self.client and self.client.reserve())
                if live: db.execute('INSERT INTO model_calls VALUES(?,?)',(uid(),s.clock()))
            title, body=SCENARIOS[scenario]
            draft={'title':title,'body':body+' 待你核对批准后，仅保存本地 outbox。'}
            source='offline'; reason='disabled' if not self.client else 'budget_exhausted'; usage={}
            if live:
                try:
                    draft,usage=self.client.generate(scenario)
                    source='model'; reason='success'
                except Exception:
                    # Never log exception strings: providers may echo credentials or content.
                    reason='provider_or_validation_error'
            with s.tx() as db:
                ident=uid()
                db.execute('INSERT INTO actions VALUES(?,?,?,?,?,?)',(ident,p['id'],draft['title'],draft['body'],'pending',s.clock()))
                result={'id':ident,'status':'pending','source':source,'reason':reason,'usage':usage,'synthetic':True,'duplicate':False}
                db.execute('UPDATE model_drafts SET result=? WHERE owner=? AND idem=?',(dump(result),p['id'],idem))
                s.log(db,p['id'],'model.draft',{'action':ident,'source':source,'reason':reason,'usage':usage,'scenario':scenario})
            return result

if __name__=='__main__':
    try:
        request=json.loads(sys.stdin.read(16384))
        print(dump(ModelClient(request['config'])._generate(request['scenario'])))
    except Exception:
        sys.exit(1)
