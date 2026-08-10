# Prototype mode

The fastest path from an idea to something a person can click. The deliverable is a judgement about the idea, not a product. Everything that does not change that judgement is cut.

Aliases the user may say: prototype, proof of concept, quick MVP, fast MVP, throwaway build, "just want to see it", "validate the idea first".

## What it optimizes

Time to a runnable prototype that carries the idea, and nothing after that. Not maintainability, not correctness at the edges, not extensibility. The code is expected to be thrown away or rewritten once the idea is validated.

## Scope rule

One flow. The single sequence a user walks to experience the idea, end to end, including the screens it passes through.

Cut by default, without asking:

- accounts, auth, onboarding, and permissions — start the app already "signed in" as a fixed local user
- backend, database, migrations, and hosting
- billing, analytics, notifications, and settings
- empty, error, offline, and loading states beyond one shared placeholder
- accessibility beyond native defaults, localization, theming, dark mode
- admin, roles, search, filters, pagination, export
- CI, release config, app icons, splash screens, store metadata

If the user asks for something on this list, take it and cut something else from the flow. Say which.

Keep, always — these are not cuttable even here:

- input validation where bad input crashes the prototype or corrupts the demo path
- secrets kept out of the repository, even when the value is a throwaway key
- native permission prompts required for a capability the flow actually uses

## Mock rule

Mock everything by default: data, network, auth, payments, third-party APIs, AI responses, uploads. Hardcoded fixtures in the repository, in-memory state, no persistence unless the idea is about persistence.

**Confirm the mock boundary with the user before drafting the plan.** Show the list of what will be faked and ask what must be real. Never silently mock the one thing the idea depends on — if the idea *is* the integration (the AI answer quality, the map routing, the payment flow), that one integration is real and everything else is mocked.

Record the confirmed boundary as `D-###` and each faked assumption as `A-###`, so the validation result is not mistaken for evidence the real version works.

## Direction rule

Pick the track with the fewest steps between an empty directory and a running app on a real device, then apply product fit only as a tiebreaker. This inverts the normal `references/platform-decision.md` ordering.

- Mobile: **Expo** unless the idea cannot exist without a deep native capability. Prefer Expo over native iOS even when the product would eventually go native — a prototype that validates the idea in Expo has done its job, and the native rewrite is a later decision. Run in Expo Go where possible; use a development build only when a config plugin requires it.
- Web: **Next.js** (or Vite for a single-page prototype) with local and in-memory state. No auth provider, no hosted database, no ORM.
- Native SwiftUI or Flutter only when the capability being validated *is* the native capability (ARKit, HealthKit, Live Activities, a custom camera pipeline, bespoke motion identity) or the user already has that toolchain set up and no other.

Ask what the user already has installed before recommending. Existing local setup outranks product fit here.

Record the choice as `D-###` with a revisit trigger stating it was made on speed and must be re-decided if the prototype survives validation.

## Research rule

Bounded to a quick validate pass, ahead of the build: does anything like this already exist, and is there any sign the pain is real? Roughly three sources, one round, no Evidence Pack. Skip the market probe entirely — there is no Indie-versus-Startup fork to resolve at this stage.

If web research is unavailable, record the gap and continue. A prototype is itself the validation instrument; do not block it on research.

## Specify rule

Short form, timeboxed to ten minutes. Skipping it entirely is not an option: a prototype that validates the wrong reading of the idea has answered nothing, and the wrong reading is exactly what a vague idea produces.

- 3–7 behaviors covering the one flow: the happy path, the one precondition failure that would embarrass the demo, and whatever the validation question actually turns on.
- Sweep only the ambiguity classes that change what the user can judge — `term`, `boundary`, `visibility`. Skip actor, state, timing, failure, identity, quantity, and reversibility unless the idea being validated is about one of them.
- Ambiguities may stay `deferred` without a revisit trigger. Nothing blocks.
- Run `scripts/validate_behavior_spec.py <spec> --prototype`; open ambiguities warn instead of failing.
- The repository mirror is optional for a throwaway prototype.

`workflow_runner.py` reads `project.mode: prototype` and records an unclosed spec as `prototype-warning: <reason>` on the phase instead of blocking the checkpoint.

## Plan rule

Produce a short MVP Build Plan, fast-mode shaped:

- the one flow, its screens, and their order
- the mock boundary the user confirmed
- 3–6 build steps in dependency order, each ending in something visible on screen
- the fixture data
- a timebox with a cut trigger per step
- how the user will judge the idea after clicking through — the actual validation question
- the explicit list of what was cut

Sequence: shell and navigation → screens with hardcoded fixtures → the one real integration if any → the interaction that carries the idea. No refactor step.

## Testing rule

Minimum. One runnable check on the flow's core logic — whatever breaks the prototype if it is wrong. Nothing else.

- no unit tests for UI components, layout, or navigation
- no snapshot tests, no end-to-end suite, no coverage target, no CI
- non-trivial logic that decides the flow's outcome (a scoring rule, a matcher, a money or date calculation) gets one small test; the rest is verified by clicking through
- the one test names the `BH-###` it proves, and the behaviors verified by clicking through use `Level: manual`
- state the manual click-through path as the acceptance check, step by step

## Done bar

- The one flow runs end to end on the target device.
- Mock boundary is explicit and was confirmed by the user.
- Cut list is written down.
- The validation question is stated and answerable by using the prototype.
- Every faked assumption is recorded as `A-###`, so validation is not mistaken for proof.

Not required: independent review of the artifact, exhaustive states, tests beyond the one check, production readiness of any kind.

Set `project.mode: prototype` in `.product-studio/project.yaml`. `scripts/workflow_runner.py` reads it and clears a checkpoint on a passing self review instead of demanding an independent reviewer.

## Final planning

Run `references/final-planning.md` in its short form. The Implementation Brief still needs Context, Task, Constraints, Verification, Output Format, and Handoff, but Verification is the click-through path plus the one test, and the review may be `self_review_only` without blocking handoff. Note in the brief that the output is a prototype and must not be extended into a product without re-running mode selection.

## Exit

At the end, ask what the validation showed and offer: throw it away, run mode selection again now that the idea is judged (Prototype is not a mode a product stays in), or keep the prototype as a reference while rebuilding properly. Record the answer as the mode revisit outcome.
