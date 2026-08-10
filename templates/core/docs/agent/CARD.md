# Workflow card — read at session start

You are in **{{PROJECT_NAME}}**. Full rules: root `AGENTS.md` (or `CLAUDE.md`). This card is the
*sequence*; it names which file to open at which trigger, so you never re-derive the workflow.

**Read now, before substantive work — the ONLY file you open unprompted:**
`docs/agent/STATE.md` (where we are).

**Open on trigger only:** debugging or something feels non-obvious → `docs/agent/GOTCHAS.md` ·
writing or changing behavior → `docs/agent/BEHAVIORS.md` · opening a PR or delegating →
`docs/agent/RUNBOOKS.md`.
**Never auto-read:** `STATE-archive.md`.

## The loop

1. **Branch first.** Never commit on the default branch.
2. **Specify.** Behaviors before tests. If `docs/agent/BEHAVIORS.md` has a `BH-###` for this work
   it is authoritative — read it, do not re-derive. Otherwise write the behaviors you are about to
   test, one Given/When/Then each, and sweep them for ambiguity (`RUNBOOKS.md#specify`). **An
   unresolved ambiguity is a question, not a guess** — a green suite over a misread requirement
   proves nothing. Architectural decision (new dependency, new boundary, rejecting a plausible
   alternative) → record it (ADR or equivalent) in the same task, never as a follow-up.
3. **Red.** One failing test per behavior, and each test names the behavior it proves — `BH-###`
   in the test name or a comment directly above it. Test: `{{TEST_CMD}}`
4. **Green.** Smallest change that passes. Build: `{{BUILD_CMD}}`
5. **Refactor.** Tests stay green. No new behavior here — that needs a new `BH-###` and its own
   red step.
6. **Commit atomically** — smallest unit that builds with its tests passing. Several commits per
   task, never one giant one. Tests go in the same commit as the code they test.
7. **Sync docs in the same commit** — contracts, maps, and `BEHAVIORS.md` when the diff changes
   what the product does.
8. **Task-completing commit updates `STATE.md`** — ONE compact ≤2-line bullet under
   "Current focus", newest first; fold the oldest into `STATE-archive.md` at the cap.
9. **Gate — only if the diff touches product source** (`{{SOURCE_DIRS}}`): spawn `task-evaluator`
   (the author must not grade its own work). SHIP → PR; FIX-FIRST → fix, re-run **once**, then
   escalate. **Docs/tooling-only diff → light lane: do NOT spawn the evaluator.**
10. **Finishing a task = opening its PR** to `{{DEFAULT_BRANCH}}` — automatic, not on request.
11. **Then the review:** {{REVIEW_LANE}} (Full flow: `RUNBOOKS.md#pr-flow`.)
12. **Bounded loops:** one evaluator re-run, one reviewer re-review. Then stop and escalate.

## Delegation

**Default: do not spawn — work inline.** Spawn only when the prompt starts with `__` or the user
names an agent. Prefer the **lowest** model tier the brief fits; never spawn at or above your own
tier. Read-only fan-out runs at the cheapest tier available; **writers run one at a time**
(parallelism is for read-only work only — concurrent writers clobber each other's edits).
Spawn foreground; brief each subagent self-contained. Full playbook — including the cache rules
that decide what a wave actually costs: `RUNBOOKS.md#agent-delegation`.
