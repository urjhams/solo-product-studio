# Accessibility Checklist

Tickable bar for anything user-facing, cited by `references/browser-verification.md` and
`references/ship.md`. The stack-neutral section applies regardless of platform; run the marked
platform section(s) that match what you shipped.

## Stack-neutral bar

- [ ] Every interactive element is reachable and operable by keyboard/switch/assistive input, not
      just by pointer or touch
- [ ] Focus order matches visual/logical order, and focus is visible at every stop
- [ ] Every control has an accessible name — not a placeholder standing in for a label
- [ ] Text and UI meet minimum contrast (4.5:1 body text, 3:1 large text/UI elements)
- [ ] Empty states and error states are meaningful — they say what happened and what to do next,
      not a blank screen or a raw error code
- [ ] Motion, parallax, and autoplay respect the user's reduced-motion preference
- [ ] Layout holds at 200% text scaling / the largest supported dynamic text size — nothing
      clipped, truncated, or overlapping

<!-- stack: web -->
## Web (WCAG 2.1 AA)

- [ ] Semantic HTML used before ARIA (`<button>`, not `<div onclick>`)
- [ ] ARIA roles/states used only where semantic HTML can't express the structure, and kept in
      sync with actual component state
- [ ] Heading hierarchy is sequential — h1 -> h2 -> h3, no skipped levels
- [ ] Dynamic content changes are announced via ARIA live regions where relevant
- [ ] Verified against the live accessibility tree, not just visually —
      `references/browser-verification.md`

<!-- stack: apple -->
## Apple

- [ ] Dynamic Type supported end to end; layout doesn't clip or truncate at the largest sizes
- [ ] VoiceOver: every control has a label, trait, and value that make sense read aloud; custom
      controls implement the accessibility protocol instead of relying on their visual affordance
- [ ] Safe areas respected on every device class — notch, Dynamic Island, home indicator included
- [ ] System gestures (edge swipes, home indicator, Control Center) are never captured or blocked
      by an app-level gesture recognizer

## Quality: avoid the AI aesthetic

A screen can clear every box above and still read as generated rather than designed. Watch for:

- [ ] No generic purple/indigo gradient standing in for an actual color decision
- [ ] Not everything is `rounded-2xl` — corner radius varies with a component's role and size
- [ ] Padding matches content density, not a uniform oversized default applied everywhere
- [ ] Layout isn't a stock card grid by default — the content's own shape gets a say
- [ ] No lorem ipsum or placeholder copy left in a state that looks shippable
