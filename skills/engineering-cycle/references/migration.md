# Deprecation and Migration

How to remove an old system, API, or feature safely, and how to move users off it before it goes.
Open this when replacing something, sunsetting a feature, consolidating duplicate implementations,
or planning a schema change.

## Code is a liability

Every line has ongoing cost: tests, docs, security patches, dependency updates, mental overhead for
anyone working nearby. The value is the functionality, not the code. When the same functionality can
be delivered with less of it, the old code should go — but removal is harder than it looks, because:

**Hyrum's Law.** With enough users, every observable behavior becomes depended on — including bugs,
timing quirks, and undocumented side effects. Announcing a deprecation is not the same as making it
safe to remove. Migration has to be active, not advisory-and-hope.

**Plan the exit at design time.** When building something new, ask how it gets removed in three
years. Clean interfaces, feature flags, and minimal surface area make deprecation tractable later;
leaking implementation details everywhere makes it a project unto itself.

## The deprecation decision

Before deprecating anything:

1. Does this still provide unique value? If yes, maintain it, stop here.
2. How many consumers depend on it — quantify the migration scope.
3. Does a replacement exist? Don't deprecate without one; build it first.
4. What's the per-consumer migration cost? Trivially automated → do it. Manual and high-effort →
   weigh against the ongoing maintenance cost of not deprecating.
5. What's the cost of *not* deprecating — security risk, engineer time, complexity tax?

A decision to deprecate a system a team relies on is itself an architectural decision under
`references/adr.md` — new boundary, rejected alternative (keep maintaining it) — record it there.

## Compulsory vs. advisory

| Type | When | Mechanism |
|---|---|---|
| **Advisory** | Migration is optional, old system is stable | Warnings, docs, nudges. Users migrate on their own timeline. |
| **Compulsory** | Security issue, blocks progress, or maintenance cost is unsustainable | Hard deadline, migration tooling and support provided — not just an announcement. |

Default to advisory. Compulsory needs the maintenance cost or risk to justify forcing the move.

## The migration process

1. **Build the replacement first.** It must cover all critical use cases of the old system, have a
   migration guide, and be proven in production — not "theoretically better."
2. **Announce and document.** State: status, replacement, removal date (or "advisory, no deadline
   yet"), reason, and the concrete migration steps.
3. **Migrate incrementally, one consumer at a time.** For each: find every touchpoint, switch it to
   the replacement, verify behavior matches, remove the old reference, confirm no regression.
   **The churn rule** — if you own the system being deprecated, you own migrating its users, or you
   ship a backward-compatible path that needs no migration. Announcing and walking away isn't
   deprecation, it's abandonment.
4. **Remove the old system**, only once usage is verified at zero (metrics, logs, dependency
   search): the code, its tests, its docs, its config, and the deprecation notice itself.

## Migration patterns

**Strangler.** Run old and new in parallel; shift traffic incrementally (0% → canary → 50% → 100%);
remove the old system once it's idle.

**Adapter.** Wrap the new implementation behind the old interface so consumers don't have to change
at all while the backend migrates underneath them.

**Feature flag.** Switch individual consumers from old to new one at a time, keyed on user or
cohort, so a bad migration is a flag flip to revert, not a redeploy.

## Expand / migrate / contract (schema changes)
<!-- stack: backend -->

A schema change is the riskiest migration because data can't be rolled back by reverting a deploy.
The failure mode: renaming a column in the same release that starts reading the new name — during
the rollout window, old and new code run at once, and one of them queries a column that doesn't
exist. Fix: never change a column in place. Migrate in additive phases so old and new code are both
valid at every step.

```
EXPAND ──────────────→ MIGRATE ──────────────→ CONTRACT
add the new column,    backfill existing rows,  once no code reads the
nullable, alongside    dual-write old+new from  old column, drop it in
the old one            the app                  a later, separate deploy
```

**Worked example — renaming `name` to `full_name`:**

1. **Expand.** Add `full_name`, nullable. Deploy — old code ignores it, nothing breaks.
2. **Dual-write.** App writes both columns on every insert/update. Deploy.
3. **Backfill.** Copy `name → full_name` for existing rows, in batches, off the hot path.
4. **Switch reads.** Point the app at `full_name`, keep writing both. Deploy and bake.
5. **Contract.** Stop writing `name`; drop the column in a *separate, later* deploy.

Each step is independently deployable and reversible — if step 4 misbehaves, roll the code back and
`full_name` is still being populated. Treat each phase as its own vertical slice —
`references/build-loop.md#slice-direction`.

**Rules:**

- Additive first, destructive last and alone. Drops and renames get their own deploy, after nothing
  references the old shape.
- Every migration has a tested `down` path, run before merging — a migration you can't reverse is a
  deploy you can't roll back.
- Backfill in throttled batches, off the hot path — a single `UPDATE` over millions of rows locks
  the table.
- Build large indexes without blocking writes (e.g. `CREATE INDEX CONCURRENTLY`).
- Gate a risky cutover behind a feature flag, same as the Feature Flag pattern above.

## Zombie code

Code nobody owns but everybody depends on: no commits in 6+ months with active consumers, no
maintainer, failing tests nobody fixes, dependencies with known vulnerabilities nobody updates,
docs referencing systems that no longer exist. It cannot stay in limbo — either assign an owner and
maintain it, or deprecate it with a concrete plan.

## Red flags

- Deprecating something with no replacement built yet
- A deprecation notice with no migration tooling behind it
- "Advisory" that's been stalled for years with zero progress
- A schema change and the code depending on it shipped in the same deploy
- A column renamed or dropped in place instead of expand/contract
- A migration merged with no tested `down` path, or a backfill that locks the table
- Removing code without verifying zero active consumers first
