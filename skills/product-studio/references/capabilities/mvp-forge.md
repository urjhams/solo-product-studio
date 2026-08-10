# mvp-forge

Purpose: create a timeboxed, executable MVP Build Plan from the Design Contract or product definition.

Inputs: Design Contract, approved Behavior Spec, product definition, repository, mode, timebox, platform surface and track.

Outputs: platform track, stack, stack rationale, architecture level, repository assessment, critical path, vertical slices, structure, data/API/mock boundaries, persistence, sequence, time allocation, tests, permissions/security, fallback, cut triggers, acceptance criteria, demo script, definition of done.

Cut vertical slices along behaviors, not along layers. Each slice names the `BH-###` it makes true, every `active` behavior lands in exactly one slice, and the Test column cites behaviors rather than describing tests. A behavior with no slice is either scheduled (`Status: planned`) or an omission — say which.

Default sequence: shell → complete mock core flow → replace only critical mocks → persistence → loading/error/fallback → polish → validate.

Gate: core flow executable, platform track chosen with rationale and revisit trigger, mocks and real integrations explicit, cuts explicit, every `active` behavior assigned to a slice, measurable definition of done.

In Hackathon mode the stack rationale is time to a running app on the demo device, not product fit. See `references/platform-decision.md`.

In Prototype mode the plan is one flow, mocked to the boundary the user confirmed, 3–6 visible build steps, one runnable check on the flow's core logic, and a click-through acceptance path. Drop the architecture level, persistence, permissions, and demo script sections unless the idea is about them. See `references/prototype-mode.md`.

On a native Apple track, resolve the XcodeBuildMCP question before writing the tests and definition-of-done sections: with it, verification items are real `build_sim` / `test_sim` runs and simulator screenshots; without it, they are `xcodebuild` shell commands or manual Xcode steps. See `adapters/xcodebuild-mcp/README.md`.

Handoff: implementation, `mvp-auditor`, or `github-delivery`.
