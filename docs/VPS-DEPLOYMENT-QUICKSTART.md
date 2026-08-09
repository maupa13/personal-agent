# VPS deployment quickstart: VPS1 + VPS2 Amnezia AWG

Документ описывает ручную установку Personal Agent Rus на VPS1 через PuTTY.

Текущая схема:

- VPS1 - сервер приложения RusPersonalAgent.
- VPS2 - уже установленный Amnezia AWG/WireGuard VPN-hop.
- Локальный файл `not-commit/amnezia_config.vpn` - клиентский Amnezia-профиль для VPS1.
- Маршрутизировать нужно только выбранный upstream API, например DeepSeek/OpenAPI. Весь остальной трафик VPS1 должен оставаться прямым.

Важно: `amnezia_config.vpn` содержит VPN-секреты. Не коммитьте его, не вставляйте содержимое в чат, issue, логи или скриншоты.

## 1. Что подготовить

Нужны:

- IP или домен VPS1.
- SSH логин VPS1, обычно `root`.
- SSH порт, обычно `22`.
- Пароль или `.ppk` ключ для PuTTY.
- Домен сервиса, например `agent.example.ru`.
- IP или домен VPS2.
- Файл `C:\AI\RusPersonalAgent\not-commit\amnezia_config.vpn`.
- IP upstream API, который надо вести через VPN, например IP `api.deepseek.com`.

## 2. Подключение через PuTTY

1. Откройте PuTTY.
2. В `Host Name` введите IP VPS1.
3. В `Port` оставьте `22`, если провайдер не дал другой порт.
4. В `Connection type` выберите `SSH`.
5. Если вход по ключу: `Connection -> SSH -> Auth -> Credentials`, выберите `.ppk`.
6. Нажмите `Open`.
7. При первом входе PuTTY покажет fingerprint. Сверьте его с панелью VPS-провайдера.
8. Введите логин и пароль, если используется парольный вход.

## 3. Установка ПО на VPS1

Команды ниже рассчитаны на Ubuntu/Debian и root-пользователя.

```sh
apt-get update
apt-get install -y ca-certificates curl git openssl docker.io docker-compose-plugin postgresql-client
systemctl enable --now docker
docker --version
docker compose version
```

Если `docker compose version` не работает:

```sh
apt-get install -y docker-compose-v2 || apt-get install -y docker-compose
docker compose version
```

## 4. Загрузка проекта на VPS1

Вариант через Git:

```sh
mkdir -p /opt
cd /opt
git clone <URL_ВАШЕГО_REPO> personal-agent
cd /opt/personal-agent
```

Если Git-репозитория на VPS нет, загрузите архив через WinSCP/PSCP в `/opt/personal-agent` и распакуйте его там.

## 5. Копирование `amnezia_config.vpn` на VPS1

Через WinSCP:

1. Подключитесь к VPS1 тем же логином, что в PuTTY.
2. Создайте папку `/opt/personal-agent/secure`.
3. Перетащите файл `C:\AI\RusPersonalAgent\not-commit\amnezia_config.vpn` в `/opt/personal-agent/secure/amnezia_config.vpn`.

Через командную строку Windows с `pscp.exe`:

```bat
pscp C:\AI\RusPersonalAgent\not-commit\amnezia_config.vpn root@VPS1_IP:/opt/personal-agent/secure/amnezia_config.vpn
```

На VPS1 выставьте права:

```sh
mkdir -p /opt/personal-agent/secure
chmod 700 /opt/personal-agent/secure
chmod 600 /opt/personal-agent/secure/amnezia_config.vpn
```

## 6. Создание env через cat

На VPS1 выполните:

```sh
cd /opt/personal-agent

ADMIN_TOKEN="$(openssl rand -hex 32)"
SEARXNG_SECRET="$(openssl rand -hex 32)"
POSTGRES_PASSWORD="$(openssl rand -hex 32)"

cat > parent.env <<EOF
PA_VERSION=0.8.0-alpha.8
PA_RUNTIME_PROFILE=server
PA_AUTH_MODE=accounts
# Users can register, but new non-owner accounts wait for admin approval.
# Passwords are stored only as password_hash values, never as plain text.
PA_SECURE_COOKIES=1
PA_REGISTRATION_POLICY=approval_required

PA_BIND_IP=127.0.0.1
PA_UI_PORT=3100
PA_PUBLIC_URL=https://agent.example.ru

PA_ADMIN_TOKEN=$ADMIN_TOKEN
PA_SEARXNG_SECRET=$SEARXNG_SECRET

PA_POSTGRES_DB=personal_agent
PA_POSTGRES_USER=personal_agent
PA_POSTGRES_PASSWORD=$POSTGRES_PASSWORD
PA_DATABASE_URL=postgresql://personal_agent:$POSTGRES_PASSWORD@postgres:5432/personal_agent

# Optional OpenAI bootstrap provider.
# Long-term production recommendation: add provider in /admin instead of keeping key in env.
OPENAI_API_KEY=
PA_OPENAI_PROVIDER_ID=openai
PA_OPENAI_PROVIDER_NAME=OpenAI
PA_OPENAI_PROVIDER_TYPE=openai_responses
PA_OPENAI_BASE_URL=https://api.openai.com/v1

PA_BOOTSTRAP_MODEL=qwen3:0.6b
PA_OLLAMA_IMAGE=ollama/ollama:0.32.6
PA_CORE_IMAGE=personal-agent-core:0.8.0-alpha.8
PA_BROWSER_IMAGE=personal-agent-browser:0.8.0-alpha.8
PA_SEARXNG_IMAGE=searxng/searxng:2026.8.5-1689cb1b5
PA_CODE_WORKER_IMAGE=personal-agent-code-worker:0.8.0-alpha.8

PA_VPN_ROUTING_ENABLED=1
PA_VPN_ROUTING_MODE=amneziawg
PA_VPN_PREFERENCE_ID=vps1-to-vps2-awg
PA_VPN_VPS2_HOST=
PA_VPN_UPSTREAM_HOST=api.deepseek.com
PA_VPN_UPSTREAM_IP=203.0.113.50
PA_VPN_ALLOWED_IPS=203.0.113.50/32
PA_VPN_PROFILE_FILE=/opt/personal-agent/secure/amnezia_config.vpn
EOF

chmod 600 parent.env
cp parent.env .env
```

Замените:

- `agent.example.ru` на домен VPS1.
- `PA_VPN_VPS2_HOST` можно оставить пустым: реальный endpoint VPS2 уже находится внутри `amnezia_config.vpn`.
- `api.deepseek.com` на нужный API host, если маршрут не для DeepSeek.
- `203.0.113.50` на реальный IP этого API.

Не переносите сюда Spring-переменные:

- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` не используйте в этом Python-сервисе. Нужны `PA_POSTGRES_DB`, `PA_POSTGRES_USER`, `PA_POSTGRES_PASSWORD` и `PA_DATABASE_URL`.
- `DB_URL=jdbc:...`, `DB_USERNAME`, `DB_PASSWORD`, `SPRING_PROFILES_ACTIVE` этим Python-сервисом не читаются.
- `ADMIN_TOKEN` должен называться `PA_ADMIN_TOKEN`.
- `OPENAI_API_KEY` теперь можно указать для bootstrap: при старте создается provider `openai`, а ключ копируется в server-side secret storage. Для постоянной эксплуатации безопаснее добавить/обновить provider через `/admin`, чтобы не держать ключ в env.

`PA_DATABASE_URL` для VPS должен быть заполнен. Именно он переключает live runtime на PostgreSQL. Пустое значение оставляет локальный SQLite-режим и для VPS больше не рекомендуется.

Посмотреть env без раскрытия токенов:

```sh
grep -v 'TOKEN\|SECRET' .env
```

## 7. Как работает регистрация

Для публичного VPS оставляйте:

```env
PA_AUTH_MODE=accounts
PA_REGISTRATION_POLICY=approval_required
```

Это значит:

- страница `/register` открыта;
- пользователь может создать аккаунт;
- запись сохраняется в PostgreSQL в таблицу `users`;
- пароль сохраняется только как `password_hash`;
- обычный новый пользователь получает статус `pending`;
- пользователь со статусом `pending` не получает рабочую сессию и не может пользоваться сервисом;
- админ потом одобряет его в `/admin`, после чего статус становится `active`.

Не ставьте `PA_REGISTRATION_POLICY=open` на публичном VPS, если не хотите автоматический доступ всем зарегистрировавшимся.

## 8. Импорт Amnezia AWG на VPS1

Env только сообщает сервису, какой VPN-профиль и маршрут используются. Сам VPN-интерфейс поднимается не Docker Compose, а Amnezia/AWG на VPS1.

Действия:

1. Установите AmneziaWG/WireGuard client tooling на VPS1, если его еще нет.
2. Импортируйте файл `/opt/personal-agent/secure/amnezia_config.vpn`.
3. Включите автозапуск импортированного профиля.
4. Проверьте, что маршрут к `PA_VPN_ALLOWED_IPS` идет через AWG/WireGuard интерфейс.

Проверка после импорта:

```sh
ip addr
ip route get 203.0.113.50
curl -4 https://api.deepseek.com/ -I
```

Если `ip route get 203.0.113.50` не идет через AWG/WireGuard интерфейс, значит `.vpn` еще не импортирован или маршрут не применен. Наличие `PA_VPN_PROFILE_FILE` в env само по себе VPN не включает.

## 9. Запуск приложения

```sh
cd /opt/personal-agent
docker compose --env-file .env -f compose.release.yaml up -d
docker compose --env-file .env -f compose.release.yaml ps
```

Если образы не опубликованы в registry и запуск пишет, что image не найден, используйте сборку из исходников:

```sh
docker compose --env-file .env -f compose.yaml up -d --build
```

Проверка локально на VPS1:

```sh
curl http://127.0.0.1:3100/api/health
```

Проверка PostgreSQL на VPS1:

```sh
docker compose --env-file .env -f compose.release.yaml exec postgres psql -U personal_agent -d personal_agent -c "\dt"
docker compose --env-file .env -f compose.release.yaml exec postgres psql -U personal_agent -d personal_agent -c "select id,email,role,status,created_at from users order by created_at desc limit 20;"
```

## 10. HTTPS через Caddy

Если домен VPS1 уже направлен A-записью на IP VPS1:

```sh
apt-get install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' > /etc/apt/sources.list.d/caddy-stable.list
apt-get update
apt-get install -y caddy
```

Создайте Caddyfile:

```sh
cat > /etc/caddy/Caddyfile <<'EOF'
agent.example.ru {
    encode zstd gzip
    reverse_proxy 127.0.0.1:3100
}
EOF

systemctl reload caddy
```

Замените `agent.example.ru` на свой домен.

Проверка:

```sh
curl -I https://agent.example.ru/
curl https://agent.example.ru/api/system
```

## 11. Firewall

Минимально:

```sh
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
ufw status
```

Порт `3100` наружу обычно не открывается, потому что Caddy проксирует HTTPS на `127.0.0.1:3100`.

## 12. Seed SQL из not-commit

Файлы `not-commit/vps/*.sql` - только синтетические тестовые данные. Не применяйте их к настоящему production без понимания последствий.

Если нужно заполнить свежую тестовую PostgreSQL DB:

```sh
docker compose --env-file .env -f compose.release.yaml up -d postgres core
docker compose --env-file .env -f compose.release.yaml exec -T postgres psql -U personal_agent -d personal_agent < not-commit/vps/bootstrap.sql
```

Тестовые логины из seed:

- `owner@example.com` / `Owner12345!`
- `admin@example.com` / `Admin12345!`
- `user@example.com` / `User12345!`

## 13. Диагностика

Статус:

```sh
docker compose --env-file .env -f compose.yaml ps
```

Логи:

```sh
docker compose --env-file .env -f compose.yaml logs --tail 200 -f
```

Перезапуск:

```sh
docker compose --env-file .env -f compose.yaml restart
```

Админ-токен:

```sh
grep '^PA_ADMIN_TOKEN=' .env
```

## 14. Что нельзя делать

- Не хранить `amnezia_config.vpn` в Git.
- Не печатать содержимое `amnezia_config.vpn` в терминал командой `cat`.
- Не писать реальные токены в `bootstrap.env.example`.
- Не открывать `3100/tcp` наружу без причины.
- Не запускать production с `PA_ADMIN_TOKEN=seed-admin-token-2026`.
- Не применять `docker compose down -v`, если не хотите удалить данные.
