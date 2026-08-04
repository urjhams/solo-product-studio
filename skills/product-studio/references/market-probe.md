# Market probe

A bounded research pass that runs **before** the mode recommendation so the Indie App versus Startup call rests on evidence instead of the user's own framing.

## When to run it

Run it only when the mode choice is genuinely between **Indie App and Startup**, or when monetization intent is unstated. Skip it for Prototype, for Hackathon, for Production, and when the user selects a mode explicitly — there is no fork to resolve.

## Three questions, nothing else

This is a probe, not the Evidence Pack.

1. **Alternatives** — who already solves this, directly and indirectly, and what do they charge? Use `workflows/competitor-review-research.md`.
2. **Monetized pain** — is there evidence someone already pays money, or does painful manual work, for this? Prefer pricing pages, paid alternatives, job posts, and repeated complaints over opinion.
3. **Market shape** — a narrow niche with a reachable direct channel, or an expandable beachhead with a distribution loop?

Bounded: roughly three sources per question, one round, no follow-on research. State the bound in the output.

## Making the call

- **Indie App** — alternatives already charge modest money in a reachable niche, support burden is low, the channel is direct (SEO, community, app store), and the economics work without expansion.
- **Startup** — frequent retained use, an expandable beachhead, a distribution loop, and unit economics that improve with scale.

Never use market size as proof.

Present the recommendation with confidence, the evidence behind it, and what would change it.

## Dispatch

Run the probe in a fresh subagent context when the host provides one, the same mechanism used for independent review. Fall back to running it inline otherwise. Record which was used.

## When research is unavailable

If there is no web tool, or the adapter fails: recommend a **provisional** mode with labeled low confidence, record the gap as `A-###`, and emit a research plan. Never claim a source was consulted when it was not.

## Mode revisit triggers

The chosen mode is a hypothesis. Write its revisit trigger down when it is chosen, then evaluate it against real signals at the MVP review.

**Indie → Startup:**

- Cohort retention flattens instead of decaying — users still active after the fourth period.
- Inbound demand exceeds what one operator can serve: waitlist, referrals, unsolicited requests.
- Users ask for team seats, admin, roles, SSO, or integrations — the wedge is expanding past single-user.
- A repeatable distribution channel appears with improving payback, not one-off launch spikes.
- An adjacent segment wants the same product with small changes.
- Support and ops load now requires headcount; indie margins no longer cover it.

**Stay Indie, or Startup → Indie** — a valid outcome, not a failure state:

- Flat or decaying retention; usage is one-off.
- Growth only from manual pushes.
- The niche has a countable ceiling and no adjacent segment.
- Margins are healthy at low volume with low support load. Indie is the better outcome here, not the consolation prize.

**Switching rule.** Require two or more signals sustained across at least two review cycles, or a named period. A switch is consequential, so it needs explicit user confirmation. Record it as a new `D-###` that **supersedes** the original mode decision, citing the observed signals; never silently rewrite the earlier decision. Market size alone never qualifies.

**A mode switch re-opens the platform decision.** Startup usually means broader surface coverage and faster iteration, which can flip an iOS-first native call toward Expo, or a single-surface call toward mobile and web. Say so at the switch instead of keeping the old track by default. See `references/platform-decision.md`.
