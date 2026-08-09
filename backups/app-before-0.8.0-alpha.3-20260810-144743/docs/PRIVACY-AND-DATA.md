# Данные и приватность

Версия: 0.8.0-alpha.3

Локальная история чатов хранится server-side в локальной SQLite БД Personal Agent и привязана к `user_id`. Обычный USER не получает provider secrets/runtime internals.

Structured logs не должны содержать пароли, raw session tokens, API keys, Authorization headers или полное приватное содержимое файлов. Diagnostic snapshot не включает private workspace по умолчанию.

Remote-provider privacy/egress policy должна быть завершена до заявления о полном privacy routing в 1.0.
