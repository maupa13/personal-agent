# Release Gate — Personal Agent Rus 0.8.0-alpha.2

## Verdict

**Deterministic authoritative suites: 11/11 PASS.**  
**Test records: 143 PASS / 0 FAIL; 129 unique PASS IDs.**

The monolithic aggregator was interrupted by the current execution-harness timeout after its Browser suite had already completed PASS. This is not counted as a product PASS or FAIL; each authoritative suite was run as a separate process and exited successfully.

## Alpha.2 scope proved

- backend-authoritative entitlements and mode gates;
- Light/Medium/Pro capability separation;
- entitlement persistence and Admin overrides;
- Argon2id + legacy PBKDF2 migration path;
- remember-me, throttling, session inventory/revocation;
- registration-policy and Admin user/session controls;
- LAN state/address/QR contracts;
- PostgreSQL server compose/schema/config **foundation**;
- regression of product shell, conversations/projects/onboarding/logging;
- Core API, Chromium USER journey, Code sandbox, Billing, deployment and Windows command contracts.

## PostgreSQL truth

Local/offline remains **SQLite canonical**. PostgreSQL is deliberately **not** called runtime-ready in alpha.2. `PG-RUNTIME-001` stays `NOT_IMPLEMENTED` until Core repositories, SQLite→PostgreSQL migration, restart, backup/restore and rollback are proven.

## Environment-bound gates

- `FND-BROWSER-LIVE-REAL-001` — authoritative on reference Windows runtime
- `FND-BROWSER-LIVE-SECURITY-001` — authoritative on reference Windows Docker runtime
- `FND-RUS-LANGUAGE-001` — stochastic real-model behavior is authoritative on reference Windows runtime
- `FND-REFERENCE-SEQUENCE-001` — runs full lifecycle on reference Windows Docker runtime
- `FND-REBOOT-001` — requires real Windows reboot
- `WEB-011` — live DTF canary requires external internet on reference runtime
- `WEB-012` — live Web diagnostics reference runtime
- `CODE-LIVE-001` — real packaged Docker code worker on reference Windows
- `BILL-LIVE-001` — real YooKassa credentials and public HTTPS webhook required
- `DEPLOY-LIVE-001` — real Linux VPS, DNS, SSH and HTTPS required
- `LAN-LIVE-001` — physical second LAN device and Windows Private firewall required
- `CONV-003` — same account on a physical second LAN device is mandatory alpha.2 live gate

## Deferred pre-beta gates

- `PG-RUNTIME-001` — NOT_IMPLEMENTED, mandatory from `0.8.0-beta.1`: PostgreSQL runtime persistence/migration/rollback is the next server database vertical slice
- `UX-009` — NOT_IMPLEMENTED, mandatory from `0.8.0-beta.1`: complete cross-surface state matrix is a pre-beta quality gate

## Release invariant

No BLOCKED/NOT_IMPLEMENTED result is converted to PASS. The Windows reference machine must still run lifecycle/full acceptance after installation of this package.
