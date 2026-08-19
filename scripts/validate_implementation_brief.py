#!/usr/bin/env python3
"""Validate the required shape and stopping conditions of an Implementation Brief."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import workflow_profile  # noqa: E402

HEADINGS = ("## Context", "## Task", "## Constraints", "## Verification — do not finish until", "## Output Format", "## Handoff")
VALID_STATUSES = {"passed", "unresolved", "blocked", "not_applicable"}
VALID_OWNERS = {"implementation", "reviewer", "user"}
BEHAVIOR_REF = re.compile(r"\bBH-[0-9]{3,}\b")
CRITERIA_LABEL = "- Non-negotiable acceptance criteria:"
# A brief may not plan a step the compiled profile does not permit.
DEPLOY_INTENT = re.compile(r"\b(deploy|deployment|release to production|ship to production|rollout)\b", re.IGNORECASE)


def _acceptance_criteria(text: str) -> list[str]:
    """Return the acceptance-criteria lines: the label line plus its indented continuations."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip().startswith(CRITERIA_LABEL):
            collected = [line] if line.strip() != CRITERIA_LABEL else []
            for continuation in lines[index + 1:]:
                if not continuation.startswith((" ", "\t")) or not continuation.strip():
                    break
                collected.append(continuation)
            return [item for item in collected if item.strip().lstrip("-").strip()]
    return []


def validate(path: Path, prototype: bool = False, *, mode: str | None = None) -> list[str]:
    text = path.read_text()
    profile = workflow_profile.compile_profile(mode or ("prototype" if prototype else "custom"))
    relaxed = profile["planning"]["spec_gate"] == "warn"
    errors = [f"missing section: {heading}" for heading in HEADINGS if heading not in text]
    if not relaxed:
        if "- Behavior spec path:" not in text:
            errors.append("context must name a behavior spec path")
        criteria = _acceptance_criteria(text)
        if not criteria:
            errors.append("acceptance criteria are empty")
        for line in criteria:
            if not BEHAVIOR_REF.search(line):
                errors.append(f"acceptance criterion cites no BH-###: {line.strip()[:60]}")
    marker = "## Verification — do not finish until"
    for section in HEADINGS:
        if section in text:
            body = text.split(section, 1)[1].split("\n## ", 1)[0]
            if not any(line.strip().startswith("-") and line.split(":", 1)[-1].strip() for line in body.splitlines() if ":" in line):
                errors.append(f"section is empty: {section}")
    if marker in text:
        verification = text.split(marker, 1)[1].split("## Output Format", 1)[0]
        if "- [ ]" not in verification:
            if "- [x]" not in verification:
                errors.append("verification must contain at least one stopping condition")
        if "Status:" not in verification:
            errors.append("verification items must expose status")
        for line in verification.splitlines():
            if "Status:" in line:
                status = line.split("Status:", 1)[1].strip().split()[0]
                if status not in VALID_STATUSES:
                    errors.append(f"invalid verification status: {status}")
            if line.lstrip().startswith("- ["):
                if "Evidence:" not in line:
                    errors.append("every verification item must name evidence")
                # Owner decides whether a pending check blocks the handoff or is a
                # future condition, so a check without one cannot be gated at all.
                if "Owner:" not in line:
                    errors.append("every verification item must name an owner")
                elif line.split("Owner:", 1)[1].split("—")[0].strip() not in VALID_OWNERS:
                    errors.append(f"invalid verification owner: {line.split('Owner:', 1)[1].split('—')[0].strip()}")
    if not profile["deployment"]["allowed"]:
        for section in ("## Output Format", "## Handoff"):
            if section in text and DEPLOY_INTENT.search(text.split(section, 1)[1].split("\n## ", 1)[0]):
                errors.append(f"brief plans a deployment in {section.strip('# ')} but the {profile['mode']} profile does not allow one")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("brief", type=Path)
    parser.add_argument("--mode", default="custom", choices=sorted(workflow_profile.MODE_PROFILES), help="operating mode whose compiled profile governs the gate")
    parser.add_argument("--prototype", action="store_const", dest="mode", const="prototype", help="alias for --mode prototype")
    parser.add_argument("--hackathon", action="store_const", dest="mode", const="hackathon", help="alias for --mode hackathon")
    args = parser.parse_args()
    errors = validate(args.brief, mode=args.mode)
    if errors:
        print("\n".join(f"ERROR {error}" for error in errors))
        return 1
    print(f"Validated Implementation Brief: {args.brief}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
