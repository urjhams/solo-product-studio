---
name: engineering-cycle
description: Use when implementing, verifying, reviewing, or shipping code in a repository — executing an Implementation Brief, running the build loop from a Behavior Spec, reviewing a diff on more than correctness, hardening before a release, instrumenting for production, or deploying and rolling out. Supplies the depth behind each gate of the generated workflow, and owns everything after the PR merges.
---

# engineering-cycle

`product-studio` decides what to build. `workflow-init` scaffolds the repository and owns the
sequence. This skill is the **depth at each gate**, plus the phase neither of the other two covers:
what happens after the PR merges.

It does not restate the loop. `docs/agent/CARD.md` is the authoritative sequence in any scaffolded
repository, and if the two ever disagree, the CARD wins — it is the file the session hook injects,
so it is what the implementing agent actually read.

## Where you are

Check these three in order; the first that matches is your entry point.

1. **An Implementation Brief exists** (`.product-studio/artifacts/08-implementation-brief.md`).
   Read it and `docs/agent/BEHAVIORS.md` before touching source. The brief names the scope, the
   `do not finish until` checks, and the first vertical slice. Its acceptance criteria cite `BH-###`
   ids; those ids are what your tests must name. Do not re-derive the plan.

2. **A scaffolded repository, no brief** — `docs/agent/CARD.md` exists. Run its loop. This skill
   supplies the content its gates point into (table below). If `BEHAVIORS.md` has a `BH-###` for
   the work, it is authoritative; if not, write the behaviors first and sweep them
   (`docs/agent/RUNBOOKS.md#specify`).

3. **Neither** — stop and route. No behaviors and no product definition means the specification
   work has not happened, and building now produces a green suite over a guess. Send the user to
   `product-studio` for an idea or a product decision, or to `workflow-init` to scaffold a
   repository that already has one. Mid-build and unsure the work still matches the intent →
   `product-recheck`.

## Which reference at which gate

Load one on demand. Do not read them all — that is context flooding, and the whole point of
splitting them is that a task needs two or three.

| When | Read |
|---|---|
| Breaking a brief or a behavior set into ordered, checkable work | `references/planning.md` |
| Writing the code — slice direction, stack discovery, test shape | `references/build-loop.md` |
| Designing a module seam, a package interface, or an endpoint | `references/api.md` |
| A framework-specific decision you would otherwise answer from memory | `references/sources.md` |
| A non-trivial decision you are about to build on | `references/doubt.md` |
| Gate 2 — reviewing a diff (five axes, severity, change sizing) | `references/review.md` |
| The diff touches untrusted input, auth, storage, or a third party | `references/security.md` |
| Something is measurably slow, or a budget is at risk | `references/performance.md` |
| Verifying behavior in a real browser | `references/browser-verification.md` |
| Adding logs, metrics, traces, or alerts | `references/observability.md` |
| An architectural decision was made — new dependency, new boundary, a rejected alternative | `references/adr.md` |
| Cutting a release — version, tag, changelog | `references/release.md` |
| Pipeline gates, feature-flag plumbing, rollback workflow | `references/ci.md` |
| Deploying, rolling out, verifying in production | `references/ship.md` |
| Removing an old system or moving users off one | `references/migration.md` |

`references/checklists/` holds the standing bars the references cite —
`definition-of-done.md` applies to every change regardless of which reference is open.

## After the merge

`workflow-init`'s generated loop ends when the PR merges. This is the part that has no card step,
and the part most likely to be skipped because nothing blocks on it:

1. **Instrument before you need it.** `references/observability.md`. Write the two-to-four
   questions you will be asked at 3am *first*, then pick the signal for each. Telemetry added
   during an incident is telemetry you do not have during the incident.
2. **Version the change.** `references/release.md` — the tag is the source of truth, the changelog
   is written by a person, and a breaking change gets a migration note and a deprecation window.
3. **Ship it.** `references/ship.md` — pre-launch checklist, flag off, staged rollout with decision
   thresholds at each stage, and a rollback plan written *before* the deploy, not during it.
4. **Verify in production.** First hour, against the questions from step 1. A deploy that nobody
   checked is a deploy that nobody knows the state of.
5. **Feed what you learned back.** A surprise in production is `docs/agent/GOTCHAS.md` material,
   in the same commit as the fix. A behavior that turned out wrong is a `BH-###` edit and a
   `product-recheck` input — retire behaviors, never delete them, so the test still asserting a
   removed one stays findable.

## Operating behaviors

These hold across every reference and every gate.

1. **Surface assumptions before building on them.** State them explicitly and invite correction.
   In a repository with a Behavior Spec, an assumption that changes what the product does is an
   `AM-###` in the ambiguity register, not a comment — and one left at `Status: open` blocks the
   work, exactly as it blocks the Implementation Brief upstream.
2. **Manage confusion actively.** Conflicting requirements, or a spec that disagrees with the code,
   means stop and name the conflict. Do not pick a reading and hope. An unresolved ambiguity is a
   question, not a guess.
3. **Push back when warranted.** Name the concrete downside, quantify it where you can, propose the
   alternative, and accept the decision once it is made with full information. Agreeing with a bad
   plan helps nobody.
4. **Enforce simplicity.** The lazy solution that works is the right one. Abstractions earn their
   place or come out.
5. **Hold scope.** Touch what the task names. Something else that needs fixing gets reported, not
   fixed silently — say what you noticed and did not touch.
6. **Verify, don't assume.** Every gate ends in evidence: a passing suite, a build, a trace, a
   screenshot. "Looks right" is not a verification step. The standing bar is
   `references/checklists/definition-of-done.md`.
