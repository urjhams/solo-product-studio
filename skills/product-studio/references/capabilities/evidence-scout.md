# evidence-scout

Purpose: investigate major assumptions without confusing evidence, inference, or vendor claims.

This runs *inside* the Define phase as the producer of the `proof` slot's records, not as a phase of
its own. Research that settles a slot goes into that slot; research about an assumption goes into the
Evidence Pack, and the `proof` slot cites it. See `references/define-loop.md`.

Inputs: Product Opportunity Brief, assumptions, mode, available research tools.

Outputs: Evidence Pack with one record per assumption: ID, statement, category, evidence for/against, source quality, confidence, access/publication date, unknowns, recommended test.

Gate: evidence is cited where available, uncertainty is explicit, and every critical assumption has a next test. If tools are unavailable, produce a research plan instead.

## Market probe mode

A bounded pre-mode variant used to resolve the Indie App versus Startup fork before a mode is recommended. Same evidence discipline and source-quality labeling, limited to three questions — alternatives and their pricing, evidence of monetized pain, and market shape — with roughly three sources each and one round. Produces a short probe note rather than a full Evidence Pack, and hands off to the mode recommendation. See `references/market-probe.md`.

Handoff: `product-to-pixels` (via `references/design-loop.md`) or `mvp-forge` based on stage.
