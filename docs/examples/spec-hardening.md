# Behaviors
<!-- behavior-spec/v1 -->

Worked example. One requirement — "Users can cancel an order before shipment." — taken through the
ambiguity sweep in `references/spec-hardening.md` and the branch sweep in
`references/behavior-discovery.md`. This file is the fixture
`scripts/validate_behavior_spec.py` is tested against.

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

## BH-016 — Packing wins a concurrent cancel
- Status: active
- Priority: edge
- Level: integration
- Given: an order in state `paid` and a warehouse pack request arriving in the same moment as a customer cancel request
- When: both are processed
- Then: exactly one succeeds; the order ends in `packed` or `cancelled` and never in both, and at most one refund job exists
- Observable: final `order.status`, refund job count, the message each caller received
- Source: AM-005, D-008

## BH-017 — Repeated cancel is idempotent
- Status: active
- Priority: edge
- Level: unit
- Given: an order already in state `cancelled`
- When: the customer requests cancellation again
- Then: the order is unchanged, no second refund job is created, and the customer sees the same cancellation confirmation
- Observable: refund job count stays at one, `order.status` stays `cancelled`
- Source: AM-005, D-008

## BH-018 — Refund failure does not un-cancel the order
- Status: active
- Priority: error
- Level: integration
- Given: an order that has just moved to `cancelled` and a payment provider that rejects the refund
- When: the refund job runs and fails
- Then: the order stays `cancelled`, the refund is marked `failed` for operator follow-up, and the customer sees "Cancelled — refund delayed, we are on it"
- Observable: `order.status` stays `cancelled`, refund row status `failed`, the delayed-refund copy
- Source: AM-006, D-009

## BH-019 — Only the ordering customer or an operator may cancel
- Status: active
- Priority: error
- Level: integration
- Given: an order belonging to another customer
- When: a signed-in customer requests its cancellation
- Then: the request is refused with a not-found response and the order is unchanged
- Observable: response status, `order.status` unchanged, no refund job
- Source: AM-004, D-010

## BH-020 — Partial cancellation of a multi-item order
- Status: out_of_scope
- Priority: edge
- Level: integration
- Given: an order containing several items, some packed and some not
- When: the customer asks to cancel only the unpacked items
- Then: not supported in this release; the customer is offered whole-order cancellation or a return
- Observable: the offered options
- Source: AM-007

## Ambiguity register

### AM-003 — what counts as "shipment"
- Class: boundary
- In requirement: "Users can cancel an order before shipment."
- Reading A: shipment means the carrier scans the parcel. The cancel window stays open through packing.
- Reading B: shipment means the warehouse marks the order packed. The cancel window closes earlier.
- User-visible difference: a customer cancelling twenty minutes after packing succeeds under A; under B the same customer is told the order already shipped.
- Decision needed: which order state closes the cancel window.
- Recommendation: B — it is the state the warehouse can actually enforce, and a cancellation accepted after packing has to be physically intercepted. Confidence: medium
- Status: resolved -> D-007
- Behaviors: BH-014, BH-015

### AM-004 — who is "users"
- Class: actor
- In requirement: "Users can cancel an order before shipment."
- Reading A: any signed-in user, including support operators acting on a customer's behalf.
- Reading B: only the customer who placed the order.
- User-visible difference: under B a support agent cannot cancel for a customer on the phone and has to ask them to do it themselves.
- Decision needed: whether operator-initiated cancellation ships in this release.
- Recommendation: B for customers plus an explicit operator role — support needs it on day one and bolting the role on later means reworking the audit trail. Confidence: high
- Status: resolved -> D-010
- Behaviors: BH-019

### AM-005 — cancel and pack arriving together
- Class: timing
- In requirement: "Users can cancel an order before shipment."
- Reading A: last write wins; whichever request commits second overwrites the order state.
- Reading B: the transition is guarded; the first to commit wins and the second is refused with the current state.
- User-visible difference: under A a customer can see "Cancelled" while the warehouse sees "Packed" and the parcel still goes out.
- Decision needed: whether the cancel and pack transitions take a lock on the order row.
- Recommendation: B — the requirement is about preventing a shipment, so an unguarded transition defeats the feature. Confidence: high
- Status: resolved -> D-008
- Behaviors: BH-016, BH-017

### AM-006 — refund timing when payment is already captured
- Class: failure
- In requirement: "Users can cancel an order before shipment."
- Reading A: the refund is issued synchronously and cancellation fails if the refund fails.
- Reading B: cancellation commits immediately and the refund is enqueued; a failed refund becomes operator work.
- User-visible difference: under A a payment-provider outage means the customer cannot cancel at all and the parcel ships; under B the order is cancelled and the customer is told the refund is delayed.
- Decision needed: whether refund success is a precondition of cancellation.
- Recommendation: B — stopping the shipment is the urgent half and it must not depend on a third party being up. Confidence: high
- Status: resolved -> D-009
- Behaviors: BH-018

### AM-007 — whole order or individual items
- Class: quantity
- In requirement: "Users can cancel an order before shipment."
- Reading A: cancellation applies to the whole order only.
- Reading B: a customer may cancel individual items while the rest ships.
- User-visible difference: under B a customer with one backordered item can drop it and keep the rest; under A they must cancel everything and reorder.
- Decision needed: whether the release supports partial cancellation.
- Recommendation: A for this release — partial cancellation changes pricing, promotions, and shipping-cost recalculation, which is a larger piece of work than the cancel window itself. Confidence: medium
- Status: deferred -> A-021
- Revisit when: support sees partial-cancel requests in more than one in twenty cancellation contacts
- Behaviors: BH-020

### AM-008 — what the customer is told about refund timing
- Class: visibility
- In requirement: "Users can cancel an order before shipment."
- Reading A: the confirmation names a specific window ("5–10 days").
- Reading B: the confirmation says only that a refund is coming.
- User-visible difference: a named window sets an expectation support is measured against; a vague one generates "where is my money" contacts.
- Decision needed: whether the product commits to a refund window in customer-facing copy.
- Status: out_of_scope
- Behaviors: BH-014
