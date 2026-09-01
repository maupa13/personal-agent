# VPS Update: current server-lite install flow

Этот документ заменяет старую инструкцию, которая ссылалась на несуществующий `compose.vps.yaml`, старые версии образов и ручную настройку Ollama на слабом VPS.

Сейчас канонический VPS-поток такой:

- профиль `server-lite` для слабого VPS;
- `PA_RUNTIME_PROFILE=server`;
- `PA_AUTH_MODE=accounts`;
- `PA_SECURE_COOKIES=1`;
- локальный Ollama с демо-моделью `qwen3:0.6b` включён по умолчанию;
- публикация через generated bundle `docker-compose-main.yaml` + `.env.server` + `Caddyfile`;
- переключение релиза через `current` / `previous`.

## Что больше не использовать

- `compose.vps.yaml` из старой схемы;
- `compose.release.yaml` как VPS-профиль для слабого сервера;
- старые теги и пути вида `0.8.0-alpha.8`, если репозиторий уже собран с более новой версией;
- локальный Ollama как ручную обязательную зависимость для VPS;
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

## Прямой deploy из репозитория

Если вы обновляете сервер прямо из git-репозитория, а не через generated bundle,
используйте такой стандартный порядок.

Публикация:

```sh
cd /opt/rodnoi-agent
git pull --ff-only --autostash origin master
docker compose --env-file deploy/server/.env.vps -f compose.vps.yaml up -d --build
```

Перед `git pull` рабочее дерево репозитория на VPS не должно содержать
`U`/`UU` conflicted-файлы. Нормальный ожидаемый локальный оверрайд для этого
сценария - `M deploy/server/.env.vps`; `--autostash` временно уберёт его и
вернёт после fast-forward обновления.

Проверка:

```sh
docker compose --env-file deploy/server/.env.vps -f compose.vps.yaml ps
curl -fsS https://rodnoi-agent.ru/
```

Если нужен совсем безопасный вариант перед обновлением:

```sh
cd /opt/rodnoi-agent
git status --short
git pull --ff-only --autostash origin master
docker compose --env-file deploy/server/.env.vps -f compose.vps.yaml up -d --build
```

Если `git status --short` показывает `U`, `UU` или другие незавершённые merge
состояния, сначала нужно починить checkout, иначе `git pull --ff-only` не
сработает независимо от того, есть ли нужные файлы в `origin/master`.

Для этого сценария отдельный внешний SMTP больше не обязателен. `compose.vps.yaml`
поднимает локальный исходящий SMTP relay на том же VPS, а `core` отправляет письма
в контейнер `smtp`.

В `deploy/server/.env.vps` должны быть такие значения:

```env
PA_EMAIL_VERIFICATION_REQUIRED=1
PA_EMAIL_VERIFICATION_TTL_SECONDS=86400
PA_PASSWORD_RESET_TTL_SECONDS=7200
PA_SMTP_HOST=smtp
PA_SMTP_PORT=25
PA_SMTP_USERNAME=
PA_SMTP_PASSWORD=
PA_SMTP_FROM=support@rodnoi-agent.ru
PA_SMTP_STARTTLS=0
PA_SMTP_USE_SSL=0
PA_SMTP_DOMAIN=rodnoi-agent.ru
PA_SMTP_HOSTNAME=mail.rodnoi-agent.ru
PA_SMTP_DKIM_SELECTOR=mail
```

После этого обычный `docker compose ... up -d --build` сразу поднимет `core` с
готовой почтовой конфигурацией и локальным relay. Отдельная первичная настройка
SMTP в Admin UI не нужна, потому что такого экрана в текущей админке нет.

Короткий smoke-check SMTP и auth после публикации:

```sh
docker compose --env-file deploy/server/.env.vps -f compose.vps.yaml ps
docker compose --env-file deploy/server/.env.vps -f compose.vps.yaml logs --tail=50 smtp
docker compose --env-file deploy/server/.env.vps -f compose.vps.yaml exec core env | grep '^PA_SMTP_'
curl -fsS https://rodnoi-agent.ru/api/system
```

Если сервис `smtp` поднялся, в его логах появился DKIM record, `PA_SMTP_HOST=smtp`
виден внутри `core`, а `https://rodnoi-agent.ru/api/system` отвечает `200`,
значит стандартный deploy получил почтовую конфигурацию. После этого регистрация,
подтверждение email и сброс пароля должны работать без отдельной настройки через
Admin UI.

Для нормальной доставки в Gmail/Yandex/Mail.ru нужно дополнительно настроить DNS
домена:

- `A` record для `mail.rodnoi-agent.ru` на IP VPS;
- `MX` record для `rodnoi-agent.ru`, указывающий на `mail.rodnoi-agent.ru`;
- `TXT` SPF, например `v=spf1 mx a:mail.rodnoi-agent.ru ~all`;
- `TXT` DKIM record, который печатает контейнер `smtp` в логах при старте;
- `TXT` DMARC, например `v=DMARC1; p=quarantine; rua=mailto:postmaster@rodnoi-agent.ru`.

Если у провайдера VPS исходящий `25/tcp` заблокирован, self-hosted SMTP на этом
сервере работать не будет. В таком случае нужен внешний SMTP relay.

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

Если VPS использует только remote/BYOK AI provider, Ollama можно переопределить или отключить отдельно. Для слабого VPS локальная демо-модель `qwen3:0.6b` уже включена в bundle по умолчанию.

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
5. Убедитесь, что вы не запускаете старую схему с отдельной ручной настройкой Ollama/GPU на слабом VPS.

## Коротко

Для нового VPS не патчите сервер вручную через старый `compose.vps.yaml`. Используйте текущий server-lite bundle, где:

- VPS собирается через generated `docker-compose-main.yaml`;
- релизы переключаются через `current` и `previous`;
- локальный Ollama на слабом VPS уже идёт в bundle как демо-модель;
- установка идёт из нормального Docker/Compose потока, а не через устаревший хак.
