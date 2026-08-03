---
name: workflow-init
description: Use when starting a new project or repo that has no agent workflow yet, when the user asks to "set up the workflow", "init the workflow", "bootstrap agent docs/memory bank", or wants the standard CARD/RUNBOOKS/STATE/GOTCHAS + evaluator/reviewer/hook setup generated into the current project.
---

# workflow-init

Generates a proven agent workflow into the current project: memory bank (STATE/GOTCHAS/archive),
session card + runbooks (delegation tiers, quota discipline, PR gates), subagent definitions
(task-evaluator, per-area reviewers), Claude Code hooks (card injection, verdict gate), and a CI
stub. The scaffold script does the copying; you do the judgment.

## Procedure

1. **Detect before asking.** In the target project root check: git repo? existing
   `AGENTS.md`/`CLAUDE.md`/`docs/agent/` (never overwrite — the script skips existing files;
   note collisions to the user)? Stack markers: `package.json`, `pyproject.toml`/`requirements*.txt`,
   `*.xcodeproj`, `build.gradle*`, `go.mod`, `Cargo.toml`. Derive per-stack build + test commands
   from the project itself (scripts in `package.json`, Makefile targets…), not from memory.

2. **One question only** (AskUserQuestion, multiSelect): which modules —
   `core` (docs, always recommended), `agents`, `claude-code` (hooks + settings), `ci` —
   plus confirmation of the detected stacks. Skip the question entirely if the user already said.

3. **Scaffold** (mechanical, zero tokens):
   `bash <this-skill-dir>/scripts/init.sh --dest <project-root> --modules <chosen>`
   The script is idempotent, records a sha256 manifest in `.workflow-init/manifest`, and
   `--uninstall` later removes only unmodified generated files. `--help` for flags.

4. **Fill placeholders** — every `{{…}}` the script's final grep lists:
   - `{{PROJECT_NAME}}`, `{{PROJECT_SLUG}}` (kebab-case, used for the verdict dir), `{{DATE}}`
   - `{{PROJECT_OVERVIEW}}`, `{{STACKS}}`, `{{SECRETS_NOTE}}`
   - `{{BUILD_CMD}}`, `{{TEST_CMD}}`, `{{BUILD_TEST_COMMANDS}}`, `{{STACK_SETUP}}` — the real
     commands you detected in step 1
   - `{{SOURCE_DIRS}}` (prose list) and `{{SOURCE_DIRS_RE}}` (alternation like `src|backend`) —
     the product-source dirs that trigger the heavy PR lane
   - `{{DEFAULT_BRANCH}}` — from `git symbolic-ref refs/remotes/origin/HEAD` or ask
   - `{{REVIEWER_MAP}}` — one line per area: `` `<paths>` → `<area>-reviewer` ``

5. **Instantiate reviewers** (agents module): copy
   `.claude/agents/_platform-reviewer.template.md` once per component to
   `.claude/agents/<area>-reviewer.md`, filling `{{AREA}}`, `{{AREA_STACK}}`, `{{AREA_PATHS}}`,
   `{{AREA_STANDARDS_DOC}}`. Delete the `_platform-reviewer.template.md` copy after. Fill these
   with **static** content only — no dates, run IDs, or current-state prose: an agent definition
   is the cached prefix every spawn of that type reuses, and one changed byte invalidates it.

6. **Verify**: `grep -rn '{{[A-Z_]*}}'` over the generated files returns nothing;
   `bash -n .claude/hooks/*.sh` passes. Report the generated file list, the collisions skipped,
   and the two manual follow-ups: hooks activate next session; `.claude/settings.json` was
   skipped if one existed — merge the hooks/permissions blocks by hand.

## Design notes (why the generated workflow looks like this)

- **Quota discipline is the default**: lowest-tier subagents, read-only fan-out at the smallest
  tier, writers serialized, no-spawn default, docs-only diffs skip the evaluator. Baked into the
  generated RUNBOOKS — don't soften it when filling placeholders.
- **Review flow is self-contained**: PR → auto-spawn own reviewer → post → fix → push. No
  dependency on external review bots.
- **A rule with no mechanism is a suggestion**: the card is hook-injected, the evaluator verdict
  is hook-enforced, the STATE cap is measured in bytes. Keep mechanisms when adapting.
