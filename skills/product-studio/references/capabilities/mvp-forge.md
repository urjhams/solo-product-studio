# mvp-forge

Purpose: create a timeboxed, executable MVP Build Plan from the Design Contract or product definition.

Inputs: Design Contract, product definition, repository, mode, timebox, platform surface and track.

Outputs: platform track, stack, stack rationale, architecture level, repository assessment, critical path, vertical slices, structure, data/API/mock boundaries, persistence, sequence, time allocation, tests, permissions/security, fallback, cut triggers, acceptance criteria, demo script, definition of done.

Default sequence: shell → complete mock core flow → replace only critical mocks → persistence → loading/error/fallback → polish → validate.

Gate: core flow executable, platform track chosen with rationale and revisit trigger, mocks and real integrations explicit, cuts explicit, measurable definition of done.

In Hackathon mode the stack rationale is time to a running app on the demo device, not product fit. See `references/platform-decision.md`.

In Prototype mode the plan is one flow, mocked to the boundary the user confirmed, 3–6 visible build steps, one runnable check on the flow's core logic, and a click-through acceptance path. Drop the architecture level, persistence, permissions, and demo script sections unless the idea is about them. See `references/prototype-mode.md`.

Handoff: implementation, `mvp-auditor`, or `github-delivery`.
