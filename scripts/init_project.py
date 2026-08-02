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
  goal: ""
  protected_outcome: ""
  path: ""

house_rules:
  constraints: []
  non_negotiables: []
  scope_exclusions: []
  evidence_policy: "cite sources; label inference and unknowns"
  approval_boundaries: ["external publication", "irreversible decisions"]

session:
  status: intake
  current_phase: intake
  current_gate: goal-and-house-rules
  next_action: ask-intake-question
  questions: []
  unanswered_questions: []
  iteration_count: 0
  approval_status: pending
  updated_at: {now}
  last_checkpoint: null

phases:
  intake: {{status: in_progress, done_bar: [goal defined, house rules confirmed]}}
  product: {{status: pending, done_bar: [target user defined, wedge narrow, assumptions recorded]}}
  research: {{status: pending, done_bar: [evidence cited or research plan created, uncertainty labeled]}}
  design: {{status: pending, done_bar: [promise, hero moment, flow, scope, three principles defined]}}
  mvp: {{status: pending, done_bar: [core flow executable, mocks explicit, cuts explicit, demo defined]}}
  review: {{status: pending, done_bar: [independent findings recorded, recommendation supported]}}
  production: {{status: pending, done_bar: [boundaries, migration, risks, release criteria defined]}}
  final_planning: {{status: pending, done_bar: [context complete, constraints explicit, verification stopping conditions defined, output format defined, independent review passed]}}

reviews: []

final_planning:
  status: pending
  source_artifacts: []
  implementation_brief: ""
  context_sources: []
  constraints: []
  verification:
    do_not_finish_until: []
    evidence: []
    unresolved: []
  output_format: {{}}
  reviewer: ""
  review_iterations: 0
  approval_status: pending

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
