# Platform decision

Decide the platform before the Design Contract. Choose a surface, then a track inside it. Bias toward the fastest good MVP and only pay for depth the product actually needs. Record the outcome as a decision with a revisit trigger.

## Step 1 — surface

| Leans web | Leans mobile |
|---|---|
| Recurring business workflow | Phone-in-hand context of use |
| Buyer and user are different people | Push-driven habit loop |
| Keyboard-heavy data entry, large screens | Offline-first usage |
| SEO or shareable links matter | Device APIs: camera pipeline, background location, HealthKit, sensors, on-device ML |
| Roles, admin, and permissions | Widgets or lock-screen presence |
| No device capability required | Consumer app-store distribution |

If both apply, pick the one to ship first and say which. Never build both inside an MVP timebox.

## Step 2 — mobile track

- **Expo (React Native)** — the default. Product MVP, startup app, CRUD or workflow app, fast iOS-and-Android launch.
- **Flutter** — a highly custom visual and motion identity shared across both platforms, where the look *is* the product.
- **Native SwiftUI** — iOS-first, deep Apple integration, demanding performance, or a premium platform-specific experience.

Score native reliance against this checklist: background execution, HealthKit, ARKit, on-device CoreML, widgets, Live Activities, App Intents or Siri, a watchOS companion, realtime graphics or a custom camera pipeline, sub-16ms bespoke rendering, deep Apple-ecosystem sync.

**Rule: two or more deep native dependencies, or one that is the hero moment, means native from the start. Otherwise Expo.**

A single ordinary native need does not disqualify Expo — config plugins, a development build, and custom native modules cover most of them. Say which escape hatch applies instead of escalating to native by reflex.

Flutter overrides Expo only when the bespoke shared visual identity is the hero moment. It does not win on "we want it to look nice".

## Step 3 — web track

- **SaaS or workflow MVP default: Next.js (App Router) + hosted Postgres + hosted auth.**
- **Responsive web or PWA** when app-store distribution and device APIs are not required. It substitutes for a mobile app in the MVP.
- Deviate when there is heavy realtime, a non-JavaScript team, or an existing backend to build on.

## Prototype override

In Prototype mode the tiebreaker is **minutes to a clickable app on a real device**, with product fit used only to break ties. Expo beats native iOS even when the eventual product would be native — validating the idea in Expo does not commit the product to it, and the native call is re-decided after the verdict. Web prototypes use Next.js or Vite with in-memory state: no auth provider, no hosted database, no ORM.

The only escalation to native SwiftUI or Flutter is when the capability being validated *is* the native capability, or when the user's only configured toolchain is that one.

Full rules: `references/prototype-mode.md`.

## Hackathon override

In Hackathon mode the tiebreaker is not product fit, it is **minutes to a running app on the demo device, counting setup**. Ask what the user already has installed before recommending anything; existing local setup outranks product fit here and nowhere else.

Mobile, in order:

1. **Expo** — `npx create-expo-app`, then run in Expo Go by scanning a QR from a physical phone. No Xcode, no Android Studio, no emulator, works from any OS, both platforms free.
2. **Native SwiftUI** — only when the demoer is already on a Mac with Xcode and the demo is iOS-only. Nothing to install.
3. **Flutter** — only if the SDK and a platform toolchain are already configured. From cold it needs the Flutter SDK plus Xcode and/or Android Studio plus an emulator. Its Step 2 advantage rarely pays back inside 2–8 hours.

Web: Next.js with local or in-memory state. No auth provider, no hosted database, no billing — scaffolding cost with no demo value.

**Exception:** if the native capability *is* the wow moment (ARKit, HealthKit, a Live Activity, a camera pipeline), go native. The demo does not exist without it.

Still record the decision, with a revisit trigger noting the choice was made on demo speed and must be re-decided if the project continues past the demo.

## Native Apple toolchain

When the track is native SwiftUI or UIKit on any Apple platform, check for XcodeBuildMCP (`mcp__XcodeBuildMCP__*`) before drafting the MVP Build Plan. It is the difference between a native plan whose builds and tests the agent can actually run and one that hands every check back to the user.

If it is missing, ask once whether to install it, then continue either way: install now, use `xcodebuild` from the shell, or write manual Xcode steps as unresolved verification items. Record the outcome in `capabilities.integrations.xcodebuild-mcp`. Never report a build, test, or simulator run that did not happen.

In Prototype and Hackathon modes an unconfigured Apple toolchain counts as setup cost against the native track — one more reason Expo wins there.

Read `adapters/xcodebuild-mcp/README.md` for detection, the install prompt, and usage rules.

## Always

- Record the choice as `D-###` with rationale, the rejected alternative, and a **revisit trigger** — the concrete signal that would flip it.
- If native reliance is uncertain, record `A-###` and run a smallest-spike check via `workflows/technical-feasibility.md` rather than guessing.
- A mode switch re-opens this decision. See `references/market-probe.md`.
- Mobile track reads `pattern-library/mobile-patterns.yaml`; web track reads `pattern-library/saas-patterns.yaml`.

Canonical state key: `constraints.platform: {surface, track, stack, rationale, revisit_trigger}` in `.product-studio/project.yaml`.
