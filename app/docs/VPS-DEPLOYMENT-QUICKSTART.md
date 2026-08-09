# VPS Deployment Quick Start

This document covers the VPS1 + VPS2 Amnezia AWG deployment hypothesis.

Topology:

- VPS1 is the service host where Personal Agent Rus runs.
- VPS2 already has the AmneziaWG/WireGuard server running.
- VPS2 is only the VPN hop / relay for selected upstream traffic.
- The client profile for VPS1 is the exported file `not-commit/amnezia_config.vpn`.

Important: `amnezia_config.vpn` contains VPN secrets. Do not commit it, print it with `cat`, paste it into tickets, or include it in logs/screenshots.

## What belongs in `not-commit`

Use `not-commit/` as a local bootstrap pack for the VPS1 deployment.

Store there:

- `.env` templates for the VPS1 bootstrap;
- synthetic SQL seed files;
- demo owner/admin/user rows;
- promo code fixtures;
- operator notes;
- the exported VPS1 client profile `amnezia_config.vpn`.

Do not store there:

- real app/API tokens;
- real passwords;
- real user data;
- private SSH keys;
- server-side Amnezia keys or server config from VPS2.

## VPS1 env

The app env stores route metadata and the path where the `.vpn` file is placed on VPS1. It does not store the `.vpn` file contents.

For public VPS registration, keep:

```env
PA_AUTH_MODE=accounts
PA_REGISTRATION_POLICY=approval_required
```

This lets users submit registration, stores them in the DB with a password hash, and keeps ordinary new accounts pending until an admin approves them.

Do not copy Spring-style variables into this service env:

- `DB_URL=jdbc:...`, `DB_USERNAME`, `DB_PASSWORD`, and `SPRING_PROFILES_ACTIVE` are not read by this Python runtime.
- `ADMIN_TOKEN` must be `PA_ADMIN_TOKEN`.
- `OPENAI_API_KEY` can bootstrap an OpenAI provider on startup. Long-term production should use Admin provider setup so the key lives in server-side secret storage instead of env.
- Use `PA_POSTGRES_DB`, `PA_POSTGRES_USER`, `PA_POSTGRES_PASSWORD`, and `PA_DATABASE_URL` for this Python runtime. Do not use Spring-style `POSTGRES_*` / `DB_*` variables as the app configuration.

On VPS, `PA_DATABASE_URL` should point to the `postgres` compose service. If it is empty, the app falls back to local SQLite mode.

```env
PA_POSTGRES_DB=personal_agent
PA_POSTGRES_USER=personal_agent
PA_POSTGRES_PASSWORD=REPLACE_WITH_POSTGRES_PASSWORD
PA_DATABASE_URL=postgresql://personal_agent:REPLACE_WITH_POSTGRES_PASSWORD@postgres:5432/personal_agent
OPENAI_API_KEY=
PA_OPENAI_PROVIDER_ID=openai
PA_OPENAI_PROVIDER_NAME=OpenAI
PA_OPENAI_PROVIDER_TYPE=openai_responses
PA_OPENAI_BASE_URL=https://api.openai.com/v1
PA_VPN_ROUTING_ENABLED=1
PA_VPN_ROUTING_MODE=amneziawg
PA_VPN_PREFERENCE_ID=vps1-to-vps2-awg
PA_VPN_VPS2_HOST=
PA_VPN_UPSTREAM_HOST=api.deepseek.com
PA_VPN_UPSTREAM_IP=203.0.113.50
PA_VPN_ALLOWED_IPS=203.0.113.50/32
PA_VPN_PROFILE_FILE=/opt/personal-agent/secure/amnezia_config.vpn
```

Replace placeholders with real VPS2/upstream values.

## Copy the VPN profile to VPS1

Copy the local file:

```text
C:\AI\RusPersonalAgent\not-commit\amnezia_config.vpn
```

to VPS1:

```text
/opt/personal-agent/secure/amnezia_config.vpn
```

Then lock down permissions on VPS1:

```sh
mkdir -p /opt/personal-agent/secure
chmod 700 /opt/personal-agent/secure
chmod 600 /opt/personal-agent/secure/amnezia_config.vpn
```

## Bootstrap flow

1. Prepare `not-commit/vps/` locally.
2. Copy the app bootstrap files to VPS1 over SSH/PuTTY SCP/SFTP.
3. Copy `not-commit/amnezia_config.vpn` to `/opt/personal-agent/secure/amnezia_config.vpn`.
4. Install Docker/Compose on VPS1.
5. Create `parent.env`, then copy it to `.env`.
6. Import `/opt/personal-agent/secure/amnezia_config.vpn` on VPS1 using Amnezia/AWG tooling.
7. Start the app.
8. Verify login, health, HTTPS, and the upstream route.

## Verification order

1. Confirm SSH access through PuTTY.
2. Confirm `/opt/personal-agent/secure/amnezia_config.vpn` exists with `600` permissions.
3. Start/import the AmneziaWG client profile on VPS1.
4. Run `ip route get <UPSTREAM_IP>` and confirm it uses the AWG/WireGuard interface.
5. Start Personal Agent Rus with Docker Compose.
6. Verify `curl http://127.0.0.1:3100/api/health`.
7. Verify public HTTPS if Caddy/Nginx is configured.

## Local note

The repository keeps the bootstrap pack separate from runtime secrets. The `.vpn` profile is intentionally under ignored `not-commit/`; never move it into tracked source.
