#!/usr/bin/env python3
"""Report deterministic local capabilities for project state."""
from __future__ import annotations
import json
import shutil

def main() -> int:
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
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
