# Authentication and Registration SDD

## Current baseline

v0.2.x has no USER registration or login. It has a local anonymous USER surface and ADMIN bearer-token authentication.

This is insufficient for LAN/VPS/multi-user operation.

## Deployment policy

`PA_AUTH_MODE`:

- `personal` — localhost/single-owner profile; USER login optional/disabled.
- `accounts` — user session required.

`PA_REGISTRATION_POLICY`:

- `open`
- `approval_required`
- `closed`

## Entities

### User

```text
id
username/display_name
email_normalized
password_hash
role
status
created_at
updated_at
```

Roles initially:

```text
USER
ADMIN
```

### Session

```text
id
user_id
token_hash
csrf_token_hash
created_at
expires_at
last_seen_at
revoked_at
```

Raw session tokens are never persisted.

## Routes

Browser pages:

```text
/register
/login
/account
```

API:

```text
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
```

Admin:

```text
GET  /api/admin/users
POST /api/admin/users/{id}/approve
POST /api/admin/users/{id}/disable
```

## Password policy

Use a slow salted password KDF. Never use plain SHA256/MD5.

Do not log submitted credentials.

## Cookies

Session cookie:

```text
HttpOnly
SameSite=Lax
Path=/
Secure on HTTPS deployments
```

State-changing session-authenticated requests require CSRF protection.

## User data isolation

When `accounts` mode ships, server-side conversations/workspaces/artifacts/tasks must carry `user_id` and every repository query must enforce ownership.

Browser localStorage alone is not acceptable multi-user persistence.

## Acceptance

- register page visible in accounts mode;
- duplicate email rejected;
- bad credentials rejected;
- good login creates HttpOnly session;
- logout revokes session;
- session expiry handled;
- disabled user cannot login;
- USER cannot use Admin API;
- two users cannot read each other's conversation/workspace/artifact;
- registration policy open/approval/closed behaves as configured;
- personal mode remains usable without account creation.
