#!/usr/bin/env python3
"""Validate the portable bundle without third-party dependencies."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "skills/product-studio/SKILL.md", "skills/product-studio/agents/openai.yaml",
    "skills/product-studio/references/framework-research.md", "schemas/project.schema.json",
    "schemas/assumption.schema.json", "schemas/decision.schema.json",
    "templates/product-opportunity.md", "templates/evidence-pack.md",
    "templates/design-contract.md", "templates/mvp-build-plan.md", "templates/mvp-review.md",
    "templates/updated-product-definition.md", "templates/production-blueprint.md",
    "templates/github-issue.md",
    "templates/implementation-brief.md",
    "schemas/implementation-brief.schema.json",
    "skills/product-studio/references/final-planning.md",
    "skills/product-studio/references/capabilities/implementation-brief.md",
    "scripts/build_implementation_brief.py",
    "scripts/validate_implementation_brief.py",
]

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    root = parser.parse_args().root.resolve()
    errors = [f"missing: {item}" for item in REQUIRED if not (root / item).is_file()]
    skill = root / "skills/product-studio/SKILL.md"
    text = skill.read_text() if skill.exists() else ""
    if not re.search(r"^---\nname: product-studio\ndescription: .+\n---", text, re.MULTILINE):
        errors.append("SKILL.md must have portable name/description frontmatter")
    if "/product-studio" not in text or "What do you want to build or improve?" not in text:
        errors.append("SKILL.md is missing public entry/intake behavior")
    for path in (root / "schemas").glob("*.json"):
        try:
            json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSON {path}: {exc}")
    if errors:
        print("\n".join(f"ERROR {error}" for error in errors))
        return 1
    print(f"Validated Solo Product Studio bundle at {root}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
