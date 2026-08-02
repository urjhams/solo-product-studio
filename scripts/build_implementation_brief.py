#!/usr/bin/env python3
"""Build an Implementation Brief Markdown artifact from structured JSON."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

VALID_STATUSES = {"passed", "unresolved", "blocked", "not_applicable"}


def validate_input(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {"context", "task", "constraints", "verification", "output_format", "handoff"}
    errors.extend(f"missing top-level field: {field}" for field in sorted(required - data.keys()))
    if errors:
        return errors
    context = data["context"]
    for field in ("goal", "audience", "stage", "source_artifacts", "context_sources", "repository", "existing_tests", "design_references", "documentation", "previous_versions", "prior_review_findings"):
        if not context.get(field):
            errors.append(f"context.{field} must be non-empty; use 'unavailable' when applicable")
    for field in ("objective", "user_outcome", "in_scope", "first_vertical_slice"):
        if not data["task"].get(field):
            errors.append(f"task.{field} must be non-empty")
    for field in ("house_rules", "scope_exclusions", "acceptance_criteria"):
        if not data["constraints"].get(field):
            errors.append(f"constraints.{field} must be present; use [] when none apply")
    checks = data["verification"].get("do_not_finish_until", [])
    if not checks:
        errors.append("verification.do_not_finish_until must contain at least one check")
    for index, check in enumerate(checks):
        if isinstance(check, str):
            continue
        for field in ("check", "evidence", "status", "owner"):
            if not check.get(field):
                errors.append(f"verification.do_not_finish_until[{index}].{field} must be non-empty")
        if check.get("status") not in VALID_STATUSES:
            errors.append(f"verification.do_not_finish_until[{index}].status is invalid")
    for field in ("files", "completion_evidence"):
        if not data["output_format"].get(field):
            errors.append(f"output_format.{field} must be non-empty")
    for field in ("first_action", "dependencies", "next_checkpoint"):
        if not data["handoff"].get(field):
            errors.append(f"handoff.{field} must be non-empty")
    return errors


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
        marker = "x" if check["status"] in {"passed", "not_applicable"} else " "
        check_lines.append(f"- [{marker}] {check['check']} — Evidence: {check['evidence']} — Owner: {check.get('owner', 'implementation')} — Status: {check['status']}")
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
- Existing tests: {context['existing_tests']}
- Design references: {context['design_references']}
- Documentation: {context['documentation']}
- Previous versions: {context['previous_versions']}
- Prior review findings: {context['prior_review_findings']}
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
    errors = validate_input(data)
    if errors:
        raise SystemExit("\n".join(f"ERROR {error}" for error in errors))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build(data))
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
