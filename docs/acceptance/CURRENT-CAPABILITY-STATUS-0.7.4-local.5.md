# Current capability status — 0.7.4-local.5

This build is a **quality local candidate**, not `1.0 RELEASE PASS`.

## Reference Windows facts already proven

- Docker/Compose readiness: PASS.
- Ollama startup and real local inference: PASS.
- SearXNG + Browser startup: PASS.
- Core startup/current-image replacement: PASS.
- Web/SSRF smoke: PASS.
- Code Worker image/start/runtime inventory: PASS.
- `0.7.4-local.4` real Code execution failed only on `/work/<job>/home` ownership (`EPERM`); local.5 changes this exact ownership path.

## Deterministic quality gates in local.5

- package/static/distribution/Windows lifecycle contract: PASS;
- local-launch/fail-soft contract: PASS;
- API acceptance: PASS;
- Browser/UI acceptance: PASS;
- Code worker execution acceptance: PASS;
- Tasks/Orchestrator/VPS/LAN contract: PASS;
- Billing/payment-adapter contract: PASS;
- `WEB-013`: root-domain news request uses site-scoped article evidence instead of raw homepage navigation: PASS;
- `WEB-014`: source/tool-dump answer is rejected and retried/fallback-synthesized: PASS;
- `FND-CHAT-EXPORT-001`: current chat exports to a verified Markdown workspace artifact: PASS.

## Remaining reference-machine proof

The patched Code execution path must be rerun on the real Windows Docker Desktop host. Live public-Web quality (RBC/DTF), reboot, LAN second-device, payment and VPS gates remain environment-bound.

## Release truth

`1.0 RELEASE PASS` remains forbidden until the full MASTER-SPEC/user-journey matrix and all mandatory environment-bound gates have real evidence.
