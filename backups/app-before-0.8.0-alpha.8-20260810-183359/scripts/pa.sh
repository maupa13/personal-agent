#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
ACTION=${1:-start}
ENV=.env
if [ ! -f "$ENV" ]; then
  TOKEN=$(python3 - <<'PY2'
import secrets
print(secrets.token_hex(32))
PY2
)
  SEARCH_SECRET=$(python3 - <<'PY3'
import secrets
print(secrets.token_hex(32))
PY3
)
  cat > "$ENV" <<EOF2
PA_BIND_IP=127.0.0.1
PA_UI_PORT=3100
PA_ADMIN_TOKEN=$TOKEN
PA_SEARXNG_SECRET=$SEARCH_SECRET
PA_BOOTSTRAP_MODEL=qwen3:0.6b
PA_OLLAMA_IMAGE=ollama/ollama:0.32.6
PA_CORE_IMAGE=personal-agent-core:0.8.0-alpha.7
PA_BROWSER_IMAGE=personal-agent-browser:0.8.0-alpha.7
PA_SEARXNG_IMAGE=searxng/searxng:2026.8.5-1689cb1b5
PA_CODE_WORKER_IMAGE=personal-agent-code-worker:0.8.0-alpha.7
PA_AUTH_MODE=personal
PA_REGISTRATION_POLICY=open
EOF2
fi
compose(){ docker compose --env-file "$ENV" -f compose.yaml "$@"; }
model=$(grep '^PA_BOOTSTRAP_MODEL=' "$ENV"|cut -d= -f2-)
case "$ACTION" in
  start)
    compose config --quiet
    compose up -d ollama searxng browser
    i=0; until compose exec -T ollama ollama list >/dev/null 2>&1; do i=$((i+1)); [ "$i" -lt 60 ] || { compose logs --tail 120 ollama; exit 1; }; sleep 2; done
    if ! compose exec -T ollama ollama list | grep -F "$model" >/dev/null; then compose exec -T ollama ollama pull "$model"; fi
    compose up -d --build code-worker
    compose up -d --build --remove-orphans core
    echo 'Open http://127.0.0.1:3100/'
    ;;
  stop) compose stop ;;
  restart) compose restart ollama searxng browser code-worker core ;;
  status) compose ps ;;
  logs) compose logs --tail 200 -f ;;
  admin) grep '^PA_ADMIN_TOKEN=' "$ENV"; echo 'Open http://127.0.0.1:3100/admin' ;;
  *) echo "Usage: $0 start|stop|restart|status|logs|admin"; exit 2 ;;
esac
