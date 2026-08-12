# Review

Depth behind Gate 2. The generated `<area>-reviewer` agent names these same six axes — it has to
state them inline, because an agent definition is the cached prefix every spawn reuses and cannot
depend on a file that may not exist in the target repo. What it has no room for is the detail:
what each axis actually checks, the severity taxonomy, how to size a change, and when a diff
should be split rather than reviewed. Open this when you are that reviewer, or standing in for
it, and a call is close.

## The six axes

**Judge Spec first.** It is the axis a clean-looking diff fails, and the only one bound to
`BH-###` ids — the order both the reviewer agent and `docs/agent/RUNBOOKS.md` use. The five below
it are ordered by how often they carry a blocker, not by importance.

### 1. Spec

Does the change do what the task or issue asked — no more, no less?

Where `docs/agent/BEHAVIORS.md` covers the diff, **a `BH-###` outranks the task prose.** Judge
against the behavior's Given/When/Then, not against a paraphrase of the ticket, and cite the id in
the finding. Two failure shapes are equally findings here:

- A behavior with no covering test — the acceptance criterion is unproven.
- **An orphan test** — a test that names no `BH-###` and asserts something no behavior asks for.
  It passed review at write time on vibes, and it will silently rot into "coverage" nobody can
  explain.

A behavior whose `AM-###` is still `Status: open` is not evaluable. Say so rather than guessing
which reading the code should have implemented. Scope creep belongs here too, not in the nits:
work the task did not ask for still has to be reviewed, tested, and maintained.

If the diff has no corresponding behaviors yet, that itself is a finding: route back to
`docs/agent/RUNBOOKS.md#specify` rather than reviewing against prose alone.

### 2. Correctness

Does the code do what it claims to?

- Does it match the spec or task requirements?
- Are edge cases handled (null, empty, boundary values)?
- Are error paths handled, not just the happy path?
- Do the tests actually test the right things, and do they pass?
- Off-by-one errors, race conditions, state inconsistencies?

### 3. Readability & Simplicity

Can another engineer, or agent, understand this without the author explaining it?

- Names descriptive and consistent with project convention — no `temp`, `data`, `result` without
  context.
- Control flow straightforward: no nested ternaries, no deep callback chains.
- **Could this be done in fewer lines?** A thousand lines where a hundred suffice is a failure.
- **Are abstractions earning their complexity?** Don't generalize until the third use case.
- Dead-code artifacts — unused variables, backwards-compat shims, `// removed` comments — are
  findings, not style.
- **A new conditional bolted onto an unrelated flow is a design smell, not a nit.** Push it into
  its own helper, state, or policy instead of tangling an existing path.
- **Repeated conditionals on the same shape signal a missing model or dispatcher.** A "temporary"
  branch is usually permanent debt.

### 4. Architecture

Does the change fit the system's design?

- Follows existing patterns, or justifies the new one.
- Clean module boundaries; no circular dependencies.
- **Does this refactor reduce complexity or just relocate it?** Count the concepts a reader must
  hold. If a "cleaner" version leaves that count unchanged, it isn't cleaner. Prefer the version
  that makes whole branches, modes, or layers disappear over one that re-centralizes the same
  logic. Prefer deleting an abstraction to polishing it.
- **Is feature-specific logic leaking into a shared or general-purpose module?** Keep logic in its
  owning layer; reuse the canonical helper instead of a near-duplicate.
- **Are type boundaries explicit?** Question gratuitous `any`/`unknown`/optional/casts and silent
  fallbacks that paper over an unclear invariant.

### 5. Security

Delegates to `references/security.md` — do not restate its content here, cite it. At review time,
check the surface, not the mechanism:

- Is user input validated and sanitized at the boundary it crosses?
- Are secrets kept out of code, logs, and version control?
- Is auth checked — not just "is the user logged in" but "is this the right user"?
- Are queries parameterized, outputs encoded, dependencies free of known reachable vulnerabilities?
- Is data from any external source — API, log, user content, config file, **LLM output** — treated
  as untrusted?

A finding on this axis with a plausible exploit path is a BLOCKER by default.

### 6. Performance

Delegates to `references/performance.md`. At review time, check for the patterns that don't need
a profiler to spot:

- N+1 query patterns.
- Unbounded loops or unconstrained data fetching.
- Synchronous work that should be async.
- Missing pagination on a list endpoint.
- Large objects allocated in a hot path.

## Severity

| Severity | Meaning | Author action |
|---|---|---|
| **BLOCKER** | Breaks correctness, security, the build, or an active `BH-###`'s acceptance criterion | Must fix before merge |
| **MAJOR** | Real structural, readability, or architecture problem; doesn't break anything today but will | Fix before merge unless the author states an explicit, logged trade-off |
| **MINOR** | Style, nit, optional suggestion, FYI | Author's call |

**Lead with what matters.** Order findings by leverage — correctness, security, and spec first,
then structural regressions and missed simplifications, then everything else. A few high-conviction
findings beat a long list. **If you have one structural problem and ten nits, the structural
problem is the review** — don't bury it.

## Structural Remedies

A finding that only names the problem leaves the author guessing. Reach for a named restructuring:

- **Replace a chain of conditionals** with a typed model or an explicit dispatcher.
- **Collapse duplicate branches** into a single clearer flow.
- **Separate orchestration from business logic** so each reads on its own.
- **Move feature-specific logic** out of a shared module into the package that owns the concept.
- **Reuse the canonical helper** instead of a bespoke near-duplicate.
- **Make a type boundary explicit** so downstream branching disappears.
- **Delete a pass-through wrapper** that adds indirection without clarifying the API.
- **Extract a helper, or split a large file** into focused modules.

Prefer the remedy that removes moving pieces over one that spreads the same complexity around.

## Change Sizing

```
~100 lines changed   → Good. Reviewable in one sitting.
~300 lines changed   → Acceptable if it's a single logical change.
~1000 lines changed  → Too large. Split it.
```

**Watch file size, not just diff size.** A small diff can still push a file past a healthy
boundary — around 1000 *total* lines in a single file is a common inspection signal, not a hard
cap. When a change materially grows an already-large file, ask whether to extract helpers,
subcomponents, or modules *first*. Decompose, then add.

**One change** is a single self-contained modification that addresses one thing, includes its
tests, and keeps the system functional after landing — one slice of a feature, not the whole
feature.

| Splitting strategy | How | When |
|---|---|---|
| **Stack** | Submit a small change, start the next one based on it | Sequential dependencies |
| **By file group** | Separate changes for groups needing different reviewers | Cross-cutting concerns |
| **Horizontal** | Shared code/stubs first, then consumers | Layered architecture |
| **Vertical** | Break into smaller full-stack slices | Feature work |

**When large is acceptable:** complete file deletions, and automated refactors where the reviewer
only needs to verify intent, not every line.

**Refactor and feature work are two changes**, submitted separately, even when the refactor was
what made the feature possible. Small mechanical cleanups (renames) can ride along at reviewer
discretion.

## Change Descriptions

**First line:** short, imperative, standalone — "Delete the FizzBuzz RPC," not "Deleting the
FizzBuzz RPC." Someone searching history should understand the change without opening the diff.

**Body:** what and why — context, decisions, and reasoning not visible in the code itself.
Acknowledge approach shortcomings when they exist.

**Anti-patterns:** "Fix bug," "Fix build," "Moving code from A to B," "Phase 1."

## Review Order

1. **Context** — what is this trying to accomplish, and against which `BH-###` or task?
2. **Tests first** — do they exist, do they test behavior rather than implementation, would they
   catch a regression, do they each name the behavior they prove?
3. **Implementation** — walk the six axes above, file by file.
4. **Verification story** — what was run, did the build pass, is there a screenshot for a
   user-visible change. "Looks right" is not a verification step.

## Honesty in Review

- **Don't rubber-stamp.** An approval with no evidence of review helps no one.
- **Don't soften a real issue.** "This might be a minor concern" on a bug that will hit production
  is dishonest.
- **Quantify when you can.** "This N+1 will add ~50ms per item in the list" beats "this could be
  slow."
- **Push back on approaches with clear problems.** Sycophancy is a failure mode in review. Say so,
  propose the alternative.
- **Accept override gracefully.** If the author has context you don't and disagrees, defer to their
  judgment — but log it (`docs/agent/GOTCHAS.md`) if the override later proves wrong.

## Handling Disagreements

1. Technical facts and data override opinions and preferences.
2. The repo's documented standards are the authority on style matters.
3. Design is judged on engineering principles, not personal taste.
4. Consistency with the surrounding codebase is acceptable grounds *only* if it doesn't degrade
   overall health.

**Don't accept "I'll clean it up later."** Deferred cleanup rarely happens. Require it before
merge unless it's a genuine emergency; if it's out of scope for this change, require a follow-up
issue with an owner.

## Dead Code Hygiene

Identify what a change orphaned, list it, and ask before deleting:

```
DEAD CODE IDENTIFIED:
- formatLegacyDate() in src/utils/date.ts — replaced by formatDate()
- LEGACY_API_URL constant in src/config.ts — no remaining references
→ Safe to remove these?
```

Don't leave it lying around — it confuses future readers and agents. Don't silently delete
something you're not sure about, either.

## Dependency-Upgrade Discipline

An upgrade is a code change, and bulk "bump deps" is the riskiest shape it comes in:

1. **Read the changelog, not just the version number.** Semver is a promise the maintainer may not
   have kept — a "patch" can carry a behavioral change. For a major bump, read the migration notes.
2. **One dependency per change.** A bulk bump that breaks the build hides which package did it; a
   single-package change makes the cause obvious and the revert clean.
3. **Let the tests decide.** Green suite before *and* after, not "it installed." Thin coverage
   around the dependency's behavior is itself a finding — add a test first.
4. **Mind the transitive graph.** Review the lockfile diff, not just the manifest; one direct bump
   can pull in dozens of indirect changes.
5. **Keep the lockfile honest.** Commit it, review its diff, never hand-edit it.

For triaging audit findings and supply-chain risk (typosquatting, compromised maintainers), that's
`references/security.md` — this section is the upgrade *workflow*, that one is the security
verdict.

## The Review Checklist

```markdown
## Review: [PR/change title]

### Context
- [ ] I understand what this change does and which BH-### or task it serves

### Correctness
- [ ] Matches spec/task requirements
- [ ] Edge cases and error paths handled
- [ ] Tests cover the change adequately

### Readability
- [ ] Names are clear and consistent
- [ ] No unnecessary complexity; no new conditional bolted onto an unrelated flow

### Architecture
- [ ] Follows existing patterns; refactors reduce complexity rather than relocate it
- [ ] No feature logic in shared modules; no file pushed past a healthy size unaddressed

### Security — see references/security.md
- [ ] Input validated at boundaries; no injection; auth checked; external data untrusted

### Performance — see references/performance.md
- [ ] No N+1, no unbounded operation, pagination present where needed

### Spec
- [ ] Every active BH-### touched by this diff has a covering test
- [ ] No orphan test — every new test names the behavior it proves

### Verification
- [ ] Tests pass, build succeeds, manual/visual verification attached where applicable

### Verdict
- [ ] path:line — severity (BLOCKER/MAJOR/MINOR) — problem — concrete fix
- [ ] **APPROVE** (no BLOCKERs) or **REQUEST-CHANGES** (list the blockers)
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It works, that's good enough" | Working code that's unreadable, insecure, or architecturally wrong creates debt that compounds. |
| "I wrote it, so I know it's correct" | Authors are blind to their own assumptions — that's the entire reason a second gate exists. |
| "We'll clean it up later" | Later never comes. The review is the quality gate. |
| "AI-generated code is probably fine" | It needs more scrutiny, not less — confident and plausible even when wrong. |
| "The tests pass, so it's good" | Tests don't catch architecture problems, security issues, or an orphan test asserting the wrong thing. |
| "The refactor makes it cleaner" | Relocating complexity isn't reducing it. Look for the version where branches disappear. |
| "It's just a version bump" | A bump is a behavior change you didn't write. Read the changelog. |

## Red Flags

- A diff merged with no covering `BH-###`, or a test that names none.
- Findings without severity labels — the author can't tell what's required.
- A large PR that's "too big to review properly" — split it, don't wave it through.
- No regression test alongside a bug fix.
- A refactor that moves code around without reducing the number of concepts a reader must hold.
- A bulk "bump dependencies" change with no changelog review and no per-package isolation.
- A lockfile change that's hand-edited, uncommitted, or merged without its diff reviewed.

## Verification

- [ ] Every BLOCKER resolved; every MAJOR resolved or explicitly deferred with a logged trade-off
- [ ] Tests pass, build succeeds
- [ ] Verification story documented — what changed, how it was checked
- [ ] Dependency upgrades reviewed against changelog, isolated per package, lockfile diff checked
