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
    "skills/product-studio/references/platform-decision.md",
    "skills/product-studio/references/market-probe.md",
    "skills/product-studio/references/prototype-mode.md",
    "skills/product-studio/references/idea-validation.md",
    "skills/product-studio/references/capabilities/idea-validator.md",
    "skills/product-studio/references/capabilities/implementation-brief.md",
    "scripts/build_implementation_brief.py",
    "scripts/validate_implementation_brief.py",
    "skills/product-recheck/SKILL.md",
    "skills/product-studio/references/spec-hardening.md",
    "skills/product-studio/references/behavior-discovery.md",
    "skills/product-studio/references/capabilities/spec-cartographer.md",
    "skills/product-studio/references/capabilities/reality-check.md",
    "templates/behavior-spec.md",
    "templates/reevaluation-verdict.md",
    "schemas/behavior-spec.schema.json",
    "scripts/validate_behavior_spec.py",
    "docs/examples/spec-hardening.md",
    "skills/workflow-init/SKILL.md",
    "skills/workflow-init/scripts/init.sh",
    "skills/workflow-init/templates/core/docs/agent/CARD.md",
    "skills/workflow-init/templates/core/docs/agent/BEHAVIORS.md",
    "skills/workflow-init/templates/agents/task-evaluator.md",
    "skills/engineering-cycle/SKILL.md",
]

# The engineering references are vendored from external skill packs so that a
# scaffolded repository stays self-contained. Every one is reachable from
# engineering-cycle's gate table; a missing file there is a dangling pointer of
# exactly the kind this bundle exists to avoid.
ENGINEERING_REFERENCES = (
    "planning", "build-loop", "api", "sources", "doubt", "review", "security",
    "performance", "browser-verification", "observability", "adr", "release",
    "ci", "ship", "migration",
)
ENGINEERING_CHECKLISTS = (
    "definition-of-done", "security-checklist", "performance-checklist",
    "accessibility-checklist", "observability-checklist", "testing-patterns",
    "orchestration-patterns",
)
REQUIRED += [
    f"skills/engineering-cycle/references/{name}.md" for name in ENGINEERING_REFERENCES
] + [
    f"skills/engineering-cycle/references/checklists/{name}.md" for name in ENGINEERING_CHECKLISTS
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
    recheck = root / "skills/product-recheck/SKILL.md"
    recheck_text = recheck.read_text() if recheck.exists() else ""
    if not re.search(r"^---\nname: product-recheck\ndescription: .+\n---", recheck_text, re.MULTILINE):
        errors.append("product-recheck SKILL.md must have portable name/description frontmatter")
    if "/product-recheck" not in recheck_text:
        errors.append("product-recheck SKILL.md is missing its public entry")
    for name in ("workflow-init", "engineering-cycle"):
        path = root / "skills" / name / "SKILL.md"
        skill_text = path.read_text() if path.is_file() else ""
        if not re.search(rf"^---\nname: {name}\ndescription: .+\n---", skill_text, re.MULTILINE):
            errors.append(f"{name} SKILL.md must have portable name/description frontmatter")
    # the behavior-spec format marker is a shared contract with the workflow-init skill
    marker = "<!-- behavior-spec/v1 -->"
    for name in ("templates/behavior-spec.md", "docs/examples/spec-hardening.md",
                 "skills/workflow-init/templates/core/docs/agent/BEHAVIORS.md"):
        path = root / name
        if path.is_file() and marker not in path.read_text():
            errors.append(f"{name} is missing the {marker} format marker")
    # The upstream skill packs these references came from linked to a sibling
    # ../../references/ directory that their installer never fetched, so every
    # such link was dead on arrival. Vendoring only helps if none survive.
    engineering = root / "skills/engineering-cycle"
    for path in sorted(engineering.rglob("*.md")) if engineering.is_dir() else []:
        if "../../references/" in path.read_text():
            errors.append(f"{path.relative_to(root)} has an unresolved upstream ../../references/ link")
    # Every reference engineering-cycle routes to must exist, or the gate table lies.
    entry = engineering / "SKILL.md"
    if entry.is_file():
        for target in sorted(set(re.findall(r"`(references/[\w/.-]+\.md)`", entry.read_text()))):
            if not (engineering / target).is_file():
                errors.append(f"engineering-cycle SKILL.md routes to missing {target}")
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
