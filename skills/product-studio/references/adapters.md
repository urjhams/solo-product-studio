# Optional adapters and fallbacks

| Capability | Preferred | Fallback |
|---|---|---|
| Web research | Host web tool with cited sources and access dates | Assumption map and research plan; never fabricate |
| UX references | Mobbin, public research, or user references | Bundled pattern library and platform guidance |
| GitHub delivery | Connected GitHub integration, then `gh` CLI | `.product-studio/github/issue-plan.yaml` and `.md` |
| Repository | Local repository inspection | Framework-neutral plan |
| Figma | User-provided references or design contract | Design Contract only |
| Workbench | Shared progress document, board, status, and review chat | Local YAML state and Markdown artifacts |

Record provider status in project state. Provider availability must never prevent a usable artifact.
