# Personal Agent product family

Canonical family: **Personal Agent**.

Current edition: **Personal Agent Rus** (`personal-agent-rus`, locale `ru-RU`).

The shared runtime is **Personal Agent Core**. Edition-specific branding, policy, defaults and integrations must stay outside provider/model internals so future editions can reuse the same Core, for example `personal-agent-eu`, `personal-agent-us` or enterprise/private distributions.

Normal USER surfaces must not expose provider names, raw model IDs, container names or runtime internals. Those remain ADMIN/Developer concerns.
