#!/usr/bin/env python3
"""Validate the required shape and stopping conditions of an Implementation Brief."""
from __future__ import annotations

import argparse
from pathlib import Path

HEADINGS = ("## Context", "## Task", "## Constraints", "## Verification — do not finish until", "## Output Format", "## Handoff")


def validate(path: Path) -> list[str]:
    text = path.read_text()
    errors = [f"missing section: {heading}" for heading in HEADINGS if heading not in text]
    marker = "## Verification — do not finish until"
    if marker in text:
        verification = text.split(marker, 1)[1].split("## Output Format", 1)[0]
        if "- [ ]" not in verification:
            errors.append("verification must contain at least one stopping condition")
        if "Status:" not in verification:
            errors.append("verification items must expose status")
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
