# Personal Agent Rus 0.7.4-local.4 — quality local launch candidate

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

0.7.4-local.4 fixes Windows distribution/first-run UX. It is **not v1.0**. v1.0 is reserved for the mandatory MASTER-SPEC acceptance matrix, including remaining context/memory, full coding-agent, media, automation/connectors, public/server operations and the required reference Windows/VPS/payment/reboot/clean-machine gates.

## 0.7.4-local.4 Windows hotfix note

This build closes the next failure found by the real Windows reference run after `0.7.4-local.3` successfully started Ollama, SearXNG, Browser, Code Worker and Core.

The worker process intentionally runs with `cap_drop: ALL` and only a minimal capability add-back. The previous job setup changed each job directory to `runner:runner` with mode `0700` before the root supervisor created `main.py`. Because the supervisor does **not** have `CAP_DAC_OVERRIDE`, the first real Code job failed even though the worker socket and runtime inventory were healthy.

`0.7.4-local.4` keeps the job directory supervisor-owned, assigns the runner group, and uses `0770`. The unprivileged runner can execute inside the directory while the supervisor can create/read job artifacts. No broad filesystem-bypass capability is added back.

Normal `START` / `REPAIR` / baseline `VERIFY` are also fail-soft for a failed real Code execution smoke: Chat/Web/Research/Files still launch and Code is reported as degraded. `CODE-ACCEPTANCE`, `FULL-ACCEPTANCE` and `RELEASE-ACCEPTANCE` remain strict.

Code smoke failures now include the returned job status/error/result diagnostics, and the worker logs non-sensitive job failure metadata instead of staying silent.
