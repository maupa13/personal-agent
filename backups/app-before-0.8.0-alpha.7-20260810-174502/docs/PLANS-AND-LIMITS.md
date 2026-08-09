# Тарифы и ограничения

Версия: 0.8.0-alpha.6

В alpha.2 действует **backend-authoritative Entitlement Engine**. UI только отображает effective access; безопасность и ограничения проверяются Core.

## Базовые профили

- **LIGHT** — обычный чат, Auto/Fast, Web, чтение файлов; без Smart/Research/Code/Create-file по умолчанию.
- **MEDIUM** — Smart, Research, создание файлов, Code и более длинные задачи.
- **PRO** — Deep Research, priority queue, advanced exports и повышенные лимиты.

Администратор может переопределять entitlement-ы плана без redeploy. Изменения сохраняются в БД.

## Важно

Роль (`OWNER/ADMIN/USER`) и коммерческий тариф — разные сущности. Административные полномочия не должны сами по себе переписывать историю подписки пользователя.

Локальный inference учитывается отдельно от platform-funded remote AI. Remote token/cost budgets остаются частью Billing policy и проверяются backend-ом.

Точные цены и лимиты — конфигурация коммерческой редакции; их нельзя считать неизменяемой частью Core.


## Execution policy

Тариф и выбранная пользователем политика исполнения — разные сущности. Даже если remote AI доступен по тарифу, `local_only` запрещает его использование для данного пользователя. `remote_only` не даёт права обойти entitlement/quota: backend проверяет оба условия.
