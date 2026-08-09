# Родной Агент / Personal Agent 0.8.0-alpha.5 — UX Complete Pass

Пятый productization slice ветки 0.8. Цель этого релиза — закрыть базовый пользовательский UX до перехода к PostgreSQL/VPS beta: локализованный бренд, полноценный RU/EN путь, state-matrix, доступность, устойчивый sidebar и единый responsive layout.

Внутренняя edition/package identity остаётся `Personal Agent Rus` (`edition=rus`), но обычный пользователь видит:

- RU: **Родной Агент**;
- EN: **Personal Agent**.

## Установка / обновление Windows

Распакуйте пакет во временный каталог и запустите:

```powershell
.\RUN-FIRST.cmd
```

Каноническая установка: `C:\AI\RusPersonalAgent\`. Конфигурация, workspace, artifacts, backups, модели и Docker named volumes сохраняются; перед заменой application payload создаётся backup предыдущего `app`.

После запуска: `http://127.0.0.1:3100/`

## Что нового в alpha.5

- локализованный пользовательский бренд: `Родной Агент / Personal Agent`;
- RU/EN shell, account, onboarding, Admin, Help links и ключевые динамические статусы;
- обязательный UX state matrix: booting / starting / degraded / offline / quota / permission / error / ready;
- понятный Retry вместо white screen/raw traceback;
- keyboard sidebar resize, clean collapsed rail, visible focus;
- `prefers-reduced-motion` и accessibility foundation;
- светлая / тёмная / системная тема на USER/Auth/Admin поверхностях;
- полноширинные Web textarea и Code editor;
- корректный вид проектов и явное действие `Новый проект`;
- UX-009 теперь mandatory PASS для alpha.5, а не отложенный pre-beta пункт.

## Сохраняется из alpha.1–alpha.4

Server-side chats/projects/onboarding, OWNER/ADMIN/USER, structured logs/diagnostics, entitlements, sessions/Argon2id, LAN foundation, PostgreSQL foundation, Scenario Engine, bounded clarification, site profiles, local/remote execution policy, tone presets, Share Chat, Feedback и Admin provider/model/routing management.

## Честные ограничения

- `PG-RUNTIME-001`: PostgreSQL ещё не canonical Core persistence;
- `BILL-LIVE-001`: реальный merchant flow требует environment/credentials/HTTPS webhook gate;
- physical second-device LAN, Windows reboot и clean-machine — environment gates;
- `VPS-EGRESS-001`: RU/global egress routing ещё не реализован;
- полный physical mobile/Secure Context acceptance остаётся отдельным real-device gate.

## Проверки

```powershell
.\VERIFY.cmd
.\CODE-ACCEPTANCE.cmd
.\FULL-ACCEPTANCE.cmd
```

Подробнее: `docs/0.8.0-ALPHA5-UX-COMPLETE.md`, `docs/USER-GUIDE.md`, `docs/ADMIN-GUIDE.md`, `docs/MASTER-IMPLEMENTATION-PROMPT-v5.md`.
