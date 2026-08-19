# {{PROJECT_NAME}} — agent instructions

Stable, cross-cutting rules only. The workflow **sequence** lives in
[`docs/agent/CARD.md`](docs/agent/CARD.md) — read it at session start; on Claude Code a
SessionStart hook injects it. Procedures load on trigger, not per turn:
[`docs/agent/RUNBOOKS.md`](docs/agent/RUNBOOKS.md). A link on this page is a pointer, not an
instruction to read.

## Project overview

{{PROJECT_OVERVIEW}}

Components: {{STACKS}}

## Core principles (apply to every change)

1. **Think before coding.** State assumptions; surface tradeoffs and competing interpretations
   instead of silently picking one; stop and ask when confused.
2. **Simplest solution that doesn't foreclose the known next step.** No speculative features,
   premature abstractions, or defensive code for conditions impossible by construction. But say
   what the simple version makes *harder* before you write it, and mark a deliberate shortcut
   with its ceiling and upgrade path.
3. **No unrelated changes in the same commit.** Match surrounding style; don't drive-by-improve
   code the task doesn't touch. A refactor the task genuinely needs **is** in scope — ship it as
   its own named commit.
4. **Goal-driven execution.** Turn the request into testable success criteria and verify against
   them before claiming done — then **state what you did not do**: skipped edge cases, deferred
   scope, untested paths.
5. **Flag deviation from settled practice.** Say so when a request departs from industry practice
   or this repo's own precedent, and why.

{{MODE_POLICY}}

## Agent memory bank

Read at the trigger, not per turn:

| Trigger | Read |
|---|---|
| Session start (only unprompted read) | [`docs/agent/STATE.md`](docs/agent/STATE.md) |
| Something non-obvious cost you time before | [`docs/agent/GOTCHAS.md`](docs/agent/GOTCHAS.md) |
| Writing or changing what the product does | [`docs/agent/BEHAVIORS.md`](docs/agent/BEHAVIORS.md) |
| Opening a PR, delegating, or delegation mode | [`docs/agent/RUNBOOKS.md`](docs/agent/RUNBOOKS.md) |
| Explicit request only | `docs/agent/STATE-archive.md` |

**Update duty (same commit):** every task-completing commit adds ONE compact ≤2-line bullet to
`STATE.md` (cap enforced by its header); anything non-obvious that cost time goes to
`GOTCHAS.md` the moment it's understood; a diff that changes what the product does updates
`BEHAVIORS.md` — retire behaviors rather than deleting them, so the test still asserting a removed
one can be found.

## Working conventions

- **Branch first** — never commit on the default branch.
- **Commit granularity:** smallest self-explanatory unit that builds with its affected tests
  passing; several commits per task, never one massive one. Tests ship with the code they test.
- **Behavior-first, then test-first:** name the behaviors before the tests. `BEHAVIORS.md` is
  authoritative when it covers the work; otherwise write the Given/When/Then you are about to test
  and sweep it for ambiguity ([`RUNBOOKS.md`](docs/agent/RUNBOOKS.md#specify)) — an unresolved
  ambiguity is a question for the user, not a guess. Then write the tests failing, each naming the
  `BH-###` it proves, and implement until green.
- **Explain every command before running it** — one plain-language line.
- {{PR_POLICY}}
  Gates + review flow: [`docs/agent/RUNBOOKS.md`](docs/agent/RUNBOOKS.md#pr-flow).
- **Merge only when the task said to.** `gh pr merge` runs unprompted so a session can chain
  PR → review → merge → next task, which makes this instruction the only gate: no "the PR looks
  good so I merged it". `gh pr merge --admin` is never an option and the hook blocks it —
  branch protection is there by intent.

## Agent delegation

Default: **don't spawn — work inline.** Triggers, tiers, and quota rules:
[`docs/agent/RUNBOOKS.md`](docs/agent/RUNBOOKS.md#agent-delegation). Never point a subagent at
`STATE.md` (orchestrator's rolling log) — brief it at `GOTCHAS.md` instead.

## Build & test

<!-- Per-component commands. Filled at init; keep current. -->
{{BUILD_TEST_COMMANDS}}

## Secrets

Never hardcode secrets. {{SECRETS_NOTE}}
