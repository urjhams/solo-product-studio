#!/usr/bin/env bash
# The one command an agent runs before it says "done": lint with a ratchet.
#   scripts/check.sh            fail if any rule's violation count differs from .swiftlint.ratchet
#   scripts/check.sh --update   record lower counts; refuses to record a higher one
#
# A ratchet instead of a baseline file: SwiftLint 0.53 has no baseline, and a count can only fall,
# so debt cannot grow while it is paid down. Ceiling: moving a violation to another file keeps the
# count; the review catches that, the tool does not.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1

if ! command -v swiftlint >/dev/null 2>&1; then
  echo "check: swiftlint is not installed (brew install swiftlint)" >&2
  exit 1
fi

report=$(mktemp)
trap 'rm -f "$report"' EXIT
swiftlint lint --quiet --no-cache --reporter json >"$report" 2>/dev/null
if ! [ -s "$report" ]; then
  echo "check: swiftlint produced no report" >&2
  exit 1
fi

python3 -I - "$report" "${1:-}" <<'PY'
import collections, json, os, sys
RATCHET = ".swiftlint.ratchet"
violations = json.load(open(sys.argv[1]))
now = collections.Counter(v["rule_id"] for v in violations)
try:
    allowed = {k: int(v) for k, v in (l.split() for l in open(RATCHET) if l.strip())}
except FileNotFoundError:
    allowed = {}
rules = sorted(set(now) | set(allowed))
rose = [r for r in rules if now[r] > allowed.get(r, 0)]
fell = [r for r in rules if now[r] < allowed.get(r, 0)]

if sys.argv[2] == "--update":
    if rose and os.path.exists(RATCHET):
        sys.exit("check: refusing to record a higher count for: " + ", ".join(rose))
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
