# Definition of Done

The standing bar every change clears before it counts as done, regardless of which reference
governed the work. Task-specific acceptance criteria (`references/planning.md`) answer "did we
build the right thing"; this answers "is it actually finished." Run it before the Gate step in
`docs/agent/CARD.md`, not after — a FIX-FIRST from `task-evaluator` on something this would have
caught is a wasted round trip.

## Correctness

- [ ] The repository's own test command was run, not an assumed default — `references/build-loop.md#discover-the-stack-first`
- [ ] The repository's own build command succeeds
- [ ] Type checking passes, where the stack has one
- [ ] Linting passes, where the repo runs one
- [ ] The affected suite was run after the last code change, not before it

## Behavior coverage

- [ ] Every `Status: active` `BH-###` touched by this change has a covering test
- [ ] Each new or changed test names the `BH-###` it proves, in its name or the comment above it
- [ ] Bug fixes include a reproduction test that failed before the fix — `references/build-loop.md#the-prove-it-pattern-bug-fixes`
- [ ] No test was skipped or disabled to make the suite pass

## Scope discipline

- [ ] The diff touches only what the task, brief, or `BH-###` named
- [ ] Anything noticed but out of scope was reported, not fixed silently —
      `references/build-loop.md#scope-discipline`
- [ ] No unrelated refactors, import cleanups, or syntax modernization riding along

## Ambiguity and decisions

- [ ] No `Status: open` ambiguity remains in the ambiguity register for this change — `open` is not
      a resting place; it's `resolved`, `deferred` with a `Revisit when:` trigger, or `out_of_scope`
- [ ] A new dependency, a new boundary, or a rejected plausible alternative has an ADR —
      `references/adr.md`

## Docs synced in the same commit

- [ ] `docs/agent/BEHAVIORS.md` reflects the diff, if the diff changes what the product does
- [ ] Contracts, maps, or other docs the diff makes stale are updated, not left to drift
- [ ] `docs/agent/STATE.md` has one compact ≤2-line bullet under "Current focus," newest first
- [ ] A production surprise this task uncovered is in `docs/agent/GOTCHAS.md`, same commit as the fix

## Commit hygiene

- [ ] Commits are atomic — smallest unit that builds with its tests passing, not one giant commit
- [ ] Tests land in the same commit as the code they test
- [ ] No debug output, commented-out code, or stray files left in the diff

## Evidence, not confidence

- [ ] Every claim of "done" has evidence behind it — a passing suite, a build, a trace, a screenshot
- [ ] "Looks right" or "should work" does not appear as the final verification step
- [ ] Gate 1 (`task-evaluator`) ran for any diff touching product source; Gate 2 (review) is queued
      or complete; Gate 3 (QA) ran if the diff touches user-visible surface
