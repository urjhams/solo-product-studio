# Performance

Open this when something is measurably slow, a stated budget is at risk, or you're about to touch
a hot path speculatively. The workflow below is the stack-neutral spine — it holds whether the hot
path is a React render, a Postgres query, or a SwiftUI list row. Stack-specific anti-patterns
follow it, marked. The Apple section at the end is a pointer, not a tutorial: SwiftUI performance
work has its own dedicated skills, and applying a web remedy to a launch stall or a render hitch
wastes the fix.

## The optimization workflow

```
1. MEASURE  -> Establish a baseline with real data
2. IDENTIFY -> Find the actual bottleneck, not the assumed one
3. FIX      -> Address that specific bottleneck, one change at a time
4. VERIFY   -> Re-measure; keep or revert
5. GUARD    -> Budget + CI check so it can't silently regress
```

Never skip to step 3. An optimization with no step-1 baseline is a guess wearing a diff.

### 1. Measure

Two complementary approaches, use both:

- **Synthetic** — controlled conditions, reproducible. Best for CI regression gates and isolating
  a specific issue.
- **Real-user data** — real conditions, required to confirm a fix actually moved the number users
  feel, not just the number you generated.

Which tool leads depends on the stack; see the marked sections below.

### 2. Identify the bottleneck

Profile before guessing. "It's probably the database" and "it's probably re-rendering" are both
hypotheses, not findings — the profiler tells you which one is true this time.

### 3. Fix one thing at a time

Three optimizations landed together produce one number you cannot attribute. If they must ship
together, measure each in isolation first, then land them together once each is proven.

### 4. Verify — keep or revert

A fix is a hypothesis until you re-measure. This step decides whether it survives.

- **Re-measure the way you measured the baseline** — same command, same conditions, same fixed
  budget (wall-clock, sample count, request count). A cold-cache baseline against a warm-cache
  result measures the cache, not your change.
- **Beat the noise, not just the mean.** Repeat the measurement and compare the delta against
  run-to-run variance. A 3% gain inside ±5% variance is a different sample, not a win.
- **Correctness gates the metric.** The suite stays green *and* the number moves. An
  "optimization" that wins by dropping work the product needed — skipping validation, caching
  something that must be fresh, removing a load-bearing `await` — is a regression, not a win.

| Result vs. baseline | Action |
|---|---|
| Past the threshold, tests green | **Keep.** Commit with the before/after numbers in the message. |
| Within noise (no measurable change) | **Revert.** |
| Worse | **Revert.** |
| Improved, but a test went red | **Revert.** A regression wearing a win's clothing. |

**"Neutral" is a revert, not a keep.** This is the step teams skip: the change is already written,
throwing it away feels wasteful, so it lands unmeasured, and the codebase accretes complexity that
never bought anything. Code you keep, you maintain forever — make it pay for itself.

#### Log every attempt, including the reverted ones

Reverted work leaves no trace in git history, which is exactly why the same dead idea gets tried
again next quarter.

| Idea | Baseline -> Result | Verdict | Why |
|---|---|---|---|
| Memoize the row component | INP 240ms -> 235ms | reverted | Inside noise (±15ms) |
| Virtualize the list | INP 240ms -> 90ms | kept | Long tasks gone from the trace |
| Preconnect to the API origin | LCP 2.8s -> 2.8s | reverted | Already same-origin |

Keep this in the PR description or a `PERF.md` in the repo. What matters is that the next agent
reads it before proposing an experiment, and doesn't re-run one that already failed.

### 5. Guard — budgets enforced in CI

State a budget for the surface you're changing, and enforce it as a build failure, not a
dashboard nobody checks. A budget that only lives in a doc erodes the first time someone is in a
hurry.

<!-- stack: web -->
## Web and frontend specifics

**Core Web Vitals thresholds:**

| Metric | Good | Needs improvement | Poor |
|---|---|---|---|
| LCP (Largest Contentful Paint) | ≤ 2.5s | ≤ 4.0s | > 4.0s |
| INP (Interaction to Next Paint) | ≤ 200ms | ≤ 500ms | > 500ms |
| CLS (Cumulative Layout Shift) | ≤ 0.1 | ≤ 0.25 | > 0.25 |

**Where to look, by symptom:**

| Symptom | Likely cause | Check |
|---|---|---|
| Slow LCP | Large images, render-blocking resources, slow server | Network waterfall, image sizes |
| High CLS | Images without dimensions, late-loading content, font shifts | Layout shift attribution |
| Poor INP | Heavy main-thread JS, large DOM updates | Long tasks (>50ms) in a Performance trace |
| Slow initial load | Large bundle, many requests | Bundle size, code splitting |

Capture the trace with `references/browser-verification.md`.

**Common fixes:**

- **Unnecessary re-renders (React)** — stabilize prop references (`const DEFAULT = {...} as const`
  instead of an inline object literal), `React.memo` on expensive leaf components, `useMemo` for
  expensive derived values. Overusing both is as bad as underusing — profile before adding either.
- **Large bundles** — dynamic `import()` for heavy, rarely-used features; route-level code
  splitting behind `Suspense`. Modern bundlers tree-shake named imports automatically for ESM
  dependencies marked `sideEffects: false` — the real win comes from splitting, not import style.
- **Images** — explicit `width`/`height` to prevent CLS, `srcset`/`sizes` for resolution
  switching, modern formats (AVIF/WebP), `loading="lazy"` below the fold, `fetchpriority="high"`
  on the LCP image only.
- **Caching** — HTTP `Cache-Control` with content-hashed filenames for static assets;
  short-TTL in-memory cache for frequently-read, rarely-changed data.

Budgets to enforce in CI: JS bundle < 200KB gzipped (initial load), CSS < 50KB gzipped, above-fold
images < 200KB each, Lighthouse Performance score ≥ 90.

<!-- stack: backend -->
## Backend and query specifics

| Symptom | Likely cause | Check |
|---|---|---|
| Slow API responses | N+1 queries, missing indexes, unoptimized queries | Database query log |
| Memory growth | Leaked references, unbounded caches, large payloads | Heap snapshot |
| CPU spikes | Synchronous heavy computation, regex backtracking | CPU profile |
| High, intermittent latency | Lock contention, GC pauses, external dependency | Trace the request through the stack |

**N+1 queries** — replace a per-row fetch loop with a single query using a join or an `include`.
Reaching for the ORM's owner/child lookup inside a `for` loop over a list is the single most
common performance bug in this category.

**Unbounded fetching** — every list endpoint takes a page size and an offset/cursor and returns a
bounded result set. `findMany()` with no `take` is a query that works until the table grows.

**Caching** — cache frequently-read, rarely-changed data with a stated TTL; set `Cache-Control` on
API responses that tolerate staleness.

Budget: API response time < 200ms (p95) is a reasonable default absent a stated SLA — state one.

<!-- stack: apple -->
## Apple platforms — use the dedicated skills

Everything above is web/backend-shaped. Don't apply it to a SwiftUI hitch or a launch-time
regression — the diagnosis tools and the fixes are different, and the workflow (measure, identify,
fix, verify, guard) stays the same but the toolset underneath it changes completely. The layered
division of labor:

| Question | Skill |
|---|---|
| Where's the evidence — trace, signpost, hang, hitch? | `ios-performance-profiling` |
| Is this on the launch path (pre-main, dyld, App startup)? | `ios-launch-performance` |
| Is a SwiftUI view invalidating or re-rendering too often? | `swiftui-performance` |
| Is a Task, actor hop, or `@MainActor` bottleneck the cause? | `swift-concurrency-performance` |
| Is the cost in allocation, ARC traffic, or dispatch? | `swift-runtime-performance` |
| Is the product *feels* slow even though nothing is technically wrong? | `ios-perceived-performance` |

Open the one that matches the symptom; do not read all six for one hitch. The keep/revert
discipline and the attempt ledger above still apply once you're inside those skills — only the
measurement tool and the fix vocabulary change.

## Verify

- [ ] Before-and-after measurements exist, with specific numbers
- [ ] Re-measured the same way as the baseline
- [ ] Improvement exceeds run-to-run variance, not just the mean
- [ ] Changes that didn't beat the baseline were reverted, not kept as neutral
- [ ] Attempts are logged — kept and reverted alike — so a dead idea isn't re-run
- [ ] Existing tests still pass
- [ ] Stated budget, if any, still holds and is enforced in CI

Full tickable list: `references/checklists/performance-checklist.md`.
