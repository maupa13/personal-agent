# System Capabilities Analysis, August 16, 2026

This document describes what the current system can do, what it cannot do yet, and where the main commercial and security risks remain.

## What the system can do

### Identity, auth, sessions, cookies
- Supports authenticated users and admin roles.
- Stores sessions in HttpOnly cookies with CSRF protection.
- Tracks remembered state for onboarding/help panels and does not reopen them on every page load if the user already dismissed them.
- Exposes cookies, sessions, cart-like state, localization, theme preference, experiment grouping, and anonymous visitor tracking in the product model.
- Separates public account experience from admin experience.

### Billing, balances, promos, themes
- Maintains per-user balances and detailed balance events.
- Allows super-admins to adjust balances manually.
- Allows super-admins to top up their own balance through the same privileged admin flow.
- Allows super-admins to create promo codes.
- Supports starter promo codes so new users can begin using the service for free.
- Allows users to redeem promo codes.
- Supports sending promo codes to email if SMTP is configured.
- Requires a payment reference for manual top-up requests and blocks duplicate references.
- Supports YooMoney as a manual top-up entry point through the account page widget.
- Supports YooKassa subscription payments with server-side verification.
- Tracks theme purchases separately from balance operations.
- Supports paid themes, including blue and light-green variants.

### Payments and anti-duplication
- Top-up requests are unique by `payment_reference`.
- Top-up approvals are audit-trailed and now carry reconciliation metadata.
- YooKassa webhooks are re-fetched and verified server-side before crediting subscriptions.
- Payment events are deduplicated with an idempotency key / event key model.

### Monitoring and observability
- Collects runtime observability snapshots.
- Includes technical signals and business metrics in admin monitoring.
- Shows parser counters for upstream fetches, retries, backoff, active requests, and effective RPS.
- Shows business metrics such as balances, subscriptions, payments, top-up requests, and recent alerts.

### Providers and inference routing
- Supports multiple provider records in admin.
- Supports local and remote provider discovery.
- Supports provider billing classes such as local, BYOK, platform remote, and private remote.
- Lets the admin route model usage to selected providers and models.
- Supports a safe default where platform remote cost limits are zero unless an admin configures otherwise.

### Deployment and VPS operations
- Stores deployment targets and SSH credentials only for the operation window.
- Supports bootstrapping, preflight, deploy, rollback, and VPN apply actions.
- Exports deployment and runtime defaults through env-backed server bundles.
- Supports a VPN routing plan for VPS1 -> VPS2 -> selected upstream API IPs.
- Supports separate VPS1 client-side and VPS2 server-side VPN apply actions.

### Legal and user-facing compliance
- Has separate pages for user agreement, privacy, cookies, and disclaimer.
- Can present disclaimers about non-professional advice.
- Can document cookie usage categories and user-consent behavior.

## What the system cannot do yet

### Payments
- It cannot fully auto-reconcile YooMoney-style manual top-ups from an open provider API, because there is no integrated provider-side balance/receipt import pipeline.
- It cannot prove cash transfer completion on its own if the user supplies fake screenshots or false claims.
- It cannot eliminate fraud if an administrator blindly approves a request without checking external evidence.
- It cannot safely treat manual top-ups as “automatically paid” unless a trusted external confirmation source exists.

### Reconciliation and fraud hardening
- It does not currently have a full bank/provider reconciliation import job for manual top-ups.
- It does not yet have a separate external evidence store with signed receipts, bank statement import, or PSP-side order lookup for every manual payment path.
- It does not automatically block all balance abuse paths if a privileged admin intentionally misuses access.

### Provider onboarding
- On VPS deployments, adding and tuning new models/providers still requires admin work.
- It does not yet provide fully automatic “connect ChatGPT/Gemini/etc. and tune it” behavior on a fresh VPS without configuration.
- Provider availability still depends on what the operator actually configures and what the external service exposes.

### VPN automation
- VPN plan generation exists, but the system still requires the admin to choose and apply the target path.
- It does not yet autodiscover every networking detail without operator input.
- The VPN routing form also expects a `preferenceId` so the operator can bind a route plan to a named configuration.

### Monitoring and alerting
- It has dashboards and metrics, but it does not yet have a full production alerting stack with tuned alert routing, paging, and SLO policy automation.

## Can top-up fraud happen?

Yes, in the manual-payment path.

Main risk cases:
- A user submits a fake proof of payment.
- An admin credits balance without checking provider-side evidence.
- A compromised admin account creates or edits balance events directly.
- A duplicated or replayed reference is attempted.

What is already in place:
- Unique `payment_reference` for top-up requests.
- Audit fields on balance changes and top-up decisions.
- Second-approval flow for larger manual top-ups.
- Admin visibility into pending, review-required, and approved requests.

What still matters operationally:
- Use the smallest possible manual crediting surface.
- Prefer promo codes or provider-confirmed flows over arbitrary balance edits.
- Keep every balance mutation auditable.
- Treat screenshots as weak evidence.

## Can super-admin edit balances?

Yes.

Current behavior:
- Super-admin can manually increase or decrease a user balance from admin.
- That action is intentional and is part of the current trust model.
- It must be treated as a privileged audit event.

Recommended policy:
- Reserve direct balance edits for support, migration, abuse recovery, or controlled promotions.
- Prefer promo codes for user-facing bonus balance distribution.
- Use balance edits only when an explicit reason and audit trail are required.

## How users should get balance

Current viable paths:
- Promo code redemption.
- Manual top-up request with payment reference and admin verification.
- Gift/promotional codes generated by super-admin and optionally emailed.

Recommended release pattern:
- Users get a small starter promo so the product is usable for free.
- Larger balances come from promo codes or controlled top-ups.
- Public sales use a trusted PSP flow, not screenshot-only manual credit.

## VPS and provider setup constraints

The current VPS1 deployment model is practical, not fully self-configuring.

What works:
- Server bundles can pull settings from env.
- VPN plan generation exists.
- VPS1 and VPS2 can be prepared separately.
- OpenAPI traffic can be routed through a specific VPN hop.

What remains manual:
- Picking the external provider and setting its credentials.
- Choosing the target VPS and applying the SSH-based action.
- Bringing up the wireguard/amnezia tunnel with the right network details.

## Release readiness

### Ready enough
- Auth and accounts.
- Admin dashboard and monitoring.
- Basic billing, balances, promo codes, paid themes.
- Legal pages and cookie/privacy coverage.
- VPS deployment basics and VPN plan generation.

### Not yet fully release-safe
- Fully automated payment reconciliation for manual top-up channels.
- Strong anti-fraud automation for manual balance credits.
- Fully autonomous model/provider onboarding on VPS without admin intervention.
- Full production alerting and incident policy automation.

## Key files

- Billing and balances: [billing_service.py](/C:/Sync/Projects/personal-agent/services/core/app/billing_service.py)
- Admin API and routes: [main.py](/C:/Sync/Projects/personal-agent/services/core/app/main.py)
- Admin UI billing panel: [admin.js](/C:/Sync/Projects/personal-agent/services/core/app/static/admin.js)
- Admin shell and buttons: [admin.html](/C:/Sync/Projects/personal-agent/services/core/app/static/admin.html)
- Status summary: [IMPLEMENTATION-STATUS-2026-08-16.md](/C:/AI/RusPersonalAgent/docs/IMPLEMENTATION-STATUS-2026-08-16.md)
