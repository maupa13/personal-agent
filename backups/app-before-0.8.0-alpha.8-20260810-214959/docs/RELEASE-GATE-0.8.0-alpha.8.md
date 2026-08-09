# Release Gate — Personal Agent Rus 0.8.0-alpha.8

## Scope

`0.8.0-alpha.8` is a focused Bootstrap Smoke Hardening release triggered by real reference-Windows evidence from `0.8.0-alpha.7`.

Observed on Windows in alpha.7:

```text
HTTP stage=bootstrap-inference ... status=200 duration_ms=43772
[FAIL] Bootstrap inference smoke test failed.
```

The transport/provider call completed, but the logical final-content assertion failed.

## Root cause contract

The bootstrap model is Qwen3, which can expose a separate thinking channel. The old smoke used a tiny 16-token output budget without explicitly disabling thinking. A thinking-capable model could therefore consume the small smoke budget without producing final `message.content`.

Alpha.8 changes only the bootstrap/release smoke policy:

- send `think=false` to Ollama for bootstrap smoke;
- use a bounded 32-token final-answer budget;
- request exact `PAR_OK`;
- preserve normal user/provider thinking behavior outside the smoke path;
- report model, reason, content length and native timings even when HTTP is 200 but logical output is empty;
- deterministic fake Ollama reproduces the thinking-only failure if `think=false` is omitted.

## Deterministic authoritative evidence

Evidence directory: `release-evidence/0.8.0-alpha.8-authoritative/`

19 isolated authoritative suites completed with exit code 0:

- Windows command contract;
- local launch contract;
- accounts / entitlements;
- Scenario Engine;
- Search Integrity / Debug Observability;
- alpha.7 runtime timing contract;
- **alpha.8 bootstrap smoke contract**;
- live-results deterministic contract;
- UX/Admin hardening;
- UX Complete;
- UX Complete Chromium;
- live-results Chromium;
- orchestrator / deployment / LAN contracts;
- USER Chromium journey;
- ADMIN Chromium journey;
- full Core API acceptance;
- productization / persistence / onboarding / observability;
- billing;
- Code Worker.

Summary: **19 PASS / 0 FAIL**.

The full Core API integration specifically verifies that `/api/admin/inference/smoke` sends `think=false` to the fake Ollama transport and receives non-empty final content.

## Environment-bound gate

`PERF-A8-WIN-001` remains **BLOCKED_ENVIRONMENT** until the reference Windows PC runs the packaged alpha.8 build.

Required real evidence:

```text
HTTP stage=bootstrap-inference ... status=200
INFERENCE bootstrap model=qwen3:0.6b ok=True reason=ok content_length=...
... load_ms=... prompt_eval_ms=... generation_ms=... tokens_per_sec=...
[PASS] Runtime verification passed ...
```

The release is therefore a verified deterministic hotfix candidate, **not** a claim that the real Windows performance gate is already PASS.

## Unchanged later gates

PostgreSQL canonical runtime, real VPS/HTTPS, real YooKassa merchant flow, physical second LAN device, Windows reboot and clean-machine gates remain separate later acceptance layers.

## Full deterministic release gate

After the isolated suites, the monolithic release aggregator also completed cleanly on the frozen source state:

```text
PAR_RELEASE_GATE PASS
233 PASS
0 FAIL
```

The aggregate evidence is stored in `release-evidence/0.8.0-alpha.8-local/release-gate.json`.

This still does **not** promote `PERF-A8-WIN-001` to PASS; the thinking-safe smoke must be rerun on the reference Windows PC with the packaged alpha.8 bytes.
