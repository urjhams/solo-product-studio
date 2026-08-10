# implementation-brief

Purpose: convert an approved MVP Build Plan or Production Blueprint into a self-contained implementation handoff.

Inputs: approved source artifact, approved Behavior Spec, project state, repository context, prior review findings, house rules, and selected mode/path.

Outputs: Context, Task, Constraints, Verification, Output Format, and Handoff sections in `08-implementation-brief.md`.

Completion gate:

- Context passes the intern test and names actual materials or records them unavailable, including the behavior spec path.
- Constraints are explicit and testable.
- Every acceptance criterion cites the `BH-###` it enforces, and every `active` behavior is covered by a criterion or explicitly scheduled for a later slice.
- The Behavior Spec has zero open ambiguities. Outside Prototype mode this blocks the brief.
- `do_not_finish_until` contains concrete stopping conditions with evidence and status.
- Output format and handoff are specified.
- Independent review passes; self-review-only remains blocked.

Handoff: implementation or GitHub Delivery. The implementation agent must read this brief and the Behavior Spec before touching source files, and must name the `BH-###` in every test it writes.
