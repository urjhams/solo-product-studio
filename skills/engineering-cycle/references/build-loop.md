# Build Loop

The sequence is `docs/agent/CARD.md`: Branch → Specify → Red → Green → Refactor → Commit → docs →
STATE → Gate → PR → Review. This doc does not restate it. It supplies what the CARD doesn't have
room for — the stack-discovery step it assumes, the slicing judgment behind "smallest change," and
the test craft behind Red and Green.

## Discover the stack first

The loop is universal; the commands are not. Before the first Red, find out how *this* repository
builds and tests, and use its commands for every Red, Green, and verification step — never assume a
default.

- **Language and build system** — `package.json`, `pom.xml`/`build.gradle`, `pyproject.toml`,
  `go.mod`, `Cargo.toml`, `Gemfile`, a `Makefile`.
- **Checked-in wrappers, preferred over globally installed tools** — `./gradlew`, `./mvnw`,
  `make test`, `swift test`, `xcodebuild test`, `pytest`.
- **How to run one focused test vs. the full suite** — both get used: focused during the loop, full
  before a gate.
- **Existing conventions** — where tests live, naming, what neighboring tests do.
- **Documented commands** — README, CONTRIBUTING, CI workflows show what actually gates merges.

`npm test` is not a safe default. A Gradle, Cargo, or pytest project has its own equivalent, and
guessing wrong either burns a cycle on a command that doesn't exist or, worse, silently runs nothing.
`{{TEST_CMD}}` and `{{BUILD_CMD}}` in the CARD are this discovery, already resolved for the current
repository — if they're unset or wrong, fix that before anything else.

## Slice direction

"Smallest change that passes," from the CARD's Green step, still needs a direction to move in:

- **Vertical** (default) — one complete path through the stack per slice: schema + API + UI for one
  user-visible capability. Each slice is independently working and testable.
- **Contract-first** — when two sides need to build in parallel, define the shared contract (types,
  interface, API shape) as its own slice first, then build both sides against it.
- **Risk-first** — when one piece is genuinely uncertain (a new integration, a protocol nobody on
  the team has used), prove that piece before building anything that depends on it. If it fails, it
  fails before the dependent slices exist.

**The test-then-implement anti-pattern:** writing all the tests for a feature, then all the
implementation. It feels efficient but the tests get written against an imagined shape of the
behavior rather than a proven one — by the time Green happens for the last test, the earlier ones
may already be testing the wrong contract. One behavior, Red then Green then Refactor, then the
next.

This is a different failure from the *horizontal slicing* `references/planning.md` warns about.
That one is about task decomposition across layers — all the database, then all the API, then all
the UI. This one is about ordering within a single slice. Both leave you with unproven work in
flight; they are not the same mistake, and a slice can hit one without the other.

## Scope discipline

Touch what the task, brief, or `BH-###` names. Something adjacent that needs fixing is reported, not
fixed silently:

```
NOTICED BUT NOT TOUCHING:
- src/utils/format.ts has an unused import (unrelated to this task)
- The auth middleware could use better error messages (separate task)
→ Flag for a follow-up task, don't fix inline.
```

This applies to refactoring imports in files you're only reading, removing comments you don't fully
understand, and modernizing syntax in passing — all out of scope unless the task names them.

## Test craft

- **Pyramid proportions** — roughly 80% unit (small: single process, no I/O, milliseconds), 15%
  integration (medium: crosses a boundary — API, DB, filesystem — localhost only, seconds), 5% e2e
  (large: full user flow, real browser or staging, minutes). Pick the cheapest level that can
  actually fail when the behavior breaks — a unit test standing in for an integration behavior is
  tautological.
- **DAMP over DRY** — production code should avoid repetition; tests should not, if avoiding it
  costs readability. Each test should read as a complete specification without the reader tracing
  through shared setup.
- **Real > fake > stub > mock** — use the real implementation unless it's too slow, non-deterministic,
  or has side effects you can't control. Mock only at that boundary, and only for interaction
  verification you can't get any other way.
- **Arrange-Act-Assert** — set up state, perform the one action under test, assert the outcome. Keep
  the three visually distinct in every test.
- **One assertion per concept** — a test with three unrelated assertions is three tests wearing one
  name; when it fails, the name doesn't tell you which one broke.
- **Test state, not interactions** — assert on the outcome (`order.status === 'cancelled'`), not on
  which internal method got called. Interaction assertions break under refactors that don't change
  behavior.

Full patterns, examples, and the anti-pattern table: `references/checklists/testing-patterns.md`.

## Keep it buildable

- **Keep it compilable.** After every increment the project builds and existing tests pass. Don't
  leave the tree broken between slices, even briefly.
- **Feature flags for incomplete work.** If a slice needs to merge before the feature is
  user-ready, gate it off by default — `ENABLE_X` checked at the call site — rather than leaving
  half-built behavior reachable.
- **Safe defaults.** New parameters and new behavior default to the conservative option; users
  opt in, not out.
- **Rollback-friendly.** Additive changes (new files, new functions, new nullable columns) are easy
  to revert. Don't delete something and replace it in the same commit — separate them so either half
  can be reverted alone. Destructive schema changes get their own migration flow —
  `references/migration.md#expand-migrate-contract`.

## The prove-it pattern (bug fixes)

Don't start a bug fix by editing the fix. Start by writing the test that fails because of the bug:

```
Bug report arrives
   → write a test that reproduces it
   → test FAILS (confirms the bug exists, not a guess about it)
   → implement the fix
   → test PASSES
   → run the full suite (no regressions)
```

The reproduction test is written *before* the fix, from the bug report, without looking at the
eventual patch — that's what makes it a real disproof attempt rather than a test shaped to match
whatever the fix ends up being.

## Name the behavior

Every test names the `BH-###` it proves — in the test name or a comment directly above it. This is
what makes coverage greppable: `grep BH-014` finds every test proving that behavior, and a `BH-###`
in `BEHAVIORS.md` with no hits is an uncovered behavior, found the same way. An orphan test — proving
no `BH-###` — is either missing a citation or testing something nobody specified.
