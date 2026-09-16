# Selective API egress

Перенесено с работающего VPS 16.09.2026. В `config/` и `scripts/` — проверенные
конфигурации действующего туннеля, Tinyproxy, systemd health и firewall.
Они привязаны к текущим адресам и Docker bridge; перед другой установкой их нужно
адаптировать. Это эксплуатационные исходники, не универсальный установщик.

Приложение: `services/core/app/llm_egress.py`, зависимость в Core requirements.
В `.env.vps` действующего VPS:

```dotenv
PA_LLM_EGRESS_PROXY_URL=http://172.30.0.1:18981
PA_LLM_EGRESS_HOSTS=api.openai.com,generativelanguage.googleapis.com,api.deepseek.com
```

Обновление теперь использует **только основной Compose**, без старого
`/opt/vps-egress/config/compose.egress.yaml`: тот монтирует старую копию main.py.

```sh
cd /opt/rodnoi-agent
docker compose --env-file deploy/server/.env.vps -f compose.vps.yaml up -d --build
systemctl is-active vps-egress-tunnel
/opt/vps-egress/scripts/health.sh
```

Работающий SSH-туннель остаётся службой хоста. Private key, доверенный host key и
секреты не копируются в Git. OpenAI ключ остаётся в `.env.vps`/хранилище секретов.
HTTP 401 в health подтверждает только транспорт; реальную авторизацию проверяют
авторизованным запросом и генерацией. API redirect и сбой прокси не обходятся
прямым соединением.
