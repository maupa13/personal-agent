# Code Execution Sandbox — v0.5.0

Status: implemented vertical slice; full repository Coding Agent remains future work.

Canonical requirements: `docs/specification/MASTER-SPEC.md`, especially Code Execution, Sandbox, Permissions, Failure Model, User Scenarios and Security Tests.

## Scope

v0.5.0 implements `code.execute` for bounded snippets in:

- Python;
- Java 21;
- PowerShell.

It does **not** yet claim the full Coding Agent workflow (repository discovery, patching, build-system discovery, JUnit/project regression, rollback). Those journeys remain `NOT_IMPLEMENTED` under UJ-300..UJ-306.

## Architecture

```text
Browser / USER
   ↓
Personal Agent Core
   ↓ HTTP API
CodeWorkerClient
   ↓ Unix domain socket (named volume)
code-worker
   ↓
per-job isolated working directory
   ↓
python3 / javac+java / pwsh
```

The worker has no Docker network and Core does not execute user shell commands itself.

## Docker boundary

Mandatory runtime contract:

- `network_mode: none`;
- no Docker socket mount;
- read-only root filesystem;
- only `/work` is writable temporary job storage;
- bounded RAM, CPU and PID count;
- capabilities dropped, with only the minimum required for privilege drop/process termination;
- `no-new-privileges` enabled;
- Core accesses worker through a Unix socket only.

## Process boundary

Each job:

1. gets a random private job directory;
2. receives only the source supplied for that job;
3. runs as a dedicated unprivileged UID/GID;
4. receives a scrubbed environment;
5. has CPU/address-space/file/process/output/time limits;
6. runs in its own process group;
7. has the whole process group terminated on timeout/cancel;
8. returns command metadata, duration, stdout, stderr and exit status.

Java uses explicit heap/metaspace/compressed-class-space limits so the JVM remains inside the sandbox memory contract instead of requiring the limit to be removed.

## Public API

- `GET /api/code/status`
- `POST /api/code/jobs`
- `GET /api/code/jobs/{id}`
- `POST /api/code/jobs/{id}/cancel`

A code job belongs to the authenticated user boundary. A second user must not be able to inspect another user's job.

## UI

`Код` opens a Code panel with:

- language selector;
- timeout selector;
- editor;
- Run;
- Cancel;
- job state;
- stdout;
- stderr.

The UI describes this as isolated code execution, not as a complete autonomous repository Coding Agent.

## Verification

Deterministic local gates verify:

- Python real execution;
- Java 21 real compile/run;
- PowerShell command contract (fake `pwsh` only when the test host does not have PowerShell);
- compile failure/non-zero status;
- timeout;
- explicit cancellation;
- bounded output;
- secret environment isolation;
- per-user job isolation;
- Docker sandbox static contract;
- browser journey.

Reference Windows/Docker gate `CODE-LIVE-001` must run real Python, Java and PowerShell inside the built `code-worker` image and inspect Docker isolation. It is never promoted to PASS from a host that cannot build/run that image.

## Next Code slice

The next Coding Agent slice must add, vertically and with new E2E:

```text
repository upload/open
→ project discovery
→ build-system detection
→ requested patch
→ build
→ tests
→ diagnose failure
→ fix
→ targeted retest
→ required regression
→ verified patch/artifacts
```
