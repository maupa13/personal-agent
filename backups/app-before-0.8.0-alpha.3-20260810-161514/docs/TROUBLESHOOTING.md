# Troubleshooting — Personal Agent Rus 0.8.0-alpha.5

## UI не открывается

1. Запустите `STATUS.cmd`/`VERIFY.cmd`.
2. Проверьте persistent log в `logs`.
3. Не выполняйте `docker compose down -v`, `docker volume prune` или `docker system prune`.
4. Используйте штатный `RUN-FIRST.cmd`/repair flow.

## Code показывает DEGRADED

Обычный Chat/Web/Files должны продолжить работу. Для строгой проверки Code используйте `CODE-ACCEPTANCE.cmd` и сохраните diagnostics/logs.

## История старого браузерного UI

При первом открытии новая версия пытается импортировать старую localStorage-историю только если серверная история пользователя ещё пуста. После импорта серверная БД становится source of truth.

## Admin недоступен USER

Это ожидаемо. В accounts mode Admin Console доступен OWNER/ADMIN. В personal mode используется аварийный Admin token.
