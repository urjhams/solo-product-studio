# Spec hardening — attack the specification

Run this after behavior discovery and before the MVP Build Plan. Its premise: **assume the
specification is incomplete.** A test suite written over a misread requirement is green and
worthless, so the misread has to be caught here, not in review.

You are not looking for missing features. You are looking for sentences that two competent
implementers would build differently.

## Sweep

Take every requirement sentence in the Design Contract, the product definition, and the user's own
words. Pass each one against all ten classes below, then stop. The sweep is bounded — it ends when
the classes are exhausted, not when the agent feels done.

| Class | The question it asks |
|---|---|
| `term` | Does a noun or verb here have more than one referent? ("shipment", "cancel", "active user") |
| `boundary` | When exactly does the state change? Inclusive or exclusive, before/at/after |
| `actor` | Who may do this, on whose behalf, and who may not? |
| `state` | Which states exist, and which transitions between them are legal? |
| `timing` | What happens on simultaneous requests, races, retries, reordering, repeats? |
| `failure` | What if half of it succeeds? Roll back or compensate? Synchronous or asynchronous? |
| `identity` | What makes two of these the same thing? What is persisted versus derived? |
| `quantity` | How many, how fast, how large? What are the zero, one, and many cases? |
| `visibility` | Who sees this, when, and what exactly are they told? |
| `reversibility` | Money, email, external calls — can this be undone, and by whom? |

A class that yields nothing is a pass, not a failure. Most requirements produce two to five real
ambiguities; a sentence producing twelve is usually several requirements wearing one coat.

## Record

Every finding becomes one `AM-###` in the Behavior Spec, in the format defined by
`templates/behavior-spec.md`. Four fields carry the weight:

- **Two readings.** Both must be reasonable. If reading B is a strawman, this is not an ambiguity —
  it is you explaining your own preference, and the record is noise.
- **User-visible difference.** State a concrete case where a real person sees a different result
  under A than under B. If you cannot, the ambiguity does not matter and you should drop it. This
  field is the filter that keeps the register from becoming a pedantry log.
- **Decision needed.** What must be settled before implementation, phrased so someone can answer it.
- **Recommendation and confidence.** Always give one. An ambiguity presented without a
  recommendation pushes work back onto the user that you were able to do.

## Resolve

Every ambiguity terminates in exactly one of four states. `open` is not a resting place.

- `resolved -> D-###` — a decision was made. Record it through `workflows/decision-log-manager.md`.
- `deferred -> A-###` — the answer is not needed for this release. Record the assumption and a
  `Revisit when:` trigger naming an observable signal, not a date.
- `out_of_scope` — the case is real but the product will not handle it. The behavior that says so
  is still worth writing, so the refusal is deliberate rather than accidental.
- `open` — **blocks the Implementation Brief.** Outside Prototype mode,
  `scripts/validate_behavior_spec.py` exits non-zero and `workflow_runner.py` refuses the `specify`
  checkpoint with `ambiguities-open`.

## Escalate

Resolve what you can from the product definition, the house rules, and prior decisions. Everything
left is a user question. Ask them in the order `references/qa-session.md` ranks — impact,
irreversibility, rework risk, inferability — one at a time, each with numbered readings and your
recommended pick. Do not batch ten ambiguities into one message; do not ask about an ambiguity whose
answer you can infer from a recorded decision.

An ambiguity the user declines to settle becomes `deferred`, never `open`.

## Second pass

After the register is closed, re-read the behaviors with the resolutions applied. Resolving one
ambiguity routinely exposes another — deciding that packing closes the cancel window (a `boundary`
finding) is what makes the concurrent pack-and-cancel case (a `timing` finding) visible. Repeat the
sweep until a pass produces nothing new, then stop.

## Prototype short form

In Prototype mode the sweep is timeboxed to ten minutes and only the classes that change what the
user can judge — `term`, `boundary`, `visibility` — are required. Ambiguities may remain `deferred`
without a revisit trigger. Run the validator with `--prototype`. Do not skip the step entirely: a
prototype that validates the wrong reading of the idea has answered nothing.
See `references/prototype-mode.md`.
