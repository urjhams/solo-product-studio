# Performance Checklist

Tickable detail behind `references/performance.md`, and one of the six sections gating
`references/ship.md`'s pre-launch checklist. Run it before marking a performance change done, and
before a release that touches a hot path.

## Before you start

- [ ] Baseline measured with real data, not assumed from reading the code
- [ ] Bottleneck identified from profiling data, not guessed from the symptom alone
- [ ] A budget exists for the surface being changed (or this checklist is the first time one is
      being set)

## Every optimization attempt

- [ ] Re-measured the same way as the baseline — same command, same conditions, same fixed budget
- [ ] Change isolated — one optimization measured at a time, even if several ship together
- [ ] Improvement exceeds run-to-run variance, not just the mean
- [ ] Correctness suite still green — a win that required a test to change, skip, or delete is a
      regression
- [ ] Neutral or worse result reverted, not kept — "it doesn't hurt" is not a keep criterion
- [ ] Attempt logged in the PR description or `PERF.md`, kept and reverted alike

<!-- stack: web -->
## Web

- [ ] LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1 (Core Web Vitals "Good" thresholds)
- [ ] No unnecessary re-renders introduced — `React.memo`/`useMemo` added only where profiling
      showed the cost, not by default
- [ ] Bundle size within budget; any new heavy dependency is code-split or lazy-loaded
- [ ] Images are dimensioned (no CLS), modern format, lazy-loaded below the fold
- [ ] Long tasks (>50ms) checked in a Performance trace — `references/browser-verification.md`
- [ ] Lighthouse Performance score ≥ 90, or the stated project budget

<!-- stack: backend -->
## Backend

- [ ] No N+1 query patterns in new data-fetching code
- [ ] List endpoints paginated — no unbounded `findMany()`/`SELECT *` equivalent
- [ ] Indexes exist for any new query pattern introduced
- [ ] Caching applied where data is read often and changes rarely, with a stated TTL
- [ ] p95 API response time within budget (default 200ms absent a stated SLA)

<!-- stack: apple -->
## Apple

- [ ] Evidence gathered via Instruments/signposts before any fix landed — `ios-performance-profiling`
- [ ] Launch-path changes checked against a launch budget — `ios-launch-performance`
- [ ] SwiftUI churn checked for unstable identity or overly broad state dependencies —
      `swiftui-performance`
- [ ] Concurrency changes checked for actor hops and `@MainActor` load — `swift-concurrency-performance`
- [ ] Allocation-heavy code checked for ARC traffic and existential overhead — `swift-runtime-performance`
- [ ] User-perceived latency checked, not just the technical trace — `ios-perceived-performance`

## Guard

- [ ] Performance budget stated for this surface, in writing
- [ ] Budget enforced in CI as a failing check, not a dashboard someone might glance at
- [ ] Monitoring or an alert exists to catch a future regression, not just this one
