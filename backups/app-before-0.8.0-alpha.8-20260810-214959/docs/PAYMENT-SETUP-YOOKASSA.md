# Подключение ЮKassa — Admin runbook

> Этот runbook описывает продуктовый flow. Юридические/налоговые настройки подтверждаются владельцем бизнеса и бухгалтером/юристом до public sales.

## 1. Создать магазин

Создайте магазин или тестовый магазин в личном кабинете ЮKassa.

Для первого интеграционного прохода рекомендуется тестовый магазин: Personal Agent не должен считать live billing проверенным только потому, что поля конфигурации заполнены.

## 2. Получить API credentials

Нужны:

- Shop ID;
- Secret Key.

В Personal Agent откройте:

`Администрирование → Подписки и Usage → ЮKassa`.

Введите Shop ID и Secret Key. Secret хранится отдельно и никогда не возвращается из Admin API после сохранения.

## 3. Указать публичный HTTPS URL

Пример:

`https://agent.example.ru`

HTTP разрешён только в автоматических тестах. Server/SaaS profile требует HTTPS.

После сохранения Admin покажет полный webhook URL:

`https://agent.example.ru/api/billing/webhook/yookassa`

## 4. Настроить HTTP-уведомления в ЮKassa

Укажите webhook URL в кабинете ЮKassa.

Personal Agent не доверяет телу webhook как единственному доказательству оплаты: после уведомления backend повторно запрашивает объект платежа у ЮKassa и сверяет payment id, metadata, amount, currency и status.

## 5. Checkout

USER выбирает платный тариф. Backend создаёт payment с уникальным Idempotence-Key, сохраняет внутренний payment id и возвращает confirmation URL.

После подтверждения пользователь возвращается в Account UI. Статус подписки меняется только после server-side verification.

## 6. Автопродление

Первый checkout запрашивает сохранение payment method. После успешного платежа backend сохраняет только provider `payment_method_id`, если provider подтвердил `saved=true`.

Повторное списание использует сохранённый `payment_method_id`; данные банковской карты Personal Agent не хранит.

## 7. Фискализация

Перед public sales выберите и настройте подходящий вашему юрлицу сценарий чеков/онлайн-кассы. Personal Agent не должен угадывать НДС или режим фискализации.

Live gate обязан проверить не только payment succeeded, но и требуемый бизнесом сценарий чеков/возврата.

## 8. Readiness checklist

Admin показывает:

- Shop ID — configured;
- Secret Key — stored;
- HTTPS — valid;
- Webhook — реально получен;
- Payment — реально подтверждён после re-fetch.

Только после этого `production_ready=true`.

## BILL-LIVE-001

На реальном VPS/HTTPS и тестовом или live merchant account проверить:

1. create checkout;
2. redirect/confirmation;
3. webhook;
4. server-side re-fetch;
5. amount/currency/metadata verification;
6. idempotent duplicate webhook;
7. entitlement activation;
8. saved payment method when recurring is enabled;
9. cancellation/renewal behavior;
10. required fiscal/receipt flow.

Без этих evidence платежный контур остаётся `BLOCKED_ENVIRONMENT`, а не PASS.
