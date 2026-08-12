# Observability checklist

Pre-ship gate for any change that adds I/O, retries, queues, a new endpoint, or a cross-service
call. Run through this before the change clears `references/ship.md`'s pre-launch checklist —
it's the tickable form of what `references/observability.md` argues for at length. If a box can't
be checked, the change isn't ready to ship, not a note for later.

## Before instrumenting

- [ ] The 2-4 questions on-call will ask about this feature are written down somewhere durable
      (the PR description, an ADR, or the ticket) — not just in someone's head
- [ ] Every signal added below traces back to one of those questions

## Logging

- [ ] Every new log line is structured (JSON fields), not string interpolation
- [ ] Every log line carries a stable `event` name
- [ ] A correlation/request ID is attached at the boundary and propagated through every downstream
      call this feature makes
- [ ] Log level matches severity: `error` = invariant broken, `warn` = degraded-but-handled,
      `info` = business event, `debug` = off in production
- [ ] No secrets, tokens, passwords, or unredacted PII in any new log line — spot-checked against
      actual output, not assumed from the code

## Metrics

- [ ] RED metrics (Rate, Errors, Duration) exist for every new endpoint
- [ ] RED metrics exist for every new external dependency call
- [ ] USE metrics (Utilization, Saturation, Errors) exist for any new resource (queue, pool, worker)
- [ ] Duration is a histogram, never a bare average
- [ ] p95 and p99 are queryable, not just p50
- [ ] Every metric label comes from a small, fixed set — no user IDs, raw URLs, or error-message
      text as labels

## Tracing

- [ ] The feature's request path is covered by auto-instrumentation or manual spans around each
      meaningful unit of work
- [ ] Context propagates across every async boundary this feature introduces (HTTP headers, queue
      message metadata) — no broken spans
- [ ] Sampling rate is set deliberately (low head-based by default, errors kept if the backend
      supports tail sampling), not left at a framework default nobody chose

## Alerting

- [ ] Every new alert fires on a symptom users feel (error rate, latency, queue age), not a cause
      (CPU, one pod restarting)
- [ ] Every new alert has exactly one severity: **page** or **ticket** — no third tier
- [ ] Every new alert links to a runbook, even a three-line one
- [ ] Every new alert's threshold is justified by an SLO or historical data, written down, not a
      guess
- [ ] Every new alert was test-fired once (temporarily lowered threshold) to confirm it reaches the
      right channel

## Verify the telemetry itself

- [ ] An error was forced in staging and located in the logs by correlation ID, with structured
      fields intact (not `[object Object]`)
- [ ] Test traffic was sent and the expected metric series appeared with sane values
- [ ] One request was followed end-to-end in the tracing UI with no broken spans
- [ ] Each new alert reached the right channel when test-fired, and its runbook link resolves

## Gate

- [ ] All boxes above are checked, or the gap is named explicitly as an accepted risk in the PR —
      not silently skipped
