# Optional adapters and fallbacks

| Capability | Preferred | Fallback |
|---|---|---|
| Web research | Host web tool with cited sources and access dates | Assumption map and research plan; never fabricate |
| Market probe | Host web tool with cited sources and access dates, in a fresh subagent context when available | Provisional mode with labeled low confidence plus a research plan |
| UX references | Mobbin, public research, or user references | Bundled pattern library and platform guidance |
| GitHub delivery | Connected GitHub integration, then `gh` CLI | `.product-studio/github/issue-plan.yaml` and `.md` |
| Native Apple build/test/run | XcodeBuildMCP (`mcp__XcodeBuildMCP__*`); offer to install it when a native Apple track is chosen | `xcodebuild` shell commands, then manual Xcode steps as unresolved verification items |
| Repository | Local repository inspection | Framework-neutral plan |
| Figma | User-provided references or design contract | Design Contract only |
| Workbench | Shared progress document, board, status, and review chat | Local YAML state and Markdown artifacts |

Record provider status in project state. Provider availability must never prevent a usable artifact.
