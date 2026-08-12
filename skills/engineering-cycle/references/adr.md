# Architecture Decision Records

`docs/agent/CARD.md` step 2 says an architectural decision — new dependency, new boundary,
rejecting a plausible alternative — gets recorded "(ADR or equivalent)" in the same task, with no
mechanism supplied. This is the mechanism: when one is required, where it lives, what it contains,
and how it ages.

## When an ADR is required

Any of:

- A new dependency (framework, library, service) enters the project
- A new boundary is drawn (module split, service split, API architecture: REST vs. GraphQL vs. tRPC)
- A plausible alternative is being rejected, not just the obviously-wrong one
- The decision would be expensive to reverse (data model, auth strategy, hosting/infra choice)

If none of these apply, a comment or a `STATE.md` line is enough — not every choice needs an ADR.

## Match the existing convention first

Before creating anything, check the repository for an established convention: existing ADRs, an
`.adr-dir` file, a MADR layout, or project instructions that name one. An established convention
overrides everything below it. Match:

- **Location and format** — `docs/adr/*.md`, `Documentation/Decisions/*.rst`, an `adr-tools` setup.
  Match the existing directory, extension, and markup.
- **Numbering and naming** — continue the existing sequence and filename pattern
  (`ADR-004-Title.rst`, `0004-title.md`, …). Don't restart at 001 or introduce a second scheme.
- **Section headings** — reuse the project's heading set instead of imposing the template below.

If the evidence conflicts — two competing conventions already in the repo — surface the conflict as
an `AM-###` (class: `term`) rather than silently picking one. Only apply the default below when no
convention can be established at all.

## Default template

Absent an existing convention, store ADRs in `docs/decisions/` with sequential numbering:

```markdown
# ADR-001: Use PostgreSQL for primary database

## Status
Proposed | Accepted | Superseded by ADR-XXX | Deprecated

## Date
2026-08-12

## Context
Requirements and constraints that made this decision necessary — what forced the choice, not just
what was chosen.

## Decision
The decision, stated plainly, one or two sentences.

## Alternatives Considered

### Alternative A
- Pros:
- Cons:
- Rejected because:

### Alternative B
- Pros:
- Cons:
- Rejected because:

## Consequences
What this commits the project to, including the costs — new operational burden, a skill the team
needs, a door this closes.
```

## Lifecycle

```
PROPOSED → ACCEPTED → (SUPERSEDED or DEPRECATED)
```

- **Don't delete old ADRs.** They're historical context — the record of why the current shape isn't
  the first one tried.
- When a decision changes, write a **new** ADR that references and supersedes the old one. Update
  the old one's `Status` line to point at the new number; leave its content intact.

## Tie to the ambiguity register

When an `AM-###` in `docs/agent/BEHAVIORS.md`'s ambiguity register resolves to `resolved -> D-###`,
the ADR is where `D-###` lives in full — context, decision, alternatives, consequences. The register
entry cites the ADR file; it doesn't restate the reasoning. If the resolution doesn't rise to the
"when an ADR is required" bar above, the register entry's own decision line is the record and no
separate file is needed.
