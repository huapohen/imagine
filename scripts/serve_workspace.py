#!/usr/bin/env python3
"""Serve only reviewable project artifacts on localhost; never serve local state."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
import argparse

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"docs", "hardware", "pitch", "media"}
EXTENSIONS = {".html", ".css", ".js", ".json", ".md", ".txt", ".csv", ".pdf", ".pptx", ".png", ".jpg", ".jpeg", ".svg", ".webp", ".mp4", ".webm", ".gif", ".stl", ".step", ".stp", ".scad", ".kicad_pcb", ".kicad_sch", ".zip"}
BLOCKED = {"downloads", "tools", "vendor", "__pycache__", "node_modules", "snapshots"}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        route = unquote(urlsplit(self.path).path)
        relative = Path(route.lstrip("/") or "index.html")
        parts = relative.parts
        if any(part.startswith(".") or part in BLOCKED for part in parts):
            return self.send_error(404)
        if len(parts) == 1:
            valid = parts[0] in {"index.html", "README.md"}
        else:
            valid = parts[0] in ALLOWED
        target = (ROOT / relative).resolve()
        if not valid or ROOT not in target.parents or target.suffix.lower() not in EXTENSIONS or not target.is_file():
            return self.send_error(404)
        if target.suffix in {".html", ".js", ".css", ".json"}:
            self.no_cache = True
        return super().do_GET()

    def do_HEAD(self):
        # No private path metadata through HEAD; public GET is the only artifact route.
        return self.send_error(405)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        # Request URLs can contain data; do not log them.
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8766)
    options = parser.parse_args()
    print(f"Imagine artifacts: http://127.0.0.1:{options.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", options.port), Handler).serve_forever()
