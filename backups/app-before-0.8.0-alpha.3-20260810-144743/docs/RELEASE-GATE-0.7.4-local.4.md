# Release Gate — Personal Agent Rus 0.7.4-local.4

Purpose: close the real Windows `0.7.4-local.3` Code execution failure without weakening sandbox privileges or allowing optional Code failure to block the rest of the local product.

## Reference Windows evidence addressed

The Windows run proved that Ollama, Web/Search, Browser, Code Worker startup, Core startup, real inference and Web/SSRF smoke all passed before the first real Code job failed. The failure was therefore narrowed to the execution path after worker readiness.

## Implemented regression contract

- Code job directory is supervisor-owned, runner-group accessible (`root:runner`, `0770`).
- The container does not add `CAP_DAC_OVERRIDE`.
- Core/worker Unix-socket GID contract remains unchanged.
- real Code execution smoke is diagnostic and fail-soft for normal local startup;
- strict Code/full/release gates remain fail-closed;
- worker/job failures produce useful non-sensitive diagnostics.

## Deterministic suites

The following suites passed after the fix:

- static package checks;
- distribution/update acceptance;
- Windows launcher static contract;
- local launch regression contract;
- orchestrator/deployment acceptance;
- browser user journeys;
- API acceptance;
- billing acceptance;
- Code worker acceptance.

That is the same deterministic release set of 104 test-ID executions / 93 unique test IDs. The aggregate harness exceeded the execution envelope while entering the API suite; the API suite and remaining suites were executed separately and passed. The aggregate timeout is not promoted as a product PASS or FAIL.

## Capability-restricted execution reproduction

A dedicated local reproduction ran the worker supervisor with `CAP_DAC_OVERRIDE` removed and a different runner UID/GID:

- old `0.7.4-local.3`: FAIL with permission denied while creating/reading `main.py`;
- patched `0.7.4-local.4`: PASS, Python job `COMPLETED`, expected stdout returned.

This directly exercises the security condition that the earlier same-UID deterministic worker test could not represent.

## Environment-bound truth

Still authoritative only on the real Windows/Docker machine:

- `RUN-FIRST.cmd` / `REPAIR.cmd` full live lifecycle;
- real Docker Code Worker with Python/Java/PowerShell through Core;
- `CODE-ACCEPTANCE.cmd`;
- external SearXNG/DTF canary;
- Windows reboot / LAN / clean-machine gates.

`1.0 RELEASE PASS` is not claimed by this local hotfix.
