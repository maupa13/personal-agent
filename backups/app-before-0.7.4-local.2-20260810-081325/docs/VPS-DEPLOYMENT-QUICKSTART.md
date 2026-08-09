# VPS Deployment Quick Start — v0.7.3

Goal: publish Personal Agent Rus to a small Linux VPS without manually assembling the application there.

## You need

- VPS IP/hostname;
- SSH username plus password **or** private key;
- public domain whose A/AAAA record can point to the VPS;
- inbound TCP 80/443 allowed by the VPS/cloud firewall;
- for server-lite: an external AI API/provider, either configured beforehand in the local Admin and selected for transfer, or configured on the VPS after deployment.

## Admin workflow

1. Open `Администрирование → VPS / Deploy`.
2. Enter host, SSH port, username and domain.
3. Click **Получить fingerprint** and verify/store the server host key.
4. Save the target.
5. If Docker is not installed and root SSH is being used, enter the SSH credential and click **Подготовить VPS**.
6. Click **Preflight**. For a small VPS select/review `server-lite`.
7. Optionally choose an existing external AI provider in `AI provider после deploy`.
8. Click **Deploy + Hot Verify**.
9. PASS is shown only after internal Core health and real public HTTPS exact-version verification succeed.

The SSH password/private key is never saved as target metadata.

## What an ordinary hosted user installs

Nothing. A hosted user opens the HTTPS site, registers/logs in and uses the configured remote/API providers. Local Docker/Ollama/GPU installation is only for the local/self-hosted or future Edge profile.

## Updating / rollback

Each deploy creates a new release directory and keeps `current` and `previous` pointers. `Rollback` switches to the previous release without deleting the persistent data volume.

## Local developer/LAN mode remains supported

The VPS workflow does not replace the local Docker product. On the development/home PC use:

- `LAN-ENABLE.cmd`
- `LAN-STATUS.cmd`
- `LAN-DISABLE.cmd`

LAN exposure is scoped to the Windows **Private** firewall profile and the configured UI port.
