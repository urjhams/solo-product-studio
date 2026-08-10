# Behavior discovery

Run this at the start of the `specify` phase, after the Design Contract and before spec hardening.
It produces the behaviors half of the Behavior Spec; `references/spec-hardening.md` produces the
ambiguity half.

## Product scope is not behavior scope

**Product scope** answers *which capabilities ship*. **Behavior scope** answers, for one in-scope
capability, *every branch it must handle*.

Cutting product scope removes capabilities and makes the release smaller. Cutting behavior scope
removes correctness and makes the release wrong. They are decided by different people for different
reasons and must not be traded against each other — "we cut the concurrency case to hit the
timebox" is a correctness decision disguised as a scope decision, and it belongs in the ambiguity
register as `deferred` with a revisit trigger, not in the cut list.

The Design Contract's cut list governs product scope. This document governs behavior scope. A
capability that survives the cut list arrives here whole.

## Branch sweep

For each in-scope capability, walk these eight and write down what happens. Most produce one
behavior; some produce none, which is a valid answer once written down.

1. **Happy path** — the capability doing its job for the intended user.
2. **Precondition failures** — each state the capability requires but might not find.
3. **Boundaries** — every `boundary` finding from the ambiguity sweep becomes at least one behavior
   on each side of the line.
4. **Concurrency** — two actors, or an actor and a background job, arriving together.
5. **Partial failure** — the capability half-succeeds. What is the user told, and what is left behind?
6. **Zero, one, many** — the empty case, the singular case, and the case past whatever limit exists.
7. **Permission denied** — the wrong actor, or the right actor on the wrong object.
8. **Reversal** — undo, retry, and repeat. Doing it twice must be defined even when it is refused.

## Write each behavior

Use the `BH-###` format in `templates/behavior-spec.md`. Three rules decide whether a behavior is
usable:

- **Given/When/Then must be constructible.** A test author has to be able to build the Given state
  and trigger the When without asking a question. "Given a user in a bad state" fails this.
- **Observable must name signals, not feelings.** Field values, rows, response codes, on-screen
  copy. "Then the experience feels responsive" is a design principle, not a behavior — it belongs
  in the Design Contract.
- **Source must cite an `AM-###` or `D-###`.** A behavior with no source is a guess, and the
  validator rejects it. If a behavior came straight from the happy path with nothing ambiguous
  about it, it still needs the decision that put the capability in scope.

## Assign a level

`unit` for logic with no collaborators. `integration` for anything crossing a boundary — a store, a
queue, an external call, a screen and its model. `e2e` for the one or two behaviors that prove the
critical path end to end. `manual` when automation costs more than the behavior is worth; a manual
behavior must still name the click-through path in `Observable`.

Prefer the cheapest level that can actually fail when the behavior is wrong. A `unit` test standing
in for an `integration` behavior is a tautological test — it cannot fail when the real thing breaks.

## Status and coverage

Only `Status: active` behaviors require a covering test. Use `planned` for behaviors deliberately
scheduled after this slice, `deferred` for ones parked with an assumption, `out_of_scope` for cases
the product refuses to handle, and `retired` for behaviors a later decision removed — retire them
rather than deleting them, so the test that still asserts them can be found and removed too.

## Handoff

Behaviors feed three places. Vertical slices in the MVP Build Plan are cut along them, the
Implementation Brief's acceptance criteria each cite one, and the implementing agent names the
`BH-###` in every test it writes. That last link is what makes an orphan test — a test asserting
something no behavior asks for — mechanically findable later by `product-recheck`.

## Prototype short form

Three to seven behaviors covering the one flow: the happy path, the one precondition failure that
would embarrass the demo, and whatever the validation question actually turns on. Skip concurrency,
partial failure, and permissions unless the idea being validated is about them.
See `references/prototype-mode.md`.
