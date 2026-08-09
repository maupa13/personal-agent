# Implementation Status, August 16, 2026

## Update, August 18, 2026
- Super-admin now sees promo code usage counts, last redemption time, and a redemption ledger with the user who activated each code.
- Admin user rows now include billing summaries: paid payment count, promo redemptions, top-up request outcomes, and balance source provenance.
- Balance provenance is derived from `balance_events`, so admin can distinguish manual adjustments, promo credits, usage charges, theme purchases, and other sources.
- The admin billing view now exposes a separate redemptions list in addition to the promo-code list and top-up requests.
- Acceptance validation still passes after the billing audit changes.

## Implemented

### Billing and balances
- User balance storage exists in `billing_balances` and `balance_events`.
- Users can request top-ups from the account page with a required payment reference.
- Top-up payment references are enforced as unique, which blocks simple duplicate-claim abuse.
- Super-admin can approve top-up requests.
- Top-up requests now keep reconciliation metadata, so admin verification has an audit trail.
- The admin UI exposes a reconcile-and-credit action for top-up requests.
- Large top-up requests require a second admin approval before crediting balance.
- Super-admin can reject top-up requests with an audit note.
- Super-admin can manually adjust any user balance from Admin.
- Promo codes can be created by super-admin and redeemed by users.
- Promo codes can optionally be emailed if SMTP is configured.
- Theme purchases are tracked separately.
- YooMoney fundraise widget is present on the account page as the first manual top-up option.

### Security and sessions
- Sessions use `HttpOnly` cookies, `SameSite=Lax`, CSRF tokens, and remember-me tracking.
- Active sessions are visible and revocable from the account page.
- Admin views expose only sanitized operational data.
- User onboarding and the main help tour persist completion/skipped state locally and via the server, so they do not reopen on every page load.

### Monitoring and observability
- Runtime observability snapshot exists.
- Admin monitoring now renders business cards, parser breakdowns, and usage summaries instead of only raw JSON.
- Business metrics are included in admin observability.
- Parser metrics were added for outbound fetches.

### Deployment and routing
- VPS deployment targets are stored and managed.
- Public deploy bundles now export the canonical public URL, SEO metadata defaults, and verification/snippet env variables.
- Super-admin can configure a VPN routing profile for VPS1 -> VPS2.
- The admin UI now generates a route plan for AllowedIPs, NAT, forwarding, and autostart.
- Server deployment bundles now export the core runtime, billing, monitoring, VPN, and tunnel defaults through `PA_*` env variables so VPS deploys can pick them up automatically.
- The admin API now exposes a VPN routing plan payload with ready-to-run client config and server commands.
- VPN application is now split into VPS1 client-side apply and VPS2 server-side apply actions over SSH.

### Themes
- Free themes exist.
- Paid themes exist, including blue and light-green variants.
- Theme IDs remain stable for saved preferences, while display names are localized for the UI.
- Account page now shows a theme catalog with one-click purchase/apply flow for paid themes.

### Legal and user-facing pages
- Separate user agreement page exists.
- Separate privacy policy page exists.
- Separate cookie policy page exists.
- Separate disclaimer page exists.
- `robots.txt`, `sitemap.xml`, canonical URLs, and verification meta/snippet injection are now supported on public pages.
- The admin shell HTML was re-encoded back to readable UTF-8 text while preserving JS hooks and panel structure.
- The admin provider form now includes the expected preset selector, and the promo generator includes the expected promo kind selector, so the HTML matches `admin.js` without missing `id` hooks.
- Auth and account screens link to the legal pages.
- Public legal HTML surfaces were rewritten in UTF-8 to remove mojibake in Russian copy.

## Partially implemented

### Payments
- YooMoney is currently a manual top-up flow, not an automatic balance-credit flow.
- YooKassa is implemented for subscription-style payments, with server-side verification.
- Manual top-up requests still need a human approval step, and larger amounts require two approvals.
- Manual top-ups now require a payment reference field, but this is still not equivalent to provider-side reconciliation.
- Reconciliation metadata is stored, but there is still no automated provider-side import pipeline for YooMoney-style proofs.

### Promos
- Promo codes work.
- Automatic promo email delivery is implemented as an optional SMTP-backed flow.

### VPN automation
- VPN profile generation exists.
- VPN config can now be applied over SSH to VPS1 and VPS2 separately from the admin UI.
- The admin UI can display a ready-made VPN plan from the server and invoke the SSH apply actions.

## Not implemented

### Fraud hardening
- Strong anti-fraud automation for manual top-ups is not complete.
- Mandatory proof-of-payment verification pipeline for all manual top-ups is not complete.
- Two-person approval for large balance changes is partially implemented for manual top-up requests.
- Automatic invoice/reference reconciliation for YooMoney-style flows is not implemented.
- Automated provider import/reconciliation for manual balance credits is not implemented.
- Payment references are now unique per top-up request, which reduces duplicate-claim attempts but does not replace provider-side reconciliation.

### External routing automation
- VPN profile generation exists.
- Automatic application now exists as separate SSH actions for VPS1 and VPS2, but it still requires the admin to choose the target machine.

## Security notes

- Manual balance credits can be abused if the admin trusts screenshots or user claims.
- The safe default is server-side verification against a payment provider, unique references, idempotency, and audit logs.
- Any balance-changing action should preserve actor, reason, reference, and timestamp.
- Data collection and cookie use should be documented in privacy/legal pages.
- Auto-open onboarding should be opt-out or one-time only; the current implementation now respects completed/skipped state.

## Release readiness

### Ready
- Authentication, accounts, legal pages, billing balances, promo codes, manual top-ups, paid themes, monitoring, and admin dashboards are implemented.
- Cookie/legal disclosure is covered in the UI and admin guidance.
- SEO delivery for public pages now includes canonical URLs, robots/sitemap output, and configurable Yandex/Google verification tags or snippets.
- Encoding issues in the rewritten public legal HTML surfaces were fixed.
- The admin surface is no longer a mojibake wall in the HTML source.

### Still missing for a full commercial release
- Automated payment reconciliation for YooMoney-style top-ups.
- Stronger fraud proofing for manual balance credits.
- A fully audited provider-side YooMoney reconciliation flow that does not rely on manual claims.
- Fully autonomous VPN target discovery and push orchestration without manual target selection.
- Production hardening for SMTP/payment credentials and monitoring alerting policies.
- A dedicated production secret manager / rotation flow for long-lived provider credentials and SMTP/payment secrets.

## Next implementation steps

1. Add provider-side reconciliation for top-ups if a usable API/receipt source is available.
2. Add stronger audit and anti-fraud checks for manual balance adjustments.
3. Automate VPN config application on the VPS side.
4. Add production alerting/thresholds for monitoring and billing anomalies.
5. Wire the env-based deployment defaults into any external release pipeline or CI job that assembles server bundles.
