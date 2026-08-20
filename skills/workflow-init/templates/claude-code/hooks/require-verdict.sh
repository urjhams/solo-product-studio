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
MERGE_POLICY="{{MERGE_POLICY}}"           # never | ask | auto_on_approve
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

# The reason is JSON, and some of what lands in it is file content the reviewer wrote in prose.
# An unescaped `"` produced unparseable stdout, and a hook whose output cannot be parsed does not
# block — which turned a REQUEST-CHANGES marker into a permitted merge. Escape, then emit.
block() {
  reason=$(printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g' | LC_ALL=C tr '\000-\037' ' ')
  printf '{"decision":"block","reason":"%s"}\n' "$reason"
  exit 0
}

# A command *target*: start of line or after a shell operator, past any leading `VAR=val`,
# `env`, `command`, or `sudo` prefix — `PAGER=cat gh pr merge` is still a merge, and a gate that
# misses it is not a gate.
CMD_START='(^|&|\||;|\()[[:space:]]*([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*[[:space:]]+)*((env|command|sudo)[[:space:]]+)*'

# Matching runs against the command with the *contents* of quoted regions removed, so a
# `gh pr merge` inside a commit message or a `--body` never trips a gate while a real one can
# never hide behind a quote. This has to be a single pass that tracks whichever quote opened
# first: a sed pass over single quotes that ignores double-quote context blanks everything
# between two apostrophes — so a chained command carrying two English contractions inside its
# double-quoted arguments made the merge between them invisible. That is a fail-open on the most
# ordinary shape an agent writes, which is why this is a scanner and not a substitution. Unbalanced
# quotes fall back to the raw command, because over-blocking is the safe direction here.
scrub() {
  awk '
    {
      out = ""; q = ""; n = length($0)
      for (i = 1; i <= n; i++) {
        c = substr($0, i, 1)
        if (q == "") { out = out c; if (c == "\"" || c == "'"'"'") q = c }
        else if (q == "\"" && c == "\\") i++
        else if (c == q) { q = ""; out = out c }
      }
      if (q != "") exit 1
      print out
    }'
}
unquoted=$(printf '%s' "$command" | scrub) || unquoted="$command"

# Merge gate. `--admin` bypasses branch protection and is never allowed, under any policy.
# Ceiling on the marker itself: it is written through Bash redirection, so the settings.json
# `Edit`/`Write` denies on the verdict directory do not cover the path that creates it. Any
# Bash-capable subagent could author its own authorization. The deny entries raise the cost;
# the reviewer's anti-forgery clause is what actually carries this, same as the SHIP verdict.
# Past that, the compiled workflow_profile decides: `never` blocks, `ask` falls through to the
# permission prompt (which is why `Bash(gh pr merge:*)` is deliberately NOT in settings.json's
# allow list), and `auto_on_approve` needs an APPROVE review marker earned on this exact HEAD.
# Known ceiling: the marker proves a review verdict, not green CI. Checking `gh pr checks` here
# would mean a network round-trip on every Bash call, so CI-green stays a RUNBOOKS instruction.
if printf '%s' "$unquoted" | grep -qE "${CMD_START}gh[[:space:]]+pr[[:space:]]+merge"; then
  printf '%s' "$unquoted" | grep -qE '(^|[[:space:]])--admin([[:space:]=]|$)' \
    && block "gh pr merge --admin bypasses branch protection. Merge without --admin, or ask the user to merge in the GitHub UI."
  case "$MERGE_POLICY" in
    ask) exit 0 ;;
    auto_on_approve)
      # Which PR is being merged? `gh pr merge 7` merges PR 7 no matter what is checked out, so
      # the ref decides which marker counts. Two rules make the parser trustworthy:
      #
      #   1. It reads $unquoted — the same text the gate matched. Reading $command instead let it
      #      lock onto a `gh pr merge 3` inside a --body while the gate had fired on a real merge
      #      of PR 7, so the two disagreed about which merge they were looking at.
      #   2. Operators are padded into their own fields first, because the walker splits on
      #      whitespace: `(gh pr merge 7)` and `true&&gh pr merge 7` otherwise found no triple at
      #      all, and "not found" fell through to the bare-merge path — the current branch's PR.
      #
      # Every outcome that is not an unambiguous ref, or a genuinely bare `gh pr merge`, blocks.
      pr_ref=$(printf '%s' "$unquoted" | sed 's/[()&|;]/ & /g' | awk '
        {
          start = 0
          for (i = 1; i <= NF; i++) if ($i == "gh" && $(i+1) == "pr" && $(i+2) == "merge") { start = i + 3; break }
          if (start == 0) exit 2
          skip = 0; found = ""; extra = 0
          for (i = start; i <= NF; i++) {
            t = $i
            if (t ~ /^[()&|;]$/) break
            if (skip) { skip = 0; continue }
            if (t ~ /^-/) {
              if (t == "-b" || t == "--body" || t == "-F" || t == "--body-file" || t == "-t" ||
                  t == "--subject" || t == "--author-email" || t == "--match-head-commit") skip = 1
              continue
            }
            if (found == "") found = t; else extra = 1
          }
          if (extra) exit 3
          bare = found
          gsub(/^["\047]+|["\047]+$/, "", bare)
          if (found != "" && bare == "") exit 4
          print bare
        }')
      case $? in
        2) block "Cannot tell which PR this merge targets — the command shape defeated the parser. Run the merge on its own (\`gh pr merge <number>\`), or ask the user to merge in the GitHub UI." ;;
        3) block "Cannot tell which PR this merge targets — more than one non-flag argument. Merge with just the PR number, or ask the user to merge in the GitHub UI." ;;
        4) block "The PR reference is quoted or comes from a variable, so it cannot be resolved before the merge runs. Pass the PR number literally, or ask the user to merge in the GitHub UI." ;;
      esac
      if [ -n "$pr_ref" ]; then
        sha=$(gh pr view "$pr_ref" --json headRefOid -q .headRefOid 2>/dev/null)
      else
        sha=$(gh pr view --json headRefOid -q .headRefOid 2>/dev/null)
      fi
      [ -n "$sha" ] || block "Cannot resolve the head commit of the PR being merged (gh pr view failed). The review marker is pinned to a sha, so this merge cannot be verified — merge in the GitHub UI, or ask the user."
      review_file="$VERDICT_DIR/$sha.review"
      [ -f "$review_file" ] || block "No review marker for the PR head $sha — the reviewer writes $review_file after reviewing that exact commit. Review the PR head first, or ask the user to merge."
      head -1 "$review_file" | grep -q '^APPROVE' || block "Review marker for the PR head is not APPROVE: $(head -1 "$review_file")"
      exit 0 ;;
    *) block "merge_policy is \`${MERGE_POLICY:-never}\` in this project: merging is the user's call. Ask them, or let them merge in the GitHub UI." ;;
  esac
fi

# Same anchor for `gh pr create`: a command target, never a prose mention.
printf '%s' "$unquoted" | grep -qE "${CMD_START}gh[[:space:]]+pr[[:space:]]+create" || exit 0

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
