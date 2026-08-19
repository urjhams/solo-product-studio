# Framework research

## Supported primitives

The portable baseline is a directory containing `SKILL.md` with YAML frontmatter (`name` and `description`) plus relative supporting files. Codex discovers skills from its skill directories and supports optional `agents/openai.yaml`. Claude Code and the Agent Skills ecosystem use self-contained skill directories. OpenCode discovers project and global `SKILL.md` directories and loads supporting files on demand.

## Unsupported or host-specific primitives

There is no portable nested-agent delegation protocol, shared database, or universal slash-command specification. Codex plugin manifests, Claude-specific plugin metadata, OpenCode permissions, MCP connectors, and app integrations are host-specific.

## Selected architecture

`product-studio` is the only public skill. Logical agents and capabilities are internal Markdown contracts under `references/`, with scripts for deterministic local state, capability discovery, validation, and issue export. The workflow itself is instruction-driven so it can use each host's native tools.

## Installation model

Copy or symlink the canonical skill folder into a host's project or global skill directory. The Codex plugin wraps the same folder; it is not a second implementation.

## Invocation model

Start with `/product-studio` where the host exposes slash skills. Otherwise use `Use product-studio to help me build a product.` The first response is always the QA intake.

## Tool integration model

Use available web research, GitHub connector, or `gh` CLI only after capability detection. Fall back to local research plans, bundled UX patterns, and local issue exports.

## Persistence model

Project state is local YAML at `.product-studio/project.json`; artifacts are Markdown. No database or hosted backend is required.

## Testing approach

Validate portable metadata, required resources, installation layouts, state helpers, fallback selection, and scripted scenario expectations with Python's standard library.
