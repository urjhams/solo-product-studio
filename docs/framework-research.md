# Framework research

The portable contract is a self-contained directory with `SKILL.md`, YAML frontmatter, and relative supporting files. Codex adds plugin metadata and `agents/openai.yaml`; Claude Code and compatible runtimes use skill directories; OpenCode supports project/global skill directories and on-demand loading. Nested agents, MCP availability, slash commands, and permissions are host-specific. Solo Product Studio keeps those differences in adapters and uses one canonical workflow.
