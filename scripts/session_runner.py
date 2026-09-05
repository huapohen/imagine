#!/usr/bin/env python3
"""Run a scoped Codex CLI task, recording the thread ID and bounded recovery."""
import argparse,datetime,json,os,subprocess,time,fcntl
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('role');p.add_argument('--effort',default='high');p.add_argument('--resume');a=p.parse_args()
local=ROOT/'.local/sessions';local.mkdir(parents=True,exist_ok=True)
prompt=(local/(a.role+'.prompt.md')).read_text()
record={'role':a.role,'model':'gpt-6-astra','effort':a.effort,'pid':os.getpid(),'started_at':datetime.datetime.now().astimezone().isoformat(),'state':'starting','thread_id':a.resume,'attempt':0}
def save():
 (local/(a.role+'.status.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2))
 rows=[]
 for f in sorted(local.glob('*.status.json')):
  try: rows.append(json.loads(f.read_text()))
  except (ValueError,OSError): pass
 out=ROOT/'docs/operations/CLI_SESSIONS.json'
 with (local/'registry.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);out.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
for attempt in range(3):
 record['attempt']=attempt+1;record['state']='running';save()
 base=['codex','-a','never','-s','danger-full-access','-c',f'model_reasoning_effort="{a.effort}"','exec','-m','gpt-6-astra','--json','-o',str(local/(a.role+'.final.md'))]
 if record['thread_id']:
  base=['codex','-a','never','-s','danger-full-access','-c',f'model_reasoning_effort="{a.effort}"','exec','resume','-m','gpt-6-astra','--json','-o',str(local/(a.role+'.final.md')),record['thread_id'],'-']
 else: base+=['-']
 proc=subprocess.Popen(base,cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
 record['child_pid']=proc.pid;save()
 proc.stdin.write(prompt if attempt==0 else '继续。完成你被分配的任务和验证，遵守仓库AGENTS.md，保持原有成果。')
 proc.stdin.close()
 with (local/(a.role+'.jsonl')).open('a') as log:
  for line in proc.stdout:
   log.write(line);log.flush()
   try:
    e=json.loads(line)
    if e.get('type')=='thread.started': record['thread_id']=e['thread_id'];save();print(a.role, 'thread',record['thread_id'],flush=True)
    if e.get('type') in ['turn.completed','turn.failed','error']: print(a.role,e.get('type'),json.dumps(e,ensure_ascii=False)[:500],flush=True)
   except ValueError: pass
 code=proc.wait();record['exit_code']=code;record['updated_at']=datetime.datetime.now().astimezone().isoformat()
 if code==0: record['state']='completed';save();break
 record['state']='retry_pending' if attempt<2 else 'failed';save();print(a.role,'exit',code,'attempt',attempt+1,flush=True)
 if attempt<2: time.sleep(15*(attempt+1))
print(a.role,record['state'],flush=True)
