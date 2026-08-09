# Personal Agent Rus 0.7.4-local.3 — Local Launch Gate

## Result

**Deterministic local gate: PASS.**

- PASS: 104
- FAIL: 0
- Environment-bound: 11
- Canonical local URL: `http://127.0.0.1:3100/`

## What changed

1. Fixed the Windows PowerShell 5.1 native-stderr failure that terminated `RUN-FIRST.cmd` while Docker Compose printed normal `Image ... Building` progress for the optional Code worker.
2. Optional Code startup now captures native output under `ErrorActionPreference=Continue`, records `$LASTEXITCODE` explicitly, restores the caller policy, and degrades Code instead of failing the whole runtime.
3. The optional Code readiness probe uses the same non-throwing native-command handling.
4. `code-worker` no longer blocks Core startup. Chat, Web, Research and Files can start if the isolated Code worker is unavailable.
5. Code runtime inventory is cached and resolved without starting a cold JVM on every `/health` request, eliminating the startup health race and repeated JVM overhead.
6. The public capability contract reports Code as `degraded` unless a real worker health probe succeeds.
7. `CODE-ACCEPTANCE.cmd`, `FULL-ACCEPTANCE.cmd` and `RELEASE-ACCEPTANCE.cmd` remain strict/fail-closed.
8. Unix-domain-socket IPC uses the explicit shared GID contract: Core UID/GID `10001`, worker socket GID `10001`, mode `0660`.
9. Existing `.env` image tags for Core, Browser and Code worker are migrated to this build while user secrets/config are preserved.
10. Release suites now execute process-heavy acceptance sequentially to avoid host-load-dependent false failures from simultaneous Playwright/JVM/code-worker test processes.
11. `LOCAL-START-001` now explicitly guards the PowerShell 5.1 native-stderr fail-soft contract.

## Deterministic evidence

The gate covers static/package contracts, Windows launcher contract, local-start architecture, distribution/update safety, API journeys, browser journeys, auth/providers, Web/Research, Files/Artifacts, Code sandbox behavior, Billing, Orchestrator/Deployment, monitoring and LAN contracts. The machine-readable result is in `docs/release-evidence/LOCAL-GATE-0.7.4-local.3.json`.

## Still requires the user's Windows/Docker reference machine

The following cannot truthfully be promoted to PASS in this build environment: real Windows browser runtime/security journey, Russian real-model stochastic behavior, complete reference lifecycle sequence, Windows reboot, live DTF canary/diagnostics, real Docker Code image acceptance, YooKassa live callback, real VPS SSH/DNS/HTTPS, and a physical LAN-device test.

For the immediate local objective, run `RUN-FIRST.cmd`. If it reaches **Personal Agent Rus is ready for local use**, open `http://127.0.0.1:3100/`. A Code warning is non-fatal for the local baseline; run `CODE-ACCEPTANCE.cmd` separately for the strict sandbox gate.
