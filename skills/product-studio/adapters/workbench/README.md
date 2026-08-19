# Workbench adapter

Workbench is optional. `scripts/workbench_adapter.py` detects `WORKBENCH_URL`, reports capability status, and provides a deterministic local fallback. When a real Workbench capability is available, use it as a progress surface for phase status, tasks, review notes, and implementation evidence. Keep `.product-studio/project.json` and local Markdown artifacts canonical. If creation, access, authentication, or synchronization fails, continue locally and record `integrations.workbench.status: unavailable` with the fallback path.
