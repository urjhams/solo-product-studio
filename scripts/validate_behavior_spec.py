#!/usr/bin/env python3
"""Validate a Behavior Spec: field completeness, ambiguity resolution, and mirror parity."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

MARKER = "<!-- behavior-spec/v1 -->"
BEHAVIOR_FIELDS = ("Status", "Priority", "Level", "Given", "When", "Then", "Observable", "Source")
AMBIGUITY_FIELDS = ("Class", "Reading A", "Reading B", "User-visible difference", "Decision needed", "Status")
BEHAVIOR_STATUSES = {"active", "planned", "deferred", "out_of_scope", "retired"}
PRIORITIES = {"core", "edge", "error"}
LEVELS = {"unit", "integration", "e2e", "manual"}
AMBIGUITY_CLASSES = {
    "term", "boundary", "actor", "state", "timing",
    "failure", "identity", "quantity", "visibility", "reversibility",
}
BEHAVIOR_HEADING = re.compile(r"^## (BH-[0-9]{3,}) — (.+)$")
AMBIGUITY_HEADING = re.compile(r"^### (AM-[0-9]{3,}) — (.+)$")
SOURCE_REF = re.compile(r"\b(?:AM|D)-[0-9]{3,}\b")


def _blocks(text: str, heading: re.Pattern[str]) -> list[tuple[str, str, list[str]]]:
    """Split the document into (id, name, body lines) for every heading that matches."""
    found: list[tuple[str, str, list[str]]] = []
    current: tuple[str, str, list[str]] | None = None
    for line in text.splitlines():
        match = heading.match(line)
        if match:
            current = (match.group(1), match.group(2).strip(), [])
            found.append(current)
        elif line.startswith("#"):
            current = None  # any other heading ends the block
        elif current is not None:
            current[2].append(line)
    return found


def _field(body: list[str], name: str) -> str | None:
    prefix = f"- {name}:"
    for index, line in enumerate(body):
        if line.strip().startswith(prefix):
            value = line.strip()[len(prefix):].strip()
            # a field may wrap onto indented continuation lines
            for continuation in body[index + 1:]:
                if continuation.startswith(("- ", "#")) or not continuation.strip():
                    break
                value += " " + continuation.strip()
            return value
    return None


def _check_behavior(bid: str, name: str, body: list[str]) -> list[str]:
    errors = [f"{bid}: missing field {field}" for field in BEHAVIOR_FIELDS if not _field(body, field)]
    if not name:
        errors.append(f"{bid}: heading has no behavior name")
    status = _field(body, "Status")
    if status and status not in BEHAVIOR_STATUSES:
        errors.append(f"{bid}: invalid Status {status}")
    priority = _field(body, "Priority")
    if priority and priority not in PRIORITIES:
        errors.append(f"{bid}: invalid Priority {priority}")
    level = _field(body, "Level")
    if level and level not in LEVELS:
        errors.append(f"{bid}: invalid Level {level}")
    source = _field(body, "Source")
    if source and not SOURCE_REF.search(source):
        errors.append(f"{bid}: Source must cite at least one AM-### or D-###")
    return errors


def _check_ambiguity(aid: str, name: str, body: list[str]) -> list[str]:
    errors = [f"{aid}: missing field {field}" for field in AMBIGUITY_FIELDS if not _field(body, field)]
    if not name:
        errors.append(f"{aid}: heading has no question")
    klass = _field(body, "Class")
    if klass and klass not in AMBIGUITY_CLASSES:
        errors.append(f"{aid}: invalid Class {klass}")
    status = (_field(body, "Status") or "").strip()
    if status == "open":
        errors.append(f"{aid}: ambiguity is still open — resolve, defer, or rule it out of scope")
    elif status.startswith("resolved"):
        if not re.search(r"\bD-[0-9]{3,}\b", status):
            errors.append(f"{aid}: resolved ambiguity must cite a D-###")
    elif status.startswith("deferred"):
        if not re.search(r"\bA-[0-9]{3,}\b", status):
            errors.append(f"{aid}: deferred ambiguity must cite an A-###")
        if not _field(body, "Revisit when"):
            errors.append(f"{aid}: deferred ambiguity must name a revisit trigger")
    elif status and status != "out_of_scope":
        errors.append(f"{aid}: invalid Status {status}")
    return errors


def validate(path: Path, mirror: Path | None = None, prototype: bool = False) -> list[str]:
    text = path.read_text()
    errors: list[str] = []
    if MARKER not in text:
        return [f"missing format marker {MARKER}"]

    behaviors = _blocks(text, BEHAVIOR_HEADING)
    ambiguities = _blocks(text, AMBIGUITY_HEADING)
    if not behaviors:
        errors.append("no behaviors defined")

    seen: set[str] = set()
    for bid, name, body in behaviors:
        if bid in seen:
            errors.append(f"{bid}: duplicate behavior id")
        seen.add(bid)
        errors.extend(_check_behavior(bid, name, body))

    seen.clear()
    for aid, name, body in ambiguities:
        if aid in seen:
            errors.append(f"{aid}: duplicate ambiguity id")
        seen.add(aid)
        errors.extend(_check_ambiguity(aid, name, body))

    if prototype:
        # ponytail: prototype validation is throwaway, open ambiguities warn instead of blocking
        errors = [error for error in errors if "still open" not in error and "revisit trigger" not in error]

    if mirror is not None:
        if not mirror.is_file():
            errors.append(f"mirror missing: {mirror}")
        elif mirror.read_bytes() != path.read_bytes():
            errors.append(f"mirror out of sync with canonical spec: {mirror}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    parser.add_argument("--mirror", type=Path, default=None, help="repository copy that must match byte for byte")
    parser.add_argument("--prototype", action="store_true", help="Prototype mode: open ambiguities warn instead of blocking")
    args = parser.parse_args()
    errors = validate(args.spec, args.mirror, args.prototype)
    if errors:
        print("\n".join(f"ERROR {error}" for error in errors))
        return 1
    print(f"Validated Behavior Spec: {args.spec}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
