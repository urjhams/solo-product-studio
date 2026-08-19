#!/usr/bin/env python3
"""Dependency-free Product Studio phase and final-planning state machine."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

import workflow_profile

PHASES = ("intake", "product", "research", "design", "specify", "mvp", "review", "production", "final_planning")
VERIFICATION_PASS = {"passed", "not_applicable"}
CHECK_STATUSES = {"passed", "unresolved", "blocked", "not_applicable"}
CHECK_OWNERS = {"implementation", "reviewer", "user"}
# A check owned by the implementing agent or its reviewer is settled *after* handoff,
# by definition. A check only the user can settle is a missing input, not a future
# condition, so it is the one owner that still blocks the handoff.
FUTURE_OWNERS = {"implementation", "reviewer"}
# "Evidence" at plan time names where the evidence will come from. These are the
# ways a brief says "nowhere" while looking filled in.
PLACEHOLDER_EVIDENCE = {"", "-", "tbd", "todo", "to be supplied", "to be determined", "none", "n/a", "unknown"}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def new_state(project_id: str = "product", mode: str = "custom", *, name: str = "", stage: str = "idea", profile_overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    timestamp = now()
    return {
        "project": {"id": project_id, "name": name or project_id, "stage": stage, "mode": mode, "created_at": timestamp, "updated_at": timestamp, "goal": "", "protected_outcome": "", "path": ""},
        # The compiled policy, not the label. Everything downstream reads this.
        "workflow_profile": workflow_profile.compile_profile(mode, profile_overrides),
        "house_rules": {"constraints": [], "non_negotiables": [], "scope_exclusions": [], "evidence_policy": "cite sources; label inference and unknowns", "approval_boundaries": ["external publication", "irreversible decisions"]},
        "session": {"status": "intake", "current_phase": "intake", "current_gate": "goal-and-house-rules", "next_action": "ask-intake-question", "questions": [], "unanswered_questions": [], "iteration_count": 0, "approval_status": "pending", "last_checkpoint": None, "updated_at": timestamp},
        "phases": {phase: {"status": "in_progress" if phase == "intake" else "pending", "done_bar": [], "result": None} for phase in PHASES},
        "reviews": [],
        "specify": {"behavior_spec": "", "mirror": "", "behaviors": 0, "open_ambiguities": 0, "validated": False},
        "final_planning": {"status": "pending", "source_artifacts": [], "implementation_brief": "", "context_sources": [], "constraints": [], "verification": {"do_not_finish_until": [], "evidence": [], "unresolved": []}, "output_format": {}, "reviewer": "", "review_iterations": 0, "approval_status": "pending", "source_fingerprint": ""},
        "capabilities": {}, "product": {}, "business": {}, "constraints": {}, "research": {}, "assumptions": [], "decisions": [], "design": {}, "mvp": {}, "production": {}, "github": {},
    }


def record_answer(state: dict[str, Any], question: str, answer: str, *, decision_id: str | None = None) -> dict[str, Any]:
    session = state["session"]
    session["questions"].append({"question": question, "answer": answer, "decision_id": decision_id, "answered_at": now()})
    session["unanswered_questions"] = [item for item in session["unanswered_questions"] if item != question]
    session["updated_at"] = now()
    state["project"]["updated_at"] = session["updated_at"]
    return state


def begin_phase(state: dict[str, Any], phase: str, done_bar: list[str] | None = None) -> dict[str, Any]:
    if phase not in PHASES:
        raise ValueError(f"Unknown phase: {phase}")
    timestamp = now()
    state["session"].update({"status": "in_progress", "current_phase": phase, "current_gate": f"{phase}-done-bar", "next_action": "run-phase", "approval_status": "pending", "updated_at": timestamp})
    state["phases"][phase]["status"] = "in_progress"
    if done_bar is not None:
        state["phases"][phase]["done_bar"] = done_bar
    if phase == "final_planning":
        state["final_planning"]["status"] = "drafting"
        state["final_planning"]["approval_status"] = "pending"
    state["project"]["updated_at"] = timestamp
    return state


def attach_final_brief(state: dict[str, Any], brief_path: str, source_artifacts: list[str], verification: list[dict[str, Any]], *, source_fingerprint: str = "") -> dict[str, Any]:
    state["final_planning"].update({"status": "reviewing", "implementation_brief": brief_path, "source_artifacts": source_artifacts, "verification": {"do_not_finish_until": verification, "evidence": [], "unresolved": [item["check"] for item in verification if item.get("status") not in VERIFICATION_PASS]}, "source_fingerprint": source_fingerprint})
    state["session"]["current_phase"] = "final_planning"
    state["session"]["current_gate"] = "implementation-brief-verification"
    state["session"]["next_action"] = "obtain-independent-review"
    state["session"]["updated_at"] = now()
    state["project"]["updated_at"] = state["session"]["updated_at"]
    return state


def record_review(state: dict[str, Any], phase: str, reviewer: str, passed: bool, findings: list[str] | None = None) -> dict[str, Any]:
    if phase not in PHASES:
        raise ValueError(f"Unknown phase: {phase}")
    independent = reviewer in {"independent", "fresh_context", "subagent"}
    review = {"phase": phase, "reviewer": reviewer, "independent": independent, "passed": passed, "findings": findings or [], "recorded_at": now()}
    state["reviews"].append(review)
    state["phases"][phase]["status"] = "reviewing"
    state["phases"][phase]["result"] = review
    state["session"]["iteration_count"] += 1
    state["session"]["next_action"] = "repair-highest-impact-gap" if not passed else "checkpoint"
    if phase == "final_planning":
        state["final_planning"]["reviewer"] = reviewer
        state["final_planning"]["review_iterations"] += 1
    state["session"]["updated_at"] = now()
    state["project"]["updated_at"] = state["session"]["updated_at"]
    return state


def attach_behavior_spec(state: dict[str, Any], path: str, mirror: str, behaviors: int, open_ambiguities: int, validated: bool) -> dict[str, Any]:
    state["specify"] = {"behavior_spec": path, "mirror": mirror, "behaviors": behaviors, "open_ambiguities": open_ambiguities, "validated": validated}
    state["session"]["updated_at"] = now()
    state["project"]["updated_at"] = state["session"]["updated_at"]
    return state


def _specify_ready(state: dict[str, Any]) -> tuple[bool, str]:
    spec = state.get("specify", {})
    if not spec.get("behavior_spec"):
        return False, "behavior-spec-missing"
    if not spec.get("behaviors"):
        return False, "no-behaviors-defined"
    if spec.get("open_ambiguities"):
        return False, "ambiguities-open"
    # scripts/validate_behavior_spec.py is the single authority on field, source, and mirror rules
    if not spec.get("validated"):
        return False, "behavior-spec-not-validated"
    return True, "ready"


def _is_placeholder(value: Any) -> bool:
    return str(value or "").strip().strip(".").lower() in PLACEHOLDER_EVIDENCE


def _plan_ready(state: dict[str, Any]) -> tuple[bool, str]:
    """May this brief be handed to an implementing agent?

    The checks in `do not finish until` are the implementing agent's *stopping
    conditions* — future conditions by construction. Requiring them satisfied
    before handoff would mean the only brief that can hand off is one describing
    work already finished. So plan readiness asks whether each check is
    well-formed: does it say what to check, who owns it, and where the evidence
    will come from. Whether it passed is `_implementation_done`'s question.
    """
    final = state["final_planning"]
    if not final["implementation_brief"]:
        return False, "implementation-brief-missing"
    checks = final["verification"]["do_not_finish_until"]
    if not checks:
        return False, "verification-stopping-conditions-missing"
    for item in checks:
        if not str(item.get("check") or "").strip():
            return False, "verification-check-description-missing"
        if item.get("owner") not in CHECK_OWNERS:
            return False, "verification-owner-missing"
        if item.get("status") not in CHECK_STATUSES:
            return False, "verification-status-invalid"
        if _is_placeholder(item.get("evidence")):
            return False, "verification-evidence-source-missing"
        # A decision only the user can make is a missing input, not a future condition.
        if item["owner"] not in FUTURE_OWNERS and item["status"] not in VERIFICATION_PASS:
            return False, "user-decisions-unresolved"
    return True, "ready"


def _implementation_done(state: dict[str, Any]) -> tuple[bool, str]:
    """May the brief be marked complete? Every check, whoever owns it, has landed."""
    ready, reason = _plan_ready(state)
    if not ready:
        return False, reason
    checks = state["final_planning"]["verification"]["do_not_finish_until"]
    if any(item.get("status") not in VERIFICATION_PASS for item in checks):
        return False, "verification-checks-unresolved"
    return True, "ready"


def _block(state: dict[str, Any], phase: str, reason: str, *, final_planning: bool = False) -> dict[str, Any]:
    state["phases"][phase]["status"] = "blocked"
    if final_planning:
        state["final_planning"]["status"] = "blocked"
        state["final_planning"]["approval_status"] = "blocked"
    state["session"]["next_action"] = reason
    state["session"]["approval_status"] = "blocked"
    state["session"]["updated_at"] = now()
    return state


def checkpoint(state: dict[str, Any], phase: str) -> dict[str, Any]:
    if phase not in PHASES:
        raise ValueError(f"Unknown phase: {phase}")
    phase_reviews = [review for review in state["reviews"] if review["phase"] == phase]
    independent_pass = any(review["independent"] and review["passed"] for review in phase_reviews)
    any_pass = any(review["passed"] for review in phase_reviews)
    profile = workflow_profile.load(state)
    spec_blocks = profile["planning"]["spec_gate"] == "block"
    if phase == "design" and profile["design"]["gate"] == "evidence_required" and not state["design"].get("evidence"):
        return _block(state, phase, "design-evidence-missing")
    if phase == "specify":
        ready, reason = _specify_ready(state)
        # A fast mode's spec is deliberately unclosed; blocking on it would spend the
        # timebox on the artifact instead of the thing the artifact is for.
        if not ready and spec_blocks:
            return _block(state, phase, reason)
        if not ready:
            state["phases"][phase]["result"] = f"{profile['mode']}-warning: {reason}"
    if phase == "final_planning":
        ready, reason = _plan_ready(state)
        if not ready:
            return _block(state, phase, reason, final_planning=True)
        specify_ready, specify_reason = _specify_ready(state)
        if not specify_ready and spec_blocks:
            return _block(state, phase, specify_reason, final_planning=True)
    # Where the profile does not require an independent reviewer, a passing self
    # review clears the checkpoint rather than parking it at self_review_only.
    if not profile["review"]["independent_required"] and any_pass:
        independent_pass = True
    if not independent_pass:
        state["phases"][phase]["status"] = "blocked" if any_pass else "reviewing"
        state["session"]["approval_status"] = "self_review_only" if any_pass else "pending"
        state["session"]["next_action"] = "obtain-independent-review"
        if phase == "final_planning":
            state["final_planning"]["approval_status"] = "self_review_only" if any_pass else "pending"
        state["session"]["updated_at"] = now()
        return state
    timestamp = now()
    state["phases"][phase]["status"] = "checkpointed"
    state["session"]["status"] = "checkpointed"
    state["session"]["approval_status"] = "approved"
    state["session"]["last_checkpoint"] = {"phase": phase, "at": timestamp}
    if phase == "final_planning":
        state["final_planning"]["status"] = "approved"
        state["final_planning"]["approval_status"] = "approved"
        state["session"]["next_action"] = "offer-completion-actions"
    else:
        index = PHASES.index(phase)
        state["session"]["next_action"] = f"begin-{PHASES[index + 1]}" if index + 1 < len(PHASES) else "offer-completion-actions"
        if index + 1 < len(PHASES):
            state["session"]["current_gate"] = f"{PHASES[index + 1]}-done-bar"
    state["session"]["updated_at"] = timestamp
    state["project"]["updated_at"] = timestamp
    return state


def can_handoff(state: dict[str, Any]) -> bool:
    """The brief may go to an implementing agent. Its checks may still be pending."""
    return state["final_planning"].get("approval_status") == "approved" and state["final_planning"].get("implementation_brief") != ""


def mark_implementation_done(state: dict[str, Any], *, evidence: list[str] | None = None) -> dict[str, Any]:
    """Close the brief. This is the gate `can_handoff` deliberately does not enforce."""
    if not can_handoff(state):
        state["session"]["next_action"] = "implementation-brief-not-approved"
        state["session"]["updated_at"] = now()
        return state
    done, reason = _implementation_done(state)
    if not done:
        state["session"]["next_action"] = reason
        state["session"]["approval_status"] = "blocked"
        state["session"]["updated_at"] = now()
        return state
    final = state["final_planning"]
    final["status"] = "done"
    final["verification"]["evidence"] = evidence or [item["evidence"] for item in final["verification"]["do_not_finish_until"]]
    final["verification"]["unresolved"] = []
    state["session"]["next_action"] = "offer-completion-actions"
    state["session"]["updated_at"] = now()
    state["project"]["updated_at"] = state["session"]["updated_at"]
    return state


def can_finish(state: dict[str, Any]) -> bool:
    return state["final_planning"].get("status") == "done"


def deploy(state: dict[str, Any], target: str, *, environment: str = "", approver: str = "", rollback: str = "", observability: str = "", thresholds: str = "") -> dict[str, Any]:
    """Production deployment is an explicit transition, never a consequence of merging."""
    profile = workflow_profile.load(state)
    if not profile["deployment"]["allowed"]:
        state["session"]["next_action"] = "deployment-not-enabled-in-profile"
        state["session"]["updated_at"] = now()
        return state
    missing = [name for name, value in (("environment", environment), ("approver", approver), ("rollback", rollback), ("observability", observability), ("thresholds", thresholds)) if not str(value).strip()]
    if missing:
        state["session"]["next_action"] = f"deployment-preconditions-missing: {', '.join(missing)}"
        state["session"]["updated_at"] = now()
        return state
    state["production"]["deployment"] = {"target": target, "environment": environment, "approver": approver, "rollback": rollback, "observability": observability, "thresholds": thresholds, "deployed_at": now()}
    state["session"]["next_action"] = "verify-in-production"
    state["session"]["updated_at"] = now()
    state["project"]["updated_at"] = state["session"]["updated_at"]
    return state


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def save(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("command", choices=("init", "begin", "answer", "attach-brief", "attach-spec", "review", "checkpoint", "done", "profile"))
    parser.add_argument("value", nargs="?")
    parser.add_argument("--answer")
    parser.add_argument("--reviewer", default="self")
    parser.add_argument("--passed", action="store_true")
    parser.add_argument("--mirror", default="docs/agent/BEHAVIORS.md")
    parser.add_argument("--behaviors", type=int, default=0)
    parser.add_argument("--open-ambiguities", type=int, default=0)
    parser.add_argument("--validated", action="store_true")
    parser.add_argument("--mode", default="custom", choices=sorted(workflow_profile.MODE_PROFILES))
    args = parser.parse_args()
    state = new_state(args.value or "product", args.mode) if args.command == "init" else load(args.state)
    if args.command == "begin":
        begin_phase(state, args.value or "intake")
    elif args.command == "answer":
        record_answer(state, args.value or "question", args.answer or "")
    elif args.command == "attach-brief":
        attach_final_brief(state, args.value or "08-implementation-brief.md", [], [])
    elif args.command == "attach-spec":
        attach_behavior_spec(state, args.value or "behavior-spec.md", args.mirror, args.behaviors, args.open_ambiguities, args.validated)
    elif args.command == "review":
        record_review(state, args.value or state["session"]["current_phase"], args.reviewer, args.passed)
    elif args.command == "checkpoint":
        checkpoint(state, args.value or state["session"]["current_phase"])
    elif args.command == "done":
        mark_implementation_done(state)
    elif args.command == "profile":
        print(json.dumps(workflow_profile.load(state), indent=2))
        return 0
    save(args.state, state)
    print(json.dumps(state, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
