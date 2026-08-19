# House rules

Create a compact working agreement before the first autonomous phase. Include only rules that should remain true regardless of implementation approach:

- goal and protected outcome
- target user and product promise
- mode, path, platform surface, stack track, timebox, budget, and team
- evidence, privacy, and security requirements
- non-negotiables and explicit scope exclusions
- approval boundaries for external publication or irreversible decisions

When a specialist recommendation conflicts with a house rule, surface the conflict as a user decision. Do not silently weaken the rule.

## The safety floor

The compiled `workflow_profile` relaxes plenty — CI, independent review, the ambiguity gate, the refactor step — but it never touches these. They hold in a four-hour demo exactly as they hold in a production migration, and no timebox, mode, or user override removes one:

- secrets out of the repository, even a throwaway key, and out of any demo output
- no production data and no destructive action against a production system
- input validation anywhere bad input can crash or corrupt the path being demonstrated
- only the permissions the demonstrated capability actually needs
- an explicit mock/real boundary, so a working demo is never reported as evidence the real thing works

Higher-risk modes add to this list; nothing subtracts from it. The full per-mode set is in `references/workflow-profile.md`, and `compile_profile` unions the mode's floor back in after any override so it cannot be edited away.

## Deployment

Deployment is opt-in and off by default in every mode, production included. It is never a consequence of finishing work or merging a PR — it is a decision the user makes, and turning it on requires a target environment, an approval owner, a rollback plan, the observability questions to check afterwards, and the advance/hold/rollback thresholds. Record it in `approval_boundaries`.
