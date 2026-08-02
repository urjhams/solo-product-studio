#!/bin/bash
# PostToolUse(Write|Edit): when STATE.md changes, mechanically fold over-cap bullets into the
# archive — compaction happens the moment it's needed, not as a manual chore at PR time.
# The verdict-gate byte cap stays as backstop for edits made outside the harness.
set -u
root="${CLAUDE_PROJECT_DIR:-.}"

input=$(cat)
if command -v jq >/dev/null 2>&1; then
  fp=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')
else
  fp=$(printf '%s' "$input" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
fi
[ -n "$fp" ] || exit 0

case "$fp" in
  */docs/agent/STATE.md|docs/agent/STATE.md)
    out=$(python3 "$root/scripts/agent/compact-state.py" "$fp" "${fp%STATE.md}STATE-archive.md" 2>&1) || exit 0
    case "$out" in
      demoted*) echo "state-autocompact: $out — include BOTH files in the commit" ;;
    esac
    ;;
esac
exit 0
