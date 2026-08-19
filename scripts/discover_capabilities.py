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
            # Local xcodebuild only proves the Apple toolchain exists; the MCP server is
            # separate and must be detected from the host tool list.
            "xcodebuild-mcp": {"status": "host-tool", "toolchain": "xcodebuild" if shutil.which("xcodebuild") else "missing", "fallback": "xcodebuild-cli-then-manual-xcode"},
            "figma": {"status": "optional", "fallback": "design-contract-only"},
        },
    }
    if args.project:
        state_path = args.project.expanduser()
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state = json.loads(state_path.read_text()) if state_path.exists() else {"project": {"id": "product", "stage": "idea", "mode": "custom"}}
        state["capabilities"] = result
        state_path.write_text(json.dumps(state, indent=2) + "\n")
        print(f"Persisted capability registry to {state_path}")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
