# Agent runbooks — on-demand procedures

Procedures pulled out of `AGENTS.md` so they don't cost tokens on every turn. Read the relevant
section when you hit its trigger.

---

## PR flow

Two independent gates guard a PR; a third is on-demand.

### Which lane?

| Diff touches… | Lane | Gate 1 (evaluator) |
|---|---|---|
| `{{SOURCE_DIRS}}` (product source) | **heavy** | **Required** — SHIP verdict |
| anything else (docs, agent config, CI files) | **light** | **Skipped** |

Mixed diff → heavy lane. Light lane is not "no gate" — cheap mechanical checks (junk files,
STATE.md cap) still run via hook where installed.

### Gate 1 — acceptance (`task-evaluator`, heavy lane only)

Spawn `task-evaluator` before opening any PR touching product source — the author must not grade
its own work. Brief: task statement + done-criteria + branch/base only, **never** the
implementation narrative. It re-derives criteria, judges test coverage, builds + runs affected
suites, and returns:

- **SHIP** → open the PR.
- **FIX-FIRST** → fix blockers, re-run **once**; still failing → stop and escalate.

Where the verdict-gate hook is installed, the evaluator writes its verdict to
`/tmp/{{PROJECT_SLUG}}-verdicts/<HEAD sha>` and `gh pr create` is blocked without it.
**Never write that verdict file yourself** — a verdict is earned by a fresh build+test pass on
the exact HEAD, or it is forged. A new commit invalidates it; commit first, evaluate last.

### Gate 2 — review (default flow, standing — no ask needed)

1. **Open the PR** to `{{DEFAULT_BRANCH}}` (push + `gh pr create`, PR template in `--body`,
   `Closes #n` when it resolves an issue).
2. **Auto-spawn the matching reviewer** on the PR's final HEAD, by changed path:
   {{REVIEWER_MAP}}
   Reviewers are read-only — they return review text; they never push or comment themselves.
3. **Post the review** as a PR comment yourself (`gh pr comment <n> --body …`).
4. **Triage every finding**: valid / false-positive / out-of-scope. Never silently drop one.
5. **Apply valid fixes**, run the affected tests, **commit + push** the fix commits.
6. **Post resolutions** — one follow-up comment: each finding → what was done + post-fix test
   result.
7. **Bounded:** at most one re-review round on the new HEAD, then stop.

A reviewer finding triaged false-positive — or a verdict that proves wrong — is GOTCHAS
material: log it and tighten that agent's brief in the same commit.

### Gate 3 — QA (on demand, never blocks)

Code gates can't see visual or behavioral regressions. When the diff touches user-visible
surface, spawn a QA agent (or run the app) to capture evidence for human review before flagging
"needs eyeball". Treat its output as evidence, not as a pass.

---

## Agent delegation

**Default: don't spawn — work inline.** "Thorough"/multi-part is *not* a license to spawn.
Without an opt-in you may add one line noting a task looks parallelizable — but don't spawn.

**Spawn trigger — prompt starts with `__`** (or the user names an agent). Then:

- **Decompose into sequential waves** — atomic tasks, explicit done-criteria, non-overlapping
  file sets. Read-only tasks in a wave batch in one message and run in parallel; **writer tasks
  run one per wave.** Orchestrator integrates between waves (build/test/commit); the
  `task-evaluator` gate runs once, after the last wave.
- **Writers always run ONE AT A TIME.** A parallel writer starts a cold context and pays a full
  uncached prefix while the orchestrator's context is warm — sequential writers reuse the cache,
  and under a quota cap that beats wall-clock. No file-overlap judgement at spawn time: writers
  serialize regardless.
- **Spawn foreground**; brief each subagent self-contained (file paths, relevant rules, expected
  output format, response-length cap). **Never point a subagent at `STATE.md`** — brief it at
  `GOTCHAS.md` instead.
- **Sub-agents never run write-commands** (`git push`, `gh pr comment`, deploys) — read/build/test
  only, unless a task explicitly authorizes a write step.

### Model tiers — quota discipline

| Tier | Use for |
|---|---|
| top (orchestrator's own tier) | never a subagent |
| mid | standard implementation; all reviews; the evaluator |
| small | mechanical work — renames, find-replace, boilerplate, log scanning; ALL read-only fan-out |

- **Never spawn at or above the orchestrator's tier — prefer the lowest tier the brief fits.**
- **Read-only fan-out runs at the smallest tier, no exceptions.** If the answer needs
  *understanding* rather than *locating*, that's reasoning — do it inline; don't upgrade the tier.
- **Reasoning is never delegated** — requirement interpretation, tradeoffs, test-case
  enumeration, wave planning stay with the orchestrator.
- Exception: reviewers and `task-evaluator` keep their own tier even under a cheaper
  orchestrator — their value is independent context, not a cost downgrade.

---

## Delegation mode

**Trigger: prompt starts with `___`.** The orchestrator does the expensive exploration and
synthesis, then hands off a ready-to-execute plan for a cheaper agent to implement. **Stop after
writing the plan file(s)** — do not implement, do not open a PR.

1. **Explore inline** (no spawning): identify every file that changes and why; enumerate test
   cases; pin exact file:line anchors — no "find it yourself" gaps.
2. If the solution needs diagnosis *during* implementation (not just upfront), **stop and ask**:
   implement inline instead, or delegate with an explicit "stop and verify" checkpoint in the plan.
3. **Write plan file(s)** to `~/Downloads/plan-<slug>-<YYYY-MM-DD>.md` (one file per independent
   parallel track). Each must be self-contained — the executing agent needs zero follow-up:

```markdown
# Plan: <task>
Repo: {{PROJECT_SLUG}}  Branch base: {{DEFAULT_BRANCH}}
## Context        <!-- pre-digested findings, exact file:line refs -->
## Success criteria  <!-- testable, binary -->
## Waves          <!-- Wave N: files, imperative task, observable done-criteria -->
## Verification   <!-- exact commands + expected output -->
## Doc-sync required <!-- same commit as the wave that triggers it -->
```

Only confirmed findings go in the plan — never speculation, never `STATE.md` contents.
