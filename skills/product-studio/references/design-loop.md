# Design loop

The Design pillar turns the six Define slots into something a person can look at. It produces one
Design Contract, one Design Prompt, and — where the host has a canvas provider — a published canvas
the user can open and keep adjusting.

Run it after the define checkpoint clears. Read `references/capabilities/product-to-pixels.md` for
the capability contract and `templates/design-contract.md` for the artifact.

## Four slots

### 1. Magic moment

The moment the product proves its promise. Earlier revisions of this bundle called it the hero
moment; the Hackathon done bar still uses that word for the same thing.

It comes from the `mechanism` slot, not from the feature list: the mechanism says what the product
does, the magic moment is the first time the user *sees* it do that. Two tests:

- **Reachable** — a first-time user gets there inside the onboarding path below, from a cold start,
  without being told what to do. A magic moment three screens past a signup wall is a magic moment
  nobody reaches.
- **Attributable** — the user can tell it was the product that did it. An outcome the user cannot
  distinguish from what would have happened anyway does not land, however good it is.

Write the moment as one sentence naming what the user sees, not what the system computes.

### 2. Onboarding path

The shortest route from cold start to the magic moment, one step per screen, with what each step
costs the user and what it earns them. Then the cut list: everything asked for before the magic
moment that does not have to be.

Load the `onboarding` and `progressive-profiling` entries in `pattern-library/mobile-patterns.yaml`
rather than re-deriving the guidance — they already carry the failure modes (long introductions,
premature permissions, unclear next action) and the accessibility notes, and they are platform-neutral
despite the filename. On a SaaS track add `team-invitation` and `billing-state` from
`pattern-library/saas-patterns.yaml`; it has no onboarding entry of its own.

Permissions, account creation, and personalization each need a reason to sit before the magic moment
rather than after it. Default is after.

### 3. Landing page / store listing

Positioning copy, and an artboard in the canvas so the page gets mocked rather than imagined. The
copy comes straight out of Define — if a line here cannot be traced to a slot, either the line is
invented or the slot is thin:

| Line | Source |
|---|---|
| Headline | `outcome`, in the customer's own words |
| Subhead | `mechanism`, one line |
| Three proof points | `proof` — cited, not asserted |
| Primary CTA | the first step of the onboarding path |
| Top objection + answer | the strongest evidence *against*, from `proof` |

For an app-store track, also fill the store variant: name, subtitle, promo text, and one caption per
screenshot. The captions are the screenshot brief — write them before choosing which screens to
capture, not after.

Prototype and Hackathon cut this slot by default. Say so in the cut list rather than skipping it
silently.

### 4. Design system

One section, not scattered lines: type scale, spacing scale, color roles (surface, content, accent,
state), the component inventory the screen list actually needs, the signature component, and the
motion character. Everything here is implementation input — the Behavior Spec and the MVP slices
both read it.

Keep it to what the screen inventory uses. A token set larger than the product is a maintenance cost
with no user on the other end of it.

## The Design Prompt

Always written, to `.product-studio/artifacts/design-prompt.md`, from `templates/design-prompt.md`.

It is the portable half of this phase: a self-contained prompt the user can paste into Claude
desktop, or any other design tool, and get a canvas out of — with no access to this repository, this
session, or the state file. Everything it needs is inlined: promise, magic moment, the artboard list,
the visual brief YAML, the three principles, the design system, and the platform conventions for the
selected track.

Write it before invoking any provider. It is the artifact; the canvas is a rendering of it.

## The canvas

Preferred provider is the host's `/design` canvas skill, which publishes a pan/zoom Artifact the user
can select elements in, edit, and re-export. `references/adapters.md` carries the row.

Procedure:

1. Write the Design Prompt.
2. Check for a canvas provider on this host. If there is one, invoke it with the prompt as written —
   not a paraphrase, so what the user sees and what the artifact says stay the same thing.
3. Record `design.prompt`, `design.canvas_provider`, and `design.canvas_url` in
   `.product-studio/project.json`. Leave `canvas_provider` empty when none ran. Never record a
   provider that did not actually run, and never describe a canvas that was not published.
4. If no provider exists, hand the user the prompt path and say plainly that the canvas is theirs to
   run elsewhere. That is the fallback working, not the phase failing.

Artboard order in the prompt: onboarding steps, then the core flow with the magic moment screen
marked, then the landing/store page.

**A published canvas counts as `design.evidence`.** Wherever the compiled profile sets
`design.gate: evidence_required`, the done bar already asks for a clickable prototype or a short
usability check before the design checkpoint clears; a canvas the user has actually looked at and
responded to satisfies it. A canvas nobody has opened does not — evidence is the response, not the
artifact.

## Gate

`references/done-bars.md` under `## Design`. The design checkpoint additionally blocks with
`design-evidence-missing` wherever `design.gate: evidence_required`, which `risk_tier: high` derives
automatically.

## Handoff

Into the Specify phase. The magic moment and the onboarding path are where behavior discovery starts
— they are the flow with the most branches per screen and the least tolerance for a wrong reading.
