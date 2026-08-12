---
name: product-recheck
description: Re-evaluate a product already under development. Reconstructs what the code actually is, diffs it against the intended product, the behavior spec, and the test suite, then runs an interactive session that returns a Continue/Redirect/Cut/Stop verdict with behavior and test deltas. Use mid-build to check the work still matches the vision, to re-scope, to harden specs against a real codebase, or to find tests that assert the wrong idea.
---

# Product Recheck

Act as the user's product QA partner for work already in flight. The question you answer is not "is this code good" — that is a code review. It is **"is this the product they meant to build, and does the test suite prove the right thing?"**

The companion skill `product-studio` takes an idea to a hardened plan. This one re-enters that loop from the middle. It reads the same `.product-studio/project.yaml`, the same references, the same templates, and writes back to the same Behavior Spec.

The public entry is `/product-recheck`. Without a slash-command surface, accept `Use product-recheck to re-evaluate this project.`

## Order of work

Follow this order. Steps 2 and 3 exist because a summary derived from documentation cannot find drift — documentation records intent, and intent is one side of the diff.

1. Load context.
2. Reconstruct the product from code.
3. Show the reconstruction and get it confirmed before analyzing anything.
4. Report the three drifts.
5. Ask the decisions that matter, highest impact first, each with a recommended pick.
6. Re-attack the specification with the code as evidence.
7. Return a verdict with behavior and test deltas.
8. Write back.

## 1. Load context

Read whatever exists, in this order, and record which were absent:

- `.product-studio/project.yaml` — goal, protected outcome, mode, decisions, assumptions, phase state
- `docs/agent/BEHAVIORS.md` — the behavior spec mirror; the canonical copy is `.product-studio/artifacts/behavior-spec.md`
- `docs/agent/CARD.md`, `AGENTS.md` / `CLAUDE.md`, `docs/agent/STATE.md` — an existing code map and working agreement
- `docs/agent/GOTCHAS.md` — what already cost someone a debugging session; a drift you are about to report may already be a known trap
- `docs/engineering/` — the standards this repo committed to; a gap against its own checklists is a finding, not a suggestion
- README, ADRs, open issues, recent commit subjects

None of these are required. Working from a repository that has never seen either skill is the normal case, not the fallback.

When no code map exists, scan directly: entry points, routes or screens, data models and their state fields, external calls, background jobs, and the test tree. Prefer breadth over depth — you are building an inventory, not reviewing implementations.

## 2. Reconstruct from code

Write down, from the code alone:

- what this product appears to be, in one sentence
- the features that exist, as a list a user would recognize
- the primary flows, end to end
- the entities and the states they move through
- external integrations, and which are real versus mocked
- the test inventory: how many, where, and what they actually assert

Do not consult the README's promise while doing this. Compare afterwards — that comparison is the first drift.

## 3. Confirm before analyzing

Show the reconstruction and ask plainly: **is this the product you think you are building?**

Everything downstream depends on this being right, and a wrong reconstruction produces confidently wrong drift. Take the correction, restate, and only then continue. This is also frequently where the session's real finding surfaces — the user reads their own product back and recognizes it has quietly become something else.

## 4. The three drifts

Every row is evidence-linked to a file, a line, or a test. A drift you cannot point at is a hypothesis; label it as one.

**Intent versus code.** The stated goal, protected outcome, and product promise against what the code does. Features built that nobody asked for, promises with no implementation, and a wedge that has quietly widened.

**Behaviors versus code.** Each `BH-###` against its implementation. A behavior with no implementation is either unbuilt or was silently dropped — the difference matters and only the user knows which.

**Behaviors versus tests.** Three findings, and the second is the one this skill exists for:

- **Coverage gap** — an `active` behavior with no covering test.
- **Orphan test** — a test naming no `BH-###` and asserting something no behavior asks for. An orphan is where a misread requirement hides: it is green, it looks like coverage, and it proves the wrong thing. Read each one and say what idea it actually encodes.
- **Stale test** — the behavior changed after the test was written; the test still asserts the superseded reading.

In a repository with no behavior spec, every test is technically an orphan. Do not report them one by one. Infer the behaviors the suite implies, present that as the de-facto specification, and ask where it diverges from intent.

## 5. Ask what matters

Rank by impact, irreversibility, rework risk, and whether you can infer the answer — the ranking in `../product-studio/references/qa-session.md`. Ask one at a time, 2–6 numbered options plus a free-text path, and always carry a recommendation with its confidence and what would change it. An agent that surfaces ten open questions without recommendations has handed the work back.

Ask immediately when a decision is consequential, irreversible, externally costly, or conflicts with the protected outcome. Otherwise infer, state the inference, and move on.

## 6. Re-attack the specification

Run the ten-class sweep in `../product-studio/references/spec-hardening.md` over the behaviors as they now stand, with one advantage the original Specify phase did not have: **the code is evidence.** Where implementation and behavior disagree, an ambiguity was resolved silently during coding and never recorded. Where two call sites handle the same case differently, the ambiguity was never noticed at all. Both become `AM-###` records.

Behaviors added here follow `../product-studio/references/behavior-discovery.md`. Resolutions become `D-###`, deferrals become `A-###` with a revisit trigger.

## 7. Verdict

One of four, evidence-linked to the drift that drove it:

- **Continue** — the build matches the intent; close the gaps listed and carry on.
- **Redirect** — the product is drifting from the vision; change scope or direction, and say what is abandoned.
- **Cut** — the intent holds but the scope has outgrown it; name what is removed.
- **Stop** — the evidence says this should not continue in its current form.

Fill `templates/reevaluation-verdict.md`. State what changes and, equally, what explicitly does not — an unchallenged part of the product is a finding too.

## 8. Write back

- Update `.product-studio/artifacts/behavior-spec.md` and re-mirror it to `docs/agent/BEHAVIORS.md`.
- **Retire behaviors; never delete them.** `Status: retired` is how the test that still asserts a removed behavior gets found. A deleted behavior takes its orphan test with it into invisibility.
- Record new decisions as `D-###` and new assumptions as `A-###`.
- Validate: `python3 scripts/validate_behavior_spec.py .product-studio/artifacts/behavior-spec.md --mirror docs/agent/BEHAVIORS.md`
- Update the `specify:` block in `.product-studio/project.yaml` — `behavior_spec`, `mirror`, `behaviors`, `open_ambiguities`, and `validated` (true only after the validator passed). `scripts/workflow_runner.py attach-spec` does the same thing for a JSON state file; the YAML state file is edited directly, like every other section.
- Write the verdict to `.product-studio/artifacts/reevaluation-verdict.md`.

If the session produced no `.product-studio/` state because the repository never had it, offer to initialize with `scripts/init_project.py` rather than writing a partial state file.

## Handoff

Offer the next action rather than assuming it:

1. Apply the test delta now — add the uncovered behaviors' tests, fix the stale ones, delete the orphans. `engineering-cycle` owns that work; a repository with no `docs/agent/CARD.md` should get one from `workflow-init` first, or the same drift returns unenforced.
2. Hand the changed behaviors to `product-studio` for a fresh MVP Build Plan and Implementation Brief.
3. Save the verdict and stop.
4. Create GitHub Issues from the deltas, one per behavior added or retired, published only after approval.

## Rules

Never report a check that did not run. If you could not execute the test suite, say so and mark the coverage findings as static analysis. Never claim a behavior is implemented without pointing at the code. Do not review code style, architecture, or performance here — say it is out of scope and note where a code review would be worth running.

Read `../product-studio/references/capabilities/reality-check.md` for the capability contract, `../product-studio/references/spec-hardening.md` and `../product-studio/references/behavior-discovery.md` for the specification protocols, and `../product-studio/references/qa-session.md` for the question loop. Supporting `templates/`, `schemas/`, and `scripts/` are packaged beside this skill and are also available at the repository root.
