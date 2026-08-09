# Personal Agent Rus 0.8.0-alpha.3 — Scenario Engine & Bounded Clarification

Третий productization slice ветки 0.8. Поверх server-history, Accounts/LAN/Entitlements и PostgreSQL foundation добавлен сценарный слой для обычных пользователей, которым не нужно знать, как писать промпты.

## Установка / обновление Windows

Распакуйте пакет во временный каталог и запустите:

```powershell
.\RUN-FIRST.cmd
```

Каноническая установка:

```text
C:\AI\RusPersonalAgent\
```

Конфигурация, workspace, artifacts, backups, модели и Docker named volumes сохраняются. Перед заменой application payload создаётся backup предыдущего `app`.

После запуска: `http://127.0.0.1:3100/`

## Что нового

- Scenario Gallery для одежды, закупок, недвижимости, подарков, товаров, поездок и новостей;
- тот же Scenario Engine работает в `Авто` по обычному тексту без клика по карточке;
- bounded clarification: 1 сгруппированный вопрос для обычных сценариев, максимум 2 для закупок/недвижимости;
- после лимита уточнений агент продолжает с разумными предположениями;
- explicit URL route имеет приоритет над generic scenario detection;
- server-side Web preferences пользователя;
- Admin site profiles для технической стратегии известных сайтов;
- site profile домен участвует в scoped search, а browser/static order применяется к чтению страницы;
- regression-защита от попадания внутренних clarification markers в поиск.

## Сохраняется из alpha.1/alpha.2

- server-side chats/projects/onboarding;
- OWNER/ADMIN/USER;
- structured logs/diagnostics;
- backend-authoritative entitlements;
- Argon2id + session controls;
- registration policies;
- LAN status/address/QR;
- PostgreSQL server foundation.

## Честные ограничения

- `PG-RUNTIME-001`: PostgreSQL ещё не canonical Core persistence;
- `egress_region`: policy metadata до отдельного multi-region worker gate;
- physical second-device LAN, Windows reboot, clean-machine, live payment/VPS — environment gates;
- полный cross-surface `UX-009` — mandatory pre-beta.

## Проверки

```powershell
.\VERIFY.cmd
.\CODE-ACCEPTANCE.cmd
.\FULL-ACCEPTANCE.cmd
```

Deterministic development gates:

```text
python tests/scenario_acceptance.py
python tests/run_acceptance.py
python tests/browser_journeys.py
python tests/release_gate.py
```

Подробнее: `docs/0.8.0-ALPHA3-SCENARIOS.md`, `docs/0.8.0-ALPHA2-ACCOUNTS-LAN-ENTITLEMENTS.md` и `docs/MASTER-IMPLEMENTATION-PROMPT-v5.md`.
