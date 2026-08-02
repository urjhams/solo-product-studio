#!/usr/bin/env python3
"""Build an Implementation Brief Markdown artifact from structured JSON."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def bullets(values: Any) -> str:
    if isinstance(values, dict):
        values = [f"{key}: {value}" for key, value in values.items()]
    if not values:
        return "- None recorded"
    return "\n".join(f"- {value}" for value in values)


def build(data: dict[str, Any]) -> str:
    context = data["context"]
    task = data["task"]
    constraints = data["constraints"]
    verification = data["verification"]
    output = data["output_format"]
    handoff = data["handoff"]
    checks = verification["do_not_finish_until"]
    check_lines = []
    for check in checks:
        if isinstance(check, str):
            check = {"check": check, "evidence": "To be supplied", "owner": "implementation", "status": "unresolved"}
        check_lines.append(f"- [ ] {check['check']} — Evidence: {check['evidence']} — Owner: {check.get('owner', 'implementation')} — Status: {check['status']}")
    return f"""# Implementation Brief

## Context
- Product goal: {context['goal']}
- Protected outcome: {context.get('protected_outcome', 'Not recorded')}
- Target user and audience: {context['audience']}
- Current stage: {context['stage']}
- Operating mode and path: {context.get('mode_path', 'Not recorded')}
- Repository and relevant directories: {context.get('repository', 'Not recorded')}
- Approved source artifacts: {', '.join(context['source_artifacts'])}
- Context sources: {', '.join(context['context_sources'])}
- Prior decisions and known risks: {context.get('prior_decisions_and_risks', 'Not recorded')}

## Task
- Exact implementation objective: {task['objective']}
- User-visible outcome: {task['user_outcome']}
- In-scope behavior: {bullets(task['in_scope'])}
- First vertical slice: {task['first_vertical_slice']}
- Required handoff from the approved plan: {task.get('approved_handoff', 'Not recorded')}

## Constraints
- House rules: {bullets(constraints['house_rules'])}
- Platform and technical constraints: {bullets(constraints.get('technical', []))}
- Timebox and budget: {constraints.get('timebox_budget', 'Not recorded')}
- Scope exclusions: {bullets(constraints['scope_exclusions'])}
- Security and privacy requirements: {bullets(constraints.get('security_privacy', []))}
- Required conventions: {bullets(constraints.get('conventions', []))}
- Mock/real integration boundaries: {bullets(constraints.get('integration_boundaries', []))}
- Approval boundaries: {bullets(constraints.get('approval_boundaries', []))}
- Non-negotiable acceptance criteria: {bullets(constraints['acceptance_criteria'])}

## Verification — do not finish until
{chr(10).join(check_lines)}

### Unverified items
{bullets(verification.get('unresolved', []))}

## Output Format
- Files to create or modify: {bullets(output['files'])}
- Expected artifact or code shape: {output.get('shape', 'Not recorded')}
- Required issue or milestone format: {output.get('issue_format', 'Not applicable')}
- Required summary format: {output.get('summary', 'Concise completion summary')}
- Evidence to return with completion: {bullets(output['completion_evidence'])}

## Handoff
- First implementation action: {handoff['first_action']}
- Dependencies: {bullets(handoff['dependencies'])}
- Next checkpoint: {handoff['next_checkpoint']}
- Rollback or recovery path: {handoff.get('recovery', 'Not recorded')}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.input.read_text())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build(data))
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
