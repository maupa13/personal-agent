# Deployment Architecture — v0.7.3

## Profiles

### local

Full Docker runtime on the Windows/Linux workstation: Core, local Ollama, SearXNG, sandboxed browser worker, Code worker, files/artifacts, auth and billing. Default bind is localhost. The supported Windows LAN workflow can expose only the Personal Agent UI to a Private network.

### server-lite

Designed for small public VPS nodes with a built-in tiny demo model:

```text
Internet
→ DNS / HTTPS
→ Caddy
→ Personal Agent Core
→ remote/BYOK/platform-paid AI provider
```

The server-lite bundle includes a local Ollama service seeded with `qwen3:0.6b` for demos. It still leaves SearXNG/browser worker and Code worker out of the bundle. Chat/Auth/Files/Tasks/Billing/Admin remain available in the control plane.

### server-standard

Same secure control plane, with capacity for additional workers/services. Heavy services are opt-in rather than mandatory.

### edge

Planned next vertical slice: an installable local worker that initiates an outbound authenticated connection to the user's cloud/VPS control plane and exposes explicitly granted local GPU/files/tools without router port forwarding.

## Deployment Manager UI

`Admin → VPS / Deploy` stores only target metadata:

- name
- host/IP
- SSH port
- username
- public domain
- profile
- trusted SSH host-key SHA256 fingerprint

Password/private key/passphrase are supplied only for the explicit operation and are never persisted in deployment target storage.

## Fresh VPS bootstrap

`Подготовить VPS` is an explicit admin action. With root SSH on a Debian/Ubuntu-family host it:

1. detects OS;
2. installs Docker + Compose from distribution package repositories;
3. enables/starts Docker;
4. verifies `docker` and `docker compose`.

It does not execute a mutable `curl | sh` installer. Non-root deployment is supported after Docker access exists; its release root is under the SSH user's home. Root deployments use `/opt/personal-agent`.

## Staged deployment

```text
SSH fingerprint verify
→ preflight
→ resolve remote release root
→ upload exact release Core bytes
→ extract new immutable release directory
→ current/previous symlink staging
→ docker compose up -d --build
→ internal Core health verification
→ public HTTPS exact-version verification
→ optional remote provider bootstrap
→ PASS
```

No normal deploy/repair path uses `docker compose down -v`, `volume prune`, `system prune` or database deletion.

## Public HTTPS verification

After internal Core health passes, the Deployment Manager repeatedly requests:

```text
https://<configured-domain>/api/system
```

with a bounded timeout. It requires:

- valid public HTTPS according to the system TLS verifier;
- HTTP 200;
- `product == Personal Agent Rus`;
- `version == release version`.

DNS/firewall/TLS errors therefore fail the deployment job instead of generating a false green status.

## Optional AI provider bootstrap

For server-lite the admin may select an already configured **external** provider before Deploy. The default bundle also seeds a local `qwen3:0.6b` Ollama model for demos. After public HTTPS verification the Deployment Manager:

1. reads the provider credential only in memory;
2. sends provider configuration to the new VPS over verified HTTPS using the generated/provided server Admin token;
3. discovers models on the VPS;
4. maps Auto/Fast/Smart to compatible discovered models, preserving existing local route choices where possible;
5. returns only redacted metadata in the deployment result.

The local system provider (`local-ollama`) cannot be copied to server-lite through this flow.

## Server auth hardening

Server bundles force:

```text
PA_RUNTIME_PROFILE=server
PA_AUTH_MODE=accounts
PA_SECURE_COOKIES=1
```

For account email verification and password recovery, the direct VPS workflow
now includes a local SMTP relay container in `compose.vps.yaml`. `core` should
therefore point to:

```text
PA_SMTP_HOST=smtp
PA_SMTP_PORT=25
PA_SMTP_FROM=robot@<your-domain>
PA_SMTP_STARTTLS=0
PA_SMTP_USE_SSL=0
```

and the server environment should also define:

```text
PA_SMTP_DOMAIN=<your-domain>
PA_SMTP_HOSTNAME=mail.<your-domain>
PA_SMTP_DKIM_SELECTOR=mail
```

For the direct VPS workflow based on `deploy/server/.env.vps` and
`compose.vps.yaml`, these variables should be stored in `.env.vps` before the
standard deploy command. During:

```text
docker compose --env-file deploy/server/.env.vps -f compose.vps.yaml up -d --build
```

the stack starts both `core` and the local `smtp` relay. That makes
registration, email verification and password-reset mail work without extra
Admin UI setup, provided the domain also has valid DNS mail records and the VPS
provider does not block outbound `25/tcp`.

For routine updates from the VPS git checkout, the supported sequence is:

```text
cd /opt/rodnoi-agent
git pull --ff-only --autostash origin master
docker compose --env-file deploy/server/.env.vps -f compose.vps.yaml up -d --build
```

This assumes the checkout has no unresolved merge state. A local
`deploy/server/.env.vps` override is acceptable; `--autostash` will preserve it
across the fast-forward update.

Session cookies are HttpOnly + SameSite=Lax + Secure. Authenticated state-changing USER endpoints require a per-session HMAC CSRF token obtained from same-origin `/api/auth/me`. Admin API continues to use explicit Bearer admin authentication.

## Persistent layout

Root SSH:

```text
/opt/personal-agent/
├── releases/<version>-<timestamp>/
├── current -> releases/...
└── previous -> releases/...
```

Non-root SSH:

```text
$HOME/.local/share/personal-agent/
├── releases/...
├── current
└── previous
```

User data remains in stable Docker named volumes and is not tied to release directories.
