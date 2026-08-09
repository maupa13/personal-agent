# Release Gate — Personal Agent Rus 0.8.0-alpha.4

## Result

**Deterministic authoritative suites: 13/13 PASS, 0 FAIL.**

Authoritative model: each subsystem suite ran as a separate process and completed with exit code 0. Logs are stored under `release-evidence/0.8.0-alpha.4-local/authoritative/` and summarized in `authoritative-release-summary.json`.

| Suite | Status |
|---|---|
| `static` | **PASS** |
| `distribution` | **PASS** |
| `windows` | **PASS** |
| `local-launch` | **PASS** |
| `accounts` | **PASS** |
| `scenario` | **PASS** |
| `alpha4` | **PASS** |
| `productization` | **PASS** |
| `orchestrator` | **PASS** |
| `billing` | **PASS** |
| `code-worker` | **PASS** |
| `api` | **PASS** |
| `browser` | **PASS** |

## Alpha.4 mandatory slice

PASS: `UX-A4-001`, `UX-A4-002`, `FEEDBACK-A4-001`, `SHARE-A4-001`, `EXEC-A4-001`, `TONE-A4-001`, `ADMIN-A4-001`, `ADMIN-A4-002`, `UI-A4-001`, `GUIDE-A4-001`, `PRIV-A4-001`.

This verifies server-side theme/language/execution/tone preferences, expiring read-only chat shares, persisted feedback, loopback-only local OWNER Admin access, provider/model/routing control including OpenAI Responses provider type, responsive/collapsed UI contracts and in-product setup/Admin guides.

## Monolithic runner

The optional monolithic `tests/release_gate.py` was interrupted by the external execution harness while starting its Browser stage. It is **not** counted as PASS and **not** treated as a product FAIL. The same Browser suite and every other authoritative subsystem suite completed independently with exit code 0 on the same code bytes.

## Not promoted to PASS

Environment-bound: real Windows lifecycle/reference sequence, reboot, physical second LAN device, live DTF/Web canary, real Docker Windows Code gate, real YooKassa merchant callback/webhook and real VPS/DNS/HTTPS.

Future mandatory gates: `PG-RUNTIME-001` (PostgreSQL canonical persistence), `UX-009` (complete cross-surface state matrix) and `VPS-EGRESS-001` (real RU/global egress routing).

## Release claim

This artifact may be called **0.8.0-alpha.4 UX/Admin Hardening**. It must not be called PostgreSQL-runtime-ready, production-payment-ready, multi-region-VPS-ready, 0.9.0 or 1.0.0.
