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

2. **Two questions, one call** (AskUserQuestion). Skip either if the user already said.
   - *Modules* (multiSelect): `core` (docs, always recommended), `agents`,
     `claude-code` (hooks + settings), `ci` (build+test workflow) — plus confirmation of the
     detected stacks.
   - *Review lane*: **offline** — the reviewer is a local subagent you spawn on the PR HEAD; or
     **online** — the review runs in GitHub Actions on the PR and posts itself. Online adds the
     `ci-review` module (needs an `ANTHROPIC_API_KEY` repo secret, and a GitHub remote). Both
     lanes keep the local `task-evaluator` gate before the PR is opened, and both keep `agents`.

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
   - `{{REVIEWER_MAP}}` — offline lane only: one line per area,
     `` `<paths>` → `<area>-reviewer` `` (it lives inside the offline `{{REVIEW_LANE_STEPS}}` text)
   - `{{REVIEW_LANE}}` (CARD step 9) and `{{REVIEW_LANE_STEPS}}` (RUNBOOKS Gate 2, steps 2–3) —
     paste the block for the lane chosen in step 2, verbatim, from "Review-lane fills" below.

   **Review-lane fills.** Copy one pair; do not paraphrase.

   *Offline* — `{{REVIEW_LANE}}`:
   ```
   spawn the matching `<area>-reviewer` on the PR's HEAD, post its review to the PR, triage
   every finding, apply valid fixes, run affected tests, commit + push, post resolutions.
   ```
   *Offline* — `{{REVIEW_LANE_STEPS}}`:
   ```
   2. **Auto-spawn the matching reviewer** on the PR's final HEAD, by changed path:
      {{REVIEWER_MAP}}
      Reviewers are read-only — they return review text; they never push or comment themselves.
   3. **Post the review** as a PR comment yourself (`gh pr comment <n> --body …`).
   ```

   *Online* — `{{REVIEW_LANE}}`:
   ```
   the `Claude review` workflow runs on the PR and posts its own comment — do NOT spawn a local
   reviewer. Wait for it (`gh pr checks --watch`), then triage every finding, apply valid fixes,
   run affected tests, commit + push, post resolutions.
   ```
   *Online* — `{{REVIEW_LANE_STEPS}}`:
   ```
   2. **The review runs in Actions** — `.github/workflows/claude-review.yml`, on PR open and on
      every push. Do not spawn a local reviewer; it would duplicate the run and the quota.
   3. **Wait for it and read its comment** (`gh pr checks --watch`, then `gh pr view <n> --comments`).
      Workflow failed (missing secret, quota, timeout) → say so and fall back to spawning the
      matching `<area>-reviewer` locally for this PR.
   ```

5. **Instantiate reviewers** (agents module): copy
   `.claude/agents/_platform-reviewer.template.md` once per component to
   `.claude/agents/<area>-reviewer.md`, filling `{{AREA}}`, `{{AREA_STACK}}`, `{{AREA_PATHS}}`,
   `{{AREA_STANDARDS_DOC}}`. Delete the `_platform-reviewer.template.md` copy after. Fill these
   with **static** content only — no dates, run IDs, or current-state prose: an agent definition
   is the cached prefix every spawn of that type reuses, and one changed byte invalidates it.

6. **Verify**: `grep -rn '{{[A-Z_]*}}'` over the generated files returns nothing;
   `bash -n .claude/hooks/*.sh` passes. Report the generated file list, the collisions skipped,
   and the manual follow-ups: hooks activate next session; `.claude/settings.json` was
   skipped if one existed — merge the hooks/permissions blocks by hand; **online lane only** —
   `gh secret set ANTHROPIC_API_KEY`, or the review workflow fails on every PR.

## Design notes (why the generated workflow looks like this)

- **Quota discipline is the default**: lowest-tier subagents, read-only fan-out at the smallest
  tier, writers serialized, no-spawn default, docs-only diffs skip the evaluator. Baked into the
  generated RUNBOOKS — don't soften it when filling placeholders.
- **The review flow is owned by the project**, in one of two lanes — a local reviewer subagent, or
  the repo's own Actions workflow. Neither depends on a third-party review bot, and both end the
  same way: triage every finding → fix → push → post resolutions, one bounded re-review.
- **A rule with no mechanism is a suggestion**: the card is hook-injected, the evaluator verdict
  is hook-enforced, the STATE cap is measured in bytes. Keep mechanisms when adapting.
