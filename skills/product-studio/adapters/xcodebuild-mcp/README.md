# XcodeBuildMCP adapter

Optional but strongly preferred provider for any **native Apple** track — SwiftUI or UIKit on iOS, macOS, watchOS, tvOS, visionOS. It gives the agent build, run, test, simulator, log, and UI-automation control over an Xcode project, so a native plan can actually be verified instead of only written.

## When to check for it

Check as soon as the platform decision lands on a native Apple track, **before** drafting the MVP Build Plan or the Implementation Brief. The answer changes the plan's verification section: with the adapter, verification items name real build and test runs; without it, they name manual Xcode steps the user must perform.

Also check before starting implementation on an existing native project.

## Detection

Look for tools named `mcp__XcodeBuildMCP__*` in the host tool list — for example `discover_projs`, `list_schemes`, `build_sim`, `build_run_sim`, `test_sim`, `screenshot`, `snapshot_ui`. Never assume availability from the presence of Xcode alone; the MCP server is separate.

Record the result in project state under `capabilities.integrations.xcodebuild-mcp` as `available`, `not-installed`, or `partial` when only some workflow groups are enabled.

## If it is not installed

Ask the user once whether to install it. Do not install it yourself and do not stall the session on the answer — offer the three options and continue with whichever they pick:

1. Install it now, then continue with verified native builds.
2. Continue without it, using `xcodebuild` shell commands.
3. Continue plan-only, with manual Xcode steps written into verification.

Point the user at the project for the current install command rather than guessing flags: <https://github.com/cameroncooke/XcodeBuildMCP>. For Claude Code the usual one-liner is:

```bash
claude mcp add XcodeBuildMCP -- npx -y xcodebuildmcp@latest
```

The server needs a restart of the host before its tools appear. If the user declines or the install fails, say so plainly and fall back — never claim a build or test ran when it did not.

## Usage rules

- Call `session_show_defaults` before the first build, run, or test call in a session; use `discover_projs` only when the project or workspace is missing or wrong.
- Set session defaults once (project or workspace, scheme, simulator) instead of repeating parameters.
- Prefer these tools over raw `xcodebuild` shell commands whenever both are available.
- Device, macOS, debugging, and UI-automation workflows may be disabled even when the server is present. When a needed tool is missing, report it as `partial` and tell the user which workflow group to enable rather than silently switching to the shell.
- Screenshots and UI snapshots are the cheapest way to prove a native flow runs. Use them as verification evidence in the Implementation Brief.

## Fallback

`xcodebuild -scheme <scheme> -destination 'platform=iOS Simulator,name=<device>' build test` via the shell, or, if the host has no shell, manual Xcode steps written as explicit verification items with `status: unresolved` until the user confirms them.
