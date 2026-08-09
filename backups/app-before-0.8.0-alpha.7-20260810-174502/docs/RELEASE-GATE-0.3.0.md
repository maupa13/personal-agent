# Release Gate — Personal Agent Rus 0.3.0

Scope: Web/Search/URL/Research vertical slice on top of the frozen Chat/Auth/Provider/Product-Shell baseline.

## Required deterministic gates

- STATIC / package integrity
- Windows lifecycle command contract
- Core/API baseline regression
- registration/login/session regression
- provider/model discovery and routing regression
- Product Shell desktop/mobile regression
- WEB-001 search
- WEB-002 static read
- WEB-003 browser fallback
- WEB-004 evidence-backed chat
- WEB-005 news/freshness routing
- WEB-006 multi-source research
- WEB-007 honest failure
- WEB-008 SSRF
- WEB-009 redirect-to-private protection
- WEB-010 indirect prompt-injection boundary

## Reference-host gates

`WEB-ACCEPTANCE.cmd`:

- live SearXNG search;
- live DTF read;
- evidence-backed DTF research chat;
- source list returned to UI/API;
- loopback SSRF remains blocked.

A live-site outage may be recorded as `BLOCKED_EXTERNAL`; it is never converted to PASS.

## Still environment-bound

- real-model Chromium FULL-ACCEPTANCE on reference Windows;
- RESTART / REPAIR / STOP→START sequence;
- real Windows reboot;
- clean-machine install.
