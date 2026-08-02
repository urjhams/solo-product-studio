# QA session protocol

Use this protocol for intake and every internal capability. It combines focused questions with autonomous phase execution.

## State machine

```text
new → intake → proposed → confirmed → drafting → reviewing → checkpointed → next phase
                         ↘ paused       ↘ rejected              ↘ blocked
```

Persist `session.status`, `session.current_phase`, `session.current_gate`, `session.questions`, `session.next_action`, `session.iteration_count`, and `session.updated_at` in `.product-studio/project.yaml`. Never advance from `proposed` without a user confirmation answer.

## Question loop

1. Read state, artifact headings, repository context, and prior review findings before asking anything.
2. Build a missing-answer list from the goal, house rules, current phase, and phase done bar.
3. Remove anything already answered or explicitly rejected.
4. Rank questions by impact, irreversibility, rework risk, and whether the answer can be inferred.
5. Ask one highest-impact question, preferring 2–6 numbered choices plus `Other`.
6. Record the answer and update the relevant product, constraint, assumption, or decision section immediately.
7. Repeat only until the phase can run safely; do not ask the user to choose internal procedures.

## Draft and review loop

1. Load the capability contract, matching template, house rules, and phase done bar.
2. Draft every required section; use `Unknown`, `Assumption`, or `Not applicable` rather than inventing content.
3. Evaluate the draft against the done bar and list the highest-impact gaps.
4. Run an independent review context. The builder must not be the only grader. If the host cannot provide one, set `approval_status: self_review_only` and keep the phase blocked for approval.
5. Repair the highest-impact gap, increment `session.iteration_count`, and evaluate again.
6. Repeat until the bar passes or the agent is genuinely blocked.
7. At the phase checkpoint, show the result, remaining uncertainty, next phase, and any user decision required. Use `scripts/workflow_runner.py` to record the transition when deterministic state is needed.

## Failure and fallback

When a tool or provider is unavailable, record its status and selected fallback in `capabilities`. Continue with the bundled fallback. When evidence is unavailable, lower confidence and create a research plan. When a required decision is missing, remain in `review` and ask for it.

## Resume

On a later invocation, read the state and artifact index, summarize the last approved artifact and current gate, then offer: continue, review state, change direction, implement, export, or deliver to GitHub. Do not restart intake unless the user requests a reset.

## Autonomy rule

Default to `phase_checkpoints`. Once a phase is confirmed, continue through drafting, review, and repair without asking for approval after every intermediate artifact. Switch to artifact checkpoints only when the user requests stricter control or when an artifact is externally consequential.
