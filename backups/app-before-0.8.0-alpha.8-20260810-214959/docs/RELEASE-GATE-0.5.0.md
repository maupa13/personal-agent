# Release Gate — Personal Agent Rus v0.5.0

Milestone: Code / Execution Sandbox vertical slice.

## Required local deterministic gates

- Static/package contract.
- Windows command-binding contract.
- Core/API regression for Chat/Auth/Providers/Web/Files/Code.
- Product Shell desktop/mobile/admin browser journeys.
- Code worker failure/security acceptance.

## Code acceptance IDs

| ID | Requirement |
|---|---|
| CODE-001 | Python execution |
| CODE-002 | Java 21 compile/run |
| CODE-003 | PowerShell execution command contract |
| CODE-004 | invalid language/source/compile error handling |
| CODE-005 | non-zero process result |
| CODE-006 | cross-user code-job isolation |
| CODE-007 | hard timeout/process-tree termination |
| CODE-008 | explicit cancellation/process-tree termination |
| CODE-009 | stdout/stderr bounded |
| CODE-010 | user process does not inherit platform secrets |
| CODE-011 | Docker sandbox static contract |
| CODE-012 | browser USER journey |
| CODE-LIVE-001 | real Windows Docker Python + Java + PowerShell + runtime isolation |

## Environment-bound gates

The local release evidence must leave these explicit rather than claiming PASS:

- real reference Windows browser/CSP runtime;
- live DTF/Web canary;
- Windows lifecycle sequence;
- real Windows reboot;
- clean-machine bootstrap;
- `CODE-LIVE-001` real built code-worker execution.

## Windows authoritative command

```text
CODE-ACCEPTANCE.cmd
```

It runs the real Docker worker through Core for Python, Java 21 and PowerShell, then inspects the running container for network/read-only/resource/Docker-socket isolation.

## No false completion

`code.execute` may be marked ready after the above vertical slice. Full Coding Agent journeys UJ-300..UJ-306 remain `NOT_IMPLEMENTED` until repository-level discovery/patch/build/test/fix/retest is implemented and proven.
