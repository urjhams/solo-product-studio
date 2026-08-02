#!/usr/bin/env python3
"""Mechanically demote the oldest 'Current focus' bullets from STATE.md to STATE-archive.md
until the section fits its caps (bullet count AND section bytes). No judgment involved:
bullets move verbatim, newest-first order preserved in both files. Safe to run any time;
a no-op when under cap. Usage: compact-state.py [STATE.md [STATE-archive.md]]
"""
import pathlib
import re
import sys

MAX_BULLETS = 8
MAX_BYTES = 3000
MARKER = "<!-- compact-state inserts below -->"

state_p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "docs/agent/STATE.md")
arch_p = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "docs/agent/STATE-archive.md")

text = state_p.read_text()
m = re.search(r"(?ms)^## Current focus\n(.*?)(?=^## |\Z)", text)
if not m:
    sys.exit(f"no '## Current focus' section in {state_p}")
section = m.group(1)

# A bullet is a "- " line plus its continuation lines, up to the next bullet or section end.
bullets = re.findall(r"(?ms)^- .*?(?=^- |\Z)", section)
if not bullets:
    print("OK: no bullets — nothing to demote")
    sys.exit(0)
lead = section[: section.find(bullets[0])]


def rebuild(bs):
    # The section as it will exist on disk: lead + bullets, blank line restored before the
    # next heading (the demoted last bullet carries the original one away with it).
    s = lead + "".join(bs)
    if not s.endswith("\n\n"):
        s += "\n"
    return s


def size(bs):
    # Measure the EXACT span the enforcing gate measures (its awk prints every line between
    # the headings — lead blank line included), in the same unit (bytes, wc -c; code points
    # disagreed at the cap on multibyte ✓/→/é). Same span and same unit, or the auto-fix and
    # the gate disagree at the boundary.
    return len(rebuild(bs).encode("utf-8"))


demoted = []
while bullets and (len(bullets) > MAX_BULLETS or size(bullets) > MAX_BYTES):
    demoted.append(bullets.pop())  # last bullet = oldest (file is newest-first)

if not demoted:
    print(f"OK: {len(bullets)} bullets, {size(bullets)}B — nothing to demote")
    sys.exit(0)

text = text[: m.start(1)] + rebuild(bullets) + text[m.end(1) :]
state_p.write_text(text)

arch = arch_p.read_text() if arch_p.exists() else f"# Project state — archive\n\n{MARKER}\n"
# demoted[] is oldest-first; archive is newest-first, so insert reversed, right after the
# marker — later runs push earlier demotions down, keeping the order stable.
block = "".join(b if b.endswith("\n") else b + "\n" for b in reversed(demoted))
if MARKER in arch:
    arch = arch.replace(MARKER, MARKER + "\n" + block.rstrip("\n"), 1)
else:
    arch = arch.rstrip("\n") + "\n\n" + block
arch_p.write_text(arch)
print(f"demoted {len(demoted)} bullet(s) -> {arch_p}; kept {len(bullets)} ({size(bullets)}B)")
