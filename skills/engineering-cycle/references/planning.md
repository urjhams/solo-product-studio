# Planning and Task Breakdown

How to turn a brief or a behavior set into small, ordered, checkable work. Open this when a task
feels too large to start, when the implementation order isn't obvious, or when work could be split
across parallel agents.

## Where the output goes

This does **not** produce a `tasks/plan.md` + `tasks/todo.md` pair. That convention exists upstream
to feed a `/build` command that is not part of this bundle, and adding it here would create a third
competing artifact location alongside `.product-studio/artifacts/` and `docs/agent/`. Use one of the
two locations this bundle already has:

- **Working from product-studio, upstream of implementation** — the plan lives in the MVP Build Plan
  (`templates/mvp-build-plan.md`): `critical_path`, `vertical_slices`, `cut_triggers`, and
  `definition_of_done` are the fields that carry dependency order, slicing, and scope guard. Fill
  those, don't invent a parallel file.
- **Working from an Implementation Brief or `docs/agent/BEHAVIORS.md` directly, no product-studio
  artifact** — the plan *is* the task ordering, cited by `BH-###`. Write it as a numbered list or a
  scratch note; it does not need a permanent home. The behaviors are already the source of truth for
  scope, so the plan's only job is sequencing them.

Everything below is technique for producing either of those, not a third file format.

## The dependency graph

Map what depends on what before ordering anything. Build foundations first — bottom-up:

```
Database schema
    │
    ├── API models/types
    │       │
    │       ├── API endpoints
    │       │       │
    │       │       └── Frontend API client
    │       │               │
    │       │               └── UI components
    │       │
    │       └── Validation logic
    │
    └── Seed data / migrations
```

## Slice vertically, not horizontally

Horizontal slicing — all the database, then all the API, then all the UI — leaves nothing working
until the last slice lands, and defers integration risk to the end:

```
Bad:  Task 1: entire database schema
      Task 2: all API endpoints
      Task 3: all UI components
      Task 4: connect everything

Good: Task 1: user can create an account (schema + API + UI for registration)
      Task 2: user can log in (auth schema + API + UI for login)
      Task 3: user can create a task (task schema + API + UI for creation)
      Task 4: user can view task list (query + API + UI for list view)
```

Each vertical slice delivers working, testable functionality end to end. Cut slices along
behaviors: a slice should map to one or a few `BH-###`, never to a layer.

## Task sizing

| Size | Files | Scope | Example |
|---|---|---|---|
| **XS** | 1 | Single function or config change | Add a validation rule |
| **S** | 1-2 | One component or endpoint | Add a new API endpoint |
| **M** | 3-5 | One feature slice | User registration flow |
| **L** | 5-8 | Multi-component feature | Search with filtering and pagination |
| **XL** | 8+ | **Too large — break it down further** | — |

Break a task down further when any of these is true:

- It would take more than one focused session (roughly 2+ hours of agent work)
- The acceptance criteria don't fit in 3 or fewer bullets
- It touches two or more independent subsystems (e.g. auth and billing)
- The title has "and" in it — a sign it is two tasks

An agent performs best on S and M tasks.

## Order and checkpoint

1. Satisfy dependencies — build foundation first.
2. Order high-risk tasks early. If a slice is going to fail, it should fail before three more slices
   are built on top of it.
3. Every task leaves the system in a working state — build and tests both green.
4. Checkpoint after every 2-3 tasks: full suite passes, build is clean, the core flow works
   end-to-end. This is also where a `docs/agent/STATE.md` bullet lands, per the CARD loop.

## Parallelization analysis

Before assuming work can run in parallel, classify it:

| Class | Examples |
|---|---|
| **Safe to parallelize** | Independent feature slices, tests for already-implemented behavior, documentation |
| **Must be sequential** | Database migrations, shared state changes, dependency chains |
| **Needs coordination** | Features that share an API contract — define the contract first (a slice of its own), then parallelize the two sides against it |

This feeds directly into wave decomposition at delegation time —
`references/checklists/orchestration-patterns.md`.

## Per-task shape

Whichever file the plan lives in, each task should carry:

```markdown
## Task N: <short title>

Description: one paragraph, what this accomplishes.

Acceptance criteria (cite the BH-### each one enforces):
- [ ] ... — BH-0NN

Verification:
- [ ] Tests pass: <repo's focused-test command>
- [ ] Build succeeds: <repo's build command>

Dependencies: <task numbers, or None>
Files likely touched: <paths>
Size: XS | S | M | L (never XL — break it down)
```

Acceptance criteria answer "did we build the right thing" for one task; the standing bar every task
clears regardless — `references/checklists/definition-of-done.md` — is separate and always applies.

## Red flags

- Starting implementation with no written ordering at all
- A task description that says "implement the feature" with no acceptance criteria
- Every task sized XL
- No checkpoints between phases
- Dependency order ignored — building the UI before the schema it reads exists
