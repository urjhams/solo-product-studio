# Design Prompt

Self-contained. Paste it into Claude desktop, `/design`, or any other design tool with no other
context and it must still produce the right canvas — so inline every value below rather than
referring to the Design Contract, the state file, or this repository.

---

## Prompt

Design a multi-artboard canvas for the product below. One artboard per screen, laid out in the order
given. Mark the magic-moment screen.

**Product:** <name> — <one line>
**Platform:** <native iOS / Expo / Flutter / Next.js / responsive web> — follow its conventions
**Promise:** <the product promise>
**Magic moment:** <one sentence, what the user sees>
**Customer:** <who this is for, from the Define customer slot>

### Artboards, in order

1. Onboarding
   - <step 1 — what the user sees, what it asks for>
   - <step 2>
   - <step 3>
2. Core flow
   - <screen> — <what it does>
   - <screen — MAGIC MOMENT> — <what the user sees here>
   - <screen>
3. Landing page / store listing
   - Headline: <the outcome, in the customer's words>
   - Subhead: <the mechanism, one line>
   - Proof points: <three, cited>
   - Primary CTA: <first step of the onboarding path>
   - Objection handled: <the strongest evidence against, and the answer>

### Three principles — every screen obeys all three

1. <principle>
2. <principle>
3. <principle>

### Visual brief

```yaml
visual_brief:
  desired_feeling:
  visual_metaphor:
  emotional_tone:
  content_density:
  contrast_level:
  image_treatment:
  motion_character:
  signature_element:
  avoid: []
```

### Design system

- Type scale:
- Spacing scale:
- Color roles (surface / content / accent / state):
- Components used:
- Signature component:
- Motion:

### Accessibility floor

<contrast, target size, dynamic type / zoom, focus order, and anything the customer slot requires>

### Do not

- Invent features not listed above.
- Show a state the screen list does not name — loading, empty, and error states only where listed.
- Copy a competitor's interface.

---

## Provenance

- Design Contract: `.product-studio/artifacts/<design-contract>.md`
- Canvas provider: <provider that actually ran, or `none`>
- Canvas URL: <url, or `not published`>
