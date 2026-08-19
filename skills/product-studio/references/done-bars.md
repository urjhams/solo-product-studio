# Phase done bars

## Prototype

Replaces the Product, Research, Design, Specification, and MVP bars in Prototype mode: the one flow runs end to end on the target device, 3–7 behaviors cover the one flow, the user-confirmed mock boundary is explicit, the cut list is written down, the validation question is stated and answerable by using the prototype, and every faked assumption is recorded as `A-###`. Independent review is not required. See `references/prototype-mode.md`.

## Hackathon

Replaces the Product, Research, Design, Specification, and MVP bars in Hackathon mode: the hero
moment lands on the target device from a cold start, the demo script is written and has been
rehearsed end to end at least once, the fallback for the real integration exists and has been
rehearsed, fixtures are seeded and work with no network, the one automated high-signal check
passes, and the mock boundary and cut list are written down. Independent review is not required.
See `references/hackathon-mode.md`.

## Product

Target user, specific problem, narrow wedge, promise, critical assumptions, risks, and next experiment are explicit.

## Research

Sources and dates are recorded where available, facts are separated from inference, unknowns are labeled, and every critical assumption has a validation test.

## Design

Promise, hero moment, primary flow, screen/state scope, exactly three actionable design principles, accessibility requirements, and cut list are defined.

When the compiled profile sets `design.gate: evidence_required` — which `risk_tier: high` derives automatically — a complete artifact is not enough. The critical interaction needs evidence that a person can understand it: a clickable prototype, or a short usability check with two or three people. Record what was run in `design.evidence`; `workflow_runner.py` blocks the design checkpoint with `design-evidence-missing` until it is there. Use this when navigation, comprehension, trust, accessibility, or a novel interaction is the main product risk — not for routine CRUD, and not in Hackathon unless the demo itself turns on the interaction.

## Specification

Every in-scope capability has behaviors; every behavior has a constructible Given/When/Then, an observable signal, a test level, and a source; every requirement sentence has been swept against all ten ambiguity classes; zero ambiguities remain `open`; every `resolved` ambiguity cites a `D-###` and every `deferred` one cites an `A-###` with a revisit trigger; the `docs/agent/BEHAVIORS.md` mirror is byte-identical; `scripts/validate_behavior_spec.py` passes.

Relaxed, not skipped, wherever the compiled profile sets `planning.spec_gate: warn` — Prototype and Hackathon. Prototype: 3–7 behaviors for the one flow, the `term`/`boundary`/`visibility` classes only. Hackathon: 5–9 behaviors, those three classes plus `failure`. In both, open ambiguities warn instead of blocking. See `references/prototype-mode.md` and `references/hackathon-mode.md`.

## MVP

The core flow is executable, vertical slices are user-visible and cut along behaviors, mock/real boundaries are explicit, cut triggers are defined, every `active` behavior is assigned to a slice, and the demo/definition of done is measurable.

## Review

An independent review has challenged the artifact, findings are recorded, fixes were attempted, debt is classified, and Continue/Pivot/Stop is evidence-linked.

## Production

Validated core, architecture boundaries, data and API contracts, security/privacy, observability, migration, release stages, dependencies, risks, and definition of done are explicit.
