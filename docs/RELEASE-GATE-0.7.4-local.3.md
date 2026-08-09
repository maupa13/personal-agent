# Release Gate — Personal Agent Rus 0.7.4-local.3

Purpose: stabilize the real Windows local launch path after the `0.7.4-local.2` reference-machine failure.

## Real failure evidence addressed

Reference Windows runtime reached healthy Ollama and Browser, then `REPAIR` aborted in `Wait-WebServices` with `RemoteException: Traceback ...`. SearXNG logs showed repeated Google/Startpage captcha and DuckDuckGo timeout events, while Core logged repeated `BrokenPipeError` from `/api/health`. The still-running Core container was the previous `personal-agent-core:0.7.3` because repair aborted before the Core rebuild stage.

## Root cause

1. Windows PowerShell 5.1 + `$ErrorActionPreference='Stop'` promoted native stderr produced by expected Docker readiness failures into a terminating `RemoteException` before `$LASTEXITCODE` could be checked.
2. Core `/api/health` executed a real SearXNG search every Docker health interval. This generated external traffic, captchas/rate limits/timeouts, made health slow, and caused client disconnect/BrokenPipe noise.

## Implemented regression contract

- `Invoke-DockerSafe` is the common native Docker wrapper for lifecycle/readiness commands.
- `Wait-Ollama`, `Wait-WebServices`, Code readiness/build, Compose calls, model bootstrap, browser acceptance and backup no longer treat native stderr as a PowerShell exception.
- Core `/api/health` is internal-only: bounded Ollama tags, SearXNG service reachability, Browser health and Code socket health.
- `/api/health` contains no `/search` request and no `personal-agent-health` query.
- `BrokenPipeError` / `ConnectionResetError` while writing a response is treated as a disconnected client, not an application crash.
- runtime verification rejects a stale `par-rus-core` image tag.
- real external search remains a strict, separate `WEB-ACCEPTANCE.cmd` gate.

## Deterministic suites executed

PASS individually after the fix:

- static package checks;
- distribution/update acceptance;
- Windows launcher static contract;
- local launch regression contract;
- API acceptance;
- browser user journeys;
- orchestrator/deployment acceptance;
- billing acceptance;
- code-worker acceptance.

The aggregate runner exceeded the execution envelope of the build environment while entering the API suite; the same API suite was executed separately and passed. This is not promoted as a Windows live PASS.

## Environment-bound truth

Still authoritative only on the user's real Windows/Docker machine:

- `RUN-FIRST.cmd` / `REPAIR.cmd` live lifecycle;
- running Core image replacement to `0.7.4-local.3`;
- real Docker Code worker;
- real external SearXNG/DTF canary;
- Windows reboot / LAN / clean-machine gates.

`1.0 RELEASE PASS` is not claimed by this hotfix.
