# Phase done bars

## Prototype

Replaces the Define, Design, Specification, and MVP bars in Prototype mode: the one flow runs end to end on the target device, 3–7 behaviors cover the one flow, the user-confirmed mock boundary is explicit, the cut list is written down, the validation question is stated and answerable by using the prototype, and every faked assumption is recorded as `A-###`. Independent review is not required. See `references/prototype-mode.md`.

## Hackathon

Replaces the Define, Design, Specification, and MVP bars in Hackathon mode: the hero
moment lands on the target device from a cold start, the demo script is written and has been
rehearsed end to end at least once, the fallback for the real integration exists and has been
rehearsed, fixtures are seeded and work with no network, the one automated high-signal check
passes, and the mock boundary and cut list are written down. Independent review is not required.
See `references/hackathon-mode.md`.

## Define

All six slots are filled — `customer`, `pain`, `outcome`, `mechanism`, `pricing`, `proof` — where filled means an answer, a confidence number, and either a cited source with its access date or an `A-###` saying it has none. Specifically: the customer is named narrowly enough that one can be reached; the pain carries frequency and cost; the outcome is measurable; the mechanism is specific, causal, and falsifiable, with the observation that would disprove it recorded; the pricing carries a number and what alternatives charge; the proof separates fact from inference, labels unknowns, gives every critical assumption a next test, and states the strongest evidence *against* the definition. Wedge, promise, and the risk/next-experiment lines follow from the six.

Wherever the compiled profile sets `define.gate: required`, `workflow_runner.checkpoint` blocks with `define-slot-missing:<slots>` until every slot is non-empty. Prototype and Hackathon compile to `advisory` — a demo is not asked to price itself — but a skipped slot is still `deferred` with an `A-###` and a revisit trigger, never blank. See `references/define-loop.md`.

## Design

Promise, magic moment (the hero moment), primary flow, screen/state scope, exactly three actionable design principles, accessibility requirements, and cut list are defined.

Four more, from `references/design-loop.md`: the magic moment is reachable from a cold start inside the onboarding path and is attributable to the product; the onboarding path is written step by step with what each step costs and earns; the landing/store copy is written with every line traceable to a Define slot; the design system covers type, spacing, color roles, and the component inventory the screen list actually uses. The Design Prompt is written to `.product-studio/artifacts/design-prompt.md` whether or not a canvas provider exists.

Prototype and Hackathon cut the landing/store slot and the full design system by default — record the cut, do not skip it silently.

When the compiled profile sets `design.gate: evidence_required` — which `risk_tier: high` derives automatically — a complete artifact is not enough. The critical interaction needs evidence that a person can understand it: a clickable prototype, a published design canvas the user has actually responded to, or a short usability check with two or three people. Record what was run in `design.evidence`; `workflow_runner.py` blocks the design checkpoint with `design-evidence-missing` until it is there. Use this when navigation, comprehension, trust, accessibility, or a novel interaction is the main product risk — not for routine CRUD, and not in Hackathon unless the demo itself turns on the interaction.

## Specification

Every in-scope capability has behaviors; every behavior has a constructible Given/When/Then, an observable signal, a test level, and a source; every requirement sentence has been swept against all ten ambiguity classes; zero ambiguities remain `open`; every `resolved` ambiguity cites a `D-###` and every `deferred` one cites an `A-###` with a revisit trigger; the `docs/agent/BEHAVIORS.md` mirror is byte-identical; `scripts/validate_behavior_spec.py` passes.

Relaxed, not skipped, wherever the compiled profile sets `planning.spec_gate: warn` — Prototype and Hackathon. Prototype: 3–7 behaviors for the one flow, the `term`/`boundary`/`visibility` classes only. Hackathon: 5–9 behaviors, those three classes plus `failure`. In both, open ambiguities warn instead of blocking. See `references/prototype-mode.md` and `references/hackathon-mode.md`.

## MVP

The core flow is executable, vertical slices are user-visible and cut along behaviors, mock/real boundaries are explicit, cut triggers are defined, every `active` behavior is assigned to a slice, and the demo/definition of done is measurable.

## Review

An independent review has challenged the artifact, findings are recorded, fixes were attempted, debt is classified, and Continue/Pivot/Stop is evidence-linked.

## Production

Validated core, architecture boundaries, data and API contracts, security/privacy, observability, migration, release stages, dependencies, risks, and definition of done are explicit.
