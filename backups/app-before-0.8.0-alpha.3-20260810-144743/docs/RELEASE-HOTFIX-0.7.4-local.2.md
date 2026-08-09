# Personal Agent Rus 0.7.4-local.3 — Windows PowerShell 5.1 launch hotfix

## Fixed

`code-worker` is optional during normal START/REPAIR. Docker Compose writes normal build progress to stderr.
Under Windows PowerShell 5.1 with `$ErrorActionPreference='Stop'`, redirected native stderr can surface as a
terminating `RemoteException` before `$LASTEXITCODE` is inspected.

The lifecycle now:

1. captures Docker Compose output for the optional Code worker under `ErrorActionPreference=Continue`;
2. records the native process exit code explicitly;
3. restores the caller error policy in `finally`;
4. treats worker build/start failure as `Code=DEGRADED`, not a product-wide failure;
5. applies the same non-throwing handling to the optional readiness probe;
6. keeps `CODE-ACCEPTANCE`, `FULL-ACCEPTANCE`, and `RELEASE-ACCEPTANCE` strict.

## Reference failure fixed

Observed on Windows:

`[FAIL] RemoteException: Image personal-agent-code-worker:0.7.4-local.1 Building`

The launcher failed while handling native stderr before the optional branch could inspect the Docker exit code.

## Expected normal-launch behavior

If Code worker succeeds:

`[PASS] Code sandbox is ready: Python, Java and PowerShell.`

If Code worker fails:

`[WARN] Code sandbox build/start failed (...). Chat, Web, Research and Files will still start.`

In both cases Core proceeds to start. A failed Code worker is still a FAIL for strict Code/release acceptance.
