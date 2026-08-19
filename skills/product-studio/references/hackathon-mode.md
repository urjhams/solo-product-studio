# Hackathon mode

The fastest path from an idea to a demo that lands with a judging audience at a fixed deadline. The deliverable is a **performance**, not a product and not a verdict on the idea — the event already chose the problem.

Aliases the user may say: hackathon, demo day, jam, sprint build, "we're pitching Saturday", "I have four hours and judges".

Read this before running any Hackathon phase. It overrides the default scope, mock, research, specification, testing, and done-bar rules.

## What it optimizes

Legibility of one hero moment to an audience under time pressure, and the demo's survivability on the day. Not maintainability, not the edges, not extensibility, and not whether the idea holds — that is Prototype's question, and confusing the two produces a build that answers neither.

## Prototype versus Hackathon

Both are fast and mock-first, and their compiled profiles are nearly identical. The difference that matters is who the build has to convince. Prototype convinces the user; a rough edge they can see past costs nothing. Hackathon convinces a room once, on someone else's schedule, with no second take — so demo reliability is a correctness requirement here and an afterthought there.

## Scope rule

One flow, **plus the demo path**. The app must open in a demoable state: seeded fixtures already loaded, and a way to reset to that state between runs. A demo that needs ninety seconds of setup taps before the hero moment has spent its best ninety seconds.

Cut by default, without asking — the Prototype list (`references/prototype-mode.md`), plus onboarding and settings.

Keep, always — not cuttable even here:

- fixtures that work with no network; venue wifi is the most reliable failure mode at any event
- a fallback for the one live integration: a recorded clip, a canned response, or a cached last-good result
- secrets out of the repository, even throwaway keys
- input validation anywhere bad input crashes the demo path

## Mock rule

Mock everything except the single integration that *is* the wow. Never fetch live on stage — pre-seed and cache, then let the demo read the cache.

Fixture data must be plausible but visibly fake. A screenshot of the demo will outlive the demo, and fake data that reads as real is how a demo gets mistaken for evidence. Record the confirmed boundary as `D-###` and each faked assumption as `A-###`.

## Direction rule

`references/platform-decision.md` already carries the Hackathon override — minutes to a running app on the demo device, counting setup. Do not restate it here.

One inversion over Prototype: **the toolchain the team already has running outranks the objectively fastest one.** A hackathon is usually more than one person, and setup cost is paid per head.

## Research rule

Skip it. No idea validation, no market probe. The event chose the problem, and hours spent confirming it are hours not spent on the thing being judged.

## Specify rule

Short form, timeboxed to ten minutes. Skipping it is not an option — a demo built on a misread of the brief loses to one that read it.

- 5–9 behaviors: the hero moment, the happy path into it, and the two failures that would break the demo in front of people — empty state, and the live integration being unreachable.
- Sweep `term`, `boundary`, `visibility`, **and `failure`**. The extra class over Prototype is the point: on stage, a failure is the risk.
- Ambiguities may stay `deferred` without a revisit trigger. Nothing blocks.
- Run `scripts/validate_behavior_spec.py <spec> --mode hackathon`; open ambiguities warn, and the behavior count is capped at 9.

## Plan rule

- The one flow, its screens, and their order.
- The riskiest real integration goes in the first spike — if it cannot be made to work, the demo has to change while there is still time to change it.
- The remaining time split into visible checkpoints, 30–60 minutes each, every one ending in something that runs.
- The seeded fixture data.
- A cut trigger per checkpoint.
- The explicit list of what was cut.

No speculative abstraction, no migration framework, no generalized configuration, no refactor phase. Git is a recovery mechanism; a pull request is optional unless the team's own workflow needs one.

## Demo rule

Write the demo script before the last checkpoint, not during it:

- the exact taps, in order, and the narration beat at each one
- who drives, and what they say if a step hangs
- the fallback if the live integration fails, and the tap that reaches it
- the time budget, and which step gets dropped first if the clock runs out
- a recording or screenshots of a working run, captured while it works

## Testing rule

One automated high-signal check, plus rehearsal. The check is chosen by **where the demo actually fails**, not by test-pyramid habit:

- consequential pure logic decides the outcome — a scoring rule, a matcher, a money or date calculation → one unit test
- the real integration *is* the hero moment → one integration smoke test against it

A mocked unit test wrapped around the hero integration proves nothing about the moment being judged, which is the whole reason this rule is not simply "one unit test".

Then, manually: run the full demo script end to end on the demo device at least once, and rehearse the fallback once. Both count as verification and both go in the brief with `Level: manual`.

Not required: coverage target, broad unit suite, E2E suite, snapshots, CI, independent review, or a performance program — unless the judging rubric explicitly asks for one.

## Done bar

- The hero moment lands on the target device from a cold start.
- The demo script is written and has been rehearsed end to end at least once.
- The fallback for the real integration exists and has been rehearsed.
- Fixtures are seeded and work with no network.
- The one automated check passes.
- Mock boundary and cut list are written down.

Not required: independent review, exhaustive states, production readiness of any kind.

## Final planning

Run `references/final-planning.md` in its short form. All six brief sections are still required, but Verification is the demo script plus the one automated check, and the review may end as `self_review_only` without blocking handoff. Note in the brief that the output is a demo artifact and must not be extended into a product without re-running mode selection.

## Exit

After the event, ask what the demo showed and offer: throw it away, run mode selection again now that the reaction is known, or keep it as a reference while rebuilding properly. Hackathon is not a mode a product stays in — `revisit_when` is *the event is over*.
