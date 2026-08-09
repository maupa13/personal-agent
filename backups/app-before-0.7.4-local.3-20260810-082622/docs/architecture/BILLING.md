# Billing / Entitlements / Usage — v0.6.0

## Product model

Personal Agent Rus charges for the maintained service/support layer, not for the user's own local compute.

| Plan | Monthly price | Local inference | Platform-paid remote API |
|---|---:|---|---|
| Light / Лайт | 0 ₽ | Unlimited; monitored | Disabled by default until admin grants quota |
| Medium / Медиум | 500 ₽ | Unlimited; monitored | Admin-configurable monthly token + cost budget |
| Pro / Про | 1000 ₽ | Unlimited; monitored | Admin-configurable monthly token + cost budget |
| Admin/owner | 0 ₽ | Unlimited | Commercially unrestricted; usage/cost still monitored |

The fixed subscription price funds product maintenance/support. It must never be interpreted as a charge for consuming the user's own GPU.

## Billing classes

Every provider has one billing class:

- `LOCAL` — local machine/private local compute; no plan quota.
- `BYOK` — user's own external API key; metered separately but does not consume platform-paid quota.
- `PLATFORM_REMOTE` — remote API paid by the Personal Agent service; subject to plan token/cost quotas.
- `PRIVATE_REMOTE` — private remote infrastructure; monitored separately and not charged as platform API by default.

Routing stores `provider_id + model_id`; usage ledger also records both. Changing a provider's billing class is an ADMIN operation.

## Safe default

Remote token and cost quotas for Light/Medium/Pro start at zero. Connecting an expensive remote provider therefore cannot silently create platform costs. ADMIN explicitly sets plan limits in `Admin -> Тарифы и Usage`.

If a `PLATFORM_REMOTE` route cannot run because quota is exhausted and a local model is available, router policy falls back to local inference and exposes a product-level notice. It must not return an unexplained HTTP 500 and must not silently bill beyond quota.

## Usage metering

Recorded per inference:

- user;
- provider;
- model;
- billing class;
- source (chat/research/file/etc.);
- input tokens;
- output tokens;
- total tokens;
- exact/estimated marker;
- estimated RUB cost for configured remote provider rates.

Provider-native usage counters are authoritative when available; otherwise an estimate may be recorded with `exact=false`.

Normal USER token telemetry is hidden in responses by default. The user can enable `Показывать токены в ответах` in the profile. ADMIN always has aggregate monitoring.

## Payment Adapter

v0.6.0 contains a YooKassa adapter boundary. Core billing is not coupled to the payment provider's UI.

ADMIN configures:

- provider = YooKassa;
- Shop ID;
- Secret Key (stored separately from browser/API responses);
- public HTTPS base URL.

Product webhook endpoint:

`/api/billing/webhook/yookassa`

Checkout creates a one-month payment for Medium or Pro, uses an idempotency key, redirects the user to the provider confirmation URL and requests a saved payment method for future recurring charges.

Incoming notification payload is never trusted as payment proof. The product fetches the payment object back from YooKassa and verifies internal metadata, user, plan, amount, currency and current provider status before activating entitlements. Duplicate notifications are idempotent.

Cancellation is `CANCEL_AT_PERIOD_END`: paid access is not destroyed immediately.

## External setup still required

The release cannot contain a merchant's Shop ID or Secret Key. To enable real payments the operator must:

1. create/configure a YooKassa merchant/test shop;
2. configure Shop ID + Secret Key in Admin;
3. deploy Personal Agent on a publicly reachable HTTPS URL;
4. configure YooKassa HTTP notifications to the product webhook endpoint and required payment events;
5. confirm the merchant account supports the intended saved-payment/recurring-payment flow;
6. satisfy receipt/cash-register/fiscal requirements applicable to that merchant configuration;
7. run `BILL-LIVE-001` with real test credentials before production billing is declared PASS.

Without those external credentials and callback infrastructure, deterministic payment integration is `PASS` but real merchant billing remains `BLOCKED_ENVIRONMENT`.

## Not yet complete

The following broader canonical billing scope remains future work and must not be falsely marked complete:

- full grace-period lifecycle and full upgrade/downgrade matrix (`UJ-623`);
- independent receipt/invoice adapter;
- refunds/partial refunds UI and workflows;
- production payment reconciliation jobs;
- tax/fiscal policy abstraction;
- multiple payment-provider adapters;
- full billing ledger/reporting/accounting exports;
- enterprise/team billing.
