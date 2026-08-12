# Observability

Adding logging, metrics, tracing, or alerting to a feature that will run in production, or
reviewing a diff that adds I/O, retries, queues, or a cross-service call. Open this while building
the feature, not after it ships — telemetry retrofitted during an incident is telemetry you did not
have during the incident.

Code you can't observe is code you can't operate. Observability answers "what is the system doing
and why?" from the outside, using only the telemetry the code emits.

Not for: diagnosing a failure happening right now (`references/doubt.md` and the debugging
workflow), or profiling measured slowness (`references/performance.md`). This file covers what
feeds both of those the next time.

## The 7-step process

### 1. Define "working" before instrumenting

Telemetry without a question is noise. Before writing any instrumentation, write 2-4 questions an
on-call engineer will ask about this feature at 3am:

```
FEATURE: checkout payment retry
QUESTIONS ON-CALL WILL ASK:
1. What fraction of payments succeed on first attempt vs. after retry?
2. When a payment fails permanently, why? (provider error? timeout? validation?)
3. Is the payment provider slower than usual?
-> Every signal below must help answer one of these.
```

If you can't name the questions, you're not ready to instrument — you'll log everything and learn
nothing. This is the strongest idea in this file; the other six steps are mechanics.

### 2. Pick the right signal for each question

| Signal | Answers | Cost profile |
|---|---|---|
| Structured log | "What happened in this specific case?" | Per-event; grows with traffic |
| Metric | "How often / how fast, in aggregate?" | Fixed per series; cheap to query |
| Trace | "Where did time go across services?" | Per-request; usually sampled |

Metrics tell you *that* something is wrong, traces tell you *where*, logs tell you *why*.

### 3. Structured logging

Log events, not prose — a stable event name plus machine-readable fields:

```typescript
// BAD: string interpolation — unqueryable, inconsistent
logger.info(`Payment ${id} failed for user ${userId} after ${n} retries`);

// GOOD: stable event name + structured fields
logger.warn({
  event: 'payment_failed',
  paymentId: id,
  provider: 'stripe',
  errorCode: err.code,
  attempt: n,
}, 'payment failed');
```

Log levels, used consistently:

| Level | Meaning | On-call action |
|---|---|---|
| `error` | Invariant broken; someone may need to act | Investigate |
| `warn` | Degraded but handled (retry succeeded, fallback used) | Watch for trends |
| `info` | Significant business event | None |
| `debug` | Diagnostic detail | Off in production by default |

**Correlation IDs are mandatory.** Generate or accept a request ID at the system boundary and
attach it to every log line, span, and outbound call — without it you cannot reconstruct a single
request from interleaved logs.

```typescript
app.use((req, res, next) => {
  req.id = req.headers['x-request-id'] ?? crypto.randomUUID();
  req.log = logger.child({ requestId: req.id });
  res.setHeader('x-request-id', req.id);
  next();
});
```

**Never log secrets, tokens, passwords, or full PII.** Allowlist fields; don't log whole request
bodies. See `references/security.md` for the rest of the data-handling rules.

### 4. Metrics: RED and USE, percentiles never averages

Instrument **RED** on every endpoint and every external dependency: Rate, Errors, Duration
(histogram, not average). For resources (queues, pools, hosts), use **USE**: Utilization,
Saturation, Errors.

```typescript
import { Histogram } from 'prom-client';

const httpDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration',
  labelNames: ['method', 'route', 'status_class'],  // '2xx', not '200'
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
});
```

**Cardinality is the failure mode.** Every unique label combination is a separate time series.
Labels come from small, fixed sets only.

```
OK as label:    route="/api/tasks/:id"   status_class="5xx"   provider="stripe"
NEVER a label:  user_id, email, request_id, full URL, error message text
```

Track averages never, percentiles always — an average hides the 1% of users having a terrible
time. Histograms, and read p50/p95/p99.

### 5. Distributed tracing

Use OpenTelemetry — vendor-neutral, and auto-instrumentation covers HTTP, gRPC, and common DB
clients near-zero-code. Add manual spans only around meaningful internal units of work
(`applyDiscounts`, `chargeProvider`) with the attributes on-call will filter by. Propagate context
across every async boundary — HTTP headers, queue message metadata — or the trace dies at the gap.
Sample head-based at a low rate by default; keep 100% of errors if the backend supports tail
sampling.

### 6. Alerting: symptoms, not causes, two severities only

```
SYMPTOM (page-worthy):           CAUSE (dashboard, not a page):
error rate > 1% for 5 min        CPU at 85%
p99 latency > 2s                 one pod restarted
queue age > 10 min               disk at 70%
```

Cause-based alerts fire when nothing is wrong and miss failures you didn't predict. Symptom-based
alerts fire exactly when users are hurt, regardless of cause.

Rules for every alert:
1. It must be actionable — if the response is "ignore it, self-heals", delete the alert.
2. It links to a runbook, even three lines: what it means, first query to run, escalation path.
3. Threshold and duration are justified by an SLO or historical data, not a guess.
4. Two severities only: **page** (user-facing, act now) and **ticket** (degradation, act this
   week). A third tier becomes noise that trains people to ignore everything.

### 7. Verify the telemetry itself

Instrumentation is code; it can be wrong. Before calling this step done, trigger the paths and look
at the actual output:

- Force an error in staging -> find it in the logs by `requestId`, confirm fields are structured
  (not `[object Object]`)
- Send test traffic -> confirm metric series appear with expected labels and sane values
- Follow one request across services in the tracing UI -> no broken spans
- Fire each new alert once (lower the threshold temporarily) -> confirm it reaches the right
  channel and the runbook link works

## Red flags

- A diff with retries, queues, or external calls and zero new telemetry
- Log lines built by string interpolation instead of structured fields
- No correlation/request ID — each log line is an orphan
- Metrics labeled with user IDs, raw URLs, or error message text (cardinality bomb)
- Latency tracked as an average with no percentiles
- Alerts that fire daily and get acknowledged without action
- Alerts on causes (CPU, memory) paging humans while user-facing error rate is unmonitored
- Secrets, tokens, or full request bodies appearing in logs

## Verify

- [ ] The 2-4 on-call questions for this feature are written down, and every signal maps to one
- [ ] All log output is structured, with stable event names and a correlation ID on every line
- [ ] No secrets, tokens, or unredacted PII in any log line (spot-check actual output)
- [ ] RED metrics exist for every new endpoint and every external dependency, bounded label sets
- [ ] Latency is a histogram; p95/p99 are queryable
- [ ] A single request can be followed end-to-end in the tracing UI without broken spans
- [ ] Every new alert is symptom-based, has a runbook link, and was test-fired once
- [ ] An induced failure in staging was located via telemetry alone, without reading the source

Tickable pre-ship version of this list: `references/checklists/observability-checklist.md`.
