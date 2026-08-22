# QA session protocol

Use this protocol for intake and every internal capability. It combines focused questions with autonomous phase execution.

## State machine

```text
new → intake → proposed → confirmed → drafting → reviewing → checkpointed → next phase
                         ↘ paused       ↘ rejected              ↘ blocked
```

Persist `session.status`, `session.current_phase`, `session.current_gate`, `session.questions`, `session.next_action`, `session.iteration_count`, and `session.updated_at` in `.product-studio/project.json`. Never advance from `proposed` without a user confirmation answer.

## Question loop

1. Read state, artifact headings, repository context, and prior review findings before asking anything.
2. Build a missing-answer list from the goal, house rules, current phase, and phase done bar.
3. Remove anything already answered or explicitly rejected.
4. Rank questions by impact, irreversibility, rework risk, and whether the answer can be inferred.
5. Ask one highest-impact question, preferring 2–6 numbered choices plus `Other`.
6. Record the answer and update the relevant product, constraint, assumption, or decision section immediately.
7. Repeat only until the phase can run safely; do not ask the user to choose internal procedures.

In the define phase this loop runs once per slot, in slot order, with a bounded research pass
attached to the slots that need one — `references/define-loop.md` carries the order, the research
triggers, and what makes a slot filled rather than merely written. In the design phase,
`references/design-loop.md` carries the same for the magic moment, onboarding path, landing/store
copy, and design system.

## Intent extraction (intake only)

For a raw or vague idea, `references/idea-validation.md` runs first, before this section. The
hypothesis below is built from its confirmed/refined idea, not the original unvalidated one.

The question loop above finds *missing answers*. Intake has a harder job first: finding out what
the user actually wants, which is not always what they say or even what they think they should
say. Everything downstream — mode, platform, behaviors, the entire Behavior Spec — inherits this
misreading if it happens, and no amount of ambiguity sweeping later catches a goal that was wrong
from the first sentence.

**Carry a hypothesis with a number.** Before the first question, and again as answers land:

```text
HYPOTHESIS: <one sentence, your best read of what they want>
CONFIDENCE: <0–100%> — <what is missing, whenever this is below ~70%>
```

Stating the number is the point. An unstated hypothesis cannot be corrected, and a confident-
sounding question built on a 30% read wastes the user's turn.

**Attach your guess to every question.** Asking blind makes the user do all the work; guessing
lets them correct in three words instead of three sentences:

```text
Q: <one focused question>
GUESS: <what you think the answer is>
```

One question per turn. Wait for the answer. This holds even when three questions feel obvious —
the second is usually answered by the first, and asking both anyway teaches the user that their
answers are not being read.

**Listen for want versus should-want.** When an answer sounds like it is signalling
sophistication, budget-consciousness, or what a Serious Product Person would say, ask:

> *"If you didn't have to justify this to anyone, what would you actually want?"*

The gap between the two answers is where the real product usually is. Record the stated answer as
the requirement and the unlocked one as an `A-###` assumption when they conflict — do not silently
prefer either.

**Stop at 95% by a test, not a feeling.** *Can I predict the user's reaction to the next three
questions I would ask?* If yes, stop asking and restate. If you have asked seven questions and
still cannot predict, something foundational is missing — say that instead of asking an eighth.

**Restate in their words, six lines, before any planning:**

```text
- Outcome:      <one line>
- User:         <one line — who benefits>
- Why now:      <one line — what changed>
- Success:      <one line — how we know it worked>
- Constraint:   <one line — the binding limit>
- Out of scope: <one line — what we are explicitly not doing>
```

**`Out of scope` is non-negotiable.** A restate without it reads as agreement with everything the
user has ever mentioned, and every later cut then looks like a broken promise rather than a
decision. This restate feeds the intake summary, the goal, and the protected outcome in
`house-rules.md`.

**Confirmation means an explicit yes.** These do not count: *"whatever you think"*, *"sounds
good"*, *"sure, let's go"*, and silence. Each is a deferral, not agreement — treat it as a signal
that a line in the restate is wrong and ask which one.

Prototype mode shortens this; it does not skip it. A prototype built on a misread intent has
validated nothing, which is the same failure `spec-hardening.md` exists to prevent one level down.

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
