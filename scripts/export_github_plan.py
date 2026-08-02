#!/usr/bin/env python3
"""Create a local GitHub delivery export from a JSON issue list."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("issues", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    issues = json.loads(args.issues.read_text())
    if not isinstance(issues, list):
        raise SystemExit("issues JSON must be an array")
    args.output.mkdir(parents=True, exist_ok=True)
    # JSON is valid YAML 1.2 and safely preserves arbitrary issue metadata
    # without requiring PyYAML or hand-escaping scalar values.
    markdown = ["# GitHub Delivery Plan", "", "Publish status: local-only", ""]
    for index, issue in enumerate(issues, 1):
        issue.setdefault("id", f"GH-{index:03d}")
        title = str(issue.get("title", f"Issue {index}"))
        body = str(issue.get("body", ""))
        markdown += [f"## {index}. {title}", ""]
        for key, value in issue.items():
            if key != "body":
                markdown.append(f"- **{key}**: {value}")
        markdown += ["", body, ""]
    (args.output / "issue-plan.yaml").write_text(json.dumps({"publish_status": "local_only", "issues": issues}, indent=2) + "\n")
    (args.output / "issue-plan.md").write_text("\n".join(markdown))
    print(f"Exported {len(issues)} issues to {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
