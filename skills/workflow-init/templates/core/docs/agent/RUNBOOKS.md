# Agent runbooks — on-demand procedures

Procedures pulled out of `AGENTS.md` so they don't cost tokens on every turn. Read the relevant
section when you hit its trigger.

---

## Specify

Runs before Red. A test suite over a misread requirement is green and proves nothing, so the
misreading gets caught here.

`docs/agent/BEHAVIORS.md` is authoritative when it already covers the work — read it, do not
re-derive. When it does not, write the behaviors you are about to test into that file first.

### 1. Behaviors

One `BH-###` per branch of behavior, format at the top of `BEHAVIORS.md`. For the capability you are
touching, walk these eight and write down what happens; a branch that genuinely has no behavior is a
valid answer once written down:

happy path · each precondition failure · each boundary · two actors arriving together · partial
failure · the zero/one/many cases · permission denied · undo, retry, and repeat.

Three rules decide whether a behavior is usable. **Given/When/Then must be constructible** — a test
author can build the state and trigger the action without asking a question. **Observable names
signals, not feelings** — field values, rows, response codes, on-screen copy. **Source cites the
ambiguity or decision it came from** — a behavior with no source is a guess.

Pick the cheapest level that can actually fail when the behavior is wrong. A `unit` test standing in
for an `integration` behavior is tautological: it cannot fail when the real thing breaks.

### 2. Ambiguity sweep

Assume the specification is incomplete. Take each requirement sentence — from the issue, the task
statement, or the user's own words — and pass it against all ten classes, then stop. You are looking
for sentences two competent implementers would build differently, not for missing features.

| Class | The question |
|---|---|
| `term` | Does a noun or verb here have more than one referent? |
| `boundary` | When exactly does the state change — before, at, or after? |
| `actor` | Who may do this, on whose behalf, and who may not? |
| `state` | Which states exist, and which transitions are legal? |
| `timing` | Simultaneous requests, races, retries, reordering, repeats? |
| `failure` | What if half succeeds? Roll back or compensate? Sync or async? |
| `identity` | What makes two of these the same? Persisted or derived? |
| `quantity` | How many, how fast, how large? Zero, one, many? |
| `visibility` | Who sees this, when, and what exactly are they told? |
| `reversibility` | Money, email, external calls — can it be undone, and by whom? |

Each finding becomes one `AM-###` with two reasonable readings, **the concrete case where a user sees
a different result under each**, the decision needed, and your recommendation with its confidence.
If you cannot name a user-visible difference, the ambiguity does not matter — drop it. If reading B
is a strawman, this is not an ambiguity, it is you stating a preference.

### 3. Close every ambiguity

`resolved` (a decision was made — record the ADR), `deferred` (not needed yet — record the assumption
and a `Revisit when:` trigger naming an observable signal, not a date), or `out_of_scope` (real case,
product will not handle it; write the behavior that refuses it so the refusal is deliberate).

**`open` is not a resting place.** Resolve what the repo's existing decisions already answer, then
ask the user the rest — one at a time, highest impact first, with numbered readings and your
recommended pick. An ambiguity the user declines to settle becomes `deferred`, never `open`.

Resolving one ambiguity routinely exposes another. Re-read the behaviors with the resolutions
applied and sweep again; stop when a pass finds nothing new.

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
{{REVIEW_LANE_STEPS}}
4. **Triage every finding**: valid / false-positive / out-of-scope. Never silently drop one.
5. **Apply valid fixes**, run the affected tests, **commit + push** the fix commits.
6. **Post resolutions** — one follow-up comment: each finding → what was done + post-fix test
   result.
7. **Bounded:** at most one re-review round on the new HEAD, then stop.

A reviewer finding triaged false-positive — or a verdict that proves wrong — is GOTCHAS
material: log it and tighten that agent's brief in the same commit.

**Review axes.** Spec, Correctness, Readability, Architecture, Security, Performance. Spec is the
one a clean-looking diff fails, so judge it first: where `docs/agent/BEHAVIORS.md` covers the diff,
the `BH-###` entries outrank the task prose, and a test naming no behavior is an orphan that
usually encodes a misread requirement. One structural problem outranks ten nits — if both are
present, the structural one *is* the review. A diff too large to review properly is itself a
finding: say what it should be split along rather than rubber-stamping it.
When `docs/engineering/` is present, `review.md` is the long form and `security.md` /
`performance.md` are the depth behind the last two axes.

### Gate 3 — QA (on demand, never blocks)

Code gates can't see visual or behavioral regressions. When the diff touches user-visible
surface, spawn a QA agent (or run the app) to capture evidence for human review before flagging
"needs eyeball". Treat its output as evidence, not as a pass.
With `docs/engineering/` present: `checklists/accessibility-checklist.md` is the standing bar for
user-visible surface, and `browser-verification.md` covers runtime checks in a real browser.

### After the merge

The loop ends at Gate 2 because that is where *this* repo's mechanisms end — nothing here blocks
on a deploy. The work that follows a merge is real and easy to skip: instrument against the
questions you'd be asked at 3am, version and changelog the change, ship it behind a flag with a
rollback plan written *before* the deploy, and verify in production within the first hour.
`docs/engineering/{observability,release,ship}.md` when present; otherwise the `engineering-cycle`
skill. A surprise in production is GOTCHAS material in the same commit as the fix; a behavior that
turned out wrong is a `BH-###` edit — retire it, never delete it.

---

## Agent delegation

**Default: don't spawn — work inline.** "Thorough"/multi-part is *not* a license to spawn.
Without an opt-in you may add one line noting a task looks parallelizable — but don't spawn.

**Spawn trigger — prompt starts with `__`** (or the user names an agent). Then:

- **Decompose into sequential waves** — atomic tasks, explicit done-criteria, non-overlapping
  file sets. Read-only tasks in a wave batch in one message and run in parallel (with the one
  warm-up exception under *Cache discipline* below); **writer tasks run one per wave.** Orchestrator integrates between waves (build/test/commit); the
  `task-evaluator` gate runs once, after the last wave.
- **Writers always run ONE AT A TIME** — two writers in flight can clobber each other's edits, and
  no file-overlap judgement at spawn time is trustworthy enough to permit it. Writers serialize
  regardless. (Sequential same-type spawns also reuse that agent type's cached prefix — a bonus,
  not the reason.)
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

### Cache discipline — where subagent quota actually goes

Prompt caching is a **prefix match**: reuse happens only where two requests share identical
leading bytes. A subagent's prefix is its own system prompt + tools + agent definition, which is
*not* the orchestrator's prefix.

- **A subagent never inherits the orchestrator's cache**, sequential or parallel. The only reuse
  available is between spawns of the **same agent type**, over their shared definition.
- **A cache entry is readable only after the first spawn's response starts streaming.** N spawns
  of one type fired in a single message therefore all miss and each pays a full uncached prefix.
  At **N ≥ 3** read-only spawns of the same type: send one, then batch the rest — one write plus
  N−1 cheap reads. At N ≤ 2, just batch; the round-trip costs more than it saves.
- **Fire a wave's spawns back-to-back.** Cache entries expire in minutes; an orchestrator detour
  between spawns of the same type forfeits the reuse.
- **Keep `.claude/agents/*.md` byte-stable.** Never write dates, run IDs, `STATE.md` contents, or
  any per-session state into an agent definition — one changed byte invalidates that agent type's
  entire cached prefix. Edit agent definitions as a deliberate change, not as routine bookkeeping.
- **Order every brief stable-first:** shared rules, output format, and length cap up top;
  task-specific paths and done-criteria last. Only the leading shared portion can be reused.

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
