#!/bin/bash
# workflow-init scaffold. Mechanical part only — copies templates into a project, tracks what it
# created in a sha256 manifest, uninstalls cleanly. Judgment (stack detection, filling
# {{PLACEHOLDERS}}) belongs to the skill/agent that wraps this, or to you with an editor.
#
# Usage:
#   init.sh [--dest DIR] [--modules core,agents,claude-code,ci,ci-review,engineering,engineering-web] [--force] [--list]
#   init.sh --uninstall [--dest DIR]
#   init.sh --check          # self-test into a temp dir
#
# Zero-arg happy path: install the core module into the current directory.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATES="$SCRIPT_DIR/../templates"
# The engineering references live in the sibling engineering-cycle skill. They are
# copied into the project rather than linked, so a scaffolded repo keeps working
# when this bundle is not installed — the same reason every pointer in the
# generated docs is repo-relative. Sibling layout holds for copy and symlink
# installs alike, so this resolves in both.
ENGINEERING="$SCRIPT_DIR/../../engineering-cycle/references"
MANIFEST_DIR=".workflow-init"
MANIFEST="$MANIFEST_DIR/manifest"

DEST="."
MODULES="core"
FORCE=0
MODE="install"
PROFILE=""
# Set from .product-studio/project.json when product-studio ran first. Defaults
# hold when it did not — workflow-init has to stay usable on its own.
PS_MODE=""
PS_CI_REQUIRED=0

while [ $# -gt 0 ]; do
  case "$1" in
    --dest) DEST="$2"; shift 2 ;;
    --modules) MODULES="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    --uninstall) MODE="uninstall"; shift ;;
    --check) MODE="check"; shift ;;
    --list) MODE="list"; shift ;;
    --profile) PROFILE="$2"; shift 2 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done

# The compiled workflow profile decides which CI ladder this repo gets. Reading it
# here rather than compiling anything keeps the single policy table in product-studio,
# which workflow-init is deliberately not packaged with.
read_profile() {
  [ -f "$1" ] || return 0
  command -v python3 >/dev/null 2>&1 || return 0
  eval "$(python3 -c '
import json, sys
try:
    profile = json.load(open(sys.argv[1])).get("workflow_profile") or {}
except Exception:
    profile = {}
mode = profile.get("mode", "")
print("PS_MODE=" + (mode if mode.isalnum() else ""))
print("PS_CI_REQUIRED=" + str(int(bool(profile.get("testing", {}).get("ci_required")))))
' "$1" 2>/dev/null)"
}

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
core/docs/agent/BEHAVIORS.md|docs/agent/BEHAVIORS.md
core/scripts/agent/compact-state.py|scripts/agent/compact-state.py
EOF
      ;;
    agents) cat <<'EOF'
agents/task-evaluator.md|.claude/agents/task-evaluator.md
agents/platform-reviewer.md|.claude/agents/_platform-reviewer.template.md
agents/qa-agent.md|.claude/agents/_qa-agent.template.md
EOF
      ;;
    claude-code) cat <<'EOF'
claude-code/settings.json|.claude/settings.json
claude-code/hooks/session-card.sh|.claude/hooks/session-card.sh
claude-code/hooks/require-verdict.sh|.claude/hooks/require-verdict.sh
claude-code/hooks/state-autocompact.sh|.claude/hooks/state-autocompact.sh
EOF
      ;;
    ci) if [ "$PS_CI_REQUIRED" = 1 ]; then
          echo 'ci/github/workflows/ci-full.yml|.github/workflows/ci.yml'
        else
          echo 'ci/github/workflows/ci.yml|.github/workflows/ci.yml'
        fi
      ;;
    # online review lane: the review runs in Actions instead of a local reviewer subagent
    ci-review) cat <<'EOF'
ci/github/workflows/claude-review.yml|.github/workflows/claude-review.yml
EOF
      ;;
    # Depth behind the gates, and the phase after the PR merges. Sources resolve
    # against $ENGINEERING, not $TEMPLATES. Sections inside these files carry
    # `<!-- stack: … -->` markers; those are reader hints, not a build step —
    # selection is per file, so nothing is ever silently dropped from one.
    engineering) cat <<'EOF'
engineering/review.md|docs/engineering/review.md
engineering/security.md|docs/engineering/security.md
engineering/performance.md|docs/engineering/performance.md
engineering/build-loop.md|docs/engineering/build-loop.md
engineering/planning.md|docs/engineering/planning.md
engineering/doubt.md|docs/engineering/doubt.md
engineering/api.md|docs/engineering/api.md
engineering/sources.md|docs/engineering/sources.md
engineering/adr.md|docs/engineering/adr.md
engineering/observability.md|docs/engineering/observability.md
engineering/release.md|docs/engineering/release.md
engineering/ci.md|docs/engineering/ci.md
engineering/ship.md|docs/engineering/ship.md
engineering/migration.md|docs/engineering/migration.md
engineering/checklists/definition-of-done.md|docs/engineering/checklists/definition-of-done.md
engineering/checklists/security-checklist.md|docs/engineering/checklists/security-checklist.md
engineering/checklists/performance-checklist.md|docs/engineering/checklists/performance-checklist.md
engineering/checklists/accessibility-checklist.md|docs/engineering/checklists/accessibility-checklist.md
engineering/checklists/observability-checklist.md|docs/engineering/checklists/observability-checklist.md
engineering/checklists/testing-patterns.md|docs/engineering/checklists/testing-patterns.md
engineering/checklists/orchestration-patterns.md|docs/engineering/checklists/orchestration-patterns.md
EOF
      ;;
    # Browser verification is the one whole-file web-only reference, and it is inert
    # without the chrome-devtools MCP server. Kept separate so an Apple-only or
    # backend-only repo does not carry a document it can never act on.
    engineering-web) cat <<'EOF'
engineering/browser-verification.md|docs/engineering/browser-verification.md
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
    case "$mod" in core|agents|claude-code|ci|ci-review|engineering|engineering-web) ;; *) echo "unknown module: $mod" >&2; exit 1 ;; esac
  done
  # Every source must exist before anything is written. The engineering modules read
  # from a sibling skill, so a workflow-init copied out on its own would otherwise
  # abort mid-run on a raw `cp:` error under `set -e` — after the core files landed
  # but before the CLAUDE.md bridge, leaving a half-scaffolded project.
  for mod in "${mods[@]}"; do
    while IFS='|' read -r src dst; do
      [ -n "$src" ] || continue
      local check="$TEMPLATES/$src"
      case "$src" in engineering/*) check="$ENGINEERING/${src#engineering/}" ;; esac
      if [ ! -f "$check" ]; then
        echo "missing source for module '$mod': $check" >&2
        case "$src" in engineering/*)
          echo "  the '$mod' module needs the engineering-cycle skill beside this one." >&2
          echo "  install the whole bundle, or drop '$mod' from --modules." >&2
          ;;
        esac
        exit 1
      fi
    done < <(map_module "$mod")
  done
  mkdir -p "$DEST/$MANIFEST_DIR"
  touch "$DEST/$MANIFEST"
  for mod in "${mods[@]}"; do
    while IFS='|' read -r src dst; do
      [ -n "$src" ] || continue
      local from="$TEMPLATES/$src" to="$DEST/$dst"
      case "$src" in engineering/*) from="$ENGINEERING/${src#engineering/}" ;; esac
      if [ -f "$to" ]; then
        if [ "$FORCE" = 1 ] && grep -q "	$dst\$" "$DEST/$MANIFEST" && [ "$(sha "$to")" = "$(grep "	$dst\$" "$DEST/$MANIFEST" | awk '{print $1}')" ]; then
          : # unmodified generated file — regenerate below
        else
          echo "skip (exists): $dst"; skipped=$((skipped+1)); continue
        fi
      fi
      mkdir -p "$(dirname "$to")"
      cp "$from" "$to"
      case "$to" in *.sh|*.py) chmod +x "$to" ;; esac
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
  echo "  2. agents module: instantiate .claude/agents/_platform-reviewer.template.md once per component,"
  echo "     and _qa-agent.template.md once for the user-visible surface (or delete it if there is none)."
  echo "  3. claude-code module: hooks activate on next session; verify with a throwaway 'gh pr create' dry-run."
  case ",$MODULES," in *,ci-review,*) echo "  4. ci-review module: set the API key secret — gh secret set ANTHROPIC_API_KEY" ;; esac
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
  # -delete implies -depth, so children go before parents in one pass. `-empty` is what
  # makes it safe to name the shared parents: a project's own docs/ or scripts/ with
  # anything left in it is never touched.
  find "$DEST/docs/agent" "$DEST/docs/engineering" "$DEST/scripts/agent" \
       "$DEST/.claude" "$DEST/.github" "$DEST/docs" "$DEST/scripts" \
       -type d -empty -delete 2>/dev/null || true
  echo "Done: $removed removed, $kept kept."
}

check() {
  local tmp; tmp=$(mktemp -d)
  echo "self-check in $tmp"
  DEST="$tmp" MODULES="core,agents,claude-code,ci,ci-review,engineering,engineering-web" FORCE=0 install >/dev/null
  local expected="AGENTS.md CLAUDE.md docs/agent/CARD.md docs/agent/RUNBOOKS.md docs/agent/STATE.md docs/agent/STATE-archive.md docs/agent/GOTCHAS.md docs/agent/BEHAVIORS.md scripts/agent/compact-state.py .claude/agents/task-evaluator.md .claude/agents/_platform-reviewer.template.md .claude/settings.json .claude/hooks/session-card.sh .claude/hooks/require-verdict.sh .claude/hooks/state-autocompact.sh .github/workflows/ci.yml .github/workflows/claude-review.yml docs/engineering/review.md docs/engineering/ship.md docs/engineering/browser-verification.md docs/engineering/checklists/definition-of-done.md"
  local fail=0
  for f in $expected; do
    [ -f "$tmp/$f" ] || { echo "MISSING: $f"; fail=1; }
  done
  # every engineering source the map names must actually exist in the sibling skill,
  # or the module silently installs a short set
  local nmapped nlanded
  nmapped=$( { map_module engineering; map_module engineering-web; } | grep -c '^engineering/')
  nlanded=$(find "$tmp/docs/engineering" -name '*.md' | wc -l | tr -d ' ')
  [ "$nmapped" = "$nlanded" ] || { echo "ENGINEERING MODULE SHORT: mapped $nmapped, landed $nlanded"; fail=1; }
  # the copies must not carry the upstream packs' unresolved ../../references/ links
  ! grep -rq '\.\./\.\./references/' "$tmp/docs/engineering" || { echo "DANGLING UPSTREAM LINK in docs/engineering"; fail=1; }
  [ -x "$tmp/.claude/hooks/session-card.sh" ] || { echo "NOT EXECUTABLE: session-card.sh"; fail=1; }
  bash -n "$tmp/.claude/hooks/require-verdict.sh" || { echo "SYNTAX ERROR: require-verdict.sh"; fail=1; }
  # the behavior-spec format marker is a shared contract with the product-studio skill
  grep -q '<!-- behavior-spec/v1 -->' "$tmp/docs/agent/BEHAVIORS.md" || { echo "MISSING MARKER: behavior-spec/v1"; fail=1; }
  # a fresh BEHAVIORS.md must declare no active behaviors, or the coverage hook blocks every PR
  local nactive; nactive=$(sed '/<!--/,/-->/d' "$tmp/docs/agent/BEHAVIORS.md" | grep -c '^- Status:[[:space:]]*active' || true)
  [ "$nactive" = 0 ] || { echo "FRESH BEHAVIORS.md DECLARES $nactive ACTIVE BEHAVIORS: coverage hook would block every PR"; fail=1; }
  # compaction: 10 over-length bullets -> caps enforced, demoted bullets land in archive
  if command -v python3 >/dev/null 2>&1; then
    for i in 10 9 8 7 6 5 4 3 2 1; do
      printf -- '- 2026-01-%02d: `b%d` — %s.\n' "$i" "$i" "$(printf 'x%.0s' $(seq 1 400))"
    done > "$tmp/bullets.txt"
    awk '/^## Current focus/{print; while((getline l < "'"$tmp"'/bullets.txt") > 0) print l; next} !/^- /' "$tmp/docs/agent/STATE.md" > "$tmp/docs/agent/STATE.tmp" && mv "$tmp/docs/agent/STATE.tmp" "$tmp/docs/agent/STATE.md"
    (cd "$tmp" && python3 scripts/agent/compact-state.py >/dev/null)
    local nb; nb=$(grep -c '^- ' "$tmp/docs/agent/STATE.md" || true)
    local sb; sb=$(awk '/^## Current focus/{f=1;next} /^## /{f=0} f' "$tmp/docs/agent/STATE.md" | wc -c | tr -d ' ')
    [ "$nb" -le 8 ] && [ "$sb" -le 3000 ] || { echo "COMPACT FAILED: $nb bullets, ${sb}B after run"; fail=1; }
    grep -q 'b1' "$tmp/docs/agent/STATE-archive.md" || { echo "COMPACT FAILED: oldest bullet not archived"; fail=1; }
    grep -q 'b10' "$tmp/docs/agent/STATE.md" || { echo "COMPACT FAILED: newest bullet lost"; fail=1; }
  fi
  # idempotency: second run writes nothing
  local second; second=$(DEST="$tmp" MODULES="core" FORCE=0 install | grep -c '^wrote:' || true)
  [ "$second" = 0 ] || { echo "NOT IDEMPOTENT: second run wrote $second files"; fail=1; }
  # uninstall leaves nothing generated behind
  DEST="$tmp" uninstall >/dev/null
  [ -f "$tmp/AGENTS.md" ] && { echo "UNINSTALL LEFT: AGENTS.md"; fail=1; }
  # empty generated dirs count as left behind — a project that uninstalled cleanly
  # should not still carry a hollow docs/engineering/checklists/
  [ -d "$tmp/docs/engineering" ] && { echo "UNINSTALL LEFT: empty docs/engineering"; fail=1; }
  # the ci module must follow the profile: a fast mode gets the single-job stub, a
  # durable one gets the full ladder on PR *and* default-branch push
  local ci_tmp; ci_tmp=$(mktemp -d)
  PS_CI_REQUIRED=0 DEST="$ci_tmp/fast" MODULES="ci" FORCE=0 install >/dev/null
  PS_CI_REQUIRED=1 DEST="$ci_tmp/durable" MODULES="ci" FORCE=0 install >/dev/null
  if diff -q "$ci_tmp/fast/.github/workflows/ci.yml" "$ci_tmp/durable/.github/workflows/ci.yml" >/dev/null 2>&1; then
    echo "CI NOT PROFILE-AWARE: both lanes emitted the same workflow"; fail=1
  fi
  grep -q '^  push:' "$ci_tmp/durable/.github/workflows/ci.yml" || { echo "DURABLE CI MISSING default-branch push trigger"; fail=1; }
  grep -q '^  push:' "$ci_tmp/fast/.github/workflows/ci.yml" && { echo "FAST CI SHOULD NOT push-trigger"; fail=1; }
  rm -rf "$ci_tmp"
  rm -rf "$tmp"
  if [ "$fail" = 0 ]; then echo "CHECK OK"; else echo "CHECK FAILED"; exit 1; fi
}

read_profile "${PROFILE:-$DEST/.product-studio/project.json}"

case "$MODE" in
  install) install ;;
  uninstall) uninstall ;;
  check) check ;;
  list) for m in core agents claude-code ci ci-review engineering engineering-web; do echo "[$m]"; map_module "$m" | sed 's/^/  /'; done ;;
esac
