# Personal Agent Rus 0.7.4-local.3 — Windows readiness/health hotfix

## Observed Windows failure

The reference Windows machine successfully started Ollama, SearXNG and Browser, but `REPAIR` aborted while waiting for Web/Search with a PowerShell `RemoteException: Traceback ...`. The still-running Core was the previous `personal-agent-core:0.7.3`.

## Root cause

Two defects amplified each other:

1. Windows PowerShell 5.1 under `$ErrorActionPreference = 'Stop'` can promote native stderr records to terminating `RemoteException`. A normal failed readiness probe from `docker compose exec ... python` therefore escaped before `$LASTEXITCODE` could be evaluated.
2. Core `/api/health` executed a real SearXNG search every Docker health interval. This generated external Google/Startpage/DDG traffic, captcha/429/timeouts, exceeded the health timeout and produced `BrokenPipeError` when the client disconnected.

Because `REPAIR` aborted before the Core rebuild step, the previous 0.7.3 Core container remained running.

## Fix

- all lifecycle Docker calls that can emit stderr are routed through `Invoke-DockerSafe`;
- expected readiness failures are evaluated only from the native process exit code;
- `/api/health` performs internal service reachability only and **never** a search query;
- Ollama, Browser and Code health calls use short bounded internal probes;
- disconnected health clients no longer generate a server traceback;
- runtime smoke verifies that `par-rus-core` uses the exact `PA_CORE_IMAGE` configured for this release;
- real external search remains covered by `WEB-ACCEPTANCE.cmd`, not by liveness/readiness.

## Expected local startup behavior

A temporary SearXNG engine captcha/timeout may degrade a real Web search, but it cannot make Docker liveness fail or crash the installer. `WEB-ACCEPTANCE.cmd` remains the strict live-search gate.
