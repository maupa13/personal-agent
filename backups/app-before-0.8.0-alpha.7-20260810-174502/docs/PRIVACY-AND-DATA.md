# Данные и приватность

Версия: 0.8.0-alpha.6

Локальная история чатов хранится server-side в локальной SQLite БД Personal Agent и привязана к `user_id`. Обычный USER не получает provider secrets/runtime internals.

Structured logs не должны содержать пароли, raw session tokens, API keys, Authorization headers или полное приватное содержимое файлов. Diagnostic snapshot не включает private workspace по умолчанию.

Remote-provider privacy/egress policy должна быть завершена до заявления о полном privacy routing в 1.0.


## Share Chat

Публичная ссылка создаётся только явным действием пользователя как отдельный read-only snapshot с ограниченным TTL. В БД хранится хэш share-token, а не raw token. Snapshot не предоставляет доступ к аккаунту, workspace, последующим сообщениям или другим диалогам и помечается `noindex`.

## Local / Remote execution

Политика `local_only` является backend-ограничением: при ней запрос не должен молча уходить в remote AI. `remote_only` требует соответствующего entitlement и настроенного remote provider. Для VPS API-ключи внешних провайдеров остаются server-side.
