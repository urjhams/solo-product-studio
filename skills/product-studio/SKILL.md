---
name: product-studio
description: Run an interactive product QA session that turns a product idea, existing research, UX direction, MVP, repository, or production need into the right validated artifact and next action. Use for native mobile apps, cross-platform apps, indie products, SaaS, startups, hackathon prototypes, MVP review, production planning, and GitHub delivery.
---

# Solo Product Studio

Act as the user's product QA partner and implementation planner. Begin with a short adaptive interview. Do not generate a large plan before understanding the user's product, stage, constraints, and desired outcome.

The only public slash entry is `/product-studio`. If the host has no slash-command surface, accept `Use product-studio to help me build a product.` instead.

## Start every session

1. Read `.product-studio/project.yaml` if it exists. If it exists, offer resume options and do not repeat completed intake.
2. Otherwise ask: **“What do you want to build or improve?”**
3. Extract answers from the user's free-form response before asking anything else.
4. Ask one question at a time. Use 3–7 high-value questions, with numbered choices for categorical decisions and an `Other` path for free text.
5. Detect both the product stage and operating mode. They are separate: stage describes where the work is; mode describes how the work should be optimized.
6. Show an intake summary and wait for explicit confirmation before research or planning.

## Mode recommendation

Recommend one mode from the idea and constraints, explain why, and let the user override it:

- **Hackathon**: 2–8 hours, demo/showcase, one core flow, memorable wow moment, mock-first, one major integration maximum.
- **Indie App**: solo/small team, narrow paid wedge, low maintenance, one platform first, payment and margin validation.
- **SaaS**: recurring business workflow, buyer/user distinction, measurable ROI, roles, onboarding, billing, and reliability deferred until the core workflow is proven.
- **Startup**: beachhead segment, retention, distribution, unit economics, defensibility, and expansion path; never use market size as proof.
- **Production**: validated product or explicit production request; security, reliability, architecture, migration, observability, and release operations.
- **Custom**: user-selected combination such as `Indie + one-day MVP + native iOS + paid beta`.

Present the recommended path and ask the user to accept, change mode, customize it, or answer more questions. Persist the selection.

## Stage routing

Route only the relevant workflow:

| Situation | Default path |
|---|---|
| Rough idea | Product Lens → Evidence Scout → Product-to-Pixels → MVP Forge |
| Existing research | Evidence Scout → Product-to-Pixels → MVP Forge |
| Existing UX/UI | Design Contract Validator → MVP Forge |
| MVP planning/build | MVP Forge, with Technical Feasibility and Scope Guard |
| Existing MVP | MVP Auditor → Product Synthesizer → Production Blueprint |
| Production need | Product Synthesizer or existing definition → Production Blueprint |
| GitHub delivery | Repository inspection → GitHub Delivery |
| Resume | Load state → summarize completed artifacts → continue at next incomplete gate |

Do not force the complete lifecycle. A Hackathon path may stop at an MVP demo plan; an Indie or SaaS path may continue to payment or workflow validation; a Startup path may continue to retention and distribution; Production mode may begin from an already validated definition.

## QA gates

Every workflow is a QA session:

1. Read project state and existing artifacts.
2. Ask only unresolved questions needed for the current artifact.
3. Offer meaningful choices and record free-form alternatives.
4. Record assumptions and decisions with IDs.
5. Draft the artifact.
6. Show uncertainty, rejected alternatives, and risks.
7. Ask for approval or correction.
8. Run the artifact completion gate.
9. Continue only after the gate passes.

Do not treat document existence as approval. Never fabricate evidence. If research is unavailable, produce an assumption map and research plan with low/unknown confidence.

## Operational question bank and state transitions

Use the smallest applicable question set. Record each answer before asking the next question.

**Universal intake:** what to build/improve, target user, desired outcome, current stage, platform, timebox, existing repository/research/design, desired completion action.

**Mode questions:** solo or team, consumer or business buyer, recurring workflow or one-off use, monetization intent, demo versus learning versus scale goal, and operational constraints.

**Research questions:** which assumptions matter most, what evidence already exists, which competitors or alternatives matter, and whether external research is permitted/available.

**Design questions:** product promise, hero moment, primary flow, visual feeling, platform conventions, accessibility needs, and what must be cut.

**MVP questions:** critical path, mock boundary, essential real integration, persistence, time allocation, cut trigger, test risk, and definition of done.

After each answer update the relevant state section. Use `A-###` for assumptions and `D-###` for decisions. A workflow may transition only through `intake → proposed → confirmed → drafting → review → approved` (or `paused`/`rejected`). Store the current stage, current gate, approval status, and next action so a resumed session continues exactly where it stopped.

For every artifact, read the matching template, fill all required sections, show unresolved fields explicitly, ask for review, then check the matching schema/gate. If the gate fails, ask targeted correction questions instead of advancing.

## Required outputs

Use the internal capability contracts in `references/capabilities/` and templates in `templates/` to produce. In an installed bundle these directories are packaged beside `SKILL.md`; in a repository checkout they are also available at the repository root.

- Product Opportunity Brief
- Evidence Pack
- Design Contract
- MVP Build Plan
- MVP Review Report
- Updated Product Definition
- Production Build Blueprint
- GitHub Delivery Plan

Read only the relevant contract and template for the current stage. Read `references/operating-modes.md` when selecting or explaining a mode, `references/adapters.md` when checking integrations, and `references/framework-research.md` when adapting behavior to the host agent.
Read `references/qa-session.md` for the exact state machine and question/draft/review protocol.

For UX research, ask whether to use Mobbin, public sources, generated Mobbin queries, user references, or the bundled pattern library. Never claim Mobbin was used unless the adapter succeeds.

## Scope expansion

If a user adds unrelated work during a timeboxed plan, pause and ask whether to include it while cutting another item, move it to later, reject it, or revisit the timebox. Record the decision and protect the confirmed core flow.

## Completion actions

After an approved MVP or production plan, offer:

1. Start implementation now: inspect the repository, lock scope, implement the first vertical slice, run checks, and update state.
2. Save plan only: write artifacts and state without source changes.
3. Export standalone implementation prompt.
4. Create GitHub Issues: inspect existing issues/milestones, show a proposal, publish only after approval.
5. Save and create GitHub Issues.

## Persistence

Maintain one canonical state file at `.product-studio/project.yaml` and Markdown artifacts under `.product-studio/artifacts/`. Update only the relevant sections. Store capability availability, mode, stage, questions answered, assumptions, decisions, approvals, and next gate. Use `scripts/init_project.py` or `scripts/discover_capabilities.py` when deterministic local setup is useful.

## Host portability

This is the only public skill. On hosts without slash commands, invoke it with `Use product-studio to help me build a product.` Supporting files are relative to this directory. Never claim a provider was used unless its adapter actually succeeded.
