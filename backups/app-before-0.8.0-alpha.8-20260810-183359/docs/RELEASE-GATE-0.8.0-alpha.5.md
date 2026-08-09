# Родной Агент / Personal Agent 0.8.0-alpha.5 — Release Gate

## Итог

```text
Version:                 0.8.0-alpha.5
Milestone:               UX Complete Pass
Deterministic PASS:      199
Deterministic FAIL:      0
Unique deterministic IDs:178
Authoritative suites:    15
UX-009:                  PASS
```

Монолитный `tests/release_gate.py` завершился с exit code `0` на frozen alpha.5 bytes. До него те же ключевые suites были прогнаны отдельно; Core API и оба Chromium journey также завершились `exit 0`.

## Пользовательская идентичность

```text
Internal family:  Personal Agent
Internal edition: Personal Agent Rus / rus
RU USER display:  Родной Агент
EN USER display:  Personal Agent
```

Внутренняя edition identity не должна отображаться обычному USER как название продукта.

## Закрытый alpha.5 scope

- RU/EN USER shell, account, guided onboarding and Admin localization foundation;
- RU display brand `Родной Агент`, EN display brand `Personal Agent`;
- light / dark / system theme;
- complete USER runtime state matrix: booting / starting / degraded / offline / quota / permission / error / ready;
- Retry/recoverable state instead of raw traceback/white screen;
- keyboard sidebar resize and accessible separator semantics;
- clean collapsed navigation rail;
- `prefers-reduced-motion` + visible focus foundation;
- responsive settings forms, Web domain textareas and Code editor;
- existing alpha.1–alpha.4 capabilities remain regression-covered: conversations/projects, roles, onboarding, observability, accounts/entitlements, scenarios/site profiles, local/remote execution policy, tone presets, sharing, feedback, Admin model/provider/routing, billing foundation, Web/Files/Code/Tasks.

## Authoritative suites

- `static`
- `distribution`
- `windows-contract-static`
- `local-launch-contract`
- `accounts-entitlements-acceptance`
- `scenario-site-preferences-acceptance`
- `ux-admin-hardening-acceptance`
- `ux-complete-acceptance`
- `ux-complete-browser`
- `orchestrator-deployment-acceptance`
- `browser-user-journeys`
- `api-acceptance`
- `productization-acceptance`
- `billing-acceptance`
- `code-worker-acceptance`

## Environment-bound — НЕ PASS

| Test | Status | Reason |
|---|---|---|
| `FND-BROWSER-LIVE-REAL-001` | BLOCKED_ENVIRONMENT | authoritative on reference Windows runtime |
| `FND-BROWSER-LIVE-SECURITY-001` | BLOCKED_ENVIRONMENT | authoritative on reference Windows Docker runtime |
| `FND-RUS-LANGUAGE-001` | BLOCKED_ENVIRONMENT | stochastic real-model language behavior is authoritative on reference Windows runtime |
| `FND-REFERENCE-SEQUENCE-001` | BLOCKED_ENVIRONMENT | runs RELEASE-ACCEPTANCE.cmd on reference Windows Docker runtime |
| `FND-REBOOT-001` | BLOCKED_ENVIRONMENT | requires real Windows reboot |
| `WEB-011` | BLOCKED_ENVIRONMENT | live DTF canary is authoritative on reference Windows with external internet |
| `WEB-012` | BLOCKED_ENVIRONMENT | live Web diagnostics are captured by WEB-ACCEPTANCE.cmd on reference Windows |
| `CODE-LIVE-001` | BLOCKED_ENVIRONMENT | real Docker code-worker image with Python/Java/PowerShell is authoritative on reference Windows Docker runtime |
| `BILL-LIVE-001` | BLOCKED_ENVIRONMENT | requires real YooKassa merchant credentials plus public HTTPS callback/webhook endpoint |
| `DEPLOY-LIVE-001` | BLOCKED_ENVIRONMENT | requires a real Linux VPS, SSH credential, DNS and public HTTPS |
| `LAN-LIVE-001` | BLOCKED_ENVIRONMENT | requires a physical second LAN device and Windows Private-network firewall |
| `CONV-003` | BLOCKED_ENVIRONMENT | requires same account on a second physical LAN device |

## Deferred later vertical slices — НЕ PASS alpha.5

| Test | Status | Mandatory from | Reason |
|---|---|---|---|
| `PG-RUNTIME-001` | NOT_IMPLEMENTED | 0.8.0-beta.1 | PostgreSQL server schema/compose are present, but canonical Core persistence switch/migration/rollback is a separate vertical slice |
| `VPS-EGRESS-001` | NOT_IMPLEMENTED | 0.9.0 | site profile egress_region is policy metadata; real RU/global worker routing requires multi-region VPS integration and policy tests |

## Release invariant

`0.8.0-alpha.5` доказывает local UX/product shell в доступной deterministic environment. Он **не** доказывает PostgreSQL canonical server persistence, реальный VPS/HTTPS, merchant payment, физический mobile/LAN, Windows reboot или clean-machine install. Эти gates остаются обязательными перед соответствующим beta/0.9/1.0 статусом.
