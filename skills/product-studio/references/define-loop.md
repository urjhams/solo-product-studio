# Define loop

The Define pillar answers six questions, in order, and it answers each one with the user in the
room. It replaces what used to be two phases and two checkpoints — `product` wrote the definition,
`research` went looking for evidence afterwards — which put the evidence downstream of the argument
it was supposed to settle.

Run it after the Idea pillar (`references/idea-validation.md`) has returned an explicit **continue**,
and before the Design pillar.

## The six slots

| Slot | The question it closes | Research |
|---|---|---|
| `customer` | Who exactly, and how is one of them reached? | when narrow-vs-broad is unresolved |
| `pain` | What breaks today, how often, and what does it cost? | always |
| `outcome` | What is different afterwards, measurably? | never — this is the user's call |
| `mechanism` | How does the product produce that outcome? | when feasibility is in doubt |
| `pricing` | What model, what number, and who signs? | always |
| `proof` | What is evidenced, and what is still assumed? | it *is* the research slot |

A slot is **filled** when it has an answer, a confidence number, and either a cited source or an
`A-###` assumption saying it has none. An answer alone is a guess with better formatting.

## Per-slot loop

For each slot, in order:

1. **Guess first.** Same pattern as `references/qa-session.md` — never ask blind:
   ```text
   SLOT: mechanism
   Q: <one focused question>
   GUESS: <what you think the answer is, from the slots already filled>
   ```
2. **Research where the table says so.** Bounded exactly as `references/idea-validation.md` and
   `references/market-probe.md` bound it: roughly three sources for the question, one round, sources
   cited with access dates, facts kept separate from inference. State the bound. Run it in a fresh
   subagent context where the host provides one; record which path was taken. If there is no web
   tool or the adapter fails, record the gap as `A-###`, label the confidence low, and emit a
   research plan. Never claim a source was consulted when it was not.
3. **Record before moving on.** Write the slot into `define.slots.<name>` in
   `.product-studio/project.json`, with its confidence and its citation or `A-###`. Findings that
   are about an assumption rather than a slot go into the Evidence Pack.
4. **Re-open what the answer breaks.** Slots are ordered because each one constrains the next, and a
   late answer routinely invalidates an early one — a pricing number that no one will pay is usually
   a customer problem, not a pricing problem. Go back and say so rather than carrying the
   contradiction forward.

Skip nothing silently. A slot the user declines to answer is `deferred` with an `A-###` and a revisit
trigger, which is visible; an empty slot is not.

## Mechanism

The slot with no prior art in this bundle, and the one that most often turns out to be missing.

Customer, pain, and outcome describe a wish. Mechanism is the sentence that says why the wish comes
true — the specific thing the product does that produces the outcome, stated concretely enough that
someone could disagree with it:

```text
Weak:   "AI-powered insights help teams move faster."
Filled: "We read the team's merged PRs nightly and post one message naming the
         review that blocked longest, so the bottleneck is named before standup
         instead of argued about after it."
```

Three tests, all of which have to pass:

- **Causal** — the mechanism produces the outcome. If you can swap in a competitor's mechanism and
  the sentence still reads fine, it is a category, not a mechanism.
- **Specific** — it names what the product actually does. "Uses AI", "streamlines the workflow", and
  "leverages data" are placeholders.
- **Falsifiable** — you can state the observation that would prove it does not work. Record that
  observation as the mechanism's `A-###` test.

Mechanism is the sentence the Design pillar builds the magic moment from and the Landing subhead
quotes. A vague mechanism produces a vague magic moment, which is where a product stops being
distinguishable from its alternatives.

## Pricing

A number and a source, not a hypothesis. The number may be wrong — that is what the revisit trigger
is for — but "freemium with a pro tier" is a shape, not a price.

Fill: the model (one-off, subscription, usage, free), the number, who signs versus who uses when they
differ, and what two or three alternatives charge with their pricing pages cited. Reuse
`references/market-probe.md`'s alternatives finding when it is fresh rather than re-probing.

Where the compiled profile sets `define.gate: advisory` — Prototype and Hackathon — a demo is not
asked to price itself. State the deferral instead of leaving the slot blank.

## Proof

The audit of the other five. For each of them: what is evidenced, what is inferred, and what is still
assumed. It cites Evidence Pack records rather than re-deriving them; `references/capabilities/evidence-scout.md`
produces those records inside this phase now instead of in a phase of its own.

Proof is filled when every critical assumption carries a next test, uncertainty is labeled, and the
strongest piece of evidence *against* the definition is written down alongside the evidence for it.
A proof section that only argues one direction has not been run.

## Gate

The done bar is in `references/done-bars.md` under `## Define`. Wherever the compiled profile sets
`define.gate: required`, `workflow_runner.checkpoint` blocks the define checkpoint with
`define-slot-missing:<slots>` until every slot is non-empty — the same mechanism as the design
evidence gate, not a new one. `references/workflow-profile.md` carries the per-mode values.

## Handoff

Into `references/capabilities/product-lens.md`, which writes the six slots into the Product
Opportunity Brief, and then into `references/design-loop.md`:

- `outcome` becomes the Landing headline.
- `mechanism` becomes the Landing subhead and the seed of the magic moment.
- `proof` supplies the three Landing proof points.
- `customer` sets the platform surface and the accessibility floor.
