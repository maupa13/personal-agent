# Release Gate — Personal Agent Rus 0.8.0-alpha.1

## Result

- Deterministic records: **130**
- PASS: **130**
- FAIL: **0**
- Environment-bound: **12**
- Deferred for a later mandatory version: **1**

`0.8.0-alpha.1` is a Productization Foundation alpha, **not 1.0 RELEASE PASS**.

## Deterministic gates proved on shipped source bytes

- static/package policy;
- distribution/update contracts;
- Windows lifecycle command contract (static/dry-run);
- local-launch fail-soft contract;
- Core/API/auth/providers/Web/Research/Files/Code/Tasks persistence and isolation;
- Chromium USER journeys desktop/mobile viewport;
- server-side conversations/projects/search/export;
- USER/ADMIN onboarding and role-aware navigation;
- structured logging/redaction/rotation/correlation;
- billing foundation;
- orchestrator/VPS/LAN contracts;
- code-worker sandbox deterministic acceptance.

## Still environment-bound

- `FND-BROWSER-LIVE-REAL-001` — authoritative on reference Windows runtime
- `FND-BROWSER-LIVE-SECURITY-001` — authoritative on reference Windows Docker runtime
- `FND-RUS-LANGUAGE-001` — stochastic real-model language behavior is authoritative on reference Windows runtime
- `FND-REFERENCE-SEQUENCE-001` — runs RELEASE-ACCEPTANCE.cmd on reference Windows Docker runtime
- `FND-REBOOT-001` — requires real Windows reboot
- `WEB-011` — live DTF canary is authoritative on reference Windows with external internet
- `WEB-012` — live Web diagnostics are captured by WEB-ACCEPTANCE.cmd on reference Windows
- `CODE-LIVE-001` — real Docker code-worker image with Python/Java/PowerShell is authoritative on reference Windows Docker runtime
- `BILL-LIVE-001` — requires real YooKassa merchant credentials plus public HTTPS callback/webhook endpoint
- `DEPLOY-LIVE-001` — requires a real Linux VPS, SSH credential, DNS and public HTTPS
- `LAN-LIVE-001` — requires a physical second LAN device and Windows Private-network firewall
- `CONV-003` — requires same account on a second physical LAN device

## Deferred by specification

- `UX-009` — mandatory from `0.8.0-beta.1`: complete cross-surface state matrix is a pre-beta product quality gate

## Evidence

Machine-readable results and per-suite logs are in `docs/release-evidence/0.8.0-alpha.1/`.
