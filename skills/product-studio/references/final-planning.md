# Final planning protocol

Run this phase after an approved MVP Build Plan or Production Blueprint and before implementation or GitHub delivery.

0. Confirm the Behavior Spec is approved and closed. Wherever the compiled profile sets `planning.spec_gate: block` — every mode except Prototype and Hackathon — an ambiguity still `open` blocks this phase — `workflow_runner.py` refuses the checkpoint with `ambiguities-open` and `validate_implementation_brief.py` exits non-zero. Do not write around it; go back and resolve, defer, or rule the ambiguity out of scope.
1. Read the approved source artifact, the Behavior Spec, project state, repository, existing tests, design references, documentation, and prior reviews.
2. Run the intern test: identify every material a new implementation agent needs and its exact path or an explicit unavailable note.
3. Ask only missing questions that affect the goal, constraints, verification, or output shape.
4. Produce `08-implementation-brief.md` with Context, Task, Constraints, Verification, Output Format, and Handoff.
5. On a native Apple track, state the build and test mechanism explicitly: XcodeBuildMCP tool calls when the adapter is available, `xcodebuild` commands when it is not, or manual Xcode steps recorded as unresolved. See `adapters/xcodebuild-mcp/README.md`.
6. Convert vague quality language into concrete checks. Every verification item must say what to check, **who owns it**, where evidence will come from, and its current status. Owner is `implementation`, `reviewer`, or `user`, and it is load-bearing: a check owned by the implementing agent or its reviewer is a future condition and may hand off `unresolved`, while a check only the user can settle is a missing input and blocks. At plan time `Evidence:` names the *source* — `tests/core/`, `xcodebuild test`, a screenshot path — not the result. Every acceptance criterion must cite the `BH-###` it enforces, and every `active` behavior must be covered by at least one criterion or explicitly scheduled for a later slice.
7. Use explicit stopping conditions: do not finish until every required check passes or is recorded as unresolved and escalated. These are the *implementing agent's* stopping conditions, and they are unmet by construction when the brief is written — handing off is gated on every check being well-formed, not on every check having already passed. `workflow_runner.py checkpoint final_planning` enforces the first; `workflow_runner.py done` enforces the second, at the end, and refuses with `verification-checks-unresolved` until every check has actually landed.
8. Send the brief to an independent reviewer. Repair the highest-impact finding and repeat until it passes. Without a fresh review context, mark `self_review_only` and block approval.
9. At the checkpoint, show source artifacts, unresolved items, verification status, and the selected next action.

**Fast-mode short form** (`planning.spec_gate: warn` — Prototype and Hackathon). All six brief sections are still required, but Verification is the manual path plus the single automated check, `BH-###` citations and the behavior spec path are optional (`--mode prototype` / `--mode hackathon` on both validators), step 8 may end as `self_review_only` without blocking handoff, and the brief must state that the output is a throwaway prototype or a demo artifact, not to be extended without re-running mode selection. See `references/prototype-mode.md` and `references/hackathon-mode.md`.

A brief may not plan a step the profile does not permit: `validate_implementation_brief.py` rejects a deployment named in Output Format or Handoff while `deployment.allowed` is false, which it is in every compiled default. See `references/prototype-mode.md`.

The detailed MVP or Production artifact remains authoritative for scope and architecture; the Implementation Brief is the final execution contract derived from it. Keep both synchronized through project state.
