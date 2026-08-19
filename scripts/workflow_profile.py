#!/usr/bin/env python3
"""Compile the confirmed intake answers into one executable workflow policy.

The operating mode used to be a free-text label that only prose enforced, so a
four-hour demo and a regulated production migration ran the same specification,
review, PR, and CI machinery. This module is the single source of truth that
replaced it: every gate downstream reads the compiled profile rather than
re-deciding from the mode string.

There is no runtime JSON-schema validator in this bundle (adding one would break
the dependency-free rule), so `compile_profile` being the only writer of these values is
the enforcement. `schemas/workflow-profile.schema.json` documents the same enums
and `tests/test_bundle.py` asserts the two never drift.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

VERSION = "workflow_profile/v1"

RISK_TIERS = ("low", "moderate", "high")
DELIVERY_TARGETS = ("local_demo", "code_only", "pull_request", "preview", "staging", "production")
SPEC_GATES = ("warn", "block")
DESIGN_GATES = ("advisory", "required", "evidence_required")
AUTOMATED_TESTS = ("smoke", "core", "full")
SLICING = ("flow", "vertical")
MERGE_POLICIES = ("never", "ask", "auto_on_approve")
REVIEW_LANES = ("offline", "online", "none")

# A deploy needs somewhere to deploy to. Anything below these targets that claims
# deployment.allowed is a mis-compiled profile, not a permissive one.
DEPLOYABLE_TARGETS = {"staging", "production"}

# Cumulative, never cuttable. An override may add to a safety floor; nothing removes
# from one. Each tier is the previous tier plus what its exposure introduces.
_DEMO_FLOOR = ("secrets-out-of-repo", "input-validation-on-demo-path")
_HACKATHON_FLOOR = _DEMO_FLOOR + ("demo-data-labeled-as-fake",)
_PRODUCT_FLOOR = _DEMO_FLOOR + ("auth-on-user-data", "dependency-audit")
_TENANT_FLOOR = _PRODUCT_FLOOR + ("authz-per-tenant", "pii-encrypted-at-rest")
_PRODUCTION_FLOOR = _TENANT_FLOOR + (
    "security-review", "observability", "rollout-plan", "rollback-plan", "human-approval-gate",
)


def _profile(
    *, risk_tier: str, delivery_target: str, spec_gate: str, max_behaviors: int | None,
    design_gate: str, slicing: str, refactor_phase: bool, pull_request_required: bool,
    automated_required: str, coverage_target: str | None, ci_required: bool,
    independent_required: bool, safety_floor: tuple[str, ...], revisit_when: str,
) -> dict[str, Any]:
    return {
        "risk_tier": risk_tier,
        "delivery_target": delivery_target,
        "planning": {"spec_gate": spec_gate, "max_behaviors": max_behaviors},
        "design": {"gate": design_gate},
        "development": {"slicing": slicing, "refactor_phase": refactor_phase, "pull_request_required": pull_request_required},
        "testing": {"automated_required": automated_required, "manual_required": True, "coverage_target": coverage_target, "ci_required": ci_required},
        "review": {"independent_required": independent_required},
        "deployment": {"allowed": False},
        "safety_floor": list(safety_floor),
        "revisit_when": revisit_when,
    }


MODE_PROFILES: dict[str, dict[str, Any]] = {
    "prototype": _profile(
        risk_tier="low", delivery_target="local_demo", spec_gate="warn", max_behaviors=7,
        design_gate="advisory", slicing="flow", refactor_phase=False, pull_request_required=False,
        automated_required="smoke", coverage_target=None, ci_required=False,
        independent_required=False, safety_floor=_DEMO_FLOOR,
        revisit_when="the validation question is answered",
    ),
    "hackathon": _profile(
        risk_tier="low", delivery_target="local_demo", spec_gate="warn", max_behaviors=9,
        design_gate="advisory", slicing="flow", refactor_phase=False, pull_request_required=False,
        automated_required="smoke", coverage_target=None, ci_required=False,
        independent_required=False, safety_floor=_HACKATHON_FLOOR,
        revisit_when="the event is over",
    ),
    "indie": _profile(
        risk_tier="moderate", delivery_target="pull_request", spec_gate="block", max_behaviors=None,
        design_gate="required", slicing="vertical", refactor_phase=True, pull_request_required=True,
        automated_required="core", coverage_target=None, ci_required=True,
        independent_required=True, safety_floor=_PRODUCT_FLOOR,
        revisit_when="first paying users or support load appears",
    ),
    "saas": _profile(
        risk_tier="moderate", delivery_target="preview", spec_gate="block", max_behaviors=None,
        design_gate="required", slicing="vertical", refactor_phase=True, pull_request_required=True,
        automated_required="core", coverage_target="core paths", ci_required=True,
        independent_required=True, safety_floor=_TENANT_FLOOR,
        revisit_when="first paying tenant or an SLA commitment",
    ),
    "startup": _profile(
        risk_tier="moderate", delivery_target="preview", spec_gate="block", max_behaviors=None,
        design_gate="required", slicing="vertical", refactor_phase=True, pull_request_required=True,
        automated_required="core", coverage_target="core paths", ci_required=True,
        independent_required=True, safety_floor=_TENANT_FLOOR,
        revisit_when="retention or distribution signal changes",
    ),
    "production": _profile(
        risk_tier="high", delivery_target="production", spec_gate="block", max_behaviors=None,
        design_gate="evidence_required", slicing="vertical", refactor_phase=True, pull_request_required=True,
        automated_required="full", coverage_target="critical paths + regression", ci_required=True,
        independent_required=True, safety_floor=_PRODUCTION_FLOOR,
        revisit_when="none — production is terminal",
    ),
    "custom": _profile(
        risk_tier="moderate", delivery_target="code_only", spec_gate="block", max_behaviors=None,
        design_gate="required", slicing="vertical", refactor_phase=True, pull_request_required=True,
        automated_required="core", coverage_target=None, ci_required=True,
        independent_required=True, safety_floor=_PRODUCT_FLOOR,
        revisit_when="user-defined at intake",
    ),
}

MODES = tuple(MODE_PROFILES)


def _merge(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """One level deep: nested dicts merge per key, scalars and lists replace."""
    merged = {key: dict(value) if isinstance(value, dict) else value for key, value in base.items()}
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def compile_profile(mode: str, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Compile one mode, plus any confirmed intake overrides, into a policy.

    Custom mode is not exempt: it compiles to concrete policy like every other
    mode, which is the whole point — a free-text label enforces nothing.
    """
    if mode not in MODE_PROFILES:
        raise ValueError(f"unknown mode: {mode} (expected one of {', '.join(MODES)})")
    profile = _merge(MODE_PROFILES[mode], overrides or {})

    # Merge policy and review lane are user answers rather than mode consequences,
    # so they default here instead of in the mode table: `ask` keeps a human on the
    # merge, and a lane only exists where an independent review does.
    profile["development"] = {"merge_policy": "ask", **profile["development"]}
    profile["review"] = {
        "lane": "offline" if profile["review"]["independent_required"] else "none",
        **profile["review"],
    }

    # Derivations run after the merge so an override can trigger them. This is the
    # risk-triggered design gate: high risk earns the evidence requirement rather
    # than needing a second mechanism to ask for it.
    if profile["risk_tier"] == "high":
        profile["design"] = {**profile["design"], "gate": "evidence_required"}
        profile["safety_floor"] = sorted(set(profile["safety_floor"]) | set(_PRODUCTION_FLOOR))
        # `human-approval-gate` is in the production floor, and an agent merging its
        # own PR is exactly the gate it names. No override reopens this.
        profile["development"] = {**profile["development"], "merge_policy": "never"}

    # The safety floor is a floor. An override adds; it never removes.
    profile["safety_floor"] = sorted(set(profile["safety_floor"]) | set(MODE_PROFILES[mode]["safety_floor"]))

    if profile["deployment"]["allowed"] and profile["delivery_target"] not in DEPLOYABLE_TARGETS:
        raise ValueError(
            f"deployment.allowed requires a delivery_target of {' or '.join(sorted(DEPLOYABLE_TARGETS))}, "
            f"not {profile['delivery_target']}"
        )
    for field, allowed in (("risk_tier", RISK_TIERS), ("delivery_target", DELIVERY_TARGETS)):
        if profile[field] not in allowed:
            raise ValueError(f"invalid {field}: {profile[field]}")
    if profile["planning"]["spec_gate"] not in SPEC_GATES:
        raise ValueError(f"invalid planning.spec_gate: {profile['planning']['spec_gate']}")
    if profile["design"]["gate"] not in DESIGN_GATES:
        raise ValueError(f"invalid design.gate: {profile['design']['gate']}")
    if profile["development"]["merge_policy"] not in MERGE_POLICIES:
        raise ValueError(f"invalid development.merge_policy: {profile['development']['merge_policy']}")
    if profile["review"]["lane"] not in REVIEW_LANES:
        raise ValueError(f"invalid review.lane: {profile['review']['lane']}")
    if profile["review"]["independent_required"] and profile["review"]["lane"] == "none":
        raise ValueError("review.independent_required needs a lane: set review.lane to offline or online")

    # Stamped last so no override can forge either.
    return {"version": VERSION, "mode": mode, **profile}


def load(state: dict[str, Any]) -> dict[str, Any]:
    """The profile a state file is governed by, compiling one for older state."""
    profile = state.get("workflow_profile")
    if not profile:
        return compile_profile(state.get("project", {}).get("mode") or "custom")
    if profile.get("version") != VERSION:
        raise ValueError(f"unsupported workflow profile version: {profile.get('version')}")
    return profile


def main() -> int:
    parser = argparse.ArgumentParser(description="Print the compiled workflow profile.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--mode", choices=sorted(MODE_PROFILES))
    source.add_argument("--state", type=Path, help="a .product-studio/project.json to read")
    args = parser.parse_args()
    profile = compile_profile(args.mode) if args.mode else load(json.loads(args.state.read_text()))
    print(json.dumps(profile, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
