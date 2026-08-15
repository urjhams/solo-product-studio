# idea-validator

Purpose: sense-check a raw idea against real-world evidence and, with the user, refine it until it
is sound enough to hand to Product Lens.

Inputs: raw idea text, available web tool.

Outputs: sense-check verdict (holds / needs narrowing / weak evidence / saturated), cited facts,
niche/scope options considered, confirmed/refined idea statement, round count.

Gate: verdict is stated with cited evidence or an explicit low-confidence fallback; the refine
loop only exits on explicit user confirmation to continue.

Handoff: `product-lens`, carrying the validated idea and cited findings forward. See
`references/idea-validation.md` for the full protocol.
