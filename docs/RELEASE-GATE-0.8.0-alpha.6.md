# Родной Агент / Personal Agent 0.8.0-alpha.6 — Release Gate

## Result

- Authoritative suites: **17 PASS / 0 FAIL**
- Release-gate records represented: **210**
- Unique test IDs represented: **189**
- Signed/package verification is performed after this report is generated.

## Alpha.6 scope

- strict explicit-domain source integrity (`dtf.ru` cannot silently become RBC);
- Admin Search Policy with actual SearXNG provider and source limits/preferences/blocklist;
- adaptive result cards for news/products/real estate/procurement;
- per-answer timings and safe trace metadata;
- actionable Windows HTTP diagnostics with stage/status/body/request/correlation/duration;
- YooKassa turnkey readiness checklist;
- artifact export rendering regression fixed and observable;
- USER and ADMIN Chromium journeys split into deterministic isolated suites.

## Authoritative suite processes

- `accounts` — **PASS**, exit `0` — `release-evidence/0.8.0-alpha.6-authoritative/logs/accounts.log`
- `alpha6` — **PASS**, exit `0` — `release-evidence/0.8.0-alpha.6-authoritative/logs/alpha6.log`
- `api` — **PASS**, exit `0` — `release-evidence/0.8.0-alpha.6-authoritative/logs/api.log`
- `billing` — **PASS**, exit `0` — `release-evidence/0.8.0-alpha.6-authoritative/logs/billing.log`
- `browser-admin` — **PASS**, exit `0` — `release-evidence/0.8.0-alpha.6-authoritative/logs/browser-admin.log`
- `browser-user` — **PASS**, exit `0` — `release-evidence/0.8.0-alpha.6-authoritative/logs/browser-user.log`
- `code-worker` — **PASS**, exit `0` — `release-evidence/0.8.0-alpha.6-authoritative/logs/code-worker.log`
- `distribution` — **PASS**, exit `0` — `release-evidence/0.8.0-alpha.6-authoritative/logs/distribution.log`
- `local-launch` — **PASS**, exit `0` — `release-evidence/0.8.0-alpha.6-authoritative/logs/local-launch.log`
- `orchestrator` — **PASS**, exit `0` — `release-evidence/0.8.0-alpha.6-authoritative/logs/orchestrator.log`
- `productization` — **PASS**, exit `0` — `release-evidence/0.8.0-alpha.6-authoritative/logs/productization.log`
- `scenario` — **PASS**, exit `0` — `release-evidence/0.8.0-alpha.6-authoritative/logs/scenario.log`
- `static` — **PASS**, exit `0` — `release-evidence/0.8.0-alpha.6-authoritative/logs/static.log`
- `ux-admin` — **PASS**, exit `0` — `release-evidence/0.8.0-alpha.6-authoritative/logs/ux-admin.log`
- `ux-browser` — **PASS**, exit `0` — `release-evidence/0.8.0-alpha.6-authoritative/logs/ux-browser.log`
- `ux-complete` — **PASS**, exit `0` — `release-evidence/0.8.0-alpha.6-authoritative/logs/ux-complete.log`
- `windows` — **PASS**, exit `0` — `release-evidence/0.8.0-alpha.6-authoritative/logs/windows.log`

## Honest external/deferred gates

`WEB-011` (live DTF), `BILL-LIVE-001` (real YooKassa), reference Windows lifecycle/reboot, physical LAN device and real VPS remain environment-bound. PostgreSQL canonical server persistence and real RU/global egress routing are separate pre-0.9 gates. Yandex/Google search adapters are not advertised as working until implemented and live-tested.

The aggregate `release_gate.py` run was interrupted by the outer execution harness after already-green stages. It is **not** promoted to PASS. The release decision here is based on the 17 independently completed authoritative suite processes on the same frozen source bytes.
