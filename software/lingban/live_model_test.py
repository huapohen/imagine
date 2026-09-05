"""Explicit local-only live test; emits sanitized metadata, never draft text."""
import argparse
import http.client
import json
from pathlib import Path
import threading
import time
from .core import Store
from .model import ModelClient, local_config, SCENARIOS
from .server import Server


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--local-only-synthetic-opt-in',action='store_true')
    args=parser.parse_args()
    if not args.local_only_synthetic_opt_in: parser.error('需要显式 --local-only-synthetic-opt-in')
    config=local_config(Path(__file__).resolve().parents[2]/'.env')
    client=ModelClient(config)
    if config['MAX_CALLS']-client.used()<3: parser.error('三场景需至少3次剩余预算；不执行任何新调用')
    store=Store(); tokens=store.seed()
    server=Server(('127.0.0.1',0),store,client)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    def request(path,body,role='employee'):
        conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=50)
        conn.request('POST',path,json.dumps(body),{'Authorization':'Bearer '+tokens[role],'Content-Type':'application/json'})
        r=conn.getresponse(); value=json.loads(r.read()); conn.close();return r.status,value
    report={'model':config['NAME'],'provider':config['PROVIDER'],'endpoint':config['BASE_URL']+'/responses',
            'reasoning_effort':config['REASONING_EFFORT'],'max_output_tokens':config['MAX_OUTPUT_TOKENS'],
            'wall_timeout_seconds':config['TIMEOUT_SECONDS'],'max_calls':config['MAX_CALLS'],'calls_before':client.used(),'scenarios':[]}
    try:
        assert request('/api/model/propose',{'scenario':'meeting','idempotency_key':'unauthorized','synthetic_consent':True},'enterprise')[0]==403
        for scenario in SCENARIOS:
            body={'scenario':scenario,'idempotency_key':'live-'+scenario,'synthetic_consent':True}
            start=time.monotonic();status,result=request('/api/model/propose',body)
            elapsed=round(time.monotonic()-start,2)
            assert status==200 and result['status']=='pending'
            assert not store.state(store.person('demo-alice'))['outbox']
            duplicate=request('/api/model/propose',body)[1]
            assert duplicate['duplicate'] and duplicate['id']==result['id']
            report['scenarios'].append({'scenario':scenario,'elapsed_seconds':elapsed,'source':result['source'],'reason':result['reason'],'usage':result['usage'],'pending':True,'duplicate_no_new_call':True,'outbox_empty':True})
        report['calls_after']=client.used()
        report['live_success']=all(r['source']=='model' for r in report['scenarios'])
        print(json.dumps(report,ensure_ascii=False,indent=2))
        if not report['live_success']:raise SystemExit(1)
    finally:
        server.shutdown();server.server_close();thread.join();store.close()

if __name__=='__main__':main()
