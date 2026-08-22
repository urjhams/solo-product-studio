# product-lens

Purpose: turn a validated idea into a narrow, testable Product Opportunity Brief by filling the six
Define slots.

Inputs: user context, the idea-validation verdict and its cited findings, stage, mode, platform,
constraints.

Outputs: the six slots — `customer`, `pain`, `outcome`, `mechanism`, `pricing`, `proof` — each with
an answer, a confidence number, and a citation or an `A-###`; then wedge, promise, alternatives,
differentiation/retention/distribution hypotheses, platform surface hypothesis, assumptions, risks,
and next experiment, all derived from the six rather than asserted alongside them.

Gate: every slot filled per `references/done-bars.md` `## Define`, and — wherever the compiled
profile sets `define.gate: required` — non-empty in `define.slots`, which
`workflow_runner.checkpoint` enforces.

Procedure: `references/define-loop.md`. Run the per-slot question/research/confidence loop rather
than drafting the brief in one pass; the brief is what the loop writes down, not a substitute for it.

Handoff: `product-to-pixels` via `references/design-loop.md`. Carry `outcome` to the Landing
headline, `mechanism` to the Landing subhead and the magic moment, and `proof` to the three Landing
proof points.

When `idea-validator` ran, populate the Product Opportunity Brief's `## Validation` section from its
verdict and cited findings instead of re-deriving alternatives and wedge from scratch.
