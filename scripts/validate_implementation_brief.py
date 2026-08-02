#!/usr/bin/env python3
"""Validate the required shape and stopping conditions of an Implementation Brief."""
from __future__ import annotations

import argparse
from pathlib import Path

HEADINGS = ("## Context", "## Task", "## Constraints", "## Verification — do not finish until", "## Output Format", "## Handoff")
VALID_STATUSES = {"passed", "unresolved", "blocked", "not_applicable"}


def validate(path: Path) -> list[str]:
    text = path.read_text()
    errors = [f"missing section: {heading}" for heading in HEADINGS if heading not in text]
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
    args = parser.parse_args()
    errors = validate(args.brief)
    if errors:
        print("\n".join(f"ERROR {error}" for error in errors))
        return 1
    print(f"Validated Implementation Brief: {args.brief}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
