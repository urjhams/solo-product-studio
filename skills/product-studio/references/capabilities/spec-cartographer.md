# spec-cartographer

Purpose: turn an approved Design Contract into a Behavior Spec whose ambiguities are all closed, so the MVP plan and its tests encode the intended product rather than a plausible misreading of it.

Inputs: Design Contract, product definition, house rules, prior decisions and assumptions, repository and existing tests when one exists.

Outputs: behaviors with `BH-###` ids (Given/When/Then, observable signals, priority, test level, source), an ambiguity register with `AM-###` ids (two readings, user-visible difference, decision needed, recommendation, resolution), new `D-###` and `A-###` records, and the `docs/agent/BEHAVIORS.md` mirror.

Sequence: branch sweep per in-scope capability (`references/behavior-discovery.md`) → ten-class ambiguity sweep (`references/spec-hardening.md`) → escalate what cannot be resolved → record resolutions → second sweep until a pass finds nothing new.

Gate: every in-scope capability has behaviors; every behavior has a constructible Given/When/Then, an observable signal, and a source; zero ambiguities in `open`; every `resolved` cites a `D-###` and every `deferred` cites an `A-###` with a revisit trigger; the mirror is byte-identical. Verify with `scripts/validate_behavior_spec.py`.

Product scope and behavior scope are separate. Do not trade a behavior away to hit a timebox — defer it with an assumption and a revisit trigger so the gap is visible.

In Prototype mode this is the short form: 3–7 behaviors for the one flow, only the `term`, `boundary`, and `visibility` ambiguity classes, `--prototype` on the validator, and the gate warns instead of blocking. See `references/prototype-mode.md`.

Handoff: `mvp-forge`. The MVP Build Plan cuts its vertical slices along behaviors and cites `BH-###` in the Test column.
