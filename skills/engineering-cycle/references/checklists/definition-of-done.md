# Definition of Done

The standing bar a change clears before it counts as done. Task-specific acceptance criteria
(`references/planning.md`) answer "did we build the right thing"; this answers "is it actually
finished." Run it before the Gate step in `docs/agent/CARD.md`, not after — a FIX-FIRST from
`task-evaluator` on something this would have caught is a wasted round trip.

**The floor applies to every change. The rest is profile-derived.** A throwaway demo held to a
production bar wastes the timebox it exists to protect, and a production change held to a demo bar
ships unreviewed. Each section below names the `workflow_profile` field that turns it on — read
`.product-studio/project.json`, or treat the durable defaults as in force when there is no profile.
Nothing here relaxes the safety floor: secret hygiene, input validation on any path that can crash
or corrupt, and least-privilege permissions hold in every mode.

## Correctness — floor, every mode

- [ ] The repository's own test command was run, not an assumed default — `references/build-loop.md#discover-the-stack-first`
- [ ] The repository's own build command succeeds
- [ ] Type checking passes, where the stack has one
- [ ] Linting passes, where the repo runs one
- [ ] No **new** build warnings beyond the recorded baseline — pre-existing warnings in an
      inherited repository are debt to report, not a gate to fail on
- [ ] The affected suite was run after the last code change, not before it

## Behavior coverage — `testing.automated_required`

- [ ] `automated_required: smoke` — the one high-signal check on the path that carries the
      change passes; `core` — every `Status: active` `BH-###` touched by this change has a
      covering test; `full` — the above plus the regression case
- [ ] Every `Status: active` `BH-###` touched by this change has a covering test (`core`, `full`)
- [ ] Each new or changed test names the `BH-###` it proves, in its name or the comment above it
- [ ] Bug fixes include a reproduction test that failed before the fix — `references/build-loop.md#the-prove-it-pattern-bug-fixes`
- [ ] No test was skipped or disabled to make the suite pass

## Scope discipline — floor, every mode

- [ ] The diff touches only what the task, brief, or `BH-###` named
- [ ] Anything noticed but out of scope was reported, not fixed silently —
      `references/build-loop.md#scope-discipline`
- [ ] No unrelated refactors, import cleanups, or syntax modernization riding along

## Ambiguity and decisions — `planning.spec_gate`

- [ ] `spec_gate: block` — no `Status: open` ambiguity remains in the register for this change;
      `open` is not a resting place, it's `resolved`, `deferred` with a `Revisit when:` trigger, or
      `out_of_scope`. `spec_gate: warn` — an open ambiguity is recorded and reported, not a blocker
- [ ] A new dependency, a new boundary, or a rejected plausible alternative has an ADR —
      `references/adr.md`. Not required where `development.refactor_phase` is false: a build with
      no second version to be consistent with has no architecture to record

## Docs synced in the same commit — floor, except the mirror (`planning.spec_gate`)

- [ ] `docs/agent/BEHAVIORS.md` reflects the diff, if the diff changes what the product does — and where `spec_gate: block`, its mirror is byte-identical to the canonical spec
- [ ] Contracts, maps, or other docs the diff makes stale are updated, not left to drift
- [ ] `docs/agent/STATE.md` has one compact ≤2-line bullet under "Current focus," newest first
- [ ] A production surprise this task uncovered is in `docs/agent/GOTCHAS.md`, same commit as the fix

## Commit hygiene — floor, every mode

- [ ] Commits are atomic — smallest unit that builds with its tests passing, not one giant commit
- [ ] Tests land in the same commit as the code they test
- [ ] No debug output, commented-out code, or stray files left in the diff

## Evidence, not confidence — floor, every mode

- [ ] Every claim of "done" has evidence behind it — a passing suite, a build, a trace, a screenshot
- [ ] "Looks right" or "should work" does not appear as the final verification step
- [ ] Gate 1 (`task-evaluator`) ran for any diff touching product source. Gate 2 (review) is queued
      or complete where `review.independent_required` is true — where it is false, a recorded self
      review is the honest outcome and the phase says `self_review_only`, never "approved".
      Gate 3 (QA) ran if the diff touches user-visible surface
