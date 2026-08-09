# Architecture

`Browser/PWA -> Personal Agent Core -> Request/Intent -> Context -> Planner -> Policy/Permission -> Capability/Tool/Provider Routers -> Workers -> Verification -> Artifact/Result`.

Core is a modular monolith first. Heavy/security-sensitive functions (browser, code, media) are isolated workers. USER never sees Docker/provider/model internals. Registries are first-class abstractions: Capability, Tool, Provider, Model, Connector, Skill, Agent.

Current v0.3 vertical slice adds `web.search`, `web.fetch`, `browser.navigate`, `research.basic`.
