import argparse
import json
import os
from pathlib import Path
import signal
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, unquote
from .core import Store, Worker, Problem, exact, text
from .protocols import A2A, agent_card, rpc_error
from .model import DraftService, ModelClient, local_config

ROOT=Path(__file__).resolve().parents[1]
MAX_BODY=32768

class Server(ThreadingHTTPServer):
    daemon_threads=True
    allow_reuse_address=True
    def __init__(self,address,store,model_client=None):
        self.store=store; self.a2a=A2A(store); self.worker=Worker(store)
        self.drafts=DraftService(store,model_client)
        super().__init__(address,Handler)
        self.base='http://127.0.0.1:'+str(self.server_port)

class Handler(BaseHTTPRequestHandler):
    server_version='Lingban/0.1'
    def setup(self):
        super().setup(); self.connection.settimeout(5)
    def log_message(self,fmt,*args): pass  # No tokens, payloads or query strings in access logs.
    def send(self,status,data,ctype='application/json; charset=utf-8'):
        body=data if isinstance(data,bytes) else json.dumps(data,ensure_ascii=False,allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        self.send_header('Connection','close'); self.end_headers(); self.close_connection=True
        self.wfile.write(body)
    def boundary(self):
        hosts={'127.0.0.1:'+str(self.server.server_port),'localhost:'+str(self.server.server_port)}
        if self.headers.get('Host') not in hosts: raise Problem(403,'Host 不在本地允许列表')
        origin=self.headers.get('Origin')
        if origin and origin not in {'http://'+h for h in hosts}: raise Problem(403,'跨域请求被拒绝')
        if self.headers.get('Sec-Fetch-Site')=='cross-site': raise Problem(403,'跨站请求被拒绝')
    def principal(self):
        auth=self.headers.get('Authorization','')
        if not auth.startswith('Bearer '): raise Problem(401,'需要 Bearer 访问令牌')
        return self.server.store.authenticate(auth[7:])
    def body(self):
        if self.headers.get('Transfer-Encoding'): raise Problem(400,'不支持分块请求体')
        lengths=self.headers.get_all('Content-Length') or []
        if len(lengths)!=1: raise Problem(411,'需要单一 Content-Length')
        try: length=int(lengths[0])
        except ValueError: raise Problem(400,'Content-Length 无效')
        if not 0<length<=MAX_BODY: raise Problem(413,'请求体上限 32 KiB')
        if self.headers.get('Content-Type','').split(';')[0].strip()!='application/json': raise Problem(415,'需要 application/json')
        raw=self.rfile.read(length)
        if len(raw)!=length: raise Problem(400,'请求体不完整')
        try:
            return json.loads(raw.decode('utf-8'),parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite')))
        except (ValueError,UnicodeError,RecursionError):
            raise Problem(400,'JSON 解析失败')
    def do_GET(self): self.run_request('GET')
    def do_POST(self): self.run_request('POST')
    def run_request(self,method):
        try:
            self.boundary(); path=unquote(urlsplit(self.path).path)
            if method=='GET' and path in ('/','/app.js','/style.css','/crystal-mouse.svg'):
                names={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/style.css':('style.css','text/css; charset=utf-8'),'/crystal-mouse.svg':('crystal-mouse.svg','image/svg+xml')}
                filename,ctype=names[path]
                return self.send(200,(ROOT/'web'/filename).read_bytes(),ctype)
            if method=='GET' and path=='/health': return self.send(200,{'ok':self.server.worker.error is None,'worker_error':self.server.worker.error,'synthetic':True})
            if method=='GET' and path=='/.well-known/agent-card.json': return self.send(200,agent_card(self.server.base))
            p=self.principal(); store=self.server.store
            if p.get('plugin_id') and path not in ('/api/events','/api/hardware','/api/plugins/'+p['plugin_id']+'/tasks'):
                raise Problem(403,'插件令牌仅可访问 manifest 授权的专用接口')
            if method=='GET':
                if path=='/api/me': result={'person':p,'synthetic':True}
                elif path=='/api/model/status': result=self.server.drafts.status(p)
                elif path=='/api/state': result=store.state(p)
                elif path=='/api/enterprise/summary': result=store.enterprise(p)
                elif path.startswith('/api/plugins/') and path.endswith('/tasks'): result=store.plugin_read(p,path.split('/')[3])
                else: raise Problem(404,'接口不存在')
            else:
                try: data=self.body()
                except Problem as e:
                    if path=='/a2a' and e.message=='JSON 解析失败': return self.send(200,rpc_error(None,-32700,'Parse error'))
                    raise
                if path=='/a2a': result=self.server.a2a.handle(p,data)
                elif path=='/api/events': result=store.ingest(p,data)
                elif path=='/api/model/propose': result=self.server.drafts.propose(p,data)
                elif path=='/api/actions': result=store.propose(p,data)
                elif path=='/api/actions/decide':
                    exact(data,{'id','decision'}); result=store.decide(p,text(data.get('id'),'id',100),data.get('decision'))
                elif path=='/api/alerts/feedback':
                    exact(data,{'id','feedback'}); result=store.feedback(p,text(data.get('id'),'id',100),data.get('feedback'))
                elif path=='/api/consent':
                    exact(data,{'enabled'}); result=store.set_consent(p,data.get('enabled'))
                elif path=='/api/share': result=store.share(p,data)
                elif path=='/api/plugins': result=store.register_plugin(p,data)
                elif path=='/api/plugins/token':
                    exact(data,{'id'}); result=store.plugin_token(p,text(data.get('id'),'id',80))
                elif path=='/api/hardware': result=store.hardware(p,data)
                elif path=='/api/scenarios':
                    exact(data,{'name'}); result=store.scenario(p,data.get('name'))
                else: raise Problem(404,'接口不存在')
            self.send(200,result)
        except Problem as e: self.send(e.status,{'error':e.message})
        except (TimeoutError,ConnectionError,OSError): self.close_connection=True
        except Exception:
            self.send(500,{'error':'本地服务内部错误；请检查服务测试与数据版本'})

def main():
    parser=argparse.ArgumentParser(description='灵伴离线合成演示，仅绑定本地回环地址')
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--host',choices=['127.0.0.1','0.0.0.0'],default='127.0.0.1')
    parser.add_argument('--allow-network',action='store_true',help='显式允许容器内部监听全部网卡；仍需安全端口映射')
    parser.add_argument('--db',default=str(ROOT/'data'/'lingban.sqlite3'))
    parser.add_argument('--local-model-test',action='store_true',help='仅本机：加载根 .env，允许限额固定合成场景模型草稿')
    args=parser.parse_args()
    model_client=None
    if args.local_model_test:
        if args.host!='127.0.0.1': parser.error('模型测试仅限回环地址')
        try: model_client=ModelClient(local_config(ROOT.parent/'.env'))
        except (ValueError,OSError): parser.error('本机模型配置无效；未启用外部调用')
    if args.host!='127.0.0.1' and not args.allow_network: parser.error('非回环绑定需显式 --allow-network；勿暴露真实数据')
    os.umask(0o077)
    dbpath=Path(args.db).resolve()
    if ROOT not in dbpath.parents: parser.error('数据库必须位于 software/ 内')
    dbpath.parent.mkdir(parents=True,exist_ok=True)
    store=Store(str(dbpath))
    # Rotate demo credentials on startup; old browser sessions must sign in again.
    with store.tx() as db: db.execute('DELETE FROM tokens')
    tokens=store.seed()
    try: server=Server((args.host,args.port),store,model_client)
    except OSError as e: parser.exit(1,'启动失败: '+str(e)+'\n')
    print('\n灵伴 LINGBAN · 合成数据 / 消息仅存本地 / '+('固定合成场景模型测试已启用' if model_client else '离线模式'),flush=True)
    for role,token in tokens.items(): print(('员工' if role=='employee' else '企业')+'工作台: '+server.base+'/#token='+token,flush=True)
    print('令牌仅用于本地演示；链接持有者拥有对应角色权限。Ctrl+C 停止。\n',flush=True)
    server.worker.start()
    def stop(*_): threading.Thread(target=server.shutdown,daemon=True).start()
    signal.signal(signal.SIGTERM,stop)
    try: server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt: pass
    finally: server.worker.stop(); server.server_close(); store.close()

if __name__=='__main__': main()
