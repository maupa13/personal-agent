# Personal Agent Rus 0.7.0 — Orchestrator / VPS Deployment / Monitoring / LAN

This release keeps the complete v0.6 Chat/Auth/Providers/Web/Research/Files/Code/Billing stack and adds the next vertical layer: durable tasks, multi-capability research reports, VPS publication, weak-server profiles, public hot verification, monitoring and preserved Windows LAN mode.

## What is new

- durable Task/Step/Event state with cancel + restart recovery;
- USER journey: Research → verified MD + XLSX + PDF artifacts;
- Admin `VPS / Deploy` manager;
- SSH password or private-key auth, pinned SSH host fingerprint;
- optional **Prepare VPS** for fresh Debian/Ubuntu root hosts using distribution Docker/Compose packages;
- `server-lite` for weak VPS: Core + HTTPS + remote/BYOK AI rather than a local GPU stack;
- staged releases with `current` / `previous` and explicit rollback;
- deployment PASS requires internal Core health **and** public HTTPS exact-version verification;
- optional transfer of an already configured external AI provider to server-lite after HTTPS verification;
- accounts-mode CSRF protection and Secure cookies in server profile;
- lightweight Admin monitoring for uptime/load/RAM/disk/DB/tasks/artifacts/usage/deployment alerts;
- preserved local Docker + Windows Private-LAN commands.

## Windows update

Extract over the existing Personal Agent Rus working directory while preserving `.git` and `.env`, then run:

```powershell
.\VERIFY-PACKAGE.ps1
.\REPAIR.cmd
.\FULL-ACCEPTANCE.cmd
.\RELEASE-ACCEPTANCE.cmd
```

For local network access:

```powershell
.\LAN-ENABLE.cmd
.\LAN-STATUS.cmd
# later
.\LAN-DISABLE.cmd
```

## VPS publication

Open `Администрирование → VPS / Deploy`. You need host/IP, SSH user + password/private key, SSH host fingerprint and a public domain. If the VPS is fresh and uses Debian/Ubuntu, root SSH can run **Подготовить VPS** first. Then Preflight → Deploy + Hot Verify.

A small `server-lite` VPS does **not** need Ollama/GPU/Playwright/Code Worker. Select an existing external AI provider during deploy or configure one in the VPS Admin after publication.

Read `docs/VPS-DEPLOYMENT-QUICKSTART.md`.

## Truthful release status

This is still not v1.0. Real VPS/DNS/TLS/provider/browser acceptance, real Windows lifecycle/reboot, real LAN device, real YooKassa merchant payment and other environment-bound gates remain explicit `BLOCKED_ENVIRONMENT` until run against those environments. The canonical specification remains `docs/specification/MASTER-SPEC.md`; machine-readable coverage is `tests/user-journeys-registry.json`.
