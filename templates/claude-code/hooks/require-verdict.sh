#!/bin/bash
# PreToolUse(Bash) hook: gate `gh pr create` behind an evaluator verdict, plus free mechanical
# checks. Rules with no mechanism behind them are suggestions — this is the mechanism.
#
# Heavy lane (diff touches SOURCE_DIRS): blocks `gh pr create` unless
#   /tmp/{{PROJECT_SLUG}}-verdicts/<full HEAD sha> exists and starts with SHIP.
#   Only task-evaluator writes that file, sha-pinned — a new commit invalidates it.
# Light lane (anything else): no evaluator needed; junk-file scan + STATE.md byte cap still run.
set -u

SOURCE_DIRS_RE='^({{SOURCE_DIRS_RE}})/'   # e.g. ^(src|backend|frontend)/
VERDICT_DIR="/tmp/{{PROJECT_SLUG}}-verdicts"
STATE_FILE="docs/agent/STATE.md"
STATE_SECTION_CAP=3000   # bytes for "## Current focus" — measure the thing you care about

input=$(cat)
command=$(printf '%s' "$input" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\(.*\)".*/\1/p')

# Match `gh pr create` as a command target (start of string or after a shell operator),
# never as a prose mention inside a commit message or comment body.
printf '%s' "$command" | grep -qE '(^|&&|\|\||;)[[:space:]]*gh[[:space:]]+pr[[:space:]]+create' || exit 0

block() { printf '{"decision":"block","reason":"%s"}\n' "$1"; exit 0; }

base=$(git merge-base HEAD "origin/{{DEFAULT_BRANCH}}" 2>/dev/null || echo "")
changed=$(git diff --name-only "${base:-HEAD~1}"...HEAD 2>/dev/null)

# Junk-file scan — free, both lanes.
junk=$(printf '%s\n' "$changed" | grep -E '\.(bak|orig|rej)$|~$' || true)
[ -n "$junk" ] && block "Junk files in diff: $(printf '%s' "$junk" | tr '\n' ' ')"

# STATE.md cap — bytes of the Current-focus section, not bullet count.
if [ -f "$STATE_FILE" ]; then
  bytes=$(awk '/^## Current focus/{f=1;next} /^## /{f=0} f' "$STATE_FILE" | wc -c | tr -d ' ')
  [ "$bytes" -gt "$STATE_SECTION_CAP" ] && block "STATE.md Current-focus is ${bytes}B > ${STATE_SECTION_CAP}B cap — fold oldest bullets into STATE-archive.md first"
fi

# Lane split: docs/tooling-only diffs skip the evaluator gate.
printf '%s\n' "$changed" | grep -qE "$SOURCE_DIRS_RE" || exit 0

sha=$(git rev-parse HEAD)
verdict_file="$VERDICT_DIR/$sha"
[ -f "$verdict_file" ] || block "No evaluator verdict for HEAD $sha — spawn task-evaluator first (heavy lane: diff touches product source)"
head -1 "$verdict_file" | grep -q '^SHIP' || block "Evaluator verdict for HEAD is not SHIP: $(head -1 "$verdict_file")"
exit 0
