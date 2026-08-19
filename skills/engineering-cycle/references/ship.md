# Ship

Deploying a change to production, running a staged rollout, or writing the rollback plan for
either. Open this after `references/release.md` has versioned the change and before you deploy it.
Neither `product-studio` nor `workflow-init` covers this phase — the generated loop
(`docs/agent/CARD.md`) ends at PR merge, and this file is the structural gap behind that ending.

## Pre-launch checklist

Six sections, all green before deploy. Treat this as a gate, not a suggestion — a missing box is a
missing control, not a formality.

### Code quality
- [ ] Full suite passes (unit, integration, e2e where present)
- [ ] Build succeeds with no **new** warnings beyond the recorded baseline (a repository that already carries warnings is not a reason to skip the check, and is not a reason to block on someone else's debt)
- [ ] Lint and type checking pass
- [ ] Gate 2 (review) is APPROVE, not a bypassed REQUEST-CHANGES
- [ ] No debug logging or `console.log`/`print` left in the shipped path
- [ ] Error handling covers the failure modes named in the behavior spec

### Security
- [ ] No secrets in code or version control
- [ ] Dependency audit shows no critical/high vulnerabilities
- [ ] Input validation on every new user-facing entry point
- [ ] Auth/authz checks in place for the touched surface
- [ ] Details: `references/security.md`

### Performance
- [ ] No newly introduced N+1 queries or unbounded loops in a hot path
- [ ] Any stated performance budget still holds
- [ ] Details: `references/performance.md`

### Infrastructure
- [ ] Environment variables and config set in production
- [ ] Migrations applied or ready to apply, with a tested rollback
- [ ] Health check endpoint exists and responds
- [ ] Logging and error reporting configured — verified per `references/observability.md`

### Documentation
- [ ] `docs/agent/BEHAVIORS.md` reflects what shipped
- [ ] ADRs written for architectural decisions made along the way (`references/adr.md`)
- [ ] Changelog entry written (`references/release.md`)

### Rollback readiness
- [ ] Rollback plan exists and is written *before* the deploy, not drafted during an incident
- [ ] Time-to-rollback budget stated for every rollback path (see template below)
- [ ] Rollback mechanism tested or dry-run where the deploy target allows it

Full detail-level checklist: `references/checklists/observability-checklist.md` for the
instrumentation half of this list.

## Feature-flag lifecycle

Flags decouple *deploying* code from *releasing* it. A flag with no owner or expiration is a future
`docs/agent/GOTCHAS.md` entry waiting to happen.

```
1. DEPLOY with flag OFF     -> code is in production, inactive
2. ENABLE for team/beta     -> internal use in the real environment
3. CANARY (5%)              -> first exposure to real users
4. GRADUAL (25% -> 50% -> 100%)
5. FULL rollout             -> flag ON for everyone
6. REMOVE the flag          -> delete the flag and the dead code path
```

Step 6 is not optional and is not "later." A flag left in place after full rollout is a silent
second code path nobody is testing. Rules:

- Every flag has an owner and an expiration date, set when the flag is created.
- Clean up within two weeks of reaching full rollout.
- Don't nest flags — the combinations become untestable.
- Test both flag states in CI, not just the one you expect to ship.

## Staged rollout sequence

```
1. STAGING           full suite + manual smoke test of critical flows
2. PRODUCTION, flag OFF   verify deploy succeeded, check health check + error monitor
3. TEAM/BETA, flag ON     24-hour monitoring window
4. CANARY, flag ON 5%     24-48 hour window, canary vs. baseline comparison
5. GRADUAL 25% -> 50% -> 100%   same monitoring at each step, can drop back a step at any point
6. FULL, flag ON 100%     monitor 1 week, then remove the flag
```

Advance only when the current stage clears the thresholds below. Do not skip a stage because the
previous one "looked fine" after ten minutes — the monitoring windows are the point.

### Rollout decision thresholds

| Metric | Advance (green) | Hold and investigate (yellow) | Roll back (red) |
|---|---|---|---|
| Error rate | Within 10% of baseline | 10-100% above baseline | >2x baseline |
| P95 latency | Within 20% of baseline | 20-50% above baseline | >50% above baseline |
| Client errors | No new error types | New errors at <0.1% of sessions | New errors at >0.1% of sessions |
| Business metrics | Neutral or positive | Decline <5% (may be noise) | Decline >5% |

These numbers are the default, not the truth about your system. Where the service has its own SLO
or a recorded baseline, that governs and this table is what you use until one exists.

Roll back immediately, without waiting out the window, on: error rate >2x baseline, P95 latency
>50% above baseline, a spike in user-reported issues, a data integrity problem, or a discovered
security vulnerability.

## Rollback plan template

Write this before the deploy. It is part of the pre-launch checklist, not a follow-up task.

```markdown
## Rollback plan for [feature/release]

### Trigger conditions
- Error rate > 2x baseline
- P95 latency > [X]ms
- User reports of [specific issue]

### Rollback steps
1. Disable the feature flag (if applicable) — OR —
1. Deploy the previous version / revert the commit
2. Verify: health check green, error monitor back to baseline
3. Communicate: notify the team a rollback happened and why

### Database considerations
- Migration [X] rollback path: [command or "none — forward-fix only"]
- Data written by the new path: [preserved / cleaned up]

### Time-to-rollback budget
- Feature flag flip: < 1 minute
- Redeploy previous version: < 5 minutes
- Database rollback: < 15 minutes
```

A rollback path with no stated time budget is not a plan yet — it's an intention.

<!-- stack: apple -->
## Mobile reality: rollout on a native app is not a load-balancer percentage

Everything above describes a server-side deploy. On iOS, most of it does not translate directly,
and following it literally will produce a plan that is wrong the day you need it.

- **You cannot roll back a shipped binary.** Once a build is live on the App Store, there is no
  "redeploy the previous version" step — Apple does not let you un-release a version users already
  downloaded. Rolling back means one of two things: roll *forward* with an expedited-review build
  that reverts the change, or **flag it off** server-side. If a change has no server-side kill
  switch, it has no fast rollback path — treat that as a pre-launch blocker, not an acceptable gap.
- **Staged rollout means App Store phased release**, not a percentage at your load balancer. Phased
  release ships to 1% of new/updated installs on day one, then steps up over roughly a week
  (1% -> 2% -> 5% -> 10% -> 20% -> 50% -> 100%), controlled by App Store Connect, not by you in
  real time. You can pause a phased release from Connect, which stops the percentage from climbing
  further — but everyone already on the build stays on it. Pausing is not rollback.
- **The kill switch is the actual rollback mechanism.** Any risky behavior shipped in a native
  build should be gated by a server-side flag (remote config, a feature-flag service, or even a
  simple "is this feature enabled" endpoint) so you can disable it without waiting on App Store
  review. A native change with no flag and no server dependency to gate it is a change you can only
  "roll back" by shipping a new build and waiting for review — budget days, not minutes.
- **Time-to-rollback budgets change accordingly:** flag flip stays <1 minute (if the flag exists);
  "redeploy previous version" becomes "submit an expedited-review build" — budget 24-48 hours even
  with Apple's expedited review, and there is no guarantee of approval speed.
- **Post-launch monitoring still applies** — crash rate, MetricKit signals, and business metrics
  per version — but you're watching a rollout percentage you don't control minute-to-minute, so the
  monitoring window is measured in days, not the 24-48 hours assumed above for a web canary.

## Post-launch verification, first hour

Against the questions written down in `references/observability.md` step 1 — not a generic list.

```
1. Health check returns 200 (or platform-appropriate equivalent)
2. Error monitor: no new error types
3. Latency dashboard: no regression
4. Manually exercise the critical user flow
5. Confirm logs/telemetry are flowing and readable
6. Confirm the rollback mechanism is actually ready (dry run if the platform allows it)
```

A deploy nobody checked in the first hour is a deploy nobody knows the state of.

## Verify

- [ ] Pre-launch checklist cleared, all six sections
- [ ] Feature flag configured with owner + expiration (if applicable)
- [ ] Rollback plan written and attached to the release, before deploy
- [ ] First-hour verification run and recorded
- [ ] Flag removal scheduled, not left open-ended
