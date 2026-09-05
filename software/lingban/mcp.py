"""MCP 2025-06-18 stdio subset; stdout contains JSON-RPC only."""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit
from .core import Problem, exact, obj, text
from .protocols import MCP_VERSION, rpc_error, valid_request

TOOLS=[
 {'name':'tasks_list','description':'读取当前员工的任务记忆（合成演示）','inputSchema':{'type':'object','properties':{},'additionalProperties':False}},
 {'name':'events_ingest','description':'摄入有幂等键的合成任务/日程事件；服务端验证权限','inputSchema':{'type':'object','properties':{'idempotency_key':{'type':'string'},'type':{'type':'string','enum':['task.upsert','meeting.upsert','focus.set','break.due']},'payload':{'type':'object'},'plugin_id':{'type':'string'}},'required':['idempotency_key','type','payload'],'additionalProperties':False}},
 {'name':'action_propose','description':'提出需要人工审批的本地动作，不执行或外发','inputSchema':{'type':'object','properties':{'title':{'type':'string'},'body':{'type':'string'}},'required':['title','body'],'additionalProperties':False}},
 {'name':'enterprise_summary','description':'仅企业角色可读的 >=5 人明确授权业务聚合','inputSchema':{'type':'object','properties':{},'additionalProperties':False}},
]

class Client:
    def __init__(self,url,token):
        parsed=urlsplit(url)
        if parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','localhost') or parsed.username or parsed.password or parsed.path not in ('','/') or parsed.query or parsed.fragment:
            raise ValueError('MCP 只允许本地 HTTP 服务 URL')
        self.url=url.rstrip('/'); self.token=token
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs): return None
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    def call(self,path,data=None):
        req=urllib.request.Request(self.url+path,data=None if data is None else json.dumps(data,allow_nan=False).encode(),headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/json'})
        try:
            with self.opener.open(req,timeout=5) as response: return json.load(response)
        except urllib.error.HTTPError as e:
            raise Problem(e.code,json.load(e).get('error','HTTP error'))
        except (OSError,ValueError): raise Problem(503,'本地服务不可用')

class MCP:
    def __init__(self,client): self.client=client; self.phase='new'
    def handle(self,req):
        if not valid_request(req): return rpc_error(None,-32600,'Invalid Request')
        ident=req.get('id'); method=req['method']; notification='id' not in req
        if notification:
            if method=='notifications/initialized' and self.phase=='initializing': self.phase='ready'
            return None
        try:
            params=obj(req.get('params',{}))
            if method=='initialize':
                if self.phase!='new': return rpc_error(ident,-32600,'Already initialized')
                text(params.get('protocolVersion'),'protocolVersion',40); obj(params.get('capabilities')); info=obj(params.get('clientInfo')); text(info.get('name'),'name',100); text(info.get('version'),'version',50)
                self.phase='initializing'
                result={'protocolVersion':MCP_VERSION,'capabilities':{'tools':{'listChanged':False}},'serverInfo':{'name':'lingban-local','version':'0.1.0'},'instructions':'合成演示。支持 MCP 2025-06-18 tools 子集，未认证；人工审批在工作台，批准仅写本地 outbox。'}
            elif method=='ping': result={}
            elif self.phase!='ready': return rpc_error(ident,-32002,'Initialize and notifications/initialized required')
            elif method=='tools/list':
                exact(params,set()); result={'tools':TOOLS}
            elif method=='tools/call':
                exact(params,{'name','arguments'}); name=text(params.get('name'),'name',80); args=obj(params.get('arguments',{}))
                if name not in {x['name'] for x in TOOLS}: return rpc_error(ident,-32602,'Unknown tool')
                if name in ('tasks_list','enterprise_summary'): exact(args,set())
                if name=='events_ingest': exact(args,{'idempotency_key','type','payload','plugin_id'})
                if name=='action_propose': exact(args,{'title','body'})
                try:
                    if name=='tasks_list': value=self.client.call('/api/state')['tasks']
                    elif name=='events_ingest': value=self.client.call('/api/events',args)
                    elif name=='action_propose': value=self.client.call('/api/actions',args)
                    else: value=self.client.call('/api/enterprise/summary')
                    result={'content':[{'type':'text','text':json.dumps(value,ensure_ascii=False)}],'isError':False}
                except Problem as e: result={'content':[{'type':'text','text':e.message}],'isError':True}
            else: return rpc_error(ident,-32601,'Method not found')
            return {'jsonrpc':'2.0','id':ident,'result':result}
        except Problem as e: return rpc_error(ident,-32602,e.message)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--url',default='http://127.0.0.1:8765'); args=parser.parse_args()
    # Only an explicitly supplied variable, never a .env file or credential discovery.
    token=os.environ.get('LINGBAN_TOKEN','')
    if not token: parser.exit(1,'请显式传入 LINGBAN_TOKEN（本地服务访问令牌）\n')
    try: mcp=MCP(Client(args.url,token))
    except ValueError as e: parser.exit(1,str(e)+'\n')
    while True:
        line=sys.stdin.buffer.readline(32770)
        if not line: break
        if len(line)>32768:
            # Drain this single oversized frame without an unbounded allocation.
            while line and not line.endswith(b'\n'): line=sys.stdin.buffer.readline(32770)
            response=rpc_error(None,-32600,'Message exceeds 32 KiB')
        else:
            try:
                req=json.loads(line.decode('utf-8'),parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
                response=mcp.handle(req)
            except (ValueError,UnicodeError,RecursionError): response=rpc_error(None,-32700,'Parse error')
            except Exception: response=rpc_error(None,-32603,'Internal error')
        if response is not None: print(json.dumps(response,ensure_ascii=False),flush=True)

if __name__=='__main__': main()
