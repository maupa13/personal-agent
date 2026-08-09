# Personal Agent Rus

## Master Spec, Release 1.0.0

Дата: 2026-08-18

Этот документ фиксирует текущие реальные возможности сервиса Personal Agent Rus, границы применения, административные функции, биллинг, наблюдаемость, деплой на VPS1, а также то, что пока не доведено до полноценного коммерческого релиза.

### Статус документа

- Canonical product spec для текущей ветки 1.0.0.
- Описывает фактическую реализацию, а не желаемую архитектуру.
- Если старые документы противоречат этому файлу, приоритет у этого файла.

### Release posture

- `1.0.0` трактуется как VPS-first релиз: базовая продуктивная цель - стабильная публикация и эксплуатация на VPS.
- Local models и локальный edge-путь остаются вторым этапом развития, а не условием для объявления `1.0.0`.
- Production VPS validation должна подтверждаться отдельным Linux/VPS gate; локальный Windows gate не подменяет эту проверку.
- Browser suites и live-browser checks считаются отдельными средовыми gates и не должны маскироваться как PASS при отсутствии нужной среды.
- Code worker должен иметь отдельную Linux/VPS verification path, даже если локальный Windows-контур уже зеленый.
- Форматы артефактов должны работать с наличием и отсутствием optional библиотек; graceful fallback обязателен, а не "best effort" только для одного окружения.

## 1. Что это за сервис

Personal Agent Rus - browser-first AI platform на русском рынке с прицелом на:

- личного AI-агента для пользователя;
- управление провайдерами и моделями;
- web/research извлечение данных;
- файловые и кодовые рабочие сценарии;
- биллинг, баланс, промокоды, темы;
- админский мониторинг и аудит;
- VPS-deploy и сетевую маршрутизацию;
- юридические страницы, privacy/cookie/disclaimer;
- SEO-обвязку и публикацию на домене;
- ориентацию на русскоязычные источники и российский веб.

Ключевая идея:

- обычный пользователь видит упрощенный продуктовый слой;
- super-admin видит технический слой, деньги, маршрутизацию, провайдеров, аудит и мониторинг;
- внутренние provider/model IDs, секреты и маршрутизация не должны быть видны обычному пользователю.

## 2. На что сервис способен

### 2.1 Пользовательские сценарии

Сервис умеет:

- вести чат и рабочие AI-сценарии;
- переключать режимы работы;
- использовать локальные и удаленные провайдеры;
- сохранять предпочтения пользователя;
- работать с темами интерфейса;
- использовать Web / Research / Files / Code как отдельные capability;
- извлекать данные из сайтов, если нет открытого API;
- учитывать категории источников, включая маркетплейсы и госреестры;
- формировать результаты в разных типах артефактов;
- запускать onboarding и help panel один раз, а не при каждом открытии страницы;
- позволять пользователю закрывать информационную панель вручную;
- поддерживать мобильную версию, PWA-ориентацию и UX для iPhone/Android;
- ориентироваться на особенности русского интернета и русскоязычных источников.

### 2.2 Web / Research

Сервис поддерживает:

- явный URL или поисковый intent;
- режимы поиска и извлечения;
- категории источников:
  - general web;
  - marketplaces;
  - registries;
  - site list;
- извлечение через открытые HTML-страницы;
- fallback на browser rendering, если HTML недостаточно;
- хранение source/evidence records;
- применение source policies и ограничений;
- учет parser metrics и сетевых событий;
- работу даже там, где нет открытого API, если извлечение технически возможно.

### 2.3 Файлы и артефакты

Сервис умеет:

- работать с файлами как с рабочей областью;
- читать и создавать артефакты;
- сохранять новые версии;
- распознавать типы результатов;
- формировать документы и выходные данные по выбранному формату;
- отделять пользовательские файлы от системных.

### 2.4 Код

Есть отдельная capability для code execution / sandboxed worker:

- запуск скриптов;
- stdout / stderr / exit code;
- compile / test / repair / retest workflow;
- изоляция от core;
- ограничение ресурсов.

## 3. Что не умеет полностью

Сервис пока не является полностью автономной production-системой без внешнего контроля.

Не закрыто полностью:

- автоматическая и безошибочная верификация всех ручных пополнений без внешнего подтверждения;
- нулевой fraud-risk для manual top-up;
- полностью автоматический provider-side reconciliation для YooMoney-style потоков;
- бесшовная ручная или автоматическая интеграция любого стороннего LLM-провайдера на VPS без админской настройки;
- автономное production-grade alerting/paging без ручной политики;
- полностью автоматический push VPN orchestration без выбора цели;
- гарантированное извлечение данных с любого сайта, если сайт сознательно защищается, блокирует ботов, требует сложный антибот, CAPTCHA или закрытый API.

## 4. Границы извлечения данных

### 4.1 Когда данные можно извлечь

Можно рассчитывать на извлечение, если:

- сайт отдаёт нормальный HTML;
- данные есть в статике или хорошо рендерятся браузером;
- доступен открытый API;
- нет жесткой блокировки;
- правила источника не запрещают такой сбор в конкретном сценарии;
- страницу можно корректно прочитать через browser fallback.

### 4.2 Когда надо считать ограничение честно

Нельзя изображать успешное извлечение, если:

- ресурс защищён и не пускает бота;
- данные доступны только после явной авторизации;
- API закрыт и HTML не содержит нужных данных;
- сайт требует сложный интерактив, который сервис не покрывает;
- извлечение нарушает доступную политику источника или юридические ограничения.

### 4.3 Что учитывать для русского интернета

Ориентация на российский веб означает:

- маркетплейсы;
- госреестры;
- корпоративные сайты;
- лендинги и каталоги;
- нестабильное качество HTML и верстки;
- темы, где данные есть только в рендере;
- очень разнородные форматы карточек, таблиц и списков.

## 5. UX-логика по категориям

Пользователь должен иметь возможность работать с источниками по категориям:

- маркетплейсы;
- государственные реестры;
- сайты из списка;
- обычный веб-поиск;
- разные типы выходных файлов и артефактов.

Система уже поддерживает:

- preset-подход для web search;
- отдельные категории результатов;
- отдельные presets для формата результатов.

## 6. Биллинг и деньги

### 6.1 Что есть

Сейчас реализованы:

- пользовательский баланс;
- события изменения баланса;
- промокоды;
- история активации промокодов;
- manual balance adjustments для super-admin;
- заявки на пополнение;
- theme purchases;
- аудит операций через `balance_events`;
- отдельный admin billing dashboard;
- payment requests / top-up requests;
- YooMoney fundraise как первый вариант для простых пользователей;
- manual reconciliation для заявок;
- второй этап approval для крупных сумм;
- уникальность `payment_reference` для снижения простых повторных клеймов.

### 6.2 Что видит super-admin

Super-admin видит:

- список пользователей с балансом;
- список промокодов;
- статус промокодов:
  - active;
  - disabled;
  - expired;
  - exhausted;
- число активаций;
- число уникальных пользователей;
- время последней активации;
- журнал активаций промокодов;
- заявки на пополнение;
- статус заявок;
- кто проверил заявку;
- кто зачислил средства;
- кто создал промокод;
- источник движения баланса;
- сводку платежей по пользователям;
- manual balance change audit.

### 6.3 Можно ли обмануть пополнение

Реально возможны риски, если:

- доверять скриншотам или ручным заявлениям без внешней сверки;
- не проверять уникальность reference;
- не хранить audit trail;
- не разводить manual adjustment и payment reconciliation;
- не ограничивать права super-admin по внутренним правилам.

Что снижает риск:

- server-side reconciliation;
- уникальный payment reference;
- audit trail в balance events;
- manual approval flow;
- second approval for large amounts;
- хранение actor / reason / reference / timestamp.

### 6.4 Может ли super-admin редактировать баланс

Да, может.

Это сделано осознанно, но требует:

- строгого audit trail;
- reason;
- actor;
- reference при необходимости;
- отдельной бизнес-политики;
- внутреннего контроля прав доступа.

### 6.5 Кто получает промокоды

Сценарии:

- пользователь вводит промокод сам;
- super-admin создаёт промокод и отправляет его на email;
- super-admin может выдать промокод точечно на конкретный email;
- в дальнейшем можно поддержать промокоды на старт, чтобы пользователь получил бесплатный рабочий вход и потом покупал дополнительные запросы.

## 7. Темы

Система поддерживает:

- бесплатные темы;
- paid themes;
- дополнительные цветовые темы;
- blue theme;
- light-green theme;
- user preference persistence.

Требования:

- темы должны работать и в light, и в dark окружении;
- нельзя допускать, чтобы панели оставались темными, а остальное белым без дизайнерского контроля;
- тему надо оценивать как продуктовую часть, а не только как CSS-override.

## 8. Cookies и персональные данные

Сервис учитывает cookies и связанные сценарии:

- авторизация;
- session/token;
- корзина без входа;
- locale/theme;
- experimentGroup;
- anonymous visitorId;
- CSRF-related cookie;
- персонализация.

Правило:

- cookies и обработка данных должны быть описаны в policy;
- privacy/legal pages должны быть отдельными;
- дисклеймер должен явно говорить, что сервис не даёт профессиональные консультации;
- пользовательское соглашение должно быть отдельной страницей;
- cookie policy должна быть отдельной страницей;
- consent / disclosure должен быть понятен для пользователя.

## 9. Обучение и onboarding

Информационная панель и обучающий блок:

- должны быть закрываемыми;
- не должны открываться каждый раз при новом заходе на страницу;
- должны сохранять состояние;
- должны быть повторно доступны пользователю, но не навязываться.

## 10. Мониторинг и дашборды

Полноценный мониторинг должен включать:

- бизнес-метрики;
- технические метрики;
- parser metrics;
- load / latency / error rate;
- remote provider status;
- billing metrics;
- promo usage;
- top-up request status;
- balance changes;
- deployment health;
- VPN status;
- audit logs.

По текущей реализации:

- мониторинг уже есть;
- наблюдаемость уже есть;
- admin UI показывает карточки и сводки;
- parser metrics и backend operational metrics уже интегрируются;
- полноценный production alerting еще требует доводки.

## 11. VPS и деплой

### 11.1 Роль VPS1

Этот сервис считается VPS1.

### 11.2 Что должно выноситься в env

Конфиги должны приходить через environment variables:

- runtime settings;
- billing settings;
- monitoring settings;
- SEO / verification settings;
- VPN routing settings;
- provider defaults;
- secret references;
- deployment URLs.

### 11.3 VPN routing

Поддерживается сценарий:

- VPS1 использует отдельный VPN-клиент;
- VPS2 выступает как выход/шлюз;
- маршрутизируется только нужный OpenAPI/IP;
- остальной трафик идёт напрямую;
- autostart VPN должен быть описан;
- admin должен видеть план маршрутизации.

### 11.4 Deploy checklist

Для публикации на VPS нужны:

- OS packages;
- Python environment;
- env variables;
- DB setup;
- reverse proxy;
- domain binding;
- robots.txt;
- sitemap.xml;
- verification tags/snippets;
- SSL/HTTPS;
- monitoring hooks;
- backup policy;
- release process.

## 12. SEO и публикация

Сервис должен поддерживать:

- `robots.txt`;
- `sitemap.xml`;
- canonical URLs;
- Yandex verification;
- Google verification;
- additional snippets / scripts;
- domain binding;
- public URL generation;
- indexability control.

## 13. Админский аудит и безопасность

Super-admin surface должна показывать:

- пользователей;
- их баланс;
- промокоды;
- активации промокодов;
- платежи;
- top-up requests;
- theme purchases;
- routing plan;
- monitoring;
- logs;
- provider inventory;
- user sessions;
- audit trail.

Безопасность в денежных сценариях должна учитывать:

- кто изменил баланс;
- почему изменил баланс;
- какой reference использован;
- когда было изменение;
- какой user получил изменение;
- как это видно в журнале;
- что не должно смешиваться manual/admin/promo/payment/top-up в одну неаудируемую массу.

## 14. Текущее состояние реализации

### Implemented

- user accounts and sessions;
- admin roles;
- billing balances;
- promo codes;
- promo redemption history;
- admin promo audit;
- manual balance adjustments;
- top-up requests;
- top-up reconciliation;
- two-step review for large top-ups;
- theme catalog, including paid themes;
- monitoring dashboards;
- provider/model administration;
- routing plans;
- mobile-aware UX;
- open/legal pages;
- SEO-related public page metadata support;
- onboarding persistence;
- parser metrics and observability.

### Partially implemented

- YooMoney remains a manual top-up flow, not a fully automatic provider-credit flow;
- third-party provider onboarding on VPS still requires configuration;
- alerting and paging are not yet fully production-complete;
- automated anti-fraud is not complete;
- some deployment steps still require manual server actions;
- automatic reimbursement / payment reconciliation remains incomplete.

### Not fully implemented

- fully automated fraud-proof payment reconciliation;
- universal provider auto-configuration;
- autonomous VPN target discovery and orchestration;
- complete production secret manager flow;
- fully deterministic extraction from every external site.

## 15. Release readiness assessment

### Good enough for

- internal alpha / beta;
- controlled production pilots;
- user testing;
- admin-controlled billing experiments;
- manual top-up workflows with audit;
- local-first / hybrid deployments.

### Not yet ideal for

- unattended commercial billing at high scale;
- fully automatic finance reconciliation without human review;
- high-trust payment automation without additional fraud controls;
- completely hands-off deployment of arbitrary providers.

## 16. Recommended next hardening steps

1. Harden manual top-up anti-fraud.
2. Add stronger provider-side reconciliation for payments.
3. Add dedicated audit views for balance events.
4. Add more explicit billing policy rules for super-admin actions.
5. Finish deploy docs for VPS1 from scratch.
6. Keep env-driven configuration for all runtime-sensitive settings.
7. Finalize release notes and changelog for 1.0.0.

## 17. Summary

Personal Agent Rus already functions as a real AI platform with:

- user accounts;
- billing;
- promo codes;
- balance audit;
- admin control;
- web extraction;
- provider management;
- monitoring;
- deploy surfaces;
- legal/SEO/public pages;
- theme monetization.

The main remaining gap for a fully commercial release is not the UI itself, but the trust layer around money, reconciliation, and automation under hostile or noisy real-world conditions.
