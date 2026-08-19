#!/usr/bin/env python3
"""Create a .product-studio project memory and artifact folders.

The state shape lives in workflow_runner.new_state(). This script used to hand-write
the same structure as YAML text, which meant the deterministic runner and the file it
was supposed to run on could never be the same file. One shape, one format, one writer.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from workflow_profile import MODE_PROFILES  # noqa: E402
from workflow_runner import new_state  # noqa: E402

DONE_BARS = {
    "intake": ["goal defined", "house rules confirmed"],
    "product": ["target user defined", "wedge narrow", "assumptions recorded"],
    "research": ["evidence cited or research plan created", "uncertainty labeled"],
    "design": ["promise, hero moment, flow, scope, three principles defined"],
    "specify": ["behaviors cover every in-scope capability", "every behavior has an observable and a source", "zero open ambiguities", "mirror in sync"],
    "mvp": ["core flow executable", "mocks explicit", "cuts explicit", "demo defined"],
    "review": ["independent findings recorded", "recommendation supported"],
    "production": ["boundaries, migration, risks, release criteria defined"],
    "final_planning": ["context complete", "constraints explicit", "verification stopping conditions defined", "output format defined", "independent review passed"],
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("--directory", type=Path, default=Path.cwd())
    parser.add_argument("--stage", default="idea")
    parser.add_argument("--mode", default="custom", choices=sorted(MODE_PROFILES))
    parser.add_argument("--risk-tier", help="override the mode's default risk tier")
    parser.add_argument("--delivery-target", help="override the mode's default delivery target")
    args = parser.parse_args()
    root = args.directory / ".product-studio"
    state_path = root / "project.json"
    if state_path.exists():
        raise SystemExit(f"Refusing to overwrite {state_path}")
    project_id = re.sub(r"[^a-z0-9]+", "-", args.name.lower()).strip("-") or "product"
    overrides = {key: value for key, value in (("risk_tier", args.risk_tier), ("delivery_target", args.delivery_target)) if value}
    state = new_state(project_id, args.mode, name=args.name, stage=args.stage, profile_overrides=overrides)
    for phase, bar in DONE_BARS.items():
        state["phases"][phase]["done_bar"] = bar
    for folder in ("artifacts", "research", "github"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2) + "\n")
    print(f"Created {state_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
