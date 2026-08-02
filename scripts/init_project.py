#!/usr/bin/env python3
"""Create a minimal .product-studio project memory and artifact folders."""
from __future__ import annotations
import argparse
import datetime as dt
import re
import json
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("--directory", type=Path, default=Path.cwd())
    parser.add_argument("--stage", default="idea")
    parser.add_argument("--mode", default="custom")
    args = parser.parse_args()
    root = args.directory / ".product-studio"
    state = root / "project.yaml"
    if state.exists():
        raise SystemExit(f"Refusing to overwrite {state}")
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    project_id = re.sub(r"[^a-z0-9]+", "-", args.name.lower()).strip("-") or "product"
    for folder in ("artifacts", "research", "github"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    state.write_text(f"""project:
  id: {json.dumps(project_id)}
  name: {json.dumps(args.name)}
  stage: {args.stage}
  mode: {args.mode}
  created_at: {now}
  updated_at: {now}

capabilities: {{}}
product: {{}}
business: {{}}
constraints: {{}}
research: {{}}
assumptions: []
decisions: []
design: {{}}
mvp: {{}}
production: {{}}
github: {{}}
""")
    print(f"Created {state}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
