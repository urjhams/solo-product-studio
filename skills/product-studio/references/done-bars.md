# Phase done bars

## Prototype

Replaces the Product, Research, Design, Specification, and MVP bars in Prototype mode: the one flow runs end to end on the target device, 3–7 behaviors cover the one flow, the user-confirmed mock boundary is explicit, the cut list is written down, the validation question is stated and answerable by using the prototype, and every faked assumption is recorded as `A-###`. Independent review is not required. See `references/prototype-mode.md`.

## Product

Target user, specific problem, narrow wedge, promise, critical assumptions, risks, and next experiment are explicit.

## Research

Sources and dates are recorded where available, facts are separated from inference, unknowns are labeled, and every critical assumption has a validation test.

## Design

Promise, hero moment, primary flow, screen/state scope, exactly three actionable design principles, accessibility requirements, and cut list are defined.

## Specification

Every in-scope capability has behaviors; every behavior has a constructible Given/When/Then, an observable signal, a test level, and a source; every requirement sentence has been swept against all ten ambiguity classes; zero ambiguities remain `open`; every `resolved` ambiguity cites a `D-###` and every `deferred` one cites an `A-###` with a revisit trigger; the `docs/agent/BEHAVIORS.md` mirror is byte-identical; `scripts/validate_behavior_spec.py` passes.

In Prototype mode this bar is relaxed, not skipped: 3–7 behaviors for the one flow, the `term`/`boundary`/`visibility` classes only, and open ambiguities warn instead of blocking. See `references/prototype-mode.md`.

## MVP

The core flow is executable, vertical slices are user-visible and cut along behaviors, mock/real boundaries are explicit, cut triggers are defined, every `active` behavior is assigned to a slice, and the demo/definition of done is measurable.

## Review

An independent review has challenged the artifact, findings are recorded, fixes were attempted, debt is classified, and Continue/Pivot/Stop is evidence-linked.

## Production

Validated core, architecture boundaries, data and API contracts, security/privacy, observability, migration, release stages, dependencies, risks, and definition of done are explicit.
