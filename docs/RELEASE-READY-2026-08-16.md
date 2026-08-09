# Release 1.0.0 Package: Personal Agent Rus

Дата: 2026-08-16
Версия релиза: 1.0.0

Этот документ сводит в один файл текущее состояние сервиса: что реализовано, как это работает для пользователя и супер-админа, что еще не автоматизировано, какие настройки нужны для релиза и какие риски нужно учитывать перед публикацией.

## 1. Что это за сервис

Personal Agent Rus — локально ориентированный AI-сервис с:
- пользовательским чатом;
- файлами и кодом;
- web/research-потоком;
- пользовательскими сессиями и cookie-aware поведением;
- биллингом, балансами и промокодами;
- темами интерфейса;
- админ-панелью;
- мониторингом;
- деплоем на VPS;
- VPN-маршрутизацией для отдельных upstream API.

Сервис рассчитан на сценарий, где один VPS выполняет роль основной платформы, а внешние модели и сетевой egress могут подключаться выборочно и управляться отдельно.

## 2. Что уже работает

### 2.1 Пользовательский слой

- Регистрация и вход.
- Сессии через cookies.
- Remember-me и пользовательские предпочтения.
- Личный кабинет.
- Баланс и промокоды.
- YooMoney как manual top-up entry point.
- Платные и бесплатные темы.
- Просмотр активных сессий и завершение чужих сессий.
- Юридические страницы: terms, privacy, cookies, disclaimer.
- Онбординг/инфопанель, которая может закрываться и не обязана открываться при каждом входе.

### 2.2 AI и product capabilities

- Чат с локальными и удаленными провайдерами.
- Управление моделями и provider registry через админку.
- Режимы web/research.
- Файлы и артефакты.
- Код как отдельная capability.
- Режимы исполнения с учетом policy.

### 2.3 Биллинг и монетизация

- Пользовательский баланс.
- События изменения баланса.
- Промокоды.
- Промокоды на email при наличии SMTP.
- Стартовые промокоды для входа в продукт без оплаты.
- Ручные top-up запросы.
- YooMoney widget как первый ручной сценарий пополнения.
- YooKassa для server-side verified flows.
- Платные темы, включая голубую и светло-зеленую.

### 2.4 Админ и супер-админ

- Полная админ-панель.
- Управление пользователями и ролями.
- Ручное изменение баланса.
- Создание и выдача промокодов.
- Self top-up для супер-админа через тот же privileged контур.
- Просмотр top-up запросов и истории платежей.
- Верификация и reconciliation top-up запросов с audit trail.
- Мониторинг, логи, диагностика, observability.
- Настройка deployment target.
- Настройка VPN routing.
- Настройка provider/model routing.
- Настройка поиска, сайтов и source policy.

### 2.5 Мониторинг

- Runtime health snapshot.
- Бизнес-метрики.
- Parser metrics:
  - `parser_requests_total{host,status}`
  - `parser_429_total{host}`
  - `parser_retry_total{host}`
  - `parser_backoff_seconds{host}`
  - `parser_active_requests{host}`
  - `parser_effective_rps{host}`
- Дашборды и карточки в админке для оперативной диагностики.

### 2.6 Деплой и VPS

- Deployment targets.
- SSH bootstrap / preflight / deploy / rollback.
- Env-driven bundle defaults.
- SEO metadata, robots, sitemap и verification snippets для публичных страниц.
- VPN routing plan:
  - VPS1 как рабочая точка;
  - VPS2 как VPN hop;
  - AllowedIPs для конкретных upstream IP;
  - `preferenceId` как операторская привязка маршрута.

## 3. Что пользователь видит

- Единый интерфейс для чата, файлов, кода и поиска.
- Баланс и промокоды в личном кабинете.
- Понятные legal pages.
- Встроенную поддержку тем, включая дополнительные платные темы.
- Онбординг и инфопанель, которые не должны мешать повторной работе.
- Прозрачные правила доступа к бесплатным и платным возможностям.

## 4. Что видит супер-админ

- Все пользователи и их статусы.
- Балансы и корректировки.
- Промокоды и стартовые промо.
- Баланс-пополнения через ручную проверку.
- Историю изменений и audit trail.
- Provider registry.
- Routing settings.
- Deployment targets.
- Monitoring.
- Logs and diagnostics.
- VPN plan generation and application.

## 5. Что намеренно не автоматизировано полностью

Это важно для релиза и для честного позиционирования продукта.

- YooMoney manual top-up не превращен в полностью автоматический provider-side reconciliation без внешнего источника подтверждения.
- Скриншоты и пользовательские claims сами по себе не считаются надежным доказательством оплаты.
- Подключение новых внешних моделей на чистом VPS все еще требует admin-managed setup.
- Полноценный production alerting stack еще не доведен до enterprise-уровня.
- VPN automation пока требует явного выбора и применения target path.

## 6. Безопасность и антифрод

Сервис уже учитывает:
- HttpOnly cookies;
- CSRF protection;
- audit trail;
- reason fields for balance changes;
- uniqueness of payment references;
- controlled top-up flow;
- privilege separation between user, admin, super-admin.

Нужно помнить:
- Любая ручная корректировка баланса — это privileged action.
- Любой payment-like flow без provider verification уязвим к злоупотреблениям.
- Любые user-facing bonus balances лучше выдавать промокодом, а не произвольным ручным credit.
- Действия админа должны оставлять понятный след: кто, когда, почему, по какому основанию.

## 7. Cookie, privacy, disclaimer

Отдельно фиксируется, что сервис работает с:
- auth/session cookies;
- cart-like state;
- locale/theme;
- experiment groups;
- anonymous visitor IDs;
- CSRF-related cookies;
- personalization.

Для релиза нужны:
- понятная privacy policy;
- cookie policy;
- disclaimer;
- user agreement;
- явное описание того, что собирается и зачем.

## 8. SEO и публичная публикация

Поддерживаются:
- canonical public URL;
- robots.txt;
- sitemap.xml;
- verification tags/snippets для поисковиков;
- подключение аналитики и веб-мастеров через env.

Для публичного деплоя нужно:
- задать домен;
- прописать `PA_PUBLIC_URL`;
- добавить verification env при необходимости;
- проверить, что страницы отдаются под одним canonical host;
- обновить robots и мета-теги при публикации.

## 9. Env и конфигурация

Для релиза важно держать настройки в env, а не в коде.

Ключевые группы:
- public/SEO:
  - `PA_PUBLIC_URL`
  - `PA_SITE_TITLE`
  - `PA_SITE_DESCRIPTION`
  - `PA_SITE_KEYWORDS`
  - `PA_GOOGLE_SITE_VERIFICATION`
  - `PA_YANDEX_VERIFICATION`
  - `PA_HEAD_SNIPPETS`
  - `PA_BODY_SNIPPETS`
  - `PA_CSP_EXTRA`
- billing:
  - payment provider credentials
  - top-up / promo settings
- VPN:
  - `preferenceId`
  - AllowedIPs
  - NAT interface
  - routing mode
- monitoring:
  - alerting thresholds
  - external sinks if used

## 10. Что еще нужно до коммерческого релиза

- Полный provider-side reconciliation для manual top-ups.
- Более сильный anti-fraud для balance changes.
- Production alert routing and paging.
- Более автономная provider onboarding story.
- Полный secret rotation / credential management flow.

## 11. Итоговая оценка готовности

Готово к использованию:
- пользовательская часть;
- админка;
- баланс и промокоды;
- темы;
- monitoring;
- VPS deploy basics;
- SEO/public pages;
- cookie/legal surfaces.

Требует дополнительной доводки:
- платежные reconciliation сценарии;
- антифрод;
- production observability/alerting;
- автономность VPN/provider onboarding.

## 12. Практический next step

Если нужна публикация на VPS, использовать:
- [VPS-DEPLOYMENT-QUICKSTART.md](/C:/AI/RusPersonalAgent/docs/VPS-DEPLOYMENT-QUICKSTART.md)

Если нужен полный функциональный разбор системы:
- [MASTER-SPEC-PERSONAL-AGENT-RUS-2026-08-16.md](/C:/AI/RusPersonalAgent/docs/MASTER-SPEC-PERSONAL-AGENT-RUS-2026-08-16.md)

Если нужен короткий статус по реализации:
- [IMPLEMENTATION-STATUS-2026-08-16.md](/C:/AI/RusPersonalAgent/docs/IMPLEMENTATION-STATUS-2026-08-16.md)
