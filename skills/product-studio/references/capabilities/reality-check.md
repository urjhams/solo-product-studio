# reality-check

Purpose: mid-development re-evaluation. Reconstruct what the code actually is, compare it against what the product was supposed to be, and return a verdict plus the behavior and test deltas needed to close the gap.

Inputs: repository, `.product-studio/project.yaml` when present, `docs/agent/BEHAVIORS.md`, `docs/agent/CARD.md`, `AGENTS.md`, README, existing test suite. No prior state is required — the capability works on a repository it has never seen.

Outputs: a reconstructed product summary derived from code, a three-part drift report, a prioritized question queue with recommended picks, an updated Behavior Spec with an explicit delta, a test delta, and a Re-evaluation Verdict of Continue / Redirect / Cut / Stop.

Sequence: load context → reconstruct from code → show the summary and confirm it with the user before analyzing anything → drift report → prioritized questions → re-run spec hardening with code as evidence → verdict → write back.

Reconstruct from code, not from documentation. Documentation records intent; the drift being hunted is the difference between intent and what was built, so a summary derived from the README cannot find it.

The three drifts: intent versus code (does the product do what it set out to do), behaviors versus code (a `BH-###` with no implementation), behaviors versus tests (a behavior with no test is a coverage gap, a test with no behavior is an orphan that likely encodes a misread requirement, a behavior edited after its test is stale).

Gate: the reconstructed summary was confirmed or corrected by the user; every drift item is evidence-linked to a file or a test; the verdict cites the drift that drove it; behavior additions, changes, and retirements are listed individually rather than as a rewritten file; the mirror is back in sync.

Retire behaviors, never delete them. A retired `BH-###` is how the test that still asserts it gets found.

Handoff: `spec-cartographer` when the spec needs rebuilding, `mvp-forge` when scope changes, `mvp-auditor` when the question is whether the product is working rather than whether it matches its spec.
