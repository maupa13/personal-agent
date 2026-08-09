# Personal Agent Rus 0.8.0 — Productization SDD

Status: **MANDATORY before Beta / 1.0**  
Baseline: `0.7.4-local.5`  
Goal: turn the working technical local alpha into a coherent consumer product for the Russian market.

## 1. Release truth

`0.7.4-local.5` is a technical alpha. Containers, local inference, web/browser, files, code sandbox, billing foundation and admin foundation exist, but this is not yet a polished end-user product.

`0.8.0-alpha.1` MUST NOT be declared complete until every mandatory item in this document has evidence.

## 1.1 Release posture for 1.0.0

`1.0.0` is a VPS-first release target.

- The primary production path is VPS/public deployment with browser access.
- Local models and local-edge expansion are phase 2, not a prerequisite to call the VPS product release-ready.
- VPS production verification must be done as a separate Linux/VPS gate with real deployment evidence.
- Browser suites remain a separate environment-bound gate when the browser automation runtime is unavailable.
- Code-worker must be verified on the Linux/VPS path, not only in a local Windows compatibility gate.
- Artifact formats must keep working when optional libraries are present or absent.

## 2. UX/UI shell — mandatory

### 2.1 Sidebar

- Desktop sidebar is resizable by drag.
- Width range: 240–420 px; persisted per browser/user.
- Sidebar can collapse to a compact rail; `Ctrl+B` toggles it.
- Mobile uses overlay drawer, never a permanently reserved column.
- `Новый чат` becomes compact and visually primary, not an oversized permanent bar.
- `Ctrl+K` is global search/command palette; new chat uses `Ctrl+N`.
- Conversations are grouped by `Сегодня / Вчера / 7 дней / Старше`.
- Support pin/archive/rename/delete.
- Support user folders/projects and move conversation to folder.
- Search matches titles and message content.

### 2.2 Primary navigation

Normal USER must NOT see infrastructure/admin concepts in primary navigation.

Primary USER navigation:

- Новый чат
- Поиск
- Проекты / папки
- Диалоги
- Workspace (contextual): Files / Artifacts / Tasks
- Account / Plan
- Settings

`Администрирование`, provider IDs, models, Docker, routing, deployment and diagnostics are hidden from USER.

Admin is available only to an authenticated privileged account or an explicit break-glass owner flow.

### 2.3 Modes

The permanent three-button `Авто / Быстро / Умно` strip is removed from the top bar.

Default: `Авто`.

Optional execution mode is a compact selector near the composer:

- Авто
- Быстро
- Глубоко

The selector only displays modes allowed by the current plan/entitlements. Technical model/provider data is never shown to USER.

### 2.4 Composer

- Compact attachment/tools button.
- Mode selector near composer, not top chrome.
- Stop-generation button while running.
- Clear status phases: `Ищу`, `Читаю`, `Анализирую`, `Выполняю`, `Проверяю`.
- No debug/runtime text in normal mode.
- Drag/drop files.
- Mobile safe-area support.

### 2.5 Welcome/onboarding

First-run welcome explains why the product exists:

1. Private/local-first AI.
2. Can search, read, execute and verify — not only chat.
3. Creates real files/artifacts.
4. Hybrid routing: local first, remote only by policy/plan.
5. Russian-market accounts, billing and deployment.

Onboarding wizard:

- Personal computer
- Home/LAN
- Team/VPS

Then configure owner/admin, access policy, registration policy, AI provider and privacy.

## 3. Conversations and persistence — mandatory

Browser `localStorage` is no longer the canonical conversation store.

### 3.1 Local DB

LOCAL/EDGE uses SQLite.

Required tables:

- users
- sessions
- folders
- conversations
- messages
- message_sources
- artifacts
- tasks
- audit_events
- usage_events
- subscriptions
- payments

Every user-owned entity has `user_id` and every repository query enforces ownership.

SQLite requirements:

- WAL mode
- foreign_keys=ON
- busy_timeout
- indexes on `(user_id, updated_at)`, conversation messages, usage period, sessions
- migrations with schema version
- backup/restore verification

SERVER/SaaS target: PostgreSQL via repository abstraction; do not force PostgreSQL onto single-PC LOCAL installations.

### 3.2 Conversation UX

- Conversations survive browser cache clear and restart.
- Same account sees history on another LAN device.
- Folders/projects are server-side.
- Export current chat: MD.
- Export all: JSON/ZIP.
- Import is versioned and validated.

## 4. Authentication / authorization — mandatory

Current auth foundation is upgraded to product auth.

### 4.1 Modes

`personal`:
- single owner; login optional.

`accounts`:
- authentication mandatory.
- required for LAN multi-user and VPS.

Registration policy:
- open
- approval_required
- closed

### 4.2 Security

- Password hashing: Argon2id preferred; migration path from existing PBKDF2 hashes.
- HttpOnly session cookies.
- SameSite=Lax/Strict as applicable.
- Secure on HTTPS.
- CSRF for state changes.
- Session rotation and revoke-all.
- Login rate limiting / temporary lockout.
- No credentials/tokens in logs.
- Admin password reset flow for self-hosted deployments.

### 4.3 Roles

Minimum roles:

- OWNER
- ADMIN
- USER

ADMIN Console access is role-based.

The `.env` admin token becomes **break-glass only**, not the normal Admin UX login.

## 5. LAN — mandatory local-product capability

`LAN-ENABLE` must:

- bind only to private LAN interfaces / configured bind address;
- configure Windows Firewall Private profile;
- automatically require `accounts` mode unless operator explicitly selects trusted single-user LAN;
- default registration to `approval_required`;
- display exact device URL and QR code;
- show LAN status in Admin;
- support second-device login and isolated data.

HTTP LAN may support chat/files, but features requiring Secure Context (microphone/camera) must be clearly marked. Production-quality phone voice/media requires an HTTPS LAN path or an approved secure bridge.

Mandatory E2E: desktop PC + second phone/laptop.

## 6. Plans / entitlements — mandatory

Plans remain:

- Light — 0 RUB/month
- Medium — 500 RUB/month
- Pro — 1000 RUB/month
- OWNER/ADMIN — commercially unrestricted, usage still measured

Local inference is effectively unlimited for all plans.

Remote platform-paid usage is quota-controlled.

Add explicit `plan_entitlements` instead of only remote token limits.

Example feature keys:

- chat
- web
- deep_research
- files_read
- files_create
- code
- long_tasks
- remote_ai
- priority_queue
- advanced_exports
- automation
- media

USER `/api/system` returns only the effective entitlements, never hidden plan internals.

UI:

- unavailable feature shows a short lock/upgrade explanation;
- hidden technical modes are not rendered;
- no API-only enforcement: backend MUST enforce every entitlement.

## 7. Billing / business — mandatory foundation

Keep YooKassa adapter but complete product lifecycle:

- checkout idempotency
- webhook verification by provider re-fetch
- recurring payment
- cancel at period end
- grace period
- failed renewal state
- upgrade/downgrade rules
- admin plan assignment
- refund/partial-refund state model
- reconciliation job
- payment audit timeline
- user invoices/receipt references where applicable
- billing export CSV

Real merchant production remains environment-bound until actual YooKassa credentials/webhooks are tested.

## 8. Admin Console — mandatory redesign

Admin Console is a separate product surface, not a list of technical forms.

### 8.1 Dashboard

Cards + trends:

- users active/new
- active sessions
- requests/min
- p50/p95 latency
- error rate
- local inference jobs
- web jobs/errors
- code jobs/errors
- tokens by provider
- estimated remote cost
- active subscriptions by plan
- failed payments
- disk/RAM/VRAM
- current alerts

### 8.2 Users

- search/filter
- status
- role
- plan
- registration approval
- disable/enable
- revoke sessions
- reset access
- per-user usage
- artifact/task counts
- last activity

### 8.3 Plans/Billing

- plan entitlements editor
- quotas
- subscription list
- payment timeline
- renewals/failures
- refunds foundation
- reconciliation status

### 8.4 AI / Routing

- providers
- models
- health
- cost rates
- route policies
- fallback chain
- plan/role eligibility

### 8.5 Runtime

- services health
- versions/image tags
- model inventory
- GPU/VRAM
- queues
- disk/RAM
- backups
- update state
- LAN state

### 8.6 Security/Audit

- login failures
- session revocations
- admin changes
- provider changes
- plan changes
- payment events
- deployment actions
- permission denials

Audit entries must include actor, action, target, outcome, timestamp and correlation ID; never raw secrets.

## 9. Observability and debug logging — mandatory until 1.0

### 9.1 Structured application log

JSONL record fields:

- timestamp
- level
- service
- version
- event
- request_id
- correlation_id
- user_id (internal ID; not email)
- conversation_id
- task_id/job_id
- intent
- route/provider/model
- duration_ms
- status
- error_type

Tool stage timings where applicable:

- routing_ms
- search_ms
- browser_ms
- inference_ms
- artifact_ms
- code_ms

### 9.2 Privacy

Default logs MUST NOT store:

- passwords
- session tokens
- API keys
- payment secrets
- raw Authorization headers
- full uploaded private file contents

Debug prompt/content logging is explicit opt-in, redacted and visibly marked.

### 9.3 Rotation / retention

LOCAL defaults:

- app logs: 20 MB × 10 files
- audit: DB retained 90 days minimum unless operator changes it
- diagnostics bundles: operator-created only

Admin can:

- view recent logs
- filter by level/service/request ID/user ID
- download diagnostic bundle
- clear old debug logs

Diagnostic bundle includes sanitized:

- product version
- compose/docker status
- service health
- recent errors
- configuration keys without secrets
- disk/RAM/GPU summary
- last acceptance results

## 10. Web quality — mandatory product behavior

For a news/current-information request:

- final answer MUST contain an actual synthesized answer;
- sources are evidence below the answer, never the answer itself;
- homepage/navigation dumps are not accepted as primary evidence;
- deduplicate sources;
- prefer article pages;
- dates visible when available;
- source count and quality thresholds depend on task type;
- `Research` may use many sources, ordinary Web questions should not flood the UI.

Quality fallback must never fabricate freshness if evidence is insufficient.

## 11. Guide / docs — mandatory

Ship in-product Guide plus files:

- `USER-GUIDE.md`
- `ADMIN-GUIDE.md`
- `LAN-GUIDE.md`
- `PRIVACY-AND-DATA.md`
- `PLANS-AND-LIMITS.md`
- `TROUBLESHOOTING.md`
- `WHY-PERSONAL-AGENT-RUS.md`

`WHY-PERSONAL-AGENT-RUS.md` must explain concrete implemented differentiation, not marketing claims without acceptance evidence.

## 12. Product differentiation

The product is not differentiated by the word `Rus` or by a dark chat UI.

The unique proposition must be implemented in the product:

**Private local-first agent workspace for Russian users that can use local GPU, search the web, work with files/projects, execute code/tasks, verify artifacts, switch to remote AI under explicit plan/cost policy, and be administered/deployed without exposing model/Docker internals to ordinary users.**

This proposition must be visible in onboarding, settings and docs.

## 13. Mandatory 0.8 acceptance journeys

- UX-001 sidebar resize persists.
- UX-002 sidebar collapse/expand; mobile overlay.
- UX-003 folder create/rename/delete and move chat.
- UX-004 time-grouped conversations.
- UX-005 normal USER cannot see Admin nav/routes/data.
- UX-006 mode control is compact and entitlement-aware.
- UX-007 first-run onboarding completes.
- CONV-001 conversation persists server-side after browser cache clear.
- CONV-002 same account sees history from second device.
- CONV-003 user A cannot read user B history/folders/messages.
- AUTH-001 open registration.
- AUTH-002 approval-required registration.
- AUTH-003 closed registration.
- AUTH-004 login/logout/session expiry/revoke.
- AUTH-005 rate-limit failed login.
- AUTH-006 ADMIN account reaches Admin; USER receives 403.
- LAN-001 enable/disable/status.
- LAN-002 second-device login.
- LAN-003 two-user isolation over LAN.
- PLAN-001 Light entitlements enforced backend+UI.
- PLAN-002 Medium entitlements enforced backend+UI.
- PLAN-003 Pro entitlements enforced backend+UI.
- PLAN-004 local inference does not consume remote quota.
- PLAN-005 platform remote quota exhaustion falls back/blocks predictably.
- BILL-001 checkout deterministic.
- BILL-002 webhook idempotency and re-fetch verification.
- BILL-003 cancel-at-period-end.
- BILL-004 renewal failure/grace state.
- ADMIN-001 dashboard metrics render from real API data.
- ADMIN-002 user/role/plan/session actions audited.
- ADMIN-003 provider/routing changes audited.
- OBS-001 structured request log has request/correlation IDs.
- OBS-002 secrets absent from logs.
- OBS-003 log rotation.
- OBS-004 diagnostic bundle sanitization.
- WEB-001 current-news answer contains synthesis + sources.
- WEB-002 no homepage dump as answer.
- GUIDE-001 first-run guide reachable from UI.
- GUIDE-002 docs survive package install/update.

## 14. Release sequence

- `0.8.0-alpha.1` — UX shell + server conversations + role-based Admin + structured logging.
- `0.8.0-alpha.2` — plan entitlements + billing/admin integration + LAN accounts E2E.
- `0.8.0-beta.1` — onboarding/guides + quality hardening + second-device E2E + backup/restore.
- `0.9.0` — feature-complete local beta against the agreed 1.0 scope.
- `1.0.0` — only after mandatory user journeys and real Windows/LAN/payment/VPS environment gates have evidence.

## 15. Non-negotiable rule

A green container health check is not product readiness.

A feature is ready only when:

`UI → API → policy/auth → execution → persistence → verification → restart/reopen → user E2E → evidence = PASS`.
