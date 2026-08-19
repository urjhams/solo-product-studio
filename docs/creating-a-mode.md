# Creating an operating mode

A mode is not prose plus a label — a label enforces nothing, which is exactly how Hackathon spent a
release being described in six files and read by zero scripts. Five steps, and the last two are what
make it real:

1. Add a row to `MODE_PROFILES` in `scripts/workflow_profile.py`. Every field needs a value; there
   are no defaults to inherit, on purpose, so a new mode cannot silently acquire a production gate.
2. Add the mode to the enum in `schemas/project.schema.json` and
   `schemas/workflow-profile.schema.json`. The parity test fails until you do.
3. Add it to `references/operating-modes.md` with its optimization priority, recommendation
   signals, QA questions, MVP rules, artifact adaptations, and exit criteria — and to
   `references/workflow-profile.md`'s table.
4. Write `references/<mode>-mode.md` only if the mode overrides the default scope, mock, research,
   testing, or done-bar rules. If it does, register it in `scripts/validate_bundle.py` and add a
   done bar to `references/done-bars.md`.
5. Add a **scenario test** to `tests/test_bundle.py` — one that drives the runner through a
   checkpoint and asserts the gates the mode claims. A test that only asserts the mode's name
   appears in a Markdown file proves the documentation exists, not the behavior.

Preserve user override through Custom mode, which compiles the same way from an override set.
