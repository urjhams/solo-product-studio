---
name: workflow-init
description: Use when starting a new project or repo that has no agent workflow yet, when the user asks to "set up the workflow", "init the workflow", "bootstrap agent docs/memory bank", or wants the standard CARD/RUNBOOKS/STATE/GOTCHAS + evaluator/reviewer/hook setup generated into the current project.
---

# workflow-init

Generates a proven agent workflow into the current project: memory bank (STATE/GOTCHAS/BEHAVIORS/
archive), session card + runbooks (Specify sweep, delegation tiers, quota discipline, PR gates),
subagent definitions (task-evaluator, per-area reviewers), Claude Code hooks (card injection,
behavior coverage, verdict gate), and a CI stub. The scaffold script does the copying; you do the
judgment.

The generated loop is **Specify → Red → Green → Refactor**, not bare test-first: behaviors get
written and swept for ambiguity before any test exists, because a suite over a misread requirement
is green and proves nothing. `docs/agent/BEHAVIORS.md` is where those behaviors live, and the
`behavior-spec/v1` marker on its line 2 is a shared format contract with the `product-studio`
skill — that skill writes the same file, so a project using both gets one specification, not two.

## Procedure

0. **Read `.product-studio/project.json` if it exists.** Its `workflow_profile` block is the
   compiled result of an intake that already happened — it answers most of step 2, and re-asking
   what it decided is how a four-hour demo ends up with a production workflow. No file, or no
   `workflow_profile` in it → run step 2 as written. This skill stays usable standalone; the
   profile is an input it prefers, not one it requires.

   | profile field | what it decides here |
   |---|---|
   | `testing.ci_required` | whether `ci` is in `--modules`; `init.sh` then picks the full ladder over the stub |
   | `review.independent_required` | the review-lane question — `false` means no reviewer lane and no `ci-review` |
   | `review.lane` | the lane itself, already chosen — `offline`, `online` (adds `ci-review`), or `none`. Set → do not re-ask |
   | `development.merge_policy` | the `{{MERGE_POLICY}}` and `{{MERGE_POLICY_TEXT}}` fills — `never`, `ask`, or `auto_on_approve` |
   | `development.pull_request_required` | the `{{PR_POLICY}}` fill, and whether `claude-code` (the verdict hook) is worth installing |
   | `planning.spec_gate` | CARD step 2 — `warn` makes the ambiguity rule advisory instead of blocking |
   | `risk_tier` | whether `engineering` is included, and whether the security and observability checklists are optional |
   | `delivery_target` | CI triggers, and whether a release section belongs in the generated docs at all |
   | `safety_floor` and `revisit_when` | the `{{MODE_POLICY}}` fill |

   Pass the path explicitly with `init.sh --profile <file>` when the state lives outside `--dest`.

1. **Detect before asking.** In the target project root check: git repo? existing
   `AGENTS.md`/`CLAUDE.md`/`docs/agent/` (never overwrite — the script skips existing files;
   note collisions to the user)? Stack markers: `package.json`, `pyproject.toml`/`requirements*.txt`,
   `*.xcodeproj`, `build.gradle*`, `go.mod`, `Cargo.toml`. Derive per-stack build + test commands
   from the project itself (scripts in `package.json`, Makefile targets…), not from memory. Note the
   test directories too (`tests/`, `test/`, `spec/`, `src/**/__tests__/`, `*Tests/`) — the behavior
   coverage hook greps them.

2. **Three questions, one call** (AskUserQuestion). Skip any the user already answered.
   - *Modules* (multiSelect): `core` (docs, always recommended), `agents`,
     `claude-code` (hooks + settings), `ci` (build+test workflow) — plus confirmation of the
     detected stacks.
   - *Review lane*: **offline** — the reviewer is a local subagent you spawn on the PR HEAD; or
     **online** — the review runs in GitHub Actions on the PR and posts itself. Online adds the
     `ci-review` module (needs an `ANTHROPIC_API_KEY` repo secret, and a GitHub remote). Both
     lanes keep the local `task-evaluator` gate before the PR is opened, and both keep `agents`.
     `review.lane` in the profile already answers this — ask only when there is none.
   - *Merge policy*: who merges the PR once the review closes. **`never`** — the agent never
     merges, you do. **`ask`** — the agent may run `gh pr merge` but it raises a permission
     prompt every time. **`auto_on_approve`** — the agent merges itself once a review marker for
     that exact HEAD says APPROVE. `development.merge_policy` in the profile already answers this;
     a high-risk profile compiles to `never` and no answer here reopens it. Default `ask`.
     This is the one question whose answer lets a session run PR → review → merge unattended, so
     ask it explicitly rather than inferring it from how autonomous the rest of the setup looks.
   - *Engineering depth*: `engineering` copies the reference set from the sibling
     `engineering-cycle` skill into `docs/engineering/` — the review axes, security, the build
     loop, planning, ADRs, observability, release, CI, shipping, migration, and the checklists.
     Add `engineering-web` only when the project has a browser frontend; it is the one whole-file
     web-only reference and it is inert without the `chrome-devtools` MCP server. Decline both for
     a repo that only wants the memory bank and the gates.

     The copy is deliberate. Pointing at the skill would make every scaffolded repo depend on this
     bundle staying installed, and the generated docs are repo-relative precisely so they do not.
     Sections inside those files carry `<!-- stack: … -->` markers; those are reader hints, not a
     build step — selection is per file, so nothing is ever silently dropped from inside one.

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
   - `{{TEST_DIRS}}` — **space-separated dir paths**, not an alternation and not a glob, e.g.
     `tests src/__tests__`. The coverage hook runs `grep -r` over them for each active `BH-###`, so
     a wrong value silently passes every PR. Leave it empty only when the project has no test tree
     yet; the hook then skips the check.
   - `{{DEFAULT_BRANCH}}` — from `git symbolic-ref refs/remotes/origin/HEAD` or ask
   - `{{REVIEWER_MAP}}` — offline lane only: one line per area,
     `` `<paths>` → `<area>-reviewer` `` (it lives inside the offline `{{REVIEW_LANE_STEPS}}` text)
   - `{{REVIEW_LANE}}` (CARD step 11) and `{{REVIEW_LANE_STEPS}}` (RUNBOOKS Gate 2, steps 2–3) —
     paste the block for the lane chosen in step 2, verbatim, from "Review-lane fills" below.
   - `{{PR_POLICY}}` (AGENTS.md, CARD step 10) and `{{MODE_POLICY}}` (AGENTS.md) — paste from
     "Profile fills" below. With no profile, use the durable fill; it is today's behavior.
   - `{{MERGE_POLICY}}` — the bare enum value (`never` / `ask` / `auto_on_approve`), in the hook's
     config block and the RUNBOOKS Merge section. `{{MERGE_POLICY_TEXT}}` (AGENTS.md) and
     `{{MERGE_POLICY_LINE}}` (CARD step 13) — paste from "Merge-policy fills" below.
   - `{{QA_SURFACE}}`, `{{QA_TOOLS}}`, `{{QA_RUN_CMD}}`, `{{QA_TOOLING}}` — the QA agent, step 5.

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

   **Profile fills.** Copy one; do not paraphrase.

   *Durable* (`development.pull_request_required: true`, or no profile) — `{{PR_POLICY}}`:
   ```
   **Finishing a task = opening its PR** — skipping the PR is what needs an explicit ask.
   ```
   *Fast* (`pull_request_required: false` — Prototype, Hackathon) — `{{PR_POLICY}}`:
   ```
   **Git is a recovery mechanism here, not a review gate.** Commit often so a bad ten minutes
   costs ten minutes; a PR is optional unless the team's own workflow needs one.
   ```

   `{{MODE_POLICY}}` — write the block from the profile, or delete the placeholder when there is
   no profile:
   ```
   ## Operating mode

   Mode: <mode> · risk tier: <risk_tier> · delivery target: <delivery_target>

   Non-negotiable regardless of timebox — these are the safety floor and nothing removes them:
   - <one line per safety_floor entry>

   Revisit this mode when: <revisit_when>
   ```

   *Online* — `{{REVIEW_LANE_STEPS}}`:
   ```
   2. **The review runs in Actions** — `.github/workflows/claude-review.yml`, on PR open and on
      every push. Do not spawn a local reviewer; it would duplicate the run and the quota.
   3. **Wait for it and read its comment** (`gh pr checks --watch`, then `gh pr view <n> --comments`).
      Workflow failed (missing secret, quota, timeout) → say so and fall back to spawning the
      matching `<area>-reviewer` locally for this PR.
   ```

   **Merge-policy fills.** Copy the pair matching the policy; do not paraphrase. `{{MERGE_POLICY}}`
   is the bare enum value in both the hook and the RUNBOOKS Merge section. The `auto_on_approve`
   text carries a nested `{{PROJECT_SLUG}}` — paste the fill first, substitute after, or step 6's
   grep is the only thing between you and a placeholder shipped verbatim.

   *`never`* — `{{MERGE_POLICY_TEXT}}`:
   ```
   **You never merge.** Say the PR is ready and stop; the hook blocks `gh pr merge` outright.
   `gh pr merge --admin` is never an option — branch protection is there by intent.
   ```
   *`never`* — `{{MERGE_POLICY_LINE}}`:
   ```
   not yours. Report the PR as ready and stop.
   ```

   *`ask`* — `{{MERGE_POLICY_TEXT}}`:
   ```
   **Merge only when the task said to.** `gh pr merge` is not pre-approved, so it raises a
   permission prompt — but the prompt is a backstop, not the decision: no "the PR looks good so I
   merged it". `gh pr merge --admin` is never an option and the hook blocks it — branch protection
   is there by intent.
   ```
   *`ask`* — `{{MERGE_POLICY_LINE}}`:
   ```
   only when the task said to merge. It prompts; the prompt is a backstop, not permission.
   ```

   *`auto_on_approve`* — `{{MERGE_POLICY_TEXT}}`:
   ```
   **Merge once the review approves.** The hook requires an `APPROVE` marker at
   `/tmp/{{PROJECT_SLUG}}-verdicts/<HEAD sha>.review`, written by the reviewer that actually read
   that HEAD — never write one for a commit nobody reviewed. Gate 2 closed and CI green are still
   yours to confirm; the hook checks the marker, not the pipeline. `gh pr merge --admin` is never
   an option and the hook blocks it — branch protection is there by intent.
   ```
   *`auto_on_approve`* — `{{MERGE_POLICY_LINE}}`:
   ```
   allowed once the HEAD's review marker says APPROVE, Gate 2 is closed, and CI is green.
   ```

5. **Instantiate the agents** (agents module). Fill every field with **static** content only — no
   dates, run IDs, or current-state prose: an agent definition is the cached prefix every spawn of
   that type reuses, and one changed byte invalidates it.

   - **Reviewers**: copy `.claude/agents/_platform-reviewer.template.md` once per component to
     `.claude/agents/<area>-reviewer.md`, filling `{{AREA}}`, `{{AREA_STACK}}`, `{{AREA_PATHS}}`,
     `{{AREA_STANDARDS_DOC}}`, `{{PROJECT_SLUG}}`. Delete the template copy after.
   - **QA agent**: rename `.claude/agents/_qa-agent.template.md` to `.claude/agents/qa-agent.md`
     and fill `{{QA_SURFACE}}`, `{{QA_TOOLS}}`, `{{QA_RUN_CMD}}`, `{{QA_TOOLING}}`,
     `{{PROJECT_SLUG}}` from the stack you detected in step 1 — this is Gate 3's agent, and the
     reason it is a template is that "run the app and look at it" means something different per
     platform:

     | Surface | `{{QA_RUN_CMD}}` | `{{QA_TOOLING}}` |
     |---|---|---|
     | Apple (iOS/macOS) | the scheme + simulator build/run | XcodeBuildMCP — `build_run_sim`, `screenshot`, `snapshot_ui`, `tap`/`type_text`; `sim_statusbar` for clean captures |
     | Web frontend | the dev-server command | the `chrome-devtools` MCP server; `docs/engineering/browser-verification.md` when the `engineering-web` module is installed |
     | Android | the emulator install/launch command | `adb shell` + `adb exec-out screencap`, plus whatever the project already scripts |
     | CLI / backend | the run or serve command | `curl` transcripts, structured log lines, and the project's own smoke script |

     `{{QA_TOOLS}}` is the frontmatter `tools:` line, and it is the one field that decides whether
     the agent can do what the body tells it to: an MCP tool the list omits is a tool the agent
     cannot call. Start from `Read, Grep, Glob, Bash` — never add `Write`, `Edit`, or `NotebookEdit`,
     because read-only is what makes QA evidence rather than a second author — and append the MCP
     tool names for the surface. Apple: the `mcp__XcodeBuildMCP__*` tools you named above. Web: the
     `chrome-devtools` server's tools. Android and CLI need nothing beyond `Bash`. Name each tool
     in full; a wildcard is not a tools-list entry.

     A repo with no user-visible surface has no Gate 3: delete the template instead of filling it,
     and say so in the report.

6. **Verify**: `grep -rn '{{[A-Z_]*}}'` over the generated files returns nothing;
   `bash -n .claude/hooks/*.sh` passes. Report the generated file list, the collisions skipped,
   and the manual follow-ups: hooks activate next session; `.claude/settings.json` was
   skipped if one existed — merge the hooks/permissions blocks by hand, and drop any pre-existing
   `Bash(gh pr merge:*)` allow entry or the `ask` policy silently stops prompting; **online lane
   only** — `gh secret set ANTHROPIC_API_KEY`, or the review workflow fails on every PR.
   Sanity-check the merge gate before reporting done:
   `echo '{"tool_input":{"command":"gh pr merge 1"}}' | bash .claude/hooks/require-verdict.sh`
   — expect a block under `never`, silence under `ask`.

## Design notes (why the generated workflow looks like this)

- **Quota discipline is the default**: lowest-tier subagents, read-only fan-out at the smallest
  tier, writers serialized, no-spawn default, docs-only diffs skip the evaluator. Baked into the
  generated RUNBOOKS — don't soften it when filling placeholders.
- **The review flow is owned by the project**, in one of two lanes — a local reviewer subagent, or
  the repo's own Actions workflow. Neither depends on a third-party review bot, and both end the
  same way: triage every finding → fix → push → post resolutions, one bounded re-review.
- **The profile decides which rules apply; it never weakens the ones that do.** A fast mode drops
  the independent reviewer and the CI ladder. It does not drop the safety floor, input validation,
  or secret hygiene — those are constant across every mode by construction.
- **A rule with no mechanism is a suggestion**: the card is hook-injected, the evaluator verdict
  is hook-enforced, the merge is gated on a sha-pinned review marker, the STATE cap is measured in
  bytes, and behavior coverage is a grep. Keep mechanisms when adapting.
- **Merging is the one action the agent takes on the user's behalf**, so it is a compiled policy
  rather than a paragraph, and `gh pr merge` is deliberately absent from the allow list: `ask`
  works precisely because the permission prompt fires. `auto_on_approve` is opt-in, unavailable at
  a high risk tier, and still needs a review it did not write itself — the same shape as the
  evaluator verdict, so there is one mechanism to understand rather than two.
- **Behaviors are addressed, not described.** `BH-###` ids are what make coverage checkable by
  machine: a behavior no test names is a gap, a test that names no behavior is an orphan likely
  encoding a misread requirement. Prose acceptance criteria cannot be grepped, which is why the
  generated loop puts ids in test names. Only `Status: active` behaviors are enforced, so parking
  work as `planned` or `deferred` is the intended escape hatch — not deleting the behavior.
