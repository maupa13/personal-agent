# Acceptance Matrix

Machine-readable registry: `tests/acceptance-registry.json`.

## Web v0.3 mandatory
- WEB-001 SearchProvider normalized results.
- WEB-002 Static URL read extracts real content.
- WEB-003 JS/dynamic page uses BrowserWorker fallback.
- WEB-004 Chat URL request uses web evidence before inference.
- WEB-005 Current/news request invokes search rather than model memory.
- WEB-006 Research uses multiple sources and returns source evidence.
- WEB-007 Unavailable source returns honest partial/failure, never fake success.
- WEB-008 SSRF/private target blocked.
- WEB-009 Redirect/private destination blocked.
- WEB-010 Prompt-injection page remains untrusted data.
- WEB-011 DTF live canary has PASS / PRODUCT_FAIL / BLOCKED_EXTERNAL evidence.
- WEB-012 Browser/search failures are diagnosable.

## Code / Execution Sandbox v0.5 mandatory
- CODE-001 Python snippet executes in isolated worker.
- CODE-002 Java 21 snippet compiles and runs in isolated worker.
- CODE-003 PowerShell command contract is exercised; real runtime is separately required by CODE-LIVE-001.
- CODE-004 Invalid source/language and compile failures are controlled failures.
- CODE-005 Non-zero process exit is never reported as success.
- CODE-006 Code jobs are isolated by authenticated user.
- CODE-007 Hard timeout kills the process group.
- CODE-008 Explicit cancel kills the process group.
- CODE-009 stdout/stderr are bounded.
- CODE-010 Runtime secrets are not inherited by user code.
- CODE-011 Docker contract: no network, no Docker socket, read-only root, bounded memory/CPU/PIDs.
- CODE-012 Browser Code journey works through the public Core API.
- CODE-LIVE-001 Reference Windows Docker image executes real Python, Java 21 and PowerShell and passes runtime isolation inspection.
