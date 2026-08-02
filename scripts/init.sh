#!/bin/bash
# workflow-init scaffold. Mechanical part only — copies templates into a project, tracks what it
# created in a sha256 manifest, uninstalls cleanly. Judgment (stack detection, filling
# {{PLACEHOLDERS}}) belongs to the skill/agent that wraps this, or to you with an editor.
#
# Usage:
#   init.sh [--dest DIR] [--modules core,agents,claude-code,ci] [--force] [--list]
#   init.sh --uninstall [--dest DIR]
#   init.sh --check          # self-test into a temp dir
#
# Zero-arg happy path: install the core module into the current directory.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATES="$SCRIPT_DIR/../templates"
MANIFEST_DIR=".workflow-init"
MANIFEST="$MANIFEST_DIR/manifest"

DEST="."
MODULES="core"
FORCE=0
MODE="install"

while [ $# -gt 0 ]; do
  case "$1" in
    --dest) DEST="$2"; shift 2 ;;
    --modules) MODULES="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    --uninstall) MODE="uninstall"; shift ;;
    --check) MODE="check"; shift ;;
    --list) MODE="list"; shift ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done

sha() { if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'; else shasum -a 256 "$1" | awk '{print $1}'; fi; }

# module template-path -> destination-path mapping (one "src|dst" pair per line)
map_module() {
  case "$1" in
    core) cat <<'EOF'
core/AGENTS.md|AGENTS.md
core/docs/agent/CARD.md|docs/agent/CARD.md
core/docs/agent/RUNBOOKS.md|docs/agent/RUNBOOKS.md
core/docs/agent/STATE.md|docs/agent/STATE.md
core/docs/agent/STATE-archive.md|docs/agent/STATE-archive.md
core/docs/agent/GOTCHAS.md|docs/agent/GOTCHAS.md
EOF
      ;;
    agents) cat <<'EOF'
agents/task-evaluator.md|.claude/agents/task-evaluator.md
agents/platform-reviewer.md|.claude/agents/_platform-reviewer.template.md
EOF
      ;;
    claude-code) cat <<'EOF'
claude-code/settings.json|.claude/settings.json
claude-code/hooks/session-card.sh|.claude/hooks/session-card.sh
claude-code/hooks/require-verdict.sh|.claude/hooks/require-verdict.sh
EOF
      ;;
    ci) cat <<'EOF'
ci/github/workflows/ci.yml|.github/workflows/ci.yml
EOF
      ;;
    *) echo "unknown module: $1" >&2; exit 1 ;;
  esac
}

install() {
  local installed=0 skipped=0
  IFS=',' read -ra mods <<< "$MODULES"
  # Validate up front: an exit inside `< <(map_module …)` process substitution
  # doesn't propagate, so a typo'd module would otherwise silently no-op.
  for mod in "${mods[@]}"; do
    case "$mod" in core|agents|claude-code|ci) ;; *) echo "unknown module: $mod" >&2; exit 1 ;; esac
  done
  mkdir -p "$DEST/$MANIFEST_DIR"
  touch "$DEST/$MANIFEST"
  for mod in "${mods[@]}"; do
    while IFS='|' read -r src dst; do
      [ -n "$src" ] || continue
      local from="$TEMPLATES/$src" to="$DEST/$dst"
      if [ -f "$to" ]; then
        if [ "$FORCE" = 1 ] && grep -q "	$dst\$" "$DEST/$MANIFEST" && [ "$(sha "$to")" = "$(grep "	$dst\$" "$DEST/$MANIFEST" | awk '{print $1}')" ]; then
          : # unmodified generated file — regenerate below
        else
          echo "skip (exists): $dst"; skipped=$((skipped+1)); continue
        fi
      fi
      mkdir -p "$(dirname "$to")"
      cp "$from" "$to"
      case "$to" in *.sh) chmod +x "$to" ;; esac
      grep -v "	$dst\$" "$DEST/$MANIFEST" > "$DEST/$MANIFEST.tmp" || true
      printf '%s\t%s\n' "$(sha "$to")" "$dst" >> "$DEST/$MANIFEST.tmp"
      mv "$DEST/$MANIFEST.tmp" "$DEST/$MANIFEST"
      echo "wrote: $dst"; installed=$((installed+1))
    done < <(map_module "$mod")
  done
  # Claude Code reads CLAUDE.md; other agents read AGENTS.md. Bridge once, never overwrite.
  if [ -f "$DEST/AGENTS.md" ] && [ ! -f "$DEST/CLAUDE.md" ]; then
    printf '@AGENTS.md\n' > "$DEST/CLAUDE.md"
    printf '%s\t%s\n' "$(sha "$DEST/CLAUDE.md")" "CLAUDE.md" >> "$DEST/$MANIFEST"
    echo "wrote: CLAUDE.md (imports AGENTS.md)"
  fi
  echo
  echo "Done: $installed written, $skipped skipped (already exist)."
  echo "Next steps:"
  echo "  1. Fill the {{PLACEHOLDERS}} — list them: grep -rn '{{[A-Z_]*}}' $DEST/AGENTS.md $DEST/docs/agent $DEST/.claude $DEST/.github 2>/dev/null"
  echo "  2. agents module: instantiate .claude/agents/_platform-reviewer.template.md once per component."
  echo "  3. claude-code module: hooks activate on next session; verify with a throwaway 'gh pr create' dry-run."
  echo "  Uninstall anytime: init.sh --uninstall (removes only unmodified generated files)."
}

uninstall() {
  [ -f "$DEST/$MANIFEST" ] || { echo "no manifest at $DEST/$MANIFEST — nothing to uninstall"; exit 0; }
  local removed=0 kept=0
  while IFS=$'\t' read -r hash path; do
    [ -n "$path" ] || continue
    local f="$DEST/$path"
    if [ ! -f "$f" ]; then continue; fi
    if [ "$(sha "$f")" = "$hash" ]; then
      rm "$f"; echo "removed: $path"; removed=$((removed+1))
    else
      echo "kept (edited since generation — remove manually): $path"; kept=$((kept+1))
    fi
  done < "$DEST/$MANIFEST"
  rm -f "$DEST/$MANIFEST"; rmdir "$DEST/$MANIFEST_DIR" 2>/dev/null || true
  find "$DEST/docs/agent" "$DEST/.claude" "$DEST/.github" -type d -empty -delete 2>/dev/null || true
  echo "Done: $removed removed, $kept kept."
}

check() {
  local tmp; tmp=$(mktemp -d)
  echo "self-check in $tmp"
  DEST="$tmp" MODULES="core,agents,claude-code,ci" FORCE=0 install >/dev/null
  local expected="AGENTS.md CLAUDE.md docs/agent/CARD.md docs/agent/RUNBOOKS.md docs/agent/STATE.md docs/agent/STATE-archive.md docs/agent/GOTCHAS.md .claude/agents/task-evaluator.md .claude/agents/_platform-reviewer.template.md .claude/settings.json .claude/hooks/session-card.sh .claude/hooks/require-verdict.sh .github/workflows/ci.yml"
  local fail=0
  for f in $expected; do
    [ -f "$tmp/$f" ] || { echo "MISSING: $f"; fail=1; }
  done
  [ -x "$tmp/.claude/hooks/session-card.sh" ] || { echo "NOT EXECUTABLE: session-card.sh"; fail=1; }
  bash -n "$tmp/.claude/hooks/require-verdict.sh" || { echo "SYNTAX ERROR: require-verdict.sh"; fail=1; }
  # idempotency: second run writes nothing
  local second; second=$(DEST="$tmp" MODULES="core" FORCE=0 install | grep -c '^wrote:' || true)
  [ "$second" = 0 ] || { echo "NOT IDEMPOTENT: second run wrote $second files"; fail=1; }
  # uninstall leaves nothing generated behind
  DEST="$tmp" uninstall >/dev/null
  [ -f "$tmp/AGENTS.md" ] && { echo "UNINSTALL LEFT: AGENTS.md"; fail=1; }
  rm -rf "$tmp"
  if [ "$fail" = 0 ]; then echo "CHECK OK"; else echo "CHECK FAILED"; exit 1; fi
}

case "$MODE" in
  install) install ;;
  uninstall) uninstall ;;
  check) check ;;
  list) for m in core agents claude-code ci; do echo "[$m]"; map_module "$m" | sed 's/^/  /'; done ;;
esac
