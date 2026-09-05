#!/usr/bin/env python3
"""Hash exact release assets; never includes credentials, runtime state or tools."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
TAG = "v0.1.0-evt-a-20260906"
paths = sorted((ROOT / "media/final").glob("0*.mp4"))
assert len(paths) == 8
paths += [ROOT / p for p in ["media/final/LINGBAN_8_concepts_2min.mp4", "media/demo/lingban-software-demo.mp4",
          "hardware/delivery/lingban_evt_a_review.zip", "hardware/delivery/lingban_factory_review.zip",
          "release/lingban_minimax_originals.zip"]]
assets = [{"name": p.name, "local_path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size,
           "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
(ROOT / "docs/operations/RELEASE_ASSETS.json").write_text(json.dumps({"tag": TAG, "assets": assets}, indent=2) + "\n")
(ROOT / "release/SHA256SUMS.txt").write_text("".join(a['sha256'] + "  " + a['name'] + "\n" for a in assets))
print(json.dumps({"tag": TAG, "assets": len(assets), "bytes": sum(a['bytes'] for a in assets)}))
