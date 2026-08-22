# product-to-pixels

Purpose: convert a filled product definition into an implementation-ready Design Contract, a portable
Design Prompt, and — where a provider exists — a published canvas.

Inputs: Product Opportunity Brief (the six Define slots), Evidence Pack, platform, mode, timebox, UX
references.

Outputs: promise, magic moment, onboarding path, experience spine, core flow, screens/states,
hierarchy, landing/store copy, UX findings, visual brief, exactly three actionable design principles,
design system (type, spacing, color roles, component inventory, signature component, motion),
accessibility, platform mapping for the selected track, cut list, acceptance criteria, and the Design
Prompt at `.product-studio/artifacts/design-prompt.md`.

Gate: promise, magic moment reachable from the onboarding path, primary flow, screen scope, exactly
three principles, landing/store copy traceable to the Define slots, design system, and a written
Design Prompt. Where the compiled profile sets `design.gate: evidence_required`, the checkpoint also
needs `design.evidence` — a clickable prototype, a canvas the user responded to, or a short usability
check.

Procedure: `references/design-loop.md`.

Handoff: `spec-cartographer`. Behavior discovery starts at the magic moment and the onboarding path.
