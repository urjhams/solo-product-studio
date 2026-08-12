# Release

Cutting a release: choosing a semantic version bump, tagging, writing the changelog, or deciding
whether a change is breaking. Open this after the diff is merged and before it ships
(`references/ship.md` is the next step).

Commit, branch, and atomic-commit discipline already live in `docs/agent/CARD.md` (the loop) — this
file does not restate them. If you're looking for commit hygiene, branch naming, or the
save-point pattern, that's the CARD, not here.

## Why version at all

Commits are how *you* track change; a version is how your *consumers* track it. The moment anything
else depends on the code — another team, a published package, a deployed client — "latest on main"
stops answering "what am I running, and is it safe to upgrade?" A version number and a changelog
are the contract that answers it.

## Semantic versioning

For anything with consumers, version `MAJOR.MINOR.PATCH` and let the number carry meaning:

```
MAJOR  breaking change — consumers must change their code to upgrade
MINOR  new functionality, backward-compatible — safe to upgrade
PATCH  bug fix, backward-compatible — safe to upgrade
```

The number is a promise; make the code match it. A "patch" that changes behavior consumers relied
on is a major change wearing a disguise (Hyrum's Law — see `references/api.md`). When unsure
whether a change is breaking, assume it is: a surprise major is far cheaper than a broken consumer.

## The tag is the source of truth

A release is an immutable point in history, not a moving branch:

```bash
git tag -a v1.4.0 -m "Release 1.4.0"
git push origin v1.4.0
```

Derive the version from the tag rather than hand-editing it in scattered files (`package.json`,
build config, a version constant), so the artifact, the tag, and the changelog can never disagree.
A hand-edited version that drifts from the tag is a `docs/agent/GOTCHAS.md` entry waiting to
happen.

## Changelog, written for humans

A changelog is not `git log`. It's the curated, consumer-facing answer to "what changed and do I
care?" — grouped by `Added / Changed / Fixed / Deprecated / Removed / Security`, newest on top,
every entry phrased around user impact, not internal mechanics.

```markdown
## [1.4.0] - 2026-08-12
### Added
- Bulk task import via CSV
### Fixed
- Timezone drift in recurring task due dates
### Deprecated
- `GET /v1/tasks/all` — use the paginated `GET /v1/tasks` (removal in 2.0)
```

Write the entry in the same change that makes the change, while the impact is fresh — not
reconstructed from commit archaeology at release time. If `docs/agent/BEHAVIORS.md` changed, the
changelog entry is the user-facing translation of that `BH-###` diff, not a copy of it.

## Breaking changes get a migration note and a deprecation window

A breaking change is never just a major-version bump. It needs:

1. A migration note describing what consumers do to move off the old behavior — full detail in
   `references/migration.md`.
2. A deprecation window — the old path keeps working, marked deprecated, for a stated period before
   removal. The changelog's `Deprecated` entry and the eventual `Removed` entry are the same line
   item, one release apart.

Shipping the release itself — deploy, staged rollout, rollback plan — is `references/ship.md`'s
job. This file is the versioning contract that feeds it: by the time you open `ship.md`, the
version is decided, tagged, and the changelog entry is written.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "It's just a small fix, bump the patch" | Check what consumers can observe. A behavior change they relied on is a major, whatever the diff size. |
| "The changelog is just the commit log" | Commits are for you; the changelog is for consumers, curated by impact. A generated dump buries what matters. |
| "We'll write the changelog at release time" | By then the impact is reconstructed from memory and half of it is missing. Write the entry with the change. |

## Verify

- [ ] The version bump matches the change: breaking -> major, additive -> minor, fix -> patch
- [ ] The release is tagged, and the version is derived from the tag, not hand-edited out of sync
- [ ] The changelog has a curated, human-readable entry grouped by impact for this version
- [ ] Any breaking change has a migration note and a stated deprecation window
