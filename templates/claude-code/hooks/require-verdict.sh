#!/bin/bash
# PreToolUse(Bash) hook: gate `gh pr create` behind an evaluator verdict, plus free mechanical
# checks. Rules with no mechanism behind them are suggestions — this is the mechanism.
#
# Heavy lane (diff touches SOURCE_DIRS): blocks `gh pr create` unless every active behavior has a
#   covering test, and unless /tmp/{{PROJECT_SLUG}}-verdicts/<full HEAD sha> exists and starts with
#   SHIP. Only task-evaluator writes that file, sha-pinned — a new commit invalidates it.
# Light lane (anything else): no evaluator needed; junk-file scan + STATE.md byte cap still run.
set -u

SOURCE_DIRS_RE='^({{SOURCE_DIRS_RE}})/'   # e.g. ^(src|backend|frontend)/
TEST_DIRS="{{TEST_DIRS}}"                 # space-separated, e.g. tests src/__tests__
VERDICT_DIR="/tmp/{{PROJECT_SLUG}}-verdicts"
STATE_FILE="docs/agent/STATE.md"
BEHAVIORS_FILE="docs/agent/BEHAVIORS.md"
STATE_SECTION_CAP=3000   # bytes for "## Current focus" — measure the thing you care about

input=$(cat)
if command -v jq >/dev/null 2>&1; then
  command=$(printf '%s' "$input" | jq -r '.tool_input.command // empty')
else
  # Fallback: stop at the first unescaped quote so a trailing "description" field
  # can't leak into the captured command and false-trigger the gate.
  command=$(printf '%s' "$input" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
fi

block() { printf '{"decision":"block","reason":"%s"}\n' "$1"; exit 0; }

# `gh pr merge --admin` bypasses branch protection — never allowed, no in-session override.
# A plain merge is allowed, so a session can chain PR -> review -> merge -> next task without
# stalling; whether to merge at all is governed by AGENTS.md (only when the task asked for it).
if printf '%s' "$command" | grep -qE '(^|&&|\|\||;)[[:space:]]*gh[[:space:]]+pr[[:space:]]+merge'; then
  printf '%s' "$command" | grep -qE '(^|[[:space:]])--admin([[:space:]=]|$)' \
    && block "gh pr merge --admin bypasses branch protection. Merge without --admin, or ask the user to merge in the GitHub UI."
  exit 0
fi

# Match `gh pr create` as a command target (start of string or after a shell operator),
# never as a prose mention inside a commit message or comment body.
printf '%s' "$command" | grep -qE '(^|&&|\|\||;)[[:space:]]*gh[[:space:]]+pr[[:space:]]+create' || exit 0

base=$(git merge-base HEAD "origin/{{DEFAULT_BRANCH}}" 2>/dev/null || echo "")
changed=$(git diff --name-only "${base:-HEAD~1}"...HEAD 2>/dev/null)

# Junk-file scan — free, both lanes.
junk=$(printf '%s\n' "$changed" | grep -E '\.(bak|orig|rej)$|~$' || true)
[ -n "$junk" ] && block "Junk files in diff: $(printf '%s' "$junk" | tr '\n' ' ')"

# STATE.md cap — bytes of the Current-focus section, not bullet count.
if [ -f "$STATE_FILE" ]; then
  bytes=$(awk '/^## Current focus/{f=1;next} /^## /{f=0} f' "$STATE_FILE" | wc -c | tr -d ' ')
  [ "$bytes" -gt "$STATE_SECTION_CAP" ] && block "STATE.md Current-focus is ${bytes}B > ${STATE_SECTION_CAP}B cap — run python3 scripts/agent/compact-state.py, commit both files, retry"
fi

# Lane split: docs/tooling-only diffs skip the evaluator gate.
printf '%s\n' "$changed" | grep -qE "$SOURCE_DIRS_RE" || exit 0

# Behavior coverage — every `Status: active` BH-### must be named by something under TEST_DIRS.
# A test that names no behavior is the evaluator's job to catch; this only catches the reverse.
# Skipped silently when the file is absent, so repos predating BEHAVIORS.md are unaffected.
test_roots=""
for dir in $TEST_DIRS; do
  [ -d "$dir" ] && test_roots="$test_roots $dir"
done
if [ -f "$BEHAVIORS_FILE" ] && [ -n "$test_roots" ]; then
  # sed strips <!-- --> blocks so the template's commented-out example never counts as a behavior
  active=$(sed '/<!--/,/-->/d' "$BEHAVIORS_FILE" | awk '
    /^## BH-[0-9]+/ { id = $2; next }
    /^#/            { id = ""; next }
    id != "" && /^- Status:[[:space:]]*active([[:space:]]|$)/ { print id; id = "" }
  ')
  missing=""
  for id in $active; do
    grep -rqF -- "$id" $test_roots 2>/dev/null || missing="$missing $id"
  done
  [ -n "$missing" ] && block "Active behaviors with no covering test:$missing — add a test naming each id, or change its Status in $BEHAVIORS_FILE (planned / deferred / out_of_scope)"
fi

sha=$(git rev-parse HEAD)
verdict_file="$VERDICT_DIR/$sha"
[ -f "$verdict_file" ] || block "No evaluator verdict for HEAD $sha — spawn task-evaluator first (heavy lane: diff touches product source)"
head -1 "$verdict_file" | grep -q '^SHIP' || block "Evaluator verdict for HEAD is not SHIP: $(head -1 "$verdict_file")"
exit 0
