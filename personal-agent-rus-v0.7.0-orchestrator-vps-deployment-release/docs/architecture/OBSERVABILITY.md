# Observability — v0.7.0

v0.7.0 ships a deliberately lightweight built-in Admin monitoring view suitable for local machines and small VPS nodes. It is not presented as the final OpenTelemetry/Prometheus architecture required by MASTER-SPEC.

`GET /api/admin/observability` (Admin only) reports:

- timestamp/version/runtime profile/uptime;
- system load;
- available/total RAM when exposed by the host/container;
- free/total persistent-data filesystem space;
- SQLite DB size;
- user/session/task/artifact/usage counts;
- task counts by status;
- configured Web/Code/local-AI component flags;
- Secure-cookie server status;
- recent deployment targets/status;
- lightweight disk/memory/task-failure alerts.

Admin UI: `Мониторинг`.

## Not yet claimed

The canonical specification also requires structured JSON logging, immutable-oriented audit, metrics backend, distributed tracing, provider/GPU metrics, queues, alert delivery and production dashboards. Those remain explicit later slices; v0.7 does not label them implemented merely because the built-in snapshot exists.
