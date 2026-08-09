# Personal Agent Rus 0.7.4-local.1 — Local Launch Gate

## Result

**Deterministic local gate: PASS.**

- PASS: 104
- FAIL: 0
- Environment-bound: 11
- Canonical local URL: `http://127.0.0.1:3100/`

## What changed

1. `code-worker` no longer blocks Core startup. Chat, Web, Research and Files can start if the isolated Code worker is unavailable.
2. The public capability contract reports Code as `degraded` unless a real worker health probe succeeds.
3. `CODE-ACCEPTANCE.cmd`, `FULL-ACCEPTANCE.cmd` and `RELEASE-ACCEPTANCE.cmd` remain strict/fail-closed.
4. Unix-domain-socket IPC now uses an explicit shared GID contract: Core UID/GID `10001`, worker socket GID `10001`, mode `0660`.
5. Existing `.env` image tags for Core, Browser and Code worker are migrated to this build while user secrets/config are preserved.
6. Added deterministic `LOCAL-START-001` regression coverage.

## Deterministic evidence

The gate covers static/package contracts, Windows launcher contract, local-start architecture, distribution/update safety, API journeys, browser journeys, auth/providers, Web/Research, Files/Artifacts, Code sandbox behavior, Billing, Orchestrator/Deployment, monitoring and LAN contracts. The machine-readable result is in `docs/release-evidence/LOCAL-GATE-0.7.4-local.1.json`.

## Still requires the user's Windows/Docker reference machine

The following cannot truthfully be promoted to PASS in this build environment: real Windows browser runtime/security journey, Russian real-model stochastic behavior, complete reference lifecycle sequence, Windows reboot, live DTF canary/diagnostics, real Docker Code image acceptance, YooKassa live callback, real VPS SSH/DNS/HTTPS, and a physical LAN-device test.

For the immediate local objective, run `RUN-FIRST.cmd`. If it reaches **Personal Agent Rus is ready for local use**, open `http://127.0.0.1:3100/`. A Code warning is non-fatal for the local baseline; run `CODE-ACCEPTANCE.cmd` separately for the strict sandbox gate.
