#!/usr/bin/env bash
# The one command an agent runs before it says "done": lint with a ratchet.
#   scripts/check.sh            fail if any rule's violation count differs from .swiftlint.ratchet, or
#                               if AGENTS.md is over 100 lines
#   scripts/check.sh --update   record lower counts; refuses to record a higher one (tighten-only)
#   scripts/check.sh --baseline record today's counts, higher or lower: the one-time step for a repo
#                               that already has violations. Review the ratchet diff before committing.
#
# A ratchet instead of a baseline file: SwiftLint 0.53 has no baseline, and a count can only fall,
# so debt cannot grow while it is paid down. Ceiling: moving a violation to another file keeps the
# count; the review catches that, the tool does not.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1

mode="${1:-}"
case "$mode" in
  ""|--update|--baseline) ;;
  *) echo "check: unknown argument '$mode' (expected --update or --baseline)" >&2; exit 2 ;;
esac

cap_failed=0
if [ -z "$mode" ] && [ -f AGENTS.md ]; then
  lines=$(wc -l < AGENTS.md | tr -d ' ')
  if [ "$lines" -gt 100 ]; then
    echo "check: AGENTS.md has $lines lines, the cap is 100; move detail to docs/agent/RUNBOOKS.md" >&2
    cap_failed=1
  fi
fi

if ! command -v swiftlint >/dev/null 2>&1; then
  echo "check: swiftlint is not installed (brew install swiftlint)" >&2
  exit 1
fi

report=$(mktemp)
errors=$(mktemp)
trap 'rm -f "$report" "$errors"' EXIT
swiftlint lint --quiet --no-cache --reporter json >"$report" 2>"$errors"
if ! [ -s "$report" ]; then
  echo "check: swiftlint produced no report" >&2
  cat "$errors" >&2
  exit 1
fi

python3 -I - "$report" "$mode" <<'PY'
import collections, json, os, sys
RATCHET = ".swiftlint.ratchet"
violations = json.load(open(sys.argv[1]))
now = collections.Counter(v["rule_id"] for v in violations)
allowed = {}
if sys.argv[2] != "--baseline" and os.path.exists(RATCHET):
    for n, line in enumerate(open(RATCHET), 1):
        parts = line.split()
        if not parts:
            continue
        if len(parts) != 2 or not parts[1].isdigit():
            sys.exit(f"check: malformed ratchet line {n} in {RATCHET}: {line.rstrip()!r}")
        allowed[parts[0]] = int(parts[1])
rules = sorted(set(now) | set(allowed))
rose = [r for r in rules if now[r] > allowed.get(r, 0)]
fell = [r for r in rules if now[r] < allowed.get(r, 0)]

if sys.argv[2] in ("--update", "--baseline"):
    if sys.argv[2] == "--update" and rose:
        sys.exit("check: refusing to record a higher count for: " + ", ".join(rose) + "; --baseline records existing debt")
    open(RATCHET, "w").write("".join(f"{r} {now[r]}\n" for r in rules if now[r]))
    print(f"check: ratchet written, {sum(now.values())} violations")
    sys.exit(0)

for r in rose:
    print(f"check: {r} {allowed.get(r, 0)} -> {now[r]}", file=sys.stderr)
    for v in [v for v in violations if v["rule_id"] == r][:5]:
        print(f"  {os.path.relpath(v['file'])}:{v['line']}: {v['reason']}", file=sys.stderr)
for r in fell:
    print(f"check: {r} fell {allowed[r]} -> {now[r]}; run scripts/check.sh --update", file=sys.stderr)
if rose or fell:
    sys.exit(1)
print(f"check: pass ({sum(now.values())} known violations, none new)")
PY
lint_status=$?
[ "$lint_status" -eq 0 ] && [ "$cap_failed" -eq 0 ]
