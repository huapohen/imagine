#!/usr/bin/env python3
"""Bounded, conservative local supervisor; usage/contract in ASSISTANT_STATUS.md."""
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT_ID = '01a0725c-ccf9-7192-8446-f23b0f6d55e3'
BASE = Path(__file__).resolve().parents[1]
TERMINAL = {'failed', 'error', 'crashed', 'exited', 'disconnected', 'rate_limited'}
ACTIVE = {'running', 'working', 'waiting', 'ui_wait', 'waiting_ui', 'waiting_for_input', 'retrying', 'completed', 'stopped'}

def read_json(path):
    try:
        if path.is_symlink() or path.stat().st_size > 65536:
            return {}
        value = json.loads(path.read_text())
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}

def stamp(value):
    try:
        parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed.timestamp() if parsed.tzinfo else None
    except (AttributeError, TypeError, ValueError, OverflowError):
        return None

def atomic(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(path)

def evidence(heartbeat, statuses, now, stale):
    at = stamp(heartbeat.get('at'))
    if heartbeat.get('thread_id') != ROOT_ID or at is None or now - at <= stale:
        return None
    roots = [heartbeat] + [s for s in statuses if s.get('thread_id') == ROOT_ID]
    # An active/waiting/completed root always vetoes recovery, even with old errors.
    if any(s.get('state') in ACTIVE for s in roots):
        return None
    for s in roots:
        if s.get('state') in TERMINAL and s.get('recovery_required') is True:
            failure = s.get('failure_id')
            failed_at = stamp(s.get('failed_at'))
            # Stable explicit incident identity, timestamp after last good heartbeat.
            if isinstance(failure, str) and failure and failed_at is not None and at <= failed_at <= now:
                return hashlib.sha256((ROOT_ID + ':' + failure).encode()).hexdigest()
    return None

def log_events(path):
    """Only structured CLI error/exit envelopes; never inspect tool/prompt text."""
    counts = {'error': 0, '429': 0, 'network': 0, 'exit': 0}
    try:
        if path.is_symlink():
            return counts
        with path.open('rb') as stream:
            size = stream.seek(0, 2)
            stream.seek(max(0, size - 65536))
            if size > 65536:
                stream.readline()
            lines = stream.read(65536).splitlines()
        for line in lines:
            try:
                event = json.loads(line)
            except (ValueError, UnicodeError):
                continue
            if not isinstance(event, dict):
                continue
            kind = event.get('type')
            if kind in {'error', 'turn.failed', 'thread.failed'}:
                counts['error'] += 1
                # Restrict to error envelope, never nested tool output or source text.
                err = event.get('error', event.get('message', ''))
                msg = json.dumps(err).lower()
                if '429' in msg or 'rate limit' in msg:
                    counts['429'] += 1
                if any(x in msg for x in ('network', 'disconnected', 'connection reset', 'connection refused', 'dns', 'timed out')):
                    counts['network'] += 1
            if kind in {'process.exited', 'session.exited'}:
                counts['exit'] += 1
    except OSError:
        pass
    return counts

def snapshot(base):
    statuses, summary = [], {}
    for path in sorted((base / '.local/sessions').glob('*.status.json')):
        status = read_json(path)
        statuses.append(status)
        role = path.name.removesuffix('.status.json')
        summary[role] = {k: status.get(k) for k in ('state', 'attempt', 'exit_code')}
        summary[role]['log_tail_counts'] = log_events(path.with_name(role + '.jsonl'))
    return statuses, summary

def self_test():
    now = 2000000000
    iso = lambda n: dt.datetime.fromtimestamp(n, dt.timezone.utc).isoformat()
    h = {'thread_id': ROOT_ID, 'at': iso(now-1000), 'state': 'working'}
    assert evidence(h, [], now, 300) is None
    fail = dict(h, state='failed', recovery_required=True, failure_id='incident-1', failed_at=iso(now-900))
    key = evidence(fail, [], now, 300)
    assert key and key == evidence(fail, [], now+100, 300)
    for patch in ({'state':'waiting_ui'}, {'state':'running'}, {'state':'completed'}, {'thread_id':'wrong'}, {'at':'bad'}, {'recovery_required':False}, {'failure_id':None}, {'failed_at':iso(now-2000)}, {'at':iso(now-10)}):
        assert evidence(dict(fail, **patch), [], now, 300) is None, patch
    assert evidence(h, [fail], now, 300) is None
    assert evidence(dict(h, state='unknown'), [dict(fail, thread_id='child')], now, 300) is None
    ledger = {key: 'attempted'}
    assert evidence(fail, [], now, 300) in ledger
    print('PASS: 14 synthetic eligibility/dedup assertions; no queue calls')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hours', type=float, default=10)
    parser.add_argument('--interval', type=float, default=60)
    parser.add_argument('--stale-seconds', type=float, default=600)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--once', action='store_true', help='Observe only, never queue')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not (0 < args.hours <= 10 and 10 <= args.interval <= 300 and args.stale_seconds >= 300):
        parser.error('hours must be (0,10], interval [10,300], stale-seconds >=300')
    state_dir = BASE / '.local/assistant-supervisor'
    state_dir.mkdir(parents=True, exist_ok=True)
    lock = (state_dir / 'supervisor.lock').open('w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        parser.error('supervisor already running')
    stopping = False
    def stop(*_):
        nonlocal stopping
        stopping = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    ledger_path = state_dir / 'ledger.json'
    ledger = read_json(ledger_path)
    # Corrupt persisted state must fail closed to preserve at-most-once behavior.
    if ledger_path.exists() and not ledger:
        parser.error('empty/invalid ledger; manual inspection required')
    ledger.setdefault('attempts', {})
    ledger.setdefault('next_allowed', 0)
    started = time.time()
    deadline = time.monotonic() + args.hours * 3600
    (state_dir / 'pid').write_text(str(os.getpid()) + '\n')
    try:
        while not stopping and time.monotonic() < deadline and not (state_dir / 'STOP').exists():
            now = time.time()
            statuses, summary = snapshot(BASE)
            heartbeat = read_json(BASE / '.local/root-heartbeat.json')
            incident = evidence(heartbeat, statuses, now, args.stale_seconds)
            report = {'pid':os.getpid(), 'started_at':started, 'checked_at':now, 'max_hours':args.hours,
                      'state':'observing', 'heartbeat':{k:heartbeat.get(k) for k in ('at','thread_id','state')},
                      'sessions':summary, 'eligible_incident':incident}
            if not args.once and incident and incident not in ledger['attempts'] and now >= ledger['next_allowed']:
                # Persist before subprocess: crash/timeout/uncertain acceptance never resends this incident.
                ledger['attempts'][incident] = {'at':now, 'result':'attempted'}
                ledger['next_allowed'] = now + 1800
                atomic(ledger_path, ledger)
                try:
                    result = subprocess.run(['codex','queue','--thread',ROOT_ID,'--message','继续'],
                                            cwd=BASE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
                    outcome = 'queued' if result.returncode == 0 else 'queue_failed'
                except (OSError, subprocess.TimeoutExpired):
                    outcome = 'queue_failed_or_unknown'
                ledger['attempts'][incident]['result'] = outcome
                atomic(ledger_path, ledger)
                report['queue_result'] = outcome
            atomic(state_dir / 'status.json', report)
            if args.once:
                break
            remaining = min(args.interval, max(0, deadline-time.monotonic()))
            end = time.monotonic()+remaining
            while not stopping and time.monotonic()<end and not (state_dir/'STOP').exists():
                time.sleep(min(1, max(0,end-time.monotonic())))
    finally:
        atomic(state_dir/'lifecycle.json', {'pid':os.getpid(), 'state':'stopped', 'at':time.time()})
        (state_dir/'pid').unlink(missing_ok=True)

if __name__ == '__main__':
    main()
