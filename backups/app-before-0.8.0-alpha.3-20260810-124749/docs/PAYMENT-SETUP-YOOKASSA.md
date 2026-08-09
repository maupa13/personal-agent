# YooKassa setup for Personal Agent Rus

The application code is payment-adapter-ready, but merchant credentials are intentionally not shipped in the release.

## 1. Prepare the deployment

Use a public HTTPS URL for the server edition, e.g. `https://agent.example.ru`.

## 2. Admin -> Тарифы и Usage

Enter:

- Shop ID
- Secret Key
- Public HTTPS URL
- Provider: YooKassa

Save. The secret is not returned to the browser after storage.

## 3. Configure notification URL in YooKassa

Use:

`https://<your-domain>/api/billing/webhook/yookassa`

Subscribe to the payment status events required for the payment flow, at minimum successful/cancelled payment events used by the application.

## 4. Configure remote AI budgets

For each plan set monthly limits for `PLATFORM_REMOTE`:

- token limit;
- estimated RUB cost limit.

Leaving both at `0` intentionally prevents platform-paid remote inference.

Local inference remains unlimited regardless of these limits.

## 5. Provider accounting

In Admin -> Providers classify each connection:

- LOCAL
- BYOK
- PLATFORM_REMOTE
- PRIVATE_REMOTE

For remote providers set estimated input/output price in RUB per 1M tokens if cost tracking is desired.

## 6. Live acceptance before public launch

A real deployment is not payment-PASS until `BILL-LIVE-001` verifies:

- checkout creation;
- redirect/confirmation;
- real callback delivery;
- server-side re-fetch/verification;
- entitlement activation;
- duplicate callback idempotency;
- saved payment method/recurring flow where enabled;
- cancellation;
- merchant-specific receipt/fiscal requirements.
