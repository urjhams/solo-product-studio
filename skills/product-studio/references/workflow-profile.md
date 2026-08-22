# Workflow profile

The confirmed intake answers compile into one policy, and every gate downstream reads that policy instead of re-deciding from the mode label. `scripts/workflow_profile.py` holds the table; `.product-studio/project.json` holds the compiled result under `workflow_profile`.

This file is the human half of that module. When a rule below says "profile-dependent", this table is what it depends on.

## Why compile at all

A mode nothing enforces is a label. Before this existed, `hackathon` was a string in a state file: the runner read only `prototype`, the validators exposed only `--prototype`, and a four-hour demo inherited zero-open-ambiguity requirements, independent review, full behavior coverage, PR creation, and reviewer re-review. The prose described seven modes; the mechanism had two.

## The table

| field | prototype | hackathon | indie | saas | startup | production | custom |
|---|---|---|---|---|---|---|---|
| `risk_tier` | low | low | moderate | moderate | moderate | **high** | moderate |
| `delivery_target` | local_demo | local_demo | pull_request | preview | preview | production | code_only |
| `planning.spec_gate` | warn | warn | block | block | block | block | block |
| `planning.max_behaviors` | 7 | 9 | — | — | — | — | — |
| `define.gate` | advisory | advisory | required | required | required | required | required |
| `design.gate` | advisory | advisory | required | required | required | evidence_required | required |
| `development.refactor_phase` | no | no | yes | yes | yes | yes | yes |
| `development.pull_request_required` | no | no | yes | yes | yes | yes | yes |
| `testing.automated_required` | smoke | smoke | core | core | core | full | core |
| `testing.coverage_target` | — | — | — | core paths | core paths | critical + regression | — |
| `testing.ci_required` | no | no | yes | yes | yes | yes | yes |
| `review.independent_required` | **no** | **no** | yes | yes | yes | yes | yes |
| `review.lane` | none | none | offline | offline | offline | offline | offline |
| `development.merge_policy` | ask | ask | ask | ask | ask | **never** | ask |
| `deployment.allowed` | no | no | no | no | no | no | no |

`review.lane` and `development.merge_policy` are the two fields the intake asks rather than the mode dictates; the row above is the default each mode compiles to when nobody answers. `lane` picks where the review runs — `offline` is a local reviewer subagent, `online` is the repo's own Actions workflow — and it may not be `none` wherever `independent_required` is true. `merge_policy` is the only field that governs an action the agent takes on the user's behalf: `ask` raises a permission prompt, `auto_on_approve` lets a session run PR → review → merge unattended once a review marker for that exact HEAD says APPROVE, and `never` blocks the merge outright. A high `risk_tier` forces `never` — `human-approval-gate` is in the production safety floor, and an agent merging its own PR is exactly the gate it names.

`deployment.allowed` is `false` in every compiled default, production included. Production deployment is an explicit opt-in, never a consequence of a mode or a merge — see below.

Prototype and Hackathon differ in exactly two enforced values: the behavior cap, and one safety-floor entry. Everything else separating them is judgment, and it lives in `references/prototype-mode.md` and `references/hackathon-mode.md`. Do not invent enforced differences to make the two rows look more distinct than they are.

## The safety floor

Cumulative, and never cuttable. An override may add entries; nothing removes one, and `compile_profile` unions the mode's floor back in after any override.

- every mode: `secrets-out-of-repo`, `input-validation-on-demo-path`
- hackathon adds: `demo-data-labeled-as-fake`
- indie and custom add: `auth-on-user-data`, `dependency-audit`
- saas and startup add: `authz-per-tenant`, `pii-encrypted-at-rest`
- production adds: `security-review`, `observability`, `rollout-plan`, `rollback-plan`, `human-approval-gate`

## Which rule depends on which field

| rule | field | enforcement |
|---|---|---|
| An open ambiguity blocks the Implementation Brief | `planning.spec_gate` | **enforced** — `workflow_runner.checkpoint`, `validate_behavior_spec.py` |
| Behavior count is capped | `planning.max_behaviors` | **enforced** — `validate_behavior_spec.py` |
| Every acceptance criterion cites its `BH-###` | `planning.spec_gate` | **enforced** — `validate_implementation_brief.py` |
| The `docs/agent/BEHAVIORS.md` mirror must be byte-identical | `planning.spec_gate` | **enforced** — `validate_behavior_spec.py --mirror` |
| An independent reviewer must clear the phase | `review.independent_required` | **enforced** — `workflow_runner.checkpoint` |
| All six define slots are filled before the definition is signed off | `define.gate` | **enforced** — `workflow_runner.checkpoint` |
| The critical interaction needs user evidence, not just a complete artifact | `design.gate` | **enforced** — `workflow_runner.checkpoint` |
| A brief may not plan a deployment | `deployment.allowed` | **enforced** — `validate_implementation_brief.py`, `workflow_runner.deploy` |
| Finishing a task means opening its PR | `development.pull_request_required` | **ci-enforced** — the generated verdict hook and branch protection |
| Every gate in the CI ladder runs on PR and default-branch push | `testing.ci_required` | **ci-enforced** — the generated workflow |
| Behavior coverage: every active `BH-###` has a test naming it | `testing.automated_required` | **ci-enforced** — the generated coverage hook |
| The agent may merge its own PR | `development.merge_policy` | **ci-enforced** — the generated verdict hook's `gh pr merge` gate, plus the deliberate absence of a `gh pr merge` allow entry |
| Where the independent review runs | `review.lane` | **ci-enforced** on the online lane — the generated `claude-review.yml` runs and posts itself. Advisory on the offline lane: spawning the local reviewer is a RUNBOOKS instruction with no mechanism behind it |
| A refactor step follows green | `development.refactor_phase` | advisory |
| Coverage target | `testing.coverage_target` | advisory |

**enforced** means a bundled script exits non-zero. **ci-enforced** means a generated workflow or hook fails. **advisory** means prose only — and a rule labelled advisory should not be described anywhere as if it blocks.

## Overrides

`compile_profile(mode, overrides)` merges one level deep: nested dicts merge per key, scalars and lists replace. Two things happen after the merge, so an override can trigger them:

- `risk_tier: high` forces `design.gate: evidence_required` and unions in the production safety floor. This is why the design evidence gate needs no separate switch.
- `define.gate` derives from `risk_tier` at compile time: `low` is `advisory`, everything else is `required`. Prototype and Hackathon are the only low-tier modes, so they are the only ones a pricing or proof slot does not block. An explicit `define.gate` override still wins.
- `deployment.allowed: true` with a `delivery_target` below `staging` raises. A deploy needs somewhere to deploy to.

`version` and `mode` are stamped last, so no override can forge either.

## Custom mode

Custom is not exempt. It compiles to concrete policy like every other mode — a durable default that the user's confirmed combination then overrides field by field. `Indie + one-day MVP + native iOS + paid beta` is an override set, not a free-text label, because a label enforces nothing.

## Enforcement honesty

There is no runtime JSON-schema validator in this bundle; adding one would break the dependency-free rule. `compile_profile` being the only writer of these values is the enforcement, `schemas/workflow-profile.schema.json` documents the same enums, and one test asserts the two never drift. Do not describe the schema as if it validates at runtime.
