# Host capabilities

The Markdown rules in this bundle are portable. The mechanisms that *enforce* them are not, and pretending otherwise is how a rule quietly becomes a suggestion on a host that cannot run it.

Every rule this bundle generates carries one of three labels. `references/workflow-profile.md` assigns them per rule; this file says what each one costs on each host.

- **enforced** — a bundled Python script exits non-zero. Portable everywhere `python3` runs, which is every supported host.
- **ci-enforced** — a generated GitHub Actions workflow or a Claude Code hook fails. Needs that specific mechanism to exist.
- **advisory** — prose. The agent may follow it. Nothing checks.

## Matrix

| Mechanism | Claude Code | Codex | OpenCode | Generic Agent Skills |
|---|---|---|---|---|
| Slash entry (`/product-studio`) | yes | yes | if enabled | natural language |
| `SKILL.md` progressive disclosure | yes | yes | yes | yes |
| Bundled validators and the runner | yes | yes | yes | yes |
| Fresh-context independent reviewer | subagents | varies | varies | often absent |
| Session-card injection (`docs/agent/CARD.md`) | SessionStart hook | no | no | no |
| Verdict gate, behavior-coverage grep | hooks | no | no | no |
| GitHub Actions review lane | yes, with a repo | yes, with a repo | yes, with a repo | yes, with a repo |
| Web research for idea validation | host tool | host tool | host tool | may be absent |

## The one that changes a gate

`review.independent_required` is unsatisfiable on a host with no fresh-context primitive. That is not a degraded version of the rule — it is the rule not running. The runner already has the honest outcome for this: the phase records `self_review_only` and stays unapproved rather than being silently cleared. Say so to the user when it happens; do not let a missing primitive read as a passed review.

Where hooks are absent, the card, the verdict gate, and the coverage check become instructions the agent may follow rather than gates that block. Move what matters into CI, which every host with a repository can run, and label the rest advisory. `workflow-init` records the resulting label per generated rule so the repository states its own enforcement level rather than implying one.

## Fallbacks

When a capability is missing, record its status and the selected fallback under `capabilities` in `.product-studio/project.json` and continue. Never claim a provider was used unless its adapter actually succeeded — the same rule that governs Mobbin, web research, and XcodeBuildMCP in `references/adapters.md`.
