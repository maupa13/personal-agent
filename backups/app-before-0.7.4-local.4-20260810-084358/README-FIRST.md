# Personal Agent Rus 0.7.4-local.3 — quality local launch candidate

## Windows: one first-run action

1. Extract this ZIP either into a temporary/package folder **or directly into `C:\AI\RusPersonalAgent`**. Existing old release/evidence/.idea folders are ignored because only the signed manifest payload is verified and staged.
2. Run **`RUN-FIRST.cmd`** by double-click, or from PowerShell use **`.\RUN-FIRST.cmd`**.
3. The installer verifies the signed payload, installs/updates the application at:

```text
C:\AI\RusPersonalAgent\app
```

and keeps stable user entrypoints directly under:

```text
C:\AI\RusPersonalAgent\
```

You no longer work from version-named release folders.

The canonical root is prepared as:

```text
C:\AI\RusPersonalAgent\
├── app\
├── config\
├── data\
├── workspace\
├── artifacts\
├── logs\
├── backups\
├── packages\
├── diagnostics\
└── temp\
```

Existing `.env` is preserved/migrated when found. Docker named volumes are not deleted. The previous `app` directory is moved to a timestamped backup before staged replacement.

## Local launch policy in this build

The user-facing runtime has **required** capabilities (Core, Ollama, Search, Browser) and an **isolated optional** Code worker. A Code-worker image/runtime failure no longer prevents the UI, Chat, Web, Research or Files from starting. The UI/API reports Code as `degraded` until its strict acceptance passes.

`CODE-ACCEPTANCE.cmd`, `FULL-ACCEPTANCE.cmd` and `RELEASE-ACCEPTANCE.cmd` remain fail-closed: they do not convert degraded Code into PASS.

After `RUN-FIRST.cmd`, the expected local URL is:

```text
http://127.0.0.1:3100/
```

If startup reports Code degraded, use the rest of the product normally and run `CODE-ACCEPTANCE.cmd` separately to diagnose the sandbox.

## Daily commands after installation

Run from `C:\AI\RusPersonalAgent`:

```powershell
.\START.cmd
.\STOP.cmd
.\RESTART.cmd
.\STATUS.cmd
.\VERIFY.cmd
.\REPAIR.cmd
.\ADMIN.cmd
```

Acceptance:

```powershell
.\WEB-ACCEPTANCE.cmd
.\CODE-ACCEPTANCE.cmd
.\FULL-ACCEPTANCE.cmd
.\RELEASE-ACCEPTANCE.cmd
```

LAN mode remains available:

```powershell
.\LAN-ENABLE.cmd
.\LAN-STATUS.cmd
.\LAN-DISABLE.cmd
```

## Release truth

0.7.4-local.3 fixes Windows distribution/first-run UX. It is **not v1.0**. v1.0 is reserved for the mandatory MASTER-SPEC acceptance matrix, including remaining context/memory, full coding-agent, media, automation/connectors, public/server operations and the required reference Windows/VPS/payment/reboot/clean-machine gates.

## 0.7.4-local.3 Windows hotfix note

This build fixes both Windows failures observed on the reference machine:

- native Docker/Compose stderr can no longer become a terminating PowerShell 5.1 `RemoteException` during expected readiness probes or build progress;
- Core `/api/health` no longer performs a real SearXNG search every health interval. Health is internal-only, so Google/Startpage captchas or DuckDuckGo timeouts cannot create a startup failure loop.

The repeated `BrokenPipeError` was a consequence of the old slow external-search health check. Client disconnects are now handled without a server traceback. Real external Web quality is tested separately by `WEB-ACCEPTANCE.cmd`.

The runtime also verifies that the running `par-rus-core` image matches the installed release, so an old `personal-agent-core:0.7.3` container cannot be silently accepted as current.
