#!/bin/sh
set -eu
systemctl is-active --quiet vps-egress-tunnel
egress=$(curl --fail --silent --show-error --connect-timeout 5 --max-time 12 --proxy http://127.0.0.1:18981 https://api.ipify.org)
test "$egress" = 89.125.3.243
for url in https://api.openai.com/v1/models https://generativelanguage.googleapis.com/v1beta/models https://api.deepseek.com/models; do
    code=$(curl --silent --show-error --connect-timeout 5 --max-time 12 --proxy http://127.0.0.1:18981 --output /dev/null --write-out '%{http_code}' "$url")
    case "$code" in 200|401|403) ;; *) printf 'egress unhealthy: HTTP %s\n' "$code"; exit 1;; esac
done
printf 'egress healthy: %s; DNS/TLS/provider transport reachable (not authentication check)\n' "$egress"
