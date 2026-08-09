# Родной Агент / Personal Agent 1.0.0 — Release baseline

Шестой productization slice ветки 0.8. Цель релиза — сделать Web-ответы проверяемыми по источникам, улучшить представление найденных результатов и превратить Windows/debug диагностику в инструмент, по которому можно быстро локализовать реальный сбой.

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

## Что нового в alpha.6

- строгая привязка к явно указанному домену: `dtf.ru` не подменяется другим источником;
- Admin Search Policy: source limits, preferred/blocked domains и site profiles;
- адаптивные карточки news/product/real-estate/procurement с reduced-motion fallback;
- время ответа и безопасные request/correlation/timing metadata;
- Windows lifecycle diagnostics: stage + endpoint + HTTP status + body + timing + trace IDs;
- YooKassa setup readiness checklist и отдельный Admin runbook;
- исправлено отображение export/artifact list после реального browser regression;
- USER и ADMIN browser journeys разделены на независимые deterministic suites;

Сохраняется UX Complete из alpha.5:

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

## Сохраняется из alpha.1–alpha.5

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
