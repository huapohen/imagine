#!/usr/bin/env python3
"""Combine reviewed hardware, firmware source and RFQ using exact allowlists."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/delivery"
SECRET = re.compile(rb"\bsk-(?:api-|ws-)?[A-Za-z0-9_-]{24,}|\bgh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")

def allowed(name):
    parts = PurePosixPath(name).parts
    return (bool(parts) and not name.startswith("/")
            and not any(p.startswith(".") or p in {"tools", "downloads", "__pycache__", "data", "build", "test-output"} for p in parts))

def main():
    archive = OUT / "lingban_evt_a_review.zip"
    blobs = {}
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for entry in z.infolist():
            if entry.is_dir(): continue
            # The hardware zip also includes tool installation scripts; factory users do not need them.
            if "tools" in PurePosixPath(entry.filename).parts: continue
            assert allowed(entry.filename), "Unexpected archive path"
            blobs[entry.filename] = z.read(entry)
    folders = ["docs/manufacturing-commercial", "firmware/src", "firmware/include", "firmware/test"]
    for folder in folders:
        for path in (ROOT / folder).rglob("*"):
            name = path.relative_to(ROOT).as_posix()
            if path.is_file() and allowed(name) and path.suffix in {".md", ".csv", ".cpp", ".hpp", ".json"}:
                blobs[name] = path.read_bytes()
    files = ["firmware/README.md", "firmware/platformio.ini", "firmware/serial-protocol.md", "firmware/test.sh",
             "docs/software/serial-protocol.md", "docs/software/serial-golden-vectors.tsv",
             "docs/verification/HARDWARE_REVIEW.md", "docs/verification/hal_independent.cpp"]
    for name in files:
        path = ROOT / name
        if path.is_file(): blobs[name] = path.read_bytes()
    blobs["FACTORY_START_HERE.md"] = (ROOT / "docs/manufacturing-commercial/FACTORY_START_HERE.md").read_bytes()
    for name, data in blobs.items():
        assert not SECRET.search(data), "Credential-like content in " + name
    manifest = {name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()} for name, data in sorted(blobs.items())}
    manifest_bytes = (json.dumps({"status": "NOT-FOR-FAB", "files": manifest}, indent=2, ensure_ascii=False) + "\n").encode()
    blobs["FACTORY_MANIFEST.json"] = manifest_bytes
    target = OUT / "lingban_factory_review.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, data in sorted(blobs.items()): z.writestr(name, data)
    with zipfile.ZipFile(target) as z: assert z.testzip() is None
    (OUT / "factory-manifest.json").write_bytes(manifest_bytes)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    (OUT / "FACTORY_SHA256SUMS.txt").write_text(digest + "  " + target.name + "\n")
    print(json.dumps({"path": target.relative_to(ROOT).as_posix(), "files": len(blobs), "bytes": target.stat().st_size, "sha256": digest}))

if __name__ == "__main__": main()
