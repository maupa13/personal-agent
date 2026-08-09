# Release Gate Report — 0.2.2

## Defect addressed

Reference Windows `FULL-ACCEPTANCE` 0.2.1 failed because the XSS journey expected a real LLM to reproduce an exact HTML payload. This is a test-design defect, not evidence that CSP or DOM escaping failed.

## Local evidence available in the build environment

Required deterministic gates executed from the release bytes:

- static/package contracts;
- API/public/admin boundary;
- validation/routing;
- concurrency;
- model-pull jobs;
- SQLite persistence;
- backend-failure behavior;
- offline Chromium UI journeys with deterministic hostile content.

The build environment administratively blocks Chromium navigation to local HTTP endpoints (`ERR_BLOCKED_BY_ADMINISTRATOR`). Therefore real HTTP Chromium gates are recorded as `BLOCKED_ENVIRONMENT` here, never promoted to PASS.

## Authoritative reference-host gate

On the Windows reference host, `FULL-ACCEPTANCE.cmd` now runs BOTH:

- `FND-BROWSER-LIVE-REAL-001`: browser journey against the actual Personal Agent runtime and real local inference;
- `FND-BROWSER-LIVE-SECURITY-001`: isolated production Core + deterministic fake provider + real browser + production CSP.

Foundation remains unfrozen until those tests and the remaining Windows lifecycle/reboot gates pass.
