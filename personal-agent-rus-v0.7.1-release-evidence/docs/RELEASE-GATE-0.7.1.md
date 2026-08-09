# Release Gate 0.7.1

Scope: durable Task Engine + `Research → MD/XLSX/PDF` + VPS Deployment Manager + weak-VPS server-lite + provider bootstrap + public HTTPS hot verification + lightweight monitoring + Windows LAN preservation.

## Mandatory deterministic gates

- full v0.6 regression: Product Shell/Auth/Providers/Web/Files/Code/Billing
- AUTH-CSRF-001 accounts-mode CSRF + Secure-cookie server contract
- TASK-001..007 durable task lifecycle, verified artifacts, isolation, cancel and restart recovery
- DEPLOY-001 server-lite excludes Ollama/GPU/browser/code worker
- DEPLOY-002 SSH host fingerprint is pinned and mismatch fails closed
- DEPLOY-003 preflight checks Docker/Compose/RAM/disk and recommends weak/standard profile
- DEPLOY-004 staged `current`/`previous` deployment and internal Core hot verify
- DEPLOY-005 rollback preserves persistent data
- DEPLOY-006 SSH password/private key/passphrase are not persisted
- DEPLOY-007 optional root bootstrap installs Docker/Compose from Debian/Ubuntu distribution packages; no curl-pipe installer
- DEPLOY-008 public `https://<domain>/api/system` must return Personal Agent Rus and the exact deployed version
- DEPLOY-009 optional selected external AI provider is configured after HTTPS verification and server routing is initialized; provider secret is not returned in deployment result
- OBS-001 Admin monitoring snapshot: uptime/load/RAM/disk/DB/tasks/artifacts/usage/deployment status/alerts
- LAN-001 Windows LAN scripts preserve named volumes and restrict firewall rule to Private profile

## Environment-bound gates

The following remain `BLOCKED_ENVIRONMENT` until executed against the real target environment; they cannot be promoted by deterministic CI:

- DEPLOY-LIVE-001 actual SSH bootstrap/deploy to a Linux VPS, real DNS, public TLS, provider call and browser chat
- BILL-LIVE-001 real YooKassa merchant/payment/webhook
- LAN-LIVE-001 real second phone/laptop over Windows Private LAN
- CODE-LIVE-001 real Docker code-worker image with Python/Java/PowerShell
- Windows lifecycle/reboot/clean-machine gates

## Release invariant

`Deploy + Hot Verify` is successful only after both checks pass:

1. Core is healthy from inside the VPS Compose network.
2. Public HTTPS `/api/system` resolves through the real domain and reports the exact release version.

If DNS, firewall or TLS is not ready, the deployment job is `FAILED`; the product never reports false publication success.
