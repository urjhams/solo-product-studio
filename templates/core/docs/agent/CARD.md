# Workflow card — read at session start

You are in **{{PROJECT_NAME}}**. Full rules: root `AGENTS.md` (or `CLAUDE.md`). This card is the
*sequence*; it names which file to open at which trigger, so you never re-derive the workflow.

**Read now, before substantive work — the ONLY file you open unprompted:**
`docs/agent/STATE.md` (where we are).

**Open on trigger only:** debugging or something feels non-obvious → `docs/agent/GOTCHAS.md` ·
opening a PR or delegating → `docs/agent/RUNBOOKS.md`.
**Never auto-read:** `STATE-archive.md`.

## The loop

1. **Branch first.** Never commit on the default branch.
2. **Plan.** State assumptions and success criteria before writing code. Architectural decision
   (new dependency, new boundary, rejecting a plausible alternative) → record it (ADR or
   equivalent) in the same task, never as a follow-up.
3. **Tests first.** Enumerate cases, write them failing, then implement until green.
   Build: `{{BUILD_CMD}}` · Test: `{{TEST_CMD}}`
4. **Commit atomically** — smallest unit that builds with its tests passing. Several commits per
   task, never one giant one. Tests go in the same commit as the code they test.
5. **Sync docs in the same commit** — contracts, maps, and specs the diff touches.
6. **Task-completing commit updates `STATE.md`** — ONE compact ≤2-line bullet under
   "Current focus", newest first; fold the oldest into `STATE-archive.md` at the cap.
7. **Gate — only if the diff touches product source** (`{{SOURCE_DIRS}}`): spawn `task-evaluator`
   (the author must not grade its own work). SHIP → PR; FIX-FIRST → fix, re-run **once**, then
   escalate. **Docs/tooling-only diff → light lane: do NOT spawn the evaluator.**
8. **Finishing a task = opening its PR** to `{{DEFAULT_BRANCH}}` — automatic, not on request.
9. **Then the review:** spawn the matching `<area>-reviewer` on the PR's HEAD, post its review to
   the PR, triage every finding, apply valid fixes, run affected tests, commit + push, post
   resolutions. (Full flow: `RUNBOOKS.md#pr-flow`.)
10. **Bounded loops:** one evaluator re-run, one reviewer re-review. Then stop and escalate.

## Delegation

**Default: do not spawn — work inline.** Spawn only when the prompt starts with `__` or the user
names an agent. Prefer the **lowest** model tier the brief fits; never spawn at or above your own
tier. Read-only fan-out runs at the cheapest tier available; **writers run one at a time**
(parallelism is for read-only work only — concurrent writers clobber each other's edits).
Spawn foreground; brief each subagent self-contained. Full playbook — including the cache rules
that decide what a wave actually costs: `RUNBOOKS.md#agent-delegation`.
