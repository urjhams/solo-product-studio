# QA session protocol

Use this protocol for intake and every internal capability.

## State machine

```text
new → intake → proposed → confirmed → drafting → review → approved
                         ↘ paused       ↘ rejected
```

Persist `session.status`, `session.current_stage`, `session.current_gate`, `session.questions`, `session.next_action`, and `session.updated_at` in `.product-studio/project.yaml`. Never advance from `proposed` without a user confirmation answer.

## Question loop

1. Read state and all artifact headings before asking anything.
2. Build a missing-answer list from the current capability's inputs and gate.
3. Remove anything already answered or explicitly rejected.
4. Ask one highest-impact question, preferring 2–6 numbered choices plus `Other`.
5. Record the answer and update the relevant product, constraint, assumption, or decision section.
6. Repeat until the current gate can be evaluated.

## Draft and review loop

1. Load the capability contract and matching template.
2. Draft every required section; use `Unknown`, `Assumption`, or `Not applicable` rather than inventing content.
3. Display the draft summary, uncertainty list, rejected alternatives, and proposed next test.
4. Ask the user to approve, correct, pause, or reject.
5. On correction, return to `drafting` and ask only targeted questions.
6. On approval, validate the completion gate, write the artifact, and set the next gate.

## Failure and fallback

When a tool or provider is unavailable, record its status and selected fallback in `capabilities`. Continue with the bundled fallback. When evidence is unavailable, lower confidence and create a research plan. When a required decision is missing, remain in `review` and ask for it.

## Resume

On a later invocation, read the state and artifact index, summarize the last approved artifact and current gate, then offer: continue, review state, change direction, implement, export, or deliver to GitHub. Do not restart intake unless the user requests a reset.
