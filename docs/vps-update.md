# VPS Update: current server-lite install flow

Этот документ заменяет старую инструкцию, которая ссылалась на несуществующий `compose.vps.yaml`, старые версии образов и локальный Ollama на слабом VPS.

Сейчас канонический VPS-поток такой:

- профиль `server-lite` для слабого VPS;
- `PA_RUNTIME_PROFILE=server`;
- `PA_AUTH_MODE=accounts`;
- `PA_SECURE_COOKIES=1`;
- без локального Ollama/GPU worker stack;
- публикация через generated bundle `docker-compose-main.yaml` + `.env.server` + `Caddyfile`;
- переключение релиза через `current` / `previous`.

## Что больше не использовать

- `compose.vps.yaml` из старой схемы;
- `compose.release.yaml` как VPS-профиль для слабого сервера;
- старые теги и пути вида `0.8.0-alpha.8`, если репозиторий уже собран с более новой версией;
- локальный Ollama как обязательную зависимость для VPS;
- старые пути VPN вроде `/etc/rodnoi-agent/vpn/amnezia_config.vpn`;
- Spring-style переменные `POSTGRES_*` / `DB_*` для этого runtime.

## Какой артефакт считается VPS-бандлом

Серверный deploy сейчас создаёт bundle, внутри которого лежат:

- `docker-compose-main.yaml`
- `.env.server`
- `Caddyfile`
- `core/`

Этот bundle разворачивается на VPS и запускается командой:

```sh
docker compose --env-file .env.server -f docker-compose-main.yaml up -d --build
```

## Базовые требования к VPS

- Debian/Ubuntu-family ОС;
- root SSH или пользователь с `sudo`;
- открытые порты `80` и `443`;
- установленный Docker и `docker compose`;
- домен, который указывает на VPS;
- trusted SSH host key fingerprint.

## Подготовка VPS

Если Docker ещё не установлен, ставьте его из пакетов ОС:

```sh
apt-get update
apt-get install -y ca-certificates curl git openssl docker.io docker-compose-plugin
systemctl enable --now docker
docker --version
docker compose version
```

Если `docker compose version` не работает, сначала проверьте пакет `docker-compose-plugin`, а не добавляйте старый отдельный bootstrap-скрипт.

## Развёртывание

Рекомендуемый путь:

1. В `Admin -> VPS / Deploy` сохраните target.
2. Укажите `server-lite`.
3. Сверьте SSH fingerprint.
4. Нажмите `Подготовить VPS`, если Docker ещё не установлен.
5. Нажмите `Deploy + Hot Verify`.

Ручной путь для уже подготовленного VPS:

```sh
cd /opt/personal-agent
mkdir -p releases/<version>
# распаковать bundle в releases/<version>
ln -sfn releases/<version> current
docker compose --env-file .env.server -f docker-compose-main.yaml up -d --build
```

Для root-установки используйте `/opt/personal-agent`. Для non-root deployment root обычно лежит в `$HOME/.local/share/personal-agent`.

## Пример `.env.server`

Для VPS-lite достаточно таких ключевых значений:

```env
PA_VERSION=1.0.0
PA_RUNTIME_PROFILE=server
PA_AUTH_MODE=accounts
PA_SECURE_COOKIES=1

PA_PUBLIC_URL=https://agent.example.ru
PA_ADMIN_TOKEN=REPLACE_WITH_SECRET
PA_SEARXNG_SECRET=REPLACE_WITH_SECRET

PA_BIND_IP=127.0.0.1
PA_UI_PORT=3100
```

Если VPS использует только remote/BYOK AI provider, не делайте local Ollama обязательной зависимостью. Для слабого VPS локальные worker-сервисы должны быть выключены или отсутствовать в bundle.

`PA_DATABASE_URL` для текущего server-lite install не обязателен. Если вы сознательно тестируете PostgreSQL foundation, используйте отдельный experimental compose из `deploy/server/`, но не смешивайте его с обычным VPS-lite запуском.

## HTTPS через Caddy

После старта backend должен быть доступен локально, а Caddy должен проксировать домен на `127.0.0.1:3100`.

Проверка:

```sh
curl http://127.0.0.1:3100/api/health
curl -I https://agent.example.ru/
curl https://agent.example.ru/api/system
```

## Диагностика

Если VPS не стартует:

1. Проверьте, что Docker установлен и `docker compose version` работает.
2. Проверьте, что в `.env.server` заполнены `PA_ADMIN_TOKEN`, `PA_SEARXNG_SECRET` и `PA_PUBLIC_URL`.
3. Проверьте, что домен смотрит на VPS и порты `80/443` открыты.
4. Проверьте логи `core` и `caddy`.
5. Убедитесь, что вы не запускаете старую схему с Ollama/GPU на слабом VPS.

## Коротко

Для нового VPS не патчите сервер вручную через старый `compose.vps.yaml`. Используйте текущий server-lite bundle, где:

- VPS собирается через generated `docker-compose-main.yaml`;
- релизы переключаются через `current` и `previous`;
- локальный Ollama на слабом VPS не требуется;
- установка идёт из нормального Docker/Compose потока, а не через устаревший хак.
