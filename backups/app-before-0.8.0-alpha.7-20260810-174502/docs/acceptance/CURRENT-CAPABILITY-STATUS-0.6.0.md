# Current Capability & User Journey Coverage — v0.6.0

This file is generated from the machine-readable `tests/user-journeys-registry.json` and is a truthful snapshot, not a product-completeness claim.

## Totals

- **PASS: 42**
- **FAIL: 0**
- **BLOCKED_ENVIRONMENT: 3**
- **BLOCKED_EXTERNAL: 0**
- **NOT_IMPLEMENTED: 90**
- **SKIPPED_NOT_APPLICABLE: 0**

## Important delivered vertical slices

- Product Shell / Chat / presets / basic auth and provider registry
- Web / URL / deterministic Research evidence
- Files / Workspace / verified artifacts
- Code Execution Sandbox foundation
- **Billing / Entitlements / Usage Metering / YooKassa payment adapter (deterministic)**

Billing policy in v0.6.0:

- Light = 0 ₽/month
- Medium = 500 ₽/month
- Pro = 1000 ₽/month
- local inference = unlimited, monitoring only
- platform-paid remote API = token/cost quotas
- BYOK = separate usage/cost class
- Admin = commercially unrestricted, usage still visible
- USER token telemetry = opt-in

## Billing journeys

- `UJ-620` — **PASS** — Plan entitlement enforcement — tests: BILL-001, BILL-002
- `UJ-621` — **PASS** — Usage metering per model/provider — tests: BILL-003, BILL-006
- `UJ-622` — **PASS** — Payment success + idempotent webhook — tests: BILL-007, BILL-008, BILL-009
- `UJ-623` — **NOT_IMPLEMENTED** — Upgrade/downgrade/grace/cancel
- `UJ-624` — **PASS** — BYOK usage separated from platform cost — tests: BILL-004
- `UJ-625` — **PASS** — Quota exhaustion local/private fallback — tests: BILL-005
- `UJ-626` — **PASS** — User opts in to token usage display; default remains hidden — tests: BILL-006
- `UJ-627` — **BLOCKED_ENVIRONMENT** — Real YooKassa merchant checkout/webhook/recurring payment on public HTTPS — tests: BILL-LIVE-001

## Still not complete

The canonical MASTER-SPEC is substantially larger than this release. Key areas still containing `NOT_IMPLEMENTED` journeys include:

- full account security (email verification, password reset, sessions, 2FA, complete personal cabinet);
- Context Engine / long-term Memory / RAG;
- repository-level Coding Agent and Data/ETL/Database agent;
- Image, Audio and Video capabilities;
- Connectors, OAuth, MCP, plugins and user skills;
- Automation/scheduler/notifications;
- **full billing lifecycle UJ-623** (complete upgrade/downgrade/grace/renewal matrix), receipts/refunds/reconciliation;
- Public API/API keys/rate limiting;
- full admin operations, audit, observability/alerts;
- backup/restore/update/rollback/reboot/clean-machine gates;
- remaining security, mobile/PWA, multi-capability and enterprise journeys.

`PASS` means the corresponding deterministic/user journey has evidence. It does not mean all product requirements are complete.
