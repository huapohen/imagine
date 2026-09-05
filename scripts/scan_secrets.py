#!/usr/bin/env python3
"""Scan Git-selected text without ever printing a matched credential."""
import argparse, hashlib, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = {
    'api_key': re.compile(rb'\bsk-(?:api-|ws-)?[A-Za-z0-9_-]{24,}'),
    'github_token': re.compile(rb'\bgh[pousr]_[A-Za-z0-9]{30,}'),
    'database_credential': re.compile(rb'postgres(?:ql)?://[^\s/:]+:[^\s/@]+@[^\s]+'),
    'private_key': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
}

def main():
    p=argparse.ArgumentParser();p.add_argument('--staged',action='store_true');a=p.parse_args()
    args=['git','diff','--cached','--name-only','--diff-filter=ACM','-z'] if a.staged else ['git','ls-files','-z']
    names=subprocess.check_output(args,cwd=ROOT).split(b'\0')
    findings=[];scanned=0
    for raw in names:
        if not raw:continue
        name=raw.decode();file=ROOT/name
        if not file.is_file():continue
        data=subprocess.check_output(['git','show',':'+name],cwd=ROOT) if a.staged else file.read_bytes()
        if b'\0' in data[:8192]:continue
        scanned+=1
        for rule,rx in RULES.items():
            for match in rx.finditer(data):
                line=data[:match.start()].count(b'\n')+1
                fingerprint=hashlib.sha256(match.group()).hexdigest()[:12]
                findings.append(f'{name}:{line} {rule} sha256:{fingerprint}')
    for f in findings:print(f)
    print(f'Scanned {scanned} text files; {len(findings)} potential credentials; matched values never printed.')
    return bool(findings)

if __name__=='__main__':raise SystemExit(main())
