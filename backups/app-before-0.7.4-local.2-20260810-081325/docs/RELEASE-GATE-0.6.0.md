# Release Gate — Personal Agent Rus v0.6.0

## Scope

v0.6.0 adds Billing / Entitlements / Usage Metering and a payment-adapter-ready YooKassa integration on top of the previously delivered Chat/Auth/Providers/Web/Research/Files/Code foundation.

## Business contract

- Light: **0 ₽ / month**
- Medium: **500 ₽ / month**
- Pro: **1000 ₽ / month**
- Local inference: **unlimited for users; monitoring only**
- Platform-paid remote inference: **token/cost quota controlled**
- BYOK: **separate from platform-paid quota/cost**
- Admin/owner: **commercially unrestricted; still metered**
- USER token display: **off by default; opt-in setting**

## Deterministic gates

Required local gates:

- `BILL-001` plan catalog and fixed prices
- `BILL-002` entitlement/remote quota enforcement
- `BILL-003` usage metering
- `BILL-004` BYOK separation
- `BILL-005` quota exhaustion -> local fallback
- `BILL-006` user token-display preference
- `BILL-007` payment adapter checkout/idempotency
- `BILL-008` verified provider webhook
- `BILL-009` duplicate webhook idempotency
- `BILL-010` cancel-at-period-end
- `BILL-011` USER/Admin billing UI

All earlier required release gates remain regression-required.

## Environment-bound gate

`BILL-LIVE-001` requires operator-owned YooKassa test/merchant credentials plus a public HTTPS callback endpoint. It MUST remain `BLOCKED_ENVIRONMENT` until actually executed against that environment. Deterministic fake-provider PASS is not promoted to live-payment PASS.

## No false completion

v0.6.0 does not claim the complete billing chapter of MASTER-SPEC. In particular `UJ-623` remains `NOT_IMPLEMENTED` until the full upgrade/downgrade/grace/renewal matrix is finished and tested.
