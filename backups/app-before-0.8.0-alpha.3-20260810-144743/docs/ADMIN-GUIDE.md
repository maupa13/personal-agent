# Руководство администратора — Personal Agent Rus

**Версия продукта:** 0.8.0-alpha.3  
**Редакция:** Rus  
**Статус:** Productization Foundation

## 1. Для кого предназначена Admin Console

Admin Console — отдельная поверхность для владельца локального экземпляра и администраторов. Обычный пользователь не должен видеть провайдеры, model IDs, Docker/runtime internals, deployment controls или секреты.

Роли:

- `OWNER` — владелец экземпляра, полный административный доступ;
- `ADMIN` — административный доступ;
- `USER` — только пользовательский продукт.

В `accounts` mode `OWNER`/`ADMIN` открывают Admin Console своей обычной сессией. В `personal` mode используется аварийный break-glass token из конфигурации: это не делает административный API общедоступным при включении LAN.

## 2. Первый вход администратора

После первого входа в Admin Console доступно отдельное пошаговое обучение. Его можно запустить повторно кнопкой **«Обучение администратора»**.

Tour объясняет назначение Dashboard, пользователей, тарифов/usage, провайдеров и маршрутизации, мониторинга, логов, диагностики и deployment controls. Технические значения рассматриваются как детали администрирования, а не пользовательского интерфейса.

## 3. Дашборд

Dashboard показывает текущую версию продукта и сводку основных сущностей. Для оперативной диагностики используются разделы **Мониторинг**, **Логи и аудит** и **Диагностика**.

Если компонент недоступен, это не должно превращаться в white screen: состояние отображается отдельно, а подробности ищутся в diagnostics/logs.

## 4. Пользователи и регистрация

Режим аутентификации задаётся конфигурацией:

- `personal` — доверенный локальный профиль;
- `accounts` — полноценные пользовательские учётные записи.

Политика регистрации:

- `open` — регистрация разрешена;
- `approval_required` — новый пользователь ожидает одобрения;
- `closed` — самостоятельная регистрация запрещена.

Первый активный пользователь нового `accounts`-экземпляра получает роль `OWNER`. При обновлении старой базы без OWNER миграция назначает OWNER старейшему активному пользователю и пишет audit event.

USER не имеет доступа к административным API. Скрытие пункта меню — только UX; реальная граница проверяется backend-ролью.

## 5. Провайдеры

Раздел **Провайдеры** управляет подключениями AI. Локальный provider обнаруживается автоматически; дополнительные OpenAI-compatible/Ollama endpoints добавляются через Admin Console.

Для каждого подключения администратор задаёт:

- понятное название;
- тип;
- base URL;
- API key, если нужен;
- класс биллинга;
- ориентировочную стоимость input/output.

Секрет после сохранения не возвращается в UI и не должен попадать в structured logs/diagnostics.

## 6. Модели

Раздел **Модели** показывает inventory доступных моделей по подключённым providers. Пользовательские экраны model IDs не показывают.

Для локального управляемого provider можно инициировать загрузку модели. Установка считается работоспособной только после provider discovery/health и реального inference acceptance соответствующего release gate.

## 7. Маршрутизация

Раздел **Маршрутизация** связывает пользовательские режимы с provider/model pair. Пользователь выбирает `Авто`, `Быстро`, `Умно` и другие разрешённые продуктом режимы, а технический выбор выполняется внутри Core.

Изменение routing должно сохраняться и переживать restart. При будущей реализации Entitlement Engine доступность режимов будет дополнительно определяться эффективными правами тарифа.

## 8. Подписки, Usage и платежи

В текущем alpha foundation уже есть plan/billing foundation, учёт remote usage и адаптер ЮKassa. Локальный inference учитывается отдельно от platform-funded remote quota.

Администратор может просматривать планы/usage и настраивать платёжное подключение. Production billing lifecycle (полная reconciliation/refund/grace-period модель) не следует считать завершённым только по наличию этой панели — соответствующие release gates должны быть PASS.

## 9. Сайты и поиск

Раздел **Сайты и поиск** отделяет техническую стратегию от понятных пользовательских предпочтений. Пользователь выбирает область поиска/регион/разрешённые сайты, а администратор управляет известными `site profiles`.

Для профиля доступны domain pattern, category, acquisition order и egress policy metadata. В alpha.3 domain profile реально участвует в scoped search, а порядок `browser/static` применяется при чтении известного домена. `egress_region` пока не означает готовый multi-region worker routing и не должен рекламироваться как такой до отдельного live VPS gate.

## 10. Deployment / VPS

Deployment Manager хранит target configuration и поддерживает staged deployment foundation. SSH credentials используются только на время операции и не должны сохраняться как обычные настройки.

Перед публикацией серверного экземпляра обязательны HTTPS, accounts mode, secure cookies, rate limiting, backup и server acceptance. Внутренние Ollama/DB/browser/runtime endpoints напрямую в интернет не публикуются.

## 11. Мониторинг

Раздел **Мониторинг** показывает встроенный observability snapshot: runtime/DB/tasks/artifacts/usage и доступные системные метрики.

В production-grade версии Dashboard должен дополнительно давать p50/p95 latency, error rate, queue depth, provider cost, GPU/VRAM и alerts. Такие метрики считаются готовыми только после соответствующего acceptance, а не по наличию placeholder UI.

## 12. Structured logs и audit

Core пишет persistent JSONL events. Типичные поля:

- timestamp / level / service / version;
- event;
- request/correlation identifiers, когда они доступны;
- user/conversation/task context;
- duration/status/error type.

Секретные поля редактируются как `[REDACTED]`. Пароли, raw session tokens, API keys и Authorization headers не должны попадать в обычные логи.

Default LOCAL rotation: около 20 MB × 10 файлов для application/runtime log. Audit хранится отдельно в БД.

В `0.8.0-alpha.3` Core создаёт/принимает `X-Request-ID` и `X-Correlation-ID`, возвращает их клиенту и передаёт во внутренние Web/Browser/Ollama/Code-worker вызовы. Идентификаторы не добавляются к произвольным внешним web-страницам.

## 13. Диагностика

Раздел **Диагностика** получает безопасный snapshot:

- product/version/edition/runtime profile;
- auth mode и registration policy;
- DB path/size;
- log directory;
- последние безопасные events;
- публичный system snapshot.

Private workspace и секреты по умолчанию не включаются. Кнопка **«Скачать диагностику»** формирует ZIP с `diagnostics.json`, схемой БД без данных, безопасными последними events и README. Это предназначено для передачи в поддержку/debug без копирования private workspace.

## 14. LAN

Локальный runtime архитектурно поддерживает LAN lifecycle. Перед реальной эксплуатацией нескольких пользователей рекомендуется `accounts` mode и `approval_required` registration policy.

Admin должен помнить, что обычный HTTP LAN origin подходит не для всех browser APIs. Microphone/camera и другие Secure Context capabilities нельзя объявлять полностью работающими до отдельной HTTPS/secure-origin стратегии и реального mobile-device gate.

Полный second-device journey остаётся environment gate и должен проверяться на реальном устройстве.

## 15. Backup / restore / update

Пользовательские данные нельзя хранить в release extraction directory. Persistent state находится в canonical runtime storage/volumes.

Update flow должен следовать контракту:

`backup → apply/migrate → recreate → health → acceptance → commit`.

При несовместимой DB migration rollback должен восстанавливать и совместимый DB snapshot, а не только старый container image.

Никогда не использовать для обычного lifecycle:

- `docker compose down -v`;
- `docker volume prune`;
- `docker system prune`.

## 16. История диалогов и проекты

С `0.8.0-alpha.3` canonical chat truth находится server-side в SQLite, а не в browser localStorage. Доступ к диалогам/папкам проверяется по `user_id`.

Администратор не должен использовать это как повод читать private user conversations: административный доступ к private content не является обычной функцией продукта.

## 17. Безопасность

Минимальные invariants:

- USER получает 403 на Admin API;
- secrets не возвращаются UI;
- external content не получает tool authority;
- Web SSRF policy блокирует внутренние адреса;
- Code sandbox не получает Docker socket, provider secrets и unrestricted host filesystem;
- CSP не ослабляется ради E2E;
- user-owned artifacts/conversations изолированы.

## 18. Проверка после изменений

После изменения provider/routing/auth/runtime configuration администратор не должен ограничиваться визуальным сохранением формы. Нужен соответствующий VERIFY/acceptance gate и persistence после restart.

Для текущего local release основные команды находятся в canonical root и включают START/STOP/RESTART/STATUS/VERIFY/REPAIR/BACKUP и специализированные acceptance launchers.

## 19. Что ещё не является production-ready в alpha.3

Честные ограничения текущего milestone:

- PostgreSQL canonical runtime — отдельный `PG-RUNTIME-001` pre-beta slice;
- реальный second-device LAN evidence — внешний Windows/mobile gate;
- полный UI state matrix — незакрытый `UX-009`;
- multi-region `egress_region` routing — policy metadata до отдельного VPS live gate;
- production SaaS billing/VK/OAuth/ads — не следует считать готовыми только по foundation-коду.

Эти ограничения должны оставаться видимыми в release evidence до фактического PASS.

## 20. Логи, аудит и корреляция запросов

В разделе **Логи и аудит** доступны фильтры по уровню, событию, `request_id` и `correlation_id`. Это позволяет собрать цепочку одного пользовательского запроса через Core и внутренние workers без вывода секретов. Аудиторские события отображаются отдельно от application events.

Для обращения в поддержку или анализа нестабильного поведения используйте **Скачать диагностику**. Архив содержит версии, состояние runtime, sanitized-конфигурацию, схему БД и последние operational events. По умолчанию в него не входят workspace пользователя, пароли, session tokens и provider API keys.
