# Personal Agent Rus roadmap after Docker foundation

Quality rule: every milestone is Specification -> architecture -> acceptance -> implementation -> automated tests -> user E2E -> PASS. No PASS, no next layer.

1. **0.2 Runtime Foundation (current)** — Docker/browser product, admin-only model registry, deterministic lifecycle, Windows command self-test, release/user E2E gate.
2. **0.3 Orchestrator** — durable tasks, states, planner/DAG, progress/SSE, retries/cancel, verification semantics.
3. **0.4 Web & Research** — SearXNG/browser workers, source evidence, freshness, citation/results contract, adversarial site tests.
4. **0.5 Files & Artifacts** — workspace, TXT/MD/JSON/CSV/PDF/DOCX/XLSX/PPTX create/read/edit/validate, artifact cards and versioning.
5. **0.6 Code & Data** — Python/PowerShell/Java execution, sandbox/permissions, tests, ETL, logs and rollback.
6. **0.7 Vision/Image/Audio/Video** — vision, image generation/editing, STT/TTS, optional video as independent capabilities.
7. **0.8 Automation & Actions** — permissioned external actions, schedules, audit, idempotency and recovery.
8. **0.9 Multi-provider & hardware profiles** — Ollama/llama.cpp/LM Studio/OpenAI-compatible/remote fallback; automatic resolver; 6/8/12/16-24 GB profiles.
9. **Beta** — update/backup/restore, multi-user/admin security, LAN/mobile/PWA, clean Windows VM matrix, offline/restricted-network scenarios.
10. **RC/1.0** — prebuilt GHCR images, signed Windows Setup.exe as a thin bootstrap over the same Docker runtime, documentation/site/releases/support.
