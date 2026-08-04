#!/usr/bin/env python3
"""Dependency-free Product Studio phase and final-planning state machine."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

PHASES = ("intake", "product", "research", "design", "mvp", "review", "production", "final_planning")
VALID_STATUSES = ("pending", "in_progress", "reviewing", "checkpointed", "approved", "blocked", "skipped")
VERIFICATION_PASS = {"passed", "not_applicable"}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def new_state(project_id: str = "product", mode: str = "custom") -> dict[str, Any]:
    timestamp = now()
    return {
        "project": {"id": project_id, "stage": "idea", "mode": mode, "created_at": timestamp, "updated_at": timestamp, "goal": "", "protected_outcome": "", "path": ""},
        "house_rules": {"constraints": [], "non_negotiables": [], "scope_exclusions": [], "evidence_policy": "cite sources; label inference and unknowns", "approval_boundaries": ["external publication", "irreversible decisions"]},
        "session": {"status": "intake", "current_phase": "intake", "current_gate": "goal-and-house-rules", "next_action": "ask-intake-question", "questions": [], "unanswered_questions": [], "iteration_count": 0, "approval_status": "pending", "last_checkpoint": None, "updated_at": timestamp},
        "phases": {phase: {"status": "in_progress" if phase == "intake" else "pending", "done_bar": [], "result": None} for phase in PHASES},
        "reviews": [],
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


def _final_planning_ready(state: dict[str, Any]) -> tuple[bool, str]:
    final = state["final_planning"]
    if not final["implementation_brief"]:
        return False, "implementation-brief-missing"
    checks = final["verification"]["do_not_finish_until"]
    if not checks:
        return False, "verification-stopping-conditions-missing"
    if any(item.get("status") not in VERIFICATION_PASS for item in checks):
        return False, "verification-checks-unresolved"
    if any(item.get("evidence") in (None, "", "To be supplied") for item in checks):
        return False, "verification-evidence-missing"
    return True, "ready"


def checkpoint(state: dict[str, Any], phase: str) -> dict[str, Any]:
    if phase not in PHASES:
        raise ValueError(f"Unknown phase: {phase}")
    phase_reviews = [review for review in state["reviews"] if review["phase"] == phase]
    independent_pass = any(review["independent"] and review["passed"] for review in phase_reviews)
    any_pass = any(review["passed"] for review in phase_reviews)
    if phase == "final_planning":
        ready, reason = _final_planning_ready(state)
        if not ready:
            state["final_planning"]["status"] = "blocked"
            state["final_planning"]["approval_status"] = "blocked"
            state["session"]["next_action"] = reason
            state["session"]["approval_status"] = "blocked"
            state["session"]["updated_at"] = now()
            return state
    # ponytail: prototype mode is throwaway validation, a passing self review clears its checkpoints
    if state["project"].get("mode") == "prototype" and any_pass:
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
    return state["final_planning"].get("approval_status") == "approved" and state["final_planning"].get("implementation_brief") != ""


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def save(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("command", choices=("init", "begin", "answer", "attach-brief", "review", "checkpoint"))
    parser.add_argument("value", nargs="?")
    parser.add_argument("--answer")
    parser.add_argument("--reviewer", default="self")
    parser.add_argument("--passed", action="store_true")
    args = parser.parse_args()
    state = new_state(args.value or "product") if args.command == "init" else load(args.state)
    if args.command == "begin":
        begin_phase(state, args.value or "intake")
    elif args.command == "answer":
        record_answer(state, args.value or "question", args.answer or "")
    elif args.command == "attach-brief":
        attach_final_brief(state, args.value or "08-implementation-brief.md", [], [])
    elif args.command == "review":
        record_review(state, args.value or state["session"]["current_phase"], args.reviewer, args.passed)
    elif args.command == "checkpoint":
        checkpoint(state, args.value or state["session"]["current_phase"])
    save(args.state, state)
    print(json.dumps(state, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
