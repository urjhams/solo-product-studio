# mvp-forge

Purpose: create a timeboxed, executable MVP Build Plan from the Design Contract or product definition.

Inputs: Design Contract, product definition, repository, mode, timebox, platform.

Outputs: stack, architecture level, repository assessment, critical path, vertical slices, structure, data/API/mock boundaries, persistence, sequence, time allocation, tests, permissions/security, fallback, cut triggers, acceptance criteria, demo script, definition of done.

Default sequence: shell → complete mock core flow → replace only critical mocks → persistence → loading/error/fallback → polish → validate.

Gate: core flow executable, mocks and real integrations explicit, cuts explicit, measurable definition of done.

Handoff: implementation, `mvp-auditor`, or `github-delivery`.
