# Idea validation

A mandatory sense-check and brainstorm loop for a raw idea, run before intent extraction so the
question loop, the mode, and Product Lens all build on an idea that has already met evidence
rather than one taken on the user's framing alone.

## When to run it

Run it immediately after capturing the raw idea (`SKILL.md` step 2), before the hypothesis and
question loop in `references/qa-session.md`. Mandatory for the `Rough idea` and
`Prototype / idea validation` situations in Stage Routing — i.e. whenever the user brought a raw
or vague idea and nothing else.

Skip it when the user already brought grounding that makes a sense-check redundant: existing
research, an existing UX/UI, an existing repository or MVP, a production need, or a
`/product-recheck` session. Those situations already start from evidence; running this against
them would re-litigate a call the user has already made.

## Research pass

Bounded, same discipline as `references/market-probe.md`: roughly three sources per question, one
round per pass, sources cited with access dates, facts kept separate from inference. State the
bound in the output.

1. **Does the problem exist?** Evidence the pain is real, not assumed — complaints, workarounds,
   job posts, forum threads, existing paid attempts. Prefer facts over opinion.
2. **Who else solves it?** Direct and indirect alternatives and what they charge. Use
   `workflows/competitor-review-research.md`.
3. **What shape is the niche?** A narrow, reachable audience the idea already fits, or something
   broad enough that it needs narrowing before it is buildable. Reuses the market-shape question
   from `references/market-probe.md`, one level earlier — at the idea, not the mode fork.

If there is no web tool, or the adapter fails: state a **provisional** verdict with labeled low
confidence, record the gap as `A-###`, and emit a research plan. Never claim a source was
consulted when it was not — same rule as the market probe.

## Verdict

State one of, with the evidence behind it:

- **Holds** — the problem is evidenced, a reachable niche exists, differentiation is plausible.
- **Needs narrowing** — the problem is real but the target/niche/scope is too broad to act on.
- **Weak evidence** — little or no sign anyone experiences or pays for this pain.
- **Saturated** — well-served already; needs a genuine differentiation angle to be worth building.

## Mandatory checkpoint

Present the verdict, the cited findings, and the niche/scope options considered. Then require an
explicit choice — do not proceed on anything less. This reuses `references/qa-session.md`'s
confirmation rule verbatim: *"whatever you think"*, *"sounds good"*, *"sure, let's go"*, and
silence are deferrals, not agreement, and each is a signal that something in the verdict needs
re-checking rather than a yes.

- **Continue** — proceed to intent extraction with this idea and these findings.
- **Refine** — enter the refine loop below.

## Refine loop

One targeted question at a time, same `GUESS:` pattern as `references/qa-session.md`, aimed at
narrowing the niche, reshaping scope, or changing the angle the idea approaches the problem from.
After each answer, re-run the bounded research pass against the reshaped idea and re-present the
checkpoint.

No fixed round cap — the user may keep refining as long as they choose to. Each round stays
bounded the same way a single market-probe pass is; state the running round count in the output so
a long loop stays visible rather than silently expanding.

The loop only ends on an explicit **continue**.

## Handoff

Carry the confirmed/refined idea statement, the verdict, and the cited findings forward:

- Into `references/qa-session.md`'s intent extraction — the hypothesis is built from the
  validated idea, not the original raw one.
- Into `references/capabilities/product-lens.md` — Product Lens populates the Product Opportunity
  Brief's `## Validation` section from this output instead of re-deriving alternatives and wedge
  from scratch.
- Into `references/prototype-mode.md`'s Research rule and `references/market-probe.md`'s
  Alternatives question, both of which reuse these findings instead of re-running the same
  research.

Record `verdict`, `rounds`, and `confidence` under a `validation:` block in
`.product-studio/project.json`.
