#!/usr/bin/env python3
"""Disposable, offline synthetic server for verify_browser.mjs; no model calls."""
import json
import os
import signal
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "software"))
from lingban.core import Store
from lingban.server import Server

os.umask(0o077)
state = ROOT / ".local"
state.mkdir(exist_ok=True)
store = Store()
tokens_path = state / "browser-qa-tokens.json"
tokens_path.write_text(json.dumps(store.seed()))
tokens_path.chmod(0o600)
server = Server(("127.0.0.1", 18765), store)
server.worker.start()
signal.signal(signal.SIGTERM, lambda *_: threading.Thread(target=server.shutdown, daemon=True).start())
print("Synthetic browser QA server: http://127.0.0.1:18765 (temporary in-memory database)", flush=True)
try:
    server.serve_forever()
finally:
    server.worker.stop()
    server.server_close()
    store.close()
    tokens_path.unlink(missing_ok=True)
