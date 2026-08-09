# Release Gate Report — 0.2.1

This release closes the strict-CSP browser acceptance defect found on the Windows reference host.

## Source/build environment evidence

Two clean release-gate runs passed from the same source bytes:

- FND-STATIC-001 — PASS
- FND-WIN-CONTRACT-001 (static launcher contract) — PASS
- FND-API-001 — PASS
- FND-BROWSER-OFFLINE-001 — PASS

Covered behavior includes public/admin boundary, invalid payloads, routing, 12 concurrent chats, async model pull, SQLite persistence after Core restart, controlled inference-backend failure, security headers, desktop/mobile UI, mode selection, chat/storage, admin routing/model pull and XSS resistance.

## Strict-CSP live browser gate

The live suite no longer contains `wait_for_function()` or JavaScript-eval polling. It verifies the real response CSP requires `script-src 'self'` and does not allow `unsafe-eval`.

The build container cannot complete FND-BROWSER-LIVE-001 because its Chromium is administratively blocked from navigating to local HTTP endpoints (`ERR_BLOCKED_BY_ADMINISTRATOR`). Per the master execution contract this is recorded as `BLOCKED_ENVIRONMENT`, not PASS.

The mandatory authoritative execution of FND-BROWSER-LIVE-001 is therefore the Windows reference-host `FULL-ACCEPTANCE.cmd` run.

## Failure evidence

Live browser failures now persist:

- screenshot
- page HTML
- browser console log
- page-error log
- failed-network log
- test context JSON

under `logs/acceptance-artifacts` on the reference host.

## Foundation freeze

0.2.1 is **not foundation-frozen** until the Windows reference machine passes the required lifecycle sequence from the acceptance registry, including live browser, repair/stop-start, and real Windows reboot gate.
