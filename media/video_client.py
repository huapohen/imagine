#!/usr/bin/env python3
"""MiniMax H3 guarded client. Only the controller may invoke submit. Stdlib only."""
import argparse, contextlib, datetime, decimal, fcntl, hashlib, json, os, pathlib, re, sys, urllib.error, urllib.parse, urllib.request
ROOT = pathlib.Path(__file__).resolve().parent
LEDGER = ROOT / 'video_ledger.json'
API = 'https://api.minimax.cn'
D = decimal.Decimal

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(b): return hashlib.sha256(b).hexdigest()
def canonical(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def save(path,data):
    tmp=path.with_suffix(path.suffix+'.tmp')
    fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w') as f:
        json.dump(data,f,ensure_ascii=False,indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)
def read(path): return json.loads(path.read_text())
@contextlib.contextmanager
def locked():
    with open(ROOT/'video_ledger.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        ledger=read(LEDGER) if LEDGER.exists() else {'budget_cny':'100','created_at':now(),'entries':{}}
        yield ledger

def price(payload):
    sources=read(ROOT/'sources.json'); s=next((x for x in sources if x['id']=='pricing-paygo.md'),None)
    doc=ROOT/'pricing-paygo.md'
    if not s or s['url']!='https://platform.minimaxi.com/docs/guides/pricing-paygo.md' or digest(doc.read_bytes())!=s['sha256']:
        raise ValueError('Missing or changed official pricing evidence; submission refused')
    age=datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(s['retrieved_at'])
    if age.total_seconds()<0 or age.total_seconds()>7*86400: raise ValueError('Pricing snapshot older than 7 days; reverify official price')
    if not re.search(r'MiniMax-H3</div>\s*\|\s*2K\s*\|\s*按秒计费\s*\|\s*0\.80 元/秒',doc.read_text()):
        raise ValueError('Official 2K price not found; unknown prices are refused')
    if set(payload)-{'model','content','resolution','duration','ratio'}: raise ValueError('Unreviewed payload fields refused')
    if payload.get('model')!='MiniMax-H3' or payload.get('resolution')!='2K' or type(payload.get('duration')) is not int or payload['duration']!=15:
        raise ValueError('This authorized batch requires exact MiniMax-H3 / 2K / 15 seconds')
    content=payload.get('content',[]); text=[x for x in content if x.get('type')=='text']; images=[x for x in content if x.get('type')=='image_url']
    if len(text)!=1 or not isinstance(text[0].get('text'),str) or not 1<=len(text[0]['text'])<=7000: raise ValueError('Exactly one prompt of 1..7000 chars required')
    if len(content)!=len(text)+len(images) or len(images)>5: raise ValueError('Only text and up to 5 free images permitted; no video/audio/IR')
    for im in images:
        if set(im)-{'type','image_url','role'} or im.get('role') not in ('first_frame','last_frame','reference_image'): raise ValueError('Unsupported image role')
        url=im.get('image_url',{}).get('url','')
        if not (url.startswith('data:image/png;base64,') or url.startswith('data:image/jpeg;base64,') or urllib.parse.urlsplit(url).scheme=='https'): raise ValueError('Image must be HTTPS or PNG/JPEG data URL')
    if not images and payload.get('ratio')!='16:9': raise ValueError('Text-to-video requires 16:9 in this batch')
    if len(canonical(payload))>60*1024*1024: raise ValueError('Payload too large')
    return D('0.80')*payload['duration']

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): raise ValueError('Redirect refused; credentials remain on official API host')
def api(method,path,payload=None):
    url=API+path; p=urllib.parse.urlsplit(url)
    if p.scheme!='https' or p.hostname!='api.minimax.cn' or p.port not in (None,443) or not (p.path=='/v2/video_generation' or p.path.startswith('/v2/query/video_generation')):
        raise ValueError('Non-allowlisted API endpoint')
    key=os.environ.get('MINIMAX_API_KEY')
    if not key: raise ValueError('MINIMAX_API_KEY environment variable is required')
    req=urllib.request.Request(url,data=canonical(payload) if payload is not None else None,method=method,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    try:
        with urllib.request.build_opener(NoRedirect()).open(req,timeout=45) as r: raw=r.read(8*1024*1024)
    except urllib.error.HTTPError as e:
        raise RuntimeError('HTTP '+str(e.code)+'; no automatic retry; response body suppressed') from None
    except (urllib.error.URLError,TimeoutError,OSError):
        raise RuntimeError('Network outcome uncertain; no automatic retry') from None
    # Persist API response faithfully unless it inexplicably echoes the credential.
    if key.encode() in raw: raise RuntimeError('Credential echo detected; response not persisted')
    return json.loads(raw)

def entry_for(ledger,id):
    if id not in ledger['entries']: raise ValueError('No reserved entry for this id')
    return ledger['entries'][id]
def request_for(path,id):
    records=read(path)
    matches=[r for r in records if r['id']==id]
    if len(matches)!=1: raise ValueError('Request id missing or duplicated')
    return matches[0]['payload']
def validate_id(id):
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}',id or ''): raise ValueError('Invalid local id')
def main():
    p=argparse.ArgumentParser(); p.add_argument('command',choices=['plan','submit','poll','list','attach','download']); p.add_argument('--requests',type=pathlib.Path,default=ROOT/'requests.json'); p.add_argument('--id'); p.add_argument('--budget-cny',type=D); p.add_argument('--task-id'); p.add_argument('--page',type=int,default=1)
    a=p.parse_args()
    if a.command=='plan':
        rows=read(a.requests); costs=[price(r['payload']) for r in rows]
        if len(rows)>8 or len({r['id'] for r in rows})!=len(rows) or sum(costs)>100: raise ValueError('Batch exceeds authorization')
        print(json.dumps({'count':len(rows),'total_cny':str(sum(costs)),'per_video_cny':[str(c) for c in costs],'network_calls':0})); return
    if a.command=='list':
        response=api('GET','/v2/query/video_generation?'+urllib.parse.urlencode({'page_num':a.page,'page_size':20,'filter.model':'MiniMax-H3','filter.task_type':'generation'}))
        save(ROOT/'task-list-private.json',response); print('Saved task-list-private.json; reconcile locally, no auto-attachment'); return
    validate_id(a.id)
    with locked() as ledger:
        if a.command=='submit':
            if a.budget_cny is None or a.budget_cny<=0 or a.budget_cny>100: raise ValueError('Explicit --budget-cny required, maximum 100')
            if not os.environ.get('MINIMAX_API_KEY'): raise ValueError('MINIMAX_API_KEY is missing')
            payload=request_for(a.requests,a.id); cost=price(payload)
            if a.id in ledger['entries']: raise ValueError('ID already reserved; do not resubmit. Poll or reconcile/attach instead')
            spent=sum(D(e['reserved_cny']) for e in ledger['entries'].values())
            if len(ledger['entries'])>=8 or spent+cost>min(a.budget_cny,D(ledger['budget_cny'])): raise ValueError('Batch count or budget exceeded')
            entry={'id':a.id,'request_sha256':digest(canonical(payload)),'model':payload['model'],'resolution':payload['resolution'],'duration':payload['duration'],'image_count':sum(x['type']=='image_url' for x in payload['content']),'reserved_cny':str(cost),'created_at':now(),'status':'submission_uncertain','task_id':None}
            ledger['entries'][a.id]=entry; save(LEDGER,ledger) # reserve durably BEFORE outbound request
            response=api('POST','/v2/video_generation',payload)
            save(ROOT/(a.id+'.create.response.json'),response)
            task_id=response.get('task_id')
            if not isinstance(task_id,str) or not re.fullmatch(r'[A-Za-z0-9_-]+',task_id): raise RuntimeError('Response missing valid task_id; reservation retained')
            entry.update(task_id=task_id,status='submitted'); save(LEDGER,ledger)
            print(json.dumps({'id':a.id,'task_id':task_id,'reserved_total_cny':str(spent+cost)})); return
        entry=entry_for(ledger,a.id)
        if a.command=='attach':
            if entry.get('task_id'): raise ValueError('Entry already has task_id')
            if not re.fullmatch(r'[A-Za-z0-9_-]+',a.task_id or ''): raise ValueError('Invalid task id')
            task=api('GET','/v2/query/video_generation/'+a.task_id).get('task',{})
            if any(task.get(k)!=entry[k] for k in ('model','resolution','duration')): raise ValueError('Reconciled task specifications mismatch')
            if any(e.get('task_id')==a.task_id for e in ledger['entries'].values()): raise ValueError('Task already attached')
            entry.update(task_id=a.task_id,status=task.get('status','unknown')); save(LEDGER,ledger); print('Attached; budget reservation retained'); return
        task_id=entry.get('task_id')
        if not task_id: raise ValueError('Uncertain submission: list and reconcile before attach; never resubmit')
        if a.command=='poll':
            response=api('GET','/v2/query/video_generation/'+task_id); task=response.get('task',{})
            save(ROOT/(a.id+'.query.response.json'),response)
            entry.update(status=task.get('status','unknown'),updated_at=now(),usage=task.get('usage',{}))
            if task.get('content',{}).get('url'): entry['download_url']=task['content']['url']
            save(LEDGER,ledger); print(json.dumps({'id':a.id,'task_id':task_id,'status':entry['status'],'usage':entry['usage']})); return
        url=entry.get('download_url'); u=urllib.parse.urlsplit(url or '')
        # Exact OSS host observed in a successful response from the authenticated official API.
        allowed=('cdn.hailuoai.com','filecdn.minimax.chat','video-product.cdn.minimax.io','algeng-video-infer.oss-cn-shanghai.aliyuncs.com')
        if entry.get('status')!='succeeded' or u.scheme!='https' or u.hostname not in allowed or u.port not in (None,443): raise ValueError('No successful official allowlisted download URL; query/review CDN before downloading')
        out=ROOT/'generated'; out.mkdir(exist_ok=True); dest=out/(a.id+'.mp4'); part=dest.with_suffix('.mp4.part')
        # No Authorization header on CDN requests, no redirects. Bounded network read.
        with urllib.request.build_opener(NoRedirect()).open(url,timeout=45) as r, open(part,'wb') as f:
            import time
            deadline=time.monotonic()+50
            while True:
                if time.monotonic()>deadline: raise RuntimeError('Download 50-second budget reached; partial retained')
                b=r.read(1024*1024)
                if not b: break
                f.write(b)
        os.replace(part,dest); entry['local_file']=str(dest.relative_to(ROOT)); entry['file_sha256']=digest(dest.read_bytes()); save(LEDGER,ledger); print(json.dumps({'saved':entry['local_file'],'sha256':entry['file_sha256']}))
if __name__=='__main__':
    try: main()
    except Exception as e:
        # No traceback or API raw body; keys are never printed.
        print('ERROR: '+str(e).replace(os.environ.get('MINIMAX_API_KEY','__NO_KEY__'),'[REDACTED]'),file=sys.stderr); sys.exit(1)
