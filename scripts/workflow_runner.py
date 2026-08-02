#!/usr/bin/env python3
"""Small dependency-free state machine for Product Studio phase checkpoints."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

PHASES = ("intake", "product", "research", "design", "mvp", "review", "production", "final_planning")
STATUSES = ("pending", "in_progress", "reviewing", "checkpointed", "approved", "blocked", "skipped")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def new_state(project_id: str = "product") -> dict[str, Any]:
    return {
        "project_id": project_id,
        "autonomy": "phase_checkpoints",
        "status": "intake",
        "current_phase": "intake",
        "current_gate": "goal-and-house-rules",
        "next_action": "ask-intake-question",
        "questions": [],
        "unanswered_questions": [],
        "iteration_count": 0,
        "approval_status": "pending",
        "last_checkpoint": None,
        "phases": {phase: {"status": "pending", "done_bar": [], "result": None} for phase in PHASES},
        "reviews": [],
        "updated_at": now(),
    }


def record_answer(state: dict[str, Any], question: str, answer: str, *, decision_id: str | None = None) -> dict[str, Any]:
    state.setdefault("questions", []).append({"question": question, "answer": answer, "decision_id": decision_id, "answered_at": now()})
    state.setdefault("unanswered_questions", [])
    state["unanswered_questions"] = [item for item in state["unanswered_questions"] if item != question]
    state["updated_at"] = now()
    return state


def begin_phase(state: dict[str, Any], phase: str, done_bar: list[str] | None = None) -> dict[str, Any]:
    if phase not in PHASES:
        raise ValueError(f"Unknown phase: {phase}")
    state["current_phase"] = phase
    state["status"] = "in_progress"
    state["approval_status"] = "pending"
    state["current_gate"] = f"{phase}-done-bar"
    state["next_action"] = "run-phase"
    state["phases"][phase]["status"] = "in_progress"
    if done_bar is not None:
        state["phases"][phase]["done_bar"] = done_bar
    state["updated_at"] = now()
    return state


def record_review(state: dict[str, Any], phase: str, reviewer: str, passed: bool, findings: list[str] | None = None) -> dict[str, Any]:
    if phase not in PHASES:
        raise ValueError(f"Unknown phase: {phase}")
    independent = reviewer in {"independent", "fresh_context", "subagent"}
    review = {"phase": phase, "reviewer": reviewer, "independent": independent, "passed": passed, "findings": findings or [], "recorded_at": now()}
    state.setdefault("reviews", []).append(review)
    state["phases"][phase]["status"] = "reviewing"
    state["phases"][phase]["result"] = review
    state["iteration_count"] += 1
    state["next_action"] = "repair-highest-impact-gap" if not passed else "checkpoint"
    state["updated_at"] = now()
    return state


def checkpoint(state: dict[str, Any], phase: str) -> dict[str, Any]:
    if phase not in PHASES:
        raise ValueError(f"Unknown phase: {phase}")
    phase_reviews = [review for review in state.get("reviews", []) if review["phase"] == phase]
    independent_pass = any(review["independent"] and review["passed"] for review in phase_reviews)
    any_pass = any(review["passed"] for review in phase_reviews)
    if not independent_pass:
        state["phases"][phase]["status"] = "blocked" if any_pass else "reviewing"
        state["approval_status"] = "self_review_only" if any_pass else "pending"
        state["next_action"] = "obtain-independent-review"
        state["updated_at"] = now()
        return state
    state["phases"][phase]["status"] = "checkpointed"
    state["status"] = "checkpointed"
    state["approval_status"] = "approved"
    state["last_checkpoint"] = {"phase": phase, "at": now()}
    index = PHASES.index(phase)
    if index + 1 < len(PHASES):
        state["next_action"] = f"begin-{PHASES[index + 1]}"
        state["current_gate"] = f"{PHASES[index + 1]}-done-bar"
    else:
        state["next_action"] = "offer-completion-actions"
    state["updated_at"] = now()
    return state


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def save(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("command", choices=("init", "begin", "answer", "review", "checkpoint"))
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
    elif args.command == "review":
        record_review(state, args.value or state["current_phase"], args.reviewer, args.passed)
    elif args.command == "checkpoint":
        checkpoint(state, args.value or state["current_phase"])
    save(args.state, state)
    print(json.dumps(state, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
