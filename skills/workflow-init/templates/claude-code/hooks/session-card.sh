#!/bin/bash
# SessionStart hook: put the workflow card in context so step 1 doesn't depend on the model
# choosing to read it. Prose in AGENTS.md is probabilistic; this is not.
set -u

root="${CLAUDE_PROJECT_DIR:-.}"
card="$root/docs/agent/CARD.md"
# AGENTS.md defers the whole workflow sequence to this card rather than restating it, so a silent
# exit here would leave a session with no sequence at all and no sign anything was missing.
if [ ! -f "$card" ]; then
  echo "⚠️ docs/agent/CARD.md is MISSING — the workflow sequence did not load."
  echo "Read docs/agent/RUNBOOKS.md before opening a PR, and tell the user the card is gone."
  exit 0
fi
cat "$card"
