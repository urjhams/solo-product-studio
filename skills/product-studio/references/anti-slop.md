# Anti-slop guardrails

Adapted from "All Code Is Slop (Except Mine)" by Lauren Tan. Read this before scaffolding a project
whose compiled profile says `engineering.guardrails: standard` or `strict`, and before upgrading an
existing repo to that standard. It does not apply when the level is `off`.

Why it exists: an agent treats the codebase as its source of truth, so every anti-pattern, dead
branch and noisy comment present today is copied tomorrow, and a rule written in prose is skimmed.
The fix is to clean the input, replace prose with checks that fail, and make the wrong code hard to write.

## Where it applies

| `engineering.guardrails` | Modes (default) | What the scaffold installs |
|---|---|---|
| `off` | prototype, hackathon | Nothing. No linter, no ban list, no size cap. `workflow-init --modules guardrails` refuses. The safety floor still holds. |
| `standard` | indie, saas, startup, custom | Lint with hazard bans, an empty debt ratchet, an instruction-file cap of 100 lines, a golden-reference pointer, lint in the CI ladder. |
| `strict` | production | Standard plus tighter size and complexity limits, property-based tests on pure logic, state-machine tests on critical flows, a command-query-separation reviewer axis. A high risk tier cannot run with guardrails off. |

A demo is not asked to carry machinery it will never maintain. A product that will be maintained for
years is asked for it on day one, when it costs nothing, rather than as a rescue later.

## The five rules

1. **The codebase is the context.** Keep it clean: one folder convention, no duplicated logic, no dead code.
   Comments say *why* (a non-obvious business rule, a workaround), never *what*; names carry the rest.
   Name one or two **golden reference files** (small, pass every check, one clear responsibility) in the
   instruction file as the copy targets for new modules.
2. **Checks over prompts.** Keep `AGENTS.md` under 100 lines: architecture, commands, core conventions.
   Every formatting, naming, import and architecture rule becomes a linter rule, a formatter setting or a
   type-check, and every project-specific mistake gets a custom rule that bans it. A rule an agent can
   break without a failing command does not exist.
3. **A pit of success.** Separate commands (mutate) from queries (return data); no hidden side effects.
   Small pure units with typed inputs and outputs, capped by a file-length limit so growth forces a split.
   Ban hazardous patterns by name (unsafe casts, force unwraps, legacy APIs, `any`) in the linter config.
4. **Verification is most of the work.** A test for every logic change. Standard: example tests.
   Strict: property-based tests for transformations (idempotence, round trip, order independence, never
   crashes on arbitrary input) and a state-machine test for each critical flow (legal transitions only, no
   dead end). The agent runs lint, types and tests itself, reads the failures, and fixes until green.
5. **Order of work on an existing repo:** audit the top three to five weaknesses with numbers; add the
   guardrails with today's debt recorded, not fixed; then pay it down in small PRs that each stay green.

## Ratchet, not baseline

Record existing violations per rule in a committed file. A count may fall, never rise; a fall must be
recorded so it cannot come back. This works with any linter, needs no baseline feature, and a stale
entry fails loudly. Ceiling: moving a violation to another file keeps the count, so review still reads
the diff. Greenfield projects start with an empty ratchet, which means zero tolerance.

## Scaffolding

`workflow-init --modules guardrails --stack <stack>` copies the stack's lint config and `scripts/check.sh`
into the project. A stack has a template only once a real repository has run it, so unlisted stacks
get this document and nothing else; add the template after the first project proves it. Today: Swift.
The CI ladder runs `scripts/check.sh` whenever it exists, and the fast single-job stub never does.
