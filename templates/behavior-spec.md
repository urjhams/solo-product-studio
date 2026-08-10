# Behaviors
<!-- behavior-spec/v1 -->

Canonical copy: `.product-studio/artifacts/behavior-spec.md`
Repository mirror: `docs/agent/BEHAVIORS.md` (must be byte-identical)

Validate with `python3 scripts/validate_behavior_spec.py <canonical> --mirror docs/agent/BEHAVIORS.md`.

## BH-001 — <short behavior name>
- Status: active
- Priority: core
- Level: integration
- Given: <starting state, stated so a test can construct it>
- When: <the single triggering action>
- Then: <the state change and what the user is told>
- Observable: <the signals a test asserts on>
- Source: AM-000, D-000

Field values:

- `Status`: `active` | `planned` | `deferred` | `out_of_scope` | `retired`. Only `active` behaviors require a covering test.
- `Priority`: `core` | `edge` | `error`.
- `Level`: `unit` | `integration` | `e2e` | `manual`.
- `Source`: at least one `AM-###` or `D-###`. A behavior with no source is a guess.

## Ambiguity register

### AM-001 — <the question the requirement does not answer>
- Class: term
- In requirement: "<the exact sentence being attacked>"
- Reading A: <first reasonable interpretation>
- Reading B: <second reasonable interpretation>
- User-visible difference: <a concrete case where a real user sees a different result under A than under B>
- Decision needed: <what must be settled before implementation>
- Recommendation: <A or B, and why> Confidence: low | medium | high
- Status: open
- Behaviors: BH-001

Field values:

- `Class`: one of the ten sweep classes in `references/spec-hardening.md` — `term`, `boundary`, `actor`, `state`, `timing`, `failure`, `identity`, `quantity`, `visibility`, `reversibility`.
- `Status`: `open` | `resolved -> D-###` | `deferred -> A-###` | `out_of_scope`.
  An ambiguity left `open` blocks the Implementation Brief outside Prototype mode.
- `deferred` also requires a revisit trigger on the line: `Revisit when: <observable signal>`.

---

## Worked example

## BH-014 — Cancel succeeds before packing
- Status: active
- Priority: core
- Level: integration
- Given: an order in state `paid` that has not reached `packed`
- When: the customer requests cancellation
- Then: the order moves to `cancelled`, a refund job is enqueued, and the customer sees "Cancelled — refund in 5–10 days"
- Observable: `order.status`, a refund job row for the order, the confirmation banner copy
- Source: AM-003, D-007

## BH-015 — Cancel is refused once packed
- Status: active
- Priority: error
- Level: integration
- Given: an order in state `packed` or later
- When: the customer requests cancellation
- Then: the order is unchanged and the customer sees "Already shipped — start a return instead" with a link to returns
- Observable: `order.status` unchanged, no refund job created, the refusal copy and the returns link
- Source: AM-003, D-007

### AM-003 — what counts as "shipment"
- Class: boundary
- In requirement: "Users can cancel an order before shipment."
- Reading A: shipment means the carrier scans the parcel. The cancel window stays open through packing.
- Reading B: shipment means the warehouse marks the order packed. The cancel window closes earlier.
- User-visible difference: a customer cancelling twenty minutes after packing succeeds under A; under B the same customer is told the order already shipped.
- Decision needed: which state closes the cancel window.
- Recommendation: B — it is the state the warehouse can actually enforce, and a cancellation accepted after packing has to be physically intercepted. Confidence: medium
- Status: resolved -> D-007
- Behaviors: BH-014, BH-015
