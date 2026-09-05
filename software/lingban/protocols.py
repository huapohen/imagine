import datetime
import hashlib
import json
from .core import Problem, dump, exact, obj, text, uid

MCP_VERSION='2025-06-18'
A2A_VERSION='0.3.0'

def rpc_error(ident,code,message):
    return {'jsonrpc':'2.0','id':ident,'error':{'code':code,'message':message}}

def valid_request(req):
    return (isinstance(req,dict) and req.get('jsonrpc')=='2.0' and isinstance(req.get('method'),str)
            and ('id' not in req or (not isinstance(req['id'],bool) and isinstance(req['id'],(int,str)))))

def agent_card(base):
    return {'name':'灵伴 LINGBAN · 合成演示','description':'电脑侧离线规则 Agent。A2A 0.3.0 JSON-RPC 子集，未认证；仅同步文本摘要，不外发消息。',
      'url':base+'/a2a','version':'0.1.0','protocolVersion':A2A_VERSION,'preferredTransport':'JSONRPC',
      'capabilities':{'streaming':False,'pushNotifications':False,'stateTransitionHistory':False},
      'defaultInputModes':['text/plain'],'defaultOutputModes':['text/plain'],
      'securitySchemes':{'bearer':{'type':'http','scheme':'bearer'}},'security':[{'bearer':[]}],
      'skills':[{'id':'local-summary','name':'授权范围内的任务摘要','description':'员工个人任务或企业合规聚合；合成数据。支持 message/send、tasks/get。','tags':['offline','synthetic','summary']}],
      'supportsAuthenticatedExtendedCard':False}

class A2A:
    def __init__(self,store): self.store=store
    def handle(self,p,req):
        if not valid_request(req) or 'id' not in req: return rpc_error(None,-32600,'Invalid Request')
        ident=req['id']; method=req['method']
        if p.get('plugin_id'): return rpc_error(ident,-32602,'Plugin tokens are not permitted for A2A')
        try:
            params=obj(req.get('params',{}))
            if method=='message/send': result=self.send(p,params)
            elif method=='tasks/get': result=self.get(p,params)
            else: return rpc_error(ident,-32601,'Method not found (supported subset: message/send, tasks/get)')
            return {'jsonrpc':'2.0','id':ident,'result':result}
        except Problem as e:
            return rpc_error(ident, -32001 if e.status==404 else -32005 if e.status==415 else -32602,e.message)
    def send(self,p,params):
        exact(params,{'message','configuration'})
        config=obj(params.get('configuration',{})); exact(config,{'blocking','acceptedOutputModes','historyLength'})
        if config.get('blocking',True) is not True: raise Problem(400,'此子集仅支持 blocking=true')
        modes=config.get('acceptedOutputModes',['text/plain'])
        if not isinstance(modes,list) or 'text/plain' not in modes: raise Problem(415,'Only text/plain output is supported')
        history=config.get('historyLength',10)
        if isinstance(history,bool) or not isinstance(history,int) or not 0<=history<=100: raise Problem(400,'historyLength 范围为 0..100')
        msg=obj(params.get('message')); exact(msg,{'kind','role','messageId','parts','taskId','contextId'})
        mid=text(msg.get('messageId'),'messageId',128)
        if msg.get('kind')!='message' or msg.get('role')!='user': raise Problem(400,'需要 kind=message, role=user')
        if 'taskId' in msg or 'contextId' in msg: raise Problem(400,'此子集仅支持新建任务；不支持继续已有上下文')
        parts=msg.get('parts')
        if not isinstance(parts,list) or not 1<=len(parts)<=8: raise Problem(400,'需要 1..8 个文本部分')
        for part in parts:
            obj(part)
            if part.get('kind')!='text': raise Problem(415,'Only text parts are supported')
            exact(part,{'kind','text'}); text(part.get('text'),'text',2000)
        digest=hashlib.sha256(dump(msg).encode()).hexdigest()
        with self.store.tx() as db:
            old=db.execute('SELECT * FROM a2a WHERE owner=? AND message_id=?',(p['id'],mid)).fetchone()
            if old:
                if old['digest']!=digest: raise Problem(400,'messageId 已用于其他内容')
                task=json.loads(old['task'])
            else:
                tid=uid(); cid=uid()
                def stamp(): return datetime.datetime.fromtimestamp(self.store.clock(),datetime.timezone.utc).isoformat().replace('+00:00','Z')
                task={'id':tid,'contextId':cid,'kind':'task','status':{'state':'submitted','timestamp':stamp()},'history':[msg]}
                self.store.log(db,p['id'],'a2a.submitted',{'task':tid})
                task['status']={'state':'working','timestamp':stamp()}
                self.store.log(db,p['id'],'a2a.working',{'task':tid})
                if p['role']=='employee':
                    rows=db.execute('SELECT state,COUNT(*) n FROM tasks WHERE owner=? GROUP BY state',(p['id'],)).fetchall()
                    counts={r['state']:r['n'] for r in rows}
                    summary='合成演示 · 个人任务摘要：待办 %s，阻塞 %s，完成 %s。仅运行本地规则，没有对外执行动作。'%(counts.get('open',0),counts.get('blocked',0),counts.get('done',0))
                else: summary=dump(self.store.enterprise(p))
                reply={'kind':'message','role':'agent','messageId':uid(),'contextId':cid,'taskId':tid,'parts':[{'kind':'text','text':summary}]}
                task['history'].append(reply)
                task['status']={'state':'completed','timestamp':stamp(),'message':reply}
                task['artifacts']=[{'artifactId':uid(),'name':'合成业务摘要','parts':reply['parts']}]
                db.execute('INSERT INTO a2a VALUES(?,?,?,?,?)',(tid,p['id'],mid,digest,dump(task)))
                self.store.log(db,p['id'],'a2a.completed',{'task':tid})
        return self.trim(task,history)
    def get(self,p,params):
        exact(params,{'id','historyLength'}); tid=text(params.get('id'),'id',128)
        history=params.get('historyLength',10)
        if isinstance(history,bool) or not isinstance(history,int) or not 0<=history<=100: raise Problem(400,'historyLength 范围为 0..100')
        with self.store.lock: row=self.store.db.execute('SELECT task FROM a2a WHERE id=? AND owner=?',(tid,p['id'])).fetchone()
        if not row: raise Problem(404,'Task not found')
        return self.trim(json.loads(row['task']),history)
    @staticmethod
    def trim(task,n):
        task['history']=task.get('history',[])[-n:] if n else []
        return task
