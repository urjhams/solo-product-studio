# Subagent Orchestration Patterns

Patterns for delegating work to subagents: when to spawn at all, how to tier and batch them, why the
cache rules aren't optional, and how to dispatch a fresh-context reviewer for a non-trivial decision.
The delegation trigger and gate mechanics live in `docs/agent/RUNBOOKS.md#agent-delegation`; this is
the reusable pattern set other references point at instead of re-deriving.

## Default: don't spawn

Work inline by default. "This is thorough" or "this has multiple parts" is not, by itself, a license
to spawn — spawning has a real quota cost and a subagent starts with none of the orchestrator's
context. Spawn only on an explicit trigger (a `__`-prefixed prompt, or the user naming an agent).
Absent the trigger, at most note that a task looks parallelizable — don't act on the note yourself.

## Decompose into waves

When delegation is triggered:

1. Break the work into atomic tasks with explicit done-criteria and non-overlapping file sets.
2. Batch every read-only task in a wave into one message — they run in parallel (see the cache
   caveat below).
3. **Writers run one at a time, always.** Two writers in flight can clobber each other's edits, and
   no amount of file-overlap analysis at spawn time is trustworthy enough to permit concurrent
   writes. This is not a judgment call per task — it's a standing rule.
4. The orchestrator integrates between waves — build, test, commit — and the `task-evaluator` gate
   runs once, after the last wave, not per wave.

## Model tiers — quota discipline

| Tier | Use for |
|---|---|
| Top (orchestrator's own tier) | Never a subagent |
| Mid | Standard implementation, all reviews, the evaluator |
| Small | Mechanical work — renames, find-replace, boilerplate, log scanning; **all** read-only fan-out |

- Never spawn at or above the orchestrator's own tier. Prefer the lowest tier the brief actually
  fits.
- Read-only fan-out runs at the smallest tier, no exceptions. If the answer needs *understanding*
  rather than *locating*, that's reasoning — do it inline; don't upgrade the tier to compensate.
- Reasoning stays with the orchestrator: requirement interpretation, tradeoffs, test-case
  enumeration, wave planning. None of that delegates.
- Exception: reviewers and `task-evaluator` keep their own tier even under a cheaper orchestrator —
  their value is independent context, not a cost downgrade.

## Cache discipline

Prompt caching is a prefix match: reuse only happens where two requests share identical leading
bytes.

- A subagent never inherits the orchestrator's cache, sequential or parallel. The only reuse
  available is between spawns of the **same agent type**, over their shared definition.
- A cache entry is only readable after the first spawn's response starts streaming. N spawns of one
  type fired together in a single message all miss and each pays the full uncached prefix.
  At N ≥ 3 read-only spawns of the same type: send one first, then batch the remaining N−1 — one
  write plus N−1 cheap reads. At N ≤ 2, just batch; the round trip costs more than it saves.
- Fire a wave's spawns back-to-back. Cache entries expire in minutes; an orchestrator detour between
  spawns of the same type forfeits the reuse.
- Keep `.claude/agents/*.md` byte-stable. Never write dates, run IDs, or per-session state into an
  agent definition — one changed byte invalidates that agent type's entire cached prefix.
- Order every brief stable-first: shared rules, output format, and length cap up top; task-specific
  paths and done-criteria last. Only the leading shared portion is reusable.

## Fresh-context review dispatch

For a non-trivial decision — new branching logic, a module or service boundary, a property the
compiler can't verify, an irreversible blast radius — the pattern is a bounded doubt cycle, not a
second opinion bolted onto the diff:

1. **Claim.** State what stands, in two or three lines, and why it matters if wrong.
2. **Extract.** Hand the reviewer the artifact (the diff, the function, the proposal) and the
   contract it has to satisfy — stripped of your reasoning. If you hand over conclusions, you get
   back agreement with your conclusions.
3. **Doubt.** Spawn the reviewer with an adversarial prompt — "find what's wrong," not "is this
   good." Pass artifact and contract only; never pass the claim, which biases toward agreement.
4. **Reconcile.** The reviewer's output is data, not a verdict — re-read the artifact against each
   finding before classifying: contract misread (fix the contract, re-run) / valid and actionable
   (fix it) / valid trade-off (document it) / noise (note it, move on).
5. **Stop.** Bounded at trivial-findings-only, three cycles, or explicit user override — whichever
   comes first. A third cycle still surfacing real issues is information about the artifact, not a
   reason to keep looping alone.

This dispatch pattern is what backs Gate 1 and Gate 2 in `docs/agent/RUNBOOKS.md#pr-flow`:
`task-evaluator` is the fresh-context reviewer for acceptance (briefed on task statement +
done-criteria + branch/base only, never the implementation narrative — the author must not grade its
own work), and the PR review pass is the same pattern applied to the finished diff.

## Sub-agent constraints

- Brief every subagent self-contained: file paths, the relevant rules, expected output format, a
  response-length cap. A subagent starts with none of the orchestrator's context — put in the brief
  what it needs, not what would be convenient to omit.
- Never point a subagent at `docs/agent/STATE.md`. Brief it at `docs/agent/GOTCHAS.md` instead —
  `STATE.md` is session-scoped and per-byte cache-fragile; `GOTCHAS.md` is the stable, shareable
  context.
- Subagents never run write-commands — `git push`, `gh pr comment`, deploys — unless the task
  explicitly authorizes that specific write step. Default to read/build/test only.
