# Solo Product Studio

Solo Product Studio is a portable Agent Skill bundle covering one lifecycle end to end: a product idea becomes a validated direction, a hardened behavior spec, a build plan, a scaffolded repository with enforced gates, a reviewed implementation, and a shipped release.

It works in Codex, Claude Code, OpenCode, and other runtimes that support directory-based `SKILL.md` skills. Internal agents, capabilities, and engineering references are bundled implementation playbooks; users only need four entry points.

| Skill | Owns | Ends at |
|---|---|---|
| `product-studio` | Idea → mode → platform → Design Contract → **Specify** (`BH-###` behaviors, `AM-###` ambiguities) → MVP plan → Implementation Brief | the brief, and `docs/agent/BEHAVIORS.md` mirrored beside the code |
| `workflow-init` | Scaffolding the repository that implements it — memory bank, runbooks, acceptance and review gates, hooks, CI. Owns the loop's **sequence** | the PR merged |
| `engineering-cycle` | The **depth behind each gate** — review axes, security, performance, sources, ADRs — and the phase after the merge: observability, release, shipping | production, verified |
| `product-recheck` | Re-evaluating a project already under development: what the code actually is, versus what you meant | a Continue / Redirect / Cut / Stop verdict |

The seam between them is one file. `docs/agent/BEHAVIORS.md` carries a `<!-- behavior-spec/v1 -->` marker on line 2; `product-studio` writes it, `workflow-init` emits a conforming skeleton for repositories that never ran it, the coverage hook greps it, and the reviewer judges against it. A project using all four gets one specification, not four.

`engineering-cycle`'s references are **vendored, not linked** — and `workflow-init` copies the relevant ones into `docs/engineering/`. A scaffolded repository therefore keeps working when this bundle is not installed, which is the same reason every pointer in the generated docs is repo-relative.

## The user experience

Start with:

```text
/product-studio
```

or:

```text
Use product-studio to help me build a product.
```

The first response is a QA session:

1. It asks what you want to build or improve.
2. It extracts context from your answer.
3. It asks only the highest-value missing questions, one at a time.
4. It detects your current stage and recommends an operating mode.
5. It explains the proposed path and waits for confirmation.
6. It researches and plans only the confirmed path.
7. It evaluates a done bar, repairs the largest gap, and pauses at meaningful phase checkpoints.

The default interaction policy is now phase-oriented: after you confirm the goal and working rules, Product Studio runs the phase, evaluates its done bar, repairs the largest gap, and returns at a meaningful checkpoint. It does not interrupt after every intermediate artifact. Ask for strict artifact-by-artifact approval when you want tighter control.

Questions use numbered choices for categorical decisions and always allow a custom answer.

## Discover → Specify → Red → Green → Refactor

Test-driven development only helps if the tests encode the right idea. A suite written over a misread requirement is green and proves nothing, so there is a phase between the design work and the build plan whose whole job is catching the misreading.

**Specify** does two things. First it discovers behaviors — for every in-scope capability it walks the happy path, the precondition failures, the boundaries, concurrency, partial failure, the zero/one/many cases, permission denial, and reversal, writing each surviving branch as a `BH-###` with Given/When/Then and an observable signal. Product scope and behavior scope are kept separate: cutting product scope removes capabilities, cutting behavior scope removes correctness.

Then it attacks its own specification. Every requirement sentence is swept against ten ambiguity classes — term, boundary, actor, state, timing, failure, identity, quantity, visibility, reversibility — and each finding is recorded with two reasonable readings, the concrete case where a user sees a different result under each, the decision needed, and a recommendation:

```text
AM-003 · boundary · "Users can cancel an order before shipment."
  Reading A: shipment = carrier scan. Cancel window closes late.
  Reading B: shipment = warehouse marks packed. Cancel window closes early.
  User-visible difference: a customer cancelling 20 min after packing succeeds
    under A; under B they are told the order already shipped.
  Decision needed: which state closes the cancel window.
  Recommendation: B — the warehouse can actually enforce it. Confidence: medium
  → resolved as D-007, produces BH-014 and BH-015
```

Every ambiguity ends as `resolved -> D-###`, `deferred -> A-###` with a revisit trigger, or `out_of_scope`. One left open blocks the Implementation Brief. Downstream, MVP slices are cut along behaviors, every acceptance criterion cites the `BH-###` it enforces, and every test the implementing agent writes names the behavior it proves — which is what makes an orphan test findable later.

Prototype mode runs a ten-minute short form instead. It is relaxed, not skipped: a prototype that validates the wrong reading of the idea has answered nothing.

## Re-evaluating a project already under way

```text
/product-recheck
```

Use this when you are mid-build and want to know whether what you are building is still what you meant to build. It reconstructs the product from the code rather than the documentation — inferred core idea, feature inventory, flows, entities, test inventory — shows you that summary first and asks whether it matches your vision, then reports three drifts:

- **intent versus code** — does the product do what it set out to do
- **behaviors versus code** — a `BH-###` with no implementation
- **behaviors versus tests** — a behavior with no test is a coverage gap, a test with no behavior is an orphan that likely encodes a misread requirement, a behavior edited after its test is stale

It then asks the decisions that matter, highest impact first, each with a recommended pick, re-runs spec hardening with the code as evidence, and returns a Continue / Redirect / Cut / Stop verdict alongside an explicit behavior delta and test delta.

## Mode-aware paths

The skill separates product stage from operating mode.

- **Prototype Mode**: super-fast MVP to validate an idea. One flow, minimum scope, mock data everywhere (boundary confirmed with you), fastest track to a clickable app, minimum tests, throwaway by design.
- **Hackathon Mode**: fast MVP, one core flow, mock-first, impressive wow moment, demo script, strict cuts.
- **Indie App Mode**: narrow paid wedge, one-person maintainability, simple distribution, early payment validation.
- **SaaS Mode**: buyer/user distinction, workflow ROI, repeat usage, roles and billing considered without premature platform overbuilding.
- **Startup Mode**: beachhead segment, retention, distribution, unit economics, defensibility, and expansion path.
- **Production Mode**: validated product, reliable architecture, security, privacy, observability, migration, and release operations.
- **Custom Mode**: combinations such as `Indie + one-day MVP + native iOS + paid beta`.

The skill may recommend different paths:

```text
Rough idea → Product Lens → Evidence Scout → UX Contract → Spec Cartographer → MVP Forge
Existing MVP → MVP Auditor → Product Synthesizer → Production Blueprint
SaaS idea → Buyer/user QA → workflow validation → SaaS MVP → production planning
Hackathon idea → hero moment → complete core flow → demo-ready MVP
Unvalidated idea → quick validate → one mocked flow → clickable prototype → verdict
Mid-development → Reality Check → Drift Report → Spec Hardening → Verdict
```

Prototype and Hackathon are both fast and mock-first but prove different things: Prototype answers "does the idea hold?" for you, Hackathon answers "does this impress an audience?" at an event. Prototype prefers the fastest track over eventual product fit — Expo over native iOS unless the native capability is the thing being validated — and it is temporary: once the idea is judged, mode selection runs again.

You can accept the recommendation, choose another mode, customize it, or answer more questions.

## Installation

### Codex plugin

This repository includes `.codex-plugin/plugin.json` and the canonical skill under `skills/product-studio/`.

For a local skill install:

```bash
python3 scripts/install.py --target codex
```

For a project-local install, choose a destination explicitly:

```bash
python3 scripts/install.py --target codex --destination .codex/skills
```

For development, use a symlink:

```bash
python3 scripts/install.py --target codex --symlink
```

The Codex plugin can also be installed through a Codex marketplace that points at this repository. Keep the plugin manifest and the `skills/product-studio/` folder together.

### Claude Code

```bash
python3 scripts/install.py --target claude-code
```

Project-local installation:

```bash
python3 scripts/install.py --target claude-code --destination .claude/skills
```

Invoke with natural language or the host's configured skill command:

```text
Use product-studio to help me build a product.
```

### OpenCode

```bash
python3 scripts/install.py --target opencode
```

Project-local installation:

```bash
python3 scripts/install.py --target opencode --destination .opencode/skills
```

OpenCode loads the directory's `SKILL.md` on demand. Use `/product-studio` if slash skills are enabled, otherwise use the natural-language invocation.

### Generic Agent Skills runtimes

```bash
python3 scripts/install.py --target agents
```

The equivalent project-local location is `.agents/skills/product-studio/`.

### Uninstall

Use the same target and destination:

```bash
python3 scripts/install.py --target codex --uninstall
python3 scripts/install.py --target claude-code --uninstall
python3 scripts/install.py --target opencode --uninstall
python3 scripts/install.py --target agents --uninstall
```

The script removes only the installed `product-studio` directory. It refuses to overwrite an existing installation during install; uninstall first when updating a copied installation.

## Artifacts and project memory

When the user approves a workflow, the skill stores state in the active repository:

```text
.product-studio/
├── project.yaml
├── artifacts/
├── research/
└── github/
```

State contains the selected mode, stage, constraints, capabilities, assumptions, decisions, approvals, and next gate. Artifacts are Markdown and include Product Opportunity Brief, Evidence Pack, Design Contract, Behavior Spec, MVP Build Plan, MVP Review Report, Updated Product Definition, Production Build Blueprint, GitHub Delivery Plan, the final Implementation Brief, and any Re-evaluation Verdict.

The Behavior Spec is the one artifact that also lives outside `.product-studio/`. It is mirrored byte-for-byte to `docs/agent/BEHAVIORS.md` so it is tracked in git beside the code, and so an implementing agent, a reviewer, or CI can read it without knowing this skill exists. `scripts/validate_behavior_spec.py <canonical> --mirror docs/agent/BEHAVIORS.md` keeps the two honest.

Project state also stores the goal, protected outcome, house rules, phase done bars, review iterations, and current checkpoint. These rules keep autonomous work aligned while allowing the agent to choose the internal procedure.

Initialize state manually when useful:

```bash
python3 scripts/init_project.py "City Travel MVP" --stage idea --mode hackathon
```

Resume by invoking `product-studio` again. It reads the state, summarizes completed artifacts, and continues from the next incomplete gate without repeating intake.

## Integrations and fallbacks

- Web research: cite sources when available; otherwise produce assumptions and a research plan.
- Mobbin: optional; otherwise use the bundled UX pattern library and platform guidance.
- XcodeBuildMCP: preferred on any native Apple track (SwiftUI/UIKit) so builds, tests, simulator runs, and screenshots are real verification instead of instructions. If it is not installed, Product Studio offers to have you install it once, then continues either with `xcodebuild` shell commands or with manual Xcode steps recorded as unresolved checks.
- GitHub connector or `gh`: inspect existing issues and publish only after approval.
- No GitHub access: export local YAML and Markdown issue plans.
- Existing repository: inspect and adapt the build plan.
- No repository: produce a framework-neutral plan.

Inspect local capability detection with:

```bash
python3 scripts/discover_capabilities.py
```

## Completion actions

After an approved MVP or production plan, choose:

- Start implementation now
- Save plan only
- Export a standalone implementation prompt
- Create GitHub Issues
- Save and create GitHub Issues

The final Implementation Brief is the execution handoff. It names the context and materials, task, constraints, explicit `do not finish until` checks, output shape, and next checkpoint. Implementation and GitHub delivery must preserve its verification criteria.

Scope expansion during a timeboxed build triggers another QA choice: include and cut something else, move to later, reject, or revisit the timebox. The decision is recorded.

## Extending the bundle

Add internal capabilities under `skills/product-studio/references/capabilities/` with purpose, inputs, outputs, completion gate, fallback, and handoff. Add provider behavior to `references/adapters.md`. Add reusable output formats under `templates/`. Add engineering guidance as a file under `skills/engineering-cycle/references/`, routed from that skill's gate table and, if a scaffolded repo should carry it, mapped in `skills/workflow-init/scripts/init.sh`. Do not create another public skill unless a host-specific distribution requirement makes it unavoidable — four is the lifecycle, not a starting point.

Two invariants the test suite enforces, both learned from the packs this content was vendored from:

- **No reference may contain a `../../references/` link.** Those packs shipped ten skills pointing at a sibling directory their installer never fetched, so the bibliographies were dead on arrival.
- **Every file `engineering-cycle` routes to must exist**, and `init.sh --check` asserts the count it maps equals the count that lands. A gate table that names a missing file is the same bug wearing a different hat.

## Validation

Run:

```bash
python3 scripts/validate_bundle.py
python3 -m unittest discover -s tests -v
```

Known limitation: host-specific slash commands, permissions, connectors, and plugin marketplaces vary. The skill's natural-language invocation and offline fallbacks are the portable baseline.
