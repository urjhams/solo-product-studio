# Doubt

A confident output is not a correct one. Open this before any non-trivial decision stands — while
course-correction is still cheap, not after it's committed. This is not Gate 2. Gate 2 is a verdict
on a finished diff; doubt is the in-flight posture that runs *while you're deciding*, one decision
at a time.

## When

A decision is non-trivial when at least one is true:

- It introduces or modifies branching logic.
- It crosses a module or service boundary.
- It asserts a property the type system or compiler cannot verify (thread safety, idempotence,
  ordering, invariants).
- Its correctness depends on context a future reader can't see.
- Its blast radius is irreversible — a production deploy, a data migration, a public API change.

**Skip it for:** mechanical operations (rename, format, file move), a clear unambiguous
instruction, reading or summarizing existing code, one-line changes with obvious correctness,
running tests or listing files. Doubting every keystroke means shipping nothing — the skill
applies to non-trivial decisions, not all of them.

## The Cycle

```
Doubt cycle:
- [ ] CLAIM      — wrote the claim + why it matters
- [ ] EXTRACT    — isolated artifact + contract, stripped reasoning
- [ ] DOUBT      — invoked a fresh-context reviewer with an adversarial prompt
- [ ] RECONCILE  — classified every finding against the artifact text
- [ ] STOP       — met a stop condition (trivial findings, 3 cycles, or user override)
```

### CLAIM — surface what stands

Name the decision in two or three lines:

```
CLAIM: "The new caching layer is thread-safe under the read-heavy workload described in the spec."
WHY THIS MATTERS: a race here corrupts user data and is hard to detect in QA.
```

If you can't write it that compactly, you have a vibe, not a decision — surface it before
scrutinizing it.

### EXTRACT — smallest reviewable unit

A fresh-context reviewer needs the **artifact** and the **contract**, not the journey.

- Code: the diff or the function, not the whole file.
- Decision: the proposal in 3–5 sentences plus the constraints it must satisfy.
- Assertion: the claim plus the evidence that supposedly supports it — kept distinct from the
  CLAIM block above, which is the hypothesis under scrutiny, not the input.

Strip your reasoning. Hand over conclusions and you'll get back validation of your conclusions. If
the unit is too big to hold in one read — a 500-line diff — decompose first.

### DOUBT — invoke the fresh-context reviewer

Framing decides the answer, so the prompt must be adversarial:

```
Adversarial review. Find what is wrong with this artifact.
Assume the author is overconfident. Look for:
- Unstated assumptions
- Edge cases not handled
- Hidden coupling or shared state
- Ways the contract could be violated
- Existing conventions this might break
- Failure modes under unexpected input

Do NOT validate. Do NOT summarize. Find issues, or state
explicitly that you cannot find any after thorough examination.

ARTIFACT: <paste artifact>
CONTRACT: <paste contract>
```

**Pass ARTIFACT + CONTRACT only. Do NOT pass the CLAIM.** Handing the reviewer your conclusion
biases it toward agreement — it must independently determine whether the artifact satisfies the
contract. A fresh subagent spawned with no shared context is what makes this fresh; briefing it
with your reasoning first defeats the point.

### RECONCILE — fold findings back

The reviewer's output is data, not a verdict — you are still the one deciding. Re-read the artifact
text against each finding before classifying; rubber-stamping the reviewer is the same failure mode
as ignoring it. Classify in this precedence order, first match wins:

1. **Contract misread** — the reviewer flagged something because the CONTRACT was unclear or
   incomplete. Fix the contract, re-classify next cycle.
2. **Valid + actionable** — a real issue. Change the artifact, re-loop.
3. **Valid trade-off** — real, but the cost of fixing exceeds the cost of accepting. Document the
   trade-off explicitly.
4. **Noise** — correct under context the reviewer didn't have. Note it, and ask: would adding that
   context to the contract have prevented the false flag?

A fresh reviewer can be wrong because it lacks context. Don't defer just because it's fresh.

### STOP — bounded loop, not recursion

Stop when the next iteration returns only trivial or already-considered findings, **or** 3 cycles
are done, **or** the user explicitly says ship it.

If cycle 3 still surfaces substantive issues, the artifact may not be ready — surface that to the
user; three unresolved cycles is information, not a reason to grind a fourth alone. If 3 feels
insufficient because the artifact is large, the artifact is too big: go back to EXTRACT and
decompose. Don't lift the bound.

## Doubt vs. task-evaluator

Same principle, two different places in the loop. `task-evaluator` is Gate 1: it grades a finished
task against re-derived acceptance criteria, brief-starved on purpose — task statement +
done-criteria + branch/base only, never the implementation narrative, so it can't be talked into
agreeing with the author's story. Doubt applies that same starvation *earlier and smaller*: strip
the CLAIM (the narrative) from what the fresh reviewer sees, one decision at a time, while the
decision is still cheap to reverse. `task-evaluator` is POST-HOC per-task; doubt is IN-FLIGHT
per-decision. By the time a diff reaches Gate 1 or Gate 2, doubt should already have caught the
wrong turns — those gates are backstops, not where doubt lives.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'm confident, skip the doubt step" | Confidence correlates poorly with correctness on novel problems. Certainty is exactly when blind spots hide. |
| "Spawning a reviewer is expensive" | Debugging a wrong commit in production is more expensive. The check is bounded; the bug isn't. |
| "The reviewer will just nitpick" | Only if unscoped. Constrain the prompt to "issues that would make this fail under the contract." |
| "I'll do doubt at the end with review" | Gate 2 is a final verdict. Doubt catches wrong directions early, when course-correction is cheap — by PR time it's too late. |
| "If I doubt every step I'll never ship" | The skill applies to non-trivial decisions, not every keystroke — see When, above. |
| "The reviewer disagreed so I was wrong" | The reviewer lacks your context. Disagreement is information, not a verdict — reconcile, then decide. |

## Red Flags

- Spawning a fresh-context reviewer for a one-line rename or formatting change.
- Treating reviewer output as authoritative without re-reading the artifact text.
- Looping more than 3 cycles without escalating to the user.
- Prompting the reviewer with "is this good?" instead of "find issues."
- Skipping doubt under time pressure on a high-stakes decision.
- Re-spawning fresh-context on an unchanged artifact — same findings, you're stalling.
- **Doubt theater:** across 2+ cycles with substantive findings, zero were classified actionable.
  You're validating, not doubting — stop and escalate.
- Doubting only after committing — that's Gate 2, not doubt-driven.
- Stripping the contract from the reviewer's input, or passing it the CLAIM.

## Interaction with Other References

- `references/review.md` — complementary, not redundant. Review is post-hoc PR verdict; doubt is
  in-flight per-decision. Use both.
- `references/sources.md` — that reference verifies *facts about frameworks* against official
  docs; doubt verifies *your reasoning about the artifact*. One checks the API exists, the other
  checks you used it correctly under the contract.
- `references/build-loop.md` — TDD's RED step is doubt made concrete: a failing test is a disproof
  attempt. When it applies, that failing test *is* the doubt step for a behavioral claim.
- `docs/agent/RUNBOOKS.md#agent-delegation` — the spawn rules (foreground, self-contained brief,
  never `STATE.md`) apply to a doubt reviewer exactly as they apply to any other subagent.

## Verification

- [ ] Every non-trivial decision (per the definition above) was named as a CLAIM before it stood
- [ ] At least one fresh-context review happened per non-trivial artifact (a RED-step failing test
      satisfies this for behavioral claims)
- [ ] The reviewer received ARTIFACT + CONTRACT only — not the CLAIM, not your reasoning
- [ ] The reviewer's prompt was adversarial ("find issues"), not validating ("is it good")
- [ ] Findings were classified against the artifact text using the precedence order — not
      rubber-stamped
- [ ] A stop condition was met: trivial findings, 3 cycles, or user override
