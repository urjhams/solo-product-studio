# CI/CD

Setting up or modifying the build/deploy pipeline, wiring feature-flag plumbing into automation, or
building a rollback workflow. Open this when a quality gate needs to move into CI, when CI is
failing and you need the feedback loop, or when deployment strategy is the question.

CI/CD is the enforcement mechanism for every other reference in this bundle — it catches what
humans and agents miss, on every single change, consistently. Two principles drive everything
below: **shift left** (a bug caught in lint costs minutes; the same bug in production costs hours —
push checks as early in the pipeline as they'll go) and **faster is safer** (smaller batches and
more frequent releases reduce risk; a 3-change deploy is easier to debug than a 30-change one).

This repository's actual pipeline lives at `.github/workflows/ci.yml` and
`.github/workflows/claude-review.yml` — read those for what's really configured here. What follows
is the shape those files fill in and the practices around them; don't duplicate the YAML, extend
it.

## The quality-gate pipeline

Every change goes through these in order before merge:

```
Pull Request Opened
    |
    v
LINT CHECK       (eslint, prettier, ...)
    | pass
TYPE CHECK       (tsc --noEmit, mypy, ...)
    | pass
UNIT TESTS
    | pass
BUILD
    | pass
INTEGRATION      (API/DB tests)
    | pass
E2E (optional)   (Playwright/Cypress)
    | pass
SECURITY AUDIT   (npm audit / pip-audit / cargo audit)
    | pass
BUNDLE SIZE      (if applicable)
    v
Ready for review
```

**No applicable gate can be skipped.** Which gates apply comes from the compiled workflow profile —
a Prototype or Hackathon build runs no CI at all (`testing.ci_required: false`), and a repository
with no type system has no type check. That is the only permitted way for a gate to be absent.
Once a gate applies it is non-negotiable: lint fails -> fix lint, don't disable the rule. A test
fails -> fix the code, don't skip the test. The fixed ordering matters: cheap, fast checks (lint, types) run before
expensive ones (integration, e2e) so a trivial mistake fails in seconds, not minutes.

This is the depth behind `docs/agent/CARD.md` step 9 (Gate 1, task-evaluator) and step 11 (Gate 2,
review) — those gates decide when a human/agent review happens; this pipeline is what runs
automatically on every push regardless.

## The CI-failure feedback loop

The value of CI with an agent in the loop is this cycle, not the gate list alone:

```
CI fails
    |
    v
Copy the failure output
    |
    v
Feed it back: "CI failed with this error: [paste]. Fix the issue and verify locally
before pushing again."
    |
    v
Agent fixes -> pushes -> CI runs again
```

Key patterns:

```
Lint failure  -> run the fixer (`lint --fix` or equivalent), commit
Type error    -> read the error location, fix the type, don't silence it
Test failure  -> follow the systematic debugging process, not a guess-and-check loop
Build error   -> check config and dependencies before touching source
```

A flaky test that gets re-run instead of fixed is a debt that compounds — it masks real failures
and trains everyone to distrust red CI.

## Deployment strategies

### Preview deployments

Every PR gets a preview deployment for manual verification before merge, where the platform
supports it (Vercel/Netlify/similar):

```yaml
deploy-preview:
  runs-on: ubuntu-latest
  if: github.event_name == 'pull_request'
  steps:
    - uses: actions/checkout@v4
    - name: Deploy preview
      run: npx vercel --token=${{ secrets.VERCEL_TOKEN }}
```

### Feature flags in CI

Flags decouple deployment from release — see `references/ship.md` for the full lifecycle. The CI
obligation is narrower but non-negotiable: **test both flag states in CI**, not just the one you
expect to ship. A flag that's only ever tested ON hides the OFF-path regression until someone flips
it back in an incident.

### Staged rollouts

```
PR merged to main
    |
    v
Staging deployment (auto)
    | manual verification
    v
Production deployment (manual trigger or auto after staging)
    |
    v
Monitor for errors (window per references/ship.md thresholds)
    |
    +-- Errors detected -> rollback
    +-- Clean -> done
```

Full staged-rollout sequence and the advance/hold/rollback thresholds: `references/ship.md`.

### Rollback workflow

Every deployment needs a way back that doesn't require redoing the deploy from memory:

```yaml
name: Rollback
on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to rollback to'
        required: true

jobs:
  rollback:
    runs-on: ubuntu-latest
    steps:
      - name: Rollback deployment
        run: |
          # Deploy the specified previous version
          npx vercel rollback ${{ inputs.version }}
```

The rollback *plan* (trigger conditions, steps, time budgets) is written before the deploy — see
the template in `references/ship.md`. This workflow is the mechanical trigger for that plan.

## Environment and secrets

```
.env.example       -> committed (template for developers)
.env                -> NOT committed (local development)
.env.test           -> committed (test environment, no real secrets)
CI secrets          -> GitHub Secrets / vault
Production secrets  -> deployment platform / vault
```

CI never holds production secrets. Use separate credentials for CI-only test infrastructure (a CI
Postgres container's password is still a secret worth keeping out of the YAML — bad habits in test
config become real leaks in production config).

## Automation beyond CI

**Dependency updates** — Dependabot or Renovate, scheduled, with a capped open-PR limit so updates
don't pile up unreviewed:

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: npm
    directory: /
    schedule:
      interval: weekly
    open-pull-requests-limit: 5
```

**Build Cop role.** Designate someone responsible for keeping CI green. When the build breaks, the
Build Cop's job is to fix or revert — not necessarily the person whose change caused it. This
prevents a broken build from sitting for hours while everyone assumes someone else is on it.

**Branch protection.** Required status checks (CI must pass), required review (Gate 2), no
force-push to the default branch.

## CI optimization ladder

Apply in order of impact once the pipeline exceeds roughly 10 minutes:

```
Slow CI pipeline?
+-- Cache dependencies (actions/cache, or setup-node's built-in cache)
+-- Run jobs in parallel (split lint/typecheck/test/build into separate jobs)
+-- Only run what changed (path filters — skip e2e for docs-only PRs)
+-- Matrix builds (shard the test suite across runners)
+-- Optimize the suite itself (move slow tests off the critical path, run on a schedule)
+-- Larger runners (GitHub-hosted large runners or self-hosted for CPU-heavy builds)
```

## Red flags

- No CI pipeline, or one that's red-by-default and ignored
- Tests disabled in CI to make the pipeline pass
- Production deploys with no staging verification
- No rollback mechanism
- Secrets committed in code or CI config instead of the secrets manager
- A flaky test re-run instead of fixed
- Long CI times with no optimization attempted

## Verify

- [ ] All quality gates present (lint, types, tests, build, audit) and none skippable
- [ ] Pipeline runs on every PR and on push to the default branch
- [ ] Failures block merge (branch protection configured)
- [ ] CI failures feed back into the build loop, not just a red X someone dismisses
- [ ] Secrets live in the secrets manager, not in code or workflow files
- [ ] Deployment has a rollback mechanism, and the rollback plan behind it exists
   (`references/ship.md`)
- [ ] Pipeline completes in a reasonable window for the test suite; if not, work the
   optimization ladder
