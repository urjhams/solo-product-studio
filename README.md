# Solo Product Studio

Solo Product Studio is a portable Agent Skill for turning a product idea or existing product into a validated direction, UX contract, MVP build plan, MVP review, production blueprint, or GitHub delivery plan.

It works as a single public entry skill in Codex, Claude Code, OpenCode, and other runtimes that support directory-based `SKILL.md` skills. Internal agents and capabilities are bundled implementation playbooks; users only need to know `product-studio`.

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

## Mode-aware paths

The skill separates product stage from operating mode.

- **Hackathon Mode**: fast MVP, one core flow, mock-first, impressive wow moment, demo script, strict cuts.
- **Indie App Mode**: narrow paid wedge, one-person maintainability, simple distribution, early payment validation.
- **SaaS Mode**: buyer/user distinction, workflow ROI, repeat usage, roles and billing considered without premature platform overbuilding.
- **Startup Mode**: beachhead segment, retention, distribution, unit economics, defensibility, and expansion path.
- **Production Mode**: validated product, reliable architecture, security, privacy, observability, migration, and release operations.
- **Custom Mode**: combinations such as `Indie + one-day MVP + native iOS + paid beta`.

The skill may recommend different paths:

```text
Rough idea → Product Lens → Evidence Scout → UX Contract → MVP Forge
Existing MVP → MVP Auditor → Product Synthesizer → Production Blueprint
SaaS idea → Buyer/user QA → workflow validation → SaaS MVP → production planning
Hackathon idea → hero moment → complete core flow → demo-ready MVP
```

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

State contains the selected mode, stage, constraints, capabilities, assumptions, decisions, approvals, and next gate. Artifacts are Markdown and include Product Opportunity Brief, Evidence Pack, Design Contract, MVP Build Plan, MVP Review Report, Updated Product Definition, Production Build Blueprint, GitHub Delivery Plan, and the final Implementation Brief.

Project state also stores the goal, protected outcome, house rules, phase done bars, review iterations, and current checkpoint. These rules keep autonomous work aligned while allowing the agent to choose the internal procedure.

Initialize state manually when useful:

```bash
python3 scripts/init_project.py "City Travel MVP" --stage idea --mode hackathon
```

Resume by invoking `product-studio` again. It reads the state, summarizes completed artifacts, and continues from the next incomplete gate without repeating intake.

## Integrations and fallbacks

- Web research: cite sources when available; otherwise produce assumptions and a research plan.
- Mobbin: optional; otherwise use the bundled UX pattern library and platform guidance.
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

Add internal capabilities under `skills/product-studio/references/capabilities/` with purpose, inputs, outputs, completion gate, fallback, and handoff. Add provider behavior to `references/adapters.md`. Add reusable output formats under `templates/`. Do not create another public skill unless a host-specific distribution requirement makes it unavoidable.

## Validation

Run:

```bash
python3 scripts/validate_bundle.py
python3 -m unittest discover -s tests -v
```

Known limitation: host-specific slash commands, permissions, connectors, and plugin marketplaces vary. The skill's natural-language invocation and offline fallbacks are the portable baseline.
