# Release Gate — Personal Agent Rus 0.8.0-alpha.3

## Verdict

**Deterministic alpha.3 scope: PASS.** 12 authoritative suites completed independently with exit code 0: **161 PASS records / 147 unique test IDs / 0 deterministic FAIL**.

The monolithic release runner was interrupted by the outer execution harness while entering the Browser stage. It is **not** counted as PASS and is **not** treated as a product failure, because the same Browser journey and every remaining subsystem suite completed independently with exit code 0 and preserved logs.

## New alpha.3 product slice

- Scenario Gallery: clothing, procurement, real estate, gift, product, travel, news.
- Auto uses the same Scenario Engine; explicit URL routing has higher priority than automatic scenario detection.
- Bounded clarification: usually one grouped question; procurement/real-estate at most two rounds.
- Clarification state persists server-side per user/conversation.
- Internal clarification scaffolding is excluded from routing signals and external search query text.
- USER Web preferences persist server-side: whole internet / prefer Russian / selected sites, region, allow/exclude lists.
- Admin site profiles affect scoped search and browser/static acquisition order.
- `egress_region` is policy metadata only; multi-region worker routing remains `VPS-EGRESS-001 NOT_IMPLEMENTED`.

## Authoritative suites

| Suite | Result |
|---|---|
| `static` | PASS |
| `distribution` | PASS |
| `windows-contract-static` | PASS |
| `local-launch-contract` | PASS |
| `accounts-entitlements-acceptance` | PASS |
| `scenario-site-preferences-acceptance` | PASS |
| `orchestrator-deployment-acceptance` | PASS |
| `browser-user-journeys` | PASS |
| `api-acceptance` | PASS |
| `productization-acceptance` | PASS |
| `billing-acceptance` | PASS |
| `code-worker-acceptance` | PASS |

## Deferred / external evidence

- **12 BLOCKED_ENVIRONMENT** checks remain reference-machine/live-only: Windows lifecycle/reboot, physical LAN device, live Web/DTF, real YooKassa, real VPS and related live paths.
- `PG-RUNTIME-001` — NOT_IMPLEMENTED, mandatory from `0.8.0-beta.1`. PostgreSQL foundation is present but is not canonical Core persistence yet.
- `UX-009` — NOT_IMPLEMENTED, mandatory from `0.8.0-beta.1`.
- `VPS-EGRESS-001` — NOT_IMPLEMENTED, mandatory from `0.9.0`. RU/global multi-region egress routing is not claimed.

## Evidence

Machine-readable summary: `release-evidence/0.8.0-alpha.3-local/authoritative-release-summary.json`.
Authoritative logs: `release-evidence/0.8.0-alpha.3-local/authoritative/`.

## Release truth

This package may be called **0.8.0-alpha.3 Scenario Engine**. It must **not** be called PostgreSQL-runtime-ready, multi-region-VPS-ready, or 0.9.0. Those claims require their own live vertical slices and evidence.
