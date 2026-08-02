#!/usr/bin/env python3
"""Optional Workbench capability contract with a deterministic local fallback."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def detect() -> dict[str, str]:
    url = os.environ.get("WORKBENCH_URL", "")
    return {"status": "available" if url else "unavailable", "url": url, "fallback": "local-artifacts"}


def publish_local(root: Path, payload: dict[str, Any]) -> Path:
    target = root / ".product-studio" / "workbench-fallback.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"status": "local_fallback", "payload": payload}, indent=2) + "\n")
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("detect", "publish"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--payload", type=Path)
    args = parser.parse_args()
    capability = detect()
    if args.command == "detect":
        print(json.dumps(capability, indent=2))
    else:
        payload = json.loads(args.payload.read_text()) if args.payload else {"message": "phase checkpoint"}
        if capability["status"] == "available":
            print(json.dumps({"status": "available", "url": capability["url"], "payload": payload}, indent=2))
        else:
            print(json.dumps({"status": "unavailable", "fallback": str(publish_local(args.root, payload))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
