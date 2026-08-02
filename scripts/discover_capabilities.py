#!/usr/bin/env python3
"""Report deterministic local capabilities for project state."""
from __future__ import annotations
import json
import shutil
import argparse
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, help="Persist the registry into a project state file")
    args = parser.parse_args()
    result = {
        "bundled": {name: "available" for name in [
            "product-lens", "evidence-scout", "product-to-pixels", "mvp-forge",
            "mvp-auditor", "product-synthesizer", "production-blueprint", "github-delivery"]},
        "integrations": {
            "web-research": {"status": "host-tool", "fallback": "research-plan-only"},
            "github": {"status": "gh-cli" if shutil.which("gh") else "local-only", "fallback": "local-export"},
            "mobbin": {"status": "optional", "fallback": "bundled-pattern-library"},
            "figma": {"status": "optional", "fallback": "design-contract-only"},
        },
    }
    if args.project:
        state = args.project.expanduser()
        state.parent.mkdir(parents=True, exist_ok=True)
        existing = state.read_text() if state.exists() else "project:\n  id: product\n  stage: idea\n  mode: custom\n\n"
        # Keep the helper dependency-free: append a canonical JSON block that
        # YAML readers can consume as a mapping while preserving user state.
        marker = "\ncapability_registry_json:"
        before = existing.split(marker, 1)[0].rstrip()
        state.write_text(before + marker + " |\n" + "\n".join("  " + line for line in json.dumps(result, indent=2).splitlines()) + "\n")
        print(f"Persisted capability registry to {state}")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
