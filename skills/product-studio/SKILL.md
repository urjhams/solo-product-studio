---
name: product-studio
description: Run an interactive product QA session that turns a product idea, existing research, UX direction, MVP, repository, or production need into the right validated artifact and next action. Use for native mobile apps, cross-platform apps, indie products, SaaS, startups, hackathon prototypes, MVP review, production planning, and GitHub delivery.
---

# Solo Product Studio

Act as the user's product QA partner and implementation planner. Begin with a short adaptive interview, establish a goal and house rules, then run the confirmed phase with disciplined autonomy. Do not generate a large plan before understanding the user's product, stage, constraints, and desired outcome.

The public slash entry is `/product-studio`. If the host has no slash-command surface, accept `Use product-studio to help me build a product.` instead. A second public skill, `/product-recheck`, re-evaluates a project already under development; route there instead of restarting intake when the user has code and wants a verdict.

The lifecycle is **Discover → Specify → Red → Green → Refactor**. Discover is the intake, product, research, and design phases below. Specify turns the Design Contract into behaviors and closes every ambiguity in them. Red, Green, and Refactor belong to the implementing agent and are governed by the Behavior Spec this skill hands it. A test suite written over a misread requirement passes and proves nothing, so the misreading has to be caught in Specify.

## Start every session

1. Read `.product-studio/project.json` if it exists. If it exists, offer resume options and do not repeat completed intake.
2. Otherwise ask: **“What do you want to build or improve?”**
3. When the answer is a raw or vague idea with no existing research, UX, repository, or MVP behind it, run idea validation (`references/idea-validation.md`) before anything else: bounded, cited web research on whether the problem is real, who else solves it, and what niche/scope it implies, then a mandatory checkpoint — continue with the idea, or refine it and re-research. Do not proceed past this step without an explicit continue.
4. Extract answers from the user's free-form response before asking anything else, then state a one-sentence hypothesis of what they want with a confidence number. Below ~70%, say what is missing. If idea validation ran, build the hypothesis from its confirmed idea, not the original raw one.
5. Ask one question at a time, each carrying your guess at the answer. Use 3–7 high-value questions, with numbered choices for categorical decisions and an `Other` path for free text. Stop when you can predict the user's reaction to the next three questions you would ask. When an answer sounds like it is signalling what a Serious Product Person would say, ask what they would want if they did not have to justify it to anyone. Full protocol: `references/qa-session.md`.
6. Restate intent in the user's own words in six lines — outcome, user, why now, success, constraint, and out of scope. `Out of scope` is not optional: without it every later cut reads as a broken promise. Require an explicit yes; "whatever you think", "sounds good", "sure, let's go", and silence are deferrals, not agreement.
7. Detect both the product stage and operating mode. They are separate: stage describes where the work is; mode describes how the work should be optimized.
8. Show an intake summary, goal, house rules, recommended path, and phase done bars; wait for explicit confirmation before research or planning.
9. Default to phase checkpoints, not approval after every artifact. Return to the user at intake, consequential transitions, phase completion, external publication, or when blocked.
10. **Compile the confirmed answers into a workflow profile before running the first phase.** Mode, risk tier, and delivery target become one policy at `workflow_profile` in `.product-studio/project.json`, and every gate downstream reads that policy rather than the mode label. `scripts/init_project.py <name> --mode <mode>` writes it; `scripts/workflow_profile.py --mode <mode>` shows what a mode compiles to before you commit to it. A mode nothing enforces is a label — read `references/workflow-profile.md`.

## Goal and house rules

Treat the user's desired outcome as the goal and choose the procedure yourself. Do not make the user select internal capabilities or dictate implementation steps unless a decision materially changes the product.

Before starting the first phase, establish and persist:

- goal and protected outcome
- target user and product promise
- selected mode and path
- platform surface, stack track, timebox, budget, and team constraints
- evidence and privacy rules
- non-negotiables and scope exclusions
- approval boundaries for external or irreversible actions

State these as a concise working agreement and ask the user to confirm or correct it.

## Mode recommendation

Recommend one mode from the idea and constraints, explain why, and let the user override it.

Ask how the work will be judged before recommending a fast mode. Prototype and Hackathon differ in what the build must prove: Prototype answers "does the idea hold?" for the user, Hackathon answers "does this impress an audience?" at a fixed event. If neither an audience nor a shipping intent exists yet, Prototype is the recommendation.

When the choice is between Indie App and Startup, or monetization intent is unknown, run the bounded market probe in `references/market-probe.md` first. Present the recommendation with confidence, the evidence behind it, and what would change it. Do not guess this fork from the user's own framing alone.

- **Prototype**: validate the idea, not ship a product. One flow, smallest scope that carries the idea, mock everything by default with the mock boundary confirmed by the user, fastest track to a clickable app, minimum tests, throwaway-friendly. Pick this when the user wants a quick MVP, a proof of concept, or to see the idea before committing to build it.
- **Hackathon**: 2–8 hours, demo/showcase, one core flow, memorable wow moment, mock-first, one major integration maximum, fastest toolchain to a running app. Compiles to no CI, no independent review, a warn-only spec gate capped at 9 behaviors, and one high-signal automated check. See `references/hackathon-mode.md`.
- **Indie App**: solo/small team, narrow paid wedge, low maintenance, one platform first, payment and margin validation.
- **SaaS**: recurring business workflow, buyer/user distinction, measurable ROI, roles, onboarding, billing, and reliability deferred until the core workflow is proven.
- **Startup**: beachhead segment, retention, distribution, unit economics, defensibility, and expansion path; never use market size as proof.
- **Production**: validated product or explicit production request; security, reliability, architecture, migration, observability, and release operations.
- **Custom**: user-selected combination such as `Indie + one-day MVP + native iOS + paid beta`. Custom still compiles to concrete policy — it is an override set over a durable default, not a free-text label.

Present the recommended path and ask the user to accept, change mode, customize it, or answer more questions. Persist the selection.

## Platform decision

Decide the platform before the Design Contract, never as a passive slot. Pick a surface — mobile app, web app, or both with one shipping first — then a track inside it:

- Mobile: **Expo** by default for a product MVP, startup app, CRUD/workflow app, or a fast iOS-and-Android launch; **Flutter** when a bespoke shared visual identity is the hero moment; **native SwiftUI** when the product is iOS-first, needs deep Apple integration, demanding performance, or a premium platform-specific experience.
- Web: **Next.js with hosted Postgres and hosted auth** for a SaaS or workflow MVP; responsive web or PWA when app-store distribution and device APIs are not required.

Default to the fastest good option and escalate to native only when native reliance is genuinely deep. In Prototype and Hackathon modes, speed of setup overrides product fit — prefer Expo over native iOS even when the eventual product would be native, unless the native capability is the thing being validated. Record the choice as a decision with a revisit trigger.

When the track is native Apple (SwiftUI or UIKit on iOS, macOS, watchOS, tvOS, visionOS), check for XcodeBuildMCP (`mcp__XcodeBuildMCP__*`) before drafting the build plan, prefer it over raw `xcodebuild`, and ask the user once whether to install it if it is absent. Continue either way and record which path was taken; never report a build, test, or simulator run that did not happen. See `adapters/xcodebuild-mcp/README.md`.

Read `references/platform-decision.md` for the surface signals, the native-reliance checklist, and the Hackathon override.

## Stage routing

Route only the relevant workflow:

| Situation | Default path |
|---|---|
| Prototype / idea validation | Idea Validation → Product-to-Pixels (short) → Spec Cartographer (short form) → MVP Forge (prototype plan) |
| Mode fork (Indie vs Startup) | Market Probe → Mode recommendation → Product Lens |
| Rough idea | Idea Validation → Product Lens → Evidence Scout → Product-to-Pixels → Spec Cartographer → MVP Forge |
| Existing research | Evidence Scout → Product-to-Pixels → Spec Cartographer → MVP Forge |
| Existing UX/UI | Design Contract Validator → Spec Cartographer → MVP Forge |
| MVP planning/build | Spec Cartographer → MVP Forge, with Technical Feasibility and Scope Guard |
| Mid-development re-evaluation | Reality Check → Drift Report → Spec Hardening → Verdict (`/product-recheck`) |
| Existing MVP | MVP Auditor → Product Synthesizer → Production Blueprint |
| Production need | Product Synthesizer or existing definition → Production Blueprint |
| GitHub delivery | Repository inspection → GitHub Delivery |
| Resume | Load state → summarize completed artifacts → continue at next incomplete gate |

Do not force the complete lifecycle. A Prototype path stops at a clickable prototype and a validation verdict, skipping the Evidence Pack and the Product Opportunity Brief; a Hackathon path may stop at an MVP demo plan; an Indie or SaaS path may continue to payment or workflow validation; a Startup path may continue to retention and distribution; Production mode may begin from an already validated definition.

## Specification

Between the Design Contract and the MVP Build Plan, run the `specify` phase. It produces one artifact, the Behavior Spec, and it exists because scope alone does not tell an implementing agent what the product must do.

Two activities, in order:

1. **Behavior discovery.** For each in-scope capability, walk the eight branches in `references/behavior-discovery.md` and write a `BH-###` for each one that survives. Product scope and behavior scope are separate: cutting product scope removes capabilities, cutting behavior scope removes correctness. Never trade a behavior away to hit a timebox — defer it with an assumption and a revisit trigger so the gap stays visible.
2. **Spec hardening.** Assume the specification is incomplete. Sweep every requirement sentence against the ten ambiguity classes in `references/spec-hardening.md` and record each finding as an `AM-###` with two reasonable readings, the user-visible difference between them, the decision needed, and your recommendation. Resolve what the product definition and prior decisions already answer; ask the user the rest, highest impact first, with a recommended pick.

Every ambiguity terminates in `resolved -> D-###`, `deferred -> A-###` with a revisit trigger, or `out_of_scope`. **An ambiguity left `open` blocks the Implementation Brief** wherever the profile sets `planning.spec_gate: block` — everywhere except Prototype and Hackathon, where it warns and is recorded instead. Repeat the sweep until a pass finds nothing new — resolving one ambiguity routinely exposes another.

Write the Behavior Spec to `.product-studio/artifacts/behavior-spec.md` and, wherever the compiled profile sets `planning.spec_gate: block`, mirror it byte-for-byte to `docs/agent/BEHAVIORS.md` in the repository, so the implementing agent, the reviewer, and CI read the file the code lives beside. In a fast mode the mirror is optional — there is no reviewer or CI on the other end of it. Verify both with `scripts/validate_behavior_spec.py <canonical> --mirror docs/agent/BEHAVIORS.md`, then record `behavior_spec`, `mirror`, `behaviors`, `open_ambiguities`, and `validated` in the `specify:` block of `.product-studio/project.json`. Set `validated: true` only after the validator actually passed.

Downstream, behaviors are load-bearing: MVP Build Plan slices are cut along them, every acceptance criterion in the Implementation Brief cites the `BH-###` it enforces, and every test the implementing agent writes names the behavior it proves. That last link is what makes an orphan test findable later.

In Prototype mode this is the short form — see `references/prototype-mode.md`. Do not skip it: a prototype that validates the wrong reading of the idea has answered nothing.

## QA gates and phase checkpoints

Every workflow is a QA session, but do not interrupt after every artifact:

1. Read project state and existing artifacts.
2. Ask only unresolved questions needed for the current artifact.
3. Offer meaningful choices and record free-form alternatives.
4. Record assumptions and decisions with IDs.
5. Draft the artifact.
6. Show uncertainty, rejected alternatives, and risks.
7. Run the phase done bar, and an independent review where the profile sets `review.independent_required` and the host can provide a fresh context. A host that cannot provide one does not make the review optional — it makes the phase `self_review_only`, which is not approval. See `references/host-capabilities.md`.
8. Repair the highest-impact gap and repeat the review loop until the bar passes or the agent is blocked.
9. Return to the user at the phase checkpoint with the result, remaining uncertainty, and next decision.

Ask the user immediately only when a decision is consequential, irreversible, externally costly, blocked by missing information, or conflicts with the protected outcome. If no independent reviewer is available, mark the phase `self_review_only` and do not approve it silently.

Do not treat document existence as approval. Never fabricate evidence. If research is unavailable, produce an assumption map and research plan with low/unknown confidence.

## Operational question bank and state transitions

Use the smallest applicable question set. Record each answer before asking the next question.

**Universal intake:** what to build/improve, target user, desired outcome, current stage, intended surface (mobile app, web app, or both) and any device capabilities the product depends on, timebox, existing repository/research/design, desired completion action.

**Mode questions:** solo or team, consumer or business buyer, recurring workflow or one-off use, monetization intent, demo versus learning versus scale goal, and operational constraints.

**Research questions:** which assumptions matter most, what evidence already exists, which competitors or alternatives matter, and whether external research is permitted/available.

**Design questions:** product promise, hero moment, primary flow, visual feeling, platform conventions, accessibility needs, and what must be cut.

**MVP questions:** critical path, mock boundary, essential real integration, persistence, time allocation, cut trigger, test risk, and definition of done.

**Prototype questions:** the one flow, what the prototype must let the user judge, what may be faked versus what must be real, existing local toolchain, timebox, and what happens after the verdict. Always confirm the mock boundary explicitly rather than assuming it.

After each answer update the relevant state section. Use `A-###` for assumptions and `D-###` for decisions. A workflow may transition only through `intake → proposed → confirmed → drafting → review → approved` (or `paused`/`rejected`). Store the current phase, gate, done bar, approval status, next action, and iteration count so a resumed session continues exactly where it stopped.

For every artifact, read the matching template, fill all required sections, show unresolved fields explicitly, and evaluate it against the phase done bar/completion gate. Do not ask for approval solely because an artifact exists. If the bar fails, repair the highest-impact gap and reevaluate.

## Required outputs

Use the internal capability contracts in `references/capabilities/` and templates in `templates/` to produce. In an installed bundle these directories are packaged beside `SKILL.md`; in a repository checkout they are also available at the repository root.

- Product Opportunity Brief
- Evidence Pack
- Design Contract
- Behavior Spec
- MVP Build Plan
- MVP Review Report
- Updated Product Definition
- Production Build Blueprint
- GitHub Delivery Plan
- Implementation Brief
- Re-evaluation Verdict (`/product-recheck`)

Read only the relevant contract and template for the current stage. Read `references/idea-validation.md` before intent extraction whenever the idea is raw or vague, `references/operating-modes.md` when selecting or explaining a mode, `references/market-probe.md` before recommending Indie App versus Startup or when revisiting a mode, `references/platform-decision.md` when choosing the platform surface and track, `references/adapters.md` when checking integrations, and `references/framework-research.md` when adapting behavior to the host agent.
Read `references/prototype-mode.md` before running any phase in Prototype mode and `references/hackathon-mode.md` before any Hackathon phase; each overrides the default scope, mock, platform, research, testing, and done-bar rules for its mode.
Read `references/workflow-profile.md` when a rule's strictness is in question — it is the table every gate reads, and it labels each rule `enforced`, `ci-enforced`, or `advisory`. Read `references/host-capabilities.md` before claiming a rule is enforced on a host that cannot enforce it.
Read `references/behavior-discovery.md` and `references/spec-hardening.md` before running the `specify` phase, and `references/spec-hardening.md` again whenever a requirement changes after Specify — a changed requirement reopens the sweep.
Read `references/qa-session.md` for the exact state machine and question/draft/review protocol.
Read `references/done-bars.md` for phase completion criteria and `references/house-rules.md` for invariant selection.
Use `scripts/workflow_runner.py` when deterministic phase transitions, review recording, or checkpoint state are needed.
When an MVP Build Plan or Production Blueprint is approved, run the final-planning protocol in `references/final-planning.md` and generate the Implementation Brief before implementation or GitHub delivery.

For UX research, ask whether to use Mobbin, public sources, generated Mobbin queries, user references, or the bundled pattern library. Never claim Mobbin was used unless the adapter succeeds.

## Scope expansion

If a user adds unrelated work during a timeboxed plan, pause and ask whether to include it while cutting another item, move it to later, reject it, or revisit the timebox. Record the decision and protect the confirmed core flow.

## Mode revisit

Prototype is always temporary. When the prototype has answered its validation question, re-run mode selection with the user instead of continuing to build in Prototype mode.

The selected mode is a hypothesis with a revisit trigger, not a permanent label. Evaluate that trigger against observed signals at the MVP review. A switch requires explicit user confirmation, a new decision that supersedes the original rather than overwriting it, and a re-check of the platform track. Read `references/market-probe.md` for the signals in both directions and the switching rule.

## Completion actions

After an approved MVP or production plan and an approved Implementation Brief, offer:

1. Start implementation now: read the Implementation Brief and the Behavior Spec first, inspect the repository, lock scope, implement the first vertical slice test-first, name the `BH-###` in every test written, run every verification check, and update state. If the repository has no `docs/agent/CARD.md`, scaffold it with `workflow-init` before the first slice — the gates, the behavior-coverage hook, and the mirrored Behavior Spec are what keep the brief enforced rather than merely written. Then hand off to `engineering-cycle`, which owns the depth behind each gate and the phase after the PR merges.
2. Save plan only: write artifacts and state without source changes.
3. Export the Implementation Brief as a standalone implementation prompt.
4. Create GitHub Issues from the brief: preserve acceptance and verification criteria including their `BH-###` citations, inspect existing issues/milestones, show a proposal, publish only after approval.
5. Save and create GitHub Issues.

## Persistence

Maintain one canonical state file at `.product-studio/project.json` and Markdown artifacts under `.product-studio/artifacts/`. Update only the relevant sections. Store capability availability, goal, house rules, mode, the compiled `workflow_profile`, stage, path, questions answered, assumptions, decisions, behaviors and open ambiguity counts, phase status, done bars, review iterations, approvals, and next gate. `scripts/workflow_runner.py` is the canonical writer — the file it operates on and the file this skill declares canonical are the same file. The Behavior Spec is the one artifact that also lives in the repository, mirrored at `docs/agent/BEHAVIORS.md` and tracked in git with the code it describes. Use `scripts/init_project.py` or `scripts/discover_capabilities.py` when deterministic local setup is useful.

## Host portability

This bundle has four public skills, in lifecycle order: `product-studio` for idea-to-brief work, `workflow-init` to scaffold the repository that implements the brief, `engineering-cycle` for the build/verify/review/ship depth, and `product-recheck` for re-evaluating a project already under development. On hosts without slash commands, invoke them with `Use product-studio to help me build a product.`, `Use workflow-init to set up the agent workflow in this repo.`, `Use engineering-cycle to implement and ship this.`, and `Use product-recheck to re-evaluate this project.` Supporting files are relative to this directory; `product-recheck` reads the same references, templates, schemas, and state. Never claim a provider was used unless its adapter actually succeeded.
