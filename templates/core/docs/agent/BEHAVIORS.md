# Behaviors
<!-- behavior-spec/v1 -->

What **{{PROJECT_NAME}}** must do, one `BH-###` per branch of behavior, plus the register of
ambiguities that were found and how each was settled. Tests name the `BH-###` they prove; that is
what makes an uncovered behavior and an orphan test both findable. Sweep procedure and the ten
ambiguity classes: `RUNBOOKS.md#specify`.

Only `Status: active` behaviors need a covering test — the PR hook enforces that. Only
`Status: open` ambiguities block.

If this project also uses the `product-studio` skill, that skill owns this file: it writes the
canonical copy to `.product-studio/artifacts/behavior-spec.md` and mirrors it here byte for byte.
Do not hand-edit one side of a mirrored pair. The `behavior-spec/v1` marker on line 2 is the shared
format contract between the two; readers fail loudly on a version they do not know.

<!--
## BH-001 — cancel succeeds before packing
- Status: active            # active | planned | deferred | out_of_scope | retired
- Priority: core            # core | edge | error
- Level: integration        # unit | integration | e2e | manual
- Given: an order in state `paid`, not yet `packed`
- When: the customer requests cancellation
- Then: the order moves to `cancelled`, a refund job is enqueued, and the customer sees
  "Cancelled — refund in 5–10 days"
- Observable: `order.status`, a refund job row, the confirmation banner copy
- Source: AM-003, D-007
-->

## Ambiguity register

<!--
### AM-003 — what counts as "shipment"
- Class: boundary           # term | boundary | actor | state | timing | failure | identity | quantity | visibility | reversibility
- In requirement: "Users can cancel an order before shipment."
- Reading A: shipment = the carrier scans the parcel. The cancel window closes late.
- Reading B: shipment = the warehouse marks the order packed. The cancel window closes early.
- User-visible difference: a customer cancelling twenty minutes after packing succeeds under A;
  under B they are told the order already shipped.
- Decision needed: which order state closes the cancel window.
- Recommendation: B — it is the state the warehouse can actually enforce. Confidence: medium
- Status: resolved -> D-007 # open | resolved -> D-### | deferred -> A-### (+ Revisit when:) | out_of_scope
- Behaviors: BH-001, BH-002
-->
