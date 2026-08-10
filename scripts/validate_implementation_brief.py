#!/usr/bin/env python3
"""Validate the required shape and stopping conditions of an Implementation Brief."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

HEADINGS = ("## Context", "## Task", "## Constraints", "## Verification — do not finish until", "## Output Format", "## Handoff")
VALID_STATUSES = {"passed", "unresolved", "blocked", "not_applicable"}
BEHAVIOR_REF = re.compile(r"\bBH-[0-9]{3,}\b")
CRITERIA_LABEL = "- Non-negotiable acceptance criteria:"


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


def validate(path: Path, prototype: bool = False) -> list[str]:
    text = path.read_text()
    errors = [f"missing section: {heading}" for heading in HEADINGS if heading not in text]
    if not prototype:
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
            if line.lstrip().startswith("- [") and "Evidence:" not in line:
                errors.append("every verification item must name evidence")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("brief", type=Path)
    parser.add_argument("--prototype", action="store_true", help="Prototype mode: behavior citations are not required")
    args = parser.parse_args()
    errors = validate(args.brief, args.prototype)
    if errors:
        print("\n".join(f"ERROR {error}" for error in errors))
        return 1
    print(f"Validated Implementation Brief: {args.brief}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
