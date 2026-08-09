# Release Gate — Personal Agent Rus 0.7.4-local.5

## Result

**Deterministic quality gate: PASS.**

- 107 release-gate records / 96 unique test IDs
- 0 deterministic FAIL
- all authoritative suites were executed separately to completion and their logs are packaged under `docs/release-evidence/0.7.4-local.5/`

The combined runner was interrupted by the execution-host duration limit while entering the API suite; this is not promoted to either PASS or product FAIL. The same API suite was then executed directly and returned exit code 0, as did Browser/UI, Code Worker, Billing and the remaining suites.

## New mandatory quality evidence

- `WEB-013` — site/root news queries are scoped to the requested domain and do not use raw homepage navigation as primary evidence.
- `WEB-014` — answers that dump `SOURCE 1`/tool output or merely list sources are rejected and retried; a bounded evidence-backed fallback exists.
- `FND-CHAT-EXPORT-001` — the current conversation has a visible export action and produces a verified Markdown workspace artifact before download.
- Code Docker Desktop ownership regression — HOME/TMP/source access no longer requires transferring UID ownership to the sandbox runner; `CAP_DAC_OVERRIDE` remains absent.

## Existing regression suites

PASS: package/static, staged distribution/update, Windows launcher contract, local launch/fail-soft, Core API, Browser/UI/mobile/XSS, Files/Artifacts, Code worker execution, Tasks/Orchestrator/VPS/LAN contracts, Billing/payment adapter.

## Not claimed

This is not `1.0 RELEASE PASS`. Real Windows Docker execution of the newly patched Code path, live RBC/DTF quality canaries, reboot, physical LAN second-device, YooKassa and real VPS gates remain environment-bound.
